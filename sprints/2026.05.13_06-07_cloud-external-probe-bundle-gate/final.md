# Sprint 2026.05.13_06-07 Cloud External Probe Bundle Gate - Final

## 最终结论

本 sprint 完成 `software_proof_docker_cloud_external_probe_bundle_gate`。Full-stack worker 建立 cloud external probe bundle artifact、Docker smoke 和 preflight consumption；Robot worker 建立 metadata-only response compatibility fence。Product side2side 验收通过。

证据边界必须保持为 Docker/local software proof：本轮没有真实云、真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue、HIL、Nav2/fixed-route、WAVE ROVER 或真实送达。

## 用户价值和产品北极星

用户价值：未来云中转接入真实公网 URL 前，团队已有一份可复用的 endpoint probe bundle，可以把 `/healthz`、`/readyz`、`/preflightz` 的状态转成 phone-safe / preflight-safe 摘要，避免把 “healthz 200” 误读成生产就绪。

产品北极星：普通手机用户只需要知道云端控制通路是否可用、是否应走 fallback、是否需要运维处理；系统内部必须用可审计 artifact 区分本地软件证明和真实生产证明。

## OKR 更新口径

- Objective 5：从约 57% 保守上调到约 59%。
- Objective 1/2/3/4：不调整。
- 最新 sprint：`2026.05.13_06-07_cloud-external-probe-bundle-gate`。
- 证据边界：`software_proof_docker_cloud_external_probe_bundle_gate`。
- 不能声明：真实云、真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue、HIL、Nav2/fixed-route、WAVE ROVER、真实送达。

## KR 拆解完成情况

- KR-A external probe artifact schema：完成。`schema=trashbot.cloud_external_probe_bundle`、`schema_version=1`。
- KR-B preflight/CLI 生成或消费 artifact：完成。有效 bundle 仍保持 `production_ready=false`、`overall_status=blocked`。
- KR-C Docker smoke endpoint 覆盖和脱敏：完成。`/healthz`、`/readyz`、`/preflightz` 均被 probe 覆盖，redaction checks 通过。
- KR-D Robot side-effect fence：完成。metadata-only response 不触发 action、不 ACK、不推进或持久化 cursor。
- KR-E 文档同步：完成。`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`docs/interfaces/ros_contracts.md`、`cloud-relay/README.md` 已同步工程口径。

## 验证摘要

```text
Full-stack:
Ran 56 tests ... OK
py_compile pass
docker_smoke pass
cloud_external_probe_bundle status=pass
evidence_boundary=software_proof_docker_cloud_external_probe_bundle_gate
production_ready=false
scoped git diff --check pass

Robot:
Ran 66 tests in 33.399s OK
py_compile pass
scoped git diff --check pass
```

## 剩余风险和阻塞

- 真实云部署仍缺公网 VM / HTTPS / 域名 / 反向代理 / 防火墙实配证据。
- 真实 4G/SIM、真实手机设备、production app 和用户侧验收未完成。
- OSS/CDN live traffic、production DB/queue、多实例一致性、production disaster recovery 未完成。
- 机器人实物链路仍缺 WAVE ROVER、真实串口、`T=1001` feedback、HIL、Nav2/fixed-route、真实送达。
- 本轮是部署前 artifact gate，不是上线许可。

## 下一步建议

下一轮继续按 live `OKR.md` 4.1 选择最低且可推进的 Objective。若继续推进 Objective 5，优先补真实云入口前的 production DB/queue 或公网/TLS dry-run 配置证据；若 CEO 提供真实云/4G/SIM/OSS/CDN 凭证，则另开 sprint 做真实外部 probe，而不能复用本轮 Docker/local proof 直接声明生产就绪。
