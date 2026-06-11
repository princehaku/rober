# sprint_type: micro

## 本轮目标与抓手

本轮目标是恢复真实上位机 `http://192.168.1.11:8787` 的 Nav2 no-motion path proof，并把上一轮
PC proxy smoke 中 `o10-amcl-nav2-runtime-wrapper-failure-1781172997846` 的退化定位到具体层。

抓手是 direct Robot API no-motion managed path refresh：不执行 `NavigateToPose`，不发布
`/cmd_vel`，不调用 `/api/base/manual`，不调用 `/api/base/status` 或 `/api/base/stop`，不打开
WAVE ROVER 底盘 UART `/dev/ttyS5`。硬件事实入口采用 `docs/vendor/VENDOR_INDEX.md`：WAVE
ROVER base 是 UART newline-delimited JSON；当前 `/dev/ttyS5 @ 115200` 只是现场底盘串口事实，
本轮不触碰底盘串口。

## 实际改动

- 新增本 sprint artifacts：
  - `artifacts/logs/ssh_initial_service_status_readback.log`
  - `artifacts/logs/ssh_cleanup_readback.log`
  - `artifacts/raw/nav2_refresh_request_body.json`
  - `artifacts/raw/nav2_refresh_response.json`
  - `artifacts/raw/nav2_refresh_response.pretty.json`
  - `artifacts/raw/nav2_refresh_response.http_code`
  - `artifacts/raw/nav2_proof_latest_after_refresh.json`
  - `artifacts/raw/nav2_proof_latest_after_refresh.http_code`
  - `artifacts/raw/nav2_status_after_refresh.json`
  - `artifacts/raw/nav2_status_after_refresh.http_code`
- 更新 `docs/navigation/fixed_route_workflow.md`，记录 19:25 direct API 恢复证据和 19:05 回归根因。
- 更新 `docs/hardware/board_sensor_stack_smoke.md`，补充本轮真实板端 no-motion Nav2 path recovery 边界。
- 未改 `onboard/scripts/o10_amcl_nav2_runtime_proof.py`，未改 onboard tests，未改 PC UI、底盘 driver、串口配置或 launch 硬件参数。

## 接口影响

无接口变更。`/api/nav2/proof/refresh` 仍使用现有 managed no-motion proof contract：

- `timeout_s=30`
- `managed_runtime_opt_in=true`
- `managed_timeout_s=30`
- `managed_map_yaml=/root/rober/onboard/runtime/maps/trashbot_map.yaml`
- `initialpose_opt_in=true`
- `initialpose_x=0`
- `initialpose_y=0`
- `initialpose_yaw=0`
- `path_generation_opt_in=true`
- `path_generation_timeout_s=30`
- path goal `map:(0.8, 0, 0)`

## 验证结果

### SSH 初始 readback

命令：SSH 到 `root@192.168.1.11 -p 37878`，采集 service、latest/status、`nav2_lifecycle_latest.json`、
process、ROS graph、`/cmd_vel` info。

关键结果：

```text
trashbot-upper-robot-api.service=active
latest_evidence_ref=o10-amcl-nav2-runtime-wrapper-failure-1781172997846
status=blocked_with_root_cause
managed_runtime_started=true
managed_runtime_cleanup_ok=false
initialpose_published=true
amcl_pose_observed=true
path_generation_requested=true
path_generation_attempted=false
path_generated=false
path_point_count=0
last_phase=interrupted
last_successful_phase=lifecycle_probe
current_command=timeout 8 ros2 topic echo --once /map
```

定位：19:05 的回归不是 map 文件或 planner 永久不可用；artifact log 显示 planner/server 后续已经能进入 active，
但 PC proxy 触发时 helper 被 outer process timeout 打断，最终由 wrapper failure artifact 覆盖为
`blocked_with_root_cause`。

### Direct Robot API refresh

命令：本机直连 `POST http://192.168.1.11:8787/api/nav2/proof/refresh`，body 为本轮固定 30s
managed no-motion path proof。

