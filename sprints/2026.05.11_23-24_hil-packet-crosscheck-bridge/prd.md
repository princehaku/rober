# Sprint 2026.05.11_23-24 HIL Packet Crosscheck Bridge - PRD

## 状态

- 阶段：prd
- 时间：2026-05-11 23:00 Asia/Shanghai
- 产品负责人：`product-okr-owner`
- 目标 owner：`robot-software-engineer`
- 产品决策：本轮不要尝试真实硬件 `hil_pass`，也不要扩大 UI/测试；主线仍是 O1 -> O3 -> O2。下一步可执行抓手是把 HIL gate 输出接入 `scripts/evidence_crosscheck.py` 的 run-level 校验。

## 背景和问题

最新提交 `d4c4089` 已交付 `scripts/hil_evidence_packet_gate.py`，能够在 Docker-only 文件层判定 HIL packet 为 `blocked`、`software_proof` 或 `hil_pass`。这解决了 O1 evidence packet 的本地 gate 问题，但还没有把 gate 结果接到 O3 fixed-route replay 和 O2 task record 的 crosscheck。

`OKR.md` 当前 O1 约 75%，低于其他 Objective，真实 WAVE ROVER `hil_pass` 仍缺。`sprints/2026.05.11_22-23_hil-evidence-packet-gate/final.md` 明确 synthetic `hil_pass` 只是 gate 逻辑验证，不是实车证据；真实 packet 通过后，需要用相同 `evidence_ref` 连接 O2/O3 crosscheck。`sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/final.md` 明确 O2/O3 已有 same-`evidence_ref` software proof，但后续要接真实 HIL + fixed-route + task record。

产品问题是：如果 `scripts/evidence_crosscheck.py` 只验证 route status/replay/task record 之间的字段一致，而不读取 HIL gate 状态，那么 blocked/software proof 仍可能被误解为 real-run aligned。

## 用户价值和产品北极星

普通手机用户最终要的是一次可信的送垃圾闭环：底盘确实动过、路线确实跑过、任务记录确实来自同一次运行。HIL packet crosscheck bridge 的用户价值在于把这三段证据用同一个 `evidence_ref` 串起来，并让错误证据在脚本层失败。

本轮北极星贡献：让未来实车验收不依赖人工口头判断，而是通过 `hil_pass + same evidence_ref` 的脚本证据确认底盘、路线和任务记录属于同一次真实运行。

## OKR 映射

- O1.KR：硬件协议可信底盘。HIL gate 已能判定 packet 状态；本轮要求 O1 gate 状态成为 O2/O3 real-run aligned 的入口门槛。
- O3.KR：可验证导航与固定路线。fixed-route status/replay 必须与 HIL packet 同一 `evidence_ref`，且 HIL gate 为 `hil_pass` 才能算真实路线运行证据。
- O2.KR：可恢复送垃圾任务闭环。task record 必须与 HIL packet 和 route status 同一 `evidence_ref`，才能算真实任务复盘证据。

## KR 拆解或更新

| KR | 用户可感知收益 | 本轮可交付证据 |
| --- | --- | --- |
| O1.KR1 gate 状态被强制消费 | 不让 blocked/software proof 被包装成实车通过。 | `tech-plan.md` 要求 `evidence_crosscheck.py` 读取 HIL gate output，并拒绝非 `hil_pass`。 |
| O3.KR2 route replay 绑定真实 HIL | 固定路线复盘来自同一次真实底盘运行。 | `evidence_ref` 不一致或缺 gate output 时 crosscheck 非 0。 |
| O2.KR3 task record 绑定真实 HIL | 任务恢复/失败记录能证明来自真实 run。 | task record 与 route status/HIL gate 使用同一 `evidence_ref`。 |
| Evidence.KR4 失败原因可解释 | Engineer 能快速定位是 gate 状态、缺文件还是 evidence_ref mismatch。 | crosscheck 输出包含 `hil_gate.status`、`evidence_ref` mismatch 或 missing gate 说明。 |

## 本轮核心抓手

核心抓手是为下一阶段实现定义一个窄接口：给 `scripts/evidence_crosscheck.py` 增加 HIL gate output 输入，要求 `status=hil_pass` 且 `evidence_ref` 与 route status/task record 一致。blocked/software gate 输出必须让 crosscheck 失败。

## 做什么

