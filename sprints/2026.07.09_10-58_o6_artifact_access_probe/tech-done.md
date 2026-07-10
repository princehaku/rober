# O6 Artifact Access Probe Tech Done

## Sprint 声明

- sprint_type: epic
- round: 2026.07.09_10-58_o6_artifact_access_probe
- owner: robot-software-engineer
- done_time: 2026-07-09 11:15:42 CST
- evidence_boundary: software_proof_local_mock_artifact_access_probe_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false
- real_oss_connected: false
- connects_cloud_production: false

## 实际改动

- `remote_cloud_relay.py`
  - 新增 `trashbot.o6.artifact_access_probe.v1`、`TRASHBOT_O6_ARTIFACT_ACCESS_ROOT`、64KB 小文件上限和固定 proof scope。
  - 为 artifact bundle 原始相对 refs、field evidence 安全 basename refs 生成受限只读 probe。
  - probe 默认 fail-closed：缺 allowlist root、root 无效、绝对路径、`..`、URL/query、credential/control/raw/base64、越界、目录、缺文件、超 64KB 都只返回 blocked reason。
  - 只有 allowlist root 内小文件才读取并计算 `sha256`，响应不回显 root、绝对路径或原始相对目录。
  - archive task detail、field_evidence、artifact_bundle、consumer detail 和 `include=artifact_access_probe` 均可回读同一 `task_id` 的 probe。
  - 危险能力字段继续固定为 false。

- `test_remote_cloud_relay.py`
  - 覆盖无 root blocked probe。
  - 覆盖 artifact bundle + `artifact_access_root` 读取 `route.csv` / replay JSONL / keyframe / evidence 小文件并回读 size、sha256、detected_type。
  - 覆盖 `..`、URL token、credential hint、`/cmd_vel` 和超大文件 blocked，不读取超大文件内容。

- `docs/interfaces/o6_cloud_archive_api.md`
  - 补充 `artifact_access_probe` schema、字段、root 来源、64KB 上限、blocked reason 和 consumer include 合同。

- `docs/navigation/field_route_evidence_manifest.md`
  - 补充 field evidence 进入 O6 archive 时的 `artifact_access_root` 使用方式和证据边界。

## 验证结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

第一次结果：失败 1 个断言。失败定位为 `../secret.csv` 先命中通用 credential marker，被归类为 `unsafe_ref`，没有返回更具体的 `path_traversal_ref_blocked`。

修复：调整 probe ref blocked reason 判定顺序，让 raw/control、URL/query、绝对路径、`..`、隐藏路径、credential hint 分层返回 blocked reason。

复验结果：

```text
Ran 153 tests in 52.427s
OK
```

```bash
git diff --check
```

结果：通过，无输出。

## 剩余风险

- 本轮只证明 local/mock fixture 的受限小文件 probe，不证明真实生产 DB/queue、OSS/CDN、TLS/4G、公网隧道或生产容量。
- 本轮未启动 ROS2 runtime、未连接机器人、未读取真实串口或硬件反馈、未执行 `/cmd_vel` 或任务控制。
- `exists=true` 和 `sha256` 只表示 allowlist root 内本地 fixture 文件可读，不等于真实媒体可播放、真实路线回放完成、真实 annotation API、真实 dataset export 或 delivery success。
- 后续仍需把真实或离线 `route.csv`、replay JSONL、keyframe 或 rosbag 放入 allowlist root，做 O6/O7 贯通 smoke。

## 协同判断

- 需要 `full-stack-software-engineer` 继续消费 O7 probe 字段：是。O6 合同已稳定暴露 `artifact_access_probe`，O7 可在 consumer/readiness 中展示 counts、sample refs、sha256 摘要和 blocked reasons，但必须保留 `local_mock/not_proven` 边界。
- 暂不需要 Hardware 或 Autonomy 协同；本轮没有硬件参数、串口、WAVE ROVER、Nav2 或真实路线运行改动。

