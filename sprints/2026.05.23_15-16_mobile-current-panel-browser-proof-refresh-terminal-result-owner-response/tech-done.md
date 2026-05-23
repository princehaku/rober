# Tech Done

sprint_type: epic

更新时间：2026-05-23 15:13 CST

## 实际改动

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
  - 新增 `mobile_current_panel_browser_proof_refresh_terminal_result_owner_response` capability 常量和 `software_proof_docker_mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_gate` boundary 常量。
  - 将两个最新 terminal-result owner-response read-only panels 纳入 current-panel DOM / boundary 断言：
    - `verified_terminal_result_material_owner_response_intake`
    - `verified_terminal_result_material_owner_response_review_decision`
  - 新增 `terminal_result_owner_response_panels_fail_closed` 判定，要求两个 panel 同时保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- `mobile/web/test_mobile_web_entrypoint.py`
  - 扩展 current-panel refresh 静态测试，覆盖新 capability、boundary、两个 owner-response panel DOM id、panel boundary 和 fail-closed 判定名。
- `mobile/test_mobile_web_entrypoint.py`
  - 扩展 browser gate 入口测试，防止后续刷新漏掉 terminal-result owner-response panel 覆盖。
- `docs/product/mobile_user_flow.md`
  - 补充 terminal-result owner-response current-panel browser proof refresh 的运行方式和产品边界。
- `sprints/2026.05.23_15-16_mobile-current-panel-browser-proof-refresh-terminal-result-owner-response/evidence/`
  - 写入 fresh local Chromium-family 证据 JSON/PNG 和 summary：
    - `mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_390x844.json`
    - `mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_390x844.png`
    - `mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_768x900.json`
    - `mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_768x900.png`
    - `mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_summary.json`

## 验证结果

### Browser proof gate

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.23_15-16_mobile-current-panel-browser-proof-refresh-terminal-result-owner-response/evidence --fresh-profile --require-console-zero --capability mobile_current_panel_browser_proof_refresh_terminal_result_owner_response --evidence-boundary software_proof_docker_mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_gate
```

结果：通过。

关键日志：

```text
viewport=390x844 passed=true ... material_resolution_panels_fail_closed=true terminal_result_owner_response_panels_fail_closed=true ... current_panels_status=passed current_boundaries_status=passed phone_safe_status=passed fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0 evidence_boundary=software_proof_docker_mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_gate
viewport=768x900 passed=true ... material_resolution_panels_fail_closed=true terminal_result_owner_response_panels_fail_closed=true ... current_panels_status=passed current_boundaries_status=passed phone_safe_status=passed fresh_browser_markers_status=passed service_worker_dynamic_no_store_status=passed console_zero_status=passed console_error_count=0 evidence_boundary=software_proof_docker_mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_gate
summary=sprints/2026.05.23_15-16_mobile-current-panel-browser-proof-refresh-terminal-result-owner-response/evidence/mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_summary.json ok=true capability=mobile_current_panel_browser_proof_refresh_terminal_result_owner_response evidence_boundary=software_proof_docker_mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_gate fresh_profile=true require_console_zero=true
```

### Unit tests

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
```

结果：通过，`Ran 302 tests in 2.857s`，`OK`。

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
```

结果：通过，`Ran 54 tests in 0.756s`，`OK`。

## 失败定位

首轮 browser proof gate 失败在新增判定 `terminal_result_owner_response_panels_fail_closed=false`。根因是判定额外依赖 not_proven 文案中的“真实手机/browser”表述，而实际渲染在 fixture safe summary 下会改写 not_proven 列表；panel DOM 和 boundary 已经存在且正确。修复后判定改为检查两个 panel 的 fail-closed flags：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 剩余风险

- 本轮证据边界是 `software_proof_docker_mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_gate`，只证明本地 fresh Chromium-family current-panel browser proof。
- 这不是 true phone/browser proof，不是真实 iPhone/Android device behavior，不是 O5 external proof，不是真实 terminal result，不是 route/elevator field pass，不是 HIL，不是 dropoff/cancel completion，不是 delivery success。
- Start Delivery、Confirm Dropoff、Cancel 保持 disabled，`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 未解除。
- 本轮 no OKR percentage lift；真实提升仍需要 Product closeout 基于真实手机/browser、真实外部云或真实现场材料另行更新。

## Task B Robot 只读验收补充

Product closeout 接受 Task B read-only evidence。Robot consultation 未改文件，确认 `mobile/web/app.js` 的两个 owner-response panels 优先消费：

- `robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary`
- `robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary`

若 Robot safe summary 不存在，panel 只回退到对应 safe summary / nested safe summary，不读取 raw material。Task B 还确认 unsafe raw-field detection 与 whitelist safe_copy path 保持 fail closed；相关 fixture 均保留 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`can_collect=false`、`can_confirm_dropoff=false`、`can_cancel=false`。Spot check 中唯一 unsafe-ish 命中是 `hil_pass_missing`，语义是缺材料声明，不是 HIL pass。

Task B validation evidence：

```text
rg ... exited 0
git diff --check -- sprints/2026.05.23_15-16_mobile-current-panel-browser-proof-refresh-terminal-result-owner-response exited 0
```

## Product Closeout 验收判断

Task A evidence：接受。理由是 browser gate 在 `390x844` 与 `768x900` 两个 viewport 均通过，并同时报告 `terminal_result_owner_response_panels_fail_closed=true`、`current_panels_status=passed`、`current_boundaries_status=passed`、`console_zero_status=passed`；unit tests `mobile.web.test_mobile_web_entrypoint` 与 `mobile.test_mobile_web_entrypoint` 均通过；required `rg` 与 scoped `git diff --check` 均通过。首轮失败已定位为动态 not_proven copy 断言过脆，修复后改为检查两个 panel 的 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 稳定 flags。

Task B evidence：接受。理由是只读 consultation 与 tech-plan 边界一致，确认 Robot diagnostics safe-summary consumption 没有 raw material consumption，也没有解除 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

本 sprint closeout 证据边界保持 `software_proof_docker_mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_gate`。它不是 true phone/browser，不是真实 terminal result，不是 O5 external proof，不是 public HTTPS/TLS，不是 4G/SIM，不是 OSS/CDN live traffic，不是 production DB/queue，不是 worker/cutover，不是 HIL，不是 route/elevator field pass，不是 delivery success，不是 PR #5 resolution；no OKR percentage lift。
