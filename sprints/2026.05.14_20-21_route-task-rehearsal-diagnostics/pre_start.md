# Sprint 2026.05.14_20-21 Route Task Rehearsal Diagnostics - Pre Start

sprint_type: epic

## 本轮目标

把上一轮 `software_proof_docker_route_task_rehearsal_artifact_gate` 从 PC 工具落盘推进到诊断/支持面可消费的 route/task rehearsal summary。目标是服务 Objective 2 和 Objective 3：任务复盘、固定路线软件排练、task_record evidence anchor 与 operator diagnostics 之间形成可见闭环。

## 证据来源

- `OKR.md` 4.1：Objective 5 约 68% 最低，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；Objective 2/3 均约 78%，剩余缺口是真实 Nav2/fixed-route、同一 `evidence_ref` 上车复账和 delivery success。
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/final.md`：上一轮已能保存 route/task rehearsal artifact，但明确风险仍是 Docker/local software proof，不是真实路线运行或 HIL。
- 近期反复问题：O5 外部证据缺失已多轮阻止进度；O4 mobile/PWA metadata 已到约 95%，继续本地 metadata 边际收益低；O1 HIL 被本机无真实硬件锁住。

## 推荐深入的 OKR

1. Objective 2/3：本轮主攻。具体抓手是让 route/task rehearsal artifact 可被 diagnostics 读取、脱敏、分类和展示，方便后续真实路线/上车复账时直接沿同一 `evidence_ref` 追踪。
2. Objective 5：只有拿到真实外部材料才回切。没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 时，不继续堆本地 O5 metadata。
3. Objective 1：真实 WAVE ROVER/HIL 缺设备，本机只能保持 blocked，不消费新 sprint。
4. Objective 4：当前约 95%，除非有真实 iPhone/Android、production app 或真实 PWA prompt/userChoice 材料，否则不继续堆本地移动端 proof。

## Owner

- `autonomy-engineer`：补强 PC route/task rehearsal artifact 的 phone-safe/diagnostics consumption 字段和工具文档。
- `robot-software-engineer`：让 operator diagnostics 读取 route/task rehearsal artifact summary，保持 metadata-only 和 not delivery success。
- `product-okr-owner`：验收收口、OKR 边界、进度日志和 sprint 文档。

## 风险

- 本机没有真实硬件、真实 Nav2/fixed-route、真实串口或 HIL，本轮不能上调 O1，也不能宣称真实 delivery success。
- 本轮不碰真实 O5 外部云，不得把 diagnostics consumption 写成公网/4G/OSS/CDN/DB/queue proof。
- 测试只做围栏：针对新增 summary/CLI 的最小 unittest、`py_compile`、required `rg` 和 scoped `git diff --check`。
