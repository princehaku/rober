# O6 Field Evidence Archive Ingest Side2side Check

- sprint_type: epic
- check_time: 2026-07-09 05:25 Asia/Shanghai
- checker: robot-software-engineer
- evidence_boundary: software_proof_local_mock_archive_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false

## 用户验收口径对照

| 验收点 | 结果 | 证据 |
| --- | --- | --- |
| Robot/O6 Python 语法检查 | 通过 | `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/scripts/field_route_evidence_manifest.py` 退出码 0 |
| Robot/O6 单元测试 | 通过 | `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`，`Ran 147 tests in 48.734s`，`OK` |
| O6 `POST /api/o6/archive/field-evidence` 能写入合法 `trashbot.field_evidence_manifest.v1` | 通过 | `unittest` 继续覆盖 field evidence ingest / readback / fail-closed 回归；本轮未单独再跑 targeted smoke |
| O6 consumer list 能回读 `field_evidence` 摘要 | 通过 | 同上，`test_remote_cloud_relay` 的 field evidence 回归维持通过 |
| O6 consumer detail 能回读 `field_evidence` section | 通过 | 同上，`test_remote_cloud_relay` 的 detail 回读回归维持通过 |
| 危险字段保持 false | 通过 | `test_remote_cloud_relay` 相关回归继续约束 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` |
| PC/O7 adapter 对新 wrapper 兼容 | 通过 | `cd pc-tools/workstation && npm run test -- catalog.test.ts` 通过，`201 passed` |
| PC/O7 应用主测试不回归 | 通过 | `cd pc-tools/workstation && npm run test -- App.test.ts` 通过，`247 passed` |
| PC/O7 build/lint 不回归 | 通过 | `cd pc-tools/workstation && npm run build` 通过，Vite 仅 chunk warning；`cd pc-tools/workstation && npm run lint` 通过 |
| Docker cloud-relay smoke | 未运行 | 本轮没有复跑 `cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh`；验收以 O6 Python 单测、PC catalog/App/build/lint 和 `git diff --check` 为准 |

## 对照结论

本轮集成验收满足 sprint PRD 的 local/mock 软件证明：field evidence manifest 可以进入 O6 archive，并能从 O6 consumer list/detail 读回；PC/O7 consumer read adapter 对 O6 新 `field_evidence` wrapper 的契约测试继续通过。该结论只覆盖 `software_proof_local_mock_archive_only`，不提升为真实生产云、真实路线回放、真实视频或 delivery success。

该结论不声明真实 production cloud、真实 OSS/CDN、TLS/4G、真实路线、电梯或送达成功。所有控制和成功字段继续关闭。

## 剩余风险

- 本轮未复跑 cloud-relay Docker smoke，也未单独复跑 targeted local/mock HTTP smoke；新 endpoint 的写入/读回通过 `test_remote_cloud_relay` 单元测试覆盖。
- 真实生产 DB/queue、OSS/CDN、TLS/4G 和真实机器人数据仍未接入。
- O7 后续如需播放真实路线，需要继续消费 replay JSONL 内容；本轮只证明 read model 和 wrapper 兼容。
