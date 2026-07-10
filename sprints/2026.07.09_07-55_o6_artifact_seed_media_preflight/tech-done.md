# O6 Artifact Seed Media Preflight Tech Done

## Sprint 类型

- sprint_type: epic
- closeout_owner: product-okr-owner
- implementation_owners: robot-software-engineer, full-stack-software-engineer
- evidence_boundary: software_proof_local_mock_media_preflight_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 实际改动

### O6 Backend / Local Mock

来源：本轮 Robot Software worker 结果摘要。

- `remote_cloud_relay.py` 新增 `artifact_media_preflight` additive 合同，绑定同一 `task_id`，围绕 field evidence / consumer detail 主路径暴露 route/replay/keyframe/evidence 计数、样本 ref、blocked reasons 和 proof boundary。
- `artifact_media_preflight` 固定输出 `consumer_section_names=["artifact_media_preflight","route_replay_mvp","labeling_mvp"]`，明确给 O7 的固定消费入口。
- O6 对 token path、credential URL、raw/base64 evidence refs、dangerous true claims 和非法 consumer query path 继续 fail-closed，不把 media ref 字符串升级成真实媒体可访问或真实云读写。
- `docs/interfaces/o6_cloud_archive_api.md` 同步记录 O6 media preflight 合同、blocked reasons、`local_mock/not_proven` 边界和 O7 消费 section 名称。

O6 实际改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

### O7 PC Adapter / UI

来源：本轮 Full-Stack worker 结果摘要。

- `o7ConsumerReadAdapter.ts` 优先读取 O6 `artifact_media_preflight`；远端缺字段时，才从 `field_evidence` / `field_evidence_consumer_ingest` / `evidence` / `trajectory` 派生保守 `derived_blocked_not_proven` 摘要。
- `contracts`、`O7FixturePreviewPanel.vue` 和相关测试补齐 media dependency 展示，route replay / labeling 现在会显式展示 media refs、blocked reasons 与 `next_required_evidence`。
- O7 保持 fail-closed：危险 true 字段、未知 schema、unsafe refs、非回环或不安全 copy 继续被拒绝；UI 只说明 local/mock、not_proven，不暗示真实 OSS/CDN、真实 annotation API、真实 dataset export、真实机器人控制或 delivery success。
- `docs/product/pc_tools_workstation.md` 同步更新 O7 如何消费 O6 `artifact_media_preflight` 以及 media dependency 展示边界。

O7 实际改动文件：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`

## 验证结果

本 Product 收口不重复跑工程测试；按本轮任务要求引用两个 worker 已完成的实现验证，并执行 closeout 轻量检查。

### O6 验证

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

关键输出：

```text
Ran 149 tests in 50.480s

OK
```

### O7 验证

```bash
cd pc-tools/workstation && npm run test -- catalog.test.ts
```

关键输出：`Tests  204 passed (204)`。

```bash
cd pc-tools/workstation && npm run test -- App.test.ts
```

关键输出：`Tests  247 passed (247)`。

```bash
cd pc-tools/workstation && npm run build
```

结果：通过。

```bash
cd pc-tools/workstation && npm run lint
```

结果：通过。

## 失败定位

- 本轮收口引用的最终验证均通过，没有遗留失败。
- 当前没有证据表明真实媒体已可访问；本轮新增的是 preflight/read-model 和 consumer 展示，不是媒体 fetch 成功。

## 偏差和边界

- 本轮没有运行 Docker、ROS2 runtime、真实上车、真实云、OSS/CDN、annotation 生产服务或机器人控制。
- `artifact_media_preflight` 和 O7 media dependency 只证明 local/mock 合同、摘要回读和 fail-closed 展示，不证明真实 route replay 文件可下载、真实 keyframe 可打开、真实 annotation API、真实 dataset export、真实机器人运动或 delivery success。
- 所有危险能力字段保持 false：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## Product Closeout 轻量验证

```bash
test -f sprints/2026.07.09_07-55_o6_artifact_seed_media_preflight/tech-done.md
test -f sprints/2026.07.09_07-55_o6_artifact_seed_media_preflight/side2side_check.md
test -f sprints/2026.07.09_07-55_o6_artifact_seed_media_preflight/final.md
```

结果：收口文件存在后应全部退出码 0。

```bash
rg -n "artifact_media_preflight|149 tests|204 passed|247 passed|safe_to_control.*false|delivery_success.*false" sprints/2026.07.09_07-55_o6_artifact_seed_media_preflight OKR.md docs/process/okr_progress_log.md
```

结果：应命中 sprint 收口文档、`OKR.md` 与 `docs/process/okr_progress_log.md` 中的本轮证据字段。

## 剩余风险

- 只证明 `software_proof_local_mock_media_preflight_only`。
- 不证明真实媒体/OSS/CDN 可访问，不证明真实 annotation API、真实 dataset export、production cloud、真实机器人控制或 delivery success。
- 不证明真实 route.csv/replay JSONL/keyframe/rosbag 已由 O6/O7 现场消费；当前仍主要是摘要、样本 ref 和 blocked reason 预检。
- O6/O7 都还缺真实生产云数据流、真实关键帧媒体读路径、真实长期路线回放与现场验收。
