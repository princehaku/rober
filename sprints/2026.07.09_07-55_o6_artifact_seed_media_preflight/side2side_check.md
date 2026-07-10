# O6 Artifact Seed Media Preflight Side-by-Side Check

## Sprint 类型和证据边界

- sprint_type: epic
- product_owner: product-okr-owner
- evidence_boundary: software_proof_local_mock_media_preflight_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## PRD 验收逐项对照

| PRD 验收口径 | 证据 | 结论 |
| --- | --- | --- |
| O6 local/mock archive 有可测试的 artifact seed/readback 主路径，并覆盖 unsafe path/token/raw content fail-closed | Robot worker 摘要显示 `artifact_media_preflight` 绑定同一 `task_id`，并对 token path、credential URL、raw/base64 evidence refs、dangerous true claims、非法 consumer query path 继续 fail-closed；`test_remote_cloud_relay` `Ran 149 tests ... OK`。 | 通过，边界为 local/mock |
| O6 可回读 route/replay/keyframe/evidence 计数、样本 ref、blocked reasons 和固定 consumer section names | `docs/interfaces/o6_cloud_archive_api.md` 与 O6 worker 摘要都明确 `artifact_media_preflight` 包含 counts、sample refs、`blocked_reasons[]`、`consumer_section_names=["artifact_media_preflight","route_replay_mvp","labeling_mvp"]`。 | 通过 |
| O7 优先消费 O6 consumer detail 的新增 artifact/media 状态，而不是只显示独立 fixture | Full-stack worker 摘要显示 `o7ConsumerReadAdapter.ts` 优先读取 O6 `artifact_media_preflight`，缺字段时才从 `field_evidence` / `field_evidence_consumer_ingest` / `evidence` / `trajectory` 派生 `derived_blocked_not_proven`。 | 通过 |
| O7 route replay / labeling 必须展示 media refs 的可用性摘要、缺口和 next required evidence | `O7FixturePreviewPanel.vue` 与测试摘要显示 UI 已展示 media refs、blocked reasons 和 `next_required_evidence`，并分别服务 route replay / labeling 的 media dependency。 | 通过 |
| O7 对危险 true 字段、未知 schema、unsafe refs 继续 fail-closed | Full-stack worker 摘要与测试覆盖说明继续阻断 dangerous true claims、schema mismatch、unsafe refs 和非回环路径。 | 通过 |
| O6 unittest 和 O7 tests/build/lint 全部通过 | O6：`Ran 149 tests in 50.480s OK`。O7：`catalog.test.ts` `204 passed`、`App.test.ts` `247 passed`、build 通过、lint 通过。 | 通过 |
| sprint 收口文档写清实际改动、验证结果和剩余风险 | 本目录 `tech-done.md`、`side2side_check.md`、`final.md` 已补齐。 | 通过 |
| 实现同步更新相关 `docs/` 文档 | O6 更新 `docs/interfaces/o6_cloud_archive_api.md`；O7 更新 `docs/product/pc_tools_workstation.md`。 | 通过 |

## 危险字段核对

本轮所有真实能力字段继续保持 fail-closed：

- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false
- connects_cloud_production: false
- real_annotation_api_connected: false
- real_dataset_export_connected: false
- real_media_read_executed: false

## 用户价值和产品北极星对照

- 用户价值：运营/开发者现在可以围绕同一 `task_id` 看到 route/replay/keyframe/evidence 的 media 依赖摘要，知道哪些材料已齐、哪些仍 blocked、下一步还缺什么证据，而不是只看到一个 manifest 字符串。
- 产品北极星：仍服务于“可验证地可靠送垃圾”的长期目标；本轮只是把复盘/打标链路从 annotation submit/export 进一步推进到 media 依赖预检，不证明真实送达或真实控制。

## OKR 映射和方向判断

- O6 KR2/KR3/KR6：archive/read model 增加 `artifact_media_preflight`，让 task/evidence 摘要能被 O7 直接消费。
- O7 KR3/KR4：PC 历史回放和标注工作台从纯 consumer summary 前进到 media dependency 预检和 next-evidence 引导。
- 方向判断：继续 O6/O7，但下一步必须消费真实 `route.csv`、replay JSONL、keyframe 或 rosbag，不能继续只堆 local/mock wrapper。

## 收口判断

本 sprint PRD 验收口径成立。验收边界必须写为 `software_proof_local_mock_media_preflight_only`。

本轮不证明真实媒体/OSS/CDN、真实 annotation API、真实 dataset export、production cloud、真实机器人控制或 delivery success。
