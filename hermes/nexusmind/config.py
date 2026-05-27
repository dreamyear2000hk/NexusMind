#!/usr/bin/env python3
"""
NexusMind Hermes 配置加載器
自動檢測 Hermes workspace + 加載 config.json
"""

import json
import os
from pathlib import Path

HERMES_DIR  = Path.home() / ".hermes"
WORKSPACE   = HERMES_DIR / "skills" / "nexusmind"
CONFIG_FILE = WORKSPACE / "config.json"

DEFAULT_WORKSPACE = str(HERMES_DIR)


def get_workspace() -> Path:
    """檢測 Hermes workspace 路徑"""
    ws = os.environ.get("NEXUSMIND_WORKSPACE")
    if ws:
        return Path(ws)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
            return Path(cfg.get("workspace", DEFAULT_WORKSPACE))
    return Path(DEFAULT_WORKSPACE)


def get_config() -> dict:
    """加載 NexusMind 配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return _default_config()


def _default_config() -> dict:
    return {
        "workspace": DEFAULT_WORKSPACE,
        "ha_url":    "http://localhost:8123",
        "ha_token":  "",
        "cron_time": "03:00",
        "devices":  [],
    }


def save_config(cfg: dict):
    """保存配置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def get_ha_token() -> str:
    """獲取 HA Token"""
    cfg   = get_config()
    token = cfg.get("ha_token", "") or os.environ.get("NEXUSMIND_HA_TOKEN", "")
    return token


def get_ha_url() -> str:
    """獲取 HA URL"""
    cfg = get_config()
    return cfg.get("ha_url", "") or os.environ.get("NEXUSMIND_HA_URL", "")


GRAPHS_DIR  = lambda: get_workspace() / "docs"
DATA_DIR    = lambda: get_workspace() / "data"
ENTITIES_DIR  = lambda: GRAPHS_DIR() / "entities"
EVENTS_DIR    = lambda: GRAPHS_DIR() / "events"
CONCEPTS_DIR  = lambda: GRAPHS_DIR() / "concepts"