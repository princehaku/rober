# 自动扫图 runtime launch 接入

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
  - 默认启动 `ros2_trashbot_nav/free_roam_autonomy_node`，节点名固定为 `/free_roam_autonomy`。
  - 新增 `free_roam_autonomy_enabled` 和 `free_roam_autonomy_artifact_path` launch 参数。
  - launch 层显式传入 `enable_cmd_vel_publish=False` 与 `motion_hil_unlocked=False`，只写 runtime artifact，不开放 `/cmd_vel`。
- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
  - 同样默认启动 artifact-only 自动扫图 runtime，让常规上车 bringup 后 PC/8787 可读真实门禁。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 新增静态合同测试，锁定 learn/bringup 都能启动 free-roam runtime，且运动发布双锁关闭。
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy_node.py`
  - stop 兜底新增会话门控：默认 artifact-only locked tick 只写门禁，不调用 stop；PC start 后或运动发布解锁后才允许 stop fallback。
- `onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`
  - 更新默认 tick 测试，并新增 active session locked 时调用 stop 兜底的覆盖。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 launch 接入边界：提供 runtime artifact 和门禁，不等同自动发车开放。

## 验证结果

- 通过：`python3 -m py_compile onboard/src/ros2_trashbot_bringup/launch/learn.launch.py onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`。
- 通过：`python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py -k free_roam`。
- 通过：`python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`，结果 `Ran 17 tests ... OK`。
- 通过：`python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py`，结果 `Ran 12 tests ... OK`。
- 通过：`bash onboard/scripts/docker_humble_build.sh`，最终结果 `Summary: 6 packages finished [42.7s]`。Docker build 阶段保留既有 base image platform warning，不影响 colcon 结果。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，`node` 监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮没有在真机上重启 `learn.launch.py` 或 `bringup.launch.py`，因此尚未证明 live 8787 已从 artifact missing 变为 runtime loaded。
- 自动扫图仍不会发布 `/cmd_vel`；真实“像扫地机一样自己跑”还需要现场 HIL 后显式打开 `enable_cmd_vel_publish` 和 `motion_hil_unlocked`。
- 本轮未修改 Clash、系统代理或 PC Node 端口；PC 工作站仍应使用 `7001`。
