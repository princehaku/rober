# Sprint 2026.05.10 17-18 Visual Gate Proof - Final

## 状态

- 阶段：final completed。
- 时间：2026-05-10 17:55 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`autonomy-engineer`。
- 收口结论：本 sprint 完成。离线 visual gate proof 证据链成立，可作为 Objective 3/4 的阶段性进展；它不代表真实相机、真实 Nav2 或上车验证完成。

## 用户价值和产品北极星

- 用户价值：把 fixed-route visual gate 从“页面/状态里能看到等待或失败”推进到“有离线可复盘 proof artifact”，让工程排查能明确缺 route、缺 keyframe、缺 live frame、匹配不足或 descriptor 不可用。
- 产品北极星：普通用户未来只需要看到机器人能否安全送达和失败原因；工程侧必须先把视觉门控证据链做成可验证、可解释、可替换的底座。

## OKR 映射

- Objective 3：约 71% -> 约 73%。原因是本轮新增了固定路线视觉门控离线 proof helper/CLI、console script 和 focused tests，扩展了无 Nav2/无硬件环境下的可验证能力。
- Objective 4：约 68% -> 约 70%。原因是本轮把 keyframe/live-frame 匹配、失败路径和 debug status 固化为视觉感知证据 artifact。
- Objective 1：不变。本轮不涉及硬件协议、UART、WAVE ROVER、ESP32、Orange Pi 或 HIL。
- Objective 2：不变。本轮不改行为状态机或真实送垃圾任务闭环。
- Objective 5：不变。本轮不是手机 UI、普通用户流程或量产硬件边界交付。

## KR 拆解或更新

- 完成 KR-A：新增 dependency-light visual gate proof helper/CLI。
- 完成 KR-B：proof JSON 包含 route、checkpoints、match count、threshold、status、summary、debug status 和 inputs。
- 完成 KR-C：单测覆盖通过、匹配不足、缺 keyframe、缺 live frame、缺 route/非法 route 和 CLI 写 JSON。
- 完成 KR-D：`tech-done.md`、`side2side_check.md`、`final.md` 和 `OKR.md` 完成本轮证据链收口。

## 本轮实际改动

- `src/ros2_trashbot_nav/ros2_trashbot_nav/visual_gate_proof.py`
- `src/ros2_trashbot_nav/setup.py`
- `src/ros2_trashbot_nav/test/test_visual_gate_proof.py`
- `sprints/2026.05.10_17-18_visual-gate-proof/tech-done.md`
- `sprints/2026.05.10_17-18_visual-gate-proof/side2side_check.md`
- `sprints/2026.05.10_17-18_visual-gate-proof/final.md`
- `OKR.md`

## 验证结果

- `visual_gate_proof` focused tests：8 tests OK。
- `py_compile`：OK。
- nav 包：39 tests OK。
- `git diff --check`：OK。
- 完整 `scripts/run_smoke_tests.sh`：通过。
- 完整 smoke 包级结果：interfaces 6、hardware 14、nav 39、bringup 9、behavior 111、vision 13 tests OK。

## 做什么 / 不做什么

已做：

- 完成离线 visual gate proof helper/CLI。
- 完成 proof artifact 的结构化失败路径。
- 完成 Product/OKR 收口并更新 Objective 3/4 进度。

未做：

- 未做真实相机验证。
- 未做真实 Nav2 waypoint 或 fixed-route 行驶验证。
- 未做上车验证。
- 未把 proof artifact 接入 route debug web、任务记录或手机诊断页面。

## 剩余风险和下一步

- 下一轮优先用真实 route、真实 keyframe/live-frame 和真实 camera frame 跑一份 proof artifact，对比离线 fixture 与实采数据差异。
- 再下一步把 proof artifact 接入 route debug web 或 task record，让视觉门控证据能进入任务复盘链路。
- 上车前仍需要 Nav2/fixed-route 实跑、ROS2 camera/odom 采集、光照/模糊/角度鲁棒性检查和人工验收记录。
