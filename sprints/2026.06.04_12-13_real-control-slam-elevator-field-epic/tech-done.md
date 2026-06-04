# Tech Done: Real Control, SLAM, Elevator Field Epic

## sprint_type

sprint_type: epic

## Hardware/O1 scoped 收口 - safe pulse evidence_ref 与 LiDAR UART 隔离

### 验收目标

本次只验收 Hardware/O1 允许范围：safe pulse evidence-ref 绑定、operator report
mismatch/missing fail-closed、LiDAR raw packet collector 默认 `/dev/lidar` 且拒绝底盘
UART、LiDAR scan proof 只读边界、HIL 文档 vendor 来源与安全边界一致。不执行真实运动
命令，不打开真实串口，不声明 HIL。

### 已读 vendor 来源

- `AGENTS.md`、`OKR.md`、`docs/vendor/VENDOR_INDEX.md`。
- WAVE ROVER：`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、
  `config.yaml`、`WAVE_ROVER_V0.9/json_cmd.h`、`uart_ctrl.h`、`movtion_module.h`。
- LiDAR：`docs/vendor/lidar_pkg_ros2-main/README.md`、`src/lidar_node.cpp`、
  `config/lidar_params.yaml`、`launch/lidar.launch.py`、`scripts/99-lidar.rules`。
- 历史 raw packet 参考：`docs/vendor/lidar_ros/README.md`、
  `docs/vendor/lidar_ros/src/lidar_pkg/scripts/lidar_driver.py`。

### 实际修补

- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`
  - 执行模式下 operator report 不仅要通过 preflight，还必须显式携带与 runner 相同的
    `evidence_ref`。
  - `operator_report_evidence_ref_missing` 和 `operator_report_evidence_ref_mismatch`
    都在 `/api/base/manual` 前 fail-closed，保持 `safe_to_control=false`、
    `hil_pass=false`。
- `onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`
  - 更新执行模式测试统一绑定 `BOUND_EVIDENCE_REF`。
  - 新增缺失 `evidence_ref` 的 operator report 阻断回归，断言只 GET `/api/status`，
    不 POST `/api/base/manual`。
- `onboard/scripts/o1_lidar_raw_packet_proof_collector.py`
  - raw collector 继续默认 `/dev/lidar @150000`。
  - 在 open 前对传入 port 做 raw/normpath/realpath 候选检查，拒绝 `/dev/ttyS5`、
    `/dev/ttyAMA0`、`/dev/serial0` 及其规范化别名，避免把 LiDAR `A5 60` 写到底盘 UART。
- `onboard/scripts/test_o1_lidar_raw_packet_proof_collector.py`
  - 新增 `/dev/../dev/ttyS5` 这类别名在 open 前被拒绝的回归。
- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`
  - 同步 operator report `evidence_ref` 缺失/不一致均阻断 manual POST 的准入口径。
  - 同步 raw collector 对规范化底盘 UART 别名 fail-closed 的安全边界。

### 验证结果

```bash
python3 -m unittest onboard.scripts.test_o1_ttyS5_safe_pulse_acceptance
```

结果：通过，`Ran 18 tests in 0.421s`，`OK`。

```bash
python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector
```

结果：通过，`Ran 5 tests in 0.666s`，`OK`。

```bash
python3 -m unittest onboard.scripts.test_o1_lidar_raw_packet_proof_collector
```

结果：通过，`Ran 7 tests in 0.258s`，`OK`。

```bash
git diff --check -- onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/o1_lidar_raw_packet_proof_collector.py onboard/scripts/test_o1_lidar_raw_packet_proof_collector.py docs/hardware/o1_pc_manual_lidar_hil_boundary.md sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic
```

结果：通过，exit 0，无输出。

### 剩余风险

- 本轮只做 fake/unit 和 diff check，不访问真实 `/dev/ttyS5`、`/dev/lidar`、
  `/dev/ttyACM0`、8787 现场 API 或 ROS graph。
- 不证明 PC WASD 真实控车、LiDAR one-click 真实启动、`T=1001` 同场、robot ACK、
  ROS `/odom`/`/imu/data`/`/battery`、HIL pass、`safe_to_control=true` 或送达闭环。
- 下一次真实 low-speed pulse 仍必须按
  `docs/hardware/o1_pc_manual_lidar_hil_boundary.md` 执行 stop-first、同一
  `evidence_ref`、operator report 和 post-status 采证。

## Robot Software field follow-up - 8787 Radar start 405 收口

### 根因

按 systematic debugging 先复现再查远端进程：

- 复现：`POST http://192.168.1.11:8787/api/radar/start` 返回
  `HTTP/1.1 405 Method Not Allowed`，`Allow: OPTIONS`；同机
  `GET /api/radar/status` 返回 200，说明 8787 在线且 radar status route 存在。
