# Sprint 2026.05.10 10-11 Pre Start

## 目标

推进当前完成度最低的 Objective 4：上一轮已经让视觉样本进入 review queue，本轮补齐 `route_data_recorder` callback runtime-style 文件写入验证，证明学习阶段实际 image/odom 回调链路能产出 route CSV、keyframe、companion JSON 和 manifest 证据。

## Owner

- Autonomy Algorithm Engineer：主责 route recorder callback 运行式验证。
- Robot Platform Engineer：只读复查下一轮 Objective 2/3 集成候选。
- Product Manager / OKR Owner：收口 OKR 进度与 sprint 记录。

## 验收口径

- 无 ROS runtime 的测试能驱动真实 `_on_image()` / `_on_odom()` 方法。
- 测试验证 `route.csv`、`keyframes/000.jpg`、`keyframes/000.json` 和 `manifest.json` 都落盘，且字段满足 `trashbot.vision_samples.v1` 诊断契约。
- 不修改硬件协议、UART、波特率、电气或 vendor 事实。
- full smoke 作为护栏，不扩大测试工作到替代功能交付。

## 风险

- 本轮不是实车路线采集，也不代表真实 `/camera/image_raw` 与 `/odom` 已完成 ROS2 runtime E2E。
- Docker/Humble build 仍可能受当前 WSL Docker integration 影响。
