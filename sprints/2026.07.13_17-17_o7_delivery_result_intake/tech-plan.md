# Tech Plan - O7 Delivery Result Intake

## 方案

在 PC workstation 的 O7 consumer-read selected-task flow 中新增 delivery result intake action：

1. `shared/contracts.ts` 增加 request/result type 和 fixed false fields。
2. `server/o7ConsumerReadAdapter.ts` 增加安全规范化、O6 receipt 校验、fail-closed receipt 与 `buildO7ConsumerDeliveryResultIntake`。
3. `server/index.ts` 增加固定 endpoint：`POST /api/o7/consumer-read/tasks/:taskId/delivery-result/intake?baseUrl=<local-loopback-url>`。
4. `client/workstationApi.ts` 增加 typed API helper。
5. `components/O7FixturePreviewPanel.vue` 在 selected task detail 区加入 operator action 和 receipt summary。
6. `test/catalog.test.ts` / `test/App.test.ts` 覆盖 success、update、unsafe input、bad O6 receipt 和 UI summary。
7. 更新 `docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md` 和本 sprint `tech-done.md`。

## 文件范围

允许改动：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.13_17-17_o7_delivery_result_intake/tech-done.md`

条件允许的窄范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`

仅当现有 O6 `/api/o6/archive/field-evidence` 无法表达 delivery result evidence intake receipt 时，才允许触碰上述 O6 文件。

## 接口边界

- O7 endpoint 固定 path，不接受动态 O6 endpoint。
- `baseUrl` 仅允许 local-loopback。
- O6 转发优先使用 existing local/mock archive/consumer contract。
- Receipt schema 固定为 O7 PC schema，source 固定 `software_proof`，`pc_only=true`。
- 所有真实能力字段保持 false：`safe_to_control`、`delivery_success`、`primary_actions_enabled`、`connects_cloud_production`、`robot_control_executed`、`route_execution_success`、`hil_pass`。

## 验收命令

Full-stack agent 必须运行并记录输出：

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_17-17_o7_delivery_result_intake
```

如触碰 O6 后端，还必须运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective：O5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 理由：O5 最新 sprint `2026.07.13_13-13_o5_cdn_tls_external_evidence_probe` 已收口为 `blocked_http_status_not_success_class`；在 public endpoint 未预期返回 success class 或无 production DB/queue、OSS/CDN、4G/SIM、真实手机/browser 材料前，继续 O5 会重复消费同一 blocker。O1/O3 的 current live HIL/current route execution 也需要 explicit operator approval。故本轮选择可在当前环境交付且不重复的 O7/O6 delivery result intake action-write。

## 风险

- 该 sprint 只产生 local/mock software proof，主百分比可能保持不变。
- 若 UI 文案过度暗示 delivery success，必须返工为 not_proven/fail-closed 口径。
- 若测试失败，Full-stack agent 需先定位并修复后复验，不得把首轮失败当最终结果。
