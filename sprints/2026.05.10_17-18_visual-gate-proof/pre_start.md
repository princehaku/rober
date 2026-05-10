# Sprint 2026.05.10 17-18 Visual Gate Proof - Pre Start

## 状态

- 阶段：pre-start completed。
- 时间：2026-05-10 17:00 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`autonomy-engineer`。

## 上轮未完成项

- Objective 3 当前约 71%，上一轮已把 fixed-route debug web 从 raw JSON 升级为可读状态面板，但仍缺真实 keyframe/live-frame 匹配样例和可复盘 proof artifact。
- Objective 4 当前约 68%，视觉能力已进入 route debug 和诊断链路，但还没有一份能离线复现 visual gate 判定的证据包。
- 上一轮 `tech-done.md` 明确建议：补真实 route/keyframe 样例，用 route debug panel 记录一次 `waiting_visual_gate -> passed -> checkpoint advance` 的证据。本轮先补 dependency-light 离线 proof，给后续真实相机/路线替换留接口。
- Docker/Humble build、真实 Nav2 行驶、真实 camera/odom 采集、WAVE ROVER HIL 仍不是本轮阻塞。

## 本轮目标

让 fixed-route visual gate 从“dry-run 能写状态、页面能看状态”推进到“有一份可复盘的离线 proof artifact”：

- 输入 route。
- 输入 keyframe/live-frame 样例。
- 输出 match count、每个 checkpoint 的 gate status、summary。
- 输出 debug JSON 摘要，后续能被 route debug page、任务记录或真实相机数据替换消费。

## 用户价值和产品北极星

- 用户价值：现场或开发同学不用先上车、接相机、跑完整 Nav2，也能判断 visual gate 证据链是否完整，减少“页面显示等待但不知道缺什么”的排查成本。
- 产品北极星：普通手机用户最终只看到“能不能安全送达、失败原因是什么”；工程侧必须先把固定路线视觉门控做成可解释、可替换、可复盘的证据链。

## OKR 映射

- 主推进 Objective 3：建立可验证导航与固定路线能力。
  - 对齐 KR3：fixed route dry-run 能在无 Nav2/无硬件环境下验证路线读取、关键帧匹配和状态输出。
  - 对齐 KR5：关键帧调试页面和状态证据能展示匹配状态、失败原因和最近一次任务状态。
- 次推进 Objective 4：把摄像头收敛为送达任务的可选感知能力。
  - 通过离线 proof artifact 固化 route/keyframe/live-frame/debug JSON 的可替换 contract。
- 不推进 Objective 1：本轮不碰硬件协议、UART、WAVE ROVER、ESP32、Orange Pi、波特率、电压、引脚或硬件 launch 参数。

## 本轮核心抓手

- 新增一个 dependency-light visual gate proof helper/CLI 或模块，优先放在 `ros2_trashbot_nav` 包内。
- 使用标准库优先；若复用 OpenCV/ORB 逻辑，必须保持测试可在无 ROS2 runtime 环境下通过。
- 产物不是“真车成功”，而是一份结构清晰、能被后续真实数据替换的 proof JSON。

## 做什么 / 不做什么

做：

- 规划并交给 `autonomy-engineer` 实现离线 proof helper/CLI。
- 生成或校验一份 fixture 级别 route、keyframe/live-frame 输入。
- 让 proof 输出包含 route、checkpoint、match count、threshold、status、summary、debug JSON 摘要。
- 写 focused 单测和 sprint `tech-done.md`。

不做：

- 不改硬件、UART、WAVE ROVER、ESP32、Orange Pi 或 launch 硬件参数。
- 不要求真实相机、真实 Nav2、真实路线采集或 Docker/Humble build 作为本轮硬门槛。
- 不改 ROS2 msg/srv/action contract。
- 不把离线 proof 宣称为真实上车 visual gate 成功。

## 优先级和验收口径

P0：

- 能在本地无 ROS2 runtime、无硬件环境下运行 proof helper/CLI 或核心模块测试。
- proof JSON 至少包含 `route`、`checkpoints`、`match_count`、`status`、`summary`、`debug_status`。
- 失败路径要可解释：缺 route、缺 keyframe、缺 live frame、匹配不足、坏输入。

P1：

- CLI 有明确输入输出参数，便于后续真实 route/keyframe/live-frame 替换。
- `tech-done.md` 写清实际改动、验证结果、接口影响和剩余风险。

## Owner

- 主责：`autonomy-engineer`。
- 协作：本轮不需要 Hardware、Robot Platform 或 Full-Stack 改动。
- Product Owner：只负责本轮范围、验收口径和 sprint planning，不写产品代码或测试代码。

## 风险、阻塞和证据链缺口

- 离线 fixture 不能代表真实相机光照、角度、模糊、曝光和运动抖动。
- proof helper 若直接依赖 OpenCV，需要在无 ROS2 环境下保持导入和测试稳定；若 OpenCV 不可用，必须有清晰降级或可测边界。
- 本轮仍不关闭 Objective 3/4 的真实数据缺口：真实 route、真实 keyframe/live-frame、真实 camera/odom 采集、Nav2/fixed-route 实跑仍需后续 sprint。

## 需要创建或更新的 sprint 文档

- 已创建：`sprints/2026.05.10_17-18_visual-gate-proof/pre_start.md`
- 已创建：`sprints/2026.05.10_17-18_visual-gate-proof/prd.md`
- 已创建：`sprints/2026.05.10_17-18_visual-gate-proof/tech-plan.md`
- implementation 完成后必须由 `autonomy-engineer` 更新：`sprints/2026.05.10_17-18_visual-gate-proof/tech-done.md`
- 验收或复盘阶段再更新：`side2side_check.md`、`final.md`
