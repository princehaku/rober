# Tech Done: Real Control, SLAM, Elevator Field Epic

## sprint_type

sprint_type: epic

## 实际改动

本轮按四个 L2 owner 并行推进，交付的是 `software_guard` 和可执行接口护栏，不声明真实 PC 控车、真实 LiDAR start/stop、真实 SLAM map、真实定位恢复、真实电梯识别、HIL 或 delivery success。

### Product / OKR Owner

- `OKR.md`
  - 把本轮 Epic 状态从“下一轮必须启动”更新为当前 sprint。
  - 最终收口为 software guard 已交付，O1/O2/O3/O7 完成度不涨。
- `docs/product/elevator_assisted_delivery.md`
  - 补充 2026-06-04 12-13 Epic 的 OpenCV/ROS2 验收边界。
- `sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/pre_start.md`
- `sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/prd.md`
- `sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/tech-plan.md`

### Robot Software Engineer

- `onboard/scripts/upper_robot_api.py`
  - 新增 `POST /api/radar/start`、`POST /api/radar/stop`。
  - 新增 `POST /api/map/start|reset|save|load`、`GET /api/map/list`、`POST /api/localize/reset`。
  - 新增 `ROBER_RADAR_START_COMMAND`、`ROBER_MAP_SAVE_COMMAND`、`ROBER_LOCALIZE_RESET_COMMAND` 等 env/CLI command hook。
  - 默认返回 `status=not_proven`、`software_guard=true`、`safe_to_control=false`、`robot_control_executed=false`。
  - 雷达控制明确只属于 LiDAR/ROS2 driver scope，不触碰 `/dev/ttyS5`、`/api/base/manual`、`/cmd_vel` 或 WAVE ROVER motion commands。
- `onboard/scripts/test_upper_robot_api.py`
  - 覆盖新 route、fail-closed payload、radar/base 串口隔离和 status route exposure。
- `docs/interfaces/o7_upper_robot_api.md`
  - 同步 8787 新合同、env switches、artifact path 和 proof boundary。

### User Touchpoint Full-Stack Engineer

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
- `pc-tools/workstation/src/styles.css`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/o5o6UpperSshCollector.test.ts`
- `docs/product/pc_tools_workstation.md`
  - PC workstation 新增 direct-upper radar start/stop、map start/reset/save/load/list、localize reset、operator report 的同源代理和 UI 控件。
  - 浏览器仍不直连 ROS graph，不直接打开串口，不把 HTTP 200 写成 robot ACK、SLAM map、定位恢复或 HIL pass。
  - UI 展示 blocked/not_proven、failure_reason、evidence_ref 和 operator report 入口。

### Robot Algorithm Engineer

- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/elevator_opencv_baseline.py`
  - 新增 `trashbot.elevator_opencv_baseline.v1` 输出 schema。
  - 覆盖门线/门缝、轿厢内外、floor ROI、target floor candidate、safe_to_exit、confidence、`uncertain_reasons` 和 `not_proven`。
  - 支持 manifest 真实图片目录输入；无 `cv2` 时支持 PGM fixture，JPEG/PNG 保留 OpenCV 读取入口。
  - 新增 `evaluate_manifest()` 输出 `trashbot.elevator_offline_eval.v1`，包含 FP/FN/uncertain 和 operator summary。
- `onboard/src/ros2_trashbot_vision/test/test_elevator_opencv_baseline.py`
  - 覆盖门开、门关、不可判定、manifest eval、CLI 输出和 `not_proven` 边界。
- `docs/vision/elevator_opencv_baseline.md`
  - 记录 taxonomy、manifest 格式、ROI/rule、offline eval artifact、最小真实采集样本要求和风险边界。

### Hardware Infra Engineer

- `docs/hardware/o1_pc_manual_lidar_hil_boundary.md`
  - 根据本地 vendor 来源写清 WAVE ROVER `/dev/ttyS5 @115200` 与 LiDAR `/dev/lidar` 或 `/dev/ttyACM0 @150000` 的隔离。
  - 明确 LiDAR `A5 60` start 和 `A5 00 A5 65 A5 65` stop 不得触碰底盘 UART。
  - 补齐 PC manual HIL 准入、operator report schema、低速短 pulse、stop-first 和 `T=1001` 证据边界。

## 验证结果

- `git diff --check -- OKR.md sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic docs/product/elevator_assisted_delivery.md`
  - 通过。
- `rg -n "sprint_type: epic|OKR 最低优先级核对|O2|O3|O7|O1|验收命令|文件范围|ssh root@192.168.1.11" sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic OKR.md`
  - 通过。
- `python3 -m unittest onboard.scripts.test_upper_robot_api`
  - `Ran 20 tests in 1.368s`，`OK`。
- `python3 -m compileall -q onboard/scripts onboard/src pc-tools/evidence`
  - 通过。
- `cd pc-tools/workstation && npm test -- --run`
  - `3 passed (3)`，`92 passed (92)`。
- `cd pc-tools/workstation && npm run build`
  - 通过，Vite built successfully。
- `cd pc-tools/workstation && npm run lint`
  - 通过。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test -p 'test*.py'`
  - `Ran 18 tests in 1.052s`，`OK`。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_nav/test -p 'test*.py'`
  - `Ran 52 tests in 5.158s`，`OK`。
- `python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector onboard.scripts.test_o1_lidar_raw_packet_proof_collector`
  - `Ran 9 tests in 0.907s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 bash onboard/scripts/run_smoke_tests.sh`
  - interfaces：`Ran 6 tests`，`OK`。
  - hardware：`Ran 68 tests`，`OK`。
  - nav：`Ran 52 tests`，`OK`。
  - bringup：`Ran 11 tests`，`OK`。
  - behavior：`Ran 841 tests in 581.578s`，`OK`。
  - vision：`Ran 18 tests`，`OK`。
- `git diff --check -- OKR.md docs onboard pc-tools sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic`
  - 通过。

## 偏差和修复

- Robot Software 首次 unittest 触发 camera proxy 依赖，已把对应测试改成 stub `camera_health()`，因为该测试目标是 route/status exposure，不是 camera proxy。
- Full-stack 首次 build/lint 曾失败于未使用 test import 和既有 `.mjs` 测试导入的 TS 指令漂移，已由 worker 小范围修正。
- Full smoke behavior 包运行约 10 分钟，期间出现一次 ResourceWarning 文本，但最终 `Ran 841 tests` / `OK`，本轮记录为残余观察项，不影响通过结论。

## 剩余风险

- 未证明真实 PC WASD 控车、真实 LiDAR start/stop、真实 `/scan` runtime、真实 SLAM map、真实 AMCL 定位恢复、真实 Nav2 消费 map+scan、真实电梯识别、楼层 OCR、真实进出电梯、HIL pass、robot ACK 或 `safe_to_control=true`。
- 8787 新端点默认是 dry-run/stub/fail-closed，需要在上位机 `ssh root@192.168.1.11 -p 37878` 环境配置真实 command hook 后，才能产生 `robot_runtime_material`。
- OpenCV baseline 目前只通过 fixture/offline eval，下一步必须接真实电梯图片 manifest，再进入 ROS2 电梯状态链。
- HIL 文档只完成准入边界，真实低速 pulse 和 operator report 仍需现场条件、观察员和急停路径。
