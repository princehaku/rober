# O5/O6 External Live Probe Micro Sprint Tech Done

## Sprint Type

sprint_type: micro

## Actual Changes

- Added `pc-tools/workstation/scripts/o5-o6-external-live-probe.mjs` and `npm run o5o6:external-probe`.
- The probe emits `schema=trashbot.o5_o6.external_live_probe.v1` and checks only three fixed GET surfaces:
  - cloud-relay `GET /api/o5/readiness/health`
  - cloud-relay `GET /api/o6/archive/health`
  - PC workstation `GET /api/o5-o6/cloud-relay-health`
- The probe reads base URLs from CLI/env, reads bearer only from env, reports only `token_status`, and redacts credential-bearing values.
- The probe preserves no-control fields: `safe_to_control=false`, `sends_commands=false`, `robot_control_executed=false`, `reads_hardware=false`, `delivery_success=false`.
- Added Vitest coverage for observed O5/O6/PC aggregate health and for unreachable services returning stable fail-closed JSON.
- Updated O5/O6 documentation and OKR records:
  - `docs/product/remote_4g_mvp.md`
  - `docs/interfaces/o6_cloud_archive_core_api.md`
  - `docs/interfaces/o1_o5_90_evidence_boundary.md`
  - `docs/process/okr_progress_log.md`
  - `OKR.md`

## Verification Results

Run on 2026-06-01 Asia/Shanghai:

```bash
$ node --check pc-tools/workstation/scripts/o5-o6-external-live-probe.mjs
# exited 0

$ cd pc-tools/workstation && npm run test
Test Files  2 passed (2)
Tests  52 passed (52)

$ cd pc-tools/workstation && npm run lint
# exited 0 with no findings
```

Local fail-closed probe:

```bash
$ cd pc-tools/workstation && node scripts/o5-o6-external-live-probe.mjs || true
schema=trashbot.o5_o6.external_live_probe.v1
probe_status=fail_closed
token_status=absent
summary.reachable_count=0
blocked_reasons=[base_url_not_configured, base_url_not_configured, base_url_not_configured]
safe_to_control=false
sends_commands=false
robot_control_executed=false
reads_hardware=false
delivery_success=false
```

Remote read-only SSH probe attempt:

```bash
$ ssh -o BatchMode=yes -o ConnectTimeout=5 -p 37878 root@192.168.1.11 '... node readiness check ...'
ssh: connect to host 192.168.1.11 port 37878: Connection timed out
```

This means no remote command ran and no bearer was printed. The remote evidence for this run is a structured blocker: `ssh_network_timeout`, not an O5/O6 endpoint observation.

Full verification after documentation updates:

```bash
$ cd pc-tools/workstation && npm run build
# passed

$ git diff --check -- <本轮改动文件>
# passed
```

## Failure Positioning

- `npm run test -- --runInBand` failed because Vitest does not support Jest's `--runInBand` option. The accepted repo command is `npm run test`, which passed.
- The first external probe test failed because safe PC aggregate metadata keys `token_status` / `token_envs` were classified as sensitive markers. The scanner now allows those metadata paths only; real bearer/token values still fail closed.
- Remote SSH to `root@192.168.1.11:37878` timed out, so this run did not prove Orange Pi can execute the probe.

## Remaining Risks

- This sprint does not prove real public HTTPS/TLS, real 4G/SIM, production DB/queue, production worker/cutover, real OSS/CDN live traffic, real inference runtime, real phone/browser, robot ACK, HIL, or delivery success.
- The external probe is an evidence entrypoint and fail-closed classifier. It depends on operator-provided PC/cloud base URLs and environment bearer for positive reachability observations.
- Remote Orange Pi / upper-computer execution remains `not_proven` because SSH timed out in this run.

---

## 2026-06-01 19:50 注释纪律修补

### Actual Changes

- Minimal patch only in `pc-tools/workstation/scripts/o5-o6-external-live-probe.mjs`.
- Added Chinese technical comments around fail-closed status, credential redaction, no-control/no-POST boundaries, endpoint aggregation, blocked reason limiting, and `not_proven` evidence boundaries.
- No behavior, schema, endpoint, command path, test expectation, package metadata, or hardware/control integration changed.

### Verification Results

```bash
$ node --check pc-tools/workstation/scripts/o5-o6-external-live-probe.mjs
# exited 0

$ node -e "const fs=require('fs');const p='pc-tools/workstation/scripts/o5-o6-external-live-probe.mjs';const lines=fs.readFileSync(p,'utf8').split(/\r?\n/).filter((line,i,arr)=>i<arr.length-1||line.length);const cn=/[\u4e00-\u9fff]/;const comments=lines.filter(l=>/^\s*\/\//.test(l)&&cn.test(l)).length;console.log(JSON.stringify({total:lines.length,chineseCommentLines:comments,ratio:Number((comments/lines.length*100).toFixed(2)),passes:comments/lines.length>0.2},null,2));"
{
  "total": 400,
  "chineseCommentLines": 83,
  "ratio": 20.75,
  "passes": true
}

$ cd pc-tools/workstation && npm run test
Test Files  2 passed (2)
Tests  52 passed (52)

$ cd pc-tools/workstation && npm run build
✓ built in 2.46s
# exited 0

$ cd pc-tools/workstation && npm run lint
# exited 0 with no findings
```

### Failure Positioning

- No validation failure in this repair pass.

### Remaining Risks

- This pass only fixes AGENTS.md Chinese comment ratio discipline for the external live probe script.
- It does not add real public HTTPS/TLS, real 4G/SIM, production DB/queue, OSS/CDN live traffic, real inference runtime, real phone/browser, robot ACK, HIL, or delivery success proof.
