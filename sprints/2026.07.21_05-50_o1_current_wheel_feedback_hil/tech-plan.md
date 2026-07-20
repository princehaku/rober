# Tech Plan：O1 当前轮速反馈 HIL

## OKR 最低优先级核对

- 数字最低 Objective 为 O5（85%）；其 provider/runtime 前置证据已达到 `2/2`，继续消费只会重复已有 surface，因此本轮暂停。
- O6/O7 均为 93%，当前受未授权 systemd holder 维护窗限制，不得在本授权内推进。
- 本 sprint 针对 O1（95%）：CEO 已给出受控运动授权，且当前可执行缺口是 during-motion 非零 `T=1001 L/R` 与 dedicated post-stop `0/0`。这是一次可产生 mission/HIL 证据的窗口，不是规划替代物。
- final 收口时必须复核：O5 暂停及 O6/O7 holder blocker 是否仍成立；不得因本轮文档或失败而上调任何完成度。

## Owner 与执行边界

- 主责：`robot-hardware-engineer`，单 owner 闭环执行、采集、停止、验证与留档。
- 授权 ID：`ceo_20260721_0651_current_wheel_feedback_hil_v8`；初始状态 `frozen_unconsumed`。
- 唯一连接入口：`ssh root@192.168.1.11 -p 37878`。
- Hardware 执行时只允许改本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`、`artifacts/`；必要 `docs/`、`OKR.md`、progress 更新必须等待 Product 验收后允许。
- 禁止触碰 `06-20`、`06-45` WIP；禁止暂存、提交、推送现有 dirty worktree。
- 本文件内 live 命令是交给 Hardware 的执行合同，本轮 Product writer 只做静态校验，绝不执行。

## Vendor 事实基线

执行前必须重新核对以下本地资料，不凭记忆解释协议：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/` 索引指向的 `json_cmd.h`
- `docs/vendor/` 索引指向的 `uart_ctrl.h`
- `docs/vendor/` 索引指向的 `ugv_advance.h`
- `docs/vendor/` 索引指向的 `movtion_module.h`
- 仓库内与当前桥接对应的 `base_ctrl.py`

本 sprint 采用的协议事实：`T=13` 为 `CMD_ROS_CTRL`，`T=130` 为 `CMD_BASE_FEEDBACK`，`T=1001` 的 `L/R` 来自 `speedGetA/speedGetB`。上层请求、bridge 日志或 Upper receipt 不能单独证明 wire 上出现 `T=13`；除非 raw serial 实际捕获到它，否则结论必须写 `T=13 wire not proven`。

## 文件范围

Hardware owner 可创建或更新：

- `sprints/2026.07.21_05-50_o1_current_wheel_feedback_hil/artifacts/**`
- `sprints/2026.07.21_05-50_o1_current_wheel_feedback_hil/tech-done.md`
- `sprints/2026.07.21_05-50_o1_current_wheel_feedback_hil/side2side_check.md`
- `sprints/2026.07.21_05-50_o1_current_wheel_feedback_hil/final.md`

只有 Product 验收后明确允许，才可更新必要的 `docs/**`、`OKR.md`、`docs/process/okr_progress_log.md`。不得修改其他代码、配置、service、holder、既有 sprint 或其他 owner WIP。

## 执行变量与产物约定

Hardware 在受控终端显式设置以下变量；`CONTROL_URL` 必须是当前部署中已验证的唯一控制入口，不得在本 sprint 临时新增接口：

```bash
export SPRINT_DIR=/root/rober/sprints/2026.07.21_05-50_o1_current_wheel_feedback_hil
export ARTIFACT_DIR="$SPRINT_DIR/artifacts"
export AUTHORIZATION_ID=ceo_20260721_0651_current_wheel_feedback_hil_v8
export CONTROL_URL='REPLACE_WITH_VERIFIED_DEPLOYED_CONTROL_URL'
export HEALTH_URL='REPLACE_WITH_VERIFIED_DEPLOYED_HEALTH_URL'
export CONTROL_SERVICE='REPLACE_WITH_VERIFIED_CONTROL_SERVICE'
mkdir -p "$ARTIFACT_DIR"
test "$CONTROL_URL" != REPLACE_WITH_VERIFIED_DEPLOYED_CONTROL_URL
test "$HEALTH_URL" != REPLACE_WITH_VERIFIED_DEPLOYED_HEALTH_URL
test "$CONTROL_SERVICE" != REPLACE_WITH_VERIFIED_CONTROL_SERVICE
```

