# Sprint 2026.05.11 03-04 HIL Reality Closure - PRD

## 状态

- 阶段：prd in progress
- 时间：2026-05-11 03:01 Asia/Shanghai
- Owner：`product-okr-owner`
- 产品目标：把“已完成的软件 dry-run 证据”升级为“可复现实车闭环证据”，优先补齐 O1 和 O2 的最短阻塞路径。

## 背景

`2026.05.11_02-03_elevator-assisted-delivery-dry-run` 已完成电梯 dry-run 骨架，且文档反复说明 dry-run 不等于真实能力。
当前 OKR 可得分高差异显示：`Objective 1` 约 75%，`Objective 2` 约 76%，`Objective 3` 约 76%，`Objective 4/5` 在 76~80%。

目标是让机器人回到“真实任务可跑、可复盘、可判定可否发版”的闭环状态。

## 本轮 KR 映射

- Objective 1：硬件协议可信底盘
  - KR1：新增可复现实车 HIL/HAL 证据清单与记录条目（含启动命令、反馈采样、速度指令映射的实测输出）。
  - KR2：把 `/odom` 与 `feedback` 的实测边界写入 sprint 证据（`command_integration` 与实测源不混淆）。
- Objective 2：送垃圾任务闭环
  - KR1：在 fixed-route/waypoint 路径上补齐失败恢复（超时、导航失败、路线缺失）证据字段，不再只依赖默认成功路径。
  - KR2：任务记录保留真实任务开始/中断/返回或错误分支与时间戳。
- Objective 3：可验证导航
  - KR1：让固定路线到达/返回的关键 checkpoint 与状态写入 task record 的可回放字段对齐。
  - KR2：形成一次最小 real route 复测清单。
- Objective 5：手机体验与量产边界
  - KR1：operator/status/diagnostics 在每次 HIL 与任务 run 后展示“模拟 vs 实机来源”与最近异常。

## 做什么（本轮边界）

1. 定义并落地 HIL 运行档口（脚本参数、输入输出和证据目录）。
2. 在行为层任务记录里补齐真实路测分支并保证与 operator 读取契约一致。
3. 在导航侧补齐 fixed-route 到达与失败状态的可复盘字段映射。
4. 对 `review` 命名覆盖问题做一次最小修复：要么补齐命名后的 `review` 测试，要么收敛验收命令。

## 不做

- 不把 `NO TESTS RAN` 这种围栏差距当作完成；不把 `test_*review*py` 作为“可选”而留空。
- 不扩展电梯场景视觉识别或楼层 OCR。
- 不在本轮扩大大量回归测试（保留围栏策略）。
- 不改动与本次目标无关的人机界面和硬件原理图。

## 优先级

- P0：HIL 证据产出、mission 主链失败恢复和 task record 可复盘。
- P1：navigation checkpoint 可复盘字段与 operator/hw proof 来源标注。
- P2：处理 review 命名覆盖策略并恢复命令可预期。

## 验收口径

1. HIL 证据能区分 dry-run 与实机实测。
2. 任务完成失败路径不会误判成功；有明确 `error_code` 和人工接管建议。
3. `task_record` 与 operator diagnostics 对应同一任务可追溯。
4. 围栏测试通过：目标 tests + `py_compile` + scoped `git diff --check`。

## 对应责任 Engineer

- `robot-software-engineer`：任务闭环与任务记录主链
- `hardware-engineer`：WAVE ROVER HIL/运行证据与 hardware/proof 分界
- `autonomy-engineer`：固定路线 / navigation 的可复盘字段与状态对齐
- `full-stack-software-engineer`：operator/status/diagnostics 的模拟/实机来源标注
