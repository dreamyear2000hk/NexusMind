---
title: "{{DEVICE_NAME}}"
tags: [device, hardware]
date: {{DATE}}
type: entity
connection:
  ip: "{{IP}}"
  ssh_port: {{SSH_PORT}}
  ssh_user: "{{USER}}"
  # ssh_password: 請使用環境變量或外部配置
status: active
valid_from: {{DATE}}
valid_until: null
---

## 基本信息

| 字段 | 值 |
|------|-----|
| 名稱 | {{DEVICE_NAME}} |
| IP | {{IP}} |
| SSH Port | {{SSH_PORT}} |
| 用途 | {{PURPOSE}} |

## 歷史版本

- v1 ({{DATE}}) — 初始版本

<!-- 變更記錄：版本號 / 日期 / 變更內容 -->
