# Task A Evidence - mobile PWA install prompt evidence export

Owner: full-stack-software-engineer

Evidence boundary: `software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`

Scope:
- `mobile/web` now exports `mobile_pwa_install_prompt_evidence_export*` as support/acceptance metadata.
- Export input priority is explicit export, event capture, previous install-prompt evidence, handoff/device/browser support metadata, then blocked-by-design fallback.
- Copy and download payloads share the same whitelist-only JSON and keep `safe_to_control=false` plus `ack_semantics=accepted_processing_only_not_delivery_success`.

Validation:
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint` -> 35 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py` -> OK.
- `node --check mobile/web/app.js` -> OK.
- Required schema/boundary `rg` command -> matched updated app, fixture, test, README, and product flow docs.
- Scoped `git diff --check` -> OK.

Not proven:
- real iPhone/Android device behavior
- production app
- real PWA install prompt or user choice
- O5 external proof
- HIL
- delivery success
