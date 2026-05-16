# Sprint 2026.05.17_02-03 Hardware Sensor HIL-entry Readiness Review - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

普通用户最终不该理解 2D LiDAR、ToF、frame ID、threshold 或 HIL-entry 的工程细节；但现场支持和工程同学必须知道“现在是否已经具备进入传感器 HIL 的材料条件”。本轮把 PR #5 review 暴露的硬件来源与基线问题继续推进成可执行 readiness review：材料不足时明确列出缺什么，材料和配置都满足时也只能进入 `not_proven` 的 HIL-entry 评审，不启用任何主操作。

产品北极星仍是低成本、可追溯、普通手机用户可用的 ROS2 自主垃圾投递机器人；硬件目标不能凭口径漂移变成已安装事实。

## 2. OKR 映射

- Objective 1：补齐可信底盘/硬件链路进入 HIL 前的材料评审入口，防止 2D LiDAR / ToF 未证实材料进入上车计划。
- Objective 4：手机端能解释 HIL-entry readiness 的缺口、下一步材料和 `not_proven` 边界，降低现场支持误解。
- Objective 5：仍是数值最低，但本机无真实公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/migration 材料，本轮不继续本地 O5 wrapper。

## 3. 核心需求

1. PC gate 输出 `trashbot.hardware_sensor_hil_entry_readiness_review.v1` 和 summary。
2. Gate 同时接受 receipt-intake summary 与 HIL-entry config-precheck summary，缺任一输入都 fail closed。
3. Gate 必须引用 `docs/vendor/VENDOR_INDEX.md` 作为 vendor/source boundary，并明确本地 vendor tree 不证明项目 2D LiDAR / ToF SKU、安装、接线、标定或 HIL。
4. Robot diagnostics 只能 metadata-only 透传 phone-safe summary，不允许改变 collect/dropoff/cancel/ACK/primary action。
5. Mobile/web 只读 panel 展示 readiness status、missing material/config groups、next required evidence、owner handoff、safe evidence ref、boundary、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. 非目标

- 不采购、不安装、不接线、不打开串口、不跑真实 HIL。
- 不证明真实 2D LiDAR / ToF、真实 Nav2/SLAM、route/elevator field pass、真实手机/browser 或 delivery success。
- 不新增广泛测试矩阵；只跑围栏命令。

## 5. 验收口径

- 每个工程 owner 必须给出实际改动文件、围栏验证输出、失败定位和剩余风险。
- 所有输出必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Sprint closeout 必须回写 OKR 和 progress log，且不得提升 Objective 5。
