# 2026.06.28 12:22 camera health not-exclusive aliases

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 8787 `/api/camera/health` 顶层 aliases：`selected_path`、`selected_name`、`selected_is_uvc_or_usb`、`source_usage_status`、`source_usage_owner_count`、`source_usage_summary`、`source_diagnosis_status`、`source_diagnosis_plain_hint`、`source_diagnosis_next_action`、`source_diagnosis_not_exclusive`、`shared_preview_contract`。
  - alias 只从 8088 camera service 已有的 `current_selection`、`source_usage`、`source_diagnosis`、`media_diagnostics` 复制只读事实；不打开摄像头，不重启 8088，不触碰底盘。
- `onboard/tests/test_upper_robot_api.py`
  - 覆盖 8088 health 只有嵌套诊断时，8787 顶层也能直接显示 `uvc_no_frame_not_exclusive` 和 `not_in_use`。
- `docs/product/pc_tools_workstation.md`
  - 记录 camera health 顶层诊断 alias，说明它服务于“谁进来都能看同一条共享预览/失败诊断”的普通用户口径。
- 真实上车部署
  - 已同步 `upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`。
  - 已重启 8787 upper Robot API，当前 PID `322795`，监听 `0.0.0.0:8787`。

## 验证结果

- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_camera_health_flattens_not_exclusive_source_diagnosis`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，78 tests。
- 真实上车只读验证：
  - `GET http://192.168.1.11:8787/api/camera/health` 顶层返回 `selected_path=/dev/video1`、`selected_name=USB Composite Device: DV20 USB (usb-5310000.usb-1)`、`source_usage_status=not_in_use`、`source_usage_owner_count=0`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`shared_preview_contract=single_shared_capture_for_multiple_clients`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 仍返回 `nav2_goal_ready=true`、`nav2_goal_blockers=[]`、`keyboard_control_start_ready=true`、`free_roam_autonomy=start_ready`。

## 剩余风险

- 本轮没有执行真实 Nav2 路线、manual/keyboard 点动、free-roam start 或 `/cmd_vel`；因此不证明 wheel raw L/R 非零、完整路线执行完成或 delivery success。
- 摄像头仍没有真实画面：当前结论是“不是页面独占，而是 `/dev/video1` UVC 无首帧”。下一步需要检查 USB、摄像头输入/供电，或换 known-good UVC 复测。
- 雷达当前读数仍可能是 stopped/stale；这影响建图验收和地图雷达 marker，不影响低速自由移动的最小安全门禁。
