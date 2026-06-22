# Wheel L/R Same-Session First-Jog Proof

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增同串口会话 manual 点动事务：写运动命令、运动窗口内写 `T=130` 并读 `T=1001`、写 stop、停车后再写 `T=130` 并读 `T=1001`。
  - 返回 `serial_motion_transaction`，包含 command、motion feedback request、stop、after-stop feedback request 和 compact frames。
  - `manual_wheel_feedback_summary` 继续只在同一 `T=1001` 帧内 `L/R` 都 finite 且非零时判定 `wheel_feedback_lr_nonzero_proven=true`。
- `onboard/tests/test_upper_robot_api.py`
  - 更新 manual 点动单测，锁定 manual 必须消费同串口会话事务，并保持 safe/delivery/primary actions 为 false。
- `pc-tools/workstation/src/server/index.ts`
  - PC first-jog/manual evidence capture 改为串行固定 GET。
  - 单 evidence endpoint timeout 从 1.5 秒提高到 5 秒，manual POST timeout 提高到 8 秒，避免上位机同步读串口/雷达时互相挤爆。
- `docs/product/pc_tools_workstation.md`
  - 记录 PC first-jog 可复验 wheel raw L/R 非零和剩余 motion gap。
- `docs/hardware/wave_rover_json_bridge.md`
  - 记录 vendor 资料来源、同串口会话证据和新的硬件证据边界。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`
  - 结果：`Ran 34 tests`，`OK`。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/camera_first_frame_probe.py`
  - 结果：通过。
- `cd pc-tools/workstation && npm test`
  - 结果：`2 passed (2)`，`99 passed`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过。

## 真实上位机证据

- 已部署到真实上位机 `root@192.168.1.11:37878`，Robot API 进程 `python3` 监听 `*:8787`，工作目录 `/root/rober`。
- 直连上位机 `POST /api/base/manual`，`direction=forward`、`speed=0.12`、`duration_ms=800`：
  - `manual_command_executed=true`
  - `auto_stop_executed=true`
  - 运动窗口 compact frames 包含 `{"T":1,"L":0.12,"R":0.12}`、`{"T":130}`、`{"T":1001,"L":61,"R":61,...}`。
  - 停车后 compact frames 包含 `{"T":1,"L":0,"R":0}`、`{"T":130}`、`{"T":1001,"L":0,"R":0,...}`。
  - `wheel_feedback_lr_nonzero_proven=true`。
- PC first-jog `POST /api/robot-control/base/first-jog?baseUrl=http://192.168.1.11:8787`，`direction=forward`、`speed=0.04`、`duration_ms=800`：
  - `proxy_status=command_forwarded`
  - `remote_http_status=200`
  - `remote_motion_key_values.wheel_feedback_lr_nonzero_proven=true`
  - `wheel_feedback_latest_left_speed=20`
  - `wheel_feedback_latest_right_speed=20`
  - `evidence_capture_status=captured`
  - `motion_evidence_gaps=["physical_motion_lidar_delta_not_proven"]`

## 证据文件

- `artifacts/01_upper_manual_samesession_012.json`
- `artifacts/02_pc_first_jog_samesession_timeoutfix.json`
- `artifacts/03_base_status_after_pc_jog.json`

## 剩余风险

- `physical_motion_lidar_delta_not_proven` 仍出现在本轮 PC first-jog response 中；历史 scan-delta artifact 仍存在，但当前 PC command response 没有把它结构化并入本轮 motion gap。
- 完整 Nav2 NavigateToPose / fixed route execution 仍未执行证明。
- `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false` 仍保持锁定。
- 后续应把 wheel L/R、LiDAR delta、可用地图和 Nav2 path proof 合并成一次完整路线执行验收，而不是继续只证明单点材料。
