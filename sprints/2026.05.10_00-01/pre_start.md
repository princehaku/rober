# Sprint 2026.05.10_00-01 Pre Start

## 状态

- 当前阶段：PRE-START。
- 上轮交接：Docker Humble build 仍 blocked；HIL deferred；本地 smoke 已能覆盖 interfaces/hardware/nav/bringup/behavior/vision。
- 本轮目标：推进 OKR 完成度低的 Objective 3 fixed-route dry-run 视觉门控，不扩大到硬件或 Docker 环境改造。

## Owner

| 角色 | 责任 |
| --- | --- |
| `Autonomy Algorithm Engineer` | fixed-route dry-run 与视觉门控实现、测试和状态输出 |
| `Robot Platform Engineer` | 确认行为层读取 fixed-route status 的边界不被破坏 |
| `Product Manager / OKR Owner` | 更新 OKR 进度和 sprint 留档 |

## 本轮验收口径

1. `enable_visual_gate=true` 时，fixed-route dry-run 不能在缺 keyframe 或 camera frame 时直接 completed。
2. `enable_visual_gate=false` 时，原有无硬件/无 Nav2 路线 dry-run 仍可 completed。
3. debug status 必须写出可被行为层和调试页面理解的状态、失败原因和当前 checkpoint。
4. 本地 nav 定向测试与全局 smoke 作为护栏；Docker/HIL 不作为本轮通过声明。

## 风险

| 风险 | 处理 |
| --- | --- |
| 默认 fixed-route dry-run 同时开启 visual gate，导致没有 keyframe 的离线演示不再 completed | 在文档和 sprint 记录中明确：路线解析 dry-run 需关闭 `enable_visual_gate`；视觉门控 dry-run 用于验证 keyframe/camera 准入 |
| 状态文件非终态会让 behavior fixed-route reader 等到 timeout | 符合当前行为层契约：视觉门控未满足时不应宣称送达成功 |
| 没有真实摄像头/HIL | 仅声明软件 dry-run 准入，不声明实机视觉匹配通过 |
