# Sprint 2026.05.10 17-18 Visual Gate Proof - PRD

## 用户价值

fixed-route visual gate 不能只停留在 dry-run 状态字段和 debug 页面。工程同学需要一份离线可复盘证据，能回答：

- 这条 route 有哪些 checkpoint 需要视觉门控。
- 每个 checkpoint 用了哪个 keyframe 和 live-frame。
- 匹配数量是多少，是否达到阈值。
- 失败时是缺文件、坏输入、无 descriptor，还是匹配不足。
- 输出的 debug JSON 能否被后续真实相机/真实路线数据替换。

这件事对普通用户的间接价值是：未来手机端只需要显示“路线视觉校验通过/失败原因”，而不是让用户或售后猜测机器人为什么不出发。

## 产品北极星

把固定路线送垃圾做成“可验证、可解释、可复盘”的低成本闭环：先用离线 proof 证明证据链结构正确，再接入真实相机和真实路线。

## OKR 映射

- Objective 3：建立可验证导航与固定路线能力。
  - KR3：无 Nav2/无硬件环境下验证路线读取、关键帧匹配和状态输出。
  - KR5：固定路线调试能展示匹配状态、失败原因和最近一次任务证据。
- Objective 4：把摄像头收敛为送达任务的可选感知能力。
  - 本轮将 keyframe/live-frame 证据固定成可替换 artifact，不把散落垃圾 detector 当核心闭环。
- Objective 5：手机体验与低成本量产边界。
  - 间接推进远程诊断最小数据包中的视觉门控证据字段，但本轮不做手机 UI。

## KR 拆解或更新

本轮不修改 `OKR.md`，只把 Objective 3/4 的小时级 KR 拆成可交付切片：

- KR-A：新增 dependency-light proof helper/CLI，能读取 route 与 keyframe/live-frame 输入。
- KR-B：proof 输出结构化 JSON，包含 route 摘要、checkpoint 列表、match count、阈值、status summary 和 debug JSON 摘要。
- KR-C：离线测试覆盖通过、匹配不足、缺 keyframe/live-frame、坏输入等关键路径。
- KR-D：`tech-done.md` 记录 proof artifact 示例、验证命令和真实数据剩余缺口。

## 本轮核心抓手

由 `autonomy-engineer` 在 `ros2_trashbot_nav` 内新增一个可被单测直接调用、也可通过 console script 运行的 proof helper。它应尽量复用 fixed-route visual gate 的概念字段，但不启动 ROS2 node、不创建 `BasicNavigator`、不依赖硬件。

## 范围

做：

- 新增 visual gate proof helper/CLI 或模块。
- 新增 focused 单测和小型 fixture，证明 proof artifact 能生成和验证。
- 将输出字段对齐现有 debug status 语义：`visual_gate_status`、`visual_gate_detail`、`visual_gate_checkpoint`、`keyframe_preflight`、`last_error`、`failure_reason`。
- 更新当前 sprint `tech-done.md`。

不做：

- 不改 `fixed_route_autonomy.py` 的实际路线推进逻辑，除非实现时发现只读 helper 必须抽取共享纯函数；若要改，必须在 `tech-done.md` 解释接口影响。
- 不改 route debug web 页面。
- 不改 ROS2 msg/srv/action。
- 不碰硬件/vendor、UART、WAVE ROVER、ESP32、Orange Pi 或 launch 硬件参数。
- 不要求真实相机或真实 Nav2 实跑。

## 优先级

- P0：离线 proof helper/CLI + JSON artifact + focused tests。
- P0：失败原因必须结构化，不能只输出一段模糊日志。
- P1：CLI 输入输出参数清晰，后续能替换为真实 route/keyframe/live-frame。
- P2：如成本很低，可补一个 sample proof JSON fixture；若会扩大范围，则只在测试中生成临时 artifact。

## 验收标准

- 能运行一个命令生成 proof JSON，命令不需要 ROS2 daemon、Nav2、相机或硬件。
- proof JSON 至少包含：
  - `route`
  - `checkpoints`
  - `summary`
  - `debug_status`
  - 每个 checkpoint 的 `index`、`keyframe`、`live_frame`、`match_count`、`threshold`、`status`
- status 至少区分：
  - `passed`
  - `insufficient_matches`
  - `missing_keyframe`
  - `missing_live_frame`
  - `invalid_route`
  - `no_descriptors` 或等价坏输入状态
- 单测覆盖通过路径和关键失败路径。
- `tech-done.md` 明确写出验证命令、结果、接口影响、剩余风险。

## 对应责任 Engineer

- `autonomy-engineer`：实现、测试、修复和 `tech-done.md`。
- Product Owner：本轮只完成 PRD/tech-plan；implementation 后验收证据链是否满足 Objective 3/4。

## 风险、阻塞和需要补齐的证据链

- 离线 proof 只证明证据结构和匹配流程，不证明真实环境鲁棒性。
- 如果本地 OpenCV 不可用，autonomy engineer 需要选择 dependency-light 的可测实现边界，不能让整个 nav 包导入失败。
- 后续仍需真实 route/keyframe/live-frame 数据、真实 camera frame、真实 Nav2/fixed-route 行驶和 route debug web 对照截图。
