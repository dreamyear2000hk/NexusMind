#!/usr/bin/env python3
"""
NexusMind 配置加載器
自動檢測 OpenClaw workspace + 加載 config.json
"""

import json
import os
from pathlib import Path

# 預設路徑
DEFAULT_WORKSPACE = Path.home() / ".openclaw" / "workspace"
CONFIG_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "nexusmind" / "config.json"


def get_workspace():
    """檢測 OpenClaw workspace 路徑"""
    ws = os.environ.get("NEXUSMIND_WORKSPACE")
    if ws:
        return Path(ws)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
            return Path(cfg.get("workspace", str(DEFAULT_WORKSPACE)))
    return DEFAULT_WORKSPACE


def get_config():
    """加載 NexusMind 配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return _default_config()


def _default_config():
    return {
        "workspace": str(DEFAULT_WORKSPACE),
        "ha_url": "",
        "ha_token": "",
        "cron_time": "03:00",
        "devices": [],
    }


def save_config(cfg):
    """保存配置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.parent.chmod(0o700)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    # 保護配置文件
    os.chmod(CONFIG_FILE, 0o600)


def get_ha_token():
    """獲取 HA Token（優先順序：config > 環境變量）"""
    cfg = get_config()
    token = cfg.get("ha_token", "") or os.environ.get("NEXUSMIND_HA_TOKEN", "")
    return token


def get_ha_url():
    """獲取 HA URL"""
    cfg = get_config()
    return cfg.get("ha_url", "") or os.environ.get("NEXUSMIND_HA_URL", "")


# ── 快捷路徑 ───────────────────────────────────────────────────────

WORKSPACE = get_workspace
GRAPHS_DIR = lambda: get_workspace() / "docs"
DATA_DIR = lambda: get_workspace() / "data"
STATE_FILE = lambda: DATA_DIR() / "nexusmind" / "forgetting_state.json"
FEEDBACK_FILE = lambda: DATA_DIR() / "nexusmind" / "memory_feedback.json"
ENTITIES_DIR = lambda: GRAPHS_DIR() / "entities"
EVENTS_DIR = lambda: GRAPHS_DIR() / "events"
CONCEPTS_DIR = lambda: GRAPHS_DIR() / "concepts"
