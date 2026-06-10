# sprint_type: micro

## 背景

本轮目标是把真实上位机 `http://192.168.1.11:8787` 的 Robot API 恢复到可读状态，并通过 PC workstation 既有只读代理 `GET /api/robot-control/summary?baseUrl=...` 拉回真实 evidence。  
本轮只做只读联调与证据留档，不改产品代码，不触发 `/cmd_vel`、`/api/base/manual`、Nav2 goal/controller，也不直接写 `/dev/ttyS5`。

## 实际改动

1. 新增 sprint 目录 `sprints/2026.06.10_22-40_pc_real_robot_api_readback/`。
2. 新增远端只读联调原始证据：
   - `artifacts/remote_service_preflight.txt`
   - `artifacts/remote_service_status.txt`
   - `artifacts/remote_service_journal_tail.txt`
   - `artifacts/status.json`
   - `artifacts/nav2_proof_latest.json`
   - `artifacts/radar_status.json`
   - `artifacts/camera_health.json`
   - `artifacts/camera_devices.json`
   - `artifacts/base_status.json`
   - `artifacts/base_feedback_samples_latest.json`
3. 新增 workstation 侧只读聚合证据：
   - `artifacts/workstation_api_health.json`
   - `artifacts/workstation_robot_control_summary.json`
   - `artifacts/readback_summary.json`

## 验证结果

### 1. 远端服务恢复/确认

- `ssh root@192.168.1.11 -p 37878 'hostname; systemctl is-active trashbot-upper-robot-api.service || true; ss -ltnp | grep 8787 || true'`
  - 主机名：`op-z3-b6.home`
  - 初始状态：`inactive`
- `ssh root@192.168.1.11 -p 37878 'systemctl start trashbot-upper-robot-api.service || true; sleep 2; systemctl is-active trashbot-upper-robot-api.service || true; systemctl --no-pager --lines=20 status trashbot-upper-robot-api.service || true'`
  - 启动后状态：`active`
  - 监听端口：`0.0.0.0:8787`
  - 进程：`python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`
- journal tail 见 `artifacts/remote_service_journal_tail.txt`，最新一轮显示 `upper_robot_api_started`，未见新的 Python traceback。

### 2. 远端只读 GET 结果

证据文件均保存在本 sprint `artifacts/` 下。

- `/api/status`
  - 已加载。
  - `camera.status=ready`
  - `radar.status=scan_once_hz_raw_packet_tf_observed`
  - `map.status=map_once_artifact_metadata_observed`
  - `nav2.proof_latest.latest_path_generated=true`
- `/api/nav2/proof/latest`
  - 已加载。
  - `latest_proof_status=nav2_no_motion_path_generation_runtime_observed`
  - `path_generated=true`
  - `path_generation_succeeded=true`
  - `path_point_count=31`
- `/api/radar/status`
  - 已加载。
  - `scan_status=fresh_scan_proof_observed`
  - `latest_scan_proof_state=scan_once_hz_raw_packet_tf_observed`
  - `latest_scan_hz_average_rate_hz=14.951`
- `/api/camera/health`
  - 已加载。
  - `status=ready`
  - `video_source=auto`
- `/api/camera/devices`
  - 已加载。
  - 发现 `/dev/video0`、`/dev/video1`、`/dev/video2`
- `/api/base/status`
  - 已加载。
  - `port=/dev/ttyS5`
  - `baudrate=115200`
  - `feedback_ack.t1001_observed=true`
  - `feedback_readback.serial_write.command={"T":130}`
  - vendor 依据：`docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `/api/base/feedback-samples/latest`
  - 已加载。
  - `latest_result.all_samples_observed_t1001=true`
  - `latest_result.t1001_observed_count=2`

### 3. PC workstation 构建与代理摘要

- `cd pc-tools/workstation && npm run build`
  - 通过。
  - `vite` + `tsc` 均完成，产物写入 `pc-tools/workstation/dist/`
- 复用本机已存在的 workstation API：`http://127.0.0.1:8787`
- `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - 原始输出：`artifacts/workstation_robot_control_summary.json`
  - 聚合摘要：`artifacts/readback_summary.json`

workstation 聚合结果：

- `console_status=blocked`
- `robot_api_connection.loaded_count=6`
- `robot_api_connection.blocked_count=4`
- `robot_api_connection.failed_count=3`
- `o3_proof_summary.path_generated=true`
- `o3_proof_summary.path_point_count=31`

按子系统拆分：

- camera
  - 远端直连：`ready` / devices 已返回
  - workstation 聚合：`fetch_failed`
  - 直接原因：代理对 `/api/status`、`/api/camera/health`、`/api/camera/devices` 读取命中了 1500ms 超时
- radar
  - workstation 聚合：`scan_once_hz_raw_packet_tf_observed`
  - 说明激光雷达 proof 已被只读代理正确读回
- base
  - 远端直连：`T=130` 反馈可读，`T=1001` 已观察到
  - workstation 聚合：`blocked`
  - 直接原因：`base_status.sends_commands`、`feedback_readback.sends_commands`、`base_feedback_samples_latest.latest_result.sends_commands` 被 PC 侧安全边界识别为危险真值字段，因此固定判成 blocked

## 剩余风险

1. PC 代理当前把远端 `camera/status` 类只读证据判成 `fetch_failed`，不是因为远端服务离线，而是因为汇总接口的短超时过紧；这会让控制台误把真实在线材料显示成失败。
2. `base` 相关接口虽然是只读取证用途，但远端 `base_status` 内部会执行 `T=130` 请求反馈，workstation 安全边界因此把它归类为 blocked；这符合当前安全设计，但会影响“loaded”统计。
3. `localize_proof_latest` 和 `operator_report_latest` 仍是 `404`，所以 workstation 总摘要仍然是 `blocked`，不能被解释为 O7 已打通或真实交付成功。
4. 本轮验证范围仅覆盖：
   - 远端 systemd 服务启动与监听
   - 指定 GET 端点返回
   - PC workstation build 与只读 summary 聚合
   不包含 HIL、运动成功、Nav2 goal 下发、串口写运动命令、真实交付成功。

## 是否需要其他角色协同

当前不需要其他角色先介入即可完成本轮 micro sprint 留档。  
如果下一轮要把 workstation 中的 `camera/status` 超时与 `base` 安全分类进一步做成更可读的 UI 摘要，再交给 `full-stack-software-engineer` 或继续由 `robot-software-engineer` 在明确文件范围后处理即可。
