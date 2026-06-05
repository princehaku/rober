# Tech Done: O9 PC Smoke + Map Runtime Epic

## sprint_type

sprint_type: epic

## Owner 1: Full-stack Software Engineer

### 实际改动

本轮状态：Owner 1 已收口。本次 Full-stack verification/fix-only 复核没有继续扩大 PC slice 代码改动；PC live smoke 的 TypeScript build blocker 已解除，8788 API 可用，8788 -> 8787 same-origin `refresh/latest` 均返回 JSON。

改动文件：

- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_direct_upper_pc_api.md`
- `sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/tech-done.md`

已做内容：

- 验证 `TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api` 能启动并监听 `http://127.0.0.1:8788`，未再复现上一轮 `tsx_ipc_pipe_enotsup`。
- 修复并验证 PC workstation build：`test/App.test.ts` 新增 scan-proof refresh/latest 回归后，TypeScript build 不再报 `Property 'aborted' does not exist on type 'never'` 或空 tuple index 错误。
- 定位并修复 8788 curl 的两个后续问题：
  - `POST /api/o7/direct-upper/radar/scan-proof/refresh` 先返回 `502`，root cause 是 PC proxy 使用 `1200ms` 通用 status timeout，而 8787 refresh 需要等待 LiDAR/ROS2 runtime warmup + collector。
  - `GET /api/o7/direct-upper/radar/scan-proof/latest` 先返回构建后的 SPA HTML fallback，不是 JSON；root cause 是 PC workstation 没有 latest 同源代理路由。
- 已补最小代码方向并完成复验：
  - `scan-proof refresh` 使用独立 `55000ms` 远端 timeout。
  - 新增 `GET /api/o7/direct-upper/radar/scan-proof/latest` 只读代理到 8787 `/api/radar/scan-proof/latest`。
  - 共享契约、测试 fixture 和文档同步补 latest path。
  - latest/readback 继续保留 `continuous_radar_not_proven`、`safe_to_control=false`、`robot_control_executed=false`，不把 once proof 包装成 continuous radar ready。

### 验证结果

已运行：

```bash
cd pc-tools/workstation && npm run build
```

结果：通过。关键日志：

- `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- `✓ 14 modules transformed.`
- `✓ built in 2.17s`

```bash
cd pc-tools/workstation && npm test -- --run test/App.test.ts
```

结果：通过。关键日志：

- `Test Files  1 passed (1)`
- `Tests  30 passed (30)`

```bash
cd pc-tools/workstation && TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api
```

结果：

- API 成功启动，日志包含 `pc-tools workstation API listening on http://127.0.0.1:8788`。

已运行 curl：

```bash
curl -fsS -X POST http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/refresh
curl -fsS http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/latest
```

结果：

- `POST /api/o7/direct-upper/radar/scan-proof/refresh` 通过 8788 同源代理拿到 JSON：`schema=trashbot.pc_tools_workstation.o7_direct_upper_radar_scan_proof_refresh.v1`、`endpoint=/api/o7/direct-upper/radar/scan-proof/refresh`、`command=radar_scan_proof_refresh`、`upper_request.path=/api/radar/scan-proof/refresh`、`upper_request.method=POST`、`upper_request.ok=true`、`upper_request.http_status=200`、`upper_result_summary.proof_status=scan_once_hz_raw_packet_tf_observed`、`upper_result_summary.latest_proof_status=scan_once_hz_raw_packet_tf_observed`、`upper_result_summary.scan_hz_average_rate_hz=241.753`、`upper_result_summary.tf_observed=true`、`upper_result_summary.all_required_observations_observed=true`、`upper_result_summary.runtime_summary_fallback_used=true`。
- refresh 响应同时保持边界：`upper_result_summary.continuous_scan_status=not_proven`、`safe_to_control=false`、`robot_control_executed=false`，`continuous_radar_not_proven` 和 `hil_pass` 仍在 `not_proven`。
- refresh 后再次 `GET /api/o7/direct-upper/radar/scan-proof/latest` 通过 8788 同源代理拿到 JSON：`schema=trashbot.pc_tools_workstation.o7_direct_upper_radar_scan_proof_latest.v1`、`endpoint=/api/o7/direct-upper/radar/scan-proof/latest`、`command=radar_scan_proof_latest`、`upper_request.path=/api/radar/scan-proof/latest`、`upper_request.method=GET`、`upper_request.ok=true`、`upper_request.http_status=200`、`upper_result_summary.status=not_reported`、`upper_result_summary.proof_status=scan_once_hz_raw_packet_tf_observed`、`upper_result_summary.latest_proof_status=scan_once_hz_raw_packet_tf_observed`、`upper_result_summary.artifact_status=loaded`、`upper_result_summary.artifact_path=runtime/lidar_scan_proof_latest.json`、`upper_result_summary.scan_hz_average_rate_hz=241.753`、`upper_result_summary.tf_observed=true`、`upper_result_summary.all_required_observations_observed=true`、`upper_result_summary.runtime_summary_fallback_used=true`。
- latest 响应继续保持边界：`upper_result_summary.continuous_scan_status=not_proven`、`safe_to_control=false`、`robot_control_executed=false`，未写成 continuous radar ready。

