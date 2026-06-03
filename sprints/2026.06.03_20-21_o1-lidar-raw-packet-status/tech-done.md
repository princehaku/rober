# 2026.06.03 20-21 O1 LiDAR Raw Packet Status

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增默认 artifact path：`runtime/lidar_raw_packet_proof_latest.json`。
  - 新增覆盖入口：`ROBER_LIDAR_RAW_PACKET_PROOF_ARTIFACT_PATH` 和 `--lidar-raw-packet-proof-artifact-path`。
  - 新增只读 endpoint：`GET /api/radar/raw-packet-proof/latest`。
  - 在 `GET /api/radar/status` 与统一 `GET /api/status` 的 radar 区域新增 `raw_packet_proof_latest` 摘要。
  - 摘要暴露 artifact status、mtime/age、`proof.status`、raw bytes/sync header/packet parse/points observed，以及 `bytes_read/sync_header_count/packets_parse_ok/points_total`。
  - 验收修复：保留上述字段，同时新增 PC 合同需要的 `latest_raw_bytes_observed/latest_sync_header_observed/latest_packet_parse_ok/latest_points_observed/latest_bytes_read/latest_sync_header_count/latest_packets_parse_ok/latest_points_total` 别名字段。
  - 验收修复：新增 `freshness.status` 与 `freshness.age_seconds`，基于 artifact mtime 计算，basis 固定为 material freshness only，不表示 HIL 或 safe 控制。
  - readback/status 只执行 artifact `stat/read_text/json.loads`，固定 fail-closed 字段；不打开 LiDAR 串口、不发送 `A5 60`、不启动 ROS2、不发送 WAVE ROVER 底盘命令、不调用 `/api/base/manual`。
- `onboard/scripts/test_upper_robot_api.py`
  - 新增 raw packet proof latest missing/loaded/bad_json 单测。
  - 补充 `radar_status` 摘要字段、`latest_*` 别名、fresh/stale/bad_json freshness 断言，并断言 `FakeSerial.instances == []`。
- `docs/hardware/o1_lidar_raw_packet_proof.md`
  - 新增 8787 readback/status 合同、默认路径、env/CLI 覆盖、安全边界。
  - 验收修复：补充 `latest_*` 别名字段和 `freshness` 语义说明。
- `OKR.md`
  - 追加 `2026.06.03_20-21_o1-lidar-raw-packet-status` O1 补充材料说明。
  - 明确 O1 百分比不变；该增量不是 `/scan`、TF、SLAM/Nav2、HIL、ACK、`safe_to_control` 或 delivery success。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`

## 已证实硬件结论

- 本轮证实的是 8787 readback/status 合同可只读消费上一轮 raw packet artifact，并能按 PC 合同提供 `latest_*` 别名和 artifact mtime freshness。
- 远端 latest artifact 来自上一轮 LiDAR-only collector：`bytes_read=9086`、`sync_header_count=275`、`packets_parse_ok=275`、`points_total=1923`。
- 本轮 readback/status 本身没有打开 LiDAR 串口，没有发送 `A5 60`，没有启动 ROS2，没有发送底盘命令，也没有调用 `/api/base/manual`。
- 上述材料仍只证明 raw packet parse/material readiness，不证明真实 ROS2 `/scan`、TF、SLAM/Nav2、HIL、ACK、`safe_to_control=true`、真实 manual 或 delivery success。

## 验证结果

本地验证：

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_upper_robot_api.py
................
----------------------------------------------------------------------
Ran 16 tests in 1.283s

OK
```

```text
$ python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py
passed, no output
```

```text
$ git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/hardware/o1_lidar_raw_packet_proof.md OKR.md sprints/2026.06.03_20-21_o1-lidar-raw-packet-status/tech-done.md
passed, no output
```

远端部署与只读验证：

```text
$ scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py
passed, no output
```

```text
$ ssh -p 37878 root@192.168.1.11 'mkdir -p /root/rober/runtime && cp /tmp/o1_lidar_raw_packet_proof_latest.json /root/rober/runtime/lidar_raw_packet_proof_latest.json && chmod 600 /root/rober/runtime/lidar_raw_packet_proof_latest.json'
artifact copied to /root/rober/runtime/lidar_raw_packet_proof_latest.json
```

