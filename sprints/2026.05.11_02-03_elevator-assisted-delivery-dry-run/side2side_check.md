# Sprint 2026.05.11 02-03 Elevator Assisted Delivery Dry Run - Side2Side Check

## 状态

- 阶段：side2side_check completed。
- 时间：2026-05-11 Asia/Shanghai。
- Owner：`product-okr-owner`。
- 对照对象：`prd.md`、`tech-plan.md`、工程 agent 结果摘要和 `tech-done.md`。

## 用户价值和产品北极星

北极星仍是普通手机用户把垃圾交给低成本 ROS2 小车后，小车能完成受控路线送达、异常解释和人工接管。本轮没有把电梯能力宣称为实机跨楼层完成，而是把 H2 elevator assisted delivery 先做成默认关闭、可演练、可复盘的软件 dry-run 骨架。

本轮用户价值成立在三个软件证据上：

- 用户触点能解释小车处于等待电梯、请求帮忙按楼层、等待目标楼层、需要人工接管等状态。
- task record 和 diagnostics 能留下 `elevator_assist` 状态、失败原因和 evidence，后续可复盘。
- 默认关闭，不影响当前单楼层送垃圾 MVP 主链路。

## OKR 映射

- Objective 2 / KR6：已推进 elevator assisted delivery 状态链路的软件 dry-run 骨架，但不代表真实电梯完成。
- Objective 4 / KR6：已补齐保守的电梯场景 dry-run evidence schema，包括门、轿厢、目标楼层和驶出条件字段；没有真实相机门识别或楼层 OCR。
- Objective 5 / KR6：已补齐手机/diagnostics/speaker prompt contract，用户可读状态更清晰；没有真实 TTS/喇叭播放验证。

## KR 拆解验收

| KR 抓手 | 验收判断 | 证据 |
| --- | --- | --- |
| KR2.6-A 行为层默认关闭 dry-run 子流程 | 通过 | Robot targeted `Ran 29 tests ... OK`；launch 参数默认关闭；未改 ROS2 action/msg/srv。 |
| KR2.6-B task record 记录状态和失败原因 | 通过 | `task_record` 新增 `elevator_assist`，包含 enabled/mode/state/phase/reason/evidence/events。 |
| KR5.6-A operator/status 输出 phone copy 和 speaker prompt | 通过 | Full-stack targeted `Ran 53 tests ... OK`；请求按楼层 prompt 保持 `你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,`。 |
| KR5.6-B diagnostics 展示机器可读 elevator dry-run 状态 | 通过 | operator diagnostics 可消费 task record/latest status 的 `elevator_assist`。 |
| KR4.6-A dry-run evidence schema | 通过 | Autonomy targeted `Ran 19 tests ... OK`；schema 覆盖 `door_open`、`door_closed_or_unknown`、`inside_elevator`、`target_floor_confirmed`、`target_floor_unconfirmed`、`safe_to_exit`、`unsafe_to_exit`。 |

## 做什么 / 不做什么

做了：

- 默认关闭的 `elevator_assist` dry-run 行为骨架。
- task record、operator status/diagnostics、nav evidence schema 的兼容扩展。
- targeted tests、py_compile 和 scoped diff check 围栏。

没有做，也不能被解读为完成：

- 没有实机电梯验证。
- 没有真实 TTS/喇叭播放。
- 没有相机门识别、目标楼层 OCR 或楼层到达实证。
- 没有 Nav2/fixed-route 上车实跑。
- 没有硬件在环 HIL 或 WAVE ROVER/Orange Pi 实机验证。

## 优先级和验收口径

P0 验收结论：通过软件 dry-run 收口。默认关闭、完整状态链、失败可解释、task record 可复盘、operator/diagnostics 可解释均有 targeted 测试证据。

P1/P2 仍未完成：真实受控路线、真实电梯、真实相机/TTS/HIL 证据仍是后续 sprint 风险。

## 对应责任 Engineer

- `robot-software-engineer`：行为 dry-run、task record、launch 默认关闭、主责验证。
- `full-stack-software-engineer`：operator status/diagnostics、手机文案、speaker prompt contract。
- `autonomy-engineer`：elevator dry-run evidence schema 和 visual gate 保守证据输出。
- `hardware-engineer`：本轮未介入；没有硬件事实变更。

## 风险、阻塞和证据链缺口

- 真实电梯、真实 TTS、相机门识别、楼层 OCR、Nav2/fixed-route 实跑、HIL 全部未完成。
- dry-run 的 `target_floor_unconfirmed` 是保守安全口径，不是目标楼层识别能力。
- `.codex/config.toml` 有无关未提交改动，未纳入本轮成果或 OKR 证据。
- 后续进入硬件、电梯实景或机械安装任务时，必须先查 `docs/vendor/VENDOR_INDEX.md` 和相关本地 vendor 文件。

## 需要创建或更新的 sprint 文档

- 已更新：`tech-done.md`。
- 本文件完成：`side2side_check.md`。
- 下一步收口：`final.md` 和 `OKR.md` 的保守进度快照。
