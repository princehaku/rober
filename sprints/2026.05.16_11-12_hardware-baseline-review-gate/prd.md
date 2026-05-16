# Sprint 2026.05.16_11-12 Hardware Baseline Review Gate - PRD

## 1. 用户价值和产品北极星

产品北极星：把 `rober` 做成普通手机用户能使用、低成本可量产、硬件事实可追溯的 ROS2 自主垃圾投递小车。

本轮用户价值是降低量产和现场 bringup 风险：当 `docs/product/production_hardware_boundary.md` 的默认硬件集、mandatory sensor baseline、vendor 证据边界和 OKR routing 口径一致时，采购、硬件安装、ROS2 bringup、Nav2/SLAM、电梯 evidence contract 和手机状态提示才能围绕同一个 baseline 执行。

本轮不是新增硬件能力，不证明 2D LiDAR / ToF 已接入，也不证明 Objective 5 external proof。它是把 PR #5 review feedback 固化成下一轮 Engineer 可以执行的 gate。

## 2. 背景与问题

GitHub PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 引入了 `monocular + 2D LiDAR + ToF` mandatory baseline，但留下三类产品/工程风险：

- P1：`Default Hardware Set` 未列 2D LiDAR / ToF，后文却把 `monocular + 2D LiDAR + ToF` 标成 mandatory baseline，BOM / procurement / bringup 计划可能互相矛盾。
- P2：sensor baseline 和 ToF channel count 没有引用 `docs/vendor/` 本地来源，不符合硬件相关规则。
- P2：历史 lowest-objective narrative 曾与 OKR table 数值不一致，后续 `OKR 最低优先级核对` 必须读取 live `OKR.md` 4.1 table。

当前 `docs/vendor/VENDOR_INDEX.md` 可作为 Orange Pi Zero 3、WAVE ROVER、UART JSON、WAVE ROVER mechanical references、vendor camera tutorials 的本地硬件事实入口；它不能证明 2D LiDAR / ToF 已有本地 vendor 实测材料。

## 3. OKR 映射

- Objective 4：主攻。低成本量产边界需要硬件 baseline、默认硬件集、采购待补证、维护成本和软件收益说明保持一致。
- Objective 1：支撑。硬件事实必须本地可追溯，不能让未引用 vendor/source 的传感器假设进入 bringup 或硬件配置。
- Objective 2/3：间接受益。电梯 assisted delivery、Nav2/SLAM、fixed-route 和近场安全需要 sensor responsibility split，但不得把软件 contract 写成真实现场已通过。
- Objective 5：不主攻。live `OKR.md` 4.1 显示 Objective 5 约 66% 为最低，但本机只有 Docker，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；本轮不继续堆本地 O5 metadata。

## 4. KR 拆解或更新

本轮计划对 KR 的影响口径：

- Objective 4 KR3：把量产硬件约束表从“默认硬件集”和“mandatory baseline”分裂状态改成一致状态；2D LiDAR / ToF 若保持 mandatory，必须进入默认/采购 baseline，并标注成本、装配、维护、软件收益与证据状态。
- Objective 4 KR8：把“单目摄像头 + 2D LiDAR + ToF 安全环”定义为产品基线或采购待补证，而不是 `docs/vendor/` 已实测事实；ToF 通道数必须有来源或降级为产品建议/待采购验证。
- Objective 4 KR9：状态机、感知 contract、手机状态展示保留参数化扩展点，但实现前必须区分 `not_proven`、`software_proof`、`hardware_material_pending` 和真实硬件 proof。
- Objective 1 KR5：launch 参数和硬件配置不得写死 Orange Pi、2D LiDAR、ToF 的具体设备路径、frame id、阈值或通道数，除非本地 vendor/采购/实测材料已补齐。

## 5. 本轮核心抓手

核心抓手是 `hardware_baseline_review_gate`：

- 让 Product 明确硬件 baseline 的产品分层和验收口径。
- 让 Hardware 能修复 `production_hardware_boundary` 的 BOM / mandatory baseline 矛盾，并补齐 vendor/source attribution 边界。
- 让 Robot / Autonomy / Full-stack 分别知道下一步可改什么、不能宣称什么、需要跑什么验证。
- 让最低 Objective 检查以 live `OKR.md` 4.1 table 为准，同时解释为什么 O5 外部证据阻塞时本轮转向 O4/O1。

