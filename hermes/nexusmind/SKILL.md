---
name: nexusmind
description: >
  Use when the user asks about device status, IP addresses, network configuration,
  temperature sensors, or home infrastructure. Also activate for memory/knowledge
  queries like "上次", "曾经", "记得". Also use for automation logic questions
  like "哪个传感器联动" or "关系". Also use when the user says "AIO打卡" or
  asks about AI server temperatures. NexusMind is the personal memory engine for
  smart home and AI infrastructure management — intent routing, device versioning,
  and forgetting algorithm.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [memory, smart-home, automation, intent-routing]
    category: memory
    requires_toolsets: [terminal]
---

# NexusMind — 智脈引擎 (Memory Engine for Hermes Agent)

> Personal long-term memory management system for AI agents — intent routing, device versioning, and forgetting algorithm.

## 當前台詞

NexusMind activates when the user asks about:
- **Device status**: "老闆在家嗎", "HA在線嗎", "玄關燈開嗎"
- **Temperature/environment**: "AIO溫度如何", "Bigcore0溫度多少", "室內溫度"
- **IP/config queries**: "IP是什麼", "密碼多少", "在哪裡"
- **History/memory**: "上次怎麼解決", "曾經做過", "記得"
- **Automation/relationships**: "哪個傳感器聯動", "客廳和什麼關係"
- **Skill/script execution**: "生成新聞", "執行腳本", "配置"
- **AIO check-in**: "AIO打卡"

## 核心模塊

### 1. Intent Router (意圖路由)

每條消息先經意圖分類，決定如何處理：

| Intent | 類型 | 召回策略 |
|--------|------|---------|
| `fact` | 設備狀態/IP/配置查詢 | keyword 精確匹配 |
| `alert` | 溫度/異常/監控報警 | keyword |
| `memory` | 歷史對話/過去事件 | semantic 語義搜索 |
| `reason` | 設備關聯/自動化邏輯 | semantic |
| `skill` | 腳本執行/技能調用 | exact 精確匹配 |
| `unknown` | 問候/噪聲 | 跳過 |

### 2. Device Versioning (設備版本化)

設備節點（伺服器/路由器/NAS）追蹤版本變更：
- 每當設備 IP/SSH 配置變更，自動歸檔舊版本到 `.vN.md`
- 新版本作為 current，實現完整可溯源的版本鏈
- 觸發鉤子：cron job 或手動 `/nexusmind check-devices`

### 3. Forgetting Algorithm (遺忘算法)

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

## 使用方式

### 意圖路由
```python
from scripts.intent_classifier import route

result = route("老闆在家嗎")
# result = {
#   "category": "fact",
#   "task_intent": "fact",
#   "recall_strategy": "keyword"
# }
```

### 記憶查詢
```python
from scripts.memory_query import query

r = query("Bigcore0溫度多少")
print(r["answer"])
```

### 設備版本檢查
```bash
python3 scripts/device_versioning.py --test
python3 scripts/device_versioning.py init
```

### 遺忘評估
```bash
python3 scripts/forgetting.py --dry-run  # 預覽
python3 scripts/forgetting.py              # 執行
```

## 命令

- `/nexusmind status` — 顯示記憶系統狀態
- `/nexusmind check-devices` — 檢查設備版本化
- `/nexusmind forget --dry-run` — 預覽遺忘演算法結果
- `/nexusmind forget` — 執行遺忘

## 配置

配置文件：`~/.hermes/skills/nexusmind/config.json`

```json
{
  "workspace": "~/.hermes",
  "ha_url": "http://localhost:8123",
  "ha_token": "",
  "cron_time": "03:00",
  "devices": []
}
```

## 依賴

- Python 3.10+
- 標準庫（無外部依賴）
- Hermes Agent framework

## 與 OpenClaw 版本差異

| 模組 | OpenClaw 路徑 | Hermes 路徑 |
|------|--------------|------------|
| Workspace | `~/.openclaw/workspace` | `~/.hermes` |
| Memory Files | `docs/` | `skills/nexusmind/docs/` |
| Config | `data/nexusmind/config.json` | `skills/nexusmind/config.json` |
| Skills Dir | `skills/` | `~/.hermes/skills/` |

Hermes 版本將所有 NexusMind 檔案隔離在 `~/.hermes/skills/nexusmind/` 目錄下，不污染 Hermes 全域 workspace。