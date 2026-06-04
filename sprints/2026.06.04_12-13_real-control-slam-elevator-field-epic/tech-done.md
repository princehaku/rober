# Tech Done: Real Control, SLAM, Elevator Field Epic

## sprint_type

sprint_type: epic

## Full-Stack Worker A follow-up - direct-upper Radar start 真实 UI/API 复现

### 根因

本轮按 systematic debugging 从 App 按钮层和 Express API 路径复现，结论是两类问题叠加：

- 代码路径层面：当前 direct-upper helper 已让 `GET /api/o7/direct-upper/status` 和 `POST /api/o7/direct-upper/radar/start|stop` 在缺 env 时走现场默认 `http://192.168.1.11:8787`，但上一轮只证明了 server helper 的 mocked HTTP contract，缺少 `O7LiveOperatorPanel` 按钮层回归。
- 运行态层面：本机 127.0.0.1:5173 仍有旧 Vite 进程，且 `vite.config.ts` 在插件初始化时执行 `const apiApp = createWorkstationApp()`。旧 dev server middleware 会固定启动时的 server code，不保证 TS server 文件变更后热更新。因此用户页面继续看到 `base_url_not_configured` / `/api/radar/start not_executed`，优先判定为旧 5173 进程仍在服务旧 Express app，而不是 ACK/T=1001 或 `/dev/ttyS5` safety gap。

`robot_ack_not_connected`、`t1001_feedback_not_observed`、`field_evidence_not_proven` 仍是现场 safety/not_proven gaps，必须继续显示；它们不应该导致 Radar start 本机代理 `not_executed`。

### 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `O7DirectUpperApiAdapterInfo`，要求 direct-upper status 和 command envelope 都返回 adapter 指纹。
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
  - 为 status/command 响应加入 `adapter.version=2026-06-04.field-default-radar-v2`、`adapter.source=pc-tools/workstation/src/server/o7DirectUpperApi.ts`、`field_default_enabled=true`、`field_default_url=http://192.168.1.11:8787` 和 dev server reload hint。
  - 保持 Radar start 缺 env 走 `field_default`，上位机失败时仍返回 `upper_request.executed=true` 和真实 `upper_http_<status>`。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - Direct 卡片显示 `adapter` 指纹；缺字段时显示 `stale_dev_server_missing_adapter` 并提示重启 `npm run dev`。
  - Radar/command 结果显示 `source=<upper_api_base_url_source>` 和 `adapter=<adapter.version>`，用于现场截图区分旧 5173 middleware 与真实上位机 HTTP 失败。
- `pc-tools/workstation/src/styles.css`
  - 新增 adapter 指纹样式。
