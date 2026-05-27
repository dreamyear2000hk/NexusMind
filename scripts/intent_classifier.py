#!/usr/bin/env python3
"""
P0.2 — 意圖路由增強：task intent 驅動的動態召回策略
深圳家智脈引擎 v2.0：將召回分為三種模式
  - fact  → 精確召回（設備狀態、IP、配置）→ keyword + BM25
  - learning → 語義召回（概念理解、決策過程）→ semantic
  - skill → 程序召回（SOP、自動化腳本）→ exact match

改動：
1. intent_classifier.py 新增 TASK_INTENT 檢測
2. memory_query.py 新增 q_fact/q_learning/q_skill 三種召回實現
3. route() 返回 memory_layers 由 string 改為 dict，含策略說明
"""

import re
import os
from pathlib import Path

WORKSPACE = Path("YOUR_WORKSPACE_PATH")
GRAPHS_DIR = WORKSPACE / "docs"
SKILLS_DIR = WORKSPACE / "skills"

# ── 任務意圖枚舉（擴展原來的 5 分類，加入 task intent）──────────────
INTENT_FACT     = "fact"      # 事實查詢（設備/IP/狀態）
INTENT_LEARNING = "learning" # 概念理解、決策過程
INTENT_SKILL    = "skill"     # 程序/SOP/腳本
INTENT_REASON   = "reason"    # 設備關係/自動化
INTENT_MEMORY   = "memory"    # 歷史事件
INTENT_ALERT    = "alert"     # 異常監控
INTENT_UNKNOWN  = "unknown"

# ── 召回策略枚舉 ─────────────────────────────────────────────────
RECALL_KEYWORD   = "keyword"    # 關鍵詞精確匹配
RECALL_SEMANTIC  = "semantic"   # 語義向量檢索（mem0）
RECALL_EXACT     = "exact"      # 精確文件名/路徑匹配
RECALL_BM25      = "bm25"       # BM25 排序

# ── 任務意圖檢測關鍵詞 ───────────────────────────────────────────
TASK_INTENT_PATTERNS = {
    INTENT_LEARNING: [
        r"(?:什麼是|怎麼|如何|為什麼|為何)",
        r"(?:原理|概念|機制|邏輯)",
        r"(?:解釋|說明|理解)",
        r"(?:設計|架構|思路)",
        r"(?:什麼情況|哪種情況)",
        r"(?:記得|印象|曾經).{0,6}(?:什麼|怎麼|做)",
        r"^(?:/grill|/zoom)",
    ],
    INTENT_SKILL: [
        r"(?:執行|運行|幫我做)",
        r"(?:生成|創建|新建)",
        r"(?:配置|設置|開啟|關閉)",
        r"(?:一鍵|自動)",
        r"(?:腳本|腳本|cron|schedule)",
        r"(?:幫我|給我).*(?:執行|生成|創建)",
    ],
    INTENT_FACT: [
        r"(?:多少|哪個|在哪|是不是|有沒有|如何|怎麼樣)",
        r"(?:狀態|在線|開著|關著|亮了|滅了)",
        r"(?:IP|地址|密碼|端口)",
        r"(?:老闆|老板).{0,6}(?:在家|在哪)",
        r"(?:溫度|濕度|負載).{0,6}(?:多少|如何|怎麼樣|正常|異常)",
        r"(?:燈|窗簾|門|鎖).{0,4}(?:開|關|亮|滅)",
        r"打卡",
    ],
}

_LEARNING_COMPILED = [re.compile(p, re.IGNORECASE) for p in TASK_INTENT_PATTERNS[INTENT_LEARNING]]
_SKILL_COMPILED   = [re.compile(p, re.IGNORECASE) for p in TASK_INTENT_PATTERNS[INTENT_SKILL]]
_FACT_COMPILED    = [re.compile(p, re.IGNORECASE) for p in TASK_INTENT_PATTERNS[INTENT_FACT]]

