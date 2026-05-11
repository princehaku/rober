# Sprint 2026.05.11_22-23 HIL Evidence Packet Gate - PRD

## 状态

- 阶段：prd
- 时间：2026-05-11 22:00 Asia/Shanghai
- 产品负责人：`product-okr-owner`
- 目标 owner：`hardware-engineer`
- 产品决策：主线深入 O1；承认本机无真实硬件，不能把 move-test 重试当完成；本轮功能抓手改为 Docker-only HIL evidence packet gate。

## 背景和问题

`OKR.md` 4.1 显示 O1 约 75%，低于 O2/O3/O4/O5。上一轮 `2026.05.11_21-22_o1-docker-humble-preflight-unblock` 已把 Docker/Humble preflight 阻断归因为 registry mirror/proxy，并确认本机没有真实串口，因此不能产生 `hil_pass`。

同时，上一轮 `tech-done.md` 已明确 HIL packet 的 required evidence files：`command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。`hardware_smoke_wave_rover.py --status` 只能证明 `source=software_proof` readiness/blocker，不是实机通过。

产品问题是：下一次有硬件时，不能等到人工复盘才发现 packet 缺文件、`evidence_ref` 不一致、`source` 写错或 blocked 结果被误报为 `hil_pass`。需要一个 Docker-only 也可执行的 gate，先把证据合规性收紧。

## 用户价值和产品北极星

普通手机用户最终需要的是可靠送垃圾闭环，而不是工程日志本身。HIL evidence packet gate 的用户价值在于：把底盘真实可控这件事从“工程师口头说跑过”变成可审计、可复账、可连接 O2/O3 的证据。只有 O1 的证据可信，后续任务恢复、固定路线、route replay 才能形成产品闭环。

本轮北极星贡献：减少下一次真机上车的证据不确定性，避免 `software_proof`、blocked evidence 和真实 `hil_pass` 混淆。

## OKR 映射

- O1.KR：硬件协议可信底盘。本轮主线是 `hil_pass` evidence packet 的合规 gate，不声明底盘已实机通过。
- O2.KR：可恢复送垃圾任务闭环。后续 task record 可用同一 `evidence_ref` 对接 HIL packet，验证任务失败/恢复是否发生在真实底盘 run 上。
- O3.KR：可验证导航与固定路线。后续 route replay 可用同一 `evidence_ref` 与 HIL packet 交叉 proof，避免 route software proof 脱离真实底盘证据。

## KR 拆解或更新

| KR | 用户可感知收益 | 本轮可交付证据 |
| --- | --- | --- |
| O1.KR1 packet 必需文件可预检 | 真机上车后少走返工，证据缺口能被脚本提前发现。 | `tech-plan.md` 定义 gate 必查文件：`command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。 |
| O1.KR2 来源状态不混淆 | 不把 Docker-only 或无串口结果误传成实机能力。 | gate 判定必须只允许 `software_proof`、`blocked`、`hil_pass` 三类，且 `hil_pass` 需要真实 packet 满足所有硬门槛。 |
| O1.KR3 blocked 可解释 | 用户和 operator 能知道是缺硬件、缺文件、缺反馈还是 topic sample 不完整。 | gate 输出必须包含失败项和 `blocked_reason`，不能只返回 generic failure。 |
| O2/O3.KR4 同证据引用可复账 | 后续任务记录和路线复盘能证明来自同一次 run。 | gate contract 必须保留并校验 `evidence_ref`，后续可接 `scripts/evidence_crosscheck.py`。 |

## 本轮核心抓手

核心抓手是定义并交付下一阶段的 engineering plan：`hardware-engineer` 实现一个 Docker-only 可运行的 HIL evidence packet gate。该 gate 不依赖当前机器有硬件，但必须严格防止假阳性 `hil_pass`。

## 做什么

- 定义 evidence packet gate 的输入：一个 evidence run 目录或显式文件路径。
- 定义 evidence packet gate 的必需文件：`command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。
- 定义三类输出：
  - `software_proof`：只证明脚本、格式或 dry-run 合规，不代表硬件通过。
  - `blocked`：缺真实串口、缺必需文件、缺反馈帧、缺 topic sample 或 Docker/Humble preflight 阻塞。
  - `hil_pass`：真实 WAVE ROVER run 的证据包完整，且同一 `evidence_ref` 下必需文件和样本全部合规。
- 定义后续 O2/O3 支撑：same-`evidence_ref` 可被 `scripts/evidence_crosscheck.py` 与 task record/route replay 消费。

## 不做什么

- 不做真实 move-test，因为 CEO 已明确本机无真实硬件。
- 不把 `--status` 或 Docker-only 输出写成 `hil_pass`。
- 不改 O2/O3 行为、导航或 UI 功能。
- 不新增宽泛测试矩阵。
- 不触碰 `.codex/config.toml` 或本轮范围外文件。

## 优先级

| 优先级 | 需求 | 理由 |
| --- | --- | --- |
| P0 | gate 严格区分 `software_proof`、`blocked`、`hil_pass` | 这是防止 OKR 证据污染的核心。 |
| P0 | `hil_pass` 必须要求完整 evidence packet | O1 当前最低且缺真实 packet，不能继续口头补证。 |
| P1 | 输出缺口可定位 | 下一次有硬件时要能快速知道缺哪一项。 |
| P1 | `evidence_ref` 可供 O2/O3 复账 | 支撑后续 route/task record 交叉 proof。 |

## 验收口径

规划文档本轮验收：

1. `pre_start.md`、`prd.md`、`tech-plan.md` 均存在。
2. scoped `git diff --check` 通过。
3. 文档明确 O1 是主线，且本机无硬件不能生成 `hil_pass`。

实现阶段验收：

1. Docker-only fixture 或 blocked packet 能被 gate 判定为 `software_proof` 或 `blocked`，不得误判 `hil_pass`。
2. 缺任一 required evidence file 时返回非通过结果，并指出缺失文件。
3. 缺 `feedback_T1001.log` 真实反馈或缺 `/odom`、`/imu/data`、`/battery` sample 时不得通过 `hil_pass`。
4. 合规 packet 的 `evidence_ref` 可被后续 crosscheck 命令复用。

## 对应责任 Engineer

- `hardware-engineer`：主责实现 gate、fixtures、围栏验证和 `tech-done.md`。
- `robot-software-engineer`：仅在 gate 输出需要与 task record/result metadata 对齐时提供只读接口事实。
- `autonomy-engineer`：仅在 route replay crosscheck 需要读取 gate 输出时提供只读接口事实。
- `full-stack-software-engineer`：本轮不介入。

## 风险、阻塞和需要补齐的证据链

- 当前机器无真实串口，`hil_pass` 仍只能等待真实 WAVE ROVER 环境。
- Docker registry mirror/proxy 仍可能阻塞完整 Docker/Humble build，但 gate 应尽量保持可在普通 Python/文件层运行。
- 若未来 packet 没有统一 `evidence_ref`，O2/O3 的 same-run proof 会断链。
- 如果 gate 只检查文件存在而不检查来源状态和关键内容，仍可能把空文件或 blocked log 误判为合规证据。

## 需要创建或更新的 sprint 文档

- 已创建/本轮创建：`pre_start.md`、`prd.md`、`tech-plan.md`
- 实现后必须更新：`tech-done.md`
- 验收或收口后更新：`side2side_check.md`、`final.md`
