#!/usr/bin/env python3
"""
test_intent.py — 意圖分類測試（Hermes 版本）
"""

import sys
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from intent_classifier import route


def test_intent_classifier():
    cases = [
        ("AIO打卡",                  "alert",   "fact"),
        ("老闆在家嗎",               "fact",    "fact"),
        ("客廳空調和哪個傳感器聯動", "reason",  "fact"),
        ("上次那個問題怎麼解決",     "memory",  "learning"),
        ("Bigcore0溫度多少",         "alert",   "fact"),
        ("HA在線嗎",                 "fact",    "fact"),
        ("幫我生成每日新聞",          "skill",   "skill"),
        ("什麼是Karpathy Pattern",  "unknown", "learning"),
        ("如何設計記憶系統",         "unknown", "learning"),
        ("執行備份腳本",             "skill",   "skill"),
        ("新建一個自動化",           "skill",   "skill"),
        ("記得昨天做了什麼",          "memory",  "learning"),
        ("走廊燈開嗎",               "fact",    "fact"),
        ("給我配置快照推送",          "skill",   "skill"),
        ("IP是多少",                 "fact",    "fact"),
        ("密碼多少",                 "fact",    "fact"),
        ("在哪裡",                  "unknown", "fact"),
        ("hello",                    "unknown", "unknown"),
        ("幫我",                     "unknown", "unknown"),
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
        print(f"   → {result['answer_hint']}")
    print("=" * 60)
    print("✅ 全部通過" if all_ok else "❌ 有失敗")
    return all_ok


if __name__ == "__main__":
    ok = test_intent_classifier()
    sys.exit(0 if ok else 1)