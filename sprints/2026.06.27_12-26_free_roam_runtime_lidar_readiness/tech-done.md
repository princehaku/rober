# Free Roam Runtime LiDAR Readiness

## Sprint 类型

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `free_roam_runtime_lidar_readiness()`，只读 `free_roam_autonomy_latest.json` 中由 free-roam 节点写出的实时 `/scan` 快照。
  - `free_roam_motion_readiness()` 的建图雷达判断从“只看 radar proof fresh”改为“radar proof fresh 或 free-roam runtime `/scan` 新鲜均可”。
  - 返回体保留 `radar.proof_ready`、`radar.runtime_scan_ready` 和 `radar.runtime_scan`，避免把 runtime 证据误读成旧 proof 已恢复。
- `onboard/scripts/test_upper_robot_api_free_roam.py`
  - 新增回归：camera ready、radar proof stale、free-roam runtime `/scan` fresh 时，`confirm_mapping_active=true` 会真正应用为 `mapping_active=true`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 free-roam 建图 readiness 现在可使用 runtime LiDAR 快照，避免雷达已开始但旧 proof 阻塞建图。
- `docs/product/pc_tools_workstation.md`
  - 同步普通 PC 端用户口径：自由移动仍只需安全确认，建图验收的雷达项可由 runtime `/scan` 新鲜证据满足。

## 验证结果

- 已通过：`python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam`，2 tests OK。
- 已通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api_free_roam.py`。
- 已通过：`python3 -m unittest discover onboard/scripts -p 'test_upper_robot_api*.py'`，2 tests OK。
- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "free-roam autonomy|free movement from mapping acceptance|start-ready free-roam autonomy"`，14 passed / 273 skipped。
- 已通过：`git diff --check`。
- 已部署到上车端：备份 `/root/rober/onboard/scripts/upper_robot_api.py.bak_<timestamp>`，同步本轮 `upper_robot_api.py`，`python3 -m py_compile` 通过后重启 8787，live PID `238659`。
- live 只读验证：远端 `api.free_roam_motion_readiness()` 返回 `ready=true`、`radar_ready=true`、`radar.proof_ready=false`、`radar.runtime_scan_ready=true`、`runtime_scan.lidar_age_s≈0.017`、`runtime_scan.lidar_min_distance_m≈0.035`；同时 `mapping_ready=false` 且 `mapping_missing=["camera_first_frame_not_observed"]`。

## 剩余风险

- 本轮不发真实 start/manual/Nav2 命令，不证明小车已经移动。
- live 摄像头仍是 `/dev/video1` 无首帧；本轮验证显示 runtime LiDAR ready 后，建图 readiness 当前只剩相机缺口。
- Nav2 同窗口 wheel raw L/R 非零仍需现场安全确认后的真实路线复验。

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`：确认本轮未修改 WAVE ROVER UART/JSON 命令、串口、电气或底盘控制参数；本轮只消费 ROS2 free-roam runtime `/scan` artifact。