```text
$ ssh -p 37878 root@192.168.1.11 'systemctl restart trashbot-upper-robot-api.service && sleep 1 && systemctl is-active trashbot-upper-robot-api.service'
active
```

```text
$ ssh -p 37878 root@192.168.1.11 'curl -fsS http://127.0.0.1:8787/api/radar/raw-packet-proof/latest; echo; curl -fsS http://127.0.0.1:8787/api/radar/status'
raw endpoint artifact.status=loaded
raw endpoint latest_result.proof.status=raw_packets_parsed
radar_status.raw_packet_proof_latest.artifact.status=loaded
radar_status.raw_packet_proof_latest.latest_proof_status=raw_packets_parsed
radar_status.raw_packet_proof_latest.bytes_read=9086
radar_status.raw_packet_proof_latest.sync_header_count=275
radar_status.raw_packet_proof_latest.packets_parse_ok=275
radar_status.raw_packet_proof_latest.points_total=1923
radar_status.raw_packet_proof_latest.latest_bytes_read=9086
radar_status.raw_packet_proof_latest.latest_sync_header_count=275
radar_status.raw_packet_proof_latest.latest_packets_parse_ok=275
radar_status.raw_packet_proof_latest.latest_points_total=1923
radar_status.raw_packet_proof_latest.freshness.status=fresh|stale
radar_status.raw_packet_proof_latest.freshness.age_seconds=<artifact mtime age>
radar_status.raw_packet_proof_latest.sends_lidar_start_command=false
radar_status.raw_packet_proof_latest.opens_lidar_serial=false
radar_status.raw_packet_proof_latest.starts_ros2=false
radar_status.raw_packet_proof_latest.calls_base_manual=false
radar_status.raw_packet_proof_latest.safe_to_control=false
radar_status.raw_packet_proof_latest.hil_pass=false
```

```text
$ ssh -p 37878 root@192.168.1.11 'GET /api/status radar.raw_packet_proof_latest summary'
artifact_status=loaded
latest_proof_status=raw_packets_parsed
bytes_read=9086
sync_header_count=275
packets_parse_ok=275
points_total=1923
latest_bytes_read=9086
latest_sync_header_count=275
latest_packets_parse_ok=275
latest_points_total=1923
freshness.status=stale
freshness.age_seconds=1711.008
sends_lidar_start_command=false
opens_lidar_serial=false
starts_ros2=false
calls_base_manual=false
safe_to_control=false
hil_pass=false
```

验收修复后的远端只读验证：

```text
$ ssh -p 37878 root@192.168.1.11 'systemctl restart trashbot-upper-robot-api.service && sleep 1 && systemctl is-active trashbot-upper-robot-api.service && GET /api/radar/status raw_packet_proof_latest summary'
active
artifact_status=loaded
latest_proof_status=raw_packets_parsed
bytes_read=9086
latest_bytes_read=9086
sync_header_count=275
latest_sync_header_count=275
packets_parse_ok=275
latest_packets_parse_ok=275
points_total=1923
latest_points_total=1923
freshness_status=stale
freshness_age_seconds=1711.008
freshness_basis=artifact_mtime_only_material_freshness_not_hil_or_safe_to_control
sends_lidar_start_command=false
opens_lidar_serial=false
starts_ros2=false
calls_base_manual=false
safe_to_control=false
hil_pass=false
```

## 剩余风险

- 真实 ROS2 Humble/install/`ros2` 仍未补齐，真实 `/scan`、`/lidar/raw_packet` topic、TF、SLAM/Nav2 仍未证明。
- raw packet artifact 来自上一轮 LiDAR-only collector；本轮只部署 readback/status，没有重新采集 raw packet。
- 该 readback/status 不证明 ACK、HIL、运动控制安全、`safe_to_control=true`、真实 manual 或完整送达任务。
- 下一步仍应补齐上位机 ROS2 runtime，采集 `ros2 topic echo --once /scan`、`ros2 topic hz /scan`、`/lidar/raw_packet` 与 `tf2_echo base_link laser_frame`。
