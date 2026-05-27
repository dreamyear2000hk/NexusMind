#!/usr/bin/env python3
"""
framework.py — 框架自動檢測
NexusMind 統一架構：同時支持 OpenClaw 和 Hermes

自動檢測運行框架，返回正確的路徑配置。
所有核心腳本 import framework 自動獲得正確路徑。
"""

import os
from pathlib import Path
from typing import NamedTuple


class FrameworkPaths(NamedTuple):
    """框架路徑集合"""
    framework: str           # 'openclaw' | 'hermes' | 'unknown'
    workspace: Path          # 主 workspace 目錄
    graphs_dir: Path         # docs/ 圖譜目錄
    data_dir: Path           # data/ 數據目錄
    skills_dir: Path         # skills/ 技能目錄
    memory_dir: Path         # memory/ 記憶日誌目錄
    hermes_dir: Path         # ~/.hermes (Hermes 專用)
    config_file: Path        # config.json 路徑
    state_file: Path         # forgetting_state.json
    feedback_file: Path      # memory_feedback.json
    ha_url: str              # Home Assistant URL
    ha_token: str            # Home Assistant Token


def _detect_framework() -> str:
    """自動檢測運行框架"""
    # 優先：显式環境變量（最可靠，跨框架共用）
    fw = os.environ.get("NEXUSMIND_FRAMEWORK")
    if fw in ("openclaw", "hermes"):
        return fw
    if os.environ.get("HERMES_AGENT"):
        return "hermes"
    if os.environ.get("OPENCLAW"):
        return "openclaw"
    # 檢查目錄存在性
    hermes_skills = Path.home() / ".hermes" / "skills"
    openclaw_ws = Path.home() / ".openclaw" / "workspace"
    if hermes_skills.exists() and openclaw_ws.exists():
        return "openclaw"  # 保守默認
    if hermes_skills.exists():
        return "hermes"
    if openclaw_ws.exists():
        return "openclaw"
    return "openclaw"  # 默認值


def _openclaw_paths() -> FrameworkPaths:
    """OpenClaw 路徑配置"""
    ws = Path.home() / ".openclaw" / "workspace"
    cfg_file = ws / "data" / "nexusmind" / "config.json"
    # 嘗試從 config.json 讀取自定義 workspace
    if cfg_file.exists():
        import json
        with open(cfg_file) as f:
            cfg = json.load(f)
            custom = cfg.get("workspace", "")
            if custom and Path(custom).exists():
                ws = Path(custom)
    return FrameworkPaths(
        framework=str(ws / "data" / "nexusmind"),
        workspace=ws,
        graphs_dir=ws / "docs",
        data_dir=ws / "data",
        skills_dir=ws / "skills",
        memory_dir=ws / "memory",
        hermes_dir=Path.home() / ".hermes",
        config_file=cfg_file,
        state_file=ws / "data" / "nexusmind" / "forgetting_state.json",
        feedback_file=ws / "data" / "nexusmind" / "memory_feedback.json",
        ha_url=_read_ha_url(cfg_file) or "http://localhost:8123",
        ha_token=_read_ha_token(cfg_file) or "",
    )


def _hermes_paths() -> FrameworkPaths:
    """Hermes 路徑配置"""
    hermes_dir = Path.home() / ".hermes"
    ws = hermes_dir / "skills" / "nexusmind"
    cfg_file = ws / "config.json"
    return FrameworkPaths(
        framework="hermes",
        workspace=ws,
        graphs_dir=ws / "docs",
        data_dir=ws / "data",
        skills_dir=hermes_dir / "skills",
        memory_dir=hermes_dir / "memories",
        hermes_dir=hermes_dir,
        config_file=cfg_file,
        state_file=ws / "data" / "forgetting_state.json",
        feedback_file=ws / "data" / "memory_feedback.json",
        ha_url=_read_ha_url(cfg_file) or "http://localhost:8123",
        ha_token=_read_ha_token(cfg_file) or "",
    )


def _read_ha_url(cfg_file: Path) -> str:
    if not cfg_file.exists():
        return ""
    import json
    with open(cfg_file) as f:
        cfg = json.load(f)
    return cfg.get("ha_url", "") or os.environ.get("NEXUSMIND_HA_URL", "")


def _read_ha_token(cfg_file: Path) -> str:
    if not cfg_file.exists():
        return ""
    import json
    with open(cfg_file) as f:
        cfg = json.load(f)
    return cfg.get("ha_token", "") or os.environ.get("NEXUSMIND_HA_TOKEN", "")


# ── 全域單例（延遲計算）─────────────────────────────────────────────
_framework: str = _detect_framework()
_paths: FrameworkPaths = _openclaw_paths() if _framework == "openclaw" else _hermes_paths()


def get_framework() -> str:
    """返回當前框架名稱"""
    return _framework


def is_openclaw() -> bool:
    return _framework == "openclaw"


def is_hermes() -> bool:
    return _framework == "hermes"


def get_workspace() -> Path:
    """返回主 workspace 目錄"""
    return _paths.workspace


def get_graphs_dir() -> Path:
    """返回 docs/ 圖譜目錄"""
    return _paths.graphs_dir


def get_data_dir() -> Path:
    """返回 data/ 目錄"""
    return _paths.data_dir


def get_skills_dir() -> Path:
    """返回 skills/ 目錄"""
    return _paths.skills_dir


def get_memory_dir() -> Path:
    """返回 memory/ 記憶日誌目錄"""
    return _paths.memory_dir


def get_hermes_dir() -> Path:
    """返回 ~/.hermes 目錄"""
    return _paths.hermes_dir


def get_config_file() -> Path:
    """返回 config.json 路徑"""
    return _paths.config_file


def get_state_file() -> Path:
    """返回 forgetting_state.json 路徑"""
    return _paths.state_file


def get_feedback_file() -> Path:
    """返回 memory_feedback.json 路徑"""
    return _paths.feedback_file


def get_ha_url() -> str:
    """返回 HA URL"""
    return _paths.ha_url


def get_ha_token() -> str:
    """返回 HA Token"""
    return _paths.ha_token


# ── 快捷別名（向後兼容）─────────────────────────────────────────────
WORKSPACE   = get_workspace
GRAPHS_DIR  = get_graphs_dir
DATA_DIR    = get_data_dir
SKILLS_DIR  = get_skills_dir
MEMORY_DIR  = get_memory_dir
HERMES_DIR  = get_hermes_dir


if __name__ == "__main__":
    fw = get_framework()
    print(f"Framework: {fw}")
    print(f"Workspace: {get_workspace()}")
    print(f"Graphs:   {get_graphs_dir()}")
    print(f"Data:     {get_data_dir()}")
    print(f"Skills:   {get_skills_dir()}")
    print(f"HA URL:   {get_ha_url()}")
    print(f"Config:   {get_config_file()}")