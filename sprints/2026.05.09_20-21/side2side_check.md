# Sprint 2026.05.09_20-21 Side To Side Check

## 文档阶段门禁

- 前置文档：`tech-done.md`。
- 前置 gate：DEV completion、实际改动、验证输出、失败定位和剩余风险已记录。
- 当前阶段：SIDE TO SIDE CHECK。
- 本阶段完成条件：完成 PRD vs 实现、OKR/KR、接口、文档、测试和 P0 风险对照，且 P0 全部 closed。
- 下一文档：只有本阶段完成且 P0 全部 closed 后，才允许创建或生效 `final.md`。
- 如果本文件早于 tech-done gate 被预创建，则在 gate 完成前只能视为 invalid draft。

## PRD vs 实现

| PRD 项 | 实现状态 | 证据 | 结论 |
| --- | --- | --- | --- |
| 用户确认装载后一键发车 | implemented, acceptance open | `operator_gateway.py`, `remote_bridge.py`; 仍需 action execution result tests | open |
| 送达垃圾站/固定路线 | implemented, verification open | `delivery_navigation.py`, fixed-route status reader, nav tests; Docker/HIL 未跑 | open |
| 成功/失败/取消/超时结果明确 | improved this sprint | `DeliveryEvent.TIMED_OUT`, `error_code`, `final_state`, static tests | open |
| 任务记录可复盘 | existing implementation present | `task_record.py`, `test_task_record.py`; 仍需 end-to-end action result record tests | open |
| 硬件事实源可追溯 | in progress | `docs/vendor/VENDOR_INDEX.md` 已读；README/docs 已修正部分边界 | open |

## OKR/KR 对照

| OKR | 本轮检查点 | 状态 |
| --- | --- | --- |
| Objective 1 | WAVE ROVER UART JSON、反馈、参数边界 | open |
| Objective 2 | 送垃圾状态机与失败恢复 | implemented, acceptance open |
| Objective 3 | fixed route/waypoint dry-run | implemented, verification open |
| Objective 4 | 视觉不绑定捡垃圾成功标准 | in progress |
| Objective 5 | 手机用户最小流程和异常接管 | in progress |

## 接口生产者/消费者矩阵

| 接口 | Producer | Consumer | 本轮关注 |
| --- | --- | --- | --- |
| `/cmd_vel` | nav/behavior | hardware bridge | 映射路径和停止路径不可写死未验证结论 |
| `TrashCollection.action` | behavior | 手机/远程入口/测试 | result 和 feedback 能表达失败原因 |
| route CSV/YAML | nav recorder/converter | fixed route autonomy/behavior | 格式稳定、dry-run 可测 |
| task record | behavior | debug/远程诊断/验收 | 可复盘任务过程 |
| `TrashStatus.msg` | vision | behavior/debug | 不作为本轮送达成功硬依赖 |

## 文档 vs 真实行为

| 文档 | 检查点 | 状态 |
| --- | --- | --- |
| `README.md` | 串口协议是否指向 WAVE ROVER UART JSON；是否区分上车验证 | updated this sprint |
| `docs/hardware/wave_rover_json_bridge.md` | 是否标明 vendor 来源和 HIL 证据 | updated this sprint |
| `docs/navigation/fixed_route_workflow.md` | route/dry-run 命令是否与代码一致 | pending |
| `docs/product/mobile_user_flow.md` | 是否保持手机用户、送垃圾、不捡垃圾 | pending |
| `docs/acceptance/robot_bringup_checklist.md` | 是否区分本地、Docker、HIL 验证 | pending |

## 验证边界

- Desktop unittest smoke 只能证明 Python 语法和包内静态/逻辑测试，不是 launch/runtime 证明。
- Docker Humble build 只能证明 ROS2 Humble 构建，不是机器人上车证明。
- fixed-route dry-run 只能证明路线解析和离线状态输出，不是定位/Nav2 证明。
- behavior dry-run 只能证明任务入口和 dry-run 契约，不是 waypoint 实机送达证明。
- interfaces 当前没有 Python `test/` 目录，msg/action 生成依赖 colcon build 证据。

## 硬件事实引用检查

已采用入口：

- `docs/vendor/VENDOR_INDEX.md`

后续硬件实现或结论必须按需要继续打开并引用：

- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf`
- `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`

## P0 清零表

| P0 | Owner | Gate | 状态 |
| --- | --- | --- | --- |
| 硬件默认行为没有 vendor/实测证据 | `p8-hardware-lead` | vendor 引用 + HIL 待验证记录 | open |
| 行为层仍是 mock/sleep 却宣称完成 | `p8-behavior-lead` | 状态机测试 | partially mitigated: delivery path has state machine; patrol demo remains separate |
| route/waypoint 输入输出不可 dry-run | `p8-nav-lead` | route dry-run 测试 | partially mitigated: existing tests pass; Docker/HIL still open |
| P0 未清零就 final | `p8-project-lead` | 本表全部 closed | open |

## 本轮启动验证

| 检查 | 结果 | 说明 |
| --- | --- | --- |
| shell 脚本可执行性 | passed | `run_smoke_tests.sh` 和 `docker_humble_build.sh` 已由 CRLF 转为 LF |
| 本地 smoke | passed | `bash scripts/run_smoke_tests.sh` exit 0 |
| interfaces Python tests | skipped | `ros2_trashbot_interfaces` 无 Python `test/` 目录，需 colcon build 验证 msg/action 生成 |
| Docker Humble build | blocked | `docker --version` exit 1；当前 WSL 2 distro 找不到 Docker |
| HIL | pending | 需要实机，不用本地测试冒充 |
