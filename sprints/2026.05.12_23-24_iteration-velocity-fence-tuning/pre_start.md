# Sprint 2026.05.12_23-24 Iteration Velocity Fence Tuning - Pre Start

## 状态

- 阶段：pre_start
- 时间：2026-05-12 23:48 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 触发来源：CEO（用户）明确反馈"每次迭代东西太少、进度太慢、coding 改动对整体进展帮助不大、是否要并行研发"

## 触发背景与诊断证据

主节点已就 `OKR.md`、`AGENTS.md`、`.codex/agents/registry.toml`、近 60 个 sprint 目录和近 10 轮 tech-plan/final 做了只读复盘，得出以下证据：

1. **迭代节奏过快但单轮产出过小**：05-10 共 17 个 sprint、05-11 共 13 个、05-12 已 4 个，绝大多数跨度 30-60 分钟。`OKR.md` 近 10 个进度快照里大量"无新增，仅护栏"、"+1pp"叙述。
2. **核心瓶颈是真实硬件实测，但近 10 轮几乎没碰**：连续 4 轮 Docker 环境调试均卡在同一 `registry mirror/proxy returns text/html` blocker；HIL 系列在 `/tmp` synthetic fixture 上反复验证 bridge 逻辑。
3. **OKR 完成度严重不均**：O1=75%、O2=74%、O3=76%、O4=75%、O5=30%、O6=12%。近 20 轮针对最低 O5/O6 的不到 1/4，反复在 O1/O3/O4 刷 +1pp 软件证据。
4. **并行规则写了但实际几乎没用**：仅 `2026.05.12_02-03_remote-4g-command-loop` 真正多 owner 并行；其余 sprint 多为 1 owner 串行。
5. **六文档契约对微切片 sprint 开销过大**：30 分钟 sprint 写 6 个 markdown，文档时间 ≥ 实现时间。
6. **主节点禁区让微变更也走 dispatch**，对 5-50 行单文件改动成本远高于实际编码。

## 本轮目标

CEO 已就关键参数做出决策，本轮直接落地：

| 参数 | CEO 决策 |
| --- | --- |
| 修改范围 | `AGENTS.md` + `.codex/agents/registry.toml` + 新建 `docs/process/iteration_velocity.md` + `OKR.md` 4.1 节增加软提醒规则 |
| 并行强度 | 默认每个 sprint 2-4 个并行子 agent |
| 主节点写代码口子 | 不开，保持纯 dispatch |
| 文档分层 | Epic（六文档全套） / Micro（仅 `tech-done.md`） |
| OKR 最低优先级 | 软提醒：tech-plan 必须说明为何不做最低 Objective |
| Blocker 切换 | 同一 blocker 卡 ≥ 2 轮强制切换或升级用户决策 |

## OKR 影响预判

- 本轮属于流程/治理改动，不直接提升 O1-O6 完成度。
- 落地后预期：后续 sprint 平均 OKR 推进幅度从 +1pp 提升到 +3~5pp；最低 Objective（O5、O6）每周获得显式优先权重；硬件 blocker 不再被反复消费。

## 责任 Owner

| Owner | 范围 |
| --- | --- |
| `product-okr-owner` | 实质修改 `AGENTS.md`、`.codex/agents/registry.toml`、新建 `docs/process/iteration_velocity.md`、追加 `OKR.md` 4.1 节软提醒段落 |
| 主节点 | sprint 留档（pre_start / prd / tech-plan / 验收后 tech-done / side2side / final） |

## 风险与阻塞

- 本轮要修改的 `AGENTS.md`、`.codex/agents/registry.toml` 都不在 `product-okr-owner` 默认 `owner_paths` 里。本 sprint 通过 tech-plan 临时授权 product-okr-owner 改动这两份文件，理由是这两份文件本质就是 agent 治理规则，是 Product Owner 的元层职责。
- 修改的是规则本身，存在自指风险（用新规则验证旧任务）。本轮只覆盖未来 sprint，不追溯过往 sprint。
- 不修改 OKR 完成度数字，避免误把流程改进当业务进展。
