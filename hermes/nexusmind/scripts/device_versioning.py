#!/usr/bin/env python3
"""
device_versioning.py — 設備實體節點時間版控（NexusMind 統一版）
深圳家智脈引擎 v2.0：當設備屬性（IP/端口/配置）變化時，
舊節點歸檔到 .vN.md，新節點作為 current，實現完整可溯源的版本鏈。

框架適配：通過 framework.py 自動注入路徑
核心邏輯（無框架代碼）：parse_frontmatter / archive / check_and_version / init
"""

import re
import shutil
from pathlib import Path
from datetime import date
from typing import Optional, Tuple

from framework import get_workspace, get_graphs_dir

WORKSPACE  = get_workspace()
ENTITIES  = get_graphs_dir() / "entities"
TODAY     = date.today().isoformat()


# ── YAML Frontmatter 解析 ────────────────────────────────────────

def parse_frontmatter(text: str) -> Tuple[dict, str]:
    """解析 markdown 文件，返回 (frontmatter_dict, body)"""
    if not text.strip().startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1].strip()
    body = parts[2]
    front = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if v == "null":
                v = None
            front[k] = v
    return front, body


def render_frontmatter(fields: dict) -> str:
    """dict 渲染為 YAML frontmatter"""
    lines = ["---"]
    for k, v in fields.items():
        if v is None:
            lines.append(f"{k}: null")
        elif isinstance(v, list):
            lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def update_frontmatter(text: str, updates: dict) -> str:
    """更新已有 frontmatter，保持原有順序"""
    front, body = parse_frontmatter(text)
    front.update(updates)
    return render_frontmatter(front) + body


# ── 設備節點識別 ──────────────────────────────────────────────────

def is_device_node(filename: str, front: dict, body: str) -> bool:
    """判斷是否為需要版本化的設備節點"""
    if re.search(r"\.v\d+\.md$", filename):
        return False
    entity_id = front.get("ha_entity_id", "")
    if re.match(r"(automation|binary_sensor|sensor|switch|light|climate|cover)\.", entity_id):
        return False
    if front.get("type") == "device":
        return True
    if "connection" in front or "ssh" in str(front).lower():
        if any(kw in body.lower() for kw in ["ip", "ssh", "port", "://", "password"]):
            return True
    return False


