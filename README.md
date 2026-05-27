# NexusMind — AI Memory Engine / 智脈引擎

> Give your AI Agent a memory that truly lasts | 讓你的 AI 真正記住一切

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**[English](#english) · [中文](#中文) · [Quick Start](#quick-start--快速開始) · [Architecture](#architecture--架構) · [API](#api-reference--api-參考)**

---

## 中文 Chinese

### 這是什麼？

NexusMind（智脈引擎）是一套 **AI 個人記憶管理系統**，基於 Karpathy 的 LLM-Wiki Pattern 設計。專為 AI Agent 打造，讓 AI 不再每次從零開始。

**支援 OpenClaw 和 Hermes 雙框架** — 統一代碼庫，通過 framework.py 自動適配。

### 核心功能

| 功能 | 說明 |
|------|------|
| **意圖路由** | 每條消息自動分類（fact/alert/memory/reason/skill/unknown），決定如何記憶 |
| **設備版本化** | cron 追蹤設備配置變更，自動保留歷史版本 |
| **遺忘算法** | 每天自動清理低價值記憶，保持系統輕量 |
| **零外部依賴** | 純 Python 標準庫 |
| **雙框架支援** | OpenClaw + Hermes，統一代碼庫 |
| **可選 HA** | 可連接 Home Assistant，也可純本地運行 |

### 熱度公式

```
W  = W_time * (1 + W_freq) * W_affinity
   = e^(-age/T) * (1 + log(1 + access_count)) * (1 + affinity)
```

| W 範圍 | 等級 |
|--------|------|
| >= 0.8 | 核心昇級候選 |
| 0.3-0.8 | 長期記憶（保留）|
| 0-0.3 | 短期記憶（30天後刪除）|

### 安裝

```bash
# OpenClaw：用 .skill 文件
cp NexusMind.skill ~/.openclaw/workspace/skills/

# Hermes：克隆到 skills 目錄
cp -r hermes/nexusmind ~/.hermes/skills/

# 或從源碼安裝（自動檢測框架）
python3 install.py
```

---

## English

### What is NexusMind?

NexusMind is an **AI personal memory management system** inspired by Karpathy's LLM-Wiki Pattern. Built for AI Agents — so your AI never starts from scratch again.

**Supports OpenClaw and Hermes dual frameworks** — unified codebase with automatic framework detection.

### Key Features

| Feature | Description |
|---------|-------------|
| **Intent Routing** | Auto-classifies every message (fact/alert/memory/reason/skill/unknown) |
| **Device Versioning** | Cron tracks device config changes, auto-archives history |
| **Forgetting Algorithm** | Daily auto-prunes low-value memories |
| **Zero Dependencies** | Pure Python standard library |
| **Dual Framework** | OpenClaw + Hermes with unified code |
| **Optional HA** | Can connect Home Assistant, or run pure local |

### Install

```bash
# OpenClaw: use .skill file
cp NexusMind.skill ~/.openclaw/workspace/skills/

# Hermes: clone to skills directory
cp -r hermes/nexusmind ~/.hermes/skills/
```

---

## Unified Architecture / 統一架構

```
NexusMind/
├── scripts/                  ← 核心邏輯（OpenClaw + Hermes 共享）
│   ├── framework.py          ← 框架自動檢測（唯一需要知道框架的地方）
│   ├── intent_classifier.py  ← 核心意圖分類（無框架代碼）
│   ├── memory_query.py       ← 核心查詢引擎
│   ├── device_versioning.py  ← 核心版本化
│   └── forgetting.py         ← 核心遺忘算法
│
├── openclaw/                 ← OpenClaw wrapper
│   └── NexusMind.skill/      ← .skill 文件 + 符號鏈接 → scripts/
│
├── hermes/                   ← Hermes wrapper
│   └── nexusmind/           ← Hermes 適配層 + 符號鏈接 → scripts/
│
├── tests/                    ← 統一測試
│   ├── test_intent.py
│   ├── test_device_versioning.py
│   └── test_forgetting.py
│
└── docs/                     ← 文檔模板
```

### framework.py 自動檢測邏輯

```python
from framework import get_workspace, get_graphs_dir, get_ha_token

# 自動返回正確路徑，無需判斷框架
workspace  = get_workspace()   # OpenClaw: ~/.openclaw/workspace
                                # Hermes:  ~/.hermes/skills/nexusmind
graphs_dir = get_graphs_dir()   # OpenClaw: docs/
                                # Hermes:  skills/nexusmind/docs/
ha_token   = get_ha_token()     # 自動讀取對應 config
```

### OpenClaw 與 Hermes 差異

| 項目 | OpenClaw | Hermes |
|------|----------|--------|
| Workspace | `~/.openclaw/workspace` | `~/.hermes/skills/nexusmind` |
| Memory Files | `docs/{entities,events,concepts}` | `skills/nexusmind/docs/{entities,events,concepts}` |
| Config | `data/nexusmind/config.json` | `skills/nexusmind/config.json` |
| State | `data/nexusmind/forgetting_state.json` | `data/forgetting_state.json` |
| Skills Dir | `skills/` | `~/.hermes/skills/` |
| 检测方式 | `OPENCLAW` env var | `HERMES_AGENT` env var |

---

## 組件說明

| 模組 | 觸發方式 | 作用 |
|------|---------|------|
| **intent_classifier.py** | 每條消息實時 | 分類意圖，決定召回策略 |
| **memory_query.py** | 被動查詢 | 從 graph 檢索事實/關係/概念 |
| **device_versioning.py** | cron 觸發 | 設備IP變了自動歸檔歷史版本 |
| **forgetting.py** | cron 每天03:00 | 清理 W < 0.3 的低價值記憶 |

### 意圖分類決策樹

```
輸入消息
    |
    v
category = fact ? ----yes----> recall = keyword（精確匹配）
    |
    no
    |
    v
category = alert ? ----yes----> recall = keyword
    |
    no
    |
    v
category = memory ? ----yes----> recall = semantic（語義搜索）
    |
    no
    |
    v
category = reason ? ----yes----> recall = semantic
    |
    no
    |
    v
category = skill ? ----yes----> recall = exact（精確匹配）
    |
    no
    |
    v
category = unknown
    |
    +-- task_intent = unknown ----->  跳過（問候/純噪聲）
    +-- task_intent = learning --->  送 LLM 處理
    +-- task_intent = skill ------>  送 LLM 處理
```

---

## Quick Start / 快速開始

```python
# Intent Classification / 意圖分類
from scripts.intent_classifier import route

result = route("老闆在家嗎")
# {"category": "fact", "task_intent": "fact", "recall_strategy": "keyword"}

result = route("什麼是 Karpathy Pattern")
# {"category": "unknown", "task_intent": "learning", "recall_strategy": "semantic"}

# Query Memory / 查詢記憶
from scripts.memory_query import query
r = query("上次那個問題怎麼解決")
# {"intent": "memory", "answer": "...", "found": 3}
```

---

## API Reference / API 參考

### intent_classifier.route(text)

```python
result = route("Bigcore0溫度多少")
# {"category": "alert", "task_intent": "fact", "recall_strategy": "keyword"}
```

| 返回欄位 | 說明 |
|---------|------|
| category | 意圖類別（fact/alert/memory/reason/skill/unknown） |
| task_intent | 任務意圖（fact/learning/skill/unknown） |
| recall_strategy | 召回策略（keyword/semantic/exact） |

### memory_query.query(text, intent?)

```python
r = query("上次那個問題怎麼解決")
# {"intent": "memory", "answer": "...", "found": 3}
```

### device_versioning.check_device_changes()

```python
changes = check_device_changes()
# {"device1.md": False, "device2.md": True}
```

### forgetting.run_dream_cycle(dry_run=False)

```python
result = run_dream_cycle(dry_run=True)
# {"purged": 0, "upgraded": 0, "total": 3958}
```

---

## Configuration / 配置

### OpenClaw
```json
{
  "workspace": "~/.openclaw/workspace",
  "ha_url": "http://localhost:8123",
  "ha_token": "your_token_here",
  "cron_time": "03:00",
  "devices": []
}
```

### Hermes
```json
{
  "workspace": "~/.hermes",
  "ha_url": "http://localhost:8123",
  "ha_token": "your_token_here",
  "cron_time": "03:00",
  "devices": []
}
```

---

## License / 許可證

MIT License — Free to use, modify, commercialize / 可自由使用、修改、商業化

## Acknowledgements / 致謝

- **Karpathy** — [LLM-Wiki Pattern](https://github.com/karpathy/llm-wiki) Theory
- **OpenClaw** — Agent Framework
- **Hermes** — Agent Framework
- **Mem0** — Intelligent Memory System Reference