- SSH 只读确认：`ss -ltnp "sport = :8787"` 显示 PID `7055`，
  `systemctl status trashbot-upper-robot-api.service` 显示服务运行
  `python3 /root/rober/onboard/scripts/upper_robot_api.py`，已运行约 14 小时。
- 远端脚本 `/root/rober/onboard/scripts/upper_robot_api.py` 的 sha256 为
  `257af64793e08a866a3df80e929e76afd2f1d90d85caab35fd09fe1fc7912735`，
  `ROUTE_PATHS` 里只有 `radar_status`、`radar_scan_proof_latest`、
  `radar_raw_packet_proof_latest`，没有 `radar_start/radar_stop`；
  router grep 也只看到 camera/base POST 注册，没有
  `app.router.add_post(ROUTE_PATHS["radar_start"], radar_start)`。

结论：PC workstation 已经把 Radar start 转发到远端，但远端 8787 仍运行旧版
`upper_robot_api.py`，旧脚本没有 `POST /api/radar/start` route，aiohttp 因只匹配到
全局 `OPTIONS` 返回 405。

### 远端动作

- 本地先验证当前脚本可部署：
  - `python3 -m unittest onboard.scripts.test_upper_robot_api`：通过，
    `Ran 23 tests in 1.710s`，`OK`。
  - `python3 -m compileall -q onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py`：
    通过，无输出。
- 通过 `scp -P 37878` 将当前
  `onboard/scripts/upper_robot_api.py` 同步到远端临时文件
  `/root/rober/onboard/scripts/upper_robot_api.py.new`。
- 远端执行 `python3 -m py_compile onboard/scripts/upper_robot_api.py.new` 通过后，
  备份旧脚本为 `upper_robot_api.py.bak-<timestamp>`，再替换同路径脚本。
- 重启 `trashbot-upper-robot-api.service`；新服务 PID 为 `24105`，
  运行命令仍是 `python3 /root/rober/onboard/scripts/upper_robot_api.py ...`。
- 部署后远端脚本 sha256 与本地一致：
  `ab0af3d6b27bc467571e2f8eff5437f226f205650b4a19a277406dc70d947a41`。
- 部署后远端 grep 已看到：
  - `ROUTE_PATHS["radar_start"] = "/api/radar/start"`
  - `ROUTE_PATHS["radar_stop"] = "/api/radar/stop"`
  - `async def radar_start(...)`
  - `app.router.add_post(ROUTE_PATHS["radar_start"], radar_start)`

本次没有配置 `ROBER_RADAR_START_COMMAND`，没有启动 ROS2/LiDAR driver，没有打开
`/dev/ttyACM0`，没有触碰 `/dev/ttyS5`，没有发送 WAVE ROVER JSON、`T=1/T=130`
或 `/cmd_vel`。

### 验证结果

远端 Radar start：

```bash
curl -i -sS -X POST http://192.168.1.11:8787/api/radar/start \
  -H 'Content-Type: application/json' \
  -d '{"evidence_ref":"robot-software-radar-start-smoke"}'
```

结果：不再 405，返回 `HTTP/1.1 200 OK` JSON object。关键字段：

```json
{
  "schema": "trashbot.upper_robot_api.v1.radar_control_result",
  "action": "radar_start",
  "endpoint": "/api/radar/start",
  "status": "not_proven",
  "software_guard": true,
  "configured_command": {
    "env": "ROBER_RADAR_START_COMMAND",
    "configured": false,
    "mode": "dry_run_stub"
  },
  "command_result": {
    "mode": "dry_run_stub",
    "executed": false,
    "reason": "no_command_configured"
  },
  "sends_base_motion_commands": false,
  "uses_base_uart": false,
  "base_uart_touched": false,
  "safe_to_control": false,
  "robot_control_executed": false
}
```

PC 代理 Radar start：

