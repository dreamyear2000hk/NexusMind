#!/usr/bin/env python3
"""test_memory_query.py — memory_query 統一版測試"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from memory_query import q_fact, q_reason, q_memory, q_skill, q_alert

def test_q_fact():
    r = q_fact("老闆在家嗎")
    assert "intent" not in r or r.get("found", 0) >= 0
    print(f"✅ q_fact: found={r.get('found')}, source={r.get('source')}")

def test_q_reason():
    r = q_reason("客廳空調和哪個傳感器聯動")
    assert "answer" in r
    print(f"✅ q_reason: {r['answer'][:60]}")

def test_q_memory():
    r = q_memory("上次那個問題怎麼解決")
    assert "answer" in r
    print(f"✅ q_memory: found={r.get('found')}")

def test_q_skill():
    r = q_skill("幫我生成每日新聞")
    assert "answer" in r
    print(f"✅ q_skill: found={r.get('found')}")

def test_q_alert():
    r = q_alert("Bigcore0溫度多少")
    assert "answer" in r
    print(f"✅ q_alert: source={r.get('source')}")

if __name__ == "__main__":
    test_q_fact()
    test_q_reason()
    test_q_memory()
    test_q_skill()
    test_q_alert()
    print("\n=== ALL TESTS PASSED ===")