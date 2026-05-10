# Sprint 2026.05.10 16-17 Route Debug Status Panel - Pre Start

## 状态

- 阶段：pre-start completed。
- 时间：2026-05-10 16:15 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`autonomy-engineer`。

## 上轮未完成项

- Objective 3 仍缺真实 fixed-route/Nav2 运行、真实 keyframe/live-frame 匹配样例和更可读的 route debug 页面。
- 现有 `route_debug_web.py` 只显示 raw JSON，不能直观看到当前位置、目标 checkpoint、visual gate、keyframe preflight、失败原因或最近任务状态。
- Docker/Humble colcon build 与 WAVE ROVER HIL 仍受环境和硬件条件限制，不作为本轮阻塞。

## 本轮目标

把 fixed-route debug web 从 raw JSON 推进为可读状态面板，让现场同学用浏览器打开后能直接判断：

- 路线处于 ready、running、waiting_visual_gate、completed、error 还是 missing/invalid status。
- 当前 checkpoint、总 checkpoint、当前目标坐标和运行模式。
- visual gate 是否通过、等待相机、特征不足或 keyframe preflight 失败。
- route-wide keyframe 覆盖情况和缺失/损坏 keyframe。
- 失败原因、最近导航结果、最近状态转换和最近任务记录引用。

## Owner

- 主责：`autonomy-engineer`
- 协作：本轮不需要 Hardware 或 Full-Stack 改动；页面属于 nav debug 工具，不触碰手机 operator gateway。
- Coordinator：只做验收、sprint 收口、OKR 更新和 git commit。

## 验收口径

- `route_debug_web.py` 继续提供 `/api/status`，并保持 raw JSON 可见。
- 首页新增可读 debug panel，不再只是一段 `<pre>`。
- 页面至少包含稳定 DOM id 和 JS 函数，便于静态测试锁定字段。
- 状态文件缺失或 JSON 损坏时，页面不能崩溃，必须显示可读错误状态。
- 不改 ROS2 msg/srv/action，不改 fixed-route status payload shape。

## 风险

- 本轮是 browser/debug 页面升级，不证明真实 Nav2 或 camera/odom 已上车跑通。
- 因为不启动浏览器，只能用静态/HTTP handler 单测和 smoke 作为护栏；真实视觉布局仍需后续人工或浏览器截图验证。
- 如果未来 fixed-route status 字段继续扩展，debug panel 的字段映射需要同步维护。
