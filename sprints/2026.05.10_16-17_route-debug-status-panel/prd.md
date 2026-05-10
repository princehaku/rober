# Sprint 2026.05.10 16-17 Route Debug Status Panel - PRD

## 用户价值

现场调试固定路线时，用户或工程同学不应该只看到一坨 JSON。打开 route debug 页面后，应直接知道机器人现在卡在哪个 checkpoint、是不是视觉门控没过、缺哪些 keyframe、失败原因是什么，以及最近一次任务证据在哪里。

## 产品北极星

让固定路线送垃圾从“代码里看起来能跑”变成“现场可观测、可解释、可复盘”的工程闭环。

## OKR 映射

- 主推进 Objective 3：建立可验证导航与固定路线能力。
  - 对齐 KR5：关键帧调试页面能展示当前位置、目标点、匹配状态、失败原因和最近一次任务状态。
- 间接推进 Objective 2：固定路线送达失败时，现场能更快定位是 route、visual gate、Nav2 还是 status 文件问题。
- 不推进 Objective 1：本轮不碰硬件协议、UART、WAVE ROVER 或 launch 硬件参数。

## 本轮范围

做：

- 改造 `route_debug_web.py` 首页，新增路线状态总览、checkpoint、目标坐标、visual gate、keyframe preflight、失败原因和任务引用展示。
- 保留 raw JSON 区域，方便工程排查。
- 增加 nav 包测试，覆盖页面 contract、status API 缺失/损坏处理，以及关键字段渲染入口。
- 更新本 sprint `tech-done.md`，后续由 Coordinator 更新 `side2side_check.md`、`final.md` 和 `OKR.md`。

不做：

- 不新增 fixed-route status payload 字段。
- 不改 `fixed_route_autonomy.py` 导航逻辑。
- 不启动真实 Nav2、相机、WAVE ROVER 或 Docker/Humble build 作为本轮硬门槛。
- 不改手机 operator gateway 页面；本轮是 nav debug 工具。

## 验收标准

- 首页必须包含稳定 DOM id：
  - `routeStateBadge`
  - `routeSummary`
  - `routeProgress`
  - `routeTarget`
  - `visualGateStatus`
  - `keyframePreflight`
  - `routeFailureReason`
  - `recentTask`
  - `rawStatus`
- JS 必须包含：
  - `routeStateView`
  - `visualGateView`
  - `renderStatus`
  - `renderKeyframePreflight`
- `/api/status` 缺文件返回 `state=missing_status_file` 的 JSON；坏 JSON 返回 `state=invalid_status_file` 的 JSON。
- 页面原因和路径必须能换行，避免长路径撑破手机或窄屏。

## 成功口径

本轮成功不是“真实机器人跑通”，而是 Objective 3 的 debug 可观测能力往前走：fixed-route status JSON 变成可读面板，并有测试证明页面 contract 和 API 错误路径不会回退。
