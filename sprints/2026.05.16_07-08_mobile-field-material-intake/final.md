# Sprint 2026.05.16_07-08 Mobile Field Material Intake - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `software_proof_docker_mobile_field_material_intake_gate`。`mobile_field_material_intake` 从 06-07 precheck 前进到 phone-safe material intake surface + Robot diagnostics metadata-only consumer + pc-tools fail-closed gate。

用户价值：现场操作者现在有一个手机可读、可复制、可由 PC gate 校验的材料 intake 入口，用同一 safe `evidence_ref` 汇总真实设备/PWA observation、route/elevator field materials、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel material status，而不是继续在分散面板或聊天里人工记忆补材料。

产品北极星：普通手机用户和现场支持人员可以在不接触 SSH、ROS2、串口、云凭证或 raw artifact 的情况下准备真实现场材料；系统保持 fail-closed，不把 software proof 写成真实手机、真实 route/elevator field pass、delivery success、HIL 或 Objective 5 external proof。

## 2. OKR 更新

- Objective 4：从约 77% 保守上调到约 78%。理由是本轮把上一轮 precheck 推进为 `mobile_field_material_intake` 首屏入口、whitelist-only copy/export、Robot diagnostics metadata-only consumer 和 pc-tools gate，能支持真实设备/PWA 与 route/elevator field materials 的下一步摄取。
- Objective 2：保持约 76%。本轮只支撑 same-evidence-ref 现场材料摄取，没有真实 route/elevator field pass、真实 dropoff/cancel completion 或 delivery success。
- Objective 3：保持约 76%。本轮只新增 intake/gate 检查入口，没有真实路线采集、真实 Nav2/fixed-route runtime log 或同一 `evidence_ref` 上车复账。
- Objective 1：保持约 73%。本轮未改 WAVE ROVER、UART、Orange Pi、真实串口、`T=1001` feedback 或 HIL。
- Objective 5：保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料；not real Objective 5 external proof。

`OKR.md` 和 `docs/process/okr_progress_log.md` 已按上述判断更新。

## 3. 工程结果

Task A `full-stack-software-engineer`：

- 改动：`mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`。
- 结果：首屏新增 `mobile_field_material_intake` panel，显示 safe entry/evidence_ref、真实设备/PWA checklist、route/elevator field materials、same-evidence-ref status，支持 whitelist-only copy/export；Start / Confirm Dropoff / Cancel gating 未改。
- 验证：`mobile/test_mobile_web_entrypoint.py` Ran 49 tests OK；`py_compile` OK；`node --check mobile/web/app.js` OK；required `rg` OK；scoped diff check OK。

Task B `robot-software-engineer`：

- 改动：`operator_gateway_diagnostics.py`、`test_operator_gateway_diagnostics.py`、`docs/interfaces/ros_contracts.md`。
- 结果：新增 `mobile_field_material_intake` / `_summary` metadata-only diagnostics consumer、schema/boundary 校验、bad JSON/missing/unsupported/unsafe/success claim fail-closed，`latest_status` 清理和 env 入口；command/ACK/control/cursor/persistence/terminal ACK/Nav2/HIL/dropoff/cancel/delivery success 旗标强制 false。
- 验证：diagnostics unittest Ran 87 tests OK；required `rg` OK；scoped diff check OK。

Task C `autonomy-engineer`：

- 改动：新增 `pc-tools/evidence/mobile_field_material_intake.py`、新增 `pc-tools/evidence/test_mobile_field_material_intake.py`、更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`。
- 结果：新增 fail-closed pc-tools intake/gate，把真实设备/PWA observation、route/elevator field materials、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel material status 收到同一 safe `evidence_ref` 下检查。
- 验证：py_compile OK；`test_mobile_field_material_intake.py` Ran 5 tests OK；`--help` OK；required `rg` OK；scoped diff check OK；首轮 unittest 发现 evidence-ref mismatch 被 precheck 层优先拦截，测试断言按更严格 fail-closed 顺序修正后通过。

## 4. Product closeout 验证

Product closeout 必跑：

```text
rg -n "mobile_field_material_intake|Objective 5|Objective 4|software_proof_docker_mobile_field_material_intake_gate|真实手机|route/elevator|not real|不证明|delivery_success=false|OKR 最低优先级核对" sprints/2026.05.16_07-08_mobile-field-material-intake OKR.md docs/process/okr_progress_log.md

git diff --check -- sprints/2026.05.16_07-08_mobile-field-material-intake OKR.md docs/process/okr_progress_log.md
```

验证结果将在提交前后以命令输出为准；本文件保留最终 closeout 口径。

## 5. 剩余风险

- 仍缺真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- 仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery success。
- 仍缺 WAVE ROVER、真实 UART/串口、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery`。
- 仍缺 Objective 5 external proof：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。

## 6. 下一步

下一轮继续按 `OKR.md` 4.1 重新排序。若仍没有真实 O5 外部材料，不要继续消费 O5 blocker；优先使用本轮 intake/gate 收真实手机/PWA observation 或 O2/O3 route/elevator 现场材料。
