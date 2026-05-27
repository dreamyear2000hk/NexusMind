#!/usr/bin/env python3
"""
forgetting.py — 遺忘算法核心（NexusMind 統一版）
深圳家智脈引擎 v2.0 核心模塊

W = W_time × (1 + W_freq) × W_affinity
W ≥ 0.8  → 核心記憶候選（昇級條件）
0.3 ≤ W < 0.8  → 長期記憶（保留）
0 < W < 0.3    → 短期記憶（30天後刪除）
W = 0         → 直接刪除（不含 compiled-truth）

框架適配：通過 framework.py 自動注入路徑
核心邏輯（無框架代碼）：calc_W_time / score_entity / evaluate_entities / execute_purge / promote_to_core
"""

import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from framework import get_graphs_dir, get_state_file, get_feedback_file

GRAPHS_DIR  = get_graphs_dir()
STATE_FILE  = get_state_file()
FEEDBACK_FILE = get_feedback_file()

# ── 默認參數 ─────────────────────────────────────────────────────────
LAMBDA = 30.0          # 時間衰減常數（天）
ALPHA  = 0.0           # 情感權重基線
DEFAULT_W = 0.5         # 新實體默認生存分數
THRESHOLD_CORE  = 0.80  # 昇級核心記憶閾值
THRESHOLD_KEEP  = 0.30  # 保留長期記憶閾值
THRESHOLD_PURGE = 0.0   # 物理刪除閾值

# ── 類型權重（不同類型實體默認權重）───────────────────────────────
TYPE_BASE_SCORES = {
    "entity":      0.60,
    "event":       0.50,
    "concept":     0.65,
    "problem":     0.70,
    "automation":  0.75,
    "compiled":    1.00,   # compiled-truth 永不刪除
}


def _load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"entities": {}, "last_run": None}


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _load_feedback() -> list:
    if not FEEDBACK_FILE.exists():
        return []
    with open(FEEDBACK_FILE) as f:
        return json.load(f)


def _clear_feedback():
    if FEEDBACK_FILE.exists():
        FEEDBACK_FILE.unlink()


def _days_old(dt_str: str) -> float:
    """計算實體上次更新的天數"""
    try:
        dt = datetime.fromisoformat(dt_str)
        return (datetime.now() - dt).total_seconds() / 86400
    except Exception:
        return 999.0


# ── 核心算法 ──────────────────────────────────────────────────────

def calc_W_time(days: float, lam: float = LAMBDA) -> float:
    """時間衰減: S_t = S_0 × e^(-t/λ)"""
    return math.exp(-days / lam)


def calc_W_freq(access_count: int) -> float:
    """頻次增益: log(1 + f)"""
    return math.log(1 + max(access_count, 0))


def calc_affinity(feedback_entries: list, entity_id: str) -> float:
    """情感權重：老闆反饋調整"""
    score = 0.0
    for entry in feedback_entries:
        if entry.get("entity_id") == entity_id:
            t = entry.get("type")
            if t == "confirm":
                score += 1.0
            elif t == "correct":
                score += 0.5
            elif t == "wrong":
                score -= 0.5
            elif t == "forget":
                score -= 1.0
    return score


def score_entity(entity_path: Path, state: dict, feedback: list) -> float:
    """
    計算單個實體的生存分數 W
    W = W_time × (1 + W_freq) × W_affinity × type_base
    """
    eid = str(entity_path.relative_to(GRAPHS_DIR))
    base_score = TYPE_BASE_SCORES.get(entity_path.parent.name, DEFAULT_W)

    stat = entity_path.stat()
    mtime_str = datetime.fromtimestamp(stat.st_mtime).isoformat()
    days = _days_old(mtime_str)

    W_time = calc_W_time(days)
    access_count = state["entities"].get(eid, {}).get("access_count", 0)
    W_freq = calc_W_freq(access_count)
    affinity_delta = calc_affinity(feedback, eid)
    W_affinity = max(0.1, 1.0 + affinity_delta)

    W = max(0.0, min(W_time * (1 + W_freq) * W_affinity * base_score, 1.0))
    return W