停止 8788 API 后运行：

```bash
lsof -ti tcp:8788
```

结果：无输出，确认 8788 无 listener。

本地验证：

```bash
git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md docs/interfaces/o7_direct_upper_pc_api.md sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/tech-done.md
```

结果：通过，无输出。

### Root Cause

- `tsx_ipc_pipe_enotsup`：`TMPDIR=/tmp` 已解除本轮复现中的启动 blocker，说明上一轮 root cause 是 `tsx` 在当前 WSL/Windows temp pipe 环境下的 IPC 路径问题。
- `test/App.test.ts` TypeScript blocker：新增 mock fetch/调用断言需要显式类型约束，否则 `vi.fn` 调用元组会被 TypeScript 推断成空 tuple/never；当前 build 已验证不再复现。
- 8788 refresh 502：不是 8787 route 不存在；直连 8787 refresh 约数秒后可 HTTP 200。PC proxy 原先 `1200ms` timeout 过短，不适合等待只读 LiDAR runtime warmup + collector。
- 8788 latest HTML：PC workstation 原先没有 `/api/o7/direct-upper/radar/scan-proof/latest` API 路由，请求落入静态 UI fallback。

### 证据边界与剩余风险

- 当前证明 `TMPDIR=/tmp` 可启动 8788 API，并证明 patch 后 8788 same-origin `refresh/latest` curl 均返回 JSON。
- 当前证明的是 once fresh scan proof artifact/readback：`proof_status=scan_once_hz_raw_packet_tf_observed`、`fresh_scan_proof_observed=true`、TF 和 required observations 为 true；它不证明 continuous radar ready。
- 即使 8788/8787 refresh/latest 返回 once fresh proof、hz/TF 或 `runtime_summary_fallback_used=true`，仍不证明 continuous radar ready、SLAM map、Nav2、PC WASD、WAVE ROVER ACK、HIL pass、`safe_to_control=true` 或真实送达。

## Owner 2: Robot Software Engineer + Robot Algorithm Engineer

### 实际改动

本轮状态：partial blocked with narrower root cause。按用户 status check 要求，已停止继续扩展和远端长任务。

改动文件：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/o3_map_lifecycle_proof.py`
- `onboard/scripts/test_upper_robot_api.py`
- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
- `docs/interfaces/lidar_ros2_closed_loop.md`
- `docs/navigation/nav2_map_quality_metrics.md`
- `sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/tech-done.md`

已做内容：

- 新增 `POST /api/map/proof/refresh`，解决 live 8787 旧接口返回 HTTP 405 的 route 缺口。
- 新增 `o3_map_lifecycle_proof.py` no-motion helper，目标是采集 `/scan` once、`/map` once、map save、map files、metadata，并把失败写入 `runtime/map_lifecycle_latest.json`。
- `learn.launch.py` 增加 `map_dir` 和 `default_map_name` 参数，map proof helper 可把 `map_recorder` 输出定向到 `runtime/maps`。
- 新增 HTTP route 回归测试，防止 `/api/map/proof/refresh` 回退成 405；测试只 mock helper，不启动 ROS2/SLAM/底盘。
- 文档同步补充 `POST /api/map/proof/refresh` / `GET /api/map/proof/latest` 的 helper 入口、root-cause 分类和 no-motion 证据边界。

### 现场基线与命令结果

用户指定原命令第一轮直接用远端默认 `zsh` source bash setup：

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; source /opt/ros/humble/setup.bash; ...; ros2 topic list; ...'
```

