# Sprint 2026.05.10 09-10 Pre Start

## 目标

推进 Objective 4 低完成度缺口：视觉样本 manifest 已经能沉淀 route keyframe / anomaly / detection 证据，本轮把它升级成远程诊断可消费的复盘队列，帮助后续标注、站点识别和异常复盘。

## Owner

- Autonomy Algorithm Engineer：主责 route keyframe / anomaly 样本复盘口径。
- User Touchpoint Full-Stack Engineer：主责 `/api/diagnostics` 和手机诊断展示。
- Product Manager / OKR Owner：收口 OKR 进度与剩余风险。

## 验收口径

- `/api/diagnostics` 的 `vision_samples` 不只返回 latest sample，还能返回按 event type 的样本计数和 bounded review queue。
- review queue 能优先暴露 anomaly、route keyframe、低置信度检测或未标注样本，包含 sample_ref、context、reason、confidence 等复盘字段。
- 手机诊断页显示 review queue 数量和最新待复核样本，供普通用户/远程支持截图转交。
- 相关逻辑有单元测试，full smoke 作为护栏。

## 风险

- 本轮仍不启动真实摄像头，不声明已经采集真实数据集。
- 不修改硬件协议、UART、波特率或电气事实，不需要 vendor 二次确认。
