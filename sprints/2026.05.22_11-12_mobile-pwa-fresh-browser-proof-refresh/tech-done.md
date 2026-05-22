# Mobile PWA Fresh Browser Proof Refresh Tech Done

Run time: 2026-05-22 11:21 Asia/Shanghai

## Sprint Type

- `sprint_type: epic`
- Owner: `full-stack-software-engineer`
- Evidence boundary: `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`

## Actual Changes

- Fixed the mobile device acceptance boundary DOM id so it no longer duplicates `mobileDeviceEvidenceBoundary`; evidence capture now owns `mobileDeviceEvidenceBoundary`, and acceptance readiness uses `mobileDeviceAcceptanceBoundary`.
- Ensured the verified terminal result material review-decision panel is created before `wireEvents()` attaches the copy listener, preventing a null `addEventListener` runtime exception without enabling any primary action.
- Rendered the fail-closed empty shell once before `wireEvents()` so all dynamic read-only safe-copy panels exist before listener attachment; the subsequent status refresh still controls all user-visible state and primary actions remain gated.
- Added the missing shared `firstObject()` helper used by newer diagnostics/status candidate lookups so acceptance-backfill and related read-only panels do not interrupt the page render.
- Added the missing `mobileRealDeviceRetestRequest` summary in `renderCommandSafety()` so command gating can evaluate the retest-request gate without throwing.
- Kept the browser gate's console-zero behavior strict while enriching runtime exception evidence with URL, line, column, and stack summary for faster scoped failure localization.
- Updated `mobile/test_mobile_web_entrypoint.py` assertions for the current configurable browser artifact prefix and for safe redaction text that says local paths are removed without allowing actual local path prefixes.
- Updated `docs/product/mobile_user_flow.md` with the 2026-05-22 fresh-browser refresh note and preserved the proof boundary.
- Regenerated fresh-browser evidence:
  - `evidence/mobile_pwa_fresh_browser_proof_390x844.json`
  - `evidence/mobile_pwa_fresh_browser_proof_390x844.png`
  - `evidence/mobile_pwa_fresh_browser_proof_768x900.json`
  - `evidence/mobile_pwa_fresh_browser_proof_768x900.png`
  - `evidence/mobile_pwa_fresh_browser_proof_summary.json`

## Validation Results

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/evidence --fresh-profile --require-console-zero
```

Result: pass. `390x844` and `768x900` both reported `passed=true`, `console_zero_status=passed`, `console_error_count=0`, `current_panels_status=passed`, `current_boundaries_status=passed`, `service_worker_dynamic_no_store_status=passed`, `primary_actions_disabled=true`, and summary `ok=true`.

```bash
node --check mobile/web/app.js
```

Result: pass.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
```

Result: pass. `Ran 54 tests ... OK`.

```bash
git diff --check -- mobile/web mobile/test_mobile_web_entrypoint.py pc-tools/evidence/phone_browser_acceptance_gate.py docs/product/mobile_user_flow.md sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh
```

Result: pass.

## Failure Location Fixed

- Initial fresh-browser proof failed on `console_zero_status=failed` from `TypeError: Cannot read properties of null (reading 'addEventListener')` at `wireEvents()` and `current_boundary_failures=["mobileDeviceEvidenceBoundary"]`.
- The first fix exposed `ReferenceError: firstObject is not defined` in `fieldEvidenceRerunExecutionResultAcceptanceBackfillCandidate()`, which interrupted later read-only panel rendering. The helper now exists and preserves the existing candidate priority order.
- The next rerun exposed `ReferenceError: mobileRealDeviceRetestRequest is not defined` inside `renderCommandSafety()`. The missing summary variable is now defined before the retest-request primary-action gate check.
- A final strict rerun exposed another dynamic safe-copy listener hazard at `copyFieldEvidenceMaterialResolutionIntakeButton`. The empty fail-closed shell render now creates dynamic read-only panels before event binding, while the later status refresh still owns all state and action gating.

## Remaining Risks

- This is local Chromium-family software proof only. It is not true iPhone/Android evidence, not a production app proof, not a real PWA install prompt/userChoice observation, not external cloud/4G/OSS/CDN/DB/queue proof, not route/elevator field pass, not WAVE ROVER/UART/HIL, not dropoff/cancel completion, and not delivery success.
- Product closeout still needs to decide whether this evidence changes any OKR text; this full-stack task did not edit `OKR.md`, `docs/process/okr_progress_log.md`, `side2side_check.md`, or `final.md`.

## Product Closeout Addendum

Run time: 2026-05-22 11:27 Asia/Shanghai

### User Value And North Star

用户价值是刷新普通手机入口的当前可用性证据：当前 `mobile/web` PWA 在 fresh Chromium-family profile 下能打开、渲染核心只读证据面板、显示 ACK is not delivery success 的安全文案，并在 blocked fixture state 下保持 Start Delivery / Confirm Dropoff / Cancel disabled。北极星仍是普通用户无需 SSH、ROS2、串口或硬件知识，也能理解当前状态和下一步恢复路径。

### OKR Mapping And KR Boundary

- Objective 4：本轮直接服务手机用户体验与量产边界，证据为 `mobile_pwa_fresh_browser_proof` / `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`。
- Objective 5：仍是最低 Objective，但本轮因连续两轮 `missing_real_owner_response_material` blocker 已被消费，按重复 blocker 红线切到 O4；没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover、true phone/browser external proof 或 verified terminal result，因此 O5 不提升。
- Objective 1/2/3：没有新增硬件、HIL、路线、电梯、Nav2/fixed-route 或真实送达证据。

### Acceptance Summary

- Evidence summary exists: `sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/evidence/mobile_pwa_fresh_browser_proof_summary.json`.
- Summary reports `ok=true`、`fresh_profile=true`、`require_console_zero=true`、`console_error_count=0`、`primary_actions_disabled=true`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
- Two viewport artifacts exist for `390x844` and `768x900`, each with JSON and PNG evidence.

### Product Risks

- This is not true phone/browser proof, not real iPhone/Android behavior, not production app proof, not real PWA prompt/userChoice, not O5 external cloud proof, not HIL, not route/elevator field pass, not dropoff/cancel completion, not verified terminal delivery/dropoff/cancel result, and not delivery success.
- O4 remains conservatively at about 99% because the missing evidence is real device/browser and production-app proof, not another local Chromium-family refresh.
- O5 remains about 68% because no external cloud/4G/OSS/CDN/DB/queue or verified terminal-result material appeared in this sprint.
