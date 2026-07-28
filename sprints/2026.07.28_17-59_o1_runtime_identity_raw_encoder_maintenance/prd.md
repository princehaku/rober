# PRD：O1 runtime identity / raw encoder 独占维护

## 状态

- `status: planning_complete`
- `sprint_type: epic`
- `O1_EXCLUSIVE_SERVICE_UART_FIRMWARE_MAINTENANCE_AUTHORIZED=true`
- CEO 继续证据：“我都授权过了”“继续推进啊”
- 授权不得再次确认；本 PRD 完成后直接派 `rober-hardware-engineer`。

## 产品问题

当前底盘命令链已证明真实非零动作与最终停车，但同窗 `T=1001 L/R=0/0`。旧诊断只确认参考 vendor 源存在 encoder update
path、bridge parser 与已见 frame 一致，却无法回答目标 ESP32 实际运行什么 firmware、runtime `mainType` 是多少、encoder
原始计数是否变化。缺少这些事实时，继续运动只会重复猜测，也不能把 `hil_pass` 或 `safe_to_control` 标为 true。

本 Epic 必须在已授权的独占维护窗口中把 runtime identity 与 raw counter 变成 current、结构化、可回滚证据；必要时才实施
最小 vendor-sourced instrumentation/build/flash，并在 counter/feedback 可观测之后执行至多一次最小受监督运动验证。

## 用户价值、OKR 与方向

- 产品北极星：可信、安全、可解释的真实底盘控制与反馈闭环。
- Objective：O1，当前约 `95%`，方向为继续。
- 最低 Objective O5 约 `85%`，但 production external evidence gate 未打开且同根因已 `2/2`，本轮不得再做 O5 local wrapper。
- 本轮抓手：把 `runtime_firmware_identity_not_observed`、`runtime_main_type_not_observed`、
  `encoder_update_path_not_observed` 推进为 current maintenance evidence。
- KR 在 Product final 验收前不归档；完成 instrumentation/build/flash 不能自动调分。

## 功能需求

1. 实现单一、不可重入的 maintenance runner，支持离线/mock 与真实 SSH 两种模式；真实入口固定
   `ssh root@192.168.1.11 -p 37878`。
2. 开始任何 mutation 前冻结 service unit、进程、holder、`/dev/ttyS5@115200`、部署文件 hash、vendor source hash、
   可用 firmware/toolchain、运行参数与 rollback manifest。
3. 先通过已部署接口、startup/readback、UART echo/feedback 和 vendor `T=900` 形成无运动 runtime identity/mainType 证据。
   `T=900` 发送/echo 只能证明 current maintenance command 已送达，不能单独冒充 runtime readback。
4. 在 bridge service 已安全 stop、holder 已释放且 exclusivity 已证明后，runner 才可直接打开 `/dev/ttyS5@115200`。所有 UART
   frame 必须使用 vendor UTF-8 newline-delimited JSON。
5. raw encoder A/B counters 必须以 current、machine-readable 字段进入 artifact；静止窗口先证明字段存在、类型合法和时间戳
   连续。若现有 firmware 不暴露 counters，才进入 instrumentation 分支。
6. instrumentation 必须从 canonical vendor V0.9 source 派生，最小 additive 暴露 firmware build identity、runtime
   `mainType`、module type、encoder A/B raw counts 与 `speedGetA/speedGetB`；不得改写 `docs/vendor/` 或 factory binary。
7. firmware build/upload 必须先证明 board/toolchain/upload port 与 rollback 可用；采用仓库既有
   `onboard/src/esp32_firmware/**` / PlatformIO 能力时必须明确它与 vendor newline-JSON firmware 的 provenance 和差异，
   禁止把仓库中的非 vendor binary-protocol 示例直接刷到 WAVE ROVER。
8. flash 后先做无运动 readback；只有 firmware/runtime/counter 字段 current 可读、service/holder 状态可控、operator 在场、
   路线清空且物理限位仍成立，才允许一次冻结参数的 supervised minimal motion。
9. minimal motion 必须 exactly once：pre-stop=`1`、nonzero=`1`、post-stop=`1`、retry=`0`；异常进入 finally stop/rollback，
   不得第二次 nonzero。最终必须确认零命令、wheel stopped、service/holder 恢复。
10. 无论成功或失败，都输出 current artifact、命令 ledger、每步 started/ended/exit、hash/provenance、counters、rollback 和
    `tech-done.md`；工具链/刷写入口不可用时仍要输出真实 blocker 和当前 runtime/raw-counter fail-closed artifact。

## Artifact 合同

主 artifact schema 固定为 `trashbot.wave_rover.runtime_identity_raw_encoder_maintenance.v1`，至少包含：

- `attempt_id`、`authorization_id`、`captured_at`、`host_identity_hash_prefix`
- `vendor_source_hashes`、`deployed_file_hashes_before/after`、`firmware_identity_before/after`
- `runtime_main_type_before/after`、`module_type_before/after`
- `raw_encoder_a_samples`、`raw_encoder_b_samples`、`raw_counter_delta_a/b`
- `t1001_samples`、`feedback_nonzero_observed`
- `toolchain_inventory`、`instrumentation_required`、`build_count`、`flash_count`
- `phase_counts`、完整 command ledger、rollback manifest/result、service/holder before/after
- `current_run_artifact_delta`、`external_artifact_delta`、`live_control_delta`
- 安全字段：`instrumentation_success`、`hil_pass`、`safe_to_control`、`route_execution_success`、
  `delivery_success`、`mission_attempt`

artifact 对缺字段、危险真值、非 current 样本、attempt mismatch、hash/provenance 缺失、stop/rollback 未确认全部 fail closed。
默认并持续固定 `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、
`delivery_success=false`、`mission_attempt=false`；只有 Product final 可依据完整 current evidence 调整允许的结论。

## 验收口径

- py_compile、targeted unittest、离线/mock fixture、JSON parse/schema/safety assertions、中文技术注释比例 `>20%` 和 scoped diff
  全部通过。
- 真实 maintenance runner 恰好执行一次，留下 current inventory、runtime/counter 或明确 blocked artifact，且每个远端 action
  都在 allowlist 中。
- mutation 前后的 service/holder/hash/provenance 可对照，rollback 可执行并有 final result。
- counter 不可观测时 motion count 必须为 `0`；counter 可观测后 motion 最多 `1`，pre/post stop 都为 `1`，retry 为 `0`。
- instrumentation success 不得被解释为 HIL、route execution、delivery、mission 或 `safe_to_control`。
- `tech-done.md` 必须记录实际文件、原始验证摘要、首轮失败与修复、现场 ledger、剩余风险；Product 后续再做
  side-to-side/final/OKR 收口。

## 非功能与拒绝项

- 所有新增/修改代码的技术注释必须为中文且有意义注释比例严格 `>20%`。
- artifacts 不得泄露凭证、完整环境变量、Wi-Fi 配置或不必要的绝对路径；只保留安全 basename/hash。
- 不允许并行进程争抢 UART，不允许覆盖 factory binary，不允许无 rollback 的 flash，不允许自动 retry motion。
- 不接受 planning、mock-only happy path、build success、flash success 或静止 counter=0 单独作为 HIL 完成。
