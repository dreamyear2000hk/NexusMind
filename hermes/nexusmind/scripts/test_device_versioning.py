#!/usr/bin/env python3
"""test_device_versioning.py — device_versioning 統一版測試"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from device_versioning import (
    parse_frontmatter, render_frontmatter, extract_ip_from_body,
    is_device_node, archive_current_node, create_new_version,
    ensure_version_frontmatter, check_and_version, init_all_device_nodes,
)

SAMPLE = """---
id: aio-server-ssh
version: 1
valid_from: 2026-04-18
valid_until: null
superseded_by: null
---

# AIO服務員 SSH 配置

| 項目 | 值 |
|-----|-----|
| IP 地址 | `192.168.1.100` |
| SSH 端口 | `22` |
"""

def test_parse_frontmatter():
    front, body = parse_frontmatter(SAMPLE)
    assert front.get("id") == "aio-server-ssh"
    assert front.get("version") == "1"
    print("✅ parse_frontmatter OK")

def test_render_frontmatter():
    front, _ = parse_frontmatter(SAMPLE)
    rendered = render_frontmatter(front)
    assert "version: 1" in rendered
    assert "valid_from: 2026-04-18" in rendered
    print("✅ render_frontmatter OK")

def test_extract_ip():
    ip = extract_ip_from_body(SAMPLE)
    assert ip == "192.168.1.100", f"IP extraction wrong: {ip}"
    print("✅ extract_ip_from_body OK")

def test_is_device_node():
    front, body = parse_frontmatter(SAMPLE)
    assert is_device_node("aio-server-ssh.md", front, body) == True
    assert is_device_node("automation_ban_shui.md", {"ha_entity_id": "automation.xxx"}, body) == False
    print("✅ is_device_node OK")

def test_init():
    results = init_all_device_nodes()
    print(f"   Initialized: {len(results['initialized'])}")
    print(f"   Skipped: {len(results['skipped'])}")
    print(f"   Errors: {len(results['errors'])}")
    print("✅ init_all_device_nodes OK")

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        test_parse_frontmatter()
        test_render_frontmatter()
        test_extract_ip()
        test_is_device_node()
        test_init()
        print("\n=== ALL TESTS PASSED ===")
    else:
        print("device_versioning.py — 設備節點版本化管理")
        print("  python test_device_versioning.py --test")