# Sprint 2026.05.16_11-12 Hardware Baseline Review Gate - Final

## 1. 收口结论

本轮 sprint 完成。PR #5 review 指出的硬件基线矛盾已完成产品/工程闭环：文档修复、PC gate、Robot diagnostics metadata-only consumer、手机只读 panel 和 OKR closeout 已对齐。

本轮证据边界是 `software_proof_docker_hardware_baseline_review_gate`。它证明当前 repo 可以把硬件基线评审状态以 fail-closed 方式贯穿 PC、Robot diagnostics 和 phone-safe UI；不证明真实 2D LiDAR、真实 ToF、真实 WAVE ROVER/UART/HIL、真实 Nav2/fixed-route、真实 route/elevator field pass、delivery success 或 Objective 5 external proof。

## 2. 实际交付

- Hardware：`docs/product/production_hardware_boundary.md` 修复 `Default Hardware Set` 与 `Navigation/Sensing Baseline` 矛盾；2D LiDAR / ToF 写为 Product Target / Procurement Validation Pending，保留 `hardware_material_pending` 和 `not_proven`。
- Autonomy：新增 `pc-tools/evidence/hardware_baseline_review_gate.py` 与测试，输出 `hardware_baseline_review` artifact/summary，固定 `delivery_success=false` 和 `primary_actions_enabled=false`。
- Robot：新增 `hardware_baseline_review` diagnostics metadata-only consumer，并在 ROS contracts 中写清 fail-closed 口径。
- Full-stack：新增只读“硬件基线评审状态”panel，copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 不变。
- Product：补齐 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 3. 验证证据

Worker 返回的分任务验证均通过：

- Hardware：关键边界 `rg` 命中；`git diff --check -- docs/product/production_hardware_boundary.md` 通过。
- Autonomy：`py_compile` 通过；`Ran 4 tests ... OK`；CLI `--help` 通过；required `rg` 与 scoped `git diff --check` 通过。
- Robot：diagnostics unittest 初次 `Ran 93 tests ... OK`；最终 schema handoff 修复后 `Ran 94 tests ... OK`；`py_compile`、required `rg`、scoped `git diff --check` 通过。
- Full-stack：mobile unittest `Ran 52 tests ... OK`；`py_compile`、`node --check mobile/web/app.js`、required `rg`、scoped `git diff --check` 通过。

最终集成审查发现 PC `--summary-output` 使用的 compact summary schema 与 Robot diagnostics 白名单不一致。已统一为 `trashbot.hardware_baseline_review_summary.v1`，并用 PC summary handoff proof 验证 Robot diagnostics 返回 `review_status.status=hardware_baseline_review_not_proven`，不是 `unsupported_schema`；该修复不改变 `software_proof_docker_hardware_baseline_review_gate` 边界。

Product closeout 已运行：

```bash
rg -n "hardware_baseline_review|software_proof_docker_hardware_baseline_review_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 5|只有 Docker|PR #5|2D LiDAR|ToF" sprints/2026.05.16_11-12_hardware-baseline-review-gate OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_11-12_hardware-baseline-review-gate OKR.md docs/process/okr_progress_log.md
```

## 4. OKR 更新

- Objective 4：从约 80% 保守上调到约 81%。理由是低成本量产边界中的硬件基线矛盾已被修复，并被 PC gate、Robot diagnostics 和手机只读 panel 串成闭环。
- Objective 1：保持约 73%。本轮没有真实 WAVE ROVER、UART、`T=1001` feedback、真实串口日志、`/odom`、`/imu/data`、`/battery` 或 HIL。
- Objective 2：保持约 78%。本轮只间接支撑电梯/送达传感器责任边界，没有真实电梯、真实 Nav2/fixed-route、dropoff/cancel completion 或 delivery success。
- Objective 3：保持约 78%。本轮没有真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据、真实 completion signal 或 task record。
- Objective 5：保持约 66%。Objective 5 仍最低，但本机只有 Docker；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他外部材料，不能上调。

## 5. 风险与下一步

下一步不要继续堆本地 O5 metadata。若外部材料仍不可用，优先推进可以实际补证的 O4/O2/O3 现场材料链：真实手机设备/PWA observation、真实 2D LiDAR / ToF 采购和安装材料、真实 Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、真实 route/elevator field pass、dropoff/cancel completion 或 delivery result。

仍未完成：真实 2D LiDAR / ToF vendor/procurement/HIL，真实 WAVE ROVER/UART/HIL，真实手机设备验收，真实 Nav2/fixed-route，真实送达，以及 Objective 5 external proof。
