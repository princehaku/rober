# Sprint 2026.05.09_22-23 PRD

## 产品目标

关闭 fixed route 送垃圾闭环的软件验收缺口：普通用户确认已装载垃圾后，行为层可以用 fixed-route dry-run 的状态结果完成 delivery mission，并把成功、失败、超时、取消写成机器可判定 action result 和 task record。

一句话：这轮先把“送垃圾闭环有没有证据”讲清楚，不开新功能战线。

## 文档阶段门禁

- 前置文档：`pre_start.md`。
- 前置 gate：上轮遗留、阻塞、owner、CEO 口径和 P0/P1 风险已列出。
- 当前阶段：PRD。
- 本阶段完成条件：OKR 映射、范围内/外、验收口径、依赖和失败处理口径明确。
- 下一文档：只有本阶段完成后，才允许创建或生效 `tech-plan.md`。

## OKR 映射

| OKR | 本轮映射 |
| --- | --- |
| Objective 1 硬件协议可信 | HIL 只做准入准备，硬件实机验证 deferred，不把静态证据写成上车通过 |
| Objective 2 送垃圾任务闭环 | action result 覆盖 success、failure、timeout、cancel，task record 可复盘 |
| Objective 3 导航与固定路线可验证 | fixed route status/dry-run 作为 delivery 主路径证据 |
| Objective 4 感知模块 | 视觉不作为本轮成功条件 |
| Objective 5 手机用户体验 | 冻结 `final_state`、`error_code`、`error_message`、`task_record_path` 等消费者字段 |

## 范围内

- fixed route delivery dry-run 结果路径验收。
- `TrashCollection.Result` 终态字段验收。
- task record 写入 target、delivery mode、navigation result、dropoff result、error code、final state。
- Docker Humble build P0 验证或阻塞根因记录。
- HIL 准入清单与 vendor 来源边界复核。
- 本轮 sprint 文档按 gate 留档。

## 范围外

- 不做完整手机 App。
- 不做机械臂、散落垃圾拾取、垃圾分类分拣。
- 不新增深度相机、昂贵传感器或多板卡默认方案。
- 不把 Nav2 waypoint 作为本轮主验收路径。
- 不声明 WAVE ROVER 实机 HIL 已通过。

## 用户故事

1. 作为普通手机用户，我触发送垃圾任务后，可以收到成功、失败、超时或取消的明确结果。
2. 作为远程/手机端消费者，我可以读取 `final_state`、`error_code`、`error_message` 和 `task_record_path` 判断任务终态。
3. 作为维护者，我可以从 task record 复盘 fixed route delivery 的目标、状态转移、导航结果、投放结果和失败原因。
4. 作为研发，我可以在没有实机的情况下用本地测试和 fixed-route dry-run 证明软件闭环。
5. 作为硬件调试者，我能拿到 HIL 准入清单，但不会把本轮文档误读成实机通过。

## 验收口径

| 编号 | 验收项 | Owner | 证据 |
| --- | --- | --- | --- |
| A1 | action result 覆盖 success、navigation_failed、timed_out、canceled | `robot-software-engineer` | 行为包测试 |
| A2 | task record 包含 `error_code`、`final_state` 和 fixed route 结果路径 | `robot-software-engineer` | task record 测试 |
| A3 | fixed route status reader 能识别 completed/failed/timeout | `autonomy-engineer` | behavior/nav 定向测试 |
| A4 | Docker Humble build 已尝试并记录 exit code | `robot-software-engineer` | Docker build 日志摘要 |
| A5 | HIL 准入清单 ready，实机验证 deferred | `hardware-engineer` | acceptance 文档/side2side |
| A6 | final 前 side2side 明确 closed/blocked/deferred，不用 partially mitigated 冒充完成 | `product-okr-owner` | `side2side_check.md` |

## 依赖与失败处理

- 本地验证依赖 `bash scripts/run_smoke_tests.sh`。
- Docker build 依赖当前 WSL 能调用 Docker；若不可用，必须记录命令、exit code 和环境提示，本轮 P0 状态为 blocked。
- HIL 依赖真实 WAVE ROVER 和 Orange Pi；本轮不要求实机，但必须保留后续上车证据字段。
- 若本地测试失败，必须先定位、修复、重跑，再进入 side-to-side。

## 本文件 Gate

- PRD 已锁定 fixed route 主路径、Docker P0、HIL 准入、手机/远程终态字段。
- 允许进入 `tech-plan.md`。