结果：

- `/opt/ros/humble/setup.bash: BASH_SOURCE[0]: parameter not set`
- `AMENT_TRACE_SETUP_FILES: parameter not set`
- `zsh:1: command not found: ros2`

修正为 `bash -lc` 且先 source 再进入严格检查后：

```bash
ssh root@192.168.1.11 -p 37878 'bash -lc '\''set -e; source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; set -u; command -v ros2; ros2 topic list; curl -fsS http://127.0.0.1:8787/api/map/list || true; echo; curl -fsS http://127.0.0.1:8787/api/map/proof/latest || true; echo'\'' '
```

结果摘要：

- `command -v ros2` -> `/opt/ros/humble/bin/ros2`
- `ros2 topic list` -> 只有 `/parameter_events`、`/rosout`
- `/api/map/list` -> HTTP 200，`failure_reason=map_artifact_dir_missing`，`map_count=0`
- `/api/map/proof/latest` -> HTTP 404，artifact `runtime/map_lifecycle_latest.json` missing

执行 no-motion proof 原命令时：

```bash
timeout 8 ros2 topic echo --once /scan
timeout 12 ros2 topic echo --once /map
curl -fsS -X POST http://127.0.0.1:8787/api/map/proof/refresh
curl -fsS http://127.0.0.1:8787/api/map/proof/latest
```

结果摘要：

- `/scan`：`WARNING: topic [/scan] does not appear to be published yet`，类型不可判定
- `/map`：`WARNING: topic [/map] does not appear to be published yet`，类型不可判定
- `POST /api/map/proof/refresh`：旧 live API 返回 HTTP 405
- `GET /api/map/proof/latest`：HTTP 404

补丁部署后：

```bash
scp -P 37878 onboard/scripts/upper_robot_api.py onboard/scripts/o3_map_lifecycle_proof.py root@192.168.1.11:/root/rober/onboard/scripts/
scp -P 37878 onboard/src/ros2_trashbot_bringup/launch/learn.launch.py root@192.168.1.11:/root/rober/onboard/src/ros2_trashbot_bringup/launch/
ssh root@192.168.1.11 -p 37878 'chmod +x /root/rober/onboard/scripts/o3_map_lifecycle_proof.py; systemctl restart trashbot-upper-robot-api.service'
```

结果：

- `trashbot-upper-robot-api.service` active running，main process 为 `/root/rober/onboard/scripts/upper_robot_api.py`
- symlink install 已生效：`/root/rober/onboard/install/.../learn.launch.py -> /root/rober/onboard/src/.../learn.launch.py`
- installed launch 可 grep 到 `map_dir`、`default_map_name`

依赖检查：

```bash
ros2 pkg prefix slam_toolbox
apt-cache policy ros-humble-slam-toolbox
```

结果：

- `slam_toolbox_missing`
- apt candidate 存在：`ros-humble-slam-toolbox 2.6.10-1jammy.20260426.081052`

按 status check 要求停止继续 broad work：远端 `apt-get install -y ros-humble-slam-toolbox` 已被中断；后续 `ps` 检查未再看到 `apt-get` / `dpkg` 活跃进程。该安装没有完成，不能作为 SLAM 可用证据。

### 本地软件护栏

已运行：

```bash
python3 -m compileall -q onboard/scripts onboard/src
python3 -m unittest discover -s onboard/scripts -p 'test_*.py'
```

结果：

- compileall 通过
- unittest 通过：`Ran 83 tests in 4.607s`，`OK (skipped=3)`

补充 narrow cleanup 后已运行：

```bash
git diff --check -- onboard/scripts onboard/src/ros2_trashbot_bringup onboard/src/ros2_trashbot_nav docs/interfaces/lidar_ros2_closed_loop.md docs/navigation sprints/2026.06.05_08-09_o9-pc-smoke-map-runtime-epic/tech-done.md
```

结果：

