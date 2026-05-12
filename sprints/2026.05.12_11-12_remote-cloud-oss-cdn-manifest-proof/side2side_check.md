# Sprint 2026.05.12_11-12 Remote Cloud OSS/CDN Manifest Proof - Side2Side Check

## 状态

- 阶段：side2side_check
- 验收时间：2026-05-12 09:21 Asia/Shanghai
- Product Owner：`product-okr-owner`
- Evidence boundary：`software_proof_docker_oss_cdn_manifest`
- Product verdict：P0 通过，按 Docker/local software proof 收口。

## PRD P0 对照验收

| PRD P0 验收项 | 证据 | 判定 |
| --- | --- | --- |
| 能在 Docker/local 环境生成 manifest artifact | Full-stack CLI smoke 输出 `manifest generate: ok=True, evidence_boundary=software_proof_docker_oss_cdn_manifest`。 | 通过 |
| 校验命令或 preflight 能拒绝 schema/version/checksum/prefix/CDN URL 错误 artifact | `test_remote_cloud_relay.py` 覆盖 manifest artifact 生成、字段 contract、checksum 校验、CDN URL 规则、无效 artifact fail-closed、preflight pass/warning/blocked 三类路径。 | 通过 |
| 有效 artifact 使 preflight 输出 `evidence_boundary=software_proof_docker_oss_cdn_manifest` | CLI smoke 输出 `preflight consume: ok=False, evidence_boundary=software_proof_docker_oss_cdn_manifest, overall_status=blocked, oss_cdn_manifest=pass`。整体 blocked 是生产缺口未证明的预期结果。 | 通过 |
| artifact/preflight 明确列出真实 OSS/CDN/4G/云/硬件未证明项 | `tech-done.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md` 均保留 real OSS upload、STS issuance、CDN origin fetch、lifecycle policy、production account、real cloud、real 4G/SIM、HTTPS/TLS public ingress、production DB/queue、Nav2/fixed-route、WAVE ROVER/HIL 未证明口径。 | 通过 |
| phone-safe redaction 检查通过 | Full-stack unit tests 覆盖脱敏断言；文档和 `tech-done.md` 明确不得暴露 bearer token、Authorization header、OSS secret、AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。 | 通过 |
| `remote_bridge` compatibility targeted tests 通过 | Robot compatibility worker 运行 `test_remote_bridge_protocol.py` 与 `test_remote_bridge.py`，输出 `Ran 31 tests in 15.132s OK`。 | 通过 |
| scoped `git diff --check` 通过 | Full-stack worker 对实现、测试、产品文档和 `tech-done.md` scoped diff check 通过；本收口另跑 OKR/sprint 文档 scoped diff check。 | 通过 |

## P0 不通过条件复核

- 未发现输出暗示 `production_ready=true`、真实云 ready、OSS uploaded、CDN reachable 或 delivery success。
- 未发现 artifact/preflight 证据把 manifest pass 写成真实上传、CDN 回源、手机正式链路或送达成功。
- 当前 diff 范围未触碰硬件/vendor、Nav2/fixed-route、WAVE ROVER、串口或 launch 硬件参数。
- command/status/ack HTTP API 未改变，ACK 仍只表示 robot bridge 已处理 command envelope，不代表真实 delivery success。

## Product Acceptance

本轮 P0 通过。用户价值成立：O6 从“OSS/CDN 只有配置形态和文档口径”推进到“manifest artifact 可生成、可校验、可被 preflight 消费，并能提升本地 evidence boundary”。这为后续真实 OSS upload、STS 和 CDN 回源提供了稳定 product contract。

验收边界必须保持保守：本轮不是生产云上线，不是真实 OSS/CDN 流量，不是真实 4G/SIM，不是 HTTPS/TLS 公网入口，不是手机正式 UI，也不是 Nav2/fixed-route、WAVE ROVER 或 HIL。

## 剩余风险和下一步证据链

- 真实 OSS upload、STS issuance、CDN origin fetch、生命周期策略、生产账号和密钥 rotate 仍未证明。
- 真实云 HTTPS、公网入口、防火墙、生产 DB/queue、多实例一致性和生产灾备仍未证明。
- 真实 4G/SIM、弱网/断网恢复和 carrier 网络行为仍未证明。
- 正式手机 UI 尚未消费 manifest；后续需要定义 artifact 过期、刷新、权限和私有对象引用策略。
