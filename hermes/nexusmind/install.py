#!/usr/bin/env python3
"""
NexusMind Hermes 安裝腳本
自動創建目錄結構、配置文件、符號連結
"""

import json
import os
import shutil
import sys
from pathlib import Path

HERMES_DIR  = Path.home() / ".hermes"
WORKSPACE   = HERMES_DIR / "skills" / "nexusmind"
SKILL_DIR   = Path(__file__).parent.parent  # nexusmind/ 的父目錄

SUPPORTED_VERSION = "1.0.0"


def print_step(msg: str):
    print(f"\n{'='*50}")
    print(f"  {msg}")
    print("=" * 50)


def check_hermes():
    """檢查 Hermes 是否已安裝"""
    if not HERMES_DIR.exists():
        print(f"❌ Hermes 目錄不存在: {HERMES_DIR}")
        print("   請先安裝 Hermes Agent: https://hermes-agent.nousresearch.com/docs/")
        return False
    hermes_bin = HERMES_DIR.parent / "bin" / "hermes"
    if not hermes_bin.exists() and not shutil.which("hermes"):
        print(f"⚠️  Hermes CLI 未找到，請確認已正確安裝")
    print(f"✅ Hermes 目錄: {HERMES_DIR}")
    return True


def create_dirs():
    """創建 NexusMind 目錄結構"""
    dirs = [
        WORKSPACE / "docs" / "entities",
        WORKSPACE / "docs" / "events",
        WORKSPACE / "docs" / "concepts",
        WORKSPACE / "data",
        WORKSPACE / "scripts",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {d.relative_to(HERMES_DIR)}")
    return True


def create_config():
    """創建預設配置文件"""
    config = {
        "workspace":  str(HERMES_DIR),
        "ha_url":     "http://localhost:8123",
        "ha_token":   "",
        "cron_time":  "03:00",
        "devices":    [],
        "version":    SUPPORTED_VERSION,
    }
    cfg_file = WORKSPACE / "config.json"
    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cfg_file, "w") as f:
        json.dump(config, f, indent=2)
    print(f"   ✅ config.json")


def setup_hermes_integration():
    """通知 Hermes 關於 NexusMind skill"""
    skills_dir = HERMES_DIR / "skills"
    nexus_skill_dir = skills_dir / "nexusmind"

    # 檢查是否已存在（避免覆蓋用戶數據）
    if nexus_skill_dir.exists() and (nexus_skill_dir / "SKILL.md").exists():
        print(f"   ⚠️  NexusMind skill 已存在: {nexus_skill_dir}")
        print(f"   💡  可直接使用 /nexusmind 命令，或運行 hermes skills install 重新安裝")
        return False

    # 創建符號連結（可選）
    # 注意：用戶可選擇直接複製或創建連結
    print(f"\n   📦 NexusMind Skill 目錄: {SKILL_DIR.parent / 'nexusmind'}")
    print(f"   💡  Hermes 自動發現: {skills_dir}/nexusmind/SKILL.md")
    return True


def create_docs_templates():
    """複製文檔模板"""
    src_docs = SKILL_DIR.parent / "nexusmind" / "docs"
    dst_docs = WORKSPACE / "docs"
    templates = ["entity_template.md", "event_template.md", "concept_template.md"]

    for t in templates:
        src = src_docs / t
        if src.exists():
            shutil.copy2(src, dst_docs / t)
            print(f"   ✅ {t}")


def print_usage():
    """打印使用說明"""
    print("""
╔══════════════════════════════════════════════════════════╗
║          NexusMind — Hermes 安裝完成！                 ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  📦 已安裝模組:                                          ║
║     • intent_classifier.py  — 意圖路由                   ║
║     • memory_query.py       — 記憶查詢                   ║
║     • device_versioning.py  — 設備版本化                 ║
║     • forgetting.py         — 遺忘算法                   ║
║                                                          ║
║  🎯 使用方式:                                            ║
║     /nexusmind status       — 查看記憶系統狀態           ║
║     /nexusmind check-devices — 檢查設備版本             ║
║     /nexusmind forget --dry-run — 預覽遺忘結果           ║
║     /nexusmind forget       — 執行遺忘                   ║
║                                                          ║
║  🧪 測試:                                                ║
║     cd ~/.hermes/skills/nexusmind                        ║
║     python3 scripts/intent_classifier.py                 ║
║     python3 scripts/device_versioning.py --test         ║
║                                                          ║
║  📁 配置:                                                ║
║     ~/.hermes/skills/nexusmind/config.json               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")


def main():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          NexusMind — Hermes Agent 適配層                ║
║          智脈引擎 v{SUPPORTED_VERSION} Hermes 安裝向導                ║
╚══════════════════════════════════════════════════════════╝
""")

    print_step("1. 檢查 Hermes 環境")
    if not check_hermes():
        sys.exit(1)

    print_step("2. 創建目錄結構")
    create_dirs()

    print_step("3. 生成配置文件")
    create_config()

    print_step("4. 複製文檔模板")
    create_docs_templates()

    print_step("5. Hermes 整合")
    setup_hermes_integration()

    print_step("安裝完成！")
    print_usage()


if __name__ == "__main__":
    main()