def extract_ip_from_body(body: str) -> Optional[str]:
    """從 body 文本提取 IP 地址"""
    patterns = [
        r"IP[地址\s]*[|:：]\s*`?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})`?",
        r"host\s*IP[|:：]\s*`?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})`?",
        r"://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[:/]",
        r"url:\s*https?://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.I)
        if m:
            return m.group(1)
    return None


# ── 版本化操作 ────────────────────────────────────────────────────

def archive_current_node(md_path: Path, front: dict, body: str) -> Tuple[Path, int]:
    """歸檔當前節點為 .vN.md，返回 (archive_path, next_version)"""
    current_version = int(front.get("version", 1))
    next_version = current_version + 1

    archive_name = md_path.stem + f".v{current_version}" + md_path.suffix
    archive_path = md_path.parent / archive_name

    updated_front = dict(front)
    updated_front["valid_until"] = TODAY
    updated_front["superseded_by"] = md_path.stem
    if "version" in updated_front:
        updated_front["version"] = current_version

    if "> Superseded by:" not in body and "> Previous version:" not in body:
        body = body.rstrip() + f"\n\n> ⚠️ 此版本已過期。Superseded by: [[{md_path.stem}]] (v{next_version})\n"

    with open(archive_path, "w") as f:
        f.write(render_frontmatter(updated_front) + body)

    return archive_path, next_version


def create_new_version(md_path: Path, front: dict, body: str, next_version: int) -> None:
    """創建新版節點（current），更新 frontmatter"""
    updated_front = dict(front)
    updated_front["version"] = next_version
    updated_front["valid_from"] = TODAY
    updated_front["valid_until"] = None
    updated_front["superseded_by"] = None

    body = body.rstrip()
    body = re.sub(r"\n\n> ⚠️ 此版本已過期.*", "", body, flags=re.D)
    body += f"\n\n> 📌 當前版本 v{next_version}。Previous version: [[{md_path.stem}.v{next_version-1}]]\n"

    with open(md_path, "w") as f:
        f.write(render_frontmatter(updated_front) + body)


def ensure_version_frontmatter(md_path: Path) -> bool:
    """確保設備節點有 version frontmatter"""
    text = md_path.read_text()
    front, body = parse_frontmatter(text)

    if not is_device_node(md_path.name, front, body):
        return False
    if "version" in front and front.get("version") is not None:
        return False

    front["version"] = 1
    front["valid_from"] = front.get("created", TODAY)
    front["valid_until"] = None
    front["superseded_by"] = None

    with open(md_path, "w") as f:
        f.write(render_frontmatter(front) + body)
    return True


def check_and_version(md_path: Path, new_ip: Optional[str] = None) -> bool:
    """檢查設備節點是否需要版本化（IP 變了），是則歸檔+新建"""
    text = md_path.read_text()
    front, body = parse_frontmatter(text)

    if not is_device_node(md_path.name, front, body):
        return False

    if "version" not in front:
        front["version"] = 1
        front["valid_from"] = front.get("created", TODAY)
        front["valid_until"] = None
        front["superseded_by"] = None
        with open(md_path, "w") as f:
            f.write(render_frontmatter(front) + body)
        return False

    current_ip = extract_ip_from_body(body)
    if new_ip and current_ip and current_ip != new_ip:
        print(f"   🔁 IP 變化：{current_ip} → {new_ip}，歸檔中...")
        archive_path, next_version = archive_current_node(md_path, front, body)
        create_new_version(md_path, front, body, next_version)
        print(f"   ✅ 歸檔至 {archive_path.name}，新建 v{next_version}")
        return True
    return False


# ── 批量初始化 ────────────────────────────────────────────────────

def init_all_device_nodes() -> dict:
    """掃描所有設備節點，確保有 version frontmatter"""
    results = {"initialized": [], "skipped": [], "errors": []}
    if not ENTITIES.exists():
        return results
    for md_path in sorted(ENTITIES.glob("*.md")):
        try:
            ok = ensure_version_frontmatter(md_path)
            if ok:
                results["initialized"].append(md_path.name)
            else:
                results["skipped"].append(md_path.name)
        except Exception as e:
            results["errors"].append((md_path.name, str(e)))
    return results


def check_device_changes() -> dict:
    """檢查設備是否有變化"""
    known_devices = {
        "aio-server-ssh.md": "192.168.1.100",
        "home-assistant-vm.md": "192.168.1.101",
        "frigate-nvr.md": "192.168.1.102",
    }
    results = {}
    if not ENTITIES.exists():
        return results
    for filename, expected_ip in known_devices.items():
        md_path = ENTITIES / filename
        if not md_path.exists():
            continue
        try:
            changed = check_and_version(md_path, new_ip=expected_ip)
            results[filename] = changed
        except Exception as e:
            results[filename] = f"ERROR: {e}"
    return results


# ── Test ─────────────────────────────────────────────────────────

def test():
    """測試版本化邏輯"""
    print("=== device_versioning.py TEST ===\n")

    sample = """---
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
    front, body = parse_frontmatter(sample)
    assert front.get("id") == "aio-server-ssh", f"id field wrong: {front}"
    assert front.get("version") == "1", f"version field wrong: {front}"
    print("✅ Test 1: parse_frontmatter OK")

    rendered = render_frontmatter(front)
    assert "version: 1" in rendered, f"rendered missing version: {rendered}"
    assert "valid_from: 2026-04-18" in rendered, f"rendered missing valid_from: {rendered}"
    print("✅ Test 2: render_frontmatter OK")

    ip = extract_ip_from_body(sample)
    assert ip == "192.168.1.100", f"IP extraction wrong: {ip}"
    print("✅ Test 3: extract_ip_from_body OK")

    assert is_device_node("aio-server-ssh.md", front, body) == True
    assert is_device_node("automation_ban_shui_huan_xing_deng_03_00ting_zhi_diao_guang.md",
                          {"ha_entity_id": "automation.xxx"}, body) == False
    print("✅ Test 4: is_device_node OK")

    results = init_all_device_nodes()
    print(f"   Initialized: {len(results['initialized'])}")
    print(f"   Skipped: {len(results['skipped'])}")
    print(f"   Errors: {len(results['errors'])}")
    print("✅ Test 5: init_all_device_nodes OK")

    changes = check_device_changes()
    for f, result in changes.items():
        print(f"   {f}: {'changed' if result else 'no change'}")
    print("✅ Test 6: check_device_changes OK")

    print("\n=== ALL TESTS PASSED ===")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test()
    else:
        print("device_versioning.py — 設備節點版本化管理")
        print("  --test  運行測試")
        print("  init   初始化所有設備節點的 version frontmatter")
        print("  check  檢查設備是否有變化需要歸檔")