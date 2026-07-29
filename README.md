# 庄方宜 Q 版桌面宠物 🦉

**庄方宜**（出自游戏《明日方舟：终末地》· 麒麟 · 天师）化身 Q 版桌面宠物，常驻桌面陪你工作学习。

> 「护生安民，职责所在」  
> 作品集介绍：https://zhangsjqaq.vexr.dev

---

## 功能一览

| 功能 | 说明 |
|------|------|
| **悬浮显示** | 无边框、透明背景，始终置顶 |
| **动画系统** | 站立、行走、挥手、开心、打瞌睡 —— 多套序列帧循环播放 |
| **点击互动** | 单击宠物 → 挥手动画 + 随机语音气泡 |
| **拖拽移动** | 按住左键拖拽至桌面任意位置 |
| **右键菜单** | 切换动作 · 关于 · 退出 |
| **空闲状态** | 长时间无操作自动进入打瞌睡模式 |
| **系统托盘** | 最小化后驻留托盘，双击/右键唤出 |

---

## 安装与运行

### 环境需求

- Python 3.9+
- pip

### 安装依赖

```bash
cd zhuangfangyi-desktop-pet
pip install -r requirements.txt
```

### 生成占位图片（如 assets 中尚无图片）

```bash
python generate_placeholders.py
```

> 已内置占位图可跳过此步。首次运行前执行一次即可。

### 运行

```bash
python main.py
```

---

## 配置说明

`config.json` 统一管理所有可调参数：

| 路径 | 参数 | 默认值 | 说明 |
|------|------|--------|------|
| `window.default_x` | 初始 X | 300 | 窗口启动时桌面横坐标 |
| `window.default_y` | 初始 Y | 300 | 窗口启动时桌面纵坐标 |
| `window.default_width` | 默认宽度 | 180 | 窗口宽度 (px) |
| `window.default_height` | 默认高度 | 240 | 窗口高度 (px) |
| `animation.frame_interval_ms` | 帧间隔 | 250 | 每帧显示时长 (ms) |
| `animation.idle_timeout_ms` | 空闲超时 | 30000 | 无操作达到此时间进入瞌睡 (ms) |
| `bubble.display_ms` | 气泡展示 | 3000 | 语音气泡持续时长 (ms) |
| `bubble.lines` | 台词列表 | [...] | 点击时随机抽取的台词（可自由增删） |
| `mouse_proximity_px` | 靠近距离 | 80 | 鼠标靠近触发注视的像素距离 (预留) |

---

## 自定义图片替换指南

1. 准备透明背景的 `.png` 序列帧图片
2. 按动作放入对应子目录：

```
assets/
├── idle/     → 站立（至少 1 帧，建议 4 帧实现呼吸/眨眼动画）
├── walk/     → 行走（建议 4 帧）
├── wave/     → 挥手（建议 3 帧）
├── happy/    → 开心（建议 3 帧）
└── sleepy/   → 打瞌睡（建议 3 帧）
```

3. 文件名命名规则：`frame_01.png`、`frame_02.png` …（2 位数字序号）
4. 每帧推荐尺寸：**120×160 px**（Q 版二头身比例）
5. 修改帧数后同步更新 `config.json` 中对应动作的 `frames` 值
6. 重启应用即可生效，无需修改代码

> **占位图片说明**
>
> 项目内置了程序生成的简易占位 PNG（彩色简笔二头身小人 + 动作名），
> 替换真实素材后重启即可。占位图片不影响任何功能。

---

## 项目结构

```
zhuangfangyi-desktop-pet/
├── main.py                  # 程序入口 + 系统托盘
├── pet_window.py            # 宠物窗口（交互、气泡、空闲状态）
├── pet_animator.py          # 动画控制引擎
├── config.json              # 统一配置文件
├── generate_placeholders.py # 占位图片生成器
├── requirements.txt         # Python 依赖
├── README.md                # 本文件
└── assets/
    ├── placeholder.md       # 资源说明
    ├── idle/                # 站立动作
    │   ├── frame_01.png
    │   └── ...
    ├── walk/                # 行走动作
    ├── wave/                # 挥手动作
    ├── happy/               # 开心动作
    └── sleepy/              # 打瞌睡动作
```

---

## 技术栈

- **Python 3.9+**
- **PyQt5** — 透明窗口、无边框、系统托盘、信号-槽机制
- 纯本地运行，无需网络

---

## 许可

仅供个人学习与娱乐，角色版权归《明日方舟：终末地》及其开发方所有。
