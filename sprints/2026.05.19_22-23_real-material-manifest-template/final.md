# Sprint 2026.05.19_22-23 Real Material Manifest Template - Final

## 1. 收口结论

- sprint_type: epic
- 本轮完成 `real_material_manifest_template` / field-owner submission pack closeout。
- 工程产物把 O5 external、O1 / PR #5 hardware、PR #4 route/elevator、O4 real phone 的真实材料需求整理成 template groups，并通过 Robot diagnostics 和 mobile/web 只读消费。
- 本轮证据边界是 `software_proof_docker_real_material_manifest_template_gate`，兼容 `real_material_evidence_intake` software-proof manifest-template boundary。
- OKR 百分比保守保持：Objective 5 约 68%，Objective 1 约 81%，Objective 2 / Objective 3 / Objective 4 约 99%。
- Product planning commit `45c705f` 已在 `origin/master`；工程改动和 Product closeout 改动由主会话在最终验收后统一提交并推送。

## 2. 实际改动文件

Product closeout 改动：

- `sprints/2026.05.19_22-23_real-material-manifest-template/tech-done.md`
- `sprints/2026.05.19_22-23_real-material-manifest-template/side2side_check.md`
- `sprints/2026.05.19_22-23_real-material-manifest-template/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

工程 owner 已完成但本轮 Product 不改动的范围：

- `pc-tools/evidence/real_material_evidence_intake.py`
- `tests/test_real_material_evidence_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/real_material_evidence_intake.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/interfaces/ros_contracts.md`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.19_22-23_real-material-manifest-template/evidence/real_material_manifest_template.json`

## 3. 验证结果

Product closeout 复跑验收命令：

```text
python3 -m unittest tests/test_real_material_evidence_intake.py
Ran 7 tests in 0.013s
OK

python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 215 tests in 0.642s
OK

python3 mobile/web/test_mobile_web_entrypoint.py
Ran 139 tests in 1.044s
OK

node --check mobile/web/app.js
exit 0

python3 -m py_compile pc-tools/evidence/real_material_evidence_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
exit 0

test -f closeout docs and real_material_manifest_template.json
exit 0

required rg over sprint, OKR.md, docs/process/okr_progress_log.md
matched real_material_manifest_template / manifest_template / template_groups / required_item_templates / Objective 5 / Objective 1 / PR #5 / PRRT_kwDOSWB9286CJ3tX / software_proof / not_proven / delivery_success=false / primary_actions_enabled=false / safe_to_control=false / Ran 7 tests / Ran 215 tests / Ran 139 tests

git diff --check -- sprints/2026.05.19_22-23_real-material-manifest-template OKR.md docs/process/okr_progress_log.md
exit 0
```

## 4. OKR 进展

| Objective | 进展判断 |
| --- | --- |
| Objective 1 | 保持约 81%。`real_material_manifest_template` 让 O1 / PR #5 hardware owner 知道要回填哪些真实材料，但没有真实 WAVE ROVER/UART/HIL、真实反馈包或真实 2D LiDAR / ToF material。 |
| Objective 2 | 保持约 99%。PR #4 route/elevator material template 更清晰，但没有真实 route/elevator field pass、真实 dropoff/cancel completion 或 delivery success。 |
| Objective 3 | 保持约 99%。Template 要求真实 Nav2/fixed-route runtime log、route completion signal 和 field task record，但本轮没有真实路线/导航运行证据。 |
| Objective 4 | 保持约 99%。mobile/web 只读展示 manifest template groups，但没有真实手机设备、production app、PWA prompt/user choice 或 true phone/browser acceptance。 |
| Objective 5 | 保持约 68%。O5 external template 要求真实公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover，但本轮没有真实 external proof。 |

## 5. 风险和后续

- 下一步不应继续增加本地 metadata wrapper；应让现场 owner 按 `real_material_manifest_template` 回填至少一种真实材料，再进入 `real_material_evidence_intake` / review decision。
- 若 O5 external materials 到位，优先回填公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 若 O1 / PR #5 materials 到位，优先回填真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，或真实 WAVE ROVER/UART/HIL packet。
- 若 PR #4 / O2/O3 materials 到位，优先回填同一 safe `evidence_ref` 的真实 Nav2/fixed-route runtime log、route completion signal、field task record、电梯门状态、目标楼层确认、人工协助记录和 delivery_result。
- 若 O4 materials 到位，优先回填真实 iPhone/Android behavior、production app、PWA prompt/user choice 和 true phone/browser acceptance。

## 6. Blocker 字段

- blocker: missing real materials
- blocker_detail: 当前仍缺真实 O5 external proof、真实 O1 / PR #5 hardware materials、真实 PR #4 route/elevator field materials 和真实 O4 phone/browser materials。
- repeated_blocker_policy: 本轮没有把 blocker 写成完成；只是提供 field-owner manifest template。下一轮若仍无真实材料，应升级现场材料提供请求，而不是继续堆本地 proof。
