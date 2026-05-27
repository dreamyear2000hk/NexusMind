# NexusMind — AI Memory Engine / 智脈引擎

> Give your AI Agent a memory that truly lasts | 讓你的 AI 真正記住一切

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**[English](#english) · [中文](#中文) · [Quick Start](#quick-start--快速開始) · [Architecture](#architecture--架構) · [API](#api-reference--api-參考)**

---

## 中文 Chinese

### 這是什麼？

NexusMind（智脈引擎）是一套 **AI 個人記憶管理系統**，基於 Karpathy 的 LLM-Wiki Pattern 設計。專為 AI Agent 打造，讓 AI 不再每次從零開始。

### 核心功能

| 功能 | 說明 |
|------|------|
| **意圖路由** | 每條消息自動分類（fact/alert/memory/reason/skill/unknown），決定如何記憶 |
| **設備版本化** | cron 追蹤設備配置變更，自動保留歷史版本 |
| **遺忘算法** | 每天自動清理低價值記憶，保持系統輕量 |
| **零外部依賴** | 純 Python 標準庫 |
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
| **Intent Routing** | Auto-classifies every message (fact/alert/memory/reason/skill/unknown) and decides how to remember |
| **Device Versioning** | Cron tracks device config changes, auto-archives history |
| **Forgetting Algorithm** | Daily auto-prunes low-value memories, keeps system lightweight |
| **Zero Dependencies** | Pure Python standard library |
| **Optional HA** | Can connect Home Assistant, or run pure local |

### Hotness Formula

```
W  = W_time * (1 + W_freq) * W_affinity
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

## Architecture / 架構

NexusMind 有三個核心模組，協作方式如下：

```
                    消息輸入 Message Input
                           |
                           v
            +----------------------------+
            |  intent_classifier.route() |
            |  category + task_intent +   |
            |  recall_strategy            |
            +----------------------------+
                     |    |    |    |
                     v    v    v    v
                  fact/ memory reason skill unknown
                  alert          /       \
                   |            |         |
                   v            v         +-- task=unknown  -->  跳過（問候/噪聲）
                keyword      semantic       |
                   |            |         +-- task=learning -->  送 Qwen LLM
                   |            |         |
                   |            |         +-- task=skill ----->  送 Qwen LLM
                   v            v
            +-----------------------------+
            |    memory_query.query()    |
            |  從 Graph Memory 檢索答案   |
            |  docs/entities/             |
            |  docs/events/              |
            |  docs/concepts/             |
            +-----------------------------+
                           |
     +---------------------+---------------------+
     |                     |                     |
     v                     v                     v
+-----------+    +------------------+    +------------------+
| device_   |    | cron: 每天一次   |    | cron: 每天 03:00  |
| versioning|    | memory_daily_    |    | forgetting.py     |
| .py       |    | sync.py         |    |                  |
|           |    |                 |    | W < 0.3 -> 刪除  |
| 設備IP變了 |    | 調用所有記憶模組 |    | W >= 0.8 -> 昇級 |
| -> 歸檔   |    |                  |    +------------------+
| .vN.md   |    +------------------+              |
|           |                                   |
+-----------+                                   |
     |                                          |
     v                                          v
  文檔歸檔                                  記憶清理
```

### 組件說明

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
    +-- task_intent = learning --->  送 Qwen LLM 處理
    +-- task_intent = skill ------>  送 Qwen LLM 處理
```

---

## Quick Start / 快速開始

```python
# Intent Classification / 意圖分類
from intent_classifier import route

result = route("老闆在家嗎")
# {"category": "fact", "task_intent": "fact", "recall_strategy": "keyword"}

result = route("什麼是 Karpathy Pattern")
# {"category": "unknown", "task_intent": "learning", "recall_strategy": "semantic"}

# Query Memory / 查詢記憶
from memory_query import query
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