def detect_task_intent(query: str) -> str:
    """檢測查詢的任務意圖（fact/learning/skill），優先級：learning > skill > fact"""
    query = query.strip()
    if not query:
        return INTENT_UNKNOWN

    if any(p.search(query) for p in _LEARNING_COMPILED):
        return INTENT_LEARNING
    if any(p.search(query) for p in _SKILL_COMPILED):
        return INTENT_SKILL
    if any(p.search(query) for p in _FACT_COMPILED):
        return INTENT_FACT
    return INTENT_UNKNOWN


# ── 原有意圖分類（保留，向下兼容）────────────────────────────────
INTENT_PATTERNS = {
    INTENT_ALERT: [
        r"(?:Bigcore|GPU|NPU|NVMe|fan|load|CPU|Bigcore0|Bigcore2).{0,6}(?:溫度|負載|多少|幾度)",
        r"打卡",
        r"AIO.{0,4}(?:溫度|狀態|如何|怎麼)",
        r"室內.{0,4}溫度|室溫|家裡溫度",
        r"(?:多少|幾度).{0,4}(?:正常|異常|超標)",
    ],
    INTENT_FACT: [
        r"(?:IP|地址|密碼|密鑰|token|key)",
        r"(?:老闆|老板).{0,6}(?:在哪|回家|在家)",
        r"HA.*(?:在線|開機|運行)",
        r"(?:燈|窗簾|門|鎖|空氣).{0,4}(?:開|關|亮|著|了)嗎",
        r"(?:是不是|有沒有).{0,6}(?:開|關|在線)",
    ],
    INTENT_REASON: [
        r"(?:哪個|誰|哪個傳感器).{0,4}(?:聯動|關聯)",
        r"(?:客廳|主臥|工作室).{0,6}(?:空調和|連動)",
        r".{0,4}和.{0,4}關係|關係.*",
    ],
    INTENT_MEMORY: [
        r"上次|曾經|以前|之前",
        r"什麼時候|哪天|何時",
        r"怎麼解決|如何處理",
        r"記得|印象",
    ],
    INTENT_SKILL: [
        r"(?:給我|幫我|執行|運行).*(?:配置|設置|開啟|關閉)",
        r"(?:執行|運行|做).{0,4}(?:腳本|腳本|cron)",
        r"每日新聞|新聞簡報|晨報|晚報",
        r"生成.*新聞|幫我.*新聞",
        r"(?:一鍵|自動)",
        r"(?:新建|創建).*(?:自動化|腳本|技能)",
    ],
}

_COMPILED = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in INTENT_PATTERNS.items()}


def classify(query: str) -> str:
    """原有 5 分類分類器（保留，向下兼容）"""
    query = query.strip()
    if not query:
        return INTENT_UNKNOWN
    for intent in [INTENT_ALERT, INTENT_FACT, INTENT_SKILL, INTENT_REASON, INTENT_MEMORY]:
        if any(p.search(query) for p in _COMPILED[intent]):
            return intent
    return INTENT_UNKNOWN


def classify_with_task_intent(query: str) -> dict:
    """
    擴展分類：返回 {category, task_intent, recall_strategy}
    - category: 原有 5 分類（fact/reason/memory/skill/alert）
    - task_intent: fact/learning/skill/unknown（查詢的任務意圖）
    - recall_strategy: keyword/semantic/exact/bm25
    """
    category = classify(query)
    task_intent = detect_task_intent(query)

    # 任務意圖受 category 約束：alert 查詢永遠是事實查詢（溫度/狀態），
    # 不應被 "如何" 等詞誤判為 learning
    if category == INTENT_ALERT:
        task_intent = INTENT_FACT

    # 根據 task_intent 決定召回策略
    if task_intent == INTENT_LEARNING:
        recall = RECALL_SEMANTIC
    elif task_intent == INTENT_SKILL:
        recall = RECALL_EXACT
    elif category in (INTENT_MEMORY, INTENT_REASON):
        recall = RECALL_SEMANTIC
    elif category == INTENT_ALERT:
        recall = RECALL_KEYWORD  # AIO溫度用 keyword 匹配
    elif task_intent == INTENT_FACT:
        recall = RECALL_KEYWORD  # IP/狀態用精確關鍵詞
    else:
        recall = RECALL_KEYWORD

    return {
        "category": category,
        "task_intent": task_intent,
        "recall_strategy": recall,
        "query": query,
    }


