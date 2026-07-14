# Tech Plan - O3 Map Server On-Configure Return Source Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target objective: O3/O1 strict no-motion field lane
- Product status: ready for Robot Software implementation
- Planned proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_on_configure_return_source_repair_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1/当前最高优先级中数字最低 Objective 是 O5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对 O5 的理由：O5 当前缺真实 external production evidence。继续做 O5 support-only readiness、review、handoff、intake 或 surface 会重复消费同一 blocker，且不能产生 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser evidence。本轮改走 O3/O1 strict no-motion field lane，解除 O1 current same-run path generation / Nav2 route execution 的 `/map_server` lifecycle 上游 blocker。
4. 方向判断：继续 O3/O1；O5 support-only 暂停；本轮不调整 OKR 百分比、不归档 KR。

## 用户价值和技术目标

用户价值是让真实上位机 fixed-route/nav 链路向同 run path generation 和 route execution 迈进。技术目标是解除或继续收窄 `/map_server` lifecycle 上游 blocker，避免继续停留在 15:54 的 timing 现象。

P0 技术目标：

- 优先证明 `/map_server active=true`；或
- 如果仍 blocked，证明比 `map_server_changestate_response_false_before_map_io_completion` 更窄的 `on_configure` return false source、参数、异常、executor/service future、map IO sync/async ordering 或 lifecycle manager response handling root cause。

## 现有 Root Cause Baseline

15:54 accepted baseline：

- `map_server_changestate_response_false_before_map_io_completion`
- `lifecycle_manager_changestate_response_false_while_map_io_completed_later`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_changestate_response_false_before_map_io_completion`
- `proof.map_server_transition_callback_probe.service_rpc_timing.changestate_response_false_before_map_io_completion=true`
- `proof.map_server_transition_callback_probe.service_rpc_timing.service_timeout_or_rpc_error_observed_in_log=false`
- `map_io_timing.image_load_to_state_failure_ms=43.624`
- `map_io_timing.state_failure_to_map_read_completed_ms=93.266`
- `map_io_timing.configure_to_map_read_completed_ms=139.415`

不可接受的本轮输出：只重复以上 baseline，且没有 `/map_server active` 或更窄 root cause。

## Owner and Team Boundary

- 主责：`robot-software-engineer`
- Algorithm：只在 `/map_server` lifecycle clean/active 后介入 path generation、AMCL/TF 或 route execution。
- Hardware：只有 LiDAR serial/runtime/wiring 成为 primary root cause 时介入，且必须先读 `docs/vendor/VENDOR_INDEX.md`。
- Full-Stack：不介入。

## Allowed File Scope for Robot Software

Robot Software 可在后续实现阶段按需触碰以下范围：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/tech-done.md`
- `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/artifacts/`

除非 root cause 明确落到相关文件，否则不要修改 launch、硬件配置、串口、WAVE ROVER、ESP32 或 UI/API 文件。

## Interface Impact

预期接口影响：

- 不改变 ROS2 public interface。
- 不改变 `/cmd_vel`、`/odom`、`/imu/data`、`/battery` 或 behavior/action contract。
- 可新增 proof JSON 字段，用于表达 `on_configure` return source、map IO ordering、service future 或 lifecycle response handling。
- 所有新增 proof 字段必须保持 fail-closed 默认值；无法观测时不能推断为 success。

严禁接口影响：

- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不发送 NavigateToPose。
- 不打开 WAVE ROVER UART。
- 不把 route execution、delivery、HIL 或 production booleans 置 true。

## Implementation Plan

1. 复用 15:54 true-board artifact 和 runtime log ordering，建立 baseline 断言。
2. Inspect Nav2 map_server `on_configure` return false path：区分 callback exception、parameter validation、YAML/image/map mode、map IO completion 和 lifecycle response。
3. 扩展 helper/proof/parser，输出更窄字段，例如 `on_configure_return_source`、`callback_exception_summary`、`map_io_exception_summary`、`parameter_failure_summary`、`executor_future_timing` 或 `lifecycle_response_handling_summary`。
4. 若找到小修路径，优先修到 `/map_server active=true`，再记录 strict no-motion artifact。
5. 若无法修复，生成 true-board strict no-motion artifact，证明 root cause 比 15:54 更窄，且下一轮可直接按字段修复。
6. 更新 tests 和 docs，最后更新 `tech-done.md`，不得把 blocked proof 包装成 OKR 增量。

## Acceptance Commands for Robot Software

Robot Software 实现阶段至少运行：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/artifacts/local_o10_map_server_on_configure_return_source_repair.raw.json
```

True-board strict no-motion run may use the established SSH/scp path if board access remains available:

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
scp -P 37878 onboard/scripts/o11_nav2_lifecycle.sh \
  root@192.168.1.11:/root/rober/onboard/scripts/o11_nav2_lifecycle.sh
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_on_configure_return_source_repair.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_on_configure_return_source_repair.raw.json \
  sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/artifacts/live_o10_map_server_on_configure_return_source_repair.raw.json
```

Scoped diff check:

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair
```

## Product Plan Validation Commands

本 Product plan 创建后必须运行：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|map_server_changestate_response_false_before_map_io_completion|on_configure|robot-software-engineer|no-motion|/cmd_vel|NavigateToPose|WAVE ROVER" sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair
```

```bash
git diff --check -- sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair
```

## Product Acceptance Gate

Product 接受条件：

- `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。
- strict no-motion artifact 存在，或明确说明真实板不可达原因。
- 安全字段 fail-closed。
- `/map_server active=true`，或 blocked root cause 比 15:54 更窄。
- 不调整 OKR 百分比，不归档 KR，除非新增证据真正越过 path/route/delivery/production gate。

Product 拒收条件：

- 没有证明 `/map_server active`，也没有比 15:54 更窄的 root cause。
- 同名 blocker 被重复包装成新进展。
- 任何 motion/control/UART 行为发生。
- Algorithm 在 `/map_server` lifecycle clean 前接手 path generation。
- Hardware 在未成为 primary root cause 且未读 vendor 资料时接手硬件判断。

## Risk and Blocker Boundaries

- 如果本轮只得到相同 root cause，Robot Software 必须返工一次。
- 如果返工后仍重复，下一轮升级 CEO 或切换 Objective。
- LiDAR serial/runtime 背景噪声不自动转 Hardware，除非 artifact primary root cause 明确指向 LiDAR serial/runtime/wiring。
- 本轮不能声明 safe-to-control、HIL、route execution、delivery success、production readiness 或 cloud cutover。

## Next Engineer Execution Summary

给 `robot-software-engineer`：

- 文件范围：优先 `onboard/scripts/o10_amcl_nav2_runtime_proof.py`、`onboard/scripts/o11_nav2_lifecycle.sh`、`onboard/tests/test_nav2_runtime_proof_helper.py`、`docs/navigation/field_route_evidence_preflight.md`、`docs/navigation/fixed_route_workflow.md`、本 sprint `tech-done.md` 和 `artifacts/`。
- 核心任务：inspect/fix/narrow Nav2 map_server `on_configure` return false path，解释 ChangeState response false while map IO still incomplete 的真实来源。
- 验收命令：运行本文件 `Acceptance Commands for Robot Software` 一节的 py_compile、unittest、bash -n、local strict no-motion、true-board strict no-motion 和 scoped `git diff --check`。
- no-motion 边界：禁止 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART；`safe_to_control`、`route_execution_success`、`delivery_success`、`hil_pass` 必须 fail-closed，除非有真实证据且本轮范围允许。