```bash
curl -sS -X POST http://127.0.0.1:5173/api/o7/direct-upper/radar/start \
  -H 'Content-Type: application/json' \
  -d '{"evidence_ref":"robot-software-pc-radar-start-smoke"}'
```

结果：PC 代理不再收到上位机 405，关键字段：

```json
{
  "adapter": {
    "version": "2026-06-04.field-default-radar-v2"
  },
  "upper_request": {
    "path": "/api/radar/start",
    "method": "POST",
    "executed": true,
    "ok": true,
    "http_status": 200,
    "failure_reason": ""
  },
  "upper_api_base_url_source": "field_default",
  "failure_reason": "none",
  "safe_to_control": false,
  "sends_commands": false,
  "robot_control_executed": false
}
```

`journalctl -u trashbot-upper-robot-api.service -n 20` 显示服务在
2026-06-04 14:23:56 CST 正常 stop/start，新日志只有
`upper_robot_api_started`，没有启动失败或异常栈。

### 剩余风险

- `/api/radar/start not_executed/base_url_not_configured/405` 已消失：远端 POST 已是
  HTTP 200，PC 代理 `upper_request.executed=true`、`http_status=200`、
  `failure_reason=none`。
- 当前仍是 `software_guard`：远端未配置 `ROBER_RADAR_START_COMMAND`，所以只证明
  HTTP route 和 fail-closed JSON 合同恢复，不证明真实 LiDAR/ROS2 driver 已启动。
- 真实转正还需要后续配置 LiDAR/ROS2 driver command hook，并采集 `/scan` once、
  `/scan` hz、必要日志和 artifact；这仍不能触碰底盘 `/dev/ttyS5` 或 WAVE ROVER
  运动指令。

## Algorithm follow-up - O2/O3 offline artifact 复跑验收

### 验收目标

本次 follow-up 只验收 Algorithm/O2/O3 范围：OpenCV 电梯 taxonomy、ROI/rule
baseline、offline eval、Nav2 map quality metrics、fixture artifact 复跑入口、测试
discover 稳定性和 docs 同步。验收边界保持 `software_guard`，不声明真实电梯图片、
真实 SLAM map、AMCL、Nav2 runtime 或现场路线完成。

### 实际修补

- `pc-tools/evidence/fixtures/elevator_opencv_baseline_offline_eval/software_guard_summary.json`
  - 补 `expected_exit_code=0`，方便 evidence runner 区分电梯 fixture 的正常通过。
- `pc-tools/evidence/fixtures/nav2_map_quality_offline_eval/software_guard_summary.json`
  - 补 `expected_exit_code=1` 和 fail-closed 原因，明确该 fixture 预期因 waypoint
    reachability gate 未通过而返回非 0，不是脚本崩溃。
- `docs/navigation/nav2_map_quality_metrics.md`
  - 新增 Nav2 map quality 专页，记录真实 map artifact 切换入口、输出字段、fixture
    复跑命令、预期 `exit_code=1` 和 O3 not_proven 边界。
- `docs/vision/elevator_opencv_baseline.md`
  - 补导航侧文档链接，避免 map quality 指标只落在 vision 文档里。

### 复跑结果

```bash
python3 -m compileall -q onboard/src/ros2_trashbot_vision onboard/src/ros2_trashbot_nav pc-tools/evidence
```

结果：通过，exit 0。

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_vision -p 'test*.py'
```

结果：通过。

```text
Ran 18 tests in 1.046s
OK
```

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_nav -p 'test*.py'
```

结果：通过。

```text
Ran 54 tests in 5.974s
OK
```

```bash
git diff --check -- onboard/src/ros2_trashbot_vision onboard/src/ros2_trashbot_nav pc-tools/evidence docs/vision/elevator_opencv_baseline.md sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic
```

结果：通过，exit 0。

Fixture artifact 额外复跑：

- 电梯 OpenCV manifest eval：exit 0，`evaluated_count=3`，
  `software_guard.pass=true`，`field_eval.pass=false`，
  `field_eval_status=needs_real_image_manifest`。
- Nav2 map quality fixture：预期 exit 1，JSON 正常输出，
  `software_guard_pass=false`，`reachable_ratio=0.25`，
  failure samples 覆盖 occupied、unknown、out_of_bounds。

### 失败定位

没有出现需要修代码的测试失败。唯一需要修补的是证据解释缺口：Nav2 map quality
fixture 的非 0 退出码是预期 fail-closed，但 summary 和导航文档未明确写出，容易被
后续 evidence runner 或人工验收误判为命令异常。

