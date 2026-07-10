# O6 Field Evidence Archive Ingest Tech Done

- sprint_type: epic
- time: 2026-07-09 05:25 CST

## Robot/O6

### 实际改动

- 在 [`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py) 增加并收紧 `POST /api/o6/archive/field-evidence` 的 ingest 口径。
- 新请求体现在显式支持 `robot_id`、`task_id`、`field_evidence_manifest`，同时兼容旧包装 `manifest` 和直传 manifest 对象。
- 新增对可选 `trajectory_frames[]`、`events[]`、`evidence_refs[]` 的 fail-closed 校验，并把它们写入 file-backed O6 store。
- 让 O6 task detail / consumer detail 继续回读 `field_evidence` 摘要，并补上 `request_summary`，方便 PC/O7 读取来源、轨迹、事件和证据计数。
- 更新 [`onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py) 增加新合同回归：
  - 显式 `field_evidence_manifest + task_id` ingest
  - 带 `trajectory_frames/events/evidence_refs` 的回读
  - unsafe gate / bad artifact fail-closed
- 更新 [`docs/interfaces/o6_cloud_archive_api.md`](/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md) 和 [`docs/navigation/field_route_evidence_manifest.md`](/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md) 说明新 ingest 入口和本地/mock 约束。

### 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/scripts/field_route_evidence_manifest.py`
  - 结果：通过，退出码 0。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 结果：通过，`Ran 147 tests in 48.734s`，`OK`。

### 失败定位

- 第一次全量 `unittest` 失败在 field evidence ingest 回归，原因是测试里用了 `mock://...` 形式的 `evidence_ref`，被 `safe_ref` 按 URL/非 basename 输入拒绝，返回 `unsafe evidence_ref`。
- 处理方式：把测试输入改成纯 basename 引用（例如 `route.csv`、`operator-note.json`），保持和本轮 fail-closed 约束一致后复验通过。

### 剩余风险

- 这条链路仍然是 `software_proof_local_mock_archive_only`，只证明本地 file-backed archive ingest 和 consumer readback，不证明真实生产云、OSS/CDN、4G/TLS 或任何 ROS2/串口/HIL 闭环。
- 当前验证覆盖了 Python 编译和单测，没有跑真实硬件、真实云服务或 PC 端联调。
- 若后续新增字段写入源，需要继续保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`connects_cloud_production=false`、`robot_control_executed=false` 的 fail-closed 约束。

## Full-stack/O7 和集成补充

### 实际改动

- 返工原因：O6 后端当前只在 `include=field_evidence` 时返回 `field_evidence` section，但 PC adapter 的默认 `DEFAULT_DETAIL_INCLUDE` 仍漏掉该 section，导致 O7 consumer read 主路径默认拿不到本轮新增字段。
- 在 [`pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts) 把 detail 默认 include 收紧为 `trajectory,events,evidence,field_evidence,labeling,inference,tunnel`，保持其余 section 顺序和 fail-closed 行为不变。
- 在 [`pc-tools/workstation/test/catalog.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts) 和 [`pc-tools/workstation/test/App.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts) 更新 request URL / `remote_endpoint` / `query_strategy.include` 断言，确保 catalog 与 App 都覆盖新 include 列表。
- 在 [`pc-tools/README.md`](/Users/m1/apps/rober/pc-tools/README.md)、[`docs/product/pc_tools_workstation.md`](/Users/m1/apps/rober/docs/product/pc_tools_workstation.md) 和 [`docs/interfaces/o7_realtime_operator_console.md`](/Users/m1/apps/rober/docs/interfaces/o7_realtime_operator_console.md) 同步修正文案，把旧 include 列表替换为包含 `field_evidence` 的新列表。

### 验证结果

- `cd pc-tools/workstation && npm run test -- catalog.test.ts`
  - 结果：通过，`201 passed`。
- `cd pc-tools/workstation && npm run test -- App.test.ts`
  - 结果：通过，`247 passed`。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过，Vite 仅提示单个 chunk 超过 500 kB 的既有 warning。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过。
- `cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh`
  - 结果：本轮未复跑；本轮以 O6 Python 单测、PC catalog/App/build/lint 和 `git diff --check` 作为验收证据。

### 剩余风险

- O7 本轮只证明 adapter/UI 对 `field_evidence` wrapper 兼容，不证明真实路线逐帧回放、标注提交、训练集导出或生产云数据流。
- 这次返工只修正 O7 consumer read 主路径的默认 include 不一致，没有改变任何播放、提交、控制、发送、导出或生产联网动作。
