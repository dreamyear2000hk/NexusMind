# NexusMind — 智脈引擎

> AI 個人記憶引擎，讓你的 AI Agent 真正記住一切

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 特性

- **意圖路由** — 自動分類消息（fact/alert/memory/reason/skill），決定如何記憶
- **設備版本化** — 追蹤設備配置變更，保留完整歷史
- **遺忘算法** — 自動清理低價值記憶，保持系統輕量（W = W_time × W_freq × W_affinity）
- **零外部依賴** — 純 Python 標準庫
- **可選 HA** — 可連接 Home Assistant，也可純本地運行

## 安裝（30秒完成）

### 方式一：直接下載 .skill 文件

```bash
# 把 NexusMind.skill 放到 OpenClaw skills 目錄
cp NexusMind.skill ~/.openclaw/workspace/skills/

# 運行安裝向導
python3 ~/.openclaw/workspace/skills/NexusMind/install.py
```

### 方式二：從源碼安裝

```bash
git clone https://github.com/your-repo/NexusMind.git
cd NexusMind
python3 install.py
```

## 快速開始

```python
# 意圖路由
from intent_classifier import route

result = route("老闆在家嗎")
# → {"category": "fact", "task_intent": "fact", "recall_strategy": "keyword"}

# 查詢記憶
from memory_query import query
r = query("上次那個問題怎麼解決")
# → {"intent": "memory", "answer": "...", "found": 3}
```

## 架構

```
┌─────────────────────────────────────────┐
│           每條消息輸入                    │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│     intent_classifier.route()           │
│  意圖分類 → task_intent → recall策略    │
└─────────────────┬───────────────────────┘
                  ▼
   ┌──────────────┼──────────────┐
   ▼              ▼              ▼
 fact/memory  reason/alert    skill/unknown
   │              │              │
   ▼              ▼              ▼
 keyword       semantic       exact
 召回           召回          召回
   │              │              │
   ▼              ▼              ▼
┌─────────────────────────────────────────┐
│     device_versioning.py                │
│     設備變更 → 版本化歸檔               │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│       forgetting.py (每天 03:00)        │
│   W < 0.3 → 刪除 | W 0.3-0.8 → 保留    │
│   W ≥ 0.8 → 核心昇級                   │
└─────────────────────────────────────────┘
```

## 配置

編輯 `~/.openclaw/workspace/data/nexusmind/config.json`：

```json
{
  "workspace": "~/.openclaw/workspace",
  "ha_url": "http://localhost:8123",
  "ha_token": "你的HA_TOKEN",
  "cron_time": "03:00",
  "devices": ["192.168.1.100", "192.168.1.101"]
}
```

## API 參考

### intent_classifier.route(text)

```python
result = route("Bigcore0溫度多少")
# {
#   "category": "alert",       # 意圖類別
#   "task_intent": "fact",     # 任務意圖
#   "recall_strategy": "keyword" # 回憶策略
# }
```

### memory_query.query(text, intent?)

```python
r = query("上次那個問題怎麼解決")
# {
#   "intent": "memory",
#   "answer": "...",
#   "source": "...",
#   "found": 3
# }
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

## 許可證

MIT License — 可自由使用、修改、商業化

## 致謝

- **Karpathy** — [LLM-Wiki Pattern](https://github.com/karpathy/llm-wiki) 理論基礎
- **OpenClaw** — Agent 框架
- **Mem0** — 智能記憶系統參考