- `pc-tools/workstation/test/App.test.ts`
  - 新增按钮层回归：缺 env、非 fixture、点击 `Radar start`，上位机 `/api/radar/start` 返回 HTTP 503 时，UI 必须显示 `source=field_default`、`adapter=2026-06-04.field-default-radar-v2`、`/api/radar/start HTTP 503`。
  - 断言不得出现 `Radar start 失败：base_url_not_configured`，不得出现 `/api/radar/start not_executed`，并保持 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`。
  - 对连续 operator 按钮测试补等待，避免防连点 disabled guard 导致异步 race。
- `docs/interfaces/o7_direct_upper_pc_api.md`
  - 记录 adapter 指纹、stale Vite dev server 判定规则和 Radar start `executed=true` 失败语义。
- `docs/product/pc_tools_workstation.md`
  - 记录 `vite.config.ts` dev middleware 固定 app 的运行态风险，以及看到旧错误时应重启占用 5173 的旧 `npm run dev` 进程。

未修改 `vite.config.ts`，因为它不在本轮允许改动范围。

### 验证结果

```bash
cd pc-tools/workstation && npm test -- --run
```

结果：通过。

```text
Test Files  3 passed (3)
Tests  97 passed (97)
```

```bash
cd pc-tools/workstation && npm run build
```

结果：通过。

```text
vite v7.3.3 building client environment for production...
dist/index.html                  0.41 kB
dist/assets/index-EBE9rJR4.css  13.79 kB
dist/assets/index-DoWp1Jfx.js   90.75 kB
✓ built in 2.03s
```

```bash
cd pc-tools/workstation && npm run lint
```

结果：通过，ESLint 无报错。

Express app 级 HTTP smoke（随机本机端口，mock 上位机 8787，不访问真实硬件）：

```json
{
  "status": {
    "status": "ready",
    "source": "field_default",
    "adapter": "2026-06-04.field-default-radar-v2",
    "health_executed": true,
    "status_executed": true
  },
  "radar_start": {
    "failure_reason": "upper_http_503",
    "source": "field_default",
    "adapter": "2026-06-04.field-default-radar-v2",
    "path": "/api/radar/start",
    "executed": true,
    "http_status": 503,
    "safe_to_control": false,
    "sends_commands": false,
    "robot_control_executed": false
  }
}
```

### 剩余风险

- 旧 5173 Vite 进程如果仍在运行，用户浏览器仍可能继续看到旧 bundle/旧 Express middleware；必须停止占用 5173 的旧 `npm run dev` 并重启后才会看到 `adapter=2026-06-04.field-default-radar-v2`。
- 本轮没有访问 ROS graph、LiDAR 串口、`/dev/ttyS5` 或 WAVE ROVER JSON，不证明真实 `/scan`、真实 Radar start、SLAM/Nav2、robot ACK、`T=1001`、HIL 或 `safe_to_control=true`。
- `robot_ack_not_connected`、`t1001_feedback_not_observed`、`field_evidence_not_proven` 继续是现场缺口；它们现在只作为锁定原因显示，不再阻止 Radar start HTTP 转发。

## 实际改动

本轮按四个 L2 owner 并行推进，交付范围是 `software_guard`、离线评估和现场准入护栏。不声明真实 PC 控车、真实 LiDAR start/stop、真实 SLAM map、真实 AMCL 定位、真实 Nav2 消费、真实电梯识别、HIL、robot ACK 或 delivery success。

### Worker A - full-stack-software-engineer

实际改动：

- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/styles.css`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`

实现内容：

- PC operator workflow 增加 operator confirmation、fixture mode 和统一 `evidence_ref`。
- WASD/Space/X、Stop、radar start/stop、map start/reset/save/load/list、localize reset、operator report 全部收敛到 PC 同源 direct-upper API。
- `upper_api_base_url_source` 新增 `fixture`。field default `http://192.168.1.11:8787` 只作为 status 和 radar start/stop 的现场 direct HTTP 默认路由；base/manual/stop/feedback、map/localize/report 需要显式 `ROBER_UPPER_API_BASE_URL` 或 operator 明确打开 fixture mode。
- Fixture mode 只生成可回放 command envelope，不执行上位机 fetch；浏览器仍不直连 ROS graph、`/cmd_vel`、`/dev/ttyS5` 或 WAVE ROVER JSON。

验证结果：

- `cd pc-tools/workstation && npm test -- --run`：3 files / 96 tests passed。
- `cd pc-tools/workstation && npm run build`：passed。
- `cd pc-tools/workstation && npm run lint`：passed。
- `git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md`：passed。

剩余风险：

- 本轮不证明真实 PC 控车、真实 radar start/stop runtime、真实 ROS2 runtime、真实 SLAM/AMCL、真实 `/scan`、robot ACK、`T=1001` 或 HIL。
- `docs/interfaces/o7_direct_upper_pc_api.md` 需要同步 direct-upper fixture/default/env 语义，已作为 full-stack follow-up 派发。

### Worker B - robot-software-engineer

实际改动：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/test_upper_robot_api.py`
- `docs/interfaces/o7_upper_robot_api.md`

实现内容：

- 新增 map/localization runtime proof readback：`GET /api/map/proof/latest`、`GET /api/localize/proof/latest`。
- 新增 Nav2 lifecycle 合同：`GET /api/nav2/status`、`POST /api/nav2/start`、`POST /api/nav2/stop`。
- 新增 elevator evidence/status 边界：`GET /api/elevator/status`。
- `/api/status` 汇总 map proof、localization proof、Nav2 lifecycle 和 elevator evidence summary。
- 所有新增入口默认 `software_guard=true`、`not_proven=true`，只读 artifact 或执行显式配置命令；不把 fixture/mock/stub 写成真实 ROS2 runtime、HIL 或 delivery success。

验证结果：

- `python3 -m unittest onboard.scripts.test_upper_robot_api`：Ran 22 tests，OK。
- `python3 -m compileall -q onboard/scripts onboard/src`：passed。
- `git diff --check -- docs/interfaces/o7_upper_robot_api.md onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py`：passed。
- `bash onboard/scripts/docker_humble_build.sh`：未进入 colcon；当前 WSL distro Docker Desktop integration 不可用，`/var/run/docker.sock` 不存在。

剩余风险：

- 未覆盖 Docker/Humble colcon、真实 ROS2 graph、SLAM `/map`、AMCL `/amcl_pose`、TF freshness、Nav2 消费 `/scan`+map、电梯 OpenCV 实景和 HIL。
- 新增 proof artifact 入口需要后续 collector/现场脚本写入真实 runtime 材料后才能转正。

### Worker C - robot-algorithm-engineer

实际改动：

- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/elevator_opencv_baseline.py`
- `onboard/src/ros2_trashbot_vision/test/__init__.py`
- `onboard/src/ros2_trashbot_vision/test/test_elevator_opencv_baseline.py`
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/map_quality_metrics.py`
- `onboard/src/ros2_trashbot_nav/test/__init__.py`
- `onboard/src/ros2_trashbot_nav/test/test_map_quality_metrics.py`
- `pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/**`
- `pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/**`
- `docs/vision/elevator_opencv_baseline.md`

实现内容：

- `elevator_opencv_baseline.py` 新增 taxonomy 样本类、manifest sample coverage、door/safe precision/recall、FP/FN rate、`acceptance_gates.software_guard` 和 `acceptance_gates.field_eval`。
- `map_quality_metrics.py` 新增 map YAML/PGM/waypoints 离线评估，输出 coverage、unknown ratio、waypoint reachability、save/load consistency 和 failure samples。
- 新增可复跑 fixture：电梯 offline eval 与 Nav2/map quality offline eval。
- 文档同步 OpenCV taxonomy、fixture 命令、Nav2/map quality 指标和 `not_proven` 边界。

验证结果：

- `python3 -m compileall -q onboard/src/ros2_trashbot_vision onboard/src/ros2_trashbot_nav pc-tools/evidence`：exit 0。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_vision -p 'test*.py'`：Ran 18 tests，OK。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_nav -p 'test*.py'`：Ran 54 tests，OK。
- 电梯 fixture eval：`evaluated_count=3`，software guard pass，field eval not ready。
- Map quality fixture：fail-closed，reachable waypoint ratio 0.25，failure samples 覆盖 occupied/unknown/out_of_bounds。

偏差和修复：

- 首次 vision discover `Ran 0 tests`，原因是 `test/` 目录不是 Python package；已补 `__init__.py`。
- 一处 coverage 断言低估了“预期门开但规则 uncertain”的样本计数，已修正。

剩余风险：

- 本轮不证明真实相机电梯识别、楼层 OCR、真实进出电梯、ROS2 电梯状态机消费、真实 SLAM map、AMCL 定位或 Nav2 实跑。
- 下一步需要接真实/受控图片 manifest，并由 robot-software 将 OpenCV evidence 接入电梯状态链。

### Worker D - robot-hardware-engineer

已读 vendor 来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
- `docs/vendor/lidar_ros/README.md`

实际改动：

- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`
- `onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`
- `onboard/scripts/o1_lidar_raw_packet_proof_collector.py`
- `onboard/scripts/test_o1_lidar_raw_packet_proof_collector.py`
- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`

实现内容：

- `o1_ttyS5_safe_pulse_acceptance.py` 增加 `--evidence-ref`、默认 evidence ref、manual/stop/post-status/operator report 同一证据链字段。
- Operator report `evidence_ref` mismatch 时运动前 fail-closed，避免把不同现场材料拼成同一 HIL 证据。
- `o1_lidar_raw_packet_proof_collector.py` 默认 LiDAR 口收敛到 vendor udev `/dev/lidar`，并在 open 前拒绝 `/dev/ttyS5`、`/dev/ttyAMA0`、`/dev/serial0`，避免把 LiDAR `A5 60` 写到底盘口。
- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md` 补下一次现场 low-speed pulse/stop/post-status/operator report 证据链 SOP，以及 LiDAR start/stop 串口隔离 SOP。

验证结果：

- `python3 -m compileall -q onboard/scripts`：passed。
- `python3 -m unittest onboard.scripts.test_o1_ttyS5_safe_pulse_acceptance`：Ran 17 tests，OK。
- `python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector`：Ran 5 tests，OK。
- `python3 -m unittest onboard.scripts.test_o1_lidar_raw_packet_proof_collector`：Ran 6 tests，OK。
- Worker D scoped `git diff --check`：passed。

剩余风险：

- 本轮仍不是 HIL pass；未证明 PC WASD 真实控车、LiDAR PC 一键 start/stop、真实 `/scan` 长稳、`T=1001` 同场材料、ROS `/odom`/`/imu/data`/`/battery` 或 `safe_to_control=true`。

## 综合验证

Owner 验证已覆盖各自范围；coordinator 收口阶段只做非侵入式检查、sprint 记录核对和 git 提交，不直接运行构建/测试或硬件 smoke。

已由各 owner 报告通过：

- PC：`npm test -- --run`、`npm run build`、`npm run lint`。
- Upper API：`python3 -m unittest onboard.scripts.test_upper_robot_api`、`python3 -m compileall -q onboard/scripts onboard/src`。
- Vision/Nav：`compileall`、vision 18 tests、nav 54 tests。
- Hardware：scripts `compileall`、safe pulse 17 tests、LiDAR scan collector 5 tests、raw packet collector 6 tests。

Coordinator 验收：

- `git diff --check -- docs onboard pc-tools sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic`：通过。
- `git diff --cached --check`：提交前通过。
- `git status --short` 和 staged diff：提交范围限定在当前 Epic 文件、fixture 和 sprint 收口文档。

## OKR 进度影响

本轮推进 O2/O3/O7/O1 的软件护栏和现场准入，但没有产生 `robot_runtime_material` 或 `field_hil_material`，因此 OKR 完成度不涨：

- O2：约 72%，新增 OpenCV taxonomy/offline fixture eval guard。
- O3：约 73%，新增 map/localization proof routes 和 map quality offline guard。
- O7：约 88%，PC operator workflow 可消费 direct-upper fixture/env contract。
- O1：约 95%，新增 evidence-ref 绑定和 LiDAR/base UART 隔离护栏。
- O5/O6：约 96%，本轮未作为主线。

## 剩余风险

- 未证明真实 PC WASD 控车、真实 LiDAR start/stop、真实 `/scan` runtime、真实 SLAM map、真实 AMCL 定位恢复、真实 Nav2 消费 map+scan、真实电梯识别、楼层 OCR、真实进出电梯、HIL pass、robot ACK 或 `safe_to_control=true`。
- 8787 新端点默认是 dry-run/stub/fail-closed，需要在上位机 `ssh root@192.168.1.11 -p 37878` 环境配置真实 command hook 后，才能产生 `robot_runtime_material`。
- OpenCV baseline 目前只通过 fixture/offline eval，下一步必须接真实电梯图片 manifest，再进入 ROS2 电梯状态链。
- HIL 文档只完成准入边界，真实低速 pulse 和 operator report 仍需现场条件、观察员和急停路径。