部署值必须来自 Phase0 的当前只读发现并原样写入 artifact；变量未替换就是 Phase0 false，禁止非零请求。

## Phase0：只读 gates

由唯一 control owner 在 operator 看护、路线清空、小车物理限位且 emergency stop 已就绪后执行。所有检查仅允许读取，不得 restart/start/stop/enable/disable systemd，不得写 ROS、串口或控制接口：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; date -Ins; systemctl is-active "$CONTROL_SERVICE"; curl -fsS "$HEALTH_URL"; ps -eo pid,user,args; ss -lntp' > "$ARTIFACT_DIR/phase0_readonly.log"
test "$(jq -r '.unique_control_owner' "$ARTIFACT_DIR/phase0.json")" = true
test "$(jq -r '.service_active' "$ARTIFACT_DIR/phase0.json")" = true
test "$(jq -r '.health_ok' "$ARTIFACT_DIR/phase0.json")" = true
test "$(jq -r '.stopped' "$ARTIFACT_DIR/phase0.json")" = true
test "$(jq -r '.no_active_hold' "$ARTIFACT_DIR/phase0.json")" = true
test "$(jq -r '.feedback_path_ok' "$ARTIFACT_DIR/phase0.json")" = true
test "$(jq -r '.operator_present' "$ARTIFACT_DIR/phase0.json")" = true
test "$(jq -r '.route_clear' "$ARTIFACT_DIR/phase0.json")" = true
test "$(jq -r '.physical_limit_ready' "$ARTIFACT_DIR/phase0.json")" = true
test "$(jq -r '.emergency_stop_ready' "$ARTIFACT_DIR/phase0.json")" = true
```

`phase0.json` 必须由 Hardware 根据现场逐项确认并带时间戳生成。任一 gate 为 false 或命令失败：立刻 abort 于 nonzero 之前，记录 `authorization_status=frozen_unconsumed`，不得调用 `CONTROL_URL`。

## 冻结请求、SHA 与 pre-stop

`frozen_nonzero_request.json` 必须使用当前已部署控制 API 的真实 schema，且显式绑定 authorization、速度和时长；不得把 HTTP JSON schema 冒充 WAVE ROVER wire schema：

```bash
jq -e --arg auth "$AUTHORIZATION_ID" '
  .authorization_id == $auth and
  (.forward_mps | type == "number") and .forward_mps > 0 and .forward_mps <= 0.08 and
  (.duration_ms | type == "number") and .duration_ms > 0 and .duration_ms <= 300 and
  .retry == 0
' "$ARTIFACT_DIR/frozen_nonzero_request.json"
jq -S . "$ARTIFACT_DIR/frozen_nonzero_request.json" > "$ARTIFACT_DIR/frozen_nonzero_request.canonical.json"
shasum -a 256 "$ARTIFACT_DIR/frozen_nonzero_request.canonical.json" | tee "$ARTIFACT_DIR/frozen_nonzero_request.sha256"
jq -e '.T == 130' "$ARTIFACT_DIR/pre_stop_t130_request.json"
jq -e '.T == 1001 and .L == 0 and .R == 0' "$ARTIFACT_DIR/pre_stop_t1001.json"
```

pre-stop 必须包含 `T=130` 请求、bridge/serial/raw `T=1001 L/R=0/0` 与对应 Upper receipt，且与 Phase0 同一执行窗口。

## 唯一一次 nonzero transport attempt

先由 operator 再次口头确认路线清空、物理限位和 emergency stop。以下 `curl` 是本授权唯一允许的非零 transport 调用，必须从冻结 stdin 读取；禁止复制、循环、shell retry、curl `--retry` 或第二次调用：

```bash
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  --data-binary @- \
  "$CONTROL_URL" \
  < "$ARTIFACT_DIR/frozen_nonzero_request.canonical.json" \
  > "$ARTIFACT_DIR/nonzero_transport_response.json"
