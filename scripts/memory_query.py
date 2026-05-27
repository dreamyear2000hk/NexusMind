#!/usr/bin/env python3
"""
memory_query.py — 意圖路由查詢執行器
深圳家智脈引擎 v2.0 核心：把意圖分類轉換為實際答案
"""

import re
import json
import sys
from pathlib import Path
from typing import Optional

# 確保 scripts/cron 在 Python 路徑中（可被 intent_classifier 等引用）
CRON_DIR = Path(__file__).parent
exec(f"import sys; sys.path.insert(0, '{CRON_DIR}')")

WORKSPACE  = Path("/home/joelam/.openclaw/workspace")
GRAPHS_DIR = WORKSPACE / "docs"
MEM_DIR    = WORKSPACE / "memory"
DATA_DIR   = WORKSPACE / "data"
SKILLS_DIR = WORKSPACE / "skills"

HA_URL = _get_ha_url() or "http://localhost:8123"

def _ha_token():
    env = Path.home() / ".agents" / "secrets" / "ha.env"
    if not env.exists(): return None
    with open(env) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() == "HA_TOKEN": return v.strip()
    return None

def _ha_get(path):
    tok = _ha_token()
    if not tok: return {}
    import urllib.request
    req = urllib.request.Request(HA_URL + "/api/" + path,
        headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except: return {}

def _title(md):
    try:
        with open(md) as f:
            for line in f:
                if line.startswith("# "): return line[2:].strip()
    except: pass
    return md.stem

# ── fact：事實性查詢（設備/IP/狀態）────────────────────────────────
def q_fact(q):
    ed = GRAPHS_DIR / "entities"
    kws = [kw for kw in re.sub(r"[老闆老板多少在哪是不是]","",q).strip().split() if len(kw) >= 2]
    res = []
    if ed.exists():
        for md in ed.rglob("*.md"):
            try:
                c = open(md).read()
                title = _title(md)
                if any(kw in title + c for kw in kws):
                    res.append({"name": md.stem, "title": title})
                    record_access(md.stem)  # P0.3: hotness tracking
            except: pass
    # 直接查 HA 實時狀態（只看燈/開關/sensor/climate）
    ha_data = []
    entity_kws = ["玄關", "玄关", "走廊", "yeelink", "mijia_cn_group", "xuan_guan", "zou_lang"]
    try:
        for s in _ha_get("states"):
            eid = s["entity_id"]
            fn = s.get("attributes",{}).get("friendly_name","")
            domain = eid.split(".")[0] if "." in eid else ""
            if domain not in ("light","switch","sensor","binary_sensor","climate"):
                continue
            # 匹配關鍵詞
            if any(kw in fn or kw in eid for kw in entity_kws):
                state = s["state"]
                if state not in ("unavailable","unknown",""):
                    ha_data.append({"name": fn or eid, "state": state})
    except: pass
    # 排序：開著的在前面
    ha_data.sort(key=lambda x: x["state"], reverse=True)
    if res or ha_data:
        lines = []
        if res:
            lines.append("📁 Graph 實體：")
            for r in res[:3]: lines.append("  • %s：%s" % (r["name"], r["title"][:80]))
        if ha_data:
            lines.append("\n📊 HA 實時：")
            for e in ha_data[:15]: lines.append("  • %s：%s" % (e["name"], e["state"]))
        return {"answer": "\n".join(lines), "source": "graph+HA", "found": len(ha_data)}
    return {"answer": "未找到相關事實", "source": "graph", "found": 0}

# ── reason：關係推理（設備聯動/wiki-link）────────────────────────
def q_reason(q):
    kw_map = ["聯動","關係","觸發","哪個傳感器","自動化"]
    if not any(kw in q for kw in kw_map): return {"answer":"無法識別","source":"reason","found":0}
    res = []
    for sub in ["concepts","events","entities"]:
        td = GRAPHS_DIR / sub
        if not td.exists(): continue
        for md in td.rglob("*.md"):
            try:
                c = open(md).read()
                if any(kw in c for kw in kw_map):
                    title = _title(md)
                    links = re.findall(r"\[\[([^\]]+)\]\]", c)
                    res.append({"name": md.stem, "title": title, "links": links[:8]})
            except: pass
    if res:
        lines = ["🔗 找到 %d 個關係節點：" % len(res)]
        for r in res[:3]:
            ls = " → ".join(r["links"][:3]) if r["links"] else "（無 wiki-link）"
            lines.append("  📄 %s：%s" % (r["name"], ls))
        return {"answer": "\n".join(lines), "source": "reason", "found": len(res)}
    return {"answer": "未找到設備關聯", "source": "reason", "found": 0}

# ── memory：模糊回憶（歷史事件/日誌）────────────────────────────────
def q_memory(q):
    kw_map = ["上次","曾經","解決","歷史","過去","哪天"]
    res = []
    # 只搜 events/ 目錄（精確歷史記錄）
    events_dir = GRAPHS_DIR / "events"
    if not events_dir.exists(): return {"answer":"未找到歷史記錄","source":"memory","found":0}
    for md in events_dir.rglob("*.md"):
        try:
            c = open(md).read()
            if any(kw in c for kw in kw_map):
                title = _title(md)
                dm = re.search(r"\d{4}-\d{2}-\d{2}", md.stem)
                res.append({"date": dm.group() if dm else "?", "name": md.stem, "title": title})
        except: pass
    if res:
        res.sort(key=lambda x: x["date"], reverse=True)
        lines = ["🔍 找到 %d 條歷史：" % len(res)]
        for r in res[:5]: lines.append("  📅 %s | %s" % (r["date"], r["title"][:60]))
        return {"answer": "\n".join(lines), "source": "memory", "found": len(res)}
    return {"answer": "未找到歷史記錄", "source": "memory", "found": 0}

# ── skill：能力執行（SKILL.md 查詢）────────────────────────────────
def q_skill(q):
    kw_map = ["配置","設置","生成","報告","執行","開啟","關閉"]
    if not SKILLS_DIR.exists(): return {"answer":"Skills目錄不存在","source":"skill","found":0}
    res = []
    for md in SKILLS_DIR.rglob("SKILL.md"):
        try:
            c = open(md).read()
            nm = re.search(r"name:\s*(.+)", c)
            tg = re.search(r"trigger:\s*(.+)", c)
            name = nm.group(1).strip() if nm else md.parent.name
            if any(kw in c for kw in kw_map):
                res.append({"name": name, "file": str(md.relative_to(WORKSPACE)), "trigger": tg.group(1).strip() if tg else ""})
        except: pass
    if res:
        lines = ["⚡ 找到 %d 個技能：" % len(res)]
        for r in res[:3]:
            lines.append("  🔧 %s" % r["name"])
            if r.get("trigger"): lines.append("     觸發：%s" % r["trigger"])
        lines.append("\n技能文件：%s" % res[0]["file"])
        return {"answer": "\n".join(lines), "source": "skill", "found": len(res)}
    return {"answer": "未找到相關技能", "source": "skill", "found": 0}

# ── alert：異常告警（溫度/設備狀態）─────────────────────────────────
def q_alert(q):
    ha = []
    try:
        for s in _ha_get("states"):
            if "temperature" in s["entity_id"].lower() and s["state"] not in ("unavailable","unknown",""):
                ha.append({"name": s.get("attributes",{}).get("friendly_name",s["entity_id"]), "state": s["state"]})
    except: pass
    hint = ""
    try:
        from smbdb import get_last_climate
        last = get_last_climate()
        if last:
            hint = "📊 室內：%s°C/%s%% (熱指數 %s°C)\n🌤️ 室外：%s°C/%s%% (體感 %s°C)" % (
                last["indoor_temp"], last["indoor_hum"], last["heat_index"],
                last["outdoor_temp"], last["outdoor_hum"], last["feels_temp"])
    except: pass
    lines = []
    if ha:
        lines.append("📊 HA 實時溫度：")
        for e in ha: lines.append("  • %s：%s" % (e["name"], e["state"]))
    if hint: lines.append(hint)
    if lines: return {"answer": "\n".join(lines), "source": "alert", "found": len(ha)}
    return {"answer": "無法獲取溫度數據", "source": "alert", "found": 0}

# ── 主入口 ───────────────────────────────────────────────────────
def query(text, intent=None):
    from intent_classifier import route
    from forgetting import record_access  # P0.3: hotness tracking
    from intent_classifier import INTENT_ALERT, INTENT_FACT, INTENT_REASON, INTENT_MEMORY, INTENT_SKILL, INTENT_UNKNOWN
    if intent is None:
        result = route(text)
        intent = result["category"]
        task_intent = result.get("task_intent", "unknown")
        recall_strategy = result.get("recall_strategy", "keyword")
    else:
        task_intent = "unknown"
        recall_strategy = "keyword"


    handlers = {
        INTENT_FACT:     q_fact,
        INTENT_REASON:   q_reason,
        INTENT_MEMORY:   q_memory,
        INTENT_SKILL:    q_skill,
        INTENT_ALERT:    q_alert,
    }
    if intent == INTENT_UNKNOWN:
        return {"intent": "unknown", "answer": "請告訴我具體需求？", "source": "unknown", "found": 0}
    h = handlers.get(intent)
    if not h:
        return {"intent": intent, "answer": "未知意圖類型", "source": "error", "found": 0}
    r = h(text)
    r["intent"] = intent
    r["task_intent"] = task_intent
    r["recall_strategy"] = recall_strategy
    return r

# ── 測試 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    from intent_classifier import classify
    cases = [
        ("老闆在家嗎", "fact"),
        ("客廳空調和哪個傳感器聯動", "reason"),
        ("上次那個問題怎麼解決", "memory"),
        ("Bigcore0溫度多少", "alert"),
        ("幫我生成每日新聞", "skill"),
        ("HA在線嗎", "fact"),
    ]
    print("=" * 60)
    for q, exp in cases:
        intent = classify(q)
        r = query(q, intent)
        ok = "✅" if intent == exp else "⚠️exp=%s" % exp
        print("\n%s [%s] %s" % (ok, intent, q))
        print("   %s (found=%s)" % (r["answer"][:80], r.get("found", 0)))
    print("=" * 60)