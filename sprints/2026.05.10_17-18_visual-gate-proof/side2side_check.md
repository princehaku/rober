# Sprint 2026.05.10 17-18 Visual Gate Proof - Side2Side Check

## 状态

- 阶段：side2side_check completed。
- 时间：2026-05-10 17:55 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`autonomy-engineer`。
- 验收结论：通过本轮产品验收，作为 Objective 3/4 的离线 proof 证据入账。

## 用户价值和产品北极星

- 用户价值：工程和售后同学不用先接真实相机、跑 Nav2 或上车，也能用离线 artifact 判断 fixed-route visual gate 的证据链是否完整、每个 checkpoint 为什么通过或失败。
- 产品北极星：让固定路线送垃圾逐步变成可验证、可解释、可复盘的低成本闭环；本轮完成的是离线 visual gate proof，不是实车送达闭环。

## OKR 映射

- Objective 3：从约 71% 提升到约 73%。本轮新增无 ROS2 daemon/Nav2/硬件依赖的 visual gate proof helper/CLI，补齐 fixed-route dry-run 证据链的可复盘 artifact。
- Objective 4：从约 68% 提升到约 70%。本轮把 keyframe/live-frame 匹配证据收敛为结构化 proof JSON，推进摄像头作为送达任务可选感知能力的 contract。
- Objective 1、Objective 2、Objective 5：本轮不抬进度。尤其 Objective 5 不抬，因为没有新增手机 UI、普通用户实测或量产硬件验收。

## KR 拆解或更新

- Objective 3 / KR3：已补 `visual_gate_proof.py`，可在离线环境验证 route 读取、checkpoint keyframe/live-frame 匹配状态和 summary 输出。
- Objective 3 / KR5：proof JSON 包含 `debug_status`，字段可对齐后续 route debug page、任务记录或真实相机数据消费。
- Objective 4 / KR4：行为和导航侧继续依赖稳定感知 contract，不把散落垃圾拾取作为本轮任务成功标准。

## 本轮核心抓手

- 新增离线 proof helper/CLI：`visual_gate_proof.py`。
- 新增 setup.py console script：`visual_gate_proof`。
- 新增 focused 单测：`test_visual_gate_proof.py`。
- 输出 proof JSON：包含 `route`、`checkpoints`、`summary`、`debug_status`、`inputs`。

## 做什么 / 不做什么

做：

- 认可本轮离线 proof artifact 达成本 sprint P0 验收口径。
- 将 Objective 3/4 的进度更新写入 `OKR.md`。
- 把验证证据、边界和剩余风险写入本 side2side check。

不做：

- 不宣称真实相机、真实 Nav2、真实 fixed-route 行驶或上车验证通过。
- 不抬 Objective 5，因为本轮不是手机 UI 或普通用户触点交付。
- 不修改硬件、UART、WAVE ROVER、ESP32、Orange Pi 或 launch 硬件参数。

## 验收证据

- `visual_gate_proof` focused tests：8 tests OK。
- `py_compile`：`visual_gate_proof.py` OK。
- nav 包：39 tests OK。
- `git diff --check`：OK。
- 完整 `scripts/run_smoke_tests.sh`：通过。
- 完整 smoke 包级结果：interfaces 6、hardware 14、nav 39、bringup 9、behavior 111、vision 13 tests OK。

## 责任 Engineer

- `autonomy-engineer`：已完成实现、测试和 `tech-done.md`。
- `product-okr-owner`：完成 side-by-side 验收、`final.md` 复盘和 `OKR.md` 进度更新。

## 风险、阻塞和证据链缺口

- 本轮是离线 proof，不等于真实 camera frame、真实 keyframe 光照鲁棒性、真实 Nav2 行驶或上车成功。
- proof artifact 尚未被 route debug web、任务记录或手机诊断页面直接消费，后续接入前需要保持字段迁移策略。
- 仍缺真实路线采集、真实 keyframe/live-frame 样例、ROS2 camera/odom 采集、Nav2/fixed-route 实跑和上车验收。
