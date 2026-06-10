# PC Map Runtime Controls V1 Tech Done

sprint_type: micro

## 自主能力目标和本轮抓手

本轮目标是让 PC 高级诊断可以完整触发上位机 no-motion 建图 runtime：PC 固定代理
调用 `/api/map/start` / `/api/map/save`，上位机启动 LiDAR + SLAM，观测 `/scan`
和 `/map`，调用 `/trashbot/save_map`，生成地图 YAML/PGM，并在结束后清理进程。

本轮不做真实底盘运动，不发布 `/cmd_vel`，不调用 `/api/base/*`，不触碰
WAVE ROVER UART `/dev/ttyS5`。WAVE ROVER vendor 边界仍以
`docs/vendor/VENDOR_INDEX.md` 及其指向资料为准；本轮只消费 LiDAR `/dev/ttyACM0`
和 ROS2 SLAM runtime。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `/api/map/start` 和 `/api/map/save` 改为调用内置
    `run_map_lifecycle_proof_helper(...)`。
  - `map_name` 只允许 `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`，并用 argv list
    传给 helper。
  - `artifact_path` 只回显并标记 ignored，不参与任意写路径。
  - map lifecycle 响应补齐 `publishes_cmd_vel=false`、
    `calls_base_manual=false`、`uses_base_uart=false` 等硬危险字段。
- `onboard/scripts/o3_map_lifecycle_proof.py`
  - 增加 `map_name` 校验。
  - `/map` 首帧等待从 12s 放宽到 20s，`save_map` service 等待从 8s 放宽到
    12s，降低实板 SLAM 首图抖动。
- `onboard/tests/test_upper_robot_api.py`
  - 覆盖 start 使用 no-motion helper、非法 `map_name` 不执行 subprocess。
- `onboard/tests/test_map_lifecycle_proof_helper.py`
  - 覆盖 `--map-name` help 和非法路径名拒绝。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - map lifecycle body 增强白名单。
  - `command_result.executed=true` 不再单独导致 `lifecycle_failed`。
  - 仍 fail closed 于 HTTP 非 OK、远端 failure/error 和硬危险字段 true。
  - start/save fetch timeout 扩到 120s。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 高级诊断地图详情新增可点击 `开始建图（高级）`。
  - 普通首屏地图卡片仍只保留 `刷新地图` / `查看地图列表`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 safe executed no-motion helper 通过代理、危险字段仍失败。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖高级诊断新建图按钮和固定 start 代理调用。
- `docs/hardware/board_sensor_stack_smoke.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.06.11_02-45_pc_map_runtime_controls/artifacts/*`

## 接口影响

- 上位机：
  - `POST /api/map/start`：执行 no-motion map runtime helper，不再返回
    `command_not_configured`。
  - `POST /api/map/save`：执行同一 no-motion helper，不再返回
    `command_not_configured`。
  - `POST /api/map/reset`、`POST /api/map/load`：仍保持 guard / dry-run 行为。
- PC 代理：
  - `POST /api/robot-control/map/start`
  - `POST /api/robot-control/map/save`
  - executed=true 现在可作为正常 no-motion runtime 诊断字段通过代理；危险 true、
    远端 failure 或 HTTP 失败仍 blocked。
- UI：
  - 普通首屏不新增建图/保存/Start/Reset/raw/HIL/速度/点动控件。
  - 高级诊断地图详情允许触发 start/save。

## 本地验证结果

```text
python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_map_lifecycle_proof_helper
Ran 18 tests in 0.091s
OK
```

```text
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o3_map_lifecycle_proof.py
OK
```

```text
cd pc-tools/workstation && npm run build
✓ built in 1.24s
```

```text
cd pc-tools/workstation && npm run test
Test Files  2 passed (2)
Tests  78 passed (78)
```

```text
cd pc-tools/workstation && npm run lint
eslint .
OK
```

## 真实上位机 smoke

部署目标：`root@192.168.1.11 -p 37878`。

远端验证：

- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o3_map_lifecycle_proof.py` 通过。
- `systemctl restart trashbot-upper-robot-api.service` 后 `systemctl is-active` 返回
  `active`。
- `POST /api/map/save` 使用 `map_name=pc_runtime_v1` 返回
  `status=map_once_artifact_metadata_observed`、
  `command_result.executed=true`、`command_result.ok=true`。
- 放宽等待窗口并重新部署后，最终版本直连 `POST /api/map/save` 使用
  `map_name=final_direct_save` 也返回 `status=map_once_artifact_metadata_observed`、
  `command_result.ok=true`。
- 生成：
  - `/root/rober/onboard/runtime/maps/pc_runtime_v1.yaml`
  - `/root/rober/onboard/runtime/maps/pc_runtime_v1.pgm`
  - `/root/rober/onboard/runtime/maps/final_direct_save.yaml`
  - `/root/rober/onboard/runtime/maps/final_direct_save.pgm`
- `GET /api/map/list` 列出 `pc_runtime_v1.yaml/pgm`。
- `GET /api/map/proof/latest` 显示 `scan_once_observed=true`、
  `map_once_observed=true`、`map_file_observed=true`、
  `map_metadata_observed=true`。
- 最终 `lsof /dev/ttyS5 /dev/ttyACM0`、`fuser -v /dev/ttyS5 /dev/ttyACM0`
  无输出；`o3_map_lifecycle_proof.py`、`slam_toolbox`、`lidar_driver` 无残留。

PC 代理 smoke：

- `POST /api/robot-control/map/start?baseUrl=http://192.168.1.11:8787`
  返回 `proxy_status=lifecycle_forwarded`、`remote_http_status=200`、
  `command_result.executed=true`、`command_result.ok=true`。
- `POST /api/robot-control/map/save?baseUrl=http://192.168.1.11:8787`
  首轮失败为远端 `/map_once_not_observed`；放宽 helper 等待窗口后 rerun 返回
  `proxy_status=lifecycle_forwarded`、`command_result.ok=true`。
- 最终生成：
  - `/root/rober/onboard/runtime/maps/pc_proxy_start.yaml`
  - `/root/rober/onboard/runtime/maps/pc_proxy_start.pgm`
  - `/root/rober/onboard/runtime/maps/pc_proxy_save2.yaml`
  - `/root/rober/onboard/runtime/maps/pc_proxy_save2.pgm`
- 最终清场仍无 `/dev/ttyS5`、`/dev/ttyACM0` 占用，目标进程无残留。

Artifact：

- `artifacts/remote_map_save_smoke.log`
- `artifacts/pc_proxy_map_start.json`
- `artifacts/pc_proxy_map_save.json`
- `artifacts/pc_proxy_save_failure_diagnosis.log`
- `artifacts/pc_proxy_map_save_rerun.json`
- `artifacts/remote_final_cleanup_after_proxy.log`
- `artifacts/remote_final_direct_save.log`

## Browser/DOM smoke

使用 in-app Browser 打开 `http://127.0.0.1:5173/`：

- 首屏 `.robot-console-grid` 为 5 张卡片。
- 地图卡片包含 `刷新地图` 和 `查看地图列表`。
- 首屏未出现 `开始建图`、`保存地图`、`Start`、`Reset`、`raw`、`HIL`、
  `速度`、`点动`。
- 打开 `高级诊断` 后，地图详情包含 `开始建图（高级）`、`保存地图`、
  `map_name（可选）`、`artifact_path（可选）`。

## 剩余风险

- 本轮未评估地图质量，`*.yaml/pgm` 只证明 runtime 可产物。
- 本轮未证明 AMCL 定位、Nav2 map_server/amcl/planner/controller 可运行。
- 本轮未证明 fixed-route execution、NavigateToPose 或 delivery success。
- 本轮未做真实底盘运动、WAVE ROVER HIL、robot ACK 或 `/cmd_vel` 链路验证。
- 首轮 PC proxy save 曾因 `/map_once_not_observed` 暴露 SLAM 首图抖动；已通过
  放宽等待窗口修复并 rerun 通过，但地图质量和长稳连续性仍需后续 gate。
