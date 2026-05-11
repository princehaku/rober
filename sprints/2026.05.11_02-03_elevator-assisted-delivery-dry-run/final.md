# Sprint 2026.05.11 02-03 Elevator Assisted Delivery Dry Run - Final

## 状态

- 阶段：final completed。
- 时间：2026-05-11 Asia/Shanghai。
- Owner：`product-okr-owner`。
- 收口结论：本轮作为软件 dry-run 能力完成；不作为实机电梯、硬件、相机、TTS 或 Nav2 上车闭环完成。

## 用户价值和产品北极星

本轮把 H2 elevator assisted delivery 从产品描述推进到可验证的软件骨架：普通手机用户未来能看到电梯段状态和人工协助原因，工程侧能在 task record 和 diagnostics 中复盘每个电梯子阶段。它服务于“低成本 ROS2 自主垃圾投递机器人”的北极星，但仍是默认关闭的受控场景能力，不改变当前 MVP 主链路。

## OKR 映射

- Objective 2：推进 KR6，送垃圾任务闭环开始具备电梯 assisted delivery 子状态 dry-run 和失败路径记录。
- Objective 4：推进 KR6，补齐电梯场景感知 evidence schema，但只到离线/dry-run contract。
- Objective 5：推进 KR6，手机/diagnostics/speaker prompt contract 能解释电梯段状态和人工接管边界。

## KR 拆解或更新

- KR2.6：从“产品 contract”推进到“默认关闭的软件 dry-run 骨架，有 targeted 测试和 task record 证据”。
- KR4.6：从“待定义电梯感知 contract”推进到“保守 evidence schema 已进入 nav/visual gate 输出”。
- KR5.6：从“跨楼层体验文案”推进到“operator status/diagnostics 可消费的字段和 speaker prompt contract”。

## 本轮核心抓手

- 默认关闭，避免污染现有单楼层送垃圾主链路。
- 用 task record/status/diagnostics 承载状态和证据，不改 ROS2 action/msg/srv。
- 只用 targeted tests、py_compile、scoped diff check 作为功能围栏，避免把本轮变成大面积测试堆叠。

## 做什么 / 不做什么

完成：

- `elevator_assist` dry-run 行为骨架。
- 电梯子状态 task record。
- operator status/diagnostics 字段和用户可读文案。
- nav evidence schema 和 visual gate 保守输出。
- sprint 留档链路：`tech-done.md`、`side2side_check.md`、`final.md`。

未完成：

- 实机电梯、真实 TTS、相机门识别、楼层 OCR、Nav2/fixed-route 实跑、HIL。
- 真实用户用手机完成跨楼层送垃圾验收。
- 电梯门/目标楼层/驶出安全证据的现场数据采集。

## 优先级和验收口径

本轮 P0 通过：软件 dry-run 的默认关闭、状态链、失败路径、task record、operator/diagnostics 和 evidence schema 均有 targeted 验证结果。

后续 P1/P2：必须进入受控路线实测，先收集真实电梯门、目标楼层、驶出路径和用户接管证据，再谈进度提升。

## 对应责任 Engineer

- `robot-software-engineer`：主责完成 Robot targeted `Ran 29 tests ... OK`，py_compile 和 scoped diff check 通过。
- `full-stack-software-engineer`：协作完成 Full-stack targeted `Ran 53 tests ... OK`，py_compile 和 scoped diff check 通过。
- `autonomy-engineer`：协作完成 Autonomy targeted `Ran 19 tests ... OK`，py_compile 和 scoped diff check 通过。
- `hardware-engineer`：本轮无硬件改动，无需记录硬件成果。

## 风险、阻塞和证据链

- dry-run 通过不等于真实电梯能力完成。
- 当前 evidence schema 是保守 contract，不是相机识别或 OCR 结果。
- speaker prompt 是字段 contract，不是 TTS/喇叭播放验证。
- 真实 fixed-route/Nav2、相机、HIL 和电梯场景仍缺实测证据。
- `.codex/config.toml` 有无关未提交改动，未纳入本轮成果。

## OKR 更新建议

可保守更新 `OKR.md` 当前快照：

- Objective 2：从约 74% 上调到约 76%，理由是 KR6 有默认关闭软件 dry-run、task record 和 targeted 验证；不再上调，因为缺实机和 Nav2/fixed-route 实跑。
- Objective 4：从约 75% 上调到约 76%，理由是电梯场景 evidence schema 完成软件 contract；不再上调，因为缺真实相机门识别和楼层 OCR。
- Objective 5：从约 79% 上调到约 80%，理由是手机/diagnostics/speaker prompt contract 能解释电梯段；不再上调，因为缺真实 TTS、普通用户验收和跨楼层实机体验。

## 最终判断

本轮功能前进成立，但只能按软件 dry-run 收口。下一轮最有价值的抓手不是继续扩大字段，而是做受控现场证据：路线样例、相机样本、speaker/TTS 播放验证、Nav2/fixed-route 实跑和 HIL。
