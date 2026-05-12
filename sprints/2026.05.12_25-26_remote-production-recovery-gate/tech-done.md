# Sprint 2026.05.12_25-26 Remote Production Recovery Gate - Tech Done

## 状态

- 阶段：tech-done
- 收口时间：2026-05-12 23:34 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主线 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- Evidence boundary：`software_proof_docker_production_recovery_gate`

## 实际改动

### Task A / full-stack-software-engineer

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 Docker/local `trashbot.production_recovery_gate` artifact builder、validator、checksum 校验、writer CLI `--write-production-recovery-artifact`。
  - 新增 preflight consumer：`--production-recovery-artifact` 与 `TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT`。
  - 有效 artifact 只让 `production_recovery=pass`，仍保持 `production_ready=false`、`overall_status=blocked`。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - 新增 `/api/status.phone_readiness.production_recovery` 的 phone-safe summary 消费。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 新增 `/api/diagnostics.production_recovery` 的同口径 phone-safe summary。
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 覆盖 artifact pass、preflight consumption、status/diagnostics summary、敏感字段过滤和 failure wording。
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/mobile_user_flow.md`
  - 同步 O6 production recovery gate、phone-safe 字段和 not-proven 边界。

### Task B / robot-software-engineer

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 新增 production recovery metadata remote bridge compatibility fence。
  - 验证 metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
  - 验证 metadata-only blocked/invalid/stale response 不触发 robot action、不 ACK、不推进或持久化 cursor。
- `docs/interfaces/ros_contracts.md`
  - 明确 production recovery metadata 是 phone/operator support metadata；旧 robot client 可忽略；它不属于 robot command envelope。
- 本轮未修改生产 `remote_bridge.py`。

## 验证结果

### Task A 验证

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `Ran 133 tests in 28.079s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile ...`
  - `remote_cloud_relay.py`、`operator_gateway_http.py`、`operator_gateway_diagnostics.py` 通过。
- `PYTHONPATH=src/ros2_trashbot_behavior python3 -m ros2_trashbot_behavior.remote_cloud_relay --write-production-recovery-artifact /tmp/trashbot_production_recovery_gate.json`
  - `ok=true`
  - `production_recovery_status=passed`
  - `evidence_boundary=software_proof_docker_production_recovery_gate`
- `PYTHONPATH=src/ros2_trashbot_behavior TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT=/tmp/trashbot_production_recovery_gate.json python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight`
  - `software_proof_ready=true`
  - `production_ready=false`
  - `overall_status=blocked`
  - `production_recovery=pass`
  - `evidence_boundary=software_proof_docker_production_recovery_gate`
- Task A scoped `git diff --check` 通过。

### Task B 验证

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - `Ran 44 tests in 21.928s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - 通过。
- Task B scoped `git diff --check` 通过。

## 失败定位和修复记录

- Task A 第一轮 unittest 失败：phone-safe summary 的 `recovery_drill_status` 对外暴露了 `checksum` 字样，不满足 public summary 脱敏口径。
- 修复：public summary 改为 `schema_integrity` wording；内部 artifact checksum validation 保持不变。
- Task B 未报告生产代码缺陷；兼容性通过新增测试围栏确认。

## 剩余风险

- 本轮只证明 Docker/local software gate 可执行，证据边界是 `software_proof_docker_production_recovery_gate`。
- 仍未证明真实生产 DB/queue、生产备份策略、真实灾备恢复、多实例一致性、真实云/HTTPS/TLS、公网入口、真实 4G/SIM、真实 OSS upload、CDN origin fetch、OSS/CDN 实流量或生产运维。
- 仍没有正式手机 app/真实手机设备验收、真实 Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只代表 command envelope accepted/processing/failure evidence，不等于 delivery success，也不等于 production recovery 完成。
