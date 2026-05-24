# Pre Start - PR5 mandatory sensor material owner-response review handoff

- sprint_type: epic
- sprint: `2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff`
- planned start time: 2026-05-24 11:02 Asia/Shanghai
- Product owner: `product-okr-owner`
- implementation owners: `hardware-engineer`, `robot-software-engineer`, `full-stack-software-engineer`
- planned boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`

## 开工依据

本轮不重启 intake，也不再做 generic blocker wrapper。上一轮
`sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision/final.md`
已完成 `pr5_mandatory_sensor_material_owner_response_review_decision`，明确下一步应推进
`pr5_mandatory_sensor_material_owner_response_review_handoff`。

GitHub live evidence：

- PR #5 已 merged/closed。
- PR #5 review thread `PRRT_kwDOSWB9286CJ3tQ` resolved。
- PR #5 review thread `PRRT_kwDOSWB9286CJ3tU` resolved。
- PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，当前阻塞语义是 `hardware_material_pending`。
- 评论 `3269642220` 只是 software-proof reply publication，不是 thread resolution。
- PR #7 当前 open；本轮不把 PR #7 当作 PR #5 material thread 的解除证据。

本地资料入口：

- 硬件事实和 vendor-source 归因必须从 `docs/vendor/VENDOR_INDEX.md` 开始。
- `docs/product/production_hardware_boundary.md` 已写明 local vendor coverage 只能证明 Orange Pi / WAVE ROVER / UART JSON / firmware / vendor app / camera references，不证明项目 2D LiDAR 或 ToF SKU、采购、安装、接线、电源、标定、HIL 或 Nav2/SLAM field pass。
- `docs/product/mobile_user_flow.md` 已存在 read-only panel / false-state flag 规则；本轮只能追加同一 fail-closed 模式。

## 用户价值和产品北极星

北极星仍是让普通手机用户完成低成本 ROS2 垃圾投递，而不是靠口头硬件假设推进。`PRRT_kwDOSWB9286CJ3tX` 卡住的是 mandatory sensor assumptions 的 repo-local vendor source 和真实材料证据链；本轮价值是把上一轮 review-decision 结果转换为可执行的三端 handoff，让硬件 owner、Robot diagnostics 和手机支持页面看到同一个安全材料缺口、同一个 `evidence_ref`、同一组下一步材料要求。

## OKR 映射

- Objective 5 当前约 68%，是 `OKR.md` 4.1 中完成度最低项；最近 08-09、09-10、10-11 三轮 O5 command lifecycle/export/support/intake 均是 Docker/local software proof，均 `no OKR percentage lift`。
- 本轮不继续推进 O5 外部云证明，因为缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 和 verified terminal result。
- 本轮主目标映射 Objective 1 的 hardware/vendor-source 缺口，并服务 Objective 4 手机只读支持面板；它不提升 Objective 1 或 Objective 5 百分比。

## 本轮核心抓手

创建 `pr5_mandatory_sensor_material_owner_response_review_handoff` 软件证明链：

1. Hardware 创建 PC handoff gate，消费上一轮 owner-response review-decision safe artifact/summary。
2. Robot 创建 diagnostics safe alias，只输出 sanitized handoff summary。
3. Full-Stack 创建 read-only mobile panel，展示 PR #5 unresolved / `hardware_material_pending`、owner/support/reviewer handoff 和下一步材料清单。
4. Product closeout 之后再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`；本轮规划阶段禁止提前更新。

## 非目标和证据边界

本轮必须持续写明：

- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`
- `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`

本轮不证明：

- real LiDAR/ToF proof
- WAVE ROVER/UART/HIL
- PR #5 thread resolution
- Objective 5 external proof
- public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover
- true phone/browser proof
- verified terminal result
- route/elevator/Nav2/fixed-route field pass
- delivery success

## 同一 Blocker 重复消费核对

最近三轮 O5 command lifecycle/export/support/intake 已连续输出 Docker/local software proof 且无 OKR 百分比提升，因此本轮不继续包一层 O5 local metadata wrapper。PR #5 unresolved sensor-source thread 是当前不同证据链：它要求 mandatory sensor assumptions 引用 repo-local vendor source，并明确真实材料仍 pending；本轮是从上一轮 review-decision 进入 review-handoff，不是重复同一 generic blocker。

## 需要更新的 sprint 文档

本规划阶段创建：

- `sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/pre_start.md`
- `sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/prd.md`
- `sprints/2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff/tech-plan.md`

实现完成后必须继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- Product closeout 后再更新 `OKR.md` 与 `docs/process/okr_progress_log.md`