```

一旦该命令开始传输，即把 authorization 记为 `consumed_no_retry`；无论返回、采集或验收成功与否，均不得再运行这条命令。并行只读采集必须覆盖：

- `T=130` feedback request；
- bridge/serial/raw `T=1001`，运动期间至少一侧 `L/R != 0`；
- Upper request/response receipts、时间戳、attempt id、请求 SHA；
- raw serial 若实际看到 `T=13 CMD_ROS_CTRL` 才能写 `T=13 wire observed`，否则写 `T=13 wire not proven`。

## Dedicated stop 与失败 no-retry cleanup

唯一 attempt 后必须立即用当前部署的专用 stop 入口执行一次 stop；stop request 必须提前冻结为 `dedicated_stop_request.canonical.json`，且它不能包含非零速度。失败路径与成功路径使用同一 cleanup，不得重放 nonzero：

```bash
jq -e '
  ((.forward_mps // 0) == 0) and
  ((.linear_x // 0) == 0) and
  ((.left // 0) == 0) and
  ((.right // 0) == 0)
' "$ARTIFACT_DIR/dedicated_stop_request.canonical.json"
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  --data-binary @- \
  "$CONTROL_URL" \
  < "$ARTIFACT_DIR/dedicated_stop_request.canonical.json" \
  > "$ARTIFACT_DIR/dedicated_stop_response.json"
jq -e '.T == 130' "$ARTIFACT_DIR/post_stop_t130_request.json"
jq -e '.T == 1001 and .L == 0 and .R == 0' "$ARTIFACT_DIR/post_stop_t1001.json"
```

若 control response、feedback 或 artifact 校验失败，仍先完成 stop 和 post-stop 只读确认，再写入 `retry=0`、`no-retry=true`、失败点与 `authorization_status=consumed_no_retry`。若唯一 nonzero 命令从未开始传输，则保持 `frozen_unconsumed`。

## Hardware 验收命令

```bash
python3 -m json.tool "$ARTIFACT_DIR/phase0.json" >/dev/null
python3 -m json.tool "$ARTIFACT_DIR/nonzero_transport_response.json" >/dev/null
python3 -m json.tool "$ARTIFACT_DIR/dedicated_stop_response.json" >/dev/null
jq -e '.pre_stop == 1 and .nonzero == 1 and .post_stop == 1 and .retry == 0' "$ARTIFACT_DIR/acceptance_summary.json"
jq -e '.authorization_id == "ceo_20260721_0651_current_wheel_feedback_hil_v8" and (.authorization_status == "frozen_unconsumed" or .authorization_status == "consumed_no_retry")' "$ARTIFACT_DIR/acceptance_summary.json"
jq -e '.T == 1001 and ((.L != 0) or (.R != 0))' "$ARTIFACT_DIR/during_motion_t1001.json"
jq -e '.T == 1001 and .L == 0 and .R == 0' "$ARTIFACT_DIR/post_stop_t1001.json"
rg -n 'T=13|T=130|T=1001|CMD_ROS_CTRL|CMD_BASE_FEEDBACK|speedGetA|speedGetB|wire not proven|consumed_no_retry|frozen_unconsumed|no-retry|retry=0' "$SPRINT_DIR"
git diff --check -- "$SPRINT_DIR"
git status --short -- "$SPRINT_DIR"
```

Hardware 必须同时人工核对 exactly-once：只有一份 nonzero transport receipt，pre-stop/nonzero/post-stop 计数为 `1/1/1`，dedicated stop 在唯一 attempt 之后。不得运行任何自动重试工具。

## 验收判定与证据边界

- Phase0 false：`hil_pass=false`，授权保持 `frozen_unconsumed`，无 nonzero receipt。
- 唯一 attempt 已发但证据不全：`hil_pass=false`，状态 `consumed_no_retry`，stop 后收口，不重试。
- 仅当三段 `1/1/1`、during-motion raw `T=1001 L/R` 非零、post-stop raw `0/0`、receipt 关联和 stop 都成立时，本 PRD 的 `hil_pass` 才可为 true。
- 即使 `hil_pass=true`，也不得自动推导 `safe_to_control=true`、`route_execution_success=true` 或 `delivery_success=true`。

## 风险与关闭条件

- 一次短窗口不足以证明持续可靠性；轮空转/打滑也不证明真实位移。
- raw serial 丢帧会导致 wire 证据不足，但不能因此进行第二次非零尝试。
- systemd holder、服务重启、反馈链修复若需要状态变更，超出本授权并触发暂停。
- `06-20`、`06-45` 或其他 dirty WIP 若发生变化，不得覆盖、暂存或纳入本 sprint。
- `tech-done.md` 必须记录实际命令、原始输出摘要、失败定位和剩余风险；`side2side_check.md` 记录 Product 对照验收；`final.md` 记录 OKR 是否保持、调整或暂停以及授权最终状态。
