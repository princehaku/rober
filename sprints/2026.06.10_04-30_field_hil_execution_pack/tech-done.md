# Field HIL Execution Pack Tech Done

## sprint_type: micro

## 目标

把截至 2026-06-10 04:15 的真实上位机证据矩阵转成下一轮现场 HIL 执行包。本轮不连接
上位机、不运行 ROS2 stack、不发送运动命令，只更新允许范围内的硬件执行文档和 sprint 留档。

## 已读来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `sprints/2026.06.10_00-25_no-motion-map-route-evidence/final.md`
- `sprints/2026.06.10_00-25_no-motion-map-route-evidence/tech-done.md`
- `sprints/2026.06.10_00-45_integrated-sensor-motion-capture/final.md`
- `sprints/2026.06.10_00-45_integrated-sensor-motion-capture/tech-done.md`
- `sprints/2026.06.10_03-45_lidar_motion_delta_retry/tech-done.md`
- `sprints/2026.06.10_04-00_board_camera_visibility_probe/tech-done.md`
- `sprints/2026.06.10_04-15_wave_rover_min_actuation_probe/tech-done.md`
- `docs/hardware/board_sensor_stack_smoke.md`
- `docs/vision/board_camera_publisher.md`
- `docs/hardware/wave_rover_json_bridge.md`

## 采用的 vendor 事实

- WAVE ROVER 上下位机链路是 UART，一行 UTF-8 JSON 以 `\n` 结束。
- vendor Raspberry Pi 示例默认底盘串口是 `/dev/ttyAMA0 @ 115200`；Orange Pi 实板串口
  必须以现场枚举和实测为准，近期实板证据使用 `/dev/ttyS5 @ 115200`。
- `CMD_SPEED_CTRL=1`，示例 `{"T":1,"L":0.5,"R":0.5}`。
- `CMD_ROS_CTRL=13`，示例 `{"T":13,"X":0.1,"Z":0.3}`；当前已验证项目路径仍是
  `command_mode:=speed` 的 `T=1`。
- `CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、
  `CMD_FEEDBACK_FLOW_INTERVAL=142`、`CMD_UART_ECHO_MODE=143`、
  `FEEDBACK_BASE_INFO=1001`。

## 实际改动

- 新增 `docs/hardware/field_hil_execution_pack.md`
  - 写入当前证据矩阵：LiDAR、camera、map/route、base UART/feedback、motion、
    stop/API restore、delivery 的 `proven / not proven / boundary / source sprint`。
  - 写入现场人工预检、允许运动前 gate、受控运动 HIL 顺序、成功判据、失败/停止判据。
  - 明确 `visible_content_proven=true`、`physical_motion_lidar_delta_proven=true`、
    `wheel_feedback_lr_nonzero_proven=true`、`real_route_map_proven=true`、
    `delivery_success=true` 的 artifact 要求。
- 更新 `docs/hardware/board_sensor_stack_smoke.md`
  - 增加 Field HIL Execution Pack 指向，要求后续停止盲跑远程低速 probe，先做现场人工预检和外部视频证据。
- 新增 `sprints/2026.06.10_04-30_field_hil_execution_pack/tech-done.md`
  - 记录本 micro sprint 的已读来源、采用事实、实际改动、验证和剩余风险。

## 验证方式与结果

本轮只做文档自检和 git 状态核对；未连接上位机，未运行运动命令。

### `git diff --stat`

```text
docs/hardware/board_sensor_stack_smoke.md | 12 ++++++++++++
1 file changed, 12 insertions(+)
```

说明：`git diff --stat` 默认只统计已跟踪文件；本轮新增的 execution pack 和 micro sprint
留档由下方 `git status --short` 记录。

### `rg` 自检

```text
rg -n "visible_content_proven|physical_motion_lidar_delta_proven|wheel_feedback_lr_nonzero_proven|delivery_success|stop|现场|artifact" \
  docs/hardware/field_hil_execution_pack.md \
  sprints/2026.06.10_04-30_field_hil_execution_pack/tech-done.md \
  docs/hardware/board_sensor_stack_smoke.md
```

结果：通过。关键命中覆盖：

- `docs/hardware/field_hil_execution_pack.md`
  - 当前证据矩阵中的 `visible_content_proven=false`、`physical_motion_lidar_delta_proven=false`、
    `wheel_feedback_lr_nonzero_proven=false`、`delivery_success=false`。
  - `现场人工预检`、`允许运动前 gate`、受控运动 step 中的 `stop`、abort 和 artifacts 要求。
  - 成功判据中的 `visible_content_proven=true`、`physical_motion_lidar_delta_proven=true`、
    `wheel_feedback_lr_nonzero_proven=true`、`real_route_map_proven=true`、`delivery_success=true`。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 新增 execution pack 指向，包含 `visible_content_proven`、
    `physical_motion_lidar_delta_proven`、`wheel_feedback_lr_nonzero_proven`、`delivery_success`。
- `sprints/2026.06.10_04-30_field_hil_execution_pack/tech-done.md`
  - 已记录本轮实际改动、验证方式、当前证据结论和剩余风险。

### `git status --short`

```text
 M docs/hardware/board_sensor_stack_smoke.md
?? docs/hardware/field_hil_execution_pack.md
?? sprints/2026.06.10_04-30_field_hil_execution_pack/
```

## 当前证据结论摘要

- LiDAR topic/聚合 scan：`proven`，但不是机械标定或物理运动证明。
- camera device/topic：`proven`；`visible_content_proven=false`，黑场仍需现场镜头/补光/朝向检查。
- map/route：`boundary`，已有 no-motion/integrated artifacts，但不是导航级地图或真实路线。
- base UART/feedback：UART 和 `T=1001` debug 记录有证据；wheel feedback 非零未证明。
- motion：`physical_motion_lidar_delta_proven=false`，`wheel_feedback_lr_nonzero_proven=false`。
- stop/API restore：`proven`，但只适用于 bounded smoke，不等于自主发车。
- `delivery_success=false`。

## 剩余风险

- 仍缺现场人工观察、外部视频和操作员报告，不能把低速命令发送解释为真实物理运动。
- 相机仍缺可见内容，在 `visible_content_proven=true` 前不能用于视觉定位、路线关键帧或远程可视验收。
- WAVE ROVER `T=1001.L/R` 仍未出现非零，可能涉及起动阈值、电机供电、急停、遥控/模式、底盘架空或反馈字段语义，需要现场排查。
- 文档执行包不能替代 HIL；下一轮必须按 execution pack 归档视频、照片、command log、feedback JSONL、scan metrics、route/map 和 operator report。
