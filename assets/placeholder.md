# 占位说明 — 替换为真实序列帧即可

## 目录结构

```
assets/
├── idle/     → 4帧，站立姿态
│   └── frame_01.png … frame_04.png
├── walk/     → 4帧，行走/小跑姿态
│   └── frame_01.png … frame_04.png
├── wave/     → 3帧，挥手打招呼
│   └── frame_01.png … frame_03.png
├── happy/    → 3帧，开心/点头
│   └── frame_01.png … frame_03.png
└── sleepy/   → 3帧，打瞌睡
    └── frame_01.png … frame_03.png
```

## 命名规则

- 文件格式：`.png`（透明背景）
- 文件名：`frame_01.png`、`frame_02.png` …（2位数字序号）
- 程序按文件名自然排序加载

## 当前状态

暂无真实图片素材，使用代码中 QPainter 程序生成的简笔二头身图形占位。
替换方式：将真实 PNG 放入对应动作目录，重启应用即可自动加载。
