#!/usr/bin/env python3
"""
NexusMind 意圖分類測試
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from intent_classifier import route, classify


def test_route():
    """測試 route() 函數"""
    cases = [
        # (text, expected_category, expected_task_intent, expected_recall)
        ("早啊", "unknown", "unknown", "keyword"),
        ("你好", "unknown", "unknown", "keyword"),
        ("服務器IP多少", "fact", "fact", "keyword"),
        ("老闆在家嗎", "fact", "fact", "keyword"),
        ("溫度多少", "unknown", "fact", "keyword"),
        ("Bigcore0溫度", "alert", "fact", "keyword"),
        ("上次那個問題", "memory", "unknown", "semantic"),
        ("歷史記錄", "unknown", "unknown", "keyword"),
        ("空調和哪個傳感器聯動", "reason", "fact", "semantic"),
        ("設備關係", "reason", "unknown", "semantic"),
        ("幫我執行備份", "unknown", "skill", "exact"),
        ("生成新聞", "skill", "skill", "exact"),
        ("什麼是 Karpathy", "unknown", "learning", "semantic"),
        ("如何設計系統", "unknown", "learning", "semantic"),
    ]

    passed = 0
    failed = []
    for text, exp_cat, exp_task, exp_recall in cases:
        r = route(text)
        ok = (
            r["category"] == exp_cat
            and r["task_intent"] == exp_task
            and r["recall_strategy"] == exp_recall
        )
        if ok:
            passed += 1
        else:
            failed.append((text, exp_cat, r["category"], exp_task, r["task_intent"]))

    total = len(cases)
    print(f"\nroute() 測試結果: {passed}/{total}")
    if failed:
        print("\n失敗用例：")
        for f in failed:
            print(f"  '{f[0]}' → expected {f[1]}/{f[3]}, got {f[2]}/{f[4]}")
    return passed == total


def test_classify():
    """測試 classify() 快捷函數"""
    cases = [
        ("溫度多少", "unknown"),
        ("老闆在家嗎", "fact"),
        ("上次", "memory"),
        ("執行腳本", "skill"),
        ("hi", "unknown"),
    ]
    passed = sum(1 for q, exp in cases if classify(q) == exp)
    print(f"\nclassify() 測試結果: {passed}/{len(cases)}")
    return passed == len(cases)


if __name__ == "__main__":
    ok1 = test_route()
    ok2 = test_classify()
    if ok1 and ok2:
        print("\n✅ 所有測試通過")
        sys.exit(0)
    else:
        print("\n❌ 部分測試失敗")
        sys.exit(1)
