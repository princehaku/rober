# Free Roam Runtime Summary

- sprint_type: micro
- time: 2026-06-25 21:24 Asia/Shanghai
- owner: full-stack-software-engineer
- safe_to_control: false
- real_motion_triggered: false

## 实际改动

- `onboard/scripts/upper_robot_api.py`：新增 `ROBER_FREE_ROAM_AUTONOMY_ARTIFACT_PATH` / `--free-roam-autonomy-artifact-path`，新增 `GET /api/free-roam/autonomy/latest`，并在 `GET /api/status` 中输出 `free_roam_autonomy` 只读摘要。
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy_node.py`：默认 artifact 路径对齐到 `/root/rober/onboard/runtime/free_roam_autonomy_latest.json`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 optional `free_roam_autonomy_latest` 读回，消费 runtime artifact 的 `decision.gates`，并把 `cmd_vel_publish_enabled=true` 纳入危险字段扫描；旧上位机返回 404/405/501 时降级为 optional missing。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：自动扫图准备在有 runtime gates 时显示上车端门禁口径，不再只显示静态 watchdog 缺口。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/src/shared/contracts.ts`：更新合同、首屏断言和旧上位机 optional endpoint 兼容测试。
- `docs/navigation/free_roam_autonomy.md`、`docs/product/pc_free_roam_mapping_design.md`、`docs/product/pc_tools_workstation.md`：同步读回链路和按钮仍锁定边界。

## 验证结果

- 已通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy_node.py`。
- 已通过：`npm test -- --testNamePattern "renders Robot Control V1 by default|summary|safe command"`，`22 passed`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_nav/test -p 'test*.py'`，`Ran 66 tests ... OK`。
- 通过：`npm run lint`。
- 通过：`npm test`，`167 passed`。
- 已通过：`npm run build`。
- 通过：`bash onboard/scripts/docker_humble_build.sh`，`Summary: 6 packages finished [42.7s]`。
- 通过：`curl -s http://127.0.0.1:7001/api/robot-control/summary`，确认 `source_base_url=http://192.168.1.11:8787`、`safe_to_control=false`、`free_roam_autonomy=locked`、`free_roam_autonomy_latest` 在旧上位机 405 下显示 `status=missing`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只完成 runtime artifact 到上位机/PC 的只读回传；没有打开 `/cmd_vel`。
- 真车自动扫图仍需要 stop fallback、雷达避障、地图覆盖增长和低速运动 HIL。
