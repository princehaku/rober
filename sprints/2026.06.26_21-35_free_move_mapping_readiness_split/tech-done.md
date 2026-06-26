# Free move 和建图 readiness 拆分

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py`：自由自助移动不再把地图记录、雷达缺失或雷达过期作为 `blocked` 门禁；这些状态改为 `not_proven`，允许低速自由移动，同时在 reason/gates 里明确“不是可验收建图”。近障碍读数仍会让状态机原地换向，不继续正向速度。
- `onboard/scripts/upper_robot_api.py`：`/api/free-roam/autonomy/start` 现在只强制 `confirm_operator_safety=true`；`confirm_mapping_active` 变成可选事实输入，只决定写给状态机的 `mapping_active`。相机首帧和雷达 fresh 进入 `sensor_readiness.mapping_readiness`，不再阻止运动双锁写入。
- `pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/src/shared/contracts.ts`：PC 固定代理允许 `confirm_mapping_active=false`，并保留 `free_move_ready`、`free_move_without_camera_allowed`、`mapping_readiness` 等字段，避免把“不能建图”误显示成“不能移动”。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `开始自动扫图（低速）` 不再要求地图记录、地图画面刷新或相机首帧；如果尚未启动地图记录，PC 发 `confirm_mapping_active=false`，按钮语义是低速自由移动。`开始扫地式建图` 仍保留相机/雷达所见即所得门禁。
- `docs/product/pc_free_roam_mapping_design.md`、`docs/product/pc_tools_workstation.md`：同步产品口径：自由移动只依赖安全确认、停止兜底和上车双锁；相机/雷达 ready 决定建图 readiness，不决定车能不能低速自助移动。

## 验证结果

- 已按硬件纪律读取 `docs/vendor/VENDOR_INDEX.md`。本轮未修改 WAVE ROVER UART、速度映射、电压、接线或底盘协议；运动链路仍通过既有 ROS2/free-roam 状态机双锁和上车固定参数接口。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api -v`：通过，52 tests。
- `PYTHONPATH=onboard/src/ros2_trashbot_nav python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py -v`：通过，10 tests。
- `cd pc-tools/workstation && npm test -- catalog.test.ts`：通过，105 tests。
- `cd pc-tools/workstation && npm test -- App.test.ts`：通过，137 tests。
- `cd pc-tools/workstation && npm test`：通过，2 files / 242 tests。
- `cd pc-tools/workstation && npm run build`：通过；仅 Vite chunk size warning。
- 已部署：上车 `/root/rober/onboard/scripts/upper_robot_api.py`、`src/ros2_trashbot_nav/.../free_roam_autonomy.py` 和当前运行的 build 路径均已同步；上车 API 重启为 PID `143470`，free-roam 节点重启为 PID `143469`。PC Node 通过 `screen` 绑定 `0.0.0.0:7001`，node PID `34835`。
- Live smoke：PC 7001 `POST /api/robot-control/free-roam/autonomy/start?baseUrl=http://192.168.1.11:8787` 携带 `confirm_operator_safety=true`、`confirm_mapping_active=false` 返回 `proxy_status=autonomy_forwarded`、`remote_http_status=200`、`command_ok=true`、`motion_unlock_requested=true`、`mapping_active_requested=false`、`sensor_ready=true`、`mapping_ready=false`、`mapping_missing=[camera_first_frame_not_observed, radar_scan_proof_not_fresh]`、`blocked_reasons=[]`。
- Live stop 收口：随后 `POST /api/robot-control/free-roam/autonomy/stop` 返回 `proxy_status=autonomy_forwarded`、`command_ok=true`、`motion_unlock_requested=false`；latest 读回 `cmd_vel_publish_enabled=false`、`decision_state=stopping`、`stop_required=true`。

## 剩余风险

- 本轮是软件门禁拆分和 mock/单测验证；还需要真车 HIL 记录来证明 `confirm_mapping_active=false` 时小车确实低速移动、stop 响应可靠、不会误记成建图成果。
- 摄像头首帧仍未修好；因此当前可以自由低速移动，但不可把本轮自动移动解释成可验收建图。
- 雷达缺失时状态机允许低速自由移动，现场必须保持 operator 监看和停止兜底；雷达 ready 后才有障碍距离和地图标记所见即所得证据。
