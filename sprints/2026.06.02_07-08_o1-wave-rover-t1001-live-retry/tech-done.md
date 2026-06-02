# 2026.06.02 07-08 O1 WAVE ROVER T1001 Live Retry

sprint_type: micro

## 目标

本轮 hourly automation 继续按 OKR 4.1 的最低 active Objective 推进 O1：硬件协议可信底盘。目标是在严格 fail-closed/no-motion 边界内，使用用户提供的上位机入口 `ssh root@192.168.1.11 -p 37878` 复采 WAVE ROVER feedback 证据，确认显式 vendor `{"T":130}\n` 后是否至少观察到一帧真实 `T=1001`。

固定安全边界：

- `safe_to_control=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- 严禁发送 `T=1`、`T=13`、`T=131`、`cmd_vel` 或任何运动命令。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/06 获取底盘反馈信息.ipynb` 与 `tutorial_en/06 Retrieving Chassis Feedback Information.ipynb`（通过全文检索确认 `T=1001` feedback 描述）
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/08 下位机 JSON 指令集.ipynb` 与 `tutorial_en/08 Microcontroller JSON Command Set.ipynb`（通过全文检索确认 `CMD_BASE_FEEDBACK` / `CMD_BASE_FEEDBACK_FLOW` 描述）

## 已证实的硬件结论

- vendor 资料确认 WAVE ROVER 上位机链路是 UART、UTF-8 JSON、每行一个 JSON 对象并以 `\n` 结束。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`，`FEEDBACK_BASE_INFO=1001`。
- `uart_ctrl.h` 中 `CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`；`ugv_advance.h` 中 `baseInfoFeedback()` 设置 `T=FEEDBACK_BASE_INFO` 并输出左右轮速度、IMU roll/pitch/yaw、电压和可选模块字段。
- `T=1` 是左右轮速度命令，`T=13` 是 ROS velocity 命令，`T=131` 会改变 feedback flow 状态；本轮没有发送这些命令。
- 本轮两条远端 SSH 命令均失败在网络层 `No route to host`，没有触达远端 Python、没有打开串口、没有机会发送 `T=130`，因此没有采到真实 `T=1001`。

## 实际改动

- 更新 `docs/hardware/o1_wave_rover_serial_feedback_probe.md`：追加 `2026.06.02_07-08` 复采结果、第三次同类 blocker 说明、安全边界和下一步处理口径。
- 新增 `sprints/2026.06.02_07-08_o1-wave-rover-t1001-live-retry/tech-done.md`：记录本轮 micro sprint 的 vendor 来源、验证结果、失败定位和剩余风险。

本轮没有修改 `onboard/scripts/o1_wave_rover_serial_feedback_probe.py`、测试文件、运动控制逻辑、launch 默认值、factory firmware、PC/mobile/cloud 代码或无关 sprint。

## 验证结果

### 1. probe 单元测试

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_o1_wave_rover_serial_feedback_probe.py'
```

结果：

```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.236s

OK
```

### 2. probe py_compile

```bash
python3 -m py_compile onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果：通过，无输出。

### 3. 远端只读 probe

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

结论：SSH 网络层失败，未触达远端 Python，未打开串口，未读取串口行。

### 4. 远端显式非运动 feedback request

```bash
timeout 35 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 12' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
```

结果：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

结论：SSH 网络层失败，未触达远端 Python，未打开串口，未发送 `{"T":130}\n`，未读取到 `T=1001`。

### 5. scoped diff check

```bash
git diff --check -- docs/hardware/o1_wave_rover_serial_feedback_probe.md sprints/2026.06.02_07-08_o1-wave-rover-t1001-live-retry/tech-done.md onboard/scripts/o1_wave_rover_serial_feedback_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py
```

结果：通过，无输出。

## 失败定位

本轮 blocker 是 `remote_network_unreachable` / `ssh_no_route_to_host`。它发生在 SSH 建连阶段，不是 pyserial 缺失、串口打开失败、`T=130` 写失败、串口无反馈或 WAVE ROVER 固件无 `T=1001` 的证据。

机器可读结论：

```yaml
remote_probe_status: ssh_no_route_to_host
t130_request_reached_serial: false
t1001_observed: false
safe_to_control: false
sends_motion_commands: false
robot_control_executed: false
delivery_success: false
evidence_boundary: remote_network_unreachable_not_serial_feedback_result
```

## 第三次同类 blocker 处理

这是第三次同类 `remote_network_unreachable` / `ssh_no_route_to_host` blocker 消费：

- `2026.06.01_20-21_o1-t130-feedback-observation`：SSH `No route to host`，未触达远端 Python。
- `2026.06.02_06-07_o1-wave-rover-t1001-live-retry`：SSH `No route to host`，未触达远端 Python。
- `2026.06.02_07-08_o1-wave-rover-t1001-live-retry`：SSH `No route to host`，未触达远端 Python。

按项目 blocker 红线，从下一轮开始不能继续把同一 SSH/路由不可达问题当作 O1 完成材料消费。必须二选一：

1. 切换 Objective：放弃当前网络 blocker，转去做不依赖 `192.168.1.11:37878` 的低完成度 Objective。
2. 升级 CEO 现场处理或决策：确认上位机开机、同网段路由、SSH 端口映射、WiFi/4G/VPN 或现场网络策略。

## 剩余风险与下一步履约动作

- 真实 `T=1001` 仍为 `not_proven`，O1 不允许提升进度，不能写成 HIL pass。
- 需要现场确认 `192.168.1.11` 开机、网络可路由、37878 SSH 映射仍有效。
- SSH 恢复后，先跑只读 probe 确认目标 by-id 设备仍存在；再跑一次显式 `--request-base-feedback`。
- 若 SSH 恢复且 `T=130` 可写入但仍无串口行，按 probe `next_required_checks[]` 检查 ESP32 供电/固件、TX/RX 交叉、目标端口是否为 WAVE ROVER ESP32、串口占用和 vendor terminal 交叉验证。
