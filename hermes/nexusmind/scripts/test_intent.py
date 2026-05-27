#!/usr/bin/env python3
"""test_intent.py — intent_classifier 統一版測試"""
import sys
sys.path.insert(0, str(__file__.rsplit("/", 2)[0] / "scripts"))

from intent_classifier import classify, route, classify_with_task_intent

CASES = [
    ("AIO打卡",                     "alert",   "fact"),
    ("老闆在家嗎",                  "fact",    "fact"),
    ("客廳空調和哪個傳感器聯動",    "reason",  "fact"),
    ("上次那個問題怎麼解決",        "memory",  "learning"),
    ("Bigcore0溫度多少",            "alert",   "fact"),
    ("HA在線嗎",                    "fact",    "fact"),
    ("幫我生成每日新聞",            "skill",   "skill"),
    ("什麼是Karpathy Pattern",      "unknown", "learning"),
    ("如何設計記憶系統",            "unknown", "learning"),
    ("執行備份腳本",                "skill",   "skill"),
    ("新建一個自動化",              "skill",   "skill"),
    ("記得昨天做了什麼",             "memory",  "learning"),
    ("走廊燈開嗎",                  "fact",    "fact"),
    ("給我配置快照推送",             "skill",   "skill"),
]

def test_classify():
    print("=== classify() ===")
    errors = []
    for q, exp_cat, exp_task in CASES:
        r = route(q)
        cat_ok = r["category"] == exp_cat
        task_ok = r["task_intent"] == exp_task
        if not (cat_ok and task_ok):
            errors.append((q, exp_cat, r["category"], exp_task, r["task_intent"]))
            print(f"⚠️  {q}")
            print(f"   category={r['category']} (exp={exp_cat}) | task={r['task_intent']} (exp={exp_task})")
        else:
            print(f"✅ {q}")
    return errors

def test_classify_with_task_intent():
    print("\n=== classify_with_task_intent() ===")
    r = classify_with_task_intent("AIO打卡")
    assert r["category"] == "alert"
    assert r["task_intent"] == "fact"
    assert r["recall_strategy"] == "keyword"
    print("✅ classify_with_task_intent OK")

def test_route_fields():
    print("\n=== route() fields ===")
    r = route("老闆在家嗎")
    assert "category" in r
    assert "task_intent" in r
    assert "recall_strategy" in r
    assert "confidence" in r
    assert "memory_layers" in r
    assert "answer_hint" in r
    print("✅ all fields present")

if __name__ == "__main__":
    errs = test_classify()
    test_classify_with_task_intent()
    test_route_fields()
    print("\n" + "=" * 60)
    if errs:
        print(f"❌ {len(errs)} 失敗")
        sys.exit(1)
    else:
        print("✅ 全部通過")