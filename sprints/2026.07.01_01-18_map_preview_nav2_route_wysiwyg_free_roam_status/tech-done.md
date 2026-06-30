# Map Preview Nav2 Route WYSIWYG And Free Roam Status Micro Sprint

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - `GET /api/map/preview` 从 Nav2 lifecycle artifact 只读提升 `path_preview_points`、`path_preview_status`、`path_preview_point_count`、`path_preview_frame_id` 和 WYSIWYG 文案。
  - `GET /api/nav2/status` 顶层同步暴露同一组路线贴图字段，避免 PC 代理只能读到 `path_generated` 却画不出路线。
  - 路线点提取只接受有限 `x/y` 数字；只有点数没有点数组时返回 `metadata_only`，不冒充路线已贴图。
  - `free_roam_autonomy_status()` 实时聚合 camera/radar readiness，并只用于 `free_roam_mapping_start_ready`；`/api/free-roam/autonomy/latest` 继续 artifact-only 快读，不阻塞自由移动入口。
- `onboard/tests/test_upper_robot_api.py`
  - 覆盖 map preview 返回 Nav2 路线点、metadata-only 不贴图、free-roam status 在 camera/radar ready 时显示可建图。
  - 雷达 proof refresh 测试同步当前默认 `driver_diagnostics` collector。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录路线 WYSIWYG 字段和自由移动/建图 readiness 分层合同。

## 验证结果

- `python3 -m py_compile onboard/scripts/upper_robot_api.py`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，90 个测试，1 skipped。
- `python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam`：通过，7 个测试。
- 上车部署：已复制 `upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`，远端 `python3 -m py_compile` 通过，`systemctl restart trashbot-upper-robot-api.service` 后服务 active，监听 `0.0.0.0:8787`。
- live 只读 GET：
  - `GET http://127.0.0.1:8787/api/map/preview`：`status=loaded`、`path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`path_preview_frame_id=map`、`sends_motion_commands=false`。
  - `GET http://127.0.0.1:8787/api/nav2/status`：`status=path_generated`、`path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`path_preview_frame_id=map`、`sends_motion_commands=false`。
  - `GET http://127.0.0.1:7001/api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787`：`proxy_status=preview_forwarded`、`path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`robot_control_executed=false`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary`：`route_path_status=path_preview_observed`、`route_path_points=18`、`free_move_start_ready=true`、`mapping_start_ready=false`、`mapping_start_missing=camera_first_frame`、`safe_to_control=false`。

## 剩余风险

- 本轮只恢复路线贴图 WYSIWYG 和自由移动/建图 readiness 表达；没有执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 当前 live 仍显示相机首帧缺失，因此建图启动保持未就绪；这与 camera blocker 一致，不影响安全确认后的低速自由移动入口。
