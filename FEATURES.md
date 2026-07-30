# 市面桌宠功能对照与本项目取舍

调研对象大致包括：Shimeji 系、Live2D 桌宠（tools_live2D / Live2DPet / Pelr / Resona）等。

## 已借鉴并落地

| 功能 | 市面常见做法 | 本项目 |
|------|-------------|--------|
| 分层立绘 / 模型热换 | Live2D model3、多角色 JSON | `characters/` + `variants/anime|pixel` 分层 PNG |
| 动作 / 表情链 | 情绪状态机、motion 队列 | `animations.json` 关键帧 + `chains` 动作链 |
| AI 对话 | OpenAI 兼容 | 已有，模型/Base URL 可换 |
| 剪贴板 | 历史 30 条、搜索、恢复 | `ClipboardService` + 面板 + 角色台词反应 |
| 日程 / TODO | 日程提醒、番茄钟 | 每日/间隔日程 + 喝水/护眼/休息健康提醒 |
| 空闲状态 | 活跃/空闲/睡眠 | 空闲瞌睡、醒来 stretch 链、随机 idle |
| 注视鼠标 | Live2D 眼球跟踪 | 头/眼骨骼 look |

## 值得后续借鉴（未做或轻量预留）

| 功能 | 价值 | 备注 |
|------|------|------|
| **番茄钟** | 学习场景强 | 可挂在日程面板旁，进度条气泡 |
| **系统监控** | CPU/内存告警互动 | 复制反应同套路即可 |
| **全局热键** | 不抢焦点唤出 | Qt 全局快捷键或系统托盘 |
| **便签** | 与剪贴板互补 | 轻量 JSON 即可 |
| **穿透点击** | 不挡操作 | Win 下 `WS_EX_TRANSPARENT` |
| **好感度 / 养成** | 粘性高 | 需存档与数值平衡 |
| **TTS / 口型** | 沉浸感 | 依赖外置语音服务 |
| **屏幕感知 / 截屏 AI** | “看你在干什么” | 隐私敏感，需明确开关 |
| **物理碰撞 / 爬窗** | Shimeji 经典 | 工作量大，可作彩蛋 |
| **MCP / Agent 工具** | 真正帮干活 | 与 Cursor/自动化联动 |

## 分层立绘替换指南

官方 Live2D 不可直接打包发行。本项目用同名 PNG 分层模拟骨骼挂点：

```
characters/luoxi/variants/
  anime/parts/*.png   # 赛璐璐风格
  pixel/parts/*.png   # 点阵风格
  anime/skeleton.json
  pixel/skeleton.json
```

用真实绘制替换同名部件即可，无需改代码。建议图层：`tail, leg_*, arm_*, torso, hood, head, ear_*, face, eyes, blush`。
