# Mobile PWA Fresh Browser Proof Refresh PRD

Run time: 2026-05-22 11:04 Asia/Shanghai

## Product Goal

普通用户的手机入口必须在当前 repo 状态下保持可打开、可读、fail-closed，并且不会因为旧 service-worker/offline cache、控制面请求缓存、console runtime error 或布局溢出而误导用户继续操作。

本轮目标不是新增测试代码堆量，而是刷新当前 `mobile/web` PWA 的本地 Chromium-family 证据包，确认最近多轮 Robot diagnostics / mobile read-only panels / service-worker cache recovery 仍能在新浏览器 profile 中安全工作。

## OKR Mapping

- Objective 4: direct target. It refreshes local browser evidence for the phone entrypoint and cache-recovery behavior.
- Objective 5: not directly progressed. O5 remains lowest, but real public HTTPS/TLS, 4G/SIM, OSS/CDN, production DB/queue, worker/cutover, or true phone/browser external proof is unavailable on this host.
- Objective 1: not progressed. Real WAVE ROVER/UART/HIL and 2D LiDAR/ToF material proof remain unavailable.

## User Value

The user-facing value is evidence that the current mobile shell still renders the first-screen journey, recovery decisions, terminal-action confirmation, browser acceptance bundle, PWA install prompt evidence, and recent read-only safety panels without enabling Start Delivery / Confirm Dropoff / Cancel under blocked states.

## Acceptance Criteria

- Run `pc-tools/evidence/phone_browser_acceptance_gate.py` with `--fresh-profile --require-console-zero`.
- Evidence directory contains:
  - `mobile_pwa_fresh_browser_proof_390x844.json`
  - `mobile_pwa_fresh_browser_proof_390x844.png`
  - `mobile_pwa_fresh_browser_proof_768x900.json`
  - `mobile_pwa_fresh_browser_proof_768x900.png`
  - `mobile_pwa_fresh_browser_proof_summary.json`
- Summary reports `ok=true`, `fresh_profile=true`, `require_console_zero=true`, and `evidence_boundary=software_proof_docker_mobile_pwa_fresh_browser_proof_gate`.
- The proof confirms service-worker dynamic no-store/bypass rules, `mobile_pwa_cache_recovery` marker, visible ACK-not-delivery-success copy, no console errors, no overflow/overlap, hit areas acceptable, and primary actions disabled.
- Any code fix must remain scoped to `mobile/web`, `mobile/test_mobile_web_entrypoint.py`, `pc-tools/evidence/phone_browser_acceptance_gate.py`, or docs directly tied to this proof.

## Non Goals

- No broad test migration or new test taxonomy work.
- No new local-only owner-response material wrapper.
- No real-device, hardware, HIL, external cloud, OSS/CDN, production DB/queue, route/elevator field-pass, or delivery-success claim.