- `git diff --check` 通过，无输出。
- narrow cleanup 未运行远端 apt install、未运行 map runtime proof、未触碰 pc-tools。

### Root Cause

当前 root cause 已收窄到具体层：

- `ROS install/source`：远端默认 shell 是 `zsh`，不能直接 source ROS bash setup；必须用 `bash -lc`，且不能在 source 前启用 `set -u`。
- `upper API`：旧 live 8787 没有 `POST /api/map/proof/refresh` route，导致 HTTP 405；本轮已补 route 并部署。
- `SLAM`：`slam_toolbox` package 未安装，`ros2 pkg prefix slam_toolbox` 失败；安装被用户 status check 中断，未完成。
- `LiDAR/launch/topic remap`：现场常驻 ROS graph 无 `/scan`，只有 `/parameter_events`、`/rosout`；短窗口 LiDAR proof 不能等价为 continuous `/scan`。
- `SLAM/TF/topic remap`：现场无 `/map`，helper 尚未跑出 `/map` once。
- `map saver/file path`：`runtime/maps` 不存在，`runtime/map_lifecycle_latest.json` missing；没有 map YAML/PGM/metadata artifact。

### 证据边界与安全字段

本轮没有形成 `/map` once、map artifact 或 metadata。当前可计为 `blocked_with_root_cause`，不可计为 `robot_runtime_material` 的 map lifecycle proof。

安全字段必须保持：

