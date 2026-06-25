# Free Roam Autonomy Core

- sprint_type: micro
- time: 2026-06-25 21:07 Asia/Shanghai
- owner: robot-algorithm-engineer
- safe_to_control: false
- real_motion_triggered: false

## 实际改动

- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py`：新增自动扫图策略内核，定义 fail-closed 门禁、低速直行、近障碍原地避让、覆盖停滞原地扫描、超时/覆盖达标停止。
- `onboard/src/ros2_trashbot_nav/setup.py`：注册 `free_roam_autonomy` console script；默认空输入输出 locked JSON，不发布 `/cmd_vel`。
- `onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py`：覆盖默认锁定、门禁通过低速前进、近障碍避让、覆盖停滞换向、超时/覆盖达标停止、雷达过期锁定和 CLI 默认 locked。
- `docs/navigation/free_roam_autonomy.md`、`docs/product/pc_free_roam_mapping_design.md`、`docs/product/pc_tools_workstation.md`：同步自动扫图状态机边界和后续 ROS2 接线顺序。

## 验证结果

- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py`，`Ran 7 tests ... OK`。
- 通过：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_nav/test -p 'test*.py'`，`Ran 62 tests ... OK`。
- 通过：`npm run lint`。
- 通过：`npm test`，`167 passed`。
- 通过：`npm run build`。
- 通过：`python3 onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py --snapshot-json ...`，输出 `state=running`、`linear_x_mps=0.12`、`stop_required=false`。
- 通过：`bash onboard/scripts/docker_humble_build.sh`，`Summary: 6 packages finished [42.8s]`。
- 通过：`git diff --check`。
- 已复原旧 DOM smoke artifact 的 `checked_at` 测试副作用，未把历史证据时间戳带入本次提交。

## 剩余风险

- 这轮没有接真实 `/scan`、`/map` 或 `/cmd_vel`，因此还不能声明小车已经能自主扫图。
- 真车自由跑动仍需要 ROS2 节点接线、stop fallback HIL、雷达避障 HIL、地图覆盖 artifact 和 PC summary 回传。
