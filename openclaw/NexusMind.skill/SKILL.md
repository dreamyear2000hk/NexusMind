---
name: NexusMind
description: |
  NexusMind — AI 個人記憶引擎（智脈引擎）
  
  三層記憶系統：意圖路由 · 設備版本化 · 遺忘機制
  
  適用場景：智能家居、個人助理、數字分身記憶管理
  
  安裝：把 .skill 文件放到 ~/.openclaw/workspace/skills/，然後運行 install.py
---

# NexusMind — 智脈引擎

> 你的 AI 不再是「每次從零開始」

## 核心理念

NexusMind 是一套給 AI Agent 用的**個人長期記憶管理系統**。基於 Karpathy 提出的 LLM-Wiki Pattern，結合三層記憶架構：

```
實時意圖路由（Intent Router）
    ↓ 分類消息，決定如何記憶
設備版本化（Device Versioning）
    ↓ 追蹤設備狀態變化，保留歷史版本
遺忘算法（Forgetting Algorithm）
    ↓ 自動清理低價值記憶，保持系統輕量
```

## 快速開始

```bash
# 1. 安裝（把 NexusMind.skill 放到 skills 目錄）
cp NexusMind.skill ~/.openclaw/workspace/skills/

# 2. 配置
python3 ~/.openclaw/workspace/skills/NexusMind/install.py

# 3. 完成，開始使用
# 在 OpenClaw 中，記憶系統自動啟動
```

## 三大核心模塊

### 1. 意圖路由（intent_classifier.py）

每條消息先經過意圖分類，決定如何處理：

| 意圖 | 類型 | 回憶策略 |
|------|------|---------|
| `fact` | 設備狀態/IP/配置查詢 | keyword（精確匹配）|
| `alert` | 溫度/異常/監控報警 | keyword |
| `memory` | 歷史對話/過去事件 | semantic（語義搜索）|
| `reason` | 設備關聯/自動化邏輯 | semantic |
| `skill` | 腳本執行/技能調用 | exact（精確匹配）|
| `unknown` | 問候/噪聲 | 跳過 |

```python
from intent_classifier import route

result = route("老闆在家嗎")
# result = {
#   "category": "fact",
#   "task_intent": "fact",
#   "recall_strategy": "keyword"
# }
```

### 2. 設備版本化（device_versioning.py）

設備節點（服務器/路由器/NAS）追蹤版本變更：

```
aio-server.md          ← 當前版本（valid_until=null）
aio-server.v1.md       ← 歷史版本（valid_until=2026-04-01）
aio-server.v2.md       ← 歷史版本（valid_until=2026-05-15）
```

每次 cron 運行自動檢測設備 IP/SSH 配置是否變更，自動歸檔舊版本。

### 3. 遺忘算法（forgetting.py）

記憶熱度公式：
```
W = W_time × (1 + W_freq) × W_affinity
  = e^(-age/τ) × (1 + log(1 + access_count)) × (1 + affinity)
```

| W 範圍 | 結果 |
|--------|------|
| ≥ 0.8 | 核心昇級候選 |
| 0.3–0.8 | 長期記憶（保留）|
| 0–0.3 | 短期記憶（30天後刪除）|

## 配置說明

配置文件：`~/.openclaw/workspace/data/nexusmind/config.json`

```json
{
  "workspace": "~/.openclaw/workspace",
  "ha_url": "http://localhost:8123",
  "ha_token": "",
  "cron_time": "03:00",
  "devices": []
}
```

## 依賴

- Python 3.10+
- 標準庫（無外部依賴）
- OpenClaw（可選 HA，不必須）

## 項目結構

```
NexusMind/
├── SKILL.md                    ← 本文件
├── README.md                   ← GitHub 首頁
├── install.py                  ← 安裝向導
├── config.py                   ← 配置加載器
├── scripts/
│   ├── intent_classifier.py    ← 意圖路由
│   ├── memory_query.py         ← 查詢引擎
│   ├── device_versioning.py    ← 設備版本化
│   └── forgetting.py           ← 遺忘算法
├── docs/
│   ├── entity_template.md      ← 設備節點模板
│   ├── event_template.md       ← 事件節點模板
│   └── concept_template.md     ← 概念節點模板
└── tests/
    └── test_intent.py          ← 意圖分類測試
```

## 許可證

MIT License

## 致謝

- Karpathy — LLM-Wiki Pattern 理論基礎
- OpenClaw — Agent 框架
- 深圳家智脈引擎 v2.0 — 原始實現
