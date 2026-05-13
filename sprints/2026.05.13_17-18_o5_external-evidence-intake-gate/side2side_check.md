# Sprint 2026.05.13_17-18 O5 External Evidence Intake Gate - Side2Side Check

## 用户要求对照

| 要求 | 对照结果 |
| --- | --- |
| 根据近期 PR 和评审，建议下一步深入 OKR，建议必须有具体证据 | 本轮从 `OKR.md` 4.1、`12-13` DB/queue external probe、`14-15` OSS/CDN live probe、`16-17` browser proof final 推导出 O5 external evidence intake gate。 |
| 用 team 继续完成 OKR | Task A Full-stack 与 Task B Robot 并行执行；Task C Product closeout 在 A/B 后收口。 |
| 重新在功能往前走 | 新增 `trashbot.external_evidence_intake` artifact、CLI writer、preflight consumption 和 metadata-only compatibility fence，不只是计划。 |
| 别测试代码一堆，测试只围栏 | 验证限制在 Task A relay unittest、Task B bridge/protocol unittest、py_compile、CLI/preflight smoke 和 scoped diff check。 |
| 优先推进 OKR 完成度低的部分 | 当前最低 Objective 是 O5 约 67%，本 sprint 针对 O5。 |
| 本机没有真实硬件，只有 Docker | 本轮不触碰 O1/HIL、WAVE ROVER、Nav2 实跑或真实送达；证据保持 software proof。 |
| 最后提交 git 并推送远程 | 由主节点完成最终 integration fence 后 commit/push。 |

## 证据边界检查

- 已完成：external evidence intake schema、checksum、redaction、artifact writer、preflight consumption。
- 已完成：Robot metadata-only fence，证明 external evidence metadata 不触发 action、ACK 或 cursor 推进。
- 未完成：真实外部材料接入。没有真实 OSS/CDN、真实云、真实 4G/SIM、真实 production DB/queue、真实 HTTPS/TLS 公网入口。

## 用户可见价值

后续拿到真实外部材料时，不需要把凭证、URL、响应体或 traceback 粘进 sprint 文档；可以先转成 `trashbot.external_evidence_intake` 脱敏 artifact，再通过 preflight 和 phone-safe readiness 判断是否能推进 O5。

## 验收结论

本 sprint 满足 Docker-only 功能推进目标，但不满足真实外部环境验收。Objective 5 保持约 67%，不因本地 intake gate 上调。
