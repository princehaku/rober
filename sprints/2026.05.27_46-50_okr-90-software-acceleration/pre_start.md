# OKR 90 Software Acceleration Pre-start

## 1. Sprint 类型和目标

sprint_type: epic

本轮由 `product-okr-owner` 启动 Epic planning，承接 CEO 方向：“继续完成迭代，所有的 OKR 必须完成到 90% 以上”。

当前 `OKR.md` 4.1 快照显示：

- Objective 6：0%，最低优先级，缺隧道接入、数据存档、打标 API、模型推理接口和历史任务查询平台。
- Objective 7：约 5%，仅有 O7 board/cloud/PC 契约和 PC Console software proof，缺真实 RTC/视频、ASR/TTS、手控/寻路、地图/电梯/回放/标注数据流和上车验证。
- Objective 5：约 80%，缺真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 证据。
- Objective 1：约 83%，缺真实 WAVE ROVER 上车实测、UART 链路、HIL 准入和 PR #5 2D LiDAR / ToF 硬件材料。

本 sprint 的规划目标是：把 O6/O7 的软件侧能力大幅推进到可由工程 agent 直接执行的任务队列，并明确 O1/O5 超过 90% 必须依赖真实材料，不能用 mock、local Docker 或 UI contract 伪造真实硬件/公网/4G/production 证据。

## 2. 上轮状态和不重复消费边界

最近 O7 RTC Realtime Foundation 已收口为 `software_proof_o7_realtime_foundation_contract`，只证明 board/cloud/PC 契约起步，不证明真实 RTC、真实视频、真实 ASR/TTS、真实手控/寻路、真实实时地图、电梯状态、历史回放、标注服务、云端生产链路或上车验证。

最近 O5 Cloud Command Result Reconciliation 收口为本地/Docker software proof，仍不证明公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、true phone/browser proof、HIL、Nav2/fixed-route、WAVE ROVER/UART 或 delivery success。

因此本轮不能继续把“契约存在”“UI 存在”“本地 mock 返回值存在”重复消费为 O7/O5 的大幅进度；后续提升必须绑定更完整的软件链路证据，真实证据缺口保持 `not_proven`。

## 3. 本轮 Owner 和工作方式

本轮 planning owner：

- `product-okr-owner`：只负责目标拆解、用户价值、范围边界、验收口径和 sprint 规划文档。

后续 implementation owner：

- `robot-software-engineer`：O6 board/event archive client、任务/感知事件 envelope、ROS2 状态到云端事件的 glue、mock runtime 验证。
- `full-stack-software-engineer`：O6 cloud archive API、任务/事件/对象引用/标注/推理 contract、O7 PC 端消费这些 API 的运营调试与回放界面。
- `robot-algorithm-engineer`：O6/O7 所需路线帧、关键帧、电梯状态、楼层证据、失败原因等离线样本和 inference stub，输出可查询事件流。
- `robot-hardware-engineer`：仅做真实材料边界和上车证据清单，不伪造 WAVE ROVER、Orange Pi、UART、4G 或公网生产材料；涉及真实硬件时必须先读 `docs/vendor/VENDOR_INDEX.md`。

后续执行应按 `tech-plan.md` 并行派发互不重叠的工程任务。主节点不得直接写产品代码、测试代码或硬件配置。

## 4. 本轮范围

允许本轮规划覆盖：

- O6 software MVP：安全隧道状态 contract、任务/事件持久化、OSS evidence_ref、标注 API、推理 API stub、PC/手机查询 API。
- O7 software MVP：实时地图、电梯状态、历史路线回放、标注界面、ASR/TTS 状态与命令草案、手控/寻路下发草案，全部走云端 API，不绕过云端直连小车。
- O5/O1 90% 边界：列出必须由真实公网/4G/production/硬件/HIL 提供的证据，不用 software proof 伪装。

本轮规划不覆盖：

- 不更新 `OKR.md` 完成度。
- 不承诺真实公网、真实 4G、真实 production DB/queue、真实 OSS/CDN live traffic。
- 不承诺真实 WAVE ROVER 上车、UART 实测、HIL 或 PR #5 硬件到货。
- 不承诺真实视频 RTC、真实 ASR/TTS、真实 PC 手控/自动寻路已可生产使用。

## 5. 验收口径

本 planning sprint 完成的验收口径：

- `pre_start.md` 明确 `sprint_type: epic`、目标、owner、证据边界。
- `prd.md` 明确 O6/O7 用户价值、O1/O5 90% 真实证据边界、验收与非目标。
- `tech-plan.md` 明确 OKR 最低优先级核对、分工、文件范围、接口影响、验收命令、风险边界，并为工程 agent 准备可直接执行任务。

本 planning sprint 不产生 O6/O7 代码交付，不得据此提升 OKR 进度。

## 6. 风险边界

- `software_proof` 可以推进 O6/O7 软件侧能力，但只能标记为 `software_proof` 或 `software_proof_docker_only`。
- 真实硬件、真实 4G、真实公网、真实生产 DB/queue、OSS/CDN live traffic、真实手机/browser、真实 RTC/视频和真实上车验证在本轮均保持 `not_proven`。
- 若后续工程实现失败，必须定位并重试；不能把第一轮失败直接作为交付。
- 所有后续代码、配置或业务文档变更必须同步更新对应 `docs/` 和本 sprint 的 `tech-done.md`。
