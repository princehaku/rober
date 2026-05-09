# Sprint 2026.05.09_20-21 Pre Start

## 轮次定位

本轮主题：送垃圾闭环可信化。

目标不是继续堆新功能，而是把项目从“ROS2 包和文档已经有雏形”推进到“用户确认已装载垃圾后，机器人送达垃圾站/固定路线，并对成功、失败、取消、超时都产出可验证结果”。

## 已读依据

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `README.md`
- `scripts/run_smoke_tests.sh`
- `docs/acceptance/robot_bringup_checklist.md`
- `docs/acceptance/wave_rover_hil_evidence.md`
- `docs/hardware/wave_rover_json_bridge.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/product/mobile_user_flow.md`
- `docs/product/production_hardware_boundary.md`
- `src/` 当前包和测试分布

硬件事实采用 `docs/vendor/VENDOR_INDEX.md` 作为入口；本轮不新增未经 vendor 资料或上车验证支撑的引脚、电压、串口设备名、波特率、速度实测或机械尺寸结论。

## 上轮遗留与阻塞

| 类型 | 事项 | Owner | 状态 | 处理口径 |
| --- | --- | --- | --- | --- |
| 遗留 | 行为层需要证明真实送垃圾状态机，而不是 sleep/mock 式 demo | `p8-behavior-lead` | open | 本轮 P0 |
| 遗留 | WAVE ROVER 硬件桥需要继续保持 vendor 事实源一致，并区分静态测试与上车验证 | `p8-hardware-lead` | open | 本轮 P0 |
| 遗留 | fixed route / waypoint 输入输出要作为送达目标，而不是写死进度 | `p8-nav-lead` | open | 本轮 P0 |
| 遗留 | 手机用户流程要保持“一键发车、状态可见、异常接管”，不要求用户懂 ROS2/SSH/串口 | `p9-product-reviewer` | open | 本轮 P1 |
| 阻塞 | 当前机器是 WSL Ubuntu-24.04，不是目标 ROS2 Humble 环境 | `p8-bringup-integration-lead` | open | ROS2 build 优先 Docker Humble |
| 阻塞 | 真实串口设备名、T=13 运动表现、反馈字段仍需要上车确认 | `p8-hardware-lead` | open | 不写成已验证 |

## 本轮组织链路

CEO -> P9 -> P8 -> P7。

本轮流程固定为 `PRD -> DEV -> TEST`，不执行 TDD，不要求测试先行：

- PRD：P9/P8 先完成范围、验收口径、接口/风险拆解，并冻结 P7 handoff。
- DEV：PRD 通过后，`p7-tech-implementation-worker` 按 P8 handoff 做窄范围实现。
- TEST：DEV completion 后，`p7-tech-test-engineer`、`p7-tech-reviewer`、`p7-tech-docs-acceptance` 进入测试、审查和验收；涉及硬件事实时追加 `p7-tech-hardware-audit`。

文档阶段门禁：

- 顺序固定为 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`。
- 一个阶段完成并写清 gate 状态后，才允许创建下一个阶段文档，禁止预生成后续文档。
- 本文件 gate：上轮遗留、阻塞、owner、P0/P1 风险和组织链路已列出，允许进入 `prd.md`。
- 如果本轮目录中已有预创建的下游文件，在对应前置 gate 完成前只能视为 invalid draft，不得作为有效交付或收口证据。

| 层级 | 角色 | 本轮职责 |
| --- | --- | --- |
| P9 | `p9-architect` | 裁剪范围、OKR/KR 映射、验收口径 |
| P9 | `p9-product-reviewer` | 手机用户闭环、产品范围、非目标 |
| P8 | `p8-project-lead` | PMO、风险台账、里程碑、收口 |
| P8 | `p8-hardware-lead` | WAVE ROVER UART JSON、反馈、HIL 清单 |
| P8 | `p8-behavior-lead` | 送垃圾状态机、失败恢复、action result |
| P8 | `p8-nav-lead` | waypoint/fixed route 输入、dry-run、状态输出 |
| P8 | `p8-interfaces-contract-lead` | action/msg/srv 契约兼容 |
| P8 | `p8-bringup-integration-lead` | launch 参数、Docker Humble 构建口径 |
| P8 | `p8-vision-lead` | 感知契约和样本沉淀，不绑定捡垃圾成功标准 |
| P7 DEV | `p7-tech-implementation-worker` | PRD 通过后按 P8 handoff 做窄范围实现 |
| P7 TEST | `p7-tech-test-engineer` | DEV 完成后跑测试、smoke、dry-run、记录验证缺口 |
| P7 TEST | `p7-tech-hardware-audit` | 硬件相关改动在 TEST 阶段做事实来源审查 |
| P7 TEST | `p7-tech-reviewer` | DEV 完成后做代码/接口/文档一致性审查 |
| P7 TEST | `p7-tech-docs-acceptance` | TEST 阶段收口留档、验收清单、用户运行说明 |

## P0 风险

| 风险 | Owner | Gate |
| --- | --- | --- |
| 硬件协议、串口参数或速度映射没有 vendor/实测证据就进入默认行为 | `p8-hardware-lead` | vendor 引用 + HIL 待验证项明确 |
| 行为层仍是 mock/sleep 却宣称完成送垃圾闭环 | `p8-behavior-lead` | 状态机测试覆盖成功/失败/取消/超时 |
| route/waypoint 输入输出不稳定，导致自主阶段无法复现 | `p8-nav-lead` | route 格式文档 + dry-run 测试 |
| P0 未清零就写 final 完成 | `p8-project-lead` | `side2side_check.md` P0 表全部 closed |

## P1 风险

- `/odom` 来源与可信度边界仍需持续标注。
- 手机端流程已有产品文档，但最小状态/诊断数据契约仍需与行为层输出打通。
- 视觉模块容易被误拉回“自动捡垃圾”叙事，本轮只作为站点识别、异常记录和数据沉淀方向。
- WSL 静态测试、Docker Humble 构建、上车 HIL 三层验证边界必须在最终说明里拆开。

## 禁止事项

- 不做机械臂、自动抓取、散落垃圾拾取。
- 不新增昂贵传感器、深度相机、多板卡方案。
- 不硬编码 Orange Pi 串口设备名。
- 不把 `T=13` 宣称为最终 `/cmd_vel` 映射，除非完成上车验证。
- 不为了 ROS2 Humble 强行改造本机 Ubuntu-24.04。
- 不把静态测试冒充硬件验证。