def evaluate_entities(graphs_dir: Path = GRAPHS_DIR) -> dict:
    """對 docs/ 下的所有實體打分，返回分類結果"""
    state    = _load_state()
    feedback = _load_feedback()

    core_待昇級 = []
    long_term  = []
    short_term = []
    purge_list = []

    if not graphs_dir.exists():
        return {"core_promote": [], "long_term": [], "short_term": [], "purge": [], "total": 0}

    for entity_path in graphs_dir.rglob("*.md"):
        if "compiled-truth" in entity_path.parts:
            continue
        W = score_entity(entity_path, state, feedback)
        result = {
            "path": str(entity_path),
            "eid":  str(entity_path.relative_to(GRAPHS_DIR)),
            "W":    round(W, 4),
            "days": round(_days_old(datetime.fromtimestamp(entity_path.stat().st_mtime).isoformat()), 1),
        }
        if W >= THRESHOLD_CORE:
            core_待昇級.append(result)
        elif W >= THRESHOLD_KEEP:
            long_term.append(result)
        elif W > THRESHOLD_PURGE:
            short_term.append(result)
        else:
            purge_list.append(result)

    return {
        "core_promote": core_待昇級,
        "long_term":    long_term,
        "short_term":   short_term,
        "purge":        purge_list,
        "total":        len(core_待昇級) + len(long_term) + len(short_term) + len(purge_list),
    }


def execute_purge(purge_list: list, dry_run: bool = False) -> list:
    """執行遺忘：物理刪除低分實體"""
    deleted = []
    for item in purge_list:
        path = Path(item["path"])
        if path.exists() and path.is_file():
            if dry_run:
                print(f"  [DRY-RUN] 刪除: {item['eid']} (W={item['W']})")
            else:
                path.unlink()
                deleted.append(item)
                print(f"  🗑️  刪除: {item['eid']} (W={item['W']})")
        elif path.exists():
            print(f"  ⚠️  跳過（目錄）: {item['eid']}")
    return deleted


def promote_to_core(long_term_list: list) -> list:
    """將高分長期記憶昇級為核心記憶"""
    promoted = []
    ct_dir = GRAPHS_DIR / "concepts" / "compiled-truth"
    if not ct_dir.exists():
        return promoted
    for item in long_term_list:
        path = Path(item["path"])
        if path.exists():
            dest = ct_dir / path.name
            if dest.exists():
                continue
            try:
                shutil.move(str(path), str(dest))
                promoted.append({**item, "new_path": str(dest)})
                print(f"  ⬆️  昇級核心: {item['eid']} → compiled-truth/")
            except Exception as e:
                print(f"  ❌ 昇級失敗: {item['eid']}: {e}")
    return promoted


def record_access(eid: str):
    """記錄某實體被訪問（用於 W_freq 計算）"""
    state = _load_state()
    if eid not in state["entities"]:
        state["entities"][eid] = {"access_count": 0}
    state["entities"][eid]["access_count"] += 1
    _save_state(state)


def run_dream_cycle(dry_run: bool = False) -> dict:
    """執行完整夢週期遺忘評估"""
    print("=" * 50)
    print("🌙 夢週期 - 遺忘算法評估")
    print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    result = evaluate_entities()

    print(f"\n📊 評估結果（共 {result['total']} 個實體）:")
    print(f"   ⬆️  核心昇級候選: {len(result['core_promote'])} 個")
    print(f"   ✅ 長期記憶:     {len(result['long_term'])} 個")
    print(f"   ⏳ 短期記憶:     {len(result['short_term'])} 個")
    print(f"   🗑️  待遺忘:      {len(result['purge'])} 個")

    deleted  = execute_purge(result["purge"], dry_run=dry_run)
    promoted = promote_to_core(result["core_promote"])

    state = _load_state()
    state["last_run"] = datetime.now().isoformat()
    _save_state(state)
    _clear_feedback()

    return {
        "result":    result,
        "deleted":   deleted,
        "promoted":  promoted,
        "last_run":  state["last_run"],
    }


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    r = run_dream_cycle(dry_run=dry)
    print(f"\n✅ 夢週期完成 | 上次運行: {r['last_run']}")