# ── 路由 ─────────────────────────────────────────────────────────
def route(query: str) -> dict:
    """
    擴展路由：返回完整召回指引
    取代舊的 route()，增加 recall_strategy 和 task_intent
    """
    result = classify_with_task_intent(query)

    # memory_layers 映射（擴展）
    layers_map = {
        INTENT_FACT:     ["compiled-truth", "entities"],
        INTENT_LEARNING: ["concepts", "events"],
        INTENT_SKILL:    ["skills", "scripts"],
        INTENT_REASON:   ["entities", "events", "concepts"],
        INTENT_MEMORY:   ["events", "graph"],
        INTENT_ALERT:    ["climate.db", "aio_event_log.db"],
        INTENT_UNKNOWN:  ["all"],
    }
    recall_map = {
        RECALL_KEYWORD:  "keyword 精確匹配（設備/IP/配置）",
        RECALL_SEMANTIC: "semantic 語義召回（概念/決策）",
        RECALL_EXACT:    "exact 精確匹配（腳本/SOP）",
        RECALL_BM25:     "BM25 排序（歷史日誌）",
    }

    # task_intent 修正規則：
    # alert → fact（"AIO溫度如何"是事實查詢，不是概念學習）
    # unknown + learning → 保持 semantic（概念查詢，無需修改）
    if result["category"] == INTENT_ALERT and result["task_intent"] == INTENT_LEARNING:
        result["task_intent"] = INTENT_FACT
        result["recall_strategy"] = RECALL_KEYWORD
        result["recall_hint"] = "keyword 精確匹配（設備/IP/配置）"

    hint = {
        INTENT_FACT:     "✅ 找到了事實",
        INTENT_LEARNING: "📚 找到了概念",
        INTENT_SKILL:    "⚡ 技能準備好了",
        INTENT_REASON:   "🔗 找到了關係",
        INTENT_MEMORY:   "🔍 找到了回憶",
        INTENT_ALERT:    "🚨 異常檢測中",
        INTENT_UNKNOWN:  "❓ 請問具體需求",
    }.get(result["category"], "❓ 需要更多信息")

    result["confidence"] = 0.0 if result["category"] == INTENT_UNKNOWN else 0.75
    result["memory_layers"] = layers_map.get(result["category"], ["all"])
    result["recall_hint"] = recall_map.get(result["recall_strategy"], "")
    result["answer_hint"] = hint

    return result


# ── 測試 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    cases = [
        # (query, expected_category, expected_task_intent)
        ("AIO打卡",                     "alert",   "fact"),
        ("老闆在家嗎",                  "fact",    "fact"),
        ("客廳空調和哪個傳感器聯動",    "reason",  "fact"),
        ("上次那個問題怎麼解決",         "memory",  "learning"),
        ("Bigcore0溫度多少",             "alert",   "fact"),
        ("HA在線嗎",                    "fact",    "fact"),
        ("幫我生成每日新聞",             "skill",   "skill"),
        ("什麼是Karpathy Pattern",      "unknown", "learning"),
        ("如何設計記憶系統",            "unknown", "learning"),
        ("執行備份腳本",                "skill",   "skill"),
        ("新建一個自動化",              "skill",   "skill"),
        ("記得昨天做了什麼",             "memory",  "learning"),
        ("走廊燈開嗎",                  "fact",    "fact"),
        ("給我配置快照推送",             "skill",   "skill"),
    ]

    print("=" * 60)
    all_ok = True
    for q, exp_cat, exp_task in cases:
        result = route(q)
        cat_ok = result["category"] == exp_cat
        task_ok = result["task_intent"] == exp_task
        ok = "✅" if (cat_ok and task_ok) else "⚠️"
        if not (cat_ok and task_ok):
            all_ok = False
        print(f"{ok} {q}")
        print(f"   category={result['category']} (exp={exp_cat}) "
              f"| task_intent={result['task_intent']} (exp={exp_task}) "
              f"| recall={result['recall_strategy']}")
        print(f"   → {result['answer_hint']} | {result['recall_hint']}")
    print("=" * 60)
    print("✅ 全部通過" if all_ok else "❌ 有失敗")