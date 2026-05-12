# Sprint 2026.05.12_10-11 Phone UI Readiness Gate - Tech Plan

## 状态

- 阶段：tech-plan
- 创建时间：2026-05-12 10:11 Asia/Shanghai
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：默认无；必要时 `robot-software-engineer` 只读补接口事实
- 证据边界：`software_proof_docker_local_phone_ui_readiness_gate`

## 1. 执行原则

本轮是单 owner 闭环：由 `full-stack-software-engineer` 负责实现、验证、修复和更新 `tech-done.md`。主节点不得直接改产品代码、测试代码或硬件配置。

工程实现必须复用既有字段和契约，不发明脱离后端/ROS2 的 UI 状态。涉及代码技术注释时必须使用中文，并保持有意义注释比例超过 20%。

## 2. 文件范围

Full-stack owner 可改范围由实现时按实际代码定位后收敛，建议起点如下：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.12_10-11_phone-ui-readiness-gate/tech-done.md`

范围边界：

- 不改 `OKR.md`，除非 Product Owner 在验收阶段基于 evidence 明确更新。
- 不改硬件/vendor、Nav2/fixed-route、vision、launch 硬件参数或 WAVE ROVER 相关文件。
- 不新建大规模测试套件；如必须补测试，只补与 phone UI readiness gate 直接相关的 targeted cases。

## 3. 技术方案

### Task A - Phone readiness aggregation

Owner：`full-stack-software-engineer`

目标：在 operator 手机入口或一个稳定 phone readiness snapshot/API 中聚合普通用户可读状态。

输入字段：

- `remote_readiness.remote_ready`
- `remote_readiness.degradation_state`
- `remote_readiness.retry_hint`
- `remote_readiness.safe_phone_copy`
- `remote_readiness.auth_state`
- `remote_readiness.status_stale`
- `remote_readiness.pending_command_count`
- command / ACK envelope state
- relay `/readyz` / `/preflightz` / backup-restore drill output中的 phone-safe summary、retry hint、not-proven/evidence boundary
- local status `phone_copy` / `speaker_prompt` / action permissions

输出要求：

- 用户主状态：可以继续、等待机器人状态、等待命令 ACK、登录/鉴权失败、远程服务不可达、服务响应异常、云端上线前检查未通过、备份恢复演练未通过或未运行。
- 用户下一步：继续操作、稍后重试、重新登录、等待状态上报、等待 ACK、联系支持、切换本地 fallback。
- 技术边界：用 machine-readable field 记录 `software_proof_docker_local_phone_ui_readiness_gate`，不把本地 proof 写成生产 ready。

### Task B - Phone-first UI/readability gate

Owner：`full-stack-software-engineer`

目标：让 dependency-free operator 手机入口从 debug 页面推进到可验收的 phone-first gate。

最低要求：

- 首屏清楚分出主状态、主操作、恢复提示、支持诊断。
- 对 remote readiness、preflight、backup/restore、delivery command state 使用普通用户文案。
- 主操作按钮不暴露 ROS2 名称或硬件细节。
- blocked/warning 不是报错墙，应显示可恢复路径和剩余未证明能力。

### Task C - Documentation and evidence capture

Owner：`full-stack-software-engineer`

目标：同步更新 docs 和 sprint `tech-done.md`，记录实际实现边界。

必须记录：

- 实际改动文件。
- 新增或变更的 API/UI 字段。
- 所有验证命令关键输出。
- 不得宣称事项。
- 剩余风险和是否需要 Robot/Hardware/Autonomy 后续配合。

## 4. 接口影响

允许的接口变化：

- 增加 backward-compatible phone readiness 字段或聚合对象。
- 在现有 status/diagnostics/remote relay 输出中增加 phone-safe summary、readiness classification 或 UI-only grouping。
- 增加 schema/version 字段便于后续正式 phone app 复用。

禁止的接口变化：

- 不破坏 `trashbot.remote.v1` command/status/ack shape。
- 不改变 ACK 语义；ACK 仍不是 delivery success。
- 不把 production preflight blocked 改成 robot delivery failed。
- 不让 UI 直接触达 `/cmd_vel`、串口、WAVE ROVER 参数或 ROS topic。

## 5. 验收命令

Full-stack owner 应根据最终改动选择最小 fenced set。默认命令如下，必须使用真实存在的文件名，不使用 `test_*review*py` pattern：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

如 touched remote relay/preflight/backup restore 聚合：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

如 touched remote bridge compatibility：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

编译围栏按 touched Python 文件收敛，例如：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

必要 local/script smoke 只在 touched surface 需要时运行，例如：

```bash
PYTHONDONTWRITEBYTECODE=1 scripts/remote_cloud_relay_docker_smoke.sh
```

Scoped diff check：

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/product/mobile_user_flow.md \
  docs/product/remote_4g_mvp.md \
  docs/interfaces/ros_contracts.md \
  sprints/2026.05.12_10-11_phone-ui-readiness-gate/tech-done.md
```

## 6. 不运行的验证

- 不运行 broad `colcon build`，除非实现触及 ROS package install/launch/build surface。
- 不运行硬件 smoke、`hardware_smoke_wave_rover.py --move-test`、HIL packet gate 或 WAVE ROVER 串口验证。
- 不运行 Nav2/fixed-route 实跑。
- 不运行真实 4G/SIM、真实云、公网 HTTPS/TLS 或 OSS/CDN 实流量验证。

## 7. 风险和回滚边界

- 风险：UI 聚合字段过多，普通用户仍像在看 debug 面板。缓解：首屏只放主状态、主操作、恢复提示，diagnostics 放次级。
- 风险：把 preflight/backup restore 状态误写成 production ready。缓解：所有 copy 保留 software-proof/local/Docker/not-proven boundary。
- 风险：测试命令误用不存在的 pattern。缓解：只运行本计划列出的真实 unittest 文件。
- 风险：注释规范不达标。缓解：复杂映射、脱敏、状态归类逻辑必须加中文“为什么”注释。

## 8. 子 Agent 交付要求

`full-stack-software-engineer` 返回时必须包含：

1. 实际改动文件列表。
2. 用户旅程变化和触点收益。
3. API/UI 字段影响和兼容性说明。
4. 验证命令输出关键日志。
5. 失败定位，如有。
6. 剩余风险和需要机器人侧配合事项。
7. 已更新 `sprints/2026.05.12_10-11_phone-ui-readiness-gate/tech-done.md`。

## 9. Product 验收计划

实现返回后，Product Owner 只做证据核对和 sprint 收口：

- 对照 PRD 检查 P0 是否全部满足。
- 确认没有把 Docker/local proof 写成真实云、真实 4G、真实送达或 HIL。
- 更新 `side2side_check.md` 和 `final.md`。
- 只有在 phone UI readiness gate 真正落地且验证通过时，才保守更新 O5；否则 O5 继续保持约 33%。
