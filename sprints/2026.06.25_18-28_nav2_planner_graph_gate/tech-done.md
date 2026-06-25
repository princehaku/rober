# 2026.06.25 18:28 Nav2 planner graph gate

## sprint_type

micro

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：managed no-motion path proof 在 `path_generation_opt_in=true` 时等待 planner 节点进入 ROS graph；新增 `planner_server_observed`、`controller_server_observed`、`planner_server_ready_for_path_generation`、顶层 `managed_runtime_wait_result`。当 planner 节点已被 graph/history 观测到但 lifecycle CLI 超时时，允许只读 `ComputePathToPose` action 自己给出成功、unavailable 或 timeout 证据；仍不启动 controller、BT、NavigateToPose、`/cmd_vel` 或底盘串口。
- `onboard/tests/test_nav2_runtime_proof_helper.py`：新增 wait history 节点观测回归测试，并锁定 planner observed/gate/顶层 wait result 字段。
- `pc-tools/README.md`：同步 Robot Control no-motion path proof 合同，说明 7001 准备行程仍只触发 planner proof，不发车。

## 验证结果

- `python3 -m pytest onboard/tests/test_nav2_runtime_proof_helper.py`：本机 Python 环境缺少 `pytest`，命令失败为 `No module named pytest`，随后改跑同一测试文件的 unittest 入口。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`：通过，`Ran 39 tests in 2.167s OK`。
- 上位机部署：已备份 `/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py.backup_20260625_1828_planner_graph_gate`，覆盖 helper 后 `python3 -m py_compile /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- 真实 PC 7001 no-motion proof refresh：`POST /api/robot-control/nav2/proof/refresh?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=refresh_forwarded`、`remote_http_status=200`、`robot_control_executed=false`、`hard_dangerous_true_fields=[]`、`non_motion_evidence_actions_observed=["starts_ros2"]`、`latest_proof_status=nav2_no_motion_path_generation_runtime_observed`、`path_generation_succeeded=true`、`path_generated=true`、`path_point_count=36`、`path_generation_boundary=explicit_opt_in_compute_path_to_pose_action_no_motion`、`root_causes=[]`。
- 上位机 latest artifact 只读核对：`planner_server_active=true`、`planner_server_observed=true`、`planner_server_ready_for_path_generation=true`、`controller_server_requested=false`、`controller_server_active=false`、`managed_runtime_cleanup_ok=true`、`managed_runtime_wait_result.ok=True`、`managed_runtime_wait_result.boundary=managed_runtime_nodes_observed`、`blockers=[]`。
- `bash onboard/scripts/docker_humble_build.sh`：通过，Docker/Humble `colcon build --symlink-install` 输出 `Summary: 6 packages finished [42.7s]`。

## 剩余风险

- 本轮已证明 no-motion Nav2 planner 能生成路径，但仍没有执行 NavigateToPose、没有证明真实路线执行、底盘运动、delivery success 或 HIL 全链路。
