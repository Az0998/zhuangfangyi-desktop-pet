# 终末地桌宠

可替换角色包 · **anime / pixel 双画风分层立绘** · 骨骼动作链 · AI 对话 · **剪贴板历史** · **日程/健康提醒**。

默认角色：**洛茜**（洛希）。角色版权归鹰角网络，《明日方舟：终末地》相关仅供个人学习娱乐。

---

## 快速开始

```bash
pip install -r requirements.txt
python tools/generate_luoxi_art.py
python main.py
```

`config.json` 中 `"art_style": "anime"` 或 `"pixel"`。也可右键菜单随时切换。

---

## 操作

| 操作 | 效果 |
|------|------|
| 单击 | 挥手 / 连点跳跃、害羞动作链 |
| 拖拽 | 带走（walk） |
| 双击 | AI 对话 |
| 右键 | 画风、剪贴板、日程、动作、换角色 |
| 复制任意文本 | 她会接话，并记入剪贴板历史 |

---

## 动作链

`characters/luoxi/animations.json` 中定义：

- `idle / blink / walk / wave / happy / shy / curious / tail_wag / sleepy`
- `think / stretch / sit / jump / alert`
- 链：`greet_flow`、`wake_up`、`praise_flow`、`copy_react`、`remind_flow`

---

## 剪贴板 & 日程

- 历史保存在 `data/clipboard_history.json`，面板可搜索、双击粘回
- 日程保存在 `data/schedule.json`：每日定点 / 间隔分钟 + 喝水/护眼/休息

---

## 精细立绘（官方参考 + AI 重绘）

参考图放在 `characters/luoxi/ref/`。AI 重绘成品经去背后写入：

```
characters/luoxi/variants/anime/parts/body.png   # 精绘全身（主显示）
characters/luoxi/variants/pixel/parts/body.png   # 像素全身
```

重新构建：

```bash
python tools/build_official_luoxi.py
```

若你有更清晰的官方图或自绘分层，直接覆盖 `variants/*/parts/` 同名 PNG，或替换 `ai_raw/fullbody.png` 后再构建。

---

## AI

`config.json` → `ai`，或环境变量 `DESKTOP_PET_API_KEY` / `DESKTOP_PET_BASE_URL` / `DESKTOP_PET_MODEL`。
