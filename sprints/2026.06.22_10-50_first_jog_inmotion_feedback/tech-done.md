# First-Jog In-Motion Feedback Evidence

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `/api/base/manual` 在非 stop 点动写入成功后，先在运动窗口内读取一次 `T=1001` feedback，再强制发送 stop，最后读取停车后 feedback。
  - 新增 `manual_wheel_feedback_summary`、`feedback_during_motion`、`feedback_during_motion_attempted`、`wheel_feedback_lr_nonzero_proven` 等字段。
  - 只有同一 `T=1001` 帧内 `L/R` 都是 finite 且非零时，才把 wheel raw L/R 证据标记为 true。
- `onboard/tests/test_upper_robot_api.py`
  - 增加 manual 点动运动窗口采样单测，防止停车后 `0/0` 覆盖运动窗口内非零 wheel material。
- `pc-tools/workstation/src/server/index.ts`
  - PC proxy 从上位机 manual 响应提取 `remote_motion_key_values`。
  - `motion_evidence_gaps` 优先参考点动窗口内 wheel material，再参考 before/after readback。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 为 base command proxy 响应补充可选 `remote_motion_key_values` 字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 高级诊断的 latest base proxy 区域展示 `motion wheel feedback`。
- `docs/product/pc_tools_workstation.md`
  - 记录默认上位机 first-jog、视觉材料、运动窗口 wheel feedback 和未完成能力边界。
- `docs/hardware/wave_rover_json_bridge.md`
  - 记录 WAVE ROVER UART JSON 资料来源、运动窗口采样策略和真实 T=1/T=13/T=11 诊断结果。
- `docs/vision/board_camera_publisher.md`
  - 记录 stale WebRTC peer 释放和 first-frame 可见样张证据。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`
  - 结果：`Ran 34 tests in 0.013s`，`OK`。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/camera_first_frame_probe.py`
  - 结果：通过。
- `cd pc-tools/workstation && npm test`
  - 结果：`2 passed (2)`，`99 passed`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过。

## 真实上位机证据

- 上位机 Robot API 当前运行在 `root@192.168.1.11:37878`，HTTP `*:8787`，进程工作目录 `/root/rober`。
- PC API 当前运行在本机 `http://127.0.0.1:8787`。
- 关闭 stale camera peer `f040d79c10d4` 后，PC first-frame probe 返回：
  - `remote_http_status=200`
  - `status=frame_read`
  - `visible_content_proven=true`
  - `sample_path=/root/rober/onboard/runtime/camera/first_frame_probe_1782096252146.jpg`
- operator report 更新为 `evidence_ref=first-jog-visual-1782096252146` 后，PC summary 的 first-jog readiness 变为 `ready_for_first_jog`。
- PC first-jog `forward, speed=0.04, duration_ms=800`：
  - `proxy_status=command_forwarded`
  - `manual_command_executed=true`
  - `auto_stop_executed=true`
  - `feedback_during_motion_attempted=true`
  - `wheel_feedback_lr_nonzero_proven=false`
  - `motion_evidence_gaps=["wheel_feedback_lr_nonzero_not_proven","physical_motion_lidar_delta_not_proven"]`
- 直连上位机 `T=1` `{"T":1,"L":0.12,"R":0.12}`、直连 UART `T=13` `{"T":13,"X":0.1,"Z":0}`、直连 UART `T=11` `{"T":11,"L":60,"R":60}` 均写入成功并执行 stop，但 `T=1001 L/R` 仍为 `0/0`。

## 剩余风险

- wheel raw L/R 非零仍未证明；本轮只证明软件已在点动窗口内采样，真实底盘反馈仍为 `0/0`。
- 完整 Nav2 路线执行仍未证明；上一轮只证明 no-motion `ComputePathToPose` 路线生成成功。
- `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false` 仍保持锁定。
- 下一轮需要人工现场继续确认电机供电、急停、底盘模式、轮子离地/落地状态、固件反馈语义，并在可控空间内继续 HIL。