- `safe_to_control=false`
- `sends_base_motion_commands=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `hil_pass=false`

本轮未发布 `/cmd_vel`，未调用 `/api/base/manual`，未发送 WAVE ROVER 底盘命令，不证明 AMCL/Nav2 ready、map 可导航、fixed-route 可跑、HIL pass 或 `safe_to_control=true`。

### 剩余风险

- 远端 `ros-humble-slam-toolbox` 安装被中断，可能需要后续先运行 `dpkg --configure -a` / `apt-get -f install` 复原 package 状态，再继续安装。
- `o3_map_lifecycle_proof.py` 已部署但尚未在安装完成后的 SLAM 环境里成功跑出 latest artifact。
- `map_recorder.py` 保存逻辑仍未在真实 `/map` 消息下验证。
- 本轮 narrow cleanup 只完成本地文档同步和软件护栏；没有继续远端 runtime、SLAM 安装或 `/map` proof。

### 2026-06-05 09:33 CST 状态检查收口更新

本段覆盖 Owner 2 上方 partial blocker 结论：本次继续执行后已经拿到新的 no-motion map lifecycle 证据，但仍保留安全边界，不把它写成 Nav2/AMCL/可控车完成。

实际追加改动：

- `onboard/scripts/o3_map_lifecycle_proof.py`：helper 启动 `learn.launch.py` 时显式传入 `no_motion_static_odom_tf:=true`、`waypoint_manager:=false`；map file 枚举改为按 onboard workdir 解析相对路径，避免 systemd/current-working-directory 造成 false-negative。
- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`：新增默认关闭的 `no_motion_static_odom_tf`，默认开启的 `waypoint_manager` 开关，以及 `slam_map_frame` / `slam_odom_frame` / `slam_base_frame` 参数；`slam_toolbox` 显式绑定 `map_frame=map`、`odom_frame=odom`、`base_frame=base_link`、`scan_topic=/scan`。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`：新增静态合同测试，锁住 no-motion proof 开关和 SLAM frame/topic 参数。
- `docs/interfaces/lidar_ros2_closed_loop.md`、`docs/navigation/nav2_map_quality_metrics.md`：同步记录远端 proof 证据、已解除的 `slam_toolbox_missing` blocker 和剩余 no-motion 边界。

远端 package/apt 结论：

```bash
dpkg --configure -a
apt-get -f install -y
apt-get install -y ros-humble-slam-toolbox
source /opt/ros/humble/setup.bash
ros2 pkg prefix slam_toolbox
```

结果摘要：

- `dpkg --audit` 初始显示大量 package `unpacked but not yet configured`，本轮已执行 `dpkg --configure -a` 完成配置。
- `apt-get -f install -y` 结束时为 `0 upgraded, 0 newly installed, 0 to remove and 325 not upgraded`。
- `apt-get install -y ros-humble-slam-toolbox` 完成，包含 `ros-humble-nav2-map-server`、`ros-humble-nav2-util`、`ros-humble-slam-toolbox` 等依赖。
- `ros2 pkg prefix slam_toolbox` 返回 `/opt/ros/humble`。
- 状态检查前后均未看到需要等待的 apt/dpkg 锁；本轮没有留下远端 apt/dpkg 长任务。

远端 no-motion proof 结论：

```bash
ssh root@192.168.1.11 -p 37878 'bash -lc '\''set -e; source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; set -u; timeout 8 ros2 topic echo --once /scan || true; timeout 12 ros2 topic echo --once /map || true; curl -fsS -X POST http://127.0.0.1:8787/api/map/proof/refresh || true; echo; curl -fsS http://127.0.0.1:8787/api/map/proof/latest || true; echo; test -f /root/rober/onboard/runtime/map_lifecycle_latest.json && cat /root/rober/onboard/runtime/map_lifecycle_latest.json || true; find /root/rober/onboard/runtime/maps -maxdepth 2 -type f 2>/dev/null | sort | tail -n 20 || true'\'' '
```

结果摘要：

- 命令开头的常驻 graph 检查仍显示 `/scan`、`/map` 未常驻发布：`topic ... does not appear to be published yet`。
- `POST /api/map/proof/refresh` 已不再 405，helper 启动短窗口 runtime。
- runtime topic list 包含 `/lidar/raw_packet`、`/map`、`/map_metadata`、`/scan`、`/tf`、`/tf_static`、`/slam_toolbox/*`。
- `/scan` once 成立：frame_id `laser_frame`，range sample `5.7144999504089355`。
- `/map` once 成立：frame_id `map`，metadata `resolution=0.05`、`width=6`、`height=116`。
- `/trashbot/save_map` 返回 `success=True, message='Map saved to runtime/maps/trashbot_map.pgm'`。
- 命令末尾 `find /root/rober/onboard/runtime/maps` 确认：
  - `/root/rober/onboard/runtime/maps/trashbot_map.pgm`
  - `/root/rober/onboard/runtime/maps/trashbot_map.yaml`
- `/api/map/proof/latest` HTTP 200，artifact `runtime/map_lifecycle_latest.json` loaded；该 artifact 曾因 helper 相对路径枚举 false-negative 标记 `status=blocked_with_root_cause`、`root_causes=[file path/permissions: map_save_reported_success_but_no_artifact_files_found]`，本轮已修 helper 路径解析，但按用户状态检查要求没有再跑第四次远端长 proof。

本地软件护栏：

```bash
python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py
python3 -m compileall -q onboard/scripts onboard/src
python3 -m unittest discover -s onboard/scripts -p 'test_*.py'
```

结果：

- launch 静态合同：`Ran 12 tests in 0.098s`，`OK`。
- compileall：通过，无输出。
- upper API scripts：`Ran 83 tests in 4.526s`，`OK (skipped=3)`。

当前 root cause 状态：

- `ROS install/source`：已处理，远端必须继续使用 `bash -lc` source ROS setup；直接 zsh source 仍是错误用法。
- `upper API`：已处理，`POST /api/map/proof/refresh` 已部署且可调用。
- `SLAM install`：已处理，`slam_toolbox` 已安装。
- `SLAM/TF/topic remap`：已处理到能产出 `/map` once；关键修复是 no-motion `odom->base_link` 静态 TF 和显式 `slam_toolbox` frame/topic 参数。
- `map saver/file path`：map saver 已保存文件；helper latest artifact 的文件枚举 false-negative 已在本地修复并等待下一轮短 proof 复验。

安全字段和剩余风险：

- 安全字段仍为 `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`hil_pass=false`。
- 本轮未发布 `/cmd_vel`，未调用 `/api/base/manual`，未发送 WAVE ROVER 底盘命令。
- 当前证明范围是 no-motion `/scan` once、`/map` once、map metadata、PGM/YAML 文件落盘和 8787 readback route 可用。
- 当前仍不证明 continuous radar ready、AMCL、Nav2 lifecycle、路径生成、地图质量可导航、fixed-route 可跑、PC WASD、WAVE ROVER ACK、HIL pass 或真实送达闭环。
