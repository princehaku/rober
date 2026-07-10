# O6 Field Evidence Archive Ingest Tech Plan

## 技术方案

本轮采用 local/mock 软件证明，不依赖真实硬件或生产云：

1. Robot/O6 seed 层：读取 `trashbot.field_evidence_manifest.v1`，校验 schema、manifest gate、安全字段和 artifact 摘要，派生 O6 task/events/evidence_refs 的安全 payload。
2. Cloud relay 层：提供 `POST /api/o6/archive/field-evidence` 或等价 helper，把上述 payload 写入 `FileBackedO6CloudArchiveStore`，并让 `GET /api/o6/consumer/tasks/<task_id>` 能读回 field evidence 摘要。
3. PC O7 层：复用 `GET /api/o7/consumer-read/tasks` / `tasks/<task_id>` 主入口，增加对远端 field evidence 来源的展示/合同验证，不提供播放、提交、控制或导出动作。

## 文件范围

Robot/O6 owner 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `onboard/scripts/field_route_evidence_manifest.py`（仅当需要导出 ingest seed helper）
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/navigation/field_route_evidence_manifest.md`

Full-stack owner 可改：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`

Sprint 留档：

- `sprints/2026.07.09_02-31_o6_field_evidence_archive_ingest/tech-done.md`
- `sprints/2026.07.09_02-31_o6_field_evidence_archive_ingest/side2side_check.md`
- `sprints/2026.07.09_02-31_o6_field_evidence_archive_ingest/final.md`

## 接口影响

- 新增 O6 local/mock ingest 能力必须只接受 safe manifest，不连接生产 DB/queue/OSS。
- O6 consumer read 输出可新增 `field_evidence` section；既有字段保持兼容。
- O7 adapter 只能消费本机回环 `baseUrl`，继续拒绝外网 URL、credentials、query/hash 和危险 true 字段。

## 验收命令

Robot/O6:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

Full-stack:

```bash
cd pc-tools/workstation && npm run test -- catalog.test.ts
cd pc-tools/workstation && npm run test -- App.test.ts
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
```

集成 smoke:

```bash
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
```

如果 Docker smoke 超出本轮时间，子 agent 必须至少运行 targeted Python/Node tests，并在 `tech-done.md` 说明未跑 Docker 的影响。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O6（约 30%）与 O7（约 30%）并列。
- 本 sprint 是否针对该 Objective：是，同时覆盖 O6/O7。
- 理由：本轮把现场/离线 field evidence 材料接入 O6 local/mock archive 和 O7 consumer read 主路径，避开真实相机、wheel raw、真实 4G/TLS/OSS 凭证等当前环境 blocker。
- final.md 收口时需复核：是否形成可执行 seed/ingest、O6 readback、O7 PC readback 三段证据；是否仍保持所有危险控制/成功字段 false。

## 风险边界

- 该链路是 `software_proof_local_mock_archive_only`，不是生产云或真实 OSS。
- field evidence manifest 的 `gate_pass=true` 仍不等于真实送达成功。
- 如果完整 cloud-relay Docker smoke 失败，需先定位；若失败来自外部 Docker 环境且 targeted tests 已过，记录剩余风险。
