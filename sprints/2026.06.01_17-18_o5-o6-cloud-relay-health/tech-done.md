# O5/O6 Cloud Relay Health Micro Sprint Tech Done

## Sprint Type

sprint_type: micro

## Actual Changes

- Reviewed the existing PC workstation O5/O6 cloud relay health implementation and tests.
- Fixed the minimal build/test blockers in `pc-tools/workstation/src/server/o5O6CloudRelayHealth.ts`: strict TypeScript now sees the IPv4 tuple as fixed-length, an unused helper was removed, the primary fail-closed reason has a fallback, and sensitive-key matching no longer treats `task_count` as an `sk` secret marker.
- Tightened the upstream contract guard in `pc-tools/workstation/src/server/o5O6CloudRelayHealth.ts`: `reads_hardware=true` and `connects_cloud_production=true` are now treated as dangerous true markers and force the aggregated probe to fail closed.
- Added a regression test in `pc-tools/workstation/test/catalog.test.ts` proving the PC aggregation endpoint fails closed for upstream hardware-read, production-cloud and sensitive `state_path` markers without echoing the sensitive value.
- Documented `GET /api/o5-o6/cloud-relay-health` in `docs/product/remote_4g_mvp.md` as a PC workstation only, read-only, private/loopback, env-bearer-only aggregation probe.
- Documented the O6 side of the PC workstation aggregated health probe in `docs/interfaces/o6_cloud_archive_core_api.md`, including O6 read boundary and fail-closed behavior.

## Verification Results

Run on 2026-06-01 18:14-18:17 CST:

```bash
$ cd pc-tools/workstation && npm run build
> rober-pc-tools-workstation@0.1.0 build
> tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
vite v7.3.3 building client environment for production...
✓ 33 modules transformed.
✓ built in 2.33s

$ cd pc-tools/workstation && npm run test
> rober-pc-tools-workstation@0.1.0 test
> vitest run
Test Files  2 passed (2)
Tests  50 passed (50)
Duration  13.08s

$ cd pc-tools/workstation && npm run lint
eslint . exited 0 with no findings.

$ git diff --check -- pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/server/catalog.ts pc-tools/workstation/src/server/o5O6CloudRelayHealth.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/catalog.test.ts docs/product/remote_4g_mvp.md docs/interfaces/o6_cloud_archive_core_api.md docs/product/pc_tools_workstation.md sprints/2026.06.01_17-18_o5-o6-cloud-relay-health/tech-done.md
exited 0 with no whitespace errors and no output.
```

First-run failures and fixes:

- `npm run build` initially failed on strict TypeScript checks in `o5O6CloudRelayHealth.ts`; fixed the tuple/unused-helper/fallback issues and reran successfully.
- `npm run test` initially failed because the sensitive-key regex matched `task_count` through the broad `sk` token; narrowed the AK/SK key match and reran successfully.
- Follow-up review found that upstream `reads_hardware=true` and `connects_cloud_production=true` were not dangerous true markers yet; added the markers plus a regression test and reran build/test/lint/diff-check successfully.

## Remaining Risks

- This sprint does not claim real public cloud, real 4G/SIM, production DB/queue, real OSS/CDN, real phone/browser, HIL, robot ACK, or delivery success.
- `GET /api/o5-o6/cloud-relay-health` remains a PC workstation software proof surface only; it depends on an operator-provided private/loopback cloud-relay base URL and bearer environment variables.
- The probe still does not read hardware or connect to production cloud itself; it only detects and blocks those claims if an upstream health payload reports them as true.
- No UI, OKR, hardware/vendor, credential, `dist`, or `node_modules` changes were made.

## Product / OKR Closeout

Product closeout run on 2026-06-01 Asia/Shanghai.

用户价值和产品北极星：本轮把 O5 readiness health 与 O6 archive health 汇总到 PC workstation 的只读 `GET /api/o5-o6/cloud-relay-health`，让运营调试入口能用一个健康探针判断云中转控制面和 archive proof 的软件状态。它服务于北极星里的“普通用户只看手机、运营/售后在 PC 端可诊断、云端可运营”，但不等于真实生产云或真实机器人控制闭环。

OKR 映射和方向判断：O5/O6 方向继续，不暂停、不替换。O5 从约 91% 调整到约 92% `software + PC aggregated live-health probe`；O6 从约 91% 调整到约 92% `software + PC aggregated live-health probe`。调整理由是本轮关闭了 PC 运营侧聚合 live-health 只读探针缺口，并通过 build/test/lint/diff-check 复验；但它只是在 software/PC workstation 层面增加可观测性，所以只保守增加 1pp。

KR 拆解和历史归档：本轮没有 KR 可归档为完成。O5 KR1/KR6 与 O6 KR2/KR6 的可观测性更完整，但真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、真实 OSS upload、OSS/CDN live traffic、真实模型/外部推理 runtime、external live probe、真实云、真实 phone/browser、上车数据、robot ACK 和 delivery success 仍为 `not_proven`，因此 O5/O6 KR 继续留在当前推进区。

本轮核心抓手：用 private/loopback baseUrl allowlist、env-only bearer、fail-closed false fields、read-only GET、不 POST、不碰 `/robots/*`，把 PC 运营探针做成安全的聚合状态入口。

下一步需要做什么：优先补 O5/O6 真实部署证据链，包括公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实云 external probe、真实 phone/browser 验收，以及 O6 真实 OSS upload / inference runtime / 上车数据查询。

优先级和验收口径：O5/O6 仍并列当前最低优先级，后续验收必须看到真实环境证据或生产等价 staging 证据；仅有本地 mock、PC workstation 聚合 endpoint 或 Docker 单测时，只能判定为 software proof，不得写成 production-ready。

对应责任 Engineer：本轮实现 owner 为 `full-stack-software-engineer`；后续真实 4G/云部署与凭证边界需要 `full-stack-software-engineer` 主责，涉及 Orange Pi 隧道/上车采集时由 `robot-software-engineer` 和 `robot-hardware-engineer` 提供接口事实。

风险、阻塞和证据链缺口：真实公网、4G、production DB/queue、OSS/CDN、phone/browser、robot ACK、delivery success 均未证明；当前 probe 依赖 operator 配置 private/loopback cloud-relay base URL 和环境变量 bearer，不能用于公网暴露或控制链路。

历史记录位置和剩余风险：无已完成 KR 历史归档；本轮证据记录在本文件、`OKR.md` 第 4/4.1/5 节和 `docs/process/okr_progress_log.md` 的 `2026-06-01 17-18｜o5-o6-cloud-relay-health` 条目。剩余风险同上。

需要创建或更新的 sprint 文档：Micro sprint 保持 `tech-done.md` 为唯一强制留档；本轮已追加 Product / OKR closeout，不升级 Epic。
