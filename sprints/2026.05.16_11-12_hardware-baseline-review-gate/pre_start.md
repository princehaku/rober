# Sprint 2026.05.16_11-12 Hardware Baseline Review Gate - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 Epic sprint：`sprints/2026.05.16_11-12_hardware-baseline-review-gate/`。

目标不是继续堆 Objective 5 本地 metadata，而是把 GitHub PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 的 Codex Review 转成可执行、可验证的 product/hardware baseline gate。主攻 Objective 4（低成本量产边界），同时支撑 Objective 1（硬件事实可追溯）。

## 2. 启动证据

- 当前 `OKR.md` 4.1 live table 显示 Objective 5 约 66%，低于 Objective 1 约 73%、Objective 2/3 约 78%、Objective 4 约 80%。Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；当前主机只有 Docker，因此本轮不继续堆本地 O5 metadata。
- 上一轮 `sprints/2026.05.16_09-10_mobile-field-material-retest-request/final.md` 已明确：当前只能证明 `software_proof_docker_mobile_field_material_retest_request_gate`，真实现场/真实设备材料不足，不能证明真实手机、真实电梯、真实 Nav2/fixed-route、HIL、真实送达或 Objective 5 external proof。
- PR #5 Codex Review P1 指出：`docs/product/production_hardware_boundary.md` 的 `Default Hardware Set` 未列 2D LiDAR / ToF，但同文档后面把 `monocular + 2D LiDAR + ToF` 标成 mandatory baseline，导致 BOM / procurement / bringup 计划可能遗漏必需传感器。
- PR #5 Codex Review P2 指出：新增强制 sensor baseline（传感器组合和 ToF 通道数）没有引用 `docs/vendor/` 本地来源，不符合硬件相关规则。
- PR #5 Codex Review P2 指出：当时 OKR lowest-objective narrative 与表格值不一致；本轮计划必须把最低 Objective 判断固定为读取 live `OKR.md` 4.1 table，而不是沿用历史叙述。
- `docs/vendor/VENDOR_INDEX.md` 已确认本地硬件事实来源覆盖 Orange Pi Zero 3、WAVE ROVER、UART JSON、WAVE ROVER mechanical references 和 vendor camera tutorials；该索引没有把 2D LiDAR / ToF 写成已采购、已接线、已实测或 vendor 已证明。

## 3. 用户价值和产品北极星

北极星：让普通手机用户可以把垃圾交给低成本 ROS2 小车，小车在可控路线和电梯 assisted delivery 边界内完成送达，并且硬件、软件和验收口径不互相矛盾。

用户价值：减少后续采购、装配和 bringup 阶段的返工。若产品文档一处说默认不含 LiDAR/ToF，另一处又把 LiDAR/ToF 作为 mandatory baseline，工程团队会在 BOM、launch 参数、传感器 contract 和验收证据上各自理解，最终拖慢低成本量产边界闭环。

## 4. 本轮核心抓手

把 PR #5 的三条评审意见转成下一步可执行的 product/hardware baseline gate：

- 对齐 `Default Hardware Set` 与 mandatory navigation/sensing baseline。
- 给 2D LiDAR / ToF 做证据分层：可作为产品基线/采购待补证，不得写成 `docs/vendor/` 已实测。
- 把最低 Objective 核对固定为 live `OKR.md` 4.1 table，并在 O5 外部证据阻塞时选择 Objective 4/O1 的可行动作。

## 5. Owner 与边界

- Product Manager / OKR Owner：负责 PRD、OKR 映射、验收口径、sprint 留档和最终 OKR 更新判断。
- Hardware Infra Engineer：负责 `docs/product/production_hardware_boundary.md` 的硬件事实来源、BOM/采购待补证、vendor 引用边界和硬件验收 gate。
- Robot Platform Engineer：负责 bringup/launch/diagnostics contract 是否会因 baseline 改动产生接口或配置影响。
- Autonomy Algorithm Engineer：负责 Nav2/SLAM/电梯语义证据与 sensor responsibility split 的工程可执行性。
- User Touchpoint Full-Stack Engineer：负责手机端是否需要展示硬件基线未证明、采购待补证或现场证据缺口，不把它写成用户可控制成功。

## 6. 风险与阻塞

- O5 仍是数值最低 Objective，但真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 不在当前 Docker-only 主机可证明范围内。
- 2D LiDAR / ToF 当前只能作为产品基线和采购/集成待补证，不能写成 vendor 已实测、HIL 通过或真实硬件 baseline 已闭环。
- `docs/vendor/VENDOR_INDEX.md` 是硬件事实入口；若下一步要写具体 LiDAR/ToF 型号、通道、引脚、电压、串口/I2C/GPIO、机械安装尺寸，必须补本地 vendor 资料或采购资料后再实施。

## 7. 本轮只创建或更新的 sprint 文档

- `sprints/2026.05.16_11-12_hardware-baseline-review-gate/pre_start.md`
- `sprints/2026.05.16_11-12_hardware-baseline-review-gate/prd.md`
- `sprints/2026.05.16_11-12_hardware-baseline-review-gate/tech-plan.md`

本轮计划文档不是 hardware proof、不是 LiDAR/ToF vendor proof、不是 Objective 5 external proof。
