# Sprint 2026.05.11_22-23 HIL Evidence Packet Gate - Pre Start

## 状态

- 阶段：pre_start
- 时间：2026-05-11 22:00 Asia/Shanghai
- 触发请求：开始下一轮迭代；根据当前 OKR 和近期 sprint/评审证据，优先推进完成度最低的 O1；本机没有真实硬件，只有 Docker；功能往前走；测试只做围栏；最后提交并推送。
- 本轮边界：只创建本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`，为后续 Engineer 实现 Docker-only HIL evidence packet gate 做交付准备。

## 用户价值和产品北极星

北极星仍是让普通手机用户把垃圾交给小车后，小车能沿固定路线完成低成本、可复盘、可恢复的送垃圾闭环。当前最影响北极星可信度的是 O1 底盘/HIL 证据仍缺真实 WAVE ROVER `hil_pass` evidence packet；如果证据包字段不完整或 `software_proof` 被误报为 `hil_pass`，后续 O2 任务复盘和 O3 route replay 都无法可信对账。

本轮用户价值不是重复在无硬件主机上尝试真实 move-test，而是把真实上车前/上车后的 evidence packet 做成可预检的 gate：Docker-only 环境可以验证证据包格式、字段、来源和阻塞原因；有硬件时同一 gate 能判断 `hil_pass` 是否合规。

## OKR 映射

| 优先级 | Objective | 当前证据 | 本轮判断 |
| --- | --- | --- | --- |
| P0 | O1 硬件协议可信底盘 | `OKR.md` 4.1 显示 O1 约 75%，低于 O2/O3/O4/O5；O1 仍缺真实 WAVE ROVER `hil_pass` evidence packet。 | 主线深入 O1，但本机无硬件，不再把 move-test 尝试当完成；改做 evidence packet gate。 |
| P1 | O2 可恢复送垃圾任务闭环 | `2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/final.md` 显示 O2 software proof 已能按同一 `evidence_ref` 复账。 | 本轮只保留支撑口径：未来 HIL packet 的 `evidence_ref` 可接 task record 对账。 |
| P1 | O3 可验证导航与固定路线 | 同一 O2/O3 sprint 显示 route replay software proof 已可按 `evidence_ref` 对齐，但仍缺真实 route run。 | 本轮为后续 `scripts/evidence_crosscheck.py` 接入同一 `evidence_ref` 留边界，不扩展导航功能。 |

## 上轮未完成项和阻塞

- `sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/final.md`：Docker/Humble preflight 已归因为 registry mirror/proxy 返回 HTML；本机仍无真实串口，不能产生 `hil_pass`。
- `sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/tech-done.md`：required evidence files 包括 `command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`；`hardware_smoke_wave_rover.py --status` 只是 `source=software_proof`。
- `sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/final.md`：O2/O3 software proof 已能按同一 `evidence_ref` 复账，但仍需真实 HIL/route run 后交叉 proof。

## KR 拆解

| KR | 目标 | 证据口径 |
| --- | --- | --- |
| O1.KR-A | 定义 HIL evidence packet gate 的最小合规 contract。 | gate 能检查必需文件、`evidence_ref`、`source`、`blocked_reason`、`hil_pass` 必备 topic/sample 证据。 |
| O1.KR-B | Docker-only 环境能产出可执行的 software/blocked 判定。 | 没有串口时只允许 `software_proof` 或 `blocked`，不得通过为 `hil_pass`。 |
| O1.KR-C | 真机上车后能用同一 gate 预检 `hil_pass` packet。 | `command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 同一 `evidence_ref` 且来源合规。 |
| O2/O3.KR-D | 后续 crosscheck 能消费同一 `evidence_ref`。 | gate 输出或证据包元数据不破坏 `scripts/evidence_crosscheck.py` 与 task record/route replay 复账入口。 |

## 本轮核心抓手

本轮核心抓手是 Product 定义 sprint：把 O1 从“反复等待硬件”推进到“先把 HIL evidence packet 合规 gate 做出来”。实现阶段由 `hardware-engineer` 主责，`robot-software-engineer` 只在 gate 输出需要对接 task record 或 ROS topic sample 语义时做接口咨询，`autonomy-engineer` 只在 route replay crosscheck 入口需要事实补充时介入。

## 做什么

- 创建 `pre_start.md`、`prd.md`、`tech-plan.md`。
- 明确 evidence packet 必需文件和 `software_proof`、`blocked`、`hil_pass` 判定边界。
- 规划后续 Docker-only gate：无硬件时也能验证字段完整性和阻塞语义。
- 规划后续 same-`evidence_ref` 对接：HIL packet 可被 O2/O3 crosscheck 消费。

## 不做什么

- 不在本机重复真实 `--move-test` 并把失败包装成交付。
- 不声明 `hil_pass`。
- 不新增宽泛测试矩阵，不用测试数量替代功能推进。
- 不修改本轮文件范围外的代码、硬件配置、launch 参数或 `.codex/config.toml`。

## 优先级和验收口径

| 优先级 | 验收点 | 通过标准 |
| --- | --- | --- |
| P0 | Sprint 规划文档存在 | 三个文件均创建在 `sprints/2026.05.11_22-23_hil-evidence-packet-gate/`。 |
| P0 | 证据边界清晰 | 文档明确 Docker-only 只能是 `software_proof` 或 `blocked`，真实 `hil_pass` 需要 WAVE ROVER/串口与完整 packet。 |
| P1 | 实现 owner 明确 | `hardware-engineer` 主责 gate 实现和验证；其他 owner 仅按接口边界咨询。 |
| P1 | O2/O3 支撑保留 | 文档明确同一 `evidence_ref` 后续接 `scripts/evidence_crosscheck.py` 与 task record/route replay。 |

## 对应责任 Engineer

- `product-okr-owner`：本轮创建 sprint 规划文档并定义验收口径。
- `hardware-engineer`：下一阶段主责实现 HIL evidence packet gate、Docker-only 判定和 `tech-done.md`。
- `robot-software-engineer`：下一阶段只在 evidence metadata 与 task record/ROS topic sample contract 需要对齐时咨询。
- `autonomy-engineer`：下一阶段只在 route replay crosscheck 接口需要事实补充时咨询。
- `full-stack-software-engineer`：本轮不介入。

## 风险、阻塞和需要补齐的证据链

- 本机没有真实 WAVE ROVER/串口，无法产生真实 `hil_pass`。
- Docker registry mirror/proxy 阻塞仍可能影响完整 Humble 容器构建，但不阻塞纯文件/脚本级 gate 设计。
- 若 gate 未严格区分 `software_proof`、`blocked`、`hil_pass`，后续 OKR 仍可能被虚假证据污染。
- O2/O3 真实交叉 proof 仍等待同一 `evidence_ref` 的 HIL packet 与 route/task record 实跑样本。

## 需要创建或更新的 sprint 文档

- 本轮创建：`pre_start.md`
- 本轮创建：`prd.md`
- 本轮创建：`tech-plan.md`
- 下一阶段实现后必须更新：`tech-done.md`
- 验收或风险状态变化后更新：`side2side_check.md`、`final.md`
