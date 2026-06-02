# 8787 Upper Robot API Hardware Safety

sprint_type: micro

## 实际改动

本轮由 Hardware Infra Engineer 收口 8787 统一上位机 Robot API 的底盘手控安全边界。

- `onboard/scripts/upper_robot_api.py`：非法 direction 结构化拒绝；manual pulse 限速限时并自动发送 stop；返回保留 `command_result`、`stop_result`、`serial_write_failures`、`auto_stop_executed` 和 `T=1001` 未观察边界；`/api/base/stop` 的 `robot_control_executed` 跟随 stop 写入结果。
- `onboard/scripts/test_upper_robot_api.py`：新增 fake pyserial 单元测试，不打开真实串口。
- `docs/interfaces/o7_upper_robot_api.md`：补充 2026-06-03 硬件安全收口规则。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`：补充 vendor 来源和本轮不构成 HIL 的边界。
- `docs/interfaces/o1_o5_90_evidence_boundary.md`：补充 O7 8787 API 本地软件证据不得提升 O1/O5 真实 90% 的边界。

## 验证结果

执行时间：2026-06-03。

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py
```

结果：exit 0，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_upper_robot_api.py
```

结果：

```text
....
----------------------------------------------------------------------
Ran 5 tests in 0.803s

OK
```

```bash
bash -n onboard/scripts/upper_robot_api.sh onboard/scripts/install_upper_robot_api_service.sh
```

结果：exit 0，无输出。

```bash
bash onboard/scripts/install_upper_robot_api_service.sh --dry-run --repo-root /root/rober --systemd-dir /tmp
```

结果：

```text
unit_name=trashbot-upper-robot-api.service
repo_root=/root/rober
systemd_dir=/tmp
defaults=HOST=0.0.0.0 PORT=8787 CAMERA=http://127.0.0.1:8088 BASE=/dev/ttyS5
safety=low_speed_pulse_auto_stop_no_cloud_relay
[dry-run] render /root/rober/onboard/systemd/trashbot-upper-robot-api.service -> /tmp/trashbot-upper-robot-api.service with @ROBER_REPO_ROOT@=/root/rober
[dry-run] systemctl daemon-reload
[dry-run] systemctl enable trashbot-upper-robot-api.service
[dry-run] systemctl restart trashbot-upper-robot-api.service
[dry-run] systemctl --no-pager --full status trashbot-upper-robot-api.service
```

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/upper_robot_api.sh onboard/scripts/install_upper_robot_api_service.sh onboard/scripts/test_upper_robot_api.py onboard/systemd/trashbot-upper-robot-api.service docs/interfaces/o7_upper_robot_api.md docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_o5_90_evidence_boundary.md sprints/2026.06.03_03-04_o7-upper-robot-api-safety/tech-done.md
```

结果：exit 0，无输出。

第一轮 dry-run 曾失败：

```text
error: required file missing: /root/rober/onboard/systemd/trashbot-upper-robot-api.service
```

定位：dry-run 用于在本机预演远端 `/root/rober` 路径，但脚本错误地要求远端 repo 文件必须在本机存在。已修复为 dry-run 使用当前 checkout 的 unit/script 模板做本地校验；真实安装仍严格检查目标 repo 文件。

## 剩余风险

- 本轮没有打开真实 `/dev/ttyS5`，没有 SSH，没有发送真实 WAVE ROVER JSON、`cmd_vel` 或运动命令。
- 本轮没有读取 `T=1001`，不证明 robot ACK、HIL pass、真实 `/odom`、真实 `/imu/data`、真实 `/battery` 或 delivery success。
- 真实上车仍需现场低速点动、人工急停、stop 写入失败演练、`T=130 -> T=1001` 反馈和 operator report。

## Product closeout / OKR verdict

- O1 保持约 93%：`/dev/ttyS5 @115200` 和低速 `T=1,L=0.08,R=0.08` 是既有现场事实，本轮 8787 upper API 只补软件 guardrail；`T=1001`、ACK、HIL、真实 `/odom`、`/imu/data`、`/battery` 仍 `not_proven`。
- O5 保持约 96%，O6 保持约 96%：本轮不涉及生产云、真实 4G/SIM、production DB/queue、OSS/CDN live traffic 或真实 phone/browser 材料。
- O7 上调到约 98%：理由是 8088 systemd + PC Live Operator + unified upper API software safety ready。
- Production path、real control、ACK、HIL 和完整 delivery success 均仍 `not_proven`。