---

# O7 Artifact Access Probe Secondary Consumer Tech Done

## Sprint 声明

- sprint_type: epic
- round: 2026.07.09_10-58_o6_artifact_access_probe
- owner: full-stack-software-engineer
- done_time: 2026-07-09 11:37:42 CST
- evidence_boundary: software_proof_local_mock_artifact_access_probe_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false
- media_access_proven: false
- real_oss_connected: false
- real_cdn_connected: false

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 O7 `artifact_access_probe` 共享类型，字段只包含 counts、basename refs、`detected_type`、`size_bytes`、sha256 prefix、blocked reasons、next required evidence 和固定 false proof boundary。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - detail include 扩展为 `trajectory,events,evidence,field_evidence,labeling,inference,tunnel,artifact_access_probe`。
  - 从 top-level `artifact_access_probe`、`field_evidence.artifact_access_probe`、`artifact_bundle.artifact_access_probe` 和相关 ingest wrapper 读取 O6 probe。
  - schema mismatch、危险 true 字段、unsafe ref、allowlist root echo 均 fail closed；缺失 probe 会让 `artifact_bundle_readiness.status=derived_blocked_not_proven` 并追加 `artifact_access_probe_missing` 与 `real_or_offline_artifact_access_probe_for_selected_task`。
  - 对 `probes[]` 全量扫描 unsafe refs，只截断展示样本，避免窗口外危险 ref 被 basename 化后漏过。
  - 只向 UI 返回 basename refs 与 sha256 prefix，不暴露 allowlist root、原始路径、URL、query 或 token。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 在 O7 consumer detail / bundle readiness 区域新增 compact `Artifact access probe` section，展示 counts、sample refs、sample probes、sha256 prefix、blocked reasons、next evidence 和固定 false 字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 O6 probe fixture、happy path 断言、missing probe blocked readiness 断言、unsafe ref fail-closed 断言。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 mounted fixture 与 include 断言，覆盖 UI 中的 probe schema、counts、sha256 prefix、blocked reason、next evidence 和 false fields。
- `docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_realtime_operator_console.md`、`pc-tools/README.md`
  - 同步 O7 consumer read include、probe 来源、脱敏展示字段、fail-closed 条件和未证明边界。

## 验证结果

```bash
cd pc-tools/workstation && npm run test
```

复验结果：

```text
Test Files  3 passed (3)
Tests       472 passed (472)
Duration    48.91s
```

```bash
cd pc-tools/workstation && npm run build
```

第一次结果：失败。`src/server/o7ConsumerReadAdapter.ts` 中 `robot_control_executed` 显式赋值后又被 `fixedFalseFields()` 覆盖，TypeScript 报 `TS2783`。

修复：删除 probe summary 里重复的显式 `robot_control_executed=false`，继续通过 `fixedFalseFields()` 固定 false。

复验结果：通过。Vite 仍提示既有 large chunk warning：

```text
✓ 34 modules transformed.
✓ built in 1.69s
```

```bash
cd pc-tools/workstation && npm run lint
```

结果：通过，无 ESLint 输出。

```bash
git diff --check
```

结果：通过，无输出。

## 剩余风险

- 本轮只证明 O7 可消费 O6 local/mock probe 摘要，不证明真实 OSS/CDN、真实生产云、真实媒体访问、真实 annotation API、真实 dataset export 或 delivery success。
- `artifact_access_probe.status=local_mock_artifact_access_probe_ready` 只表示 O6 local/mock 小文件读取摘要可被 O7 安全展示；`media_access_proven=false`、`real_oss_connected=false`、`real_cdn_connected=false` 仍固定。
- 未改 O6 Python、O6 tests、OKR、硬件配置、launch 参数或 vendor 文档；不需要 O6/Robot Software 复改，除非后续 O6 变更 probe schema 或新增真实/offline probe 来源。
