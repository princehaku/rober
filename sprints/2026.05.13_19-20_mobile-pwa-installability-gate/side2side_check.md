# Sprint 2026.05.13_19-20 Mobile PWA Installability Gate - Side2Side Check

## 验收结论

本轮按 PRD/tech-plan 验收，Objective 4 手机 PWA installability software proof 成立，可作为 `software_proof_docker_cloud_hosted_mobile_pwa_installability_gate` 收口；不作为 Objective 5 真实外部材料、不作为真实手机设备验收、不作为真实 PWA install prompt、不作为 delivery success。

## Side-by-side 对照

| 验收项 | 计划口径 | 实际证据 | 结论 |
| --- | --- | --- | --- |
| Cloud-hosted PWA gate | 通过 cloud-relay hosted URL 验证当前 `mobile/web/` PWA | `cloud_hosted_pwa_installability_summary.json`：`ok=true`，`hosted_url=http://127.0.0.1:61214/` | 通过 |
| Manifest installability metadata | 覆盖 name、short_name、start_url、scope、display、theme/background、icons、evidence boundary | summary 中 manifest required 字段均为 true，display 为 standalone，icons 路由 200 | 通过 |
| Service worker 控制面隔离 | `/api/*`、`/robots/*`、commands、ACK、diagnostics、非 GET 不缓存、不排队、不重放 | summary 中 `api_bypassed`、`robots_bypassed`、`commands_bypassed`、`ack_bypassed`、`diagnostics_bypassed`、`non_get_bypassed`、`no_queue_or_replay_api` 均为 true | 通过 |
| Offline shell 安全边界 | 离线壳不启用 Start/Confirm/Cancel，不把 ACK 写成成功 | summary 中 `primary_actions_disabled=true`、`ack_not_success=true` | 通过 |
| Browser viewports | 390x844 与 768x900 无 overflow、主操作 disabled、Diagnostics/Support 可用 | 两个 viewport 均 passed；primary actions disabled；Diagnostics/Support available；bundle visible/copyable | 通过 |
| Robot metadata fence | installability/browser metadata 不触发 command、ACK、cursor | Task B `Ran 112 tests in 52.197s OK`；metadata-only 不触发 collect/confirm_dropoff/cancel、不 POST ACK、不推进/持久化 cursor | 通过 |
| ACK 语义 | ACK 只是 accepted/processing evidence，不是 delivery success | sprint docs、OKR、progress log 均保留该口径 | 通过 |

## OKR 判定

- Objective 4：从约 70% 谨慎上调到约 72%。理由是本轮把 cloud-hosted `mobile/web/` PWA 的 manifest、service worker、offline shell、static routes、browser viewports、fail-closed 主操作和 metadata-only robot fence 串成可复现 software proof。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 或其他真实外部 O5 材料。
- Objective 1/2/3：不调整。本轮没有硬件、Nav2/fixed-route、task_orchestrator、HIL 或真实送达证据。

## 未证明事项

- 真实 iPhone/Android device behavior：not_proven。
- production app：not_proven。
- 真实 PWA install prompt：not_proven。
- public HTTPS/TLS、真实 4G/cloud、OSS/CDN live traffic、production DB/queue：not_proven。
- Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成、真实送达：not_proven。

## 产品收口

本轮用户价值是让同一份手机 PWA 在 cloud-relay hosted URL 上具备可机器验收的 installability/browser readiness，而不是把本地 Docker/browser proof 包装成真实用户现场闭环。下一轮如果继续 O5，必须拿真实外部材料；如果外部材料仍不可用，继续 O4 时应转向真实手机设备/browser、production app 或真实 PWA install prompt 验收。
