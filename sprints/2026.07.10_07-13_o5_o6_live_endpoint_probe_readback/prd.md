# O5/O6 Live Endpoint Probe Readback PRD

## 用户价值

普通用户和运营人员最终需要看到的是：手机/PC 侧发起的任务是否经过真实云中转、是否被生产级状态层记录、是否能按同一 `task_id` 回读并定位失败原因。本轮不解决真实云资源到位问题，但要让外部 endpoint probe 结果进入同一任务证据链，减少后续接入 production cloud 时的人工对照成本。

## OKR 对齐

- O5 / KR1：云中转 commands/status/ack 主链路需要从本地 shadow 过渡到 live endpoint / production-like probe evidence。
- O5 / KR6：4G 中断、OSS 写失败、CDN 不可达、生产 DB/queue 问题需要能在远程诊断中区分。
- O6 / KR2 / KR6：任务记录和事件证据需要支持按 `robot_id / task_id / date` 查询，并供 PC/手机消费。

## 需求

1. Robot Software 新增或扩展 smoke/readback，使 live endpoint probe artifact 能被同一 `task_id` 汇总到 O5/O6 证据链。
2. O6 archive/readback 或 consumer detail 必须能回读 probe 摘要，并保持脱敏。
3. 本轮必须明确 proof boundary，不能把可执行 probe 契约误写成真实 production cloud 成功。
4. 文档必须同步更新 `docs/interfaces/o6_cloud_archive_api.md` 与 `docs/product/cloud_4g_infrastructure.md`。

## 非目标

- 不接入真实公网域名、真实 TLS 证书、真实 4G/SIM、真实 production DB/queue 或 OSS/CDN 账号。
- 不声明真实 robot motion、真实 delivery record、operator confirmation 或 delivery success。
- 不修改硬件、串口、WAVE ROVER、Nav2 或 O7 UI。

## 验收

- 单元测试覆盖 probe artifact 缺失、有效 artifact、危险字段泄露/hostile artifact fail-closed。
- smoke summary 或 O6 readback 中存在 probe status、blocked reasons、next required evidence、proof boundary 和 false safety fields。
- 文档写清真实切换入口和本轮证据边界。
