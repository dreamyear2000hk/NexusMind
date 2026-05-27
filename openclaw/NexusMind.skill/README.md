# NexusMind — AI Memory Engine / 智脈引擎

> Give your AI Agent a memory that truly lasts | 讓你的 AI 真正記住一切

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**[English](#english) · [中文](#中文) · [Quick Start](#quick-start--快速開始) · [API](#api-reference--api-參考)**

---

## 中文 Chinese

### 這是什麼？

NexusMind（智脈引擎）是一套 **AI 個人記憶管理系統**，基於 Karpathy 的 LLM-Wiki Pattern 設計。專為 AI Agent 打造，讓 AI 不再每次從零開始。

### 核心功能

| 功能 | 說明 |
|------|------|
| **意圖路由** | 自動分類消息（fact/alert/memory/reason/skill），決定如何記憶 |
| **設備版本化** | 追蹤設備配置變更，自動保留歷史版本 |
| **遺忘算法** | 自動清理低價值記憶，保持系統輕量 |
| **零外部依賴** | 純 Python 標準庫 |
| **可選 HA** | 可連接 Home Assistant，也可純本地運行 |

### 熱度公式

```
W = W_time * (1 + W_freq) * W_affinity
  = e^(-age/T) * (1 + log(1 + access_count)) * (1 + affinity)
```

| W 範圍 | 等級 |
|--------|------|
| >= 0.8 | 核心昇級候選 |
| 0.3-0.8 | 長期記憶（保留）|
| 0-0.3 | 短期記憶（30天後刪除）|

### 安裝

```bash
# 方式一：直接使用 .skill 文件
cp NexusMind.skill ~/.openclaw/workspace/skills/

# 方式二：從源碼
git clone https://github.com/dreamyear2000hk/NexusMind.git
cd NexusMind
python3 install.py
```

---

## English

### What is NexusMind?

NexusMind is an **AI personal memory management system** inspired by Karpathy's LLM-Wiki Pattern. Built for AI Agents — so your AI never starts from scratch again.

### Key Features

| Feature | Description |
|---------|-------------|
| **Intent Routing** | Auto-classifies messages (fact/alert/memory/reason/skill) and decides how to remember |
| **Device Versioning** | Tracks device config changes, auto-archives history |
| **Forgetting Algorithm** | Auto-prunes low-value memories, keeps system lightweight |
| **Zero Dependencies** | Pure Python standard library |
| **Optional HA** | Can connect Home Assistant, or run pure local |

### Hotness Formula

```
W = W_time * (1 + W_freq) * W_affinity
  = e^(-age/T) * (1 + log(1 + access_count)) * (1 + affinity)
```

| W Range | Result |
|---------|--------|
| >= 0.8 | Core upgrade candidate |
| 0.3-0.8 | Long-term memory (keep) |
| 0-0.3 | Short-term memory (delete after 30 days) |

### Install

```bash
# Method 1: Use .skill file directly
cp NexusMind.skill ~/.openclaw/workspace/skills/

# Method 2: From source
git clone https://github.com/dreamyear2000hk/NexusMind.git
cd NexusMind
python3 install.py
```

---

## Quick Start / 快速開始

```python
# Intent Classification / 意圖分類
from intent_classifier import route

result = route("老闆在家嗎")
# {"category": "fact", "task_intent": "fact", "recall_strategy": "keyword"}

# Query Memory / 查詢記憶
from memory_query import query
r = query("上次那個問題怎麼解決")
# {"intent": "memory", "answer": "...", "found": 3}
```

---

## Architecture / 架構

```
Message Input
       |
       v
intent_classifier.route()
  Category -> Task Intent -> Recall Strategy
       |
       v
  +------------+-------------+
  |            |             |
  v            v             v
fact/memory reason/skill  unknown
  |            |             |
  v            v             v
keyword     semantic      exact
  |            |             |
  v            v             v
device_versioning.py      |
  Device change -> archive  |
       |                    v
       v                    v
  forgetting.py (daily 03:00)
  W < 0.3 -> delete
```

---

## API Reference / API 參考

### intent_classifier.route(text)

```python
result = route("Bigcore0溫度多少")
# {"category": "alert", "task_intent": "fact", "recall_strategy": "keyword"}
```

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

```json
{
  "workspace": "~/.openclaw/workspace",
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
- **Mem0** — Intelligent Memory System Reference