```text
nav2_refresh_http=200
status=nav2_no_motion_path_generation_runtime_observed
evidence_ref=o10-amcl-nav2-runtime-1781173633739
managed_runtime_started=true
managed_runtime_cleanup_ok=true
initialpose_published=true
amcl_pose_observed=true
planner_server_active=true
path_generation_requested=true
path_generation_attempted=true
path_generation_succeeded=true
path_generated=true
path_point_count=32
publishes_cmd_vel=false
calls_base_manual=false
uses_base_uart=false
safe_to_control=false
robot_control_executed=false
delivery_success=false
root_causes=[]
blockers=[]
```

结论：Nav2 no-motion path proof 已恢复。与 18:20 的 31 points 证据相比，本轮生成 32 points；
这是同一 `map:(0.8, 0, 0)` no-motion planner proof contract 下的新鲜 direct Robot API 证据。

### Latest/status readback

```text
GET /api/nav2/proof/latest HTTP 200
latest status=nav2_no_motion_path_generation_runtime_observed
latest evidence_ref=o10-amcl-nav2-runtime-1781173633739
latest path_generated=true
latest path_point_count=32
latest planner_server_active=true
latest managed_runtime_cleanup_ok=true
latest root_causes=[]

GET /api/nav2/status HTTP 200
status=not_proven
```

`/api/nav2/status` 继续保持 software guard `not_proven` 是预期行为：本轮只证明 no-motion path generation，
不证明可发车、controller 执行、固定路线执行、HIL 或 delivery success。

### 清理与安全边界

SSH cleanup readback：

```text
trashbot-upper-robot-api.service=active
ps target check: no o10_amcl_nav2_runtime_proof/map_server/amcl/planner_server/lifecycle_manager/controller_server helper residual
ros2 lifecycle nodes: no managed lifecycle nodes after cleanup
ros2 topic info /cmd_vel: Unknown topic '/cmd_vel'
ros2 topic echo --once /cmd_vel: Could not determine the type for the passed topic
lsof /dev/ttyS5: no output
fuser -v /dev/ttyS5: no output
```

`ps` 里唯一包含 `/dev/ttyS5` 的条目是既有 `upper_robot_api.py --base-port /dev/ttyS5 --base-baudrate 115200`
服务参数；`lsof`/`fuser` 对 `/dev/ttyS5` 均无 holder 输出，本轮未打开底盘串口。

### `git diff --check`

通过，无输出：

```text
git diff --check -- sprints/2026.06.11_19-25_nav2_no_motion_path_regression_recovery docs/navigation/fixed_route_workflow.md docs/hardware/board_sensor_stack_smoke.md onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

## 数据、样本和调试输出变化

- 新鲜 Nav2 proof evidence：`o10-amcl-nav2-runtime-1781173633739`。
- 新鲜 path point count：`32`。
- 新鲜 latest/status readback 保存在 `artifacts/raw/`。
- 初始 wrapper failure 和 cleanup readback 保存在 `artifacts/logs/`。

## 剩余风险

- 本轮恢复的是 direct Robot API no-motion path proof；不等于 `NavigateToPose`、controller/BT 执行、固定路线执行、真实运动、HIL 或 delivery success。
- PC proxy 侧 19:05 的 `84s` helper cap 仍可能在慢现场再次把已接近完成的 helper 打断；建议后续由 full-stack/robot-software owner 调整 PC proxy 或 upper API timeout 预算，至少让 fixed 30s managed/path proof 有足够完成和 cleanup 余量。
- Cleanup log 中 LiDAR driver 在 SIGINT cleanup 时打印 `rcl_shutdown already called` traceback，但 `managed_runtime_cleanup_ok=true`、`root_causes=[]` 且清理 readback 无残留；这是清理日志噪声，不影响本轮 path proof。

## 完成前反思

- 需求满足：已完成 SSH readback、direct Robot API no-motion refresh、latest/status readback、cleanup readback，并恢复 `path_generated=true`。
- 范围控制：未改底盘串口、WAVE ROVER driver、PC 普通首屏 UI、launch 硬件参数或无关文件。
- 验证缺口：未执行任何 motion，不验证 controller、fixed-route execution、真实路线、HIL 或 delivery success。
- 文档同步：已同步更新 navigation/hardware 证据边界文档。
