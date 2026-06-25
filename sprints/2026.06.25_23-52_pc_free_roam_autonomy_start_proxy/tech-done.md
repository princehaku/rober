# 2026.06.25 23:52 PC 自动扫图 start/stop 固定代理

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`：新增固定 `POST /api/free-roam/autonomy/start` 与 `POST /api/free-roam/autonomy/stop`。start 要求 `confirm_operator_safety=true` 和 `confirm_mapping_active=true`，只通过 `ros2 param set /free_roam_autonomy ...` 设置状态机参数；stop 随时可请求状态机停止。
- `pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/src/client/workstationApi.ts`、`pc-tools/workstation/src/shared/contracts.ts`：新增 PC 固定代理 `/api/robot-control/free-roam/autonomy/start|stop`，白名单 body 只有两个确认布尔值，响应固定保留 fail-closed proof flags。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `自动扫图` 按钮在 readiness ready、安全确认、地图记录、地图刷新、雷达运行和停止可用时调用固定 start 代理；未满足时仍跳到下一步。新增 `停止自动扫图` 按钮请求状态机 stop。
- `onboard/tests/test_upper_robot_api.py`、`pc-tools/workstation/test/App.test.ts`：覆盖缺确认不执行、start 不触碰 `enable_cmd_vel_publish/motion_hil_unlocked/cmd_vel_topic`、PC 只调用固定 start 代理且不调用 manual/Nav2/`/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`、`docs/product/pc_tools_workstation.md`：同步自动扫图 start/stop 代理边界。

## 验证结果

- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_upper_robot_api.py -k free_roam`
- 通过：`npm test -- -t "free-roam autonomy"`
- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`
- 通过：`npm run lint`
- 通过：`npm run build`
- 通过：`npm test`（2 test files，176 passed）
- 通过：`git diff --check`

## 剩余风险

- 本轮没有在真实上位机调用 `/api/free-roam/autonomy/start|stop`，也没有做真车自动扫图 HIL。
- start 只设置状态机参数；真实运动发布仍依赖上车端 `enable_cmd_vel_publish=true` 且 `motion_hil_unlocked=true`，本轮没有改变这两个锁。
