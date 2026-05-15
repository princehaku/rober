# Sprint 2026.05.16_01-02 Elevator Evidence Driven Mainline - PRD

sprint_type: epic

## 1. 用户价值

现场同学下一次受控楼宇演练前，需要的不只是材料包，还需要机器人软件主链路能读取“门状态、目标楼层、驶出条件、人工协助和同一 `evidence_ref`”这类 rehearsal evidence，并把结果写进 task record、diagnostics/mobile safe summary。这样现场复跑后才能判断缺的是门状态、楼层确认、Nav2/fixed-route runtime、completion signal 还是 HIL，而不是继续靠聊天和手工对照。

## 2. OKR 对齐

- Objective 2：推进 KR6/KR7。电梯 assisted delivery 已是必达主链路；本轮让行为层从固定 dry-run 阶段推进到 evidence-driven dry-run rehearsal，不证明真实电梯。
- Objective 3：推进同一 `evidence_ref` 下 route/task/elevator evidence 的可复账链路。Nav2/fixed-route 仍是 software proof 或 blocked，不能声明实跑。
- Objective 4：手机端只读解释 evidence-driven elevator assist 状态，普通用户/现场同学能看懂为什么需要人工接管。
- Objective 5：本轮不推进 completion；没有真实外部云/4G/OSS/CDN/DB/queue 材料。

## 3. 验收口径

- 新 artifact/schema 必须固定为 Docker/local software proof，默认 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。
- Robot 行为链必须支持：
  - 无 evidence artifact 时保持既有 dry-run fallback。
  - evidence artifact 明确失败时 fail closed，并写入 `manual_takeover_reason`、`failure_reason`、`human_intervention_required=true`。
  - evidence artifact 通过时仍只表示 rehearsal evidence chain passed，不代表真实送达。
- Mobile panel 必须展示 evidence-driven summary，同时保留主操作 fail-closed。
- 验证只做围栏：目标 unit、`py_compile`、`node --check`、required `rg`、scoped `git diff --check`。

## 4. 不做什么

- 不做真实 HIL、真实电梯、真实 Nav2/fixed-route、真实手机设备、真实云外部 probe。
- 不新增广泛测试堆叠。
- 不把 execution pack、ACK、HTTP accepted、diagnostics summary 或 rehearsal evidence 写成 delivery success。

