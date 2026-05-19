# Sprint 2026.05.20_04-05 PR5 Vendor Source Review Reply Dispatch - Tech Done

## 1. Sprint 类型

- sprint_type: epic
- Sprint 主题：`pr5_vendor_source_review_reply_dispatch`
- Product closeout 时间：2026-05-20 04:18 Asia/Shanghai

## 2. 实际改动

### Hardware Infra Engineer

- 新增 `pc-tools/evidence/pr5_vendor_source_review_reply_dispatch.py`。
- 新增 `tests/test_pr5_vendor_source_review_reply_dispatch.py`。
- 新增 `docs/interfaces/pr5_vendor_source_review_reply_dispatch.md`。
- 新增 sprint evidence：
  - `evidence/pr5_vendor_source_review_reply_dispatch.json`
  - `evidence/pr5_vendor_source_review_reply_dispatch_summary.json`
  - `evidence/pr5_vendor_source_review_reply.md`

Hardware 输出把 03-04 packet 转成可人工发布的 PR #5 review-thread Markdown reply / sanitized summary。它明确 `PRRT_kwDOSWB9286CJ3tX` 仍是 `ready_for_manual_github_review_reply_not_proven`，本地 vendor source boundary 只来自 `docs/vendor/VENDOR_INDEX.md`、`base_ctrl.py`、`config.yaml`、`json_cmd.h`，2D LiDAR / ToF 继续是 `hardware_material_pending` / `not_proven`。

### Robot Platform Engineer

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`。
- 更新 `docs/interfaces/ros_contracts.md`。

Robot 只读暴露 `robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary`，保留 `software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate`、`software_proof`、`not_proven`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false` 和 `safe_to_control=false`。

### User Touchpoint Full-Stack Engineer

- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 新增 `mobile/web/fixtures/robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary.json`。
- 更新 `docs/product/mobile_user_flow.md`。

Mobile/web 只读展示 `PRRT_kwDOSWB9286CJ3tX` 的 reply-dispatch 状态。Start Delivery / Confirm Dropoff / Cancel 继续 fail-closed；没有新增 endpoint、ACK、cursor、retry 或控制副作用。

### Product Manager / OKR Owner

- 更新 `OKR.md`。
- 更新 `docs/process/okr_progress_log.md`。
- 新增本文件。
- 新增 `side2side_check.md`。
- 新增 `final.md`。

Product closeout 明确：本轮只生成可人工发布的 PR #5 review-thread Markdown reply / sanitized summary；没有实际发布 GitHub reply；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`。

## 3. 验证结果

### Worker 证据汇总

- Hardware：vendor index exists；03-04 packet summary exists；`py_compile` pass；`python3 -m unittest tests/test_pr5_vendor_source_review_reply_dispatch.py` 输出 `Ran 5 tests ... OK`；generator 输出 `overall_status=not_proven`、`reply_status=ready_for_manual_github_review_reply_not_proven`；required `rg` pass；scoped `git diff --check` pass。
- Robot：`py_compile` pass；`python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 221 tests in 0.608s OK`；required `rg` pass；scoped `git diff --check` pass。
- Full-Stack：`python3 mobile/web/test_mobile_web_entrypoint.py` 输出 `Ran 149 tests ... OK`；`node --check mobile/web/app.js` pass；required `rg` pass；scoped `git diff --check` pass。

### Product / Integration 复核

Product closeout 复跑：

```bash
rg -n "sprint_type: epic|pr5_vendor_source_review_reply_dispatch|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate|software_proof|not_proven|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch
git diff --check -- OKR.md docs/process/okr_progress_log.md pc-tools/evidence/pr5_vendor_source_review_reply_dispatch.py tests/test_pr5_vendor_source_review_reply_dispatch.py docs/interfaces/pr5_vendor_source_review_reply_dispatch.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary.json docs/product/mobile_user_flow.md sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch
```

结果：required `rg` 命中 closeout 所需字段；scoped `git diff --check` 通过。

## 4. 偏差和边界

- 本轮没有实际发布 GitHub reply；生成的 Markdown reply 仍需人工复核后手动发布。
- `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`。
- `reply_status=ready_for_manual_github_review_reply_not_proven` 不等于 reviewer 已接受，不等于 thread resolved。
- 本轮不证明真实 2D LiDAR / ToF、WAVE ROVER/UART/HIL、真实手机/browser、O5 external proof、route/elevator field pass 或 delivery success。
- Objective 5 保持约 68%，Objective 1 保持约 81%，Objective 4 保持约 99%，均不提高。

## 5. OKR 最低优先级核对

当前最低 Objective 仍是 Objective 5（约 68%）。本 sprint 未针对 O5 completion，因为没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 证据。本轮改走 PR #5 reply-dispatch，是为了处理仍 unresolved 的 `PRRT_kwDOSWB9286CJ3tX` review-thread 风险，并且只记录 `software_proof` / `not_proven` 边界。
