# O6/O7 Delivery Result Evidence Tech Done

## robot-algorithm-engineer

- 实际改动：
  - 在 `onboard/scripts/field_route_evidence_manifest.py` 新增可选 `--delivery-result-json`，从安全裁剪后的 delivery result JSON 生成 `delivery_result_evidence` 摘要，写入 manifest 顶层与 `field_motion_evidence_packet.delivery_result_evidence`。
  - 新增 `trashbot.delivery_result_evidence.v1` 和 `software_proof_delivery_result_evidence_only`，并保持 field packet 的 `task_id` lineage 不被外部输入覆盖。
  - 对缺输入、JSON 不可读、root 非 object、schema mismatch、`task_id` mismatch、UTC 时间非法、危险 true、path/root/token/raw/base64/credential URL 等输入统一 fail-closed，不回显危险内容。
  - 在 `onboard/tests/test_field_route_evidence_manifest.py` 增加 ready / missing / schema mismatch / unsafe / lineage 校验覆盖。
  - 在 `docs/navigation/field_route_evidence_manifest.md` 同步记录新参数、摘要 schema、proof scope 与 fail-closed 规则。

- 验证结果：
  - `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
    - 结果：`Ran 20 tests in 0.069s`，`OK`
  - `git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/tech-done.md`
    - 结果：通过，无 whitespace / conflict marker 问题。

- 首轮失败定位：
  - ready fixture 默认携带与 field packet lineage 不同的 `task_id`，被新逻辑按预期拦截。
  - 已修复 fixture，使其与 packet lineage 对齐后复验通过。

- 剩余风险：
  - 当前只证明 local/mock delivery result evidence 生成链路，未证明真实 delivery record、真实 operator confirmation 媒体、真实 live Nav2 run 或真实 delivery success。
  - 若未来现场采集侧仍输出未裁剪的路径、token、credential URL 或原始 payload，本轮 contract 会 fail-closed，需要采集链路继续提供安全裁剪版本。

## robot-software-engineer

- 实际改动：
  - 在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 为 `delivery_result_evidence` 增加 O6 additive 白名单摘要，接入 field-evidence / artifact-bundle ingest、archive task detail、field evidence、artifact bundle、consumer detail 顶层 alias，以及 `include=delivery_result_evidence` 单独回读。
  - 新增坏 schema、坏 proof_scope、危险 true、path/root/token/raw/base64/credential URL/unsafe text 的 fail-closed 占位摘要逻辑；所有安全旗标继续固定为 false。
  - 在 `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 增加 ready / missing / unsafe / include 回读覆盖，并把 field-evidence、artifact-bundle、empty consumer detail fixture 扩展到 `delivery_result_evidence`。
  - 在 `docs/interfaces/o6_cloud_archive_api.md` 同步记录 `delivery_result_evidence` schema、回读 alias、`include=delivery_result_evidence` 与 fail-closed 规则。

- 验证结果：
  - `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
    - 结果：`Ran 157 tests in 55.196s`，`OK`
  - `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/tech-done.md`
    - 结果：通过，无 whitespace / conflict marker 问题。

- 剩余风险：
  - 当前只证明 local/mock O6 archive/readback 合同，未证明真实 production cloud、真实 OSS/CDN、真实 delivery record、真实 operator confirmation 介质、真实 Nav2 live run 或真实 delivery success。
  - 本轮只消费安全裁剪后的摘要；如果 Algorithm 侧后续调整 `delivery_result_evidence` ready status 文案或字段命名，需要与 O6/O7 合同继续同步。

## full-stack-software-engineer

- 用户旅程变化和触点收益：
  - O7 consumer detail 现在会随同同一 `task_id` 主路径读取 `delivery_result_evidence`，运营人员在 PC 端可以直接看到 delivery record / operator confirmation readiness，而不必只从 `nav2_goal_execution_evidence.next_required_evidence` 反推还缺什么。
  - `artifact_bundle_readiness` 和 `O7FixturePreviewPanel.vue` 已把 delivery result 摘要收敛成 status、record/operator confirmation、blocked reasons、next required evidence 和固定 false 安全旗标；任何危险 true、坏 schema、path/root/token/raw/base64/credential URL/unsafe text 都会 fail-closed，不回显危险内容。

- 实际改动：
  - `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
    - `include` 默认请求增加 `delivery_result_evidence`。
    - 新增 delivery result source scan、白名单归一、unsafe text 拒绝、坏 schema / bad proof_scope / dangerous true / missing required fields fail-closed。
    - 把 `delivery_result_evidence` 接入 consumer detail 顶层摘要和 `artifact_bundle_readiness` readiness 汇总。
  - `pc-tools/workstation/src/shared/contracts.ts`
    - 新增 `O7ConsumerDeliveryResultEvidenceSummary`，并把它接入 task detail 与 artifact bundle readiness shared contract。
  - `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
    - 新增 delivery result evidence 只读面板与 readiness 摘要，不打开任何 submit/control/action。
  - `pc-tools/workstation/test/catalog.test.ts`
    - 新增 delivery result fixture、detail/readiness 断言，以及 schema mismatch / dangerous true / unsafe text fail-closed 覆盖。
  - `pc-tools/workstation/test/App.test.ts`
    - 更新 consumer detail fixture、include 断言和 UI 文案断言，覆盖 delivery result evidence 展示。
  - `docs/product/pc_tools_workstation.md`
    - 同步记录 `include=delivery_result_evidence`、consumer detail / readiness 来源、展示字段和 fail-closed 规则。

- 验证结果：
  - `cd pc-tools/workstation && npm run test`
    - 结果：`Test Files  3 passed (3)`，`Tests  478 passed (478)`
  - `cd pc-tools/workstation && npm run build`
    - 结果：`vite v7.3.3 building client environment for production...`，`✓ built in 1.72s`
    - 备注：Vite 保留既有 chunk size warning，未因本轮 delivery result 改动新增 build failure。
  - `cd pc-tools/workstation && npm run lint`
    - 结果：通过，无 lint 报错。

- 剩余风险：
  - 当前 O7 只证明 local/mock consumer detail 已消费 delivery result additive 摘要，未证明真实 production cloud、真实 delivery record、真实 operator confirmation 媒体、真实 OSS/CDN、真实 Nav2 live run 或真实 delivery success。
  - `artifact_bundle_readiness` 现在要求同 task 的 delivery result evidence ready 才进入 ready summary；若上游 Algorithm/O6 后续调整 delivery result ready 文案或字段命名，O7 shared contract 与断言需要同步更新。