### 剩余风险

- OpenCV baseline 仍未接真实/受控电梯图片 manifest，不证明真实门状态、楼层 OCR、
  safe exit 或跨楼层送达。
- Map quality helper 仍是 ROS-free 离线过滤，不证明真实 SLAM `/map`、map artifact、
  AMCL pose、TF freshness、Nav2 消费 `/scan`+map 或固定路线实跑。
- 下一步 Algorithm 可涨分抓手是接真实图片 manifest 与真实 map artifact，而不是继续
  增加 fixture 数量。

## Full-Stack Worker A follow-up - direct-upper Radar start 按钮层/UI API 复现

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
  - 保持 Radar start 缺 env 走 `field_default`，上位机失败时仍返回 `upper_request.executed=true` 和实际 `upper_http_<status>`。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - Direct 卡片显示 `adapter` 指纹；缺字段时显示 `stale_dev_server_missing_adapter` 并提示重启 `npm run dev`。
  - Radar/command 结果显示 `source=<upper_api_base_url_source>` 和 `adapter=<adapter.version>`，用于现场截图区分旧 5173 middleware 与上位机 HTTP 失败。
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

## Full-Stack/O7 scoped acceptance - PC operator workflow / direct-upper contract

本轮按 Full-Stack/O7 文件范围复核 PC operator workflow、direct-upper API、fixture/default/env 语义和文档同步。结论：

- `pc-tools/workstation/src/server/o7DirectUpperApi.ts` 当前保持 `status` 与 `radar start/stop` 缺 env 走 `field_default=http://192.168.1.11:8787`；`base/manual/stop/feedback`、`map/*`、`localize/reset` 和 `operator-report` 仍要求显式 `ROBER_UPPER_API_BASE_URL` 或显式 fixture mode。
- `O7LiveOperatorPanel.vue` 的按钮、WASD/Space/X、Stop、Radar、Map、Localize 和 Operator report 均经 PC 同源 client helper，且需要 `operator confirmation`，不会从浏览器直连 8787、ROS graph、`/cmd_vel`、`/dev/ttyS5` 或 WAVE ROVER JSON。
- `docs/product/pc_tools_workstation.md` 与 `docs/interfaces/o7_direct_upper_pc_api.md` 已同步 adapter 指纹、stale dev server、field default、fixture mode 和 fail-closed/not_proven 边界。
- 本次复核未发现需要在允许代码范围内新增修补的构建、类型、lint 或文档阻塞；仅更新本 `tech-done.md` 验收记录。

验证结果：

- `cd pc-tools/workstation && npm test -- --run`：通过，`Test Files 3 passed (3)`，`Tests 97 passed (97)`。
- `cd pc-tools/workstation && npm run build`：通过，Vite 产物 `dist/assets/index-EBE9rJR4.css` 和 `dist/assets/index-DoWp1Jfx.js` 正常生成，`built in 2.34s`。
- `cd pc-tools/workstation && npm run lint`：通过，ESLint 无输出。
- `git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md docs/interfaces/o7_direct_upper_pc_api.md sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic`：通过。

剩余风险：

- 本轮只完成 PC software guard 和本机同源代理验收，不证明真实 8787 runtime 已部署新端点、真实 PC WASD 控车、真实 Radar start/stop、真实 SLAM/AMCL、真实 Nav2 消费、robot ACK、`T=1001`、HIL 或 `safe_to_control=true`。
- 真实现场浏览器如果仍由旧 5173 Vite middleware 服务，operator 仍需重启占用 5173 的旧 `npm run dev` 后再用 `adapter=2026-06-04.field-default-radar-v2` 复核。

## Full-Stack/O7 live re-smoke - 5173 field_default 复核

### 根因定位

本次按用户反馈重新复现 127.0.0.1:5173 live API。当前监听进程为
`node /mnt/e/rober/pc-tools/workstation/node_modules/.bin/../vite/bin/vite.js --host 127.0.0.1 --host 127.0.0.1`，
PID `63891`。当前 5173 已返回 `adapter.version=2026-06-04.field-default-radar-v2`，
不再是缺 adapter 或缺 field default 的旧 middleware。

