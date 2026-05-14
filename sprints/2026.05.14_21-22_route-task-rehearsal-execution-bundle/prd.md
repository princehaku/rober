# Sprint 2026.05.14_21-22 Route Task Rehearsal Execution Bundle - PRD

sprint_type: epic

## 用户价值

现场支持或开发者不应只拿到分散的 status、task record、replay 和 artifact 路径。本轮要提供一个可重复执行的 bundle 入口，把一次 route/task rehearsal 的关键软件证据聚合成 manifest，并让 diagnostics 以只读方式展示该 bundle 的状态、证据边界和下一步。

## 北极星

普通支持人员能看懂：这是一份 Docker/local 软件排练 bundle，说明 status/replay/task_record/crosscheck 是否一致，以及下一步需要真实路线/HIL 补证；它不是 delivery success。

## OKR 映射

- Objective 2：提升任务闭环复盘能力，从 diagnostics 单点摘要推进到可复跑 execution bundle。
- Objective 3：提升固定路线可验证能力，把 route status、replay 和 task_record 对账打包为可传递材料。
- Objective 5：不推进，除非出现真实外部云/4G/OSS/CDN/DB/queue 材料。

## 本轮核心抓手

1. 新增 route/task rehearsal execution bundle 生成入口，输出 manifest、artifact ref、crosscheck 状态、not_proven 和 boundary。
2. Operator diagnostics 新增只读 bundle summary，不能放行 Start/Confirm/Cancel、ACK、cursor、HIL 或 delivery success。
3. 文档和 OKR 只按 `software_proof_docker_route_task_rehearsal_execution_bundle_gate` 记录。

## 验收口径

- 能用现有 route status / task record fixture 或临时输入生成 bundle manifest。
- bundle manifest 指向 artifact，并保留 `software_proof`、`not_proven`、HIL 未证明和 delivery success 未证明边界。
- diagnostics 能读取 bundle manifest，并在 missing/invalid/crosscheck-fail 场景保守降级。
- 验证只跑围栏命令：py_compile、一个 bundle CLI drill、现有 task_record/diagnostics unittest、required rg、scoped diff check。

## 非目标

- 不做真实 HIL。
- 不做真实 Nav2/fixed-route 实跑。
- 不做真实 dropoff/cancel completion 或 delivery success。
- 不新增大测试套件，不做宽泛回归。
