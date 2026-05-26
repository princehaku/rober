# PRD - PR5 mandatory sensor material owner-response review handoff

- sprint_type: epic
- sprint: `2026.05.24_11-12_pr5-mandatory-sensor-material-owner-response-review-handoff`
- target capability: `pr5_mandatory_sensor_material_owner_response_review_handoff`
- proof boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`

## 用户价值和产品北极星

普通用户不关心 PR thread，也不会判断 2D LiDAR / ToF 的采购、安装、接线、标定和 HIL 材料是否齐全。产品要把“mandatory sensor assumptions 是否可信”翻译为一个安全、可追溯、可交接的材料状态：当前 thread `PRRT_kwDOSWB9286CJ3tX` 仍是 `hardware_material_pending`，下一步必须由硬件 owner 补齐真实材料，而手机和 Robot 只能展示只读支持信息，不能放开控制。

北极星：让低成本垃圾投递机器人所有关键硬件假设都能从 `docs/vendor/VENDOR_INDEX.md` 追溯到 repo-local source，并在真实材料缺失时 fail closed，不让 UI 或 diagnostics 把 software proof 误讲成 HIL、实机传感器或送达成功。

## OKR 映射

### Objective 1：硬件协议可信底盘

本轮主映射 Objective 1 的 vendor-source 与真实材料缺口：

- 继续承认 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。
- 将上一轮 owner-response review-decision 转成 owner/support/reviewer handoff。
- 明确 `docs/vendor/VENDOR_INDEX.md` 是 source-entry，但它不证明项目 2D LiDAR / ToF real SKU、receipt、mounting、wiring、power、calibration 或 HIL。

### Objective 4：手机用户体验与低成本量产边界

本轮支持 Objective 4 的只读用户触点：

- 手机端可显示材料缺口和下一步 owner action。
- Start Delivery、Confirm Dropoff、Cancel 仍由既有 fail-closed gates 控制。
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 必须可见。

### Objective 5：云中转 + OSS/CDN 数据通路产品化

Objective 5 当前约 68%，是 OKR 4.1 最低项。但最近 O5 三轮 command lifecycle/export/support/intake 都是 Docker/local `software_proof`，均 `no OKR percentage lift`，仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result。本轮不继续叠 O5 local wrapper。

## KR 拆解或更新

- KR-A Hardware：新增 PC handoff gate，把 `pr5_mandatory_sensor_material_owner_response_review_decision` safe input 转为 `pr5_mandatory_sensor_material_owner_response_review_handoff` safe artifact/summary。
- KR-B Robot：新增 diagnostics safe alias，让 `/api/status` 和 `/api/diagnostics` 可消费同一 sanitized summary，不泄漏 raw artifact、raw diagnostics、local path、checksum、credentials、serial/UART detail 或 control endpoint。
- KR-C Full-Stack：新增 `mobile/web` read-only panel，展示 handoff status、source review decision、PR #5 thread status、`hardware_material_pending`、owner/support/reviewer handoff、next required evidence、safe copy 和 false-state flags。
- KR-D Product Closeout：实现验收后再更新 sprint closeout、`OKR.md` 与 `docs/process/okr_progress_log.md`；预计仍 `no OKR percentage lift`，除非真实材料或 GitHub reviewer resolution 同步出现。

## 本轮核心抓手

本轮不是“解释为什么没硬件”，而是把 owner-response review-decision 推进到 review-handoff，让下一位执行同学可以直接拿到：

- 同一个 safe `evidence_ref`。
- 同一个 PR thread status：`PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。
- 同一组 next required evidence：2D LiDAR SKU/source/receipt、ToF SKU/source/channel-count material、mounting/wiring/power plan、calibration material、HIL-entry material、Nav2/SLAM field-pass material。
- 同一组 false-state flags：`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 需要做什么

1. Hardware 创建 PC handoff gate。
2. Robot 创建 diagnostics safe alias。
3. Full-Stack 创建 read-only mobile panel。
4. Product 完成 side-by-side 验收与 final 收口后，再更新 `OKR.md` / progress log。

## 优先级和验收口径

P0：

- 必须从上一轮 review-decision 进入 `pr5_mandatory_sensor_material_owner_response_review_handoff`，不得回退到 intake。
- 必须包含 `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`。
- 必须展示 `PRRT_kwDOSWB9286CJ3tX`、`hardware_material_pending`、`docs/vendor/VENDOR_INDEX.md`、`no OKR percentage lift`。
- 必须保留 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

P1：

- Robot 和 mobile 只能消费 sanitized summary / safe copy。
- mobile panel 必须 read-only，不新增 control path、review mutation、GitHub mutation、upload path 或 material fetch path。
- docs 必须同步说明边界，不把 source attribution 写成真实硬件证明。

P2：

- Product closeout 记录 PR #7 thread 查询若仍不可用或超时，不得据此宣称 PR #7 无 comments/reviews 已被再次确认。

## 对应责任 Engineer

- `robot-hardware-engineer`：PC handoff gate、fixture、targeted unit tests、hardware boundary docs。
- `robot-software-engineer`：Robot diagnostics safe alias、status/diagnostics exposure、targeted Robot tests、runtime contract docs。
- `full-stack-software-engineer`：read-only mobile panel、fixture、targeted mobile tests、mobile user flow docs。
- `product-okr-owner`：验收口径、side2side/final、OKR/progress closeout；本规划阶段不更新 `OKR.md`。

## 风险、阻塞和需要补齐的证据链

- 真实 2D LiDAR / ToF 材料仍缺失：不能写 real LiDAR/ToF proof。
- 无 WAVE ROVER/UART/HIL：不能写 hardware HIL pass。
- `PRRT_kwDOSWB9286CJ3tX` unresolved：不能写 PR #5 resolved。
- 当前主机只有 Docker/local：不能写 true phone/browser proof、public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 delivery success。
- PR #7 live comments/review-thread 工具查询如果超时，只能记录工具风险，不能替代 reviewer evidence。

## 需要创建或更新的 sprint 文档

本规划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现阶段完成后补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

Product closeout 之后再更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`
