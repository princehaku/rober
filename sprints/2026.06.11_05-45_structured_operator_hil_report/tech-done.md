# Structured Operator HIL Report

- sprint_type: micro
- owner: robot-hardware-engineer
- run_time: 2026-06-11 05:50:11 CST

## 已读资料

本轮按硬件任务要求先读取：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

采用的硬件事实边界：WAVE ROVER 上下位机链路是 UART newline-delimited UTF-8 JSON；
vendor Raspberry Pi 示例串口是 `/dev/ttyAMA0 @ 115200`，当前 Orange Pi 实板串口
仍按现场证据使用 `/dev/ttyS5 @ 115200`；`json_cmd.h` 中运动/反馈命令包含
`T=1/T=13/T=130/T=131`。本轮没有调用这些底盘控制或反馈命令。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `structured_hil_claims` 归一化，支持顶层字段或 nested
    `structured_hil_claims` 输入。
  - 一等字段包含 `external_video_recorded`、`external_video_ref`、
    `visible_content_proven`、`camera_artifacts_ref`、
    `wheel_feedback_lr_nonzero_proven`、`wheel_feedback_ref`,
    `physical_motion_lidar_delta_proven`、`scan_delta_ref`、
    `real_route_map_proven`、`route_map_ref`、`delivery_success`、`site_state`。
  - POST artifact、POST 回包、GET readback 和 status summary 均回显结构化 claims。
  - 顶层安全字段继续 fail-closed：`operator_report_material_only=true`、
    `hil_pass=false`、`delivery_success=false`、
    `report_replaces_stop_status_ack_or_hil=false`、`sends_motion_commands=false`、
    `opens_serial=false`。
- `onboard/tests/test_upper_robot_api.py`
  - 覆盖结构化 HIL claims 持久化、GET 回显、nested claims 输入。
  - 覆盖 report 声称 `delivery_success=true` 时，顶层仍强制 false。
- `docs/hardware/field_hil_operator_report_template.md`
  - 更新现场填写模板，移除“只能塞进 notes”的旧边界。
  - 增加顶层字段和 nested `structured_hil_claims` payload 示例。
- `docs/hardware/field_hil_execution_pack.md`
  - 更新 operator report intake 说明，明确结构化字段只是材料 claim。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 新增 2026-06-11 05:45 structured report intake no-motion 边界。

## 验证结果

本地验证：

```text
$ python3 -m unittest onboard.tests.test_upper_robot_api
..................
----------------------------------------------------------------------
Ran 18 tests in 0.018s

OK

$ python3 -m py_compile onboard/scripts/upper_robot_api.py
<no output, exit 0>

$ git diff --check
<no output, exit 0>
```

真实上位机部署与 smoke：

- 远端：`root@192.168.1.11 -p 37878`
- 备份：`/root/rober/onboard/scripts/upper_robot_api.py.bak_structured_report_20260611_054907`
- 部署目标：`/root/rober/onboard/scripts/upper_robot_api.py`
- 远端 `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py`：exit 0。
- `systemctl restart trashbot-upper-robot-api.service` 后：

```text
active
Active: active (running) since Thu 2026-06-11 05:49:17 CST
Main PID: 231108 (python3)
```

POST/GET `/api/operator/report` smoke 只使用 `curl http://127.0.0.1:8787/api/operator/report`。
smoke payload 故意提交 `delivery_success=true` claim；断言结果：

```text
operator_report_post_get_smoke_assertions=PASS
POST top-level:
  operator_report_material_only=True
  hil_pass=False
  delivery_success=False
  sends_motion_commands=False
  opens_serial=False
  report_replaces_stop_status_ack_or_hil=False
POST claims:
  structured_hil_claims.delivery_success=True
  structured_hil_claims.site_state=api_intake_no_motion_no_serial_smoke
GET top-level: same fail-closed values
GET claims: same structured claim values
```

远端清场：

```text
# service active
active
# lsof /dev/ttyS5 /dev/ttyACM0
# fuser -v /dev/ttyS5 /dev/ttyACM0
```

`lsof`/`fuser` 对 `/dev/ttyS5` 与 `/dev/ttyACM0` 无输出，证明本轮 report smoke
未占用底盘或雷达串口。

## Artifacts

- `sprints/2026.06.11_05-45_structured_operator_hil_report/artifacts/remote_smoke/01_predeploy_backup_compile_status.log`
- `sprints/2026.06.11_05-45_structured_operator_hil_report/artifacts/remote_smoke/02_deploy_compile_restart_active.log`
- `sprints/2026.06.11_05-45_structured_operator_hil_report/artifacts/remote_smoke/03_operator_report_post.json`
- `sprints/2026.06.11_05-45_structured_operator_hil_report/artifacts/remote_smoke/04_operator_report_get.json`
- `sprints/2026.06.11_05-45_structured_operator_hil_report/artifacts/remote_smoke/05_service_device_clearance.log`

## 剩余风险

- 本轮只证明 operator report 的结构化材料 intake、持久化和回显；它不是 HIL pass。
- 本轮没有发送 `/cmd_vel`、没有调用 `/api/base/manual`、没有打开 `/dev/ttyS5`、
  没有启动 Nav2 goal，也没有证明真实路线、真实送达、相机可见内容、wheel feedback 非零
  或 LiDAR motion delta。
- 后续 PC/现场流程可以稳定消费 `structured_hil_claims`，但最终 HIL 结论仍必须由外部视频、
  相机 artifact、`T=1001` JSONL、scan delta、route/map artifact 和 stop/API restore
  记录共同支撑。
