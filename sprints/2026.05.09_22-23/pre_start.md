# Sprint 2026.05.09_22-23 Pre Start

## 轮次定位

本轮主题：Fixed Route 送垃圾闭环验收清零。

本轮不是扩功能 sprint，而是关闭上一轮 `sprints/2026.05.09_20-21/` 未清零 P0。主路径固定为：

`fixed route delivery dry-run -> action result -> task record -> side2side P0 清零`

## 已读依据

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.05.09_20-21/pre_start.md`
- `sprints/2026.05.09_20-21/prd.md`
- `sprints/2026.05.09_20-21/tech-plan.md`
- `sprints/2026.05.09_20-21/tech-done.md`
- `sprints/2026.05.09_20-21/side2side_check.md`
- `sprints/2026.05.09_20-21/final.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/acceptance/wave_rover_hil_evidence.md`
- `scripts/run_smoke_tests.sh`
- `scripts/docker_humble_build.sh`
- `src/ros2_trashbot_behavior/`
- `src/ros2_trashbot_nav/`

硬件事实入口采用 `docs/vendor/VENDOR_INDEX.md`。本轮 HIL 只做准入准备，不声明 WAVE ROVER 实机验证通过；任何串口、波特率、命令 ID、速度映射、反馈字段、引脚、电压或机械尺寸结论仍必须继续引用 vendor 本地资料和实测证据。

## CEO 口径

| 决策 | 本轮口径 |
| --- | --- |
| Docker Humble build | P0 gate，必须尝试并记录结果 |
| HIL | 只做准入准备，不关闭实机验证 |
| delivery 主路径 | fixed route 优先，Nav2 waypoint 降为 P1/后续 |
| 手机端 | 不做完整 App，只冻结状态、错误码、诊断契约 |
| 视觉 | 不作为送达成功前提 |

## 上轮遗留与阻塞

| 类型 | 事项 | Owner | 本轮处理 |
| --- | --- | --- | --- |
| P0 | 行为层 action execution result tests 仍 open | `robot-software-engineer` | 覆盖 success、navigation_failed、timed_out、canceled 的终态字段 |
| P0 | fixed route delivery 结果路径与文档一致性仍 open | `autonomy-engineer` | 用 fixed-route status reader、dry-run status 和文档命令对齐 |
| P0 | Docker Humble build 上轮 blocked | `robot-software-engineer` | 本轮作为 P0 重跑；不可用则记录阻塞根因 |
| P0 | HIL 缺少实机证据 | `hardware-engineer` | 本轮只关闭准入清单，不声明实机通过 |
| P1 | 手机/远程消费者需要机器可判定终态 | `full-stack-software-engineer` | 保持 `final_state`、`error_code`、`error_message` 可消费 |

## 本轮组织链路

CEO -> Product Manager / OKR Owner -> Engineers。

| 类型 | 角色 | 本轮职责 |
| --- | --- | --- |
| Product | `product-okr-owner` | 确认只收敛送垃圾闭环，不扩功能；阶段 gate、P0 清零、证据整合 |
| Engineer | `robot-software-engineer` | action result、状态机、task record、Docker Humble build P0 |
| Engineer | `autonomy-engineer` | fixed route delivery dry-run 结果路径 |
| Engineer | `full-stack-software-engineer` | 手机/远程终态字段契约 |
| Engineer | `hardware-engineer` | HIL 准入清单和 vendor 来源边界 |

## P0 风险

| P0 | Owner | Gate |
| --- | --- | --- |
| action result 不能机器判定 success/failure/timeout/cancel | `robot-software-engineer` | 结果字段和 task record 测试通过 |
| fixed route delivery 只停留在文档，没有离线结果路径证据 | `autonomy-engineer` | dry-run/status reader 测试通过 |
| Docker Humble build 不能证明接口/action/msg 生成 | `robot-software-engineer` | Docker build 通过；或 P0 blocked 记录根因 |
| HIL 准入资料不完整却宣称硬件完成 | `hardware-engineer` | HIL checklist ready，实机验证明确 deferred |
| P0 未清零就 final | `product-okr-owner` | `side2side_check.md` 明确区分 closed、blocked、deferred |

## 本文件 Gate

- 上轮未完成项、阻塞、owner 已继承。
- CEO 口径已记录。
- P0/P1 风险和组织链路已列出。
- 允许进入 `prd.md`。

禁止预生成后续阶段文档；只有前置 gate 完成并写清状态后，下一阶段文档才生效。
