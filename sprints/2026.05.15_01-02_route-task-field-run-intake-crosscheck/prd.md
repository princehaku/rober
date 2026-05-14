# Sprint 2026.05.15_01-02 Route Task Field Run Intake Crosscheck - PRD

sprint_type: epic

## 1. 产品背景

上一轮 `2026.05.15_00-01_route-task-field-run-readiness` 已经把路线/任务现场联跑前的材料清单、同一 `evidence_ref` 要求和 phone-safe 复盘口径做成 Docker/local readiness handoff。

现在的问题不是继续证明 readiness，而是进入下一层：现场人员拿到 route status、task record、Nav2/fixed-route runtime log、robot-side task evidence、support-safe mobile summary 后，系统必须能用同一 `evidence_ref` 接收、校验、分类和给出补跑命令。

## 2. 用户价值和产品北极星

- 用户价值：现场人员只需要围绕一个 `evidence_ref` 收集材料，系统能判断材料是否齐、是否互相匹配、还不能证明什么，以及应该补跑哪些命令。
- 产品北极星：普通手机用户和售后人员能从只读 mobile/diagnostics 摘要理解一次 route-task field run 的复盘状态，而不是阅读 raw ROS2 日志、串口输出或云端基础设施细节。
- 成功标准不是 delivery success；成功标准是 intake/crosscheck 软件能力能保守地区分 `missing`、`mismatch`、`not_proven` 和 `commands_to_rerun`。

## 3. OKR 映射

- Objective 2：可送垃圾任务完整闭环。
  - 对应 KR5：每次任务产出可复盘记录。
  - 本轮推进点：把 task record、robot-side task evidence 和 mobile support summary 纳入同一 `evidence_ref` crosscheck。
- Objective 3：可验证导航与固定路线能力。
  - 对应 KR2 / KR3 / KR5：route 数据、fixed-route dry-run、PC debug/任务状态复盘。
  - 本轮推进点：把 route status、Nav2/fixed-route runtime log 和 PC/debug 摘要纳入 intake artifact。
- Objective 5：云中转 + OSS/CDN 数据通路产品化。
  - 当前约 68% 仍最低，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
  - 本轮不推进 O5 external proof，也不把本地 intake/crosscheck metadata 计入 O5 完成。
- Objective 1：硬件协议可信底盘。
  - 当前仍缺真实 WAVE ROVER、串口/UART、`T=1001` feedback 和 HIL。
  - 本轮不推进 O1，也不把任何 Docker/local proof 写成 `hil_pass`。

## 4. KR 拆解或更新

- KR-A：field-run intake artifact 能接收以下材料引用或摘要：route status、task record、Nav2/fixed-route runtime log、robot-side task evidence、support-safe mobile summary。
- KR-B：所有材料必须通过同一 `evidence_ref` 交叉核对；缺失输出 `missing_materials`，不一致输出 `mismatch_reasons`。
- KR-C：artifact 必须输出 `not_proven`，至少覆盖真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、串口/UART、HIL、dropoff/cancel completion、delivery success、Objective 5 external proof。
- KR-D：artifact 必须输出 `commands_to_rerun`，用于提示下一次应补采 route status、task record、runtime log、robot-side task evidence 或 mobile summary。
- KR-E：diagnostics/mobile 只能只读消费 support-safe summary；不得读取 raw artifact、不得改变 Start/Confirm/Cancel gating、不得触发机器人动作或 ACK/cursor。

## 5. 本轮核心抓手

本轮核心抓手是 `route_task_field_run_intake`。它把上一轮 readiness 的“下一次要收什么”升级为“已经收到什么、哪些对不上、哪些还没证明、需要补跑什么”。

推荐 schema / boundary：

