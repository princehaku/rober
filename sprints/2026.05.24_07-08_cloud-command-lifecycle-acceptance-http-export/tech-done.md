# Cloud Command Lifecycle Acceptance HTTP Export Tech Done

Run time: 2026-05-24 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Task A - Full-Stack HTTP Export

Owner: `full-stack-software-engineer`

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 新增 `cloud_command_lifecycle_replay_acceptance_packet_http_export` 常量、HTTP export payload builder 和免 bearer 的只读 GET route：`/api/support/cloud-command-lifecycle-replay-acceptance-packet-export`。
- HTTP export 复用上一轮 CLI export helper，保留源 CLI export boundary `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`、源 packet boundary `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`、`accepted_processing_only_not_delivery_success`、`terminal_result_pending`、`owner_handoff`、`next_required_evidence`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 和 `redaction_status=passed`。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 新增 focused HTTP support tests，覆盖 no-auth GET、required markers、safe false flags、unsafe text redaction 和 GET 前后 state file 不变。
- `cloud-relay/README.md`、`docs/product/remote_4g_mvp.md`、`docs/product/cloud_4g_infrastructure.md` 同步新增 HTTP export route、证据边界和 no-side-effect / no-overclaim 说明。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`：通过。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m pytest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k "cloud_command_lifecycle_replay_acceptance_packet_http_export or support" -q`：系统 Python 缺少 pytest，直接运行失败为 `No module named pytest`；随后按 PEP 668 提示创建 `/tmp/rober-pytest-venv` 临时虚拟环境并安装 pytest，用 `PATH=/tmp/rober-pytest-venv/bin:$PATH` 保持 `python3 -m pytest ...` 形式重跑，通过：`2 passed, 77 deselected in 36.12s`。
- Focused `rg` 覆盖 `cloud_command_lifecycle_replay_acceptance_packet_http_export`、`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`、`accepted_processing_only_not_delivery_success`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`not true phone/browser proof`、`no OKR percentage lift`、`not delivery success`：通过，相关 marker 分布在代码、测试、cloud-relay README、产品文档和本 sprint tech-done。
- Scoped `git diff --check`：通过。

### 剩余风险

- 本轮仍是 Docker/local HTTP export software proof，不是 delivery success、not true phone/browser proof、not real external cloud proof、not public HTTPS/TLS、not 4G/SIM、not OSS/CDN live traffic、not production DB/queue、not worker/cutover、not HIL、not PR #5 resolution；no OKR percentage lift。
- 该 route 只暴露 support / field-owner review metadata，不 replay/resubmit command、不 post ACK、不 mutate cursor/state、不上传材料、不触发 GitHub action、不控制 Nav2/机器人、不写 delivery success。

## Task B - Robot Safe-Alias Boundary Check

Owner: `robot-software-engineer`

### 实际改动

- Changed files: none。
- 只读核对确认 `operator_gateway_diagnostics.py` 既有 `cloud_command_lifecycle_replay_acceptance_packet`、`cloud_command_lifecycle_replay_acceptance_packet_summary` 和 `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary` 已满足 HTTP export 消费边界。
- 既有 Robot diagnostics contract 已包含 `accepted_processing_only_not_delivery_success`、owner handoff、next required evidence、false-state flags，以及 disabled ACK/cursor/replay/material/GitHub/robot/Nav2/HIL side effects。

### 验证结果

- Required `rg`：首轮失败仅因为 Product closeout 文件 `tech-done.md` 当时尚未存在；Robot code/docs marker 本身已存在。
- Scoped Robot `git diff --check`：通过。

### 剩余风险

- Robot consultation 没有改变代码，因此本轮 Robot 侧只作为 read-only boundary proof。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；HTTP export 不等于 PR #5 resolved、not HIL、not WAVE ROVER/UART proof、not delivery success。

## Task C - Product Closeout

Owner: `product-okr-owner`

### 实际改动

- 新增 `side2side_check.md`，按 PRD P0/P1/P2 对照确认 HTTP export route、payload marker、false-state flags、no-side-effect、docs/product 同步和 no-overclaim 边界。
- 新增 `final.md`，收口 sprint evidence、Objective 5 判断、PR #5 unresolved 状态、剩余外部材料缺口和下一步建议。
- 更新 `OKR.md` 当前 4.1 snapshot，将最新 sprint 从 06-07 CLI export 推进到本轮 07-08 HTTP export；Objective 5 仍约 68%，no OKR percentage lift。
- 更新 `docs/process/okr_progress_log.md` 顶部 2026-05-24 系列，新增本轮 closeout 历史记录。

### 验证结果

- Product closeout 将运行最终 fenced commands：required file check、required marker `rg`、scoped `git diff --check`、`git diff --cached --check`，以及 Task A 的 `py_compile` / focused pytest。
- 本段记录最终验证结果时只接受 fresh command output；最终结果见本轮提交前命令输出和 `final.md`。

### 剩余风险

- 本轮只证明 local/Docker support HTTP export 可读、可脱敏、无状态副作用；not true phone/browser proof、not delivery success、not HIL、not PR #5 resolved、not external O5 proof。
- Objective 5 保守保持约 68%；只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser 或 verified terminal delivery/dropoff/cancel result 到位后才可考虑 percentage lift。
