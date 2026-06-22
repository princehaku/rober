# sprint_type: micro

## 实际改动

- 上位机 `onboard/scripts/upper_robot_api.py` 新增送达完成 gate：
  - `POST /api/delivery/complete` 合成最近 Nav2 goal execution latest 与 operator report latest。
  - `GET /api/delivery/latest` 只读最近 gate artifact。
  - artifact 默认写入 `/root/rober/onboard/runtime/delivery_completion_latest.json`。
- 送达 gate 的成功条件保持保守：必须显式 `confirm_delivery_completion=true`，最近 Nav2 `goal_succeeded`、`goal_accepted=true`、`result_received=true`、`result_status=succeeded`，最近 operator report `ready_for_review`，并且现场材料包含 observed motion/stop、nested delivery success claim、route/map ref 和外部视频或可见相机 ref；任一缺失都返回 `delivery_success=false` 和 `missing_required_material`。
- PC workstation 新增固定代理 `POST /api/robot-control/delivery/complete?baseUrl=...`，只转发到上位机 `/api/delivery/complete`，不暴露任意 endpoint，不发送 Nav2 goal、manual、stop、`/cmd_vel` 或底盘串口命令。
- `RobotControlConsolePanel` 的默认关闭 `高级诊断 -> Nav2 规划详情` 新增 `确认送达（高级）` 表单和 gate readback。普通首屏保持简易风格，不出现送达确认、HIL、proof、Nav2 goal 或 raw key values。
- `onboard/tests/test_upper_robot_api.py` 新增 delivery completion gate 单测，覆盖缺现场材料 blocked 和材料齐备 success 两条路径。
- 更新 `docs/interfaces/ros_runtime_contracts.md` 与 `docs/product/pc_tools_workstation.md`，明确 Nav2 goal succeeded 不等于送达成功；delivery success 只能由 delivery completion gate 在材料齐备时给出。

## 验证结果

- 本地：
  - `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py` 通过。
  - `python3 -m unittest onboard.tests.test_upper_robot_api` 通过，36 tests。
  - `cd pc-tools/workstation && npm test` 通过，99 tests。
  - `cd pc-tools/workstation && npm run lint` 通过。
  - `cd pc-tools/workstation && npm run build` 通过。
  - `git diff --check` 通过。
  - `bash onboard/scripts/docker_humble_build.sh` 通过，`Summary: 6 packages finished [1min 45s]`。
- 上车机：
  - `scp` 部署 `upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/`，远端 `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py.next` 通过。
  - 重启后进程为 `python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`。
  - `GET http://192.168.1.11:8787/api/delivery/latest` 在 artifact 缺失时返回 HTTP 404 语义 payload，`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
- 真实 PC proxy smoke：
  - direct upper 请求：`POST http://192.168.1.11:8787/api/delivery/complete`，body 含 `confirm_delivery_completion=true` 与 `delivery_evidence_ref=delivery-gate-smoke-20260622`。
  - direct upper 返回 HTTP 200，`status=blocked_missing_delivery_material`、`delivery_success=false`。
  - PC 代理请求：`POST http://127.0.0.1:8787/api/robot-control/delivery/complete?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`。
  - PC 代理返回 HTTP 200，`proxy_status=completion_forwarded`、`status=loaded_fail_closed_summary`、`proof_status=not_proven`、`delivery_success=false`、`remote_http_status=200`、`hard_dangerous_true_fields=[]`。
  - `GET http://192.168.1.11:8787/api/nav2/goal/execution/latest` 仍读回上一轮真实 Nav2 材料：`status=goal_succeeded`、`evidence_ref=o11-nav2-goal-execution-1782099547218`。
  - `GET http://192.168.1.11:8787/api/delivery/latest` 读回本轮 gate artifact：`status=blocked_missing_delivery_material`、`delivery_success=false`，缺项为 `operator_report_latest_http_200`、`operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop`、`structured_hil_claims.delivery_success`、`structured_hil_claims.real_route_map_proven`、`structured_hil_claims.route_map_ref`、`external_video_or_visible_camera_ref`。

## 剩余风险

- 本轮实现的是送达完成的证据 gate，不伪造真实投放结果；当前真实上车机 smoke 已证明 gate 可用且正确 blocked，但还没有现场 operator report 材料，因此 `delivery_success` 没有翻 true。
- PC 键盘连续手控仍未在本轮实现；现有能力仍是受限 first-jog/manual/stop 与高级 Nav2 目标执行。
