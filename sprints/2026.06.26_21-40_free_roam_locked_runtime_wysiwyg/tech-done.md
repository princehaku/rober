# 自动扫图 locked runtime 所见即所得

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py`
  - 调整自动扫图策略优先级：外部停止请求仍最高优先级；其后如果现场确认、地图记录、停止兜底、雷达等门禁存在 blocked，先输出 `locked` 和首个门禁原因。
  - 超时和 unknown 覆盖达标只在门禁已通过的会话中输出 `completed`，避免 PC runtime marker 把未开始状态误读成完成。
- `onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py`
  - 新增回归测试，覆盖 `elapsed_s` 已超时且 `map_unknown_ratio` 已达标，但 `operator_confirmed=false` 时仍必须输出 `locked`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 runtime artifact 的 locked 优先级和 PC 所见即所得边界。

## 验证结果

- 通过：`python3 -m py_compile onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py`。
- 通过：`python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`，结果 `Ran 13 tests ... OK`。
- 通过：`python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`，结果 `Ran 17 tests ... OK`。
- 通过：`bash onboard/scripts/docker_humble_build.sh`，结果 `Summary: 6 packages finished [42.6s]`。Docker build 阶段保留既有 base image platform warning，不影响 colcon 结果。
- 上位机 `192.168.1.11:37878` 已部署：
  - 远端旧文件备份到 `/root/rober/runtime/deploy_backups/free_roam_strategy_20260626_121116`。
  - 远端通过：`python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`，结果 `Ran 13 tests ... OK`。
  - 远端通过：`colcon build --symlink-install --packages-select ros2_trashbot_nav`，结果 `Summary: 1 package finished [7.84s]`。
  - 远端已重启 artifact-only `/free_roam_autonomy`，新进程 PID `109000`。
- 远端 8787 直连验收：`GET /api/free-roam/autonomy/latest` 返回 `latest_result.decision.state=locked`、`reason=还未勾选现场安全确认`、`artifact_only=true`、`cmd_vel_publish_enabled=false`。
- 本机 7001 PC 代理验收：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `safe_command_boundary.free_roam_autonomy=locked`，runtime `state=locked`、`reason=还未勾选现场安全确认`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，`node` 监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 自动扫图仍保持 artifact-only，不发布 `/cmd_vel`；真实自由移动还需要现场 HIL 后显式打开 `enable_cmd_vel_publish` 与 `motion_hil_unlocked`。
- 当前现场 LiDAR 最近障碍约 `0.04m`，PC 正确显示 `obstacle_clear=not_proven`；这不是自动运动通过证明。
- 本轮没有修改 Clash、系统代理或系统端口配置；项目 Node 继续使用 `0.0.0.0:7001`。