- 定义 crosscheck 新输入：HIL gate output JSON 或 packet gate 结果文件。
- 定义 real-run aligned 规则：`hil_gate.status == "hil_pass"`，且 `hil_gate.evidence_ref == route_status.evidence_ref == task_record.evidence_ref`。
- 定义失败规则：
  - gate output 缺失时，不允许声明 real-run aligned。
  - gate output 为 `blocked` 时，crosscheck 返回失败并输出 blocked reason。
  - gate output 为 `software_proof` 时，crosscheck 返回失败并说明不是 real HIL。
  - gate `evidence_ref` 与 route/task 不一致时，crosscheck 返回 mismatch。
- 定义围栏验证：最小 fixture 覆盖 `hil_pass` 对齐、`blocked` 失败、`software_proof` 失败、`evidence_ref` mismatch。

## 不做什么

- 不做真实硬件 `hil_pass`。
- 不把 synthetic gate fixture 当作 OKR 的真实 HIL evidence。
- 不修改 UI、operator diagnostics、Nav2 route execution 或 task orchestrator 状态机。
- 不新增宽泛测试矩阵；只做 `evidence_crosscheck.py` 的 targeted script/fixture 验证。
- 不触碰 `.codex/config.toml` 或本轮范围外文件。

## 优先级

| 优先级 | 需求 | 理由 |
| --- | --- | --- |
| P0 | crosscheck 必须拒绝 `blocked` 和 `software_proof` gate output | 这是防止 O1/O3/O2 证据污染的核心。 |
| P0 | crosscheck 必须校验 HIL gate 与 route/task 的同一 `evidence_ref` | 这是 same-run proof 的最低门槛。 |
| P1 | 输出失败原因必须可读 | 便于下一次有硬件时快速补缺口。 |
| P1 | 保持现有 route/task software proof 路径可用但不能冒充 real-run aligned | 软件围栏仍有价值，但证据等级必须清楚。 |

## 验收口径

规划文档本轮验收：

1. `pre_start.md`、`prd.md`、`tech-plan.md` 均存在。
2. scoped `git diff --check` 通过。
3. 文档明确 O1 是主线，且本机无硬件不能生成真实 `hil_pass`。
4. 文档明确 `blocked`/`software_proof` gate output 必须让 real-run crosscheck 失败。

实现阶段验收：

1. `python3 scripts/evidence_crosscheck.py ... --hil-gate-output <blocked.json>` 返回非 0，并输出 `blocked` 或 blocked reason。
2. `python3 scripts/evidence_crosscheck.py ... --hil-gate-output <software_proof.json>` 返回非 0，并说明不是 real HIL。
3. `python3 scripts/evidence_crosscheck.py ... --hil-gate-output <hil_pass_same_ref.json>` 在 route/task record 同一 `evidence_ref` 时返回 0。
4. `python3 scripts/evidence_crosscheck.py ... --hil-gate-output <hil_pass_wrong_ref.json>` 返回非 0，并输出 `evidence_ref` mismatch。

## 对应责任 Engineer

- `robot-software-engineer`：主责实现 `scripts/evidence_crosscheck.py` HIL gate input、fixtures、targeted 验证和 `tech-done.md`。
- `hardware-engineer`：只读确认 `scripts/hil_evidence_packet_gate.py` 输出字段，包括 `status`、`evidence_ref`、`blocked_reason` 和失败项语义。
- `autonomy-engineer`：只读确认 fixed-route replay/status 字段不被破坏。
- `full-stack-software-engineer`：本轮不介入。

## 风险、阻塞和需要补齐的证据链

- 当前机器无真实串口，仍不能产生真实 WAVE ROVER `hil_pass`。
- synthetic `hil_pass` fixture 只能验证 crosscheck 逻辑，不是实车证据。
- 如果 HIL gate output 未来没有稳定 JSON 输出路径，Engineer 需要先读取当前脚本输出格式并选择最小兼容方式。
- 真实 OKR 升级仍需要同一 `evidence_ref` 下的真实 HIL packet、fixed-route replay 和 task record。

## 需要创建或更新的 sprint 文档

- 已创建/本轮创建：`pre_start.md`、`prd.md`、`tech-plan.md`
- 实现后必须更新：`tech-done.md`
- 验收或收口后更新：`side2side_check.md`、`final.md`
