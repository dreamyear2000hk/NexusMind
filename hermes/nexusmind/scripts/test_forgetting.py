#!/usr/bin/env python3
"""test_forgetting.py — forgetting 統一版測試"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from forgetting import (
    calc_W_time, calc_W_freq, calc_affinity, score_entity,
    evaluate_entities, execute_purge, record_access,
    LAMBDA, THRESHOLD_CORE, THRESHOLD_KEEP,
)

def test_calc_W_time():
    # 0 days old → exp(0) = 1.0
    assert abs(calc_W_time(0) - 1.0) < 0.001
    # λ days old → exp(-1) ≈ 0.368
    assert abs(calc_W_time(LAMBDA) - 0.3679) < 0.01
    print("✅ calc_W_time OK")

def test_calc_W_freq():
    assert abs(calc_W_freq(0) - 0.0) < 0.001
    assert abs(calc_W_freq(1) - 0.6931) < 0.01
    assert abs(calc_W_freq(9) - 2.3026) < 0.01
    print("✅ calc_W_freq OK")

def test_calc_affinity():
    feedback = [
        {"entity_id": "e1", "type": "confirm"},
        {"entity_id": "e1", "type": "correct"},
        {"entity_id": "e2", "type": "wrong"},
        {"entity_id": "e1", "type": "forget"},
    ]
    assert abs(calc_affinity(feedback, "e1") - 0.5) < 0.001
    assert abs(calc_affinity(feedback, "e2") - (-0.5)) < 0.001
    assert abs(calc_affinity(feedback, "e3") - 0.0) < 0.001
    print("✅ calc_affinity OK")

def test_evaluate_entities():
    result = evaluate_entities()
    assert "core_promote" in result
    assert "long_term" in result
    assert "short_term" in result
    assert "purge" in result
    assert "total" in result
    print(f"   Total entities: {result['total']}")
    print("✅ evaluate_entities OK")

def test_record_access():
    record_access("test-entity")
    print("✅ record_access OK (no crash)")

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        test_calc_W_time()
        test_calc_W_freq()
        test_calc_affinity()
        test_evaluate_entities()
        test_record_access()
        print("\n=== ALL TESTS PASSED ===")
    else:
        print("forgetting.py — 遺忘算法")
        print("  python test_forgetting.py --test")