结论：本机 live API 当前没有复现 `base_url_not_configured` 或 `/api/radar/start not_executed`。
如果 operator 浏览器仍看到旧错误，优先按 stale Vite/browser cache 处理：重启占用 5173 的旧
`npm run dev` 进程并刷新页面，再以 Direct 卡片的 adapter 指纹为准复核。

### 实际改动

- 未修改 `pc-tools/workstation/src/server/o7DirectUpperApi.ts`、
  `pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  或 `pc-tools/workstation/test/App.test.ts`。现有源码和回归测试已覆盖本轮目标语义。
- 仅补充本 `tech-done.md` live re-smoke 记录。

### 验证结果

```bash
cd pc-tools/workstation && npm test -- --run
```

结果：通过，`Test Files 3 passed (3)`，`Tests 97 passed (97)`。

```bash
cd pc-tools/workstation && npm run build
```

结果：通过，Vite 产物 `dist/assets/index-EBE9rJR4.css`、
`dist/assets/index-DoWp1Jfx.js` 正常生成，`built in 2.10s`。

```bash
cd pc-tools/workstation && npm run lint
```

结果：通过，ESLint 无输出。

Live status smoke：

```json
{
  "status": "ready",
  "upper_api_base_url": "http://192.168.1.11:8787",
  "upper_api_base_url_source": "field_default",
  "adapter": "2026-06-04.field-default-radar-v2",
  "health_request": {
    "path": "/health",
    "executed": true,
    "ok": true,
    "http_status": 200,
    "failure_reason": ""
  },
  "status_request": {
    "path": "/api/status",
    "executed": true,
    "ok": true,
    "http_status": 200,
    "failure_reason": ""
  },
  "safe_to_control": false,
  "robot_ack_connected": false,
  "t1001_observed": false,
  "failure_reason": "none"
}
```

Live Radar start smoke：

```json
{
  "command": "radar_start",
  "upper_api_base_url_source": "field_default",
  "adapter": "2026-06-04.field-default-radar-v2",
  "upper_request": {
    "path": "/api/radar/start",
    "method": "POST",
    "executed": true,
    "ok": true,
    "http_status": 200,
    "failure_reason": ""
  },
  "failure_reason": "none",
  "safe_to_control": false,
  "robot_ack_connected": false,
  "t1001_observed": false,
  "blocked_reasons": [
    "robot_ack_not_connected",
    "t1001_feedback_not_observed",
    "field_evidence_not_proven"
  ],
  "robot_control_executed": false
}
```

### 剩余风险

- 本次 live smoke 只证明 PC 5173 direct-upper 到 8787 Radar start HTTP 执行链恢复；
  不证明真实 LiDAR/ROS2 driver 已启动、`/scan` once/hz 已观察、SLAM/Nav2 已消费雷达、
  PC WASD 已真实控车、robot ACK、`T=1001`、HIL 或 `safe_to_control=true`。
- `safe_to_control=false`、`robot_ack_connected=false`、`t1001_observed=false` 继续保持，
  不得用 Radar start HTTP 200 替代现场材料。

## Hardware/O1 follow-up - T=1001 边界与 Radar start 解耦

### 根因边界

`T=1001 not_observed_after_t130` 的准确含义是：runner 或 probe 已经写出 vendor 非运动
反馈请求 `{"T":130}`，但读取窗口内没有解析到 vendor `T=1001` JSON feedback。它不是
UI refresh 可解决的问题，不是 robot ACK，不是 HIL pass，也不能单独证明底盘不可用。

Radar start/stop 属于 LiDAR/ROS2 driver 链路，不应被底盘 `T=1001` 当作是否 POST 的
前置门。`robot_ack_not_connected`、`t1001_feedback_not_observed`、
`field_evidence_not_proven` 继续作为 safety/HIL/not_proven 展示 blocker，但不得再被包装成
`/api/radar/start not_executed` 或 `base_url_not_configured`。

### 实际改动

- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`
  - `vendor_sources` 补充 `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`，
    明确 `baseInfoFeedback()` / `T=1001` 字段来源。
  - 输出新增 `hardware_boundary`，固定声明 `T=1001` 只是 feedback material、不是页面刷新问题，
    Radar start/stop 不得被 base `T=1001` gate，manual/base 控制仍需 operator/env/ACK/T1001/HIL。
- `onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`
  - 回归断言 vendor source 和 `hardware_boundary` 字段。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 补 `not_observed_after_t130` 的窄口径解释、现场下一步检查和 Radar start/stop 解耦边界。
- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`
  - 补 PC/Radar 卡片可以展示 T1001/HIL blocker，但不能用它阻断 `/api/radar/start|stop` 转发。

### 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino`

### 验证结果

```bash
python3 -m compileall -q onboard/scripts
```

结果：通过，命令无输出。

```bash
python3 -m unittest onboard.scripts.test_o1_ttyS5_safe_pulse_acceptance
```

结果：通过，`Ran 18 tests in 0.364s`，`OK`。

```bash
python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector
```

结果：通过，`Ran 5 tests in 0.598s`，`OK`。

```bash
python3 -m unittest onboard.scripts.test_o1_lidar_raw_packet_proof_collector
```

结果：通过，`Ran 7 tests in 0.246s`，`OK`。

本次没有打开 `/dev/ttyS5`，没有发送 `/api/base/manual`，没有发送 `T=1/T=13/T=130/T=131`，
没有做真实 HIL。

### 剩余风险

- Manual/base 控制仍不能转正，必须继续保留 operator confirmation、显式 env/API 配置、
  stop/post-status、ACK/T1001/HIL 证据边界。
- 下一步如果要消除 `T=1001 not_observed_after_t130`，需要现场核对 ESP32 供电/固件、
  UART TX/RX、目标端口身份、串口占用和 vendor terminal 交叉验证。

## Robot Software Worker B follow-up - O3/O2 proof readback fail-closed 验收修补

### 根因

验收 Robot Software/O3 范围时发现两个护栏缺口：

- `map_list()` 是本地地图 artifact 只读列举，但共用 `software_guard_payload()` 时，只要本地目录存在且 `command_result.ok=true`，响应可能把 `sends_commands` 标为 `true`。这会让 PC/operator 把只读文件扫描误读成上位机已经执行 ROS2/map 命令。
- 现有 upper API 单测覆盖了 map/localize/Nav2/elevator proof artifact 的 loaded fixture readback，但没有直接覆盖 artifact 缺失和坏 JSON 时的 fail-closed 行为。代码实现已有 `404/422` 保守回包，本轮补回归测试，避免后续改动把 readback 变成启动 ROS2 或发送命令。

### 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `software_guard_payload()` 的 `sends_commands` 收紧为“显式配置 command 且执行成功”才为 `true`。
  - 保持显式配置的 radar/map/localize/Nav2 command hook 可作为真实 runtime 切换入口，但只读 `map_list()`、proof readback 和 status summary 不再被误标为发送命令。
- `onboard/scripts/test_upper_robot_api.py`
  - `test_map_list_reads_artifacts_only_and_unified_status_exposes_routes` 新增 `sends_commands=false` 断言。
  - 新增 `test_runtime_artifact_readbacks_missing_and_bad_json_fail_closed`，覆盖 `/api/map/proof/latest`、`/api/localize/proof/latest`、`/api/nav2/status.proof_latest`、`/api/elevator/status.proof_latest` 在 artifact missing 和 bad JSON 时的 `404/422`、`not_proven`、`readback_sends_commands=false`、`starts_ros2=false`、`safe_to_control=false` 和 `robot_control_executed=false`。
- `docs/interfaces/o7_upper_robot_api.md`
  - 补齐 map/localize/Nav2/elevator readback 的 missing、bad JSON、非 object、read_failed 回包语义。
  - 明确 readback 无论 artifact 是否读取成功，都不启动 SLAM、Nav2、OpenCV、电梯状态机、`/initialpose`、`/cmd_vel` 或 WAVE ROVER 串口。

### 验证结果

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
```

结果：通过。

```text
Ran 23 tests in 1.759s
OK
```

```bash
python3 -m compileall -q onboard/scripts onboard/src
```

结果：通过，命令无输出。

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py onboard/src/ros2_trashbot_nav onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_bringup docs/interfaces/o7_upper_robot_api.md docs/product/elevator_assisted_delivery.md sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic
```

结果：通过，命令无输出。

Docker/Humble 额外检查：

```bash
docker info
```

结果：失败于当前 WSL distro 缺 Docker CLI / Docker Desktop WSL integration，未运行 `bash onboard/scripts/docker_humble_build.sh`，因此本轮没有新增 colcon 证据。

