# O1 Feedback Request Probe Tech Done

## Sprint 类型

sprint_type: micro

## 目标

在上一轮只读串口 probe 已确认 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0` 可打开、但短窗口无被动反馈行的基础上，本轮新增显式、一次性的非运动反馈请求能力：只允许发送 vendor `CMD_BASE_FEEDBACK` / `{"T":130}`，随后读取短窗口反馈，尝试采集 `T=1001` 或其他反馈类型。

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

## 已证实硬件结论

- WAVE ROVER vendor reference 使用 UART、UTF-8 JSON、newline-delimited framing。
- vendor Raspberry Pi reference baudrate 为 `115200`；Orange Pi 真实 port 仍必须由目标机枚举确认，不能硬编码 Raspberry Pi 路径。
- `CMD_BASE_FEEDBACK` 对应 `{"T":130}`，firmware `uart_ctrl.h` 中分支调用 `baseInfoFeedback()`。
- `T=1`、`T=13`、`T=131` 分别涉及轮速/ROS velocity/feedback flow 状态，本轮继续禁止发送。

## 实际改动

- `onboard/scripts/o1_wave_rover_serial_feedback_probe.py`
  - 保持默认 read-only 行为。
  - 新增 `--request-base-feedback`，显式启用后只发送一次 compact JSON `{"T":130}\n`。
  - 输出新增 `sends_motion_commands=false` 与 `feedback_request` 结构化字段。
  - 显式请求模式的证据边界标记为 `serial_open_t130_feedback_request_not_hil`。
- `onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py`
  - 更新默认不写串口测试。
  - 新增显式请求只写一次 `T=130` 的回归测试。
  - 保持运动命令、`cmd_vel`、`T=131` blocked contract。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 更新默认只读与显式 `T=130` 请求两种模式。
  - 写明该能力不是 HIL pass，也不是底盘可控证据。

## 验证结果

- `python3 -m py_compile onboard/scripts/o1_wave_rover_serial_feedback_probe.py`
  - 结果：通过，exit 0，无输出。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py`
  - 结果：通过，`Ran 7 tests in 0.167s`，`OK`。
- `git diff --check -- onboard/scripts/o1_wave_rover_serial_feedback_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py docs/hardware/o1_wave_rover_serial_feedback_probe.md sprints/2026.06.01_19-20_o1-feedback-request-probe/tech-done.md`
  - 结果：通过，exit 0，无输出。
- 中文技术注释比例检查：
  - `onboard/scripts/o1_wave_rover_serial_feedback_probe.py total_lines=254 chinese_comment_lines=57 ratio=22.4%`
  - `onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py total_lines=184 chinese_comment_lines=41 ratio=22.3%`

## 远端 SSH / 串口 probe

已尝试运行显式非运动反馈请求 probe：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果：失败，SSH 不可达，未触达远端串口，未发送任何串口命令。

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

## Product Closeout

用户价值：本轮把 O1 的下一步硬件验证从“等被动反馈”推进到“可显式请求一次 vendor base feedback”，并且保持默认 read-only、不发运动命令。该能力让后续 Hardware Engineer 可以在 SSH/网络恢复后，用同一 by-id 串口安全采集 `T=130` 请求后的反馈材料。

产品北极星：仍服务于“普通手机用户交垃圾后，小车可验证地送到垃圾站/桶点位并返回”的底盘可信层。没有真实 `T=1001` feedback 和受控 HIL 前，不把本轮解释成用户可用的底盘能力。

OKR 映射和方向判断：映射 Objective 1「打通官方硬件协议，建立可信底盘控制层」。方向判断为**继续**，不调整、不暂停、不替换；本轮只关闭“Feedback Request 软件入口 ready”的缺口，不关闭真实 feedback、真实 UART/HIL、真实底盘控制或送达闭环缺口。

KR 拆解和进度判断：O1 继续保持约 93%，不调百分比。口径更新为 `software_reference + upper-computer serial-open observed + feedback request entry ready; remote not reached; T=1001 not_proven`。KR1/KR3/KR4 受益于显式 `T=130` request contract 和回归测试，但真实 `T=1001` 反馈解析仍没有远端材料支撑，不能归档为完成 KR。

本轮核心抓手：把 `--request-base-feedback` 作为受控、显式、一次性、非运动的 feedback request 入口，并用本地 py_compile、unittest、diff-check 和中文注释比例证明软件侧 contract。

需要做什么：下一轮先恢复 `ssh root@192.168.1.11 -p 37878` 网络可达性，再对 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00` 执行显式 `--request-base-feedback`，采集是否出现 `T=1001` 或其他 vendor feedback。若仍无反馈，需要记录电源、线缆、串口归属、固件状态和 WAVE ROVER feedback 配置。

优先级和验收口径：P0 是远端可达性与一次真实 `T=130` request 后的机器可读 JSON artifact；验收必须包含 `feedback_request.sent=true`、`sends_motion_commands=false`、`robot_control_executed=false`、原始/脱敏串口行计数、`observed_feedback_types`，并明确是否观测到 `T=1001`。即使观测到 `T=1001`，也只能记为 feedback material observed，不能直接升级为底盘可控或 HIL pass。

对应责任 Engineer：Hardware Infra Engineer 继续主责远端 SSH/串口/WAVE ROVER feedback probe；Robot Software Engineer 只在后续需要把真实 feedback 接入 ROS2 runtime、IMU/battery/odom 语义和测试时介入。

风险、阻塞和证据链缺口：当前阻塞是远端 SSH `No route to host`，导致真实串口未触达、远端 `T=130` 未发送、`T=1001` feedback 未证明。剩余缺口包括真实 WAVE ROVER feedback、真实底盘控制、真实 UART/HIL、ROS Humble runtime、IMU/battery/odom 标定、TF、Nav2/SLAM、真实 LiDAR `/scan` 和 PR #5 硬件材料。

已完成 KR 历史记录：本轮没有已完成 KR 需要移入历史归档区；O1 KR 仍留在当前推进区。历史记录位置为 `docs/process/okr_progress_log.md` 的 `2026-06-01 19-20｜o1-feedback-request-probe` 小节、`OKR.md` 第 4/4.1/5 节和本文件。

需要创建或更新的 sprint 文档：本 micro sprint 只需更新本 `tech-done.md`；同步更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。无需创建 `pre_start.md`、`prd.md`、`tech-plan.md`、`side2side_check.md` 或 `final.md`。

## 剩余风险

- 即使读到 `T=1001`，仍只证明一次 `T=130` 查询后观察到反馈，不证明底盘运动控制、IMU/battery 标定、odom 或完整 HIL pass。
- 本轮不发送 `T=1`、`T=13`、`T=131`、`/cmd_vel`、速度或转向命令。
- 本轮远端 SSH 不可达，真实 WAVE ROVER `T=1001` feedback 仍为 `not_proven`。
