# Sprint 2026.05.20_02-03 Cloud Command Expiry Safety Guard - Tech Plan

## 1. 技术方案

本轮在已有 `expires_at` 和 `command_expired(command)` 基础上做最小功能增量：过期云命令仍 ACK `ignored`，但 Robot/operator/mobile 必须同步看到 `command_expired` 的 fail-closed 状态。这样手机用户能知道旧命令没有执行，并重新下发新指令；系统不能把 ignored ACK 或本地空闲状态误写成 delivery success。

证据边界：`software_proof_docker_cloud_command_expiry_safety_guard`。

## 2. 文件范围

### robot-software-engineer

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `docs/product/remote_4g_mvp.md`

### full-stack-software-engineer

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_expiry_safety_guard.json`
- `docs/product/mobile_user_flow.md`

### product-okr-owner

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_02-03_cloud-command-expiry-safety-guard/tech-done.md`
- `sprints/2026.05.20_02-03_cloud-command-expiry-safety-guard/side2side_check.md`
- `sprints/2026.05.20_02-03_cloud-command-expiry-safety-guard/final.md`

范围外文件不得修改；如发现必须改共享 fixture 或 docs，需要在输出里说明原因。

## 3. 接口影响

- 不新增 command type。
- 复用已有 `expires_at` 和 ignored ACK。
- 新增/标准化 status/readiness 字段：
  - `degradation_state=command_expired`
  - `expired_command_id`
  - `remote_ready=false`
  - `primary_actions_enabled=false`
  - `safe_phone_copy`
  - `retry_hint=resubmit_command`
  - `proof_boundary=software_proof_docker_cloud_command_expiry_safety_guard`
- 手机端和 operator gateway 只读消费新状态；不新增控制动作。

## 4. 验收命令

### Robot

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
rg -n "cloud_command_expiry_safety_guard|command_expired|expired_command_id|remote_ready=false|primary_actions_enabled=false|delivery success|production DB/queue|4G" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py docs/product/remote_4g_mvp.md
```

### Full-Stack

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "cloud_command_expiry_safety_guard|command_expired|expired_command_id|remote_ready=false|primary_actions_enabled=false|software_proof_docker_cloud_command_expiry_safety_guard|delivery success" mobile/web docs/product/mobile_user_flow.md
```

### Product / Integration

```bash
rg -n "sprint_type: epic|cloud_command_expiry_safety_guard|Objective 5|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_command_expiry_safety_guard|OKR 最低优先级核对|delivery success" sprints/2026.05.20_02-03_cloud-command-expiry-safety-guard OKR.md docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py docs/product/remote_4g_mvp.md mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_expiry_safety_guard.json docs/product/mobile_user_flow.md sprints/2026.05.20_02-03_cloud-command-expiry-safety-guard
git diff --cached --check
```

## 5. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 针对 Objective 5，但不做 external material proof，也不提升百分比。
3. 选择理由：真实 O5 external proof 在 Docker-only 主机不可得；但 command/status/ack 主链路仍有一个可执行功能缺口，即 expired command 目前只 ACK `ignored`，缺少用户可见的 fail-closed readiness 和 mobile copy。
4. PR / 评审证据：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，不能关闭；近期 ACK sprint 反复强调 ACK/cursor/command 状态不得被写成 delivery success，本轮延续该具体问题。

## 6. 风险边界

- 如果 expired command 已经完整覆盖 status/readiness/mobile copy，停止实现并由 Product 记录“不需要新增功能”的 closeout。
- 如果验证失败，先定位并修复；不得把第一次失败作为最终结果。
- 保持本轮验证围栏，不新增大规模测试套件。
