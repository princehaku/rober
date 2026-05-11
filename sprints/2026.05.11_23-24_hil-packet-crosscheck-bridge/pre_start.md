# Sprint 2026.05.11_23-24 HIL Packet Crosscheck Bridge - Pre Start

## 状态

- 阶段：pre_start
- 时间：2026-05-11 23:00 Asia/Shanghai
- 触发请求：继续下一轮迭代；优先推进 OKR 完成度最低的 O1；功能往前走；测试只围栏；本机仍只有 Docker/无真实硬件。
- 本轮边界：只创建本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`，为后续 Engineer 把 HIL packet gate 输出接入 run-level crosscheck 做准备。

## 用户价值和产品北极星

北极星仍是让普通手机用户把垃圾交给小车后，小车能沿固定路线完成低成本、可复盘、可恢复的送垃圾闭环。当前最短板是 O1 真实 WAVE ROVER `hil_pass` evidence packet 仍缺；在没有硬件的机器上继续重试 move-test 不能产生用户价值。

本轮用户价值是把上轮已交付的 HIL packet gate 继续往 O2/O3 证据链连接：只有 gate 输出 `status=hil_pass` 且 O3 fixed-route/O2 task record 使用同一 `evidence_ref` 时，crosscheck 才能被视为 real-run aligned。`blocked` 或 `software_proof` packet 必须让 crosscheck 失败，避免软件证明被误写成实跑闭环。

## OKR 映射

| 优先级 | Objective | 当前证据 | 本轮判断 |
| --- | --- | --- | --- |
| P0 | O1 硬件协议可信底盘 | `OKR.md` 4.1 显示 O1 约 75%，低于 O2/O3/O4/O5；最新 `d4c4089` 已交付 `scripts/hil_evidence_packet_gate.py`，但真实 WAVE ROVER `hil_pass` 仍缺。 | 不尝试在无硬件机器上制造 `hil_pass`；把 gate 输出变成后续 run-level crosscheck 的硬前置。 |
| P1 | O3 可验证导航与固定路线 | `scripts/evidence_crosscheck.py` 已能按 `evidence_ref` 对齐 fixed-route status/replay/task record，但尚未消费 HIL gate 状态。 | 本轮下一步抓手是让 O3 crosscheck 只有在 HIL gate 为 real `hil_pass` 时才算 real-run aligned。 |
| P1 | O2 可恢复送垃圾任务闭环 | `2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof` 已有 same-`evidence_ref` software proof。 | 后续 task record 也必须与同一个 HIL `evidence_ref` 对齐，才能从 software proof 升级为真实运行证据。 |

## 上轮未完成项和阻塞

- `sprints/2026.05.11_22-23_hil-evidence-packet-gate/final.md`：Docker-only HIL evidence packet gate ready；真实 `hil_pass` pending。
- 同一 final 明确：synthetic `hil_pass` 只是 gate 逻辑验证，不是实车证据；真实 packet 通过后，需要用相同 `evidence_ref` 连接 O2/O3 crosscheck。
- `sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/final.md`：O2/O3 已有 same-`evidence_ref` software proof，但后续必须接真实 HIL + fixed-route + task record。
- 当前本机仍无 WAVE ROVER/串口，不能产生真实硬件 evidence packet。

## KR 拆解

| KR | 目标 | 证据口径 |
| --- | --- | --- |
| O1.KR-A | HIL gate 输出成为真实运行证据的入口门槛。 | crosscheck 必须读取 gate output 或 packet metadata，并要求 `status=hil_pass`。 |
| O3.KR-B | fixed-route replay 与 HIL packet 使用同一 `evidence_ref`。 | `scripts/evidence_crosscheck.py` 在 `evidence_ref` 不一致时返回 mismatch。 |
| O2.KR-C | task record 与 HIL packet 使用同一 `evidence_ref`。 | task record 自动查找或显式输入时，必须和 route status/HIL gate 对齐。 |
| Evidence.KR-D | blocked/software proof 不可被升级为 real-run aligned。 | gate 输出 `blocked` 或 `software_proof` 时 crosscheck 必须失败，并说明原因。 |

## 本轮核心抓手

本轮核心抓手是把 HIL gate 和 O2/O3 crosscheck 之间的产品验收口径固化下来：`hil_pass + same evidence_ref` 才是 real-run aligned；其余状态只能是 blocked/software proof。实现阶段由 `robot-software-engineer` 主责修改 `scripts/evidence_crosscheck.py`，`hardware-engineer` 只读确认 `hil_evidence_packet_gate.py` 输出 contract，`autonomy-engineer` 只读确认 fixed-route replay 字段不被破坏。

## 做什么

- 创建新的 sprint 目录和三份规划文档。
- 明确 `scripts/evidence_crosscheck.py` 后续要增加 HIL gate input。
- 明确 gate 输出 `status=hil_pass` 与 same-`evidence_ref` 是 real-run aligned 的必要条件。
- 明确 `blocked`、`software_proof`、缺 gate output、缺同一 `evidence_ref` 都必须让 crosscheck 失败。
- 明确下一阶段只做文件层/脚本层围栏验证，不扩大 UI、Nav2 或宽泛测试。

## 不做什么

- 不尝试真实硬件 `hil_pass`，因为本机无 WAVE ROVER/串口。
- 不把 synthetic `hil_pass` 或 Docker-only fixture 写成实车证据。
- 不扩大 UI、operator 页面、Nav2 行为或任务状态机功能。
- 不修改本轮文件范围外的代码、硬件配置、launch 参数或 `.codex/config.toml`。
- 不用宽泛回归测试替代本轮证据链推进。

## 优先级和验收口径

| 优先级 | 验收点 | 通过标准 |
| --- | --- | --- |
| P0 | Sprint 规划文档存在 | 三个文件均创建在 `sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/`。 |
| P0 | 证据边界清晰 | 文档明确 `hil_pass + same evidence_ref` 才能 real-run aligned。 |
| P0 | blocked/software proof 失败口径清晰 | 文档明确 gate 输出 `blocked` 或 `software_proof` 时 crosscheck 必须返回失败。 |
| P1 | Owner 和文件范围清晰 | 下一阶段主责 `robot-software-engineer`，文件范围以 `scripts/evidence_crosscheck.py` 与 targeted fixtures/docs 为主。 |

## 对应责任 Engineer

- `product-okr-owner`：本轮创建 sprint 规划文档并定义产品验收口径。
- `robot-software-engineer`：下一阶段主责把 HIL gate output 接入 `scripts/evidence_crosscheck.py` 并运行围栏验证。
- `hardware-engineer`：下一阶段只读确认 `scripts/hil_evidence_packet_gate.py` 输出 contract 和 status/evidence_ref 字段语义。
- `autonomy-engineer`：下一阶段只读确认 fixed-route replay/status 字段对齐不被破坏。
- `full-stack-software-engineer`：本轮不介入。

## 风险、阻塞和需要补齐的证据链

- 当前本机无真实 WAVE ROVER/串口，O1 仍不能升级为真实 `hil_pass`。
- 若 crosscheck 只对齐 route/task record 而不读取 HIL gate 状态，O2/O3 software proof 仍可能被误认为真实运行闭环。
- 若 gate output 与 route/task record 的 `evidence_ref` 生成规则不一致，same-run proof 会断链。
- 真实完成仍需要同一 `evidence_ref` 下的 HIL packet、fixed-route replay 和 task record 实跑样本。

## 需要创建或更新的 sprint 文档

- 本轮创建：`pre_start.md`
- 本轮创建：`prd.md`
- 本轮创建：`tech-plan.md`
- 下一阶段实现后必须更新：`tech-done.md`
- 验收或风险状态变化后更新：`side2side_check.md`、`final.md`
