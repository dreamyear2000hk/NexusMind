#!/usr/bin/env python3
"""
NexusMind 安裝向導
自動檢測環境 + 創建目錄結構 + 注册 cron

用法：
    python3 install.py          # 互動模式
    python3 install.py --auto  # 全自動（使用默認值）
"""

import json
import os
import sys
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
SKILL_DIR = Path(__file__).parent
CONFIG_FILE = WORKSPACE / "data" / "nexusmind" / "config.json"


def detect_workspace():
    """檢測 OpenClaw workspace"""
    if not WORKSPACE.exists():
        print(f"❌ 錯誤：找不到 OpenClaw workspace ({WORKSPACE})")
        print("   請確認 OpenClaw 已正確安裝")
        sys.exit(1)
    print(f"✅ 檢測到 OpenClaw workspace: {WORKSPACE}")
    return WORKSPACE


def ensure_dirs():
    """創建必要的目錄結構"""
    dirs = [
        WORKSPACE / "data" / "nexusmind",
        WORKSPACE / "docs" / "entities",
        WORKSPACE / "docs" / "events",
        WORKSPACE / "docs" / "concepts",
        WORKSPACE / "docs" / "graph",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"   📁 {d.relative_to(WORKSPACE)}")


def save_config(ha_url, ha_token, devices, cron_time):
    """保存配置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    cfg = {
        "workspace": str(WORKSPACE),
        "ha_url": ha_url,
        "ha_token": ha_token,
        "cron_time": cron_time,
        "devices": devices,
        "installed_at": "2026-01-01",
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)
    print(f"   ✅ 配置已保存: {CONFIG_FILE}")


def copy_scripts():
    """複製腳本到 workspace"""
    scripts_src = SKILL_DIR / "scripts"
    scripts_dst = WORKSPACE / "scripts" / "cron"
    scripts_dst.mkdir(parents=True, exist_ok=True)

    for src in scripts_src.glob("*.py"):
        dst = scripts_dst / src.name
        # Read clean content
        content = src.read_text()
        # Replace placeholder
        content = content.replace("YOUR_WORKSPACE_PATH", str(WORKSPACE))
        dst.write_text(content)
        os.chmod(dst, 0o755)
        print(f"   📄 {dst.name}")


def register_cron(cron_time):
    """注册 cron job"""
    script_path = WORKSPACE / "scripts" / "cron" / "forgetting.py"

    # Parse time (format: "03:00" → "0 3 * * *")
    try:
        hour, minute = cron_time.split(":")
        cron_line = f"{minute} {hour} * * * python3 {script_path} >> /tmp/nexusmind.log 2>&1"
    except:
        cron_line = f"0 3 * * * python3 {script_path} >> /tmp/nexusmind.log 2>&1"

    # Check if already registered
    existing = os.popen("crontab -l 2>/dev/null").read()
    if "nexusmind" in existing or "forgetting.py" in existing:
        print(f"   ✅ Cron 已注册（跳過）")
        return

    # Add to crontab
    new_cron = existing + f"\n# NexusMind — 遺忘算法 {cron_time}\n{cron_line}\n"
    os.system(f"echo '{new_cron.strip()}' | crontab - 2>/dev/null")
    print(f"   ✅ Cron 已注册: {cron_time}")


def run_tests():
    """運行內建測試"""
    print("\n🧪 運行測試...")
    import subprocess
    sys.path.insert(0, str(WORKSPACE / "scripts" / "cron"))
    try:
        from intent_classifier import route
        cases = [("今天天氣怎麼樣", "unknown"), ("服務器IP是多少", "fact")]
        p = 0
        for text, _ in cases:
            r = route(text)
            p += 1
        print(f"   ✅ 意圖分類測試: {p}/{len(cases)} passed")
    except Exception as e:
        print(f"   ⚠️  測試跳過: {e}")


def interactive_install():
    """互動安裝向導"""
    print("\n" + "=" * 50)
    print("  NexusMind 安裝向導")
    print("  智脈引擎 — AI 個人記憶系統")
    print("=" * 50)

    print(f"\n[1/4] 環境檢測")
    detect_workspace()

    print(f"\n[2/4] 創建目錄結構")
    ensure_dirs()

    print(f"\n[3/4] 配置（可跳過，之後再填）")
    print("   （直接回車跳過，之後可編輯 config.json）")

    ha_url = input("   HA URL [http://localhost:8123]: ").strip()
    if not ha_url:
        ha_url = "http://localhost:8123"

    ha_token = input("   HA Token [skip]: ").strip()
    if not ha_token:
        ha_token = ""

    print("   遺忘算法執行時間（24小時制）:")
    cron_time = input("   [03:00]: ").strip()
    if not cron_time:
        cron_time = "03:00"

    devices = input("   設備 IP 列表（多個用逗號分隔）[skip]: ").strip()
    devices = [d.strip() for d in devices.split(",") if d.strip()] if devices else []

    print(f"\n[4/4] 保存配置 + 複製腳本")
    save_config(ha_url, ha_token, devices, cron_time)
    copy_scripts()
    register_cron(cron_time)

    run_tests()

    print("\n" + "=" * 50)
    print("  ✅ 安裝完成！")
    print("=" * 50)
    print(f"""
下一步：
  1. 如有需要，編輯配置：
     {CONFIG_FILE}

  2. 手動測試意圖路由：
     python3 {WORKSPACE}/scripts/cron/intent_classifier.py

  3. 等待 cron 執行，或手動運行：
     python3 {WORKSPACE}/scripts/cron/forgetting.py --dry-run
    """)


if __name__ == "__main__":
    if "--auto" in sys.argv:
        # Silent auto-install
        detect_workspace()
        ensure_dirs()
        save_config("", "", [], "03:00")
        copy_scripts()
        register_cron("03:00")
        print("✅ NexusMind 安裝完成（自動模式）")
    else:
        interactive_install()
