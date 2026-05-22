# Mobile PWA Fresh Browser Proof Refresh Tech Plan

Run time: 2026-05-22 11:04 Asia/Shanghai

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否，主目标为 Objective 4。
- 如不针对，理由：Objective 5 的可提升证据需要真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser external proof；当前 Docker-only 主机无法提供。最近两轮已消费同一 `missing_real_owner_response_material` blocker，本轮按重复 blocker 红线切换到不依赖硬件/外部云的 Objective 4 fresh-browser proof。
- final.md 收口时需复核：本轮是否仍未出现真实 O5/O1/field materials；若出现真实材料，下轮应重新 rerank。

## Architecture And Interface

No product API or ROS2 interface change is planned unless the fresh-browser gate exposes a concrete regression.

The existing gate is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py \
  --output-dir sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/evidence \
  --fresh-profile \
  --require-console-zero
```

Expected proof boundary:

- `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- not true phone/device/browser external proof

## Work Split

### Task A Full-Stack Fresh Browser Execution

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
- `sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/evidence/`
- `sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/tech-done.md`

Validation commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/evidence --fresh-profile --require-console-zero
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
git diff --check -- mobile/web mobile/test_mobile_web_entrypoint.py pc-tools/evidence/phone_browser_acceptance_gate.py docs/product/mobile_user_flow.md sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh
```

### Task B Product Closeout

Owner: `product-okr-owner`

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/tech-done.md`
- `sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/side2side_check.md`
- `sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/final.md`

Validation commands:

```bash
test -f sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/evidence/mobile_pwa_fresh_browser_proof_summary.json
rg -n "mobile_pwa_fresh_browser_proof|software_proof_docker_mobile_pwa_fresh_browser_proof_gate|Objective 5|Objective 4|not true phone/browser|delivery_success=false" sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh OKR.md docs/process/okr_progress_log.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh
```

## Risk Boundary

- Browser proof is local Chromium-family proof only.
- This sprint must not claim real iPhone/Android validation, production app proof, real PWA install prompt/userChoice, real external cloud, real 4G/SIM, real OSS/CDN traffic, production DB/queue proof, route/elevator field pass, WAVE ROVER/UART/HIL, PR #5 resolution, dropoff/cancel completion, terminal delivery result, or delivery success.
- If the browser gate fails, the full-stack owner should fix the concrete scoped issue and rerun the same fenced commands. Do not broaden into test taxonomy migration or unrelated UI rewrite.

