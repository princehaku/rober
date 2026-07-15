# PRD - O3 Live TF Receipt Capture

## 产品问题

TF receipt-time freshness 已离线修复，但还没有真实上位机 artifact 证明 callback receipt 字段和三类 age
在 current runtime 中可复算。继续做离线测试或 readiness/readback wrapper 不会提升 mission evidence；需要一次
严格无运动、无 topic write、无底盘控制的现场采集。

## 产品北极星与 OKR 映射

- 北极星：同一真实机器人运行窗口内，定位与 TF 证据可信、可归因、可复算，为后续受控 route execution
  提供安全前置条件。
- 直接推进 O3 current localization evidence chain，并支持 O1 的 live route/HIL 准入；本轮不声称 O1 HIL。
- O5 约 `85%` 仍最低，但本轮真实上位机审计确认缺公网 tunnel/runtime/endpoint/凭证，且 support wrapper
  已退役；因此按规则转向当前可执行的下一低进度链。

## 核心抓手

使用当前已验证 helper，在上位机启动一次 helper-owned strict-no-motion localization-only runtime，采集：

1. map_server/AMCL lifecycle 与 helper-owned process group 边界；
2. 当前 `/scan`、`/amcl_pose`、`/tf`、`/tf_static` 可见性与 callback receipt；
3. dynamic `map->odom` 的 header、receipt、evaluation time 与三类 age；
4. 缺失或 stale 时的 exact fail-closed reason；
5. cleanup 后 process/graph residual。

## 验收口径

### 必须满足

- 本地 `py_compile` 与 targeted unittest 先通过，remote helper SHA 与 local SHA 一致。
- 只执行一次最终 live helper capture；若首次命令在 helper 进入 runtime 前因部署/命令拼写失败且完全未启动
  runtime，可修复后执行唯一 final capture，并在 `tech-done.md` 记录两者边界。
- 命令包含 `--strict-no-motion --no-base-uart --managed-runtime-opt-in`，且不包含
  `--initialpose-opt-in`、`--path-generation-opt-in`。
- artifact 明确 `managed_runtime_started`、cleanup 结果、`uses_base_uart=false`、`publishes_cmd_vel=false`、
  `calls_base_manual=false`、`robot_control_executed=false`、route/delivery/HIL false。
- 每个 rclpy TF transform 保留 `received_at_ms`；若 dynamic `map->odom` 存在，三类 age 必须按整数等式复算，
  clean decision 使用 `header_age_at_receipt_ms`，threshold 保持 `3000ms`。
- 若 dynamic edge 缺失、receipt 非法或 runtime 前置失败，必须输出 exact blocker 并 fail closed，不能伪造
  success，也不能发布 `/initialpose` 解锁。
- 拉回本 sprint 自有 artifact，更新 `docs/navigation/field_route_evidence_preflight.md` 与 `tech-done.md`。

### Mission Objective 0 判定

- 新 live runtime artifact 可令 `current_run_artifact_delta=true`；但只有 route/delivery/current HIL/user action
  或 production external evidence 出现时才可满足 Mission Objective 0。
- 本轮默认 `external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`；不得用无运动
  localization artifact 冒充 mission closure。

## 明确拒绝项

- 禁止任何 `/initialpose` 发布、planner/controller/path、NavigateToPose、`/cmd_vel`、`/api/base/manual`。
- 禁止打开 WAVE ROVER UART、发送 JSON 控制、运动、route execution、delivery 或 HIL。
- 禁止安装 tunnel provider、改远端 systemd/launch/config、修改硬件参数或读取/输出 credential。
- 禁止重写旧 sprint artifact，或把本轮失败改包装成新的 preflight/readback 合同。

## 责任与证据链

- Owner：`robot-algorithm-engineer`。
- 工程证据：本地测试日志、local/remote helper SHA、唯一 live command/exit、runtime artifact、cleanup residual、
  forbidden-action assertions、导航文档与 `tech-done.md`。
- Product 收口：工程证据完整后，再生成 `side2side_check.md`、`final.md` 并保守更新 `OKR.md` 和
  `docs/process/okr_progress_log.md`；未满足 Mission Objective 0 时主百分比保持不变。
