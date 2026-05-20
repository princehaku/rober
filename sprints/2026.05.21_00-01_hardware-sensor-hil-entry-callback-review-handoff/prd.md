# Hardware Sensor HIL-entry Callback Review Handoff PRD

## 用户价值和产品北极星

普通用户最终需要的是“机器人能安全、可靠、可解释地送垃圾”。但当前 Objective 1 的硬件证据链仍卡在真实 2D LiDAR / ToF 材料和 HIL-entry 材料未回填：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / material pending。

本轮产品价值不是宣称硬件完成，而是把上一轮 `hardware_sensor_hil_entry_callback_review_decision` 的复核结果交接给后续 owner：哪些材料已被软件复核、哪些仍缺、下一步应由谁提供真实证据、手机端和 Robot diagnostics 只能看到什么安全摘要。这样可以减少后续反复询问和误关 GitHub thread 的风险。

产品北极星：面向普通手机用户的低成本 ROS2 自主垃圾投递机器人，关键证据必须可追溯、可复盘、可解释。本轮只推进 `software_proof` 证据链的 handoff，不把 software proof 写成真实传感器、真实底盘或真实送达。

## OKR 映射

### Objective 1：硬件协议可信底盘

- 当前约 81%。
- 本轮针对 Objective 1 的材料交接链路，但不提高完成度。
- 关联缺口：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍需真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；还缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report。
- 资料来源边界：硬件事实入口为 `docs/vendor/VENDOR_INDEX.md`，本轮只引用 source boundary，不新增硬件参数假设。

### Objective 5：云中转 + OSS/CDN 数据通路产品化

- 当前约 68%，数字最低。
- 本轮不针对 Objective 5 completion。
- 不推进理由：本机无真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 phone/browser external proof。最近 21-22/22-23/23-24 已连续做 O5 local software guards，继续做本地 metadata 不会成为 O5 external proof。

### Objective 4：手机用户体验与低成本量产边界

- 本轮只要求 mobile/web 增加只读 panel 的验收口径。
- 不声明 real phone/browser、production app、真实 PWA prompt/userChoice 或手机设备验收。

## KR 拆解或更新

- KR-O1-HANDOFF-1：PC gate 接收上一轮 callback review decision artifact/summary，输出 `hardware_sensor_hil_entry_callback_review_handoff` artifact 和 summary。
- KR-O1-HANDOFF-2：Robot diagnostics 只暴露 `robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary` safe alias，并 fail closed。
- KR-O1-HANDOFF-3：mobile/web 增加“传感器 HIL 回调复核交接”只读 panel，展示 handoff 状态、safe evidence ref、missing materials、next required evidence 和 owner handoff。
- KR-O1-HANDOFF-4：Product closeout 后续复核 OKR 仍不提升，除非真实材料和 reviewer resolution 到位。

## 本轮核心抓手

将 callback review decision 的结论转成跨 owner 的 review handoff：

- 从“是否接受 callback material”进入“交给谁补哪些真实材料”。
- 从 raw artifact 进入 safe summary。
- 从 PC-only 进入 Robot diagnostics 和 phone-safe 可见状态。
- 从本地 proof 进入明确的真实材料待补清单。

## 范围边界

### In Scope

- `hardware_sensor_hil_entry_callback_review_handoff` PC gate planning。
- `robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary` safe alias planning。
- mobile/web read-only panel planning。
- 保留 `software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate`、`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 后续实现必须同步更新对应 `docs/`。

### Out Of Scope

- 不声明真实 2D LiDAR / ToF。
- 不声明 WAVE ROVER/UART/HIL。
- 不声明 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved。
- 不声明 Objective 5 external proof。
- 不声明 real phone/browser。
- 不声明 route/elevator field pass。
- 不声明 delivery success。
- 不改产品代码、测试、`OKR.md` 或 `docs/process`；本轮只写 planning docs。

## 优先级和验收口径

P0：三个 owner 的实现任务必须互不覆盖文件范围，并能并行启动。

P0：所有实现输出必须在 schema、fixture、docs 和 sprint docs 中保留：

- `software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

P0：任何 summary 或 panel 都不能触发 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、diagnostics fetch side effect、handoff route、callback route、review route、Nav2 或 robot command。

P1：对用户展示只允许安全摘要：handoff status、source review decision status、safe evidence ref、missing required materials、next required evidence、owner handoff、evidence boundary 和 non-claims。

P1：Engineer 后续实现要给出 focused tests、schema/fixture sanity、scoped `git diff --check`，并报告失败定位。

## 对应责任 Engineer

- Hardware Infra Engineer：PC gate、schema、tests、source-boundary docs。
- Robot Platform Engineer：operator diagnostics safe alias、scrub/fail-closed behavior、diagnostics tests、runtime contract docs。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、mobile tests、mobile user-flow docs。
- Product Manager / OKR Owner：后续阶段验收、side2side、final、OKR/progress 保守 closeout。

## 风险、阻塞和需要补齐的证据链

- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 未到位，Objective 1 不应上调。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 未解决，不得由 software proof 自动关闭。
- 本机无真实硬件，不能证明 WAVE ROVER/UART/HIL、T=1001 feedback、真实 odom/imu/battery。
- 本机无真实外部云材料，Objective 5 不应上调。
- mobile/web 只读 panel 不等于真实手机/browser 验收。
- route/elevator field pass、dropoff/cancel completion、delivery result 和 delivery success 仍需真实现场材料。
