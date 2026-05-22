# Mobile Current Panel Browser Proof Refresh Tech Plan

Run time: 2026-05-22 17:18 Asia/Shanghai

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否，主目标为 Objective 4 的当前手机入口 browser proof refresh。
- 不针对 Objective 5 的理由：Objective 5 当前需要真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 或 verified terminal delivery/dropoff/cancel result 才能形成新的 completion evidence；当前 Docker/local 主机没有这些外部材料。最新 `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/final.md` 也明确不要在无真实外部材料时继续堆本地 O5 wrapper。
- Objective 1 也不是本轮目标：Objective 1 约 81%，仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF material、operator HIL report 和 PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution。
- final.md 收口要求：如执行期间没有真实外部/硬件/现场材料，本轮保持 no OKR percentage lift，并继续写明 not true phone/browser。

## Architecture And Interface Boundary

No ROS2 API, cloud API, Robot command API, hardware configuration, launch parameter, or `OKR.md` change is planned.

This sprint should only refresh local browser evidence for the current `mobile/web` shell and its current panels. Any implementation fix must be scoped to a concrete browser-proof regression:

- stale shell or service-worker cache recovery issue
- current panel DOM/fixture wiring issue
- console runtime error
- blocked-state copy or fail-closed primary action regression
- browser gate coverage for current panels / evidence boundary

Expected capability:

- `mobile_current_panel_browser_proof_refresh`

Expected evidence boundary:

- `software_proof_docker_mobile_current_panel_browser_proof_refresh_gate`

Required proof booleans:

- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Required non-claim:

- `not true phone/browser`

## Work Split

### Task A Full-Stack Current Panel Browser Proof Refresh

Owner: `full-stack-software-engineer`

Allowed files:

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/service-worker.js`
- `mobile/web/offline.html`
- `mobile/web/manifest.webmanifest`
- `mobile/test_mobile_web_entrypoint.py`
- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/evidence/`
- `sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/tech-done.md`

Task detail:

- Run the browser proof gate with a fresh profile and console-zero requirement.
- Ensure the gate checks current panels introduced by recent material-resolution / reviewer ACK / terminal-result / support / cloud-readiness work.
- If the gate fails, fix only the concrete current-panel or browser-proof regression.
- Preserve Chinese technical comments if code is touched; any new technical comments must explain why the fail-closed behavior exists.
- Do not enable Start Delivery, Confirm Dropoff, or Cancel in blocked/not_proven fixture states.

Validation commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/evidence --fresh-profile --require-console-zero --capability mobile_current_panel_browser_proof_refresh --evidence-boundary software_proof_docker_mobile_current_panel_browser_proof_refresh_gate
node --check mobile/web/app.js
node --check mobile/web/service-worker.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
rg -n "mobile_current_panel_browser_proof_refresh|software_proof_docker_mobile_current_panel_browser_proof_refresh_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser" mobile/web mobile/test_mobile_web_entrypoint.py pc-tools/evidence/phone_browser_acceptance_gate.py docs/product/mobile_user_flow.md sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh
git diff --check -- mobile/web mobile/test_mobile_web_entrypoint.py pc-tools/evidence/phone_browser_acceptance_gate.py docs/product/mobile_user_flow.md sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh
```

If `phone_browser_acceptance_gate.py` does not yet support the optional `--capability` / `--evidence-boundary` flags, the Full-Stack owner must either add scoped support or run the existing equivalent gate and record the exact emitted boundary in `tech-done.md`.

### Task B Robot Safe Summary Read-Only Consultation

Owner: `robot-software-engineer`

Allowed files:

- `sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/tech-done.md`

Read-only scope:

- `mobile/fixtures/`
- `mobile/web/fixtures/`
- Robot diagnostics summary producers under `onboard/src/` if needed for fact checks
- Existing docs that describe safe diagnostics summaries

Task detail:

- Confirm the current panels consumed by `mobile/web` remain phone-safe summaries.
- Check that no panel requires raw ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER parameters, credentials, local paths, tracebacks, checksums, or complete artifacts.
- Confirm `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false` stay semantically aligned with Robot safe summary fields.

Validation commands:

```bash
rg -n "safe_to_control=false|delivery_success=false|primary_actions_enabled=false|software_proof_docker_mobile_current_panel_browser_proof_refresh_gate|not true phone/browser" sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh mobile/web mobile/fixtures mobile/web/fixtures
git diff --check -- sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh
```

### Task C Product Closeout

Owner: `product-okr-owner`

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/tech-done.md`
- `sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/side2side_check.md`
- `sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/final.md`

Task detail:

- Accept or reject Engineer evidence against this plan.
- If browser proof passes but no true external/phone/material evidence appears, keep Objective 5 about 68%, Objective 1 about 81%, and Objective 2/3/4 about 99%.
- Record that the sprint is `software_proof_docker_mobile_current_panel_browser_proof_refresh_gate` only.
- State no OKR percentage lift unless real external, hardware, field, or true phone/browser proof appears.

Validation commands:

```bash
test -f sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/tech-done.md && test -f sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/side2side_check.md && test -f sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/final.md
rg -n "mobile_current_panel_browser_proof_refresh|software_proof_docker_mobile_current_panel_browser_proof_refresh_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser|no OKR percentage lift" sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh OKR.md docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh
```

## Planning Task Acceptance

This planning task is accepted when these commands pass:

```bash
test -f sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/pre_start.md && test -f sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/prd.md && test -f sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|mobile_current_panel_browser_proof_refresh|software_proof_docker_mobile_current_panel_browser_proof_refresh_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser" sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh
git diff --check -- sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh
```

## Risk Boundary

- 本轮是 planning sprint start，后续才进入 Engineer execution。
- Local Chromium proof is still software proof only; it is not true phone/browser, not real iPhone/Android behavior, not production app proof, and not real PWA prompt/userChoice.
- It is not Objective 5 external proof: not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, and not verified terminal result.
- It is not Objective 1 hardware proof: not WAVE ROVER/UART/HIL, not `/odom`、`/imu/data`、`/battery` real feedback, not 2D LiDAR/ToF material, and not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.
- It is not Objective 2/3 field proof: not real route/elevator field pass, not Nav2/fixed-route runtime, not dropoff/cancel completion, not delivery result, and not delivery success.