## 6. 需要做什么

下一步实施阶段需要 Engineer 完成：

1. Hardware：更新 `docs/product/production_hardware_boundary.md`，统一 `Default Hardware Set` 与 `Navigation/Sensing Baseline`；明确 2D LiDAR / ToF 是 mandatory product baseline 还是 procurement pending baseline，并引用 `docs/vendor/VENDOR_INDEX.md` 已覆盖与未覆盖的事实。
2. Hardware：若坚持 ToF 2 路/4 路，补齐来源；若没有来源，改成“安全环采购/集成待补证，不得作为已验证通道数”。
3. Robot：检查 bringup/launch/diagnostics 是否引用该 baseline；只允许参数化 contract，不允许硬编码未证明的具体设备路径、frame id、阈值、通道数。
4. Autonomy：检查 Nav2/SLAM、monocular/elevator semantic evidence、ToF near-field safety 的 responsibility split 是否是 contract，不把 ToF 写成主建图输入。
5. Full-stack：如手机端展示该状态，只能显示 phone-safe 的硬件基线缺口、采购待补证、`not_proven` 和下一步材料，不解锁 Start / Confirm Dropoff / Cancel。
6. Product：实施完成后更新 `tech-done.md`、`side2side_check.md`、`final.md` 和 `OKR.md` 进展；只有真实 evidence 改变时才调整 OKR 百分比。

## 7. 优先级和验收口径

优先级：

- P0：修复 `Default Hardware Set` 与 mandatory sensor baseline 矛盾。
- P0：写清 `docs/vendor/VENDOR_INDEX.md` 对已覆盖硬件事实和未覆盖 LiDAR/ToF 事实的边界。
- P1：为 Robot / Autonomy / Full-stack 给出参数化 implementation gate，避免写死未证明硬件假设。
- P1：在 sprint 文档中保留 `OKR 最低优先级核对`，并以 live `OKR.md` 4.1 table 为准。

验收口径：

- `rg` 能在本 sprint 文档中检索到 PR #5、`production_hardware_boundary`、2D LiDAR、ToF、`docs/vendor/VENDOR_INDEX.md`、Objective 5 / O5、Docker、`software_proof`、`OKR 最低优先级核对`。
- `git diff --check -- sprints/2026.05.16_11-12_hardware-baseline-review-gate` 通过。
- 后续实施验收必须证明文档矛盾被消除，并且没有把计划文档、vendor index、local Docker proof 写成 hardware proof、LiDAR/ToF vendor proof 或 Objective 5 external proof。

## 8. 对应责任 Engineer

- `hardware-engineer`：主责硬件 baseline 文档修复、vendor/source attribution、BOM/采购待补证边界。
- `robot-software-engineer`：负责 bringup/launch/diagnostics contract 与参数化 gate。
- `autonomy-engineer`：负责 Nav2/SLAM、电梯语义证据、ToF safety responsibility split 的可执行 contract。
- `full-stack-software-engineer`：负责 phone-safe 状态展示和 action gating 边界。
- `product-okr-owner`：负责 OKR 映射、验收口径、sprint 留档和最终 OKR 更新。

## 9. 风险、阻塞和证据链

- 风险：把 LiDAR/ToF 写成 vendor 已实测会违反硬件事实规则；当前只能写成产品基线或采购/集成待补证。
- 风险：只修 `production_hardware_boundary`，不让 Robot / Autonomy / Full-stack 明确 contract，后续仍可能在 launch、frame id、阈值和 UI copy 上漂移。
- 阻塞：Objective 5 外部证据仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；本机 Docker 无法补齐。
- 证据链：AGENTS.md 硬件相关规则、live `OKR.md` 4.1、上一轮 final 的 `software_proof_docker` 边界、PR #5 Codex Review P1/P2、`docs/vendor/VENDOR_INDEX.md`。

## 10. 需要创建或更新的 sprint 文档

本轮只写计划文档：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实施完成后必须继续补齐 Epic 链路：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
