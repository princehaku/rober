# O1 T=130 Feedback Observation Tech Done

## sprint_type

micro

## 实际改动

- 更新 `docs/hardware/o1_wave_rover_serial_feedback_probe.md`：补充本轮 `2026.06.01_20-21_o1-t130-feedback-observation` 的远端 SSH / T=130 观察结果和证据边界。
- 创建 `sprints/2026.06.01_20-21_o1-t130-feedback-observation/tech-done.md`：记录本轮 micro sprint 的 vendor 来源、验证命令、远端失败定位和剩余风险。
- 未修改 `onboard/scripts/o1_wave_rover_serial_feedback_probe.py` 和 `onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py`；现有脚本已满足本轮只允许显式发送一次 vendor `{"T":130}\n` 的边界。
- 未更新 `OKR.md`，OKR closeout 交给 Product / OKR Owner。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/08 下位机 JSON 指令集.ipynb` grep 命中 `{"T":130}`

## 已证实的硬件结论

- WAVE ROVER vendor firmware 定义 `CMD_BASE_FEEDBACK` 为 `T=130`，`json_cmd.h` 示例为 `{"T":130}`。
- `uart_ctrl.h` 中 `CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`。
- vendor 上位机 reference 使用 UART + UTF-8 JSON + newline framing，`115200` 是 vendor Raspberry Pi reference baudrate；Orange Pi 真实设备名仍必须以上车枚举和打开结果为准。
- `T=1`、`T=13`、`T=131`、`cmd_vel` 均不是本轮允许命令；本轮未发送任何运动命令。

## 验证结果

本地脚本编译：

```text
$ python3 -m py_compile onboard/scripts/o1_wave_rover_serial_feedback_probe.py
pass: exit 0, no output
```

本地单测：

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py
.......
----------------------------------------------------------------------
Ran 7 tests in 0.147s

OK
```

远端一次性 T=130 probe：

```text
$ ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --request-base-feedback --port /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 --baudrate 115200 --read-timeout-s 2' < onboard/scripts/o1_wave_rover_serial_feedback_probe.py
ssh: connect to host 192.168.1.11 port 37878: No route to host
exit 255
```

Scoped diff check：

```text
$ git diff --check -- onboard/scripts/o1_wave_rover_serial_feedback_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py docs/hardware/o1_wave_rover_serial_feedback_probe.md sprints/2026.06.01_20-21_o1-t130-feedback-observation/tech-done.md
pass: exit 0, no output
```

新增 `tech-done.md` whitespace check：

```text
$ git diff --check --no-index /dev/null sprints/2026.06.01_20-21_o1-t130-feedback-observation/tech-done.md
pass: no whitespace warning output; exit 1 is expected because --no-index compares a new file against /dev/null
```

中文注释比例：本轮未修改 Python 脚本或测试文件，因此不重新计算注释比例；既有脚本和测试仍保留高密度中文安全边界注释。

## 远端 SSH / probe 摘要

- SSH 可达性：不可达，`No route to host`。
- 是否触达远端 Python：否。
- 是否打开 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`：否。
- 是否发送 vendor `{"T":130}\n`：否，SSH 连接未建立。
- 是否发送 `T=1`、`T=13`、`T=131`、`cmd_vel` 或运动命令：否。
- 是否读到 `T=1001`：否。
- 是否读到其他 feedback 类型：否。

## 失败定位

失败发生在 SSH 网络连接层，命令尚未进入远端 shell。当前证据只能定位为 `remote_network_unreachable`，不能定位为 pyserial 缺失、串口打不开、WAVE ROVER 不响应、波特率错误或反馈协议错误。

## 剩余风险与下一步

- 恢复当前开发机到 `192.168.1.11:37878` 的路由或网络连通性后，重复同一条 SSH 命令。
- 若 SSH 可达但 pyserial 缺失，记录 `pyserial_unavailable` JSON blocker，不要临时改脚本绕过。
- 若 SSH 可达且串口可打开但无反馈，保留 probe JSON 中的 `serial_opened`、`feedback_request.sent`、`read_line_count`、`observed_feedback_types`，再判断是否需要调整 read window 或人工确认底盘电源/线缆。
- 在真实 `T=1001` 出现前，O1 仍为 `T=1001 not_proven`，不得升级为 HIL pass。

## Product Closeout

2026-06-01 20-21 Product / OKR closeout：本轮用户价值是把显式 `--request-base-feedback` 入口推进到真实上车观察路径，用非运动命令 `{"T":130}\n` 请求底盘反馈，争取拿到真实 `T=1001`，但必须把网络层失败和硬件/串口/协议失败分开归因。

OKR 映射和方向判断：Objective 1 保持约 93%，方向为继续；本轮只能记录 `T=130 observation blocked by remote_network_unreachable`，不能上调 O1，不能写成 HIL pass、真实反馈通过或真实底盘可控。Objective 5、Objective 6、Objective 7 本轮未触碰，进度不变。

KR 拆解和归档：O1 KR3 的真实 `T=1001` 反馈仍为 `T=1001 not_proven`，O1 KR1/KR2/KR4/KR5/KR6 也没有新的真实硬件完成证据；本轮没有已完成 KR 可移入历史区。历史记录位置为 `docs/process/okr_progress_log.md` 的 `2026-06-01 20-21` 小节、`OKR.md` 第 4/4.1/5 节和本文档。

本轮核心抓手和下一步：先恢复开发机到 `192.168.1.11:37878` 的网络/路由可达性，再重复同一条 SSH 命令；若 SSH 可达后 pyserial、串口打开或反馈读取失败，再分别记录 `pyserial_unavailable`、`serial_open_failed` 或 no-feedback 观察，不要把网络 blocker 混成 WAVE ROVER 协议问题。

优先级和责任 Engineer：下一步仍由 Hardware Infra Engineer 主责；验收口径是远端命令真实进入 Python、打开 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00`、显式发送一次 `{"T":130}\n`、输出结构化 JSON，并能证明是否读到 `T=1001`。未读到前，O1 不上调。

风险和证据链缺口：当前证据停在 SSH 网络层，未触达远端 Python、未打开串口、未发送 T=130、未读到 T=1001。真实 WAVE ROVER feedback、真实 UART/HIL、真实底盘控制、真实 LiDAR `/scan`、ROS Humble runtime、TF、Nav2/SLAM、150000 上车稳定性和 PR #5 硬件材料仍未证明。