```text
The command 'docker' could not be found in this WSL 2 distro.
We recommend to activate the WSL integration in Docker Desktop settings.
```

### 剩余风险

- 本轮仍未覆盖真实 Docker/Humble colcon、真实 ROS2 graph、SLAM `/map`、map artifact、AMCL `/amcl_pose`、TF freshness、Nav2 消费 `/scan`+map、电梯 OpenCV 实景或 HIL。
- 当前修补只把 upper API software guard/readback 语义压实，不把 O3/O2 写成真实 runtime 完成，也不提升 OKR 百分比。

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

- `cd pc-tools/workstation && npm test -- --run`：3 files / 97 tests passed。
- `cd pc-tools/workstation && npm run build`：passed。
- `cd pc-tools/workstation && npm run lint`：passed。
- `git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md`：passed。

剩余风险：

- 本轮不证明真实 PC 控车、真实 radar start/stop runtime、真实 ROS2 runtime、真实 SLAM/AMCL、真实 `/scan`、robot ACK、`T=1001` 或 HIL。
- `docs/interfaces/o7_direct_upper_pc_api.md` 已同步 direct-upper fixture/default/env 语义；真实 runtime 仍需现场 8787 与上车材料复核。

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

## Hardware/O1 scoped closeout - T1001 feedback boundary

运行时间：2026-06-04T07:13:52Z。

### 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

### 已证实硬件结论

- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130` 和 `FEEDBACK_BASE_INFO=1001`；`uart_ctrl.h` 的 `CMD_BASE_FEEDBACK` 分支调用 `baseInfoFeedback()`。
- `ugv_advance.h` 的 `baseInfoFeedback()` 输出 `T=1001`，包含 `L/R/r/p/y/v` 等 vendor feedback 字段，并通过 `Serial.println(...)` 发出。
- `T=1001` 只能作为 vendor feedback material；没有同场 command、stop、post-status、operator report 和现场安全观察时，不得写成 robot ACK、HIL pass 或 `safe_to_control=true`。
- `T=1001 not_observed_after_t130` 表示显式写出 vendor `{"T":130}` 后读取窗口内未观察到 `T=1001`，不是 PC 页面刷新可修复状态。
- `robot_ack_not_connected`、`t1001_feedback_not_observed`、`field_evidence_not_proven` 不应作为 `POST /api/radar/start|stop` 转发前置门；Radar start/stop 属于 LiDAR/ROS2 driver 链路，底盘 feedback 缺口只阻断 manual/base 控制转正。

### 实际改动

- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`：补 `uart_ctrl.h`、`ugv_advance.h` vendor 来源和 `T=1001` 字段来源；明确 radar start/stop 不由底盘 T1001 缺口 gating。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`：补 `ugv_advance.h` 来源，收窄 `not_observed_after_t130` 语义，并明确它只能作为 safety/HIL/not_proven blocker 展示。
- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`：在 runner JSON 中补 `hardware_boundary` 机器字段，固定表达 T1001 是 feedback material、not observed 不是 UI refresh、radar start/stop 不被 base T1001 gating、manual/base 控制仍需 operator/env/ACK/T1001/HIL。
- `onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`：补回归断言，覆盖 `ugv_advance.h` vendor source 和 manual/radar fail-closed boundary 字段。

### 验证结果

```bash
python3 -m compileall -q onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.scripts.test_o1_ttyS5_safe_pulse_acceptance
```

结果：通过，`Ran 18 tests in 0.383s`，`OK`。

```bash
git diff --check -- docs/hardware/o1_pc_manual_lidar_hil_boundary.md docs/hardware/o1_wave_rover_serial_feedback_probe.md onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/tech-done.md
```

结果：通过，无输出。

### 剩余风险

- 本次只做本地编译、fake HTTP 单测、文档和 diff check；没有打开真实串口、没有触碰 `/dev/ttyS5`、没有发送 `T=130/T=1/T=13/T=131`，也没有执行真实运动。
- 仍未证明真实 radar start/stop、真实 LiDAR `/scan` 长稳、PC WASD 真实控车、底盘 HIL、robot ACK、真实 `/odom`、`/imu/data`、`/battery` 或 `safe_to_control=true`。
- 下一步现场履约仍需同一 evidence ref 下采集 low-speed pulse、stop/post-status、至少一组 vendor feedback、operator report 和现场安全记录后，再由 Product/OKR Owner 复核是否可转正。
