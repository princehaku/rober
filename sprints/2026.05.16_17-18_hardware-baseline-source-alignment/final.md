# Sprint 2026.05.16_17-18 Hardware Baseline Source Alignment - Final

sprint_type: epic

## 1. 最终结论

本轮完成 `hardware_baseline_source_alignment` software proof closeout。PR #5 review 暴露的硬件基线矛盾和 source attribution 风险，已经被收敛为 PC gate、Robot diagnostics metadata-only consumer、mobile/web 只读 panel 和 Product OKR 留档。

证据边界固定为 `software_proof_docker_hardware_baseline_source_alignment_gate`。所有输出保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. OKR 进展

- Objective 1：从约 73% 保守上调到约 74%。理由是硬件基线 source alignment 已可机器验收，能防止未证实 2D LiDAR / ToF 假设进入 bringup/HIL 计划。
- Objective 4：从约 86% 保守上调到约 87%。理由是手机端新增 phone-safe “硬件基线来源对齐”只读展示，普通用户和现场支持能看懂默认硬件集、目标传感器基线、vendor/source boundary 和缺失材料。
- Objective 5：保持约 66%。理由是本轮没有真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 或其他 Objective 5 external proof。

## 3. 实际改动

- Task A Hardware：新增 `hardware_baseline_source_alignment` PC gate / test，更新 `pc-tools/README.md` 与 `docs/product/production_hardware_boundary.md`。
- Task B Robot：更新 `operator_gateway_diagnostics.py`、diagnostics test 和 `docs/interfaces/ros_contracts.md`，新增 metadata-only consumer。
- Task C Full-stack：更新 `mobile/web`、fixture、test 和 `docs/product/mobile_user_flow.md`，新增只读 panel，copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 不变。
- Task D Product：更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 4. 验证摘要

- Task A：py_compile passed；unittest `Ran 5 tests in 0.005s OK`；CLI `--help` passed；required `rg` passed；scoped `git diff --check` passed；`--once-json` 输出 `overall_status=hardware_baseline_source_aligned_not_proven`、`missing_alignment_items=[]`、`delivery_success=false`、`primary_actions_enabled=false`。
- Task B：py_compile passed；diagnostics unittest `Ran 106 tests in 0.117s OK`；required `rg` passed；scoped `git diff --check` passed。
- Task C：mobile unittest `Ran 8 tests ... OK`；`node --check mobile/web/app.js` passed；required `rg` passed；scoped `git diff --check` passed。
- Task D：required `rg` passed；closeout scoped `git diff --check` passed。

## 5. 失败定位

Task B 中间一次 unittest 因旧断言全局禁止 WAVE ROVER，导致 hardware baseline summary 中安全摘要也被拦截；已改为只在 unsafe blocked summary 限制 raw hardware detail，复验通过。

Task D 未发现验证失败。

## 6. 未完成事项和风险

- 未完成真实硬件证明：没有真实 WAVE ROVER/UART/Orange Pi 串口、`T=1001` feedback、`/odom`、`/imu/data`、`/battery`、HIL 或现场运行。
- 未完成真实传感器材料：没有真实 2D LiDAR / ToF SKU/source/receipt、采购、安装、接线、供电、标定或 HIL-entry 材料。
- 未完成真实手机/量产证明：没有真实 iPhone/Android device behavior、production app、PWA prompt/user choice 或量产实物验收。
- 未完成 O5 external proof：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration、queue ordering 或 transaction isolation。

## 7. 下一步建议

下一轮继续按 `OKR.md` 4.1 重新排序。若仍没有 O5 外部材料，优先补真实设备/现场材料：O1 的 WAVE ROVER/UART/HIL packet 或 2D LiDAR / ToF source/receipt/install/calibration/HIL-entry；若手机设备可用，则补 O4 真实 iPhone/Android/PWA 现场证据；若 route/elevator field materials 可用，则推进 O2/O3 同一 `evidence_ref` 的现场复账。
