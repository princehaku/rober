# Upper LiDAR Scan Preview Readback

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`：新增只读 LaserScan stdout preview 解析逻辑，在 `/api/radar/scan-proof/latest` 加载既有 `runtime/lidar_scan_proof_latest.json` 时，从 `topic_reads.results.scan_once.stdout_preview` 抽取 `scan_preview_points`、点数、原始槽位数、`frame_id` 和解析来源；解析会过滤 NaN/inf、低于 `range_min` 和高于 `range_max` 的距离。
- `onboard/scripts/upper_robot_api.py`：同步把 scan preview 字段提升到 `/api/radar/status` 的 `scan_proof_latest` summary，方便 PC 只读 summary 或 latest 任一入口消费。
- `onboard/tests/test_upper_robot_api.py`：新增单元测试覆盖 LaserScan YAML 解析、越界距离过滤、`source_index` 保留，以及 `safe_to_control=false` / `robot_control_executed=false` 的安全边界。
- `docs/product/pc_tools_workstation.md`：补充上位机 latest readback 现在会从已有 scan proof artifact 派生结构化雷达点，且不启动硬件或控制链路。

## 验证结果

- `python3 -m py_compile onboard/scripts/upper_robot_api.py`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，39 tests。
- 远端部署：`upper_robot_api.py` 已备份并替换到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`，远端 `python3 -m py_compile` 通过，8787 以 `/root/rober` 为 cwd 重新启动，PID `87806`，监听 `0.0.0.0:8787`。
- 上位机只读 smoke：`GET http://192.168.1.11:8787/api/radar/scan-proof/latest` 返回 `artifact.status=loaded`、`scan_preview_point_count=79`、`scan_preview_source_point_count=84`、`scan_preview_frame_id=laser_frame`、`scan_preview_source=topic_reads.results.scan_once.stdout_preview`、`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`。
- PC 7001 summary smoke：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `scan_preview_point_count=72`、`scan_preview_frame_id=laser_frame`、`safe_to_control=false`、`delivery_success=false`；PC 本机 Node 仍监听 `*:7001`，未改 Clash。

## 剩余风险

- 本轮只让已有 scan proof artifact 在地图层可见；没有触发新的 LiDAR refresh、没有启动建图、没有执行 Nav2 route、没有发送 manual/keyboard/stop/delivery 或 `/cmd_vel`。
- 当前 PC summary 仍缺 `robot_pose`，所以点位可读但地图全局叠加仍会显示等待定位；需要 AMCL/map-frame 位姿材料后才能达到完整地图所见即所得。
