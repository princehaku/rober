# Sprint 2026.05.10 13-14 OKR Function - Pre Start

## 状态

- 阶段：pre_start 已完成，进入 PRD/tech-plan。
- Sprint 类型：业务功能迭代，不归入同时间段 `sprints/2026.05.10_13-14/` 流程修复 sprint。
- 本轮原则：功能往前走，测试只做护栏；优先补 Objective 4 的真实 route/camera 样本闭环缺口。

## 用户价值和产品北极星

北极星仍是低成本 ROS2 自主垃圾投递机器人：普通用户把垃圾交给小车后，小车可沿固定路线送达垃圾站，并留下可复盘证据。

本轮用户价值不是新增一个视觉 demo，而是让真实采集后的 route/camera 样本不再散落在文件夹里：manifest 能被离线检查、汇总，并产出后续 diagnostics 和人工复盘可消费的证据摘要。这样 Autonomy/Behavior/手机诊断后续才能回答“这一轮路线采集有没有相机样本、关键帧是否齐、异常帧是否可追溯”。

## OKR 映射

- 主目标：Objective 4 感知模块产品化，当前约 63%。
- 直接 KR：
  - KR3：未来视觉样本目录和 manifest contract 保留为可选诊断引用。
  - KR4：行为层只依赖稳定感知契约，不直接耦合具体视觉算法。
- 间接受益：
  - Objective 3：route/keyframe 采集后的样本可验证。
  - Objective 5：远程诊断可引用样本汇总，而不是只看任务成功/失败。

## 上轮事实和未完成项

- `route_data_recorder` 已能通过 runtime-style fake image/odom 回调写出 route CSV、keyframe、companion JSON 和 manifest。
- 视觉样本已有 raw/annotated/json/manifest、delivery/anomaly 上下文和可选负样本入口。
- 当前缺口仍是：真实路线数据集、真实 ROS2 camera/odom 采集后的 manifest 检查、持续标注/人工复盘链路。
- 本轮不解决实车采集本身，先补一个可运行的离线 manifest 验证/汇总能力，作为真实采集后的护栏和诊断入口。

## Owner

- 主责 Engineer：Autonomy Algorithm Engineer。
- Product Manager / OKR Owner：负责本 sprint 目标、范围、验收口径和收口证据。
- Robot Platform Engineer：本轮不主责；如后续 diagnostics 接口接入需要，再作为接口咨询。
- Hardware Infra Engineer：本轮不涉及硬件参数、UART、WAVE ROVER、ESP32、Orange Pi、电气或机械尺寸。
- User Touchpoint Full-Stack Engineer：本轮不改手机 UI/API；只要求输出格式未来可被 diagnostics 消费。

## 本轮核心抓手

建立一个离线 route/camera sample manifest 检查与汇总能力：

- 输入：真实或测试生成的 vision sample manifest。
- 输出：结构化 summary，包含样本总数、raw/annotated/json 文件引用完整性、route/task/checkpoint 上下文覆盖、负样本/异常样本计数、缺失项和可读 error/warning。
- 验收：无 ROS2/无硬件环境也能运行；有最小测试覆盖 manifest 正常、缺文件、空 manifest 或 schema 缺字段场景。

## 做什么 / 不做什么

做：

- 增加离线验证/汇总入口和对应测试。
- 固化 summary 字段，便于后续 diagnostics/人工复盘引用。
- 更新本 sprint `tech-done.md`，实现完成后再更新 OKR 进度。

不做：

- 不启动散落垃圾 detector。
- 不承诺真实相机采集已完成。
- 不改硬件/vendor、串口、launch 默认硬件参数。
- 不把测试数量当主目标，不为覆盖率扩展无关重构。
- 不把业务功能写进 `sprints/2026.05.10_13-14/` 流程修复 sprint。

## 阻塞和风险

- 没有真实 route/camera 数据集时，只能用 fixture 验证离线能力；最终仍需实采 manifest 证明。
- manifest 现有字段如未完全稳定，Autonomy Engineer 需要先读当前 vision/nav 产物格式后再落实现。
- 如果 summary 要接入 `/api/diagnostics`，应另开跨 owner sprint，避免本轮扩大到 full-stack/API。