- `schema=trashbot.route_task_field_run_intake_crosscheck.v1`
- `evidence_boundary=software_proof_docker_route_task_field_run_intake_crosscheck_gate`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`

## 6. 范围内需求

1. 支持接收材料引用：
   - `route_status_ref`
   - `task_record_ref`
   - `runtime_log_ref`
   - `robot_side_task_evidence_ref`
   - `support_safe_mobile_summary_ref`
2. 支持 JSON object 输入校验：
   - schema 支持和兼容 summary 判定。
   - `evidence_ref` 提取和一致性校验。
   - material-level `load_status` / `load_issue`。
3. 输出复盘分类：
   - `overall_status=ready_for_review|blocked_missing_material|blocked_mismatch|blocked_unsafe_summary`
   - `missing_materials`
   - `mismatch_reasons`
   - `commands_to_rerun`
   - `not_proven`
4. 输出 phone-safe summary：
   - 只包含状态、同一 `evidence_ref`、材料 readiness、缺失/不一致摘要、补跑命令摘要、证据边界和 `not_proven`。
   - 不包含 raw artifact、完整本地路径、凭证、ROS 控制 topic、串口/UART、baudrate、WAVE ROVER 参数、DB/queue URL、OSS AK/SK、traceback 或 checksum。
5. diagnostics/mobile 只读消费该 summary：
   - metadata-only。
   - 不触发 collect/dropoff/cancel。
   - 不 POST ACK。
   - 不推进 cursor。
   - 不触发 Nav2/fixed-route 或 HIL。

## 7. 范围外

- 不执行真实 Nav2/fixed-route。
- 不采集真实路线。
- 不连接 WAVE ROVER、串口/UART 或 HIL。
- 不证明真实 dropoff/cancel completion。
- 不证明 delivery success。
- 不证明 Objective 5 external cloud/4G/OSS/CDN/DB/queue。
- 不修改生产云、worker、migration 或公网 HTTPS/TLS。
- 不把 mobile/diagnostics 只读摘要作为控制授权。

## 8. 优先级和验收口径

- P0：CLI / artifact 能对齐同一 `evidence_ref`，并在 missing/mismatch 场景保守失败。
- P0：diagnostics metadata-only 消费，不触发任何机器人动作或 ACK/cursor。
- P1：mobile/web 展示只读 intake/crosscheck summary 和 commands_to_rerun，不改变 Start/Confirm/Cancel gating。
- P1：docs 同步更新，明确 `software_proof_docker_route_task_field_run_intake_crosscheck_gate` 只等于 Docker/local software proof。

验收口径：

- 单元测试覆盖 happy path、missing material、mismatch `evidence_ref`、unsupported schema、unsafe summary redaction。
- diagnostics test 覆盖 metadata-only fence。
- mobile test 覆盖只读渲染、缺失 fallback、button gating 不变。
- `rg` 必须命中新 schema/boundary、Objective 2/3/5、`not_proven`、`delivery success`、`HIL`、`OKR 最低优先级核对`。
- scoped `git diff --check` 必须通过。

## 9. 对应责任 Engineer

- `autonomy-engineer`：主责 intake/crosscheck CLI、artifact schema、PC/navigation 文档、CLI 单元测试。
- `robot-software-engineer`：主责 operator diagnostics summary、robot-side metadata-only fence、interfaces 文档、diagnostics 单元测试。
- `full-stack-software-engineer`：主责 mobile/web 只读 panel、fixture、entrypoint tests、product 文档。
- `product-okr-owner`：负责本 sprint 收口、OKR 证据边界、progress log 和 final 复盘；本 planning 阶段不修改 `OKR.md`。

## 10. 风险、阻塞和证据链

- 最大风险：把材料齐全误写成 delivery success。防线：artifact 顶层固定 `delivery_success=false`，`not_proven` 必须保留真实 Nav2/fixed-route、HIL、dropoff/cancel completion 和 O5 external proof。
- 证据混淆风险：不同 `evidence_ref` 材料被合并。防线：任何不一致输出 `blocked_mismatch` 和 commands_to_rerun。
- 手机误导风险：用户看到“ready_for_review”后误以为可发车。防线：mobile 只读；Start/Confirm/Cancel gating 不变；summary 写明 accepted/processing/support metadata only。
- 安全泄露风险：raw artifact 或路径/凭证进入 mobile copy。防线：白名单输出和 unsafe summary tests。
- 外部依赖阻塞：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；本轮明确不推进 Objective 5 external proof。

## 11. 需要创建或更新的 sprint 文档

- 已创建/更新：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现后必须继续更新：`tech-done.md`、`side2side_check.md`、`final.md`。
- 实现后如 OKR 证据足够，Product Owner 再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`；planning 阶段不修改。
