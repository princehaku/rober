# Sprint 2026.05.09_20-21 PRD

## 产品目标

本轮建立“用户交付垃圾后的最小送达闭环”：普通手机用户确认已把垃圾放到小车上后，机器人按已配置垃圾站 waypoint 或 fixed route 执行送达，到站后投放/提醒人工取走，并在成功、失败、取消、超时情况下给出明确状态、结果和可复盘记录。

一句话：先让小车可证明地去送垃圾，不急着让它看起来很聪明。

## OKR 映射

| OKR | 本轮映射 |
| --- | --- |
| Objective 1 硬件协议可信 | 保持 WAVE ROVER UART newline-delimited JSON 事实源一致，串口设备名/速度映射/反馈字段不写死未验证结论 |
| Objective 2 送垃圾任务闭环 | 围绕 `IDLE -> LOADED -> DELIVERING -> DROPOFF -> RETURNING -> IDLE/ERROR` 固化行为状态和失败结果 |
| Objective 3 导航与固定路线可验证 | waypoint/fixed route 作为送达目标输入，支持无硬件 dry-run 验证 |
| Objective 4 感知模块 | 摄像头只作为站点识别、异常记录、样本沉淀方向，不作为本轮任务成功前提 |
| Objective 5 手机用户体验与量产边界 | 保持一键发车、状态查看、异常接管，默认低成本硬件边界 |

## 用户故事

1. 作为普通用户，我可以用手机确认“垃圾已放入”，然后一键发车，不需要理解 ROS2、SSH 或串口。
2. 作为普通用户，我可以看到小车正在去垃圾站、已到站、返回中或失败待接管。
3. 作为维护者，我可以从任务记录里看到目标、状态变化、失败原因、导航结果和关键证据。
4. 作为开发者，我可以在没有硬件时用静态测试和 dry-run 验证 route/waypoint 与状态机逻辑。
5. 作为硬件调试者，我可以清楚区分 vendor 资料结论、自动化测试结论和真实上车 HIL 结论。

## 范围内

- 行为层送垃圾状态机和 action result 语义。
- 送达目标输入：garbage station waypoint 或 fixed route。
- 成功、失败、取消、超时路径的结果与错误信息。
- 任务记录字段：开始/结束时间、目标、状态转移、失败原因、导航结果、证据引用。
- 硬件桥事实源审查：WAVE ROVER UART JSON、反馈流、可配置串口参数。
- dry-run 和 smoke gate 留档。
- 手机端最小流程与状态字段定义，不做完整 UI。

## 范围外

- 机械臂、自动抓取、散落垃圾拾取。
- 把视觉垃圾检测作为任务成功标准。
- 新增昂贵传感器、深度相机或多板卡架构。
- 完整商业化手机 App。
- 未上车验证就固定 Orange Pi 串口设备名或宣称 `T=13` 是最终控制路径。

## 验收口径

| 编号 | 验收项 | Owner | 证据 |
| --- | --- | --- | --- |
| A1 | PRD 明确“送垃圾”而不是“捡垃圾” | `p9-product-reviewer` | 本文件 |
| A2 | 行为状态机覆盖成功/失败/取消/超时 | `p8-behavior-lead` | 单元测试 + `tech-done.md` |
| A3 | route/waypoint 输入能 dry-run 验证 | `p8-nav-lead` | route 测试 + dry-run 记录 |
| A4 | 硬件事实引用 vendor index，不新增未验证结论 | `p8-hardware-lead` | `side2side_check.md` |
| A5 | smoke gate 可运行或明确失败根因 | `p7-tech-test-engineer` | 命令输出摘要 |
| A6 | P0 全部关闭后才 final | `p8-project-lead` | `side2side_check.md` |

## 估时与里程碑

- M0：建立 sprint 留档和 P0/P1 风险台账。
- M1：完成 PRD 与 P9/P8 对齐。
- M2：完成 tech-plan，拆清行为、导航、硬件、接口、bringup、文档验证。
- M3：P7 执行实现与测试，失败必须定位后重跑。
- M4：side2side 对照，P0 清零。
- M5：final 收口，记录 OKR 推进和下轮 backlog。

## 依赖

- 本地静态验证：`scripts/run_smoke_tests.sh`。
- ROS2 构建验证：Docker Humble 挂载仓库到 `/ws` 后执行 `colcon build --symlink-install`。
- 硬件验证：WAVE ROVER + Orange Pi 实机串口、反馈、停止路径；证据记录到 `docs/acceptance/wave_rover_hil_evidence.md` 或本轮 sprint 证据区。
