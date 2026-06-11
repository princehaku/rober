# Radar Continuity Status Contract

## sprint_type

micro

## 设计摘要

- `GET /api/radar/status` 继续只读 `runtime/lidar_scan_proof_latest.json`，并新增只读
  LiDAR lifecycle status readback：
  - 优先 `bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh status`
  - 脚本缺失时 fallback 同目录 `o1_lidar_lifecycle.sh status`
- 新增字段：
  - `lifecycle_status`
  - `lifecycle_running`
  - `lifecycle_state`
  - `lifecycle_pid`
  - `lifecycle_status_readback`
  - `continuous_window_observed`
  - `continuity_window_status`
  - `continuity_blocked_reasons`
  - `latest_scan_proof_fresh`
- 兼容策略：
  - 保留旧字段 `continuous_scan_status`、`continuous_blocked_reasons`、
    `blocked_reasons`、`latest_scan_proof*`
  - 旧字段不删，只把 `continuous_scan_status` 从固定 `not_proven` 改为更准确的
    continuity 状态字符串
- 安全边界：
  - 只读脚本 + 只读 artifact，不探 ROS graph，不碰 `/dev/ttyS5`
  - 不发送 `/cmd_vel`、`/api/base/manual`、`T=1/T=13/T=130/T=131`
  - `safe_to_control=false`、`primary_actions_enabled=false`、
    `robot_control_executed=false`、`delivery_success=false` 保持不变

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 为 LiDAR latest proof summary 增加 freshness 摘要
  - 新增 lifecycle status 脚本只读 helper
  - 重构 `/api/radar/status` continuity/lifecycle 合同
- `onboard/tests/test_upper_robot_api.py`
  - 新增三条单测，覆盖：
    - lifecycle running + fresh proof
    - lifecycle stopped + proof present
    - lifecycle status readback fail-closed
- `docs/hardware/board_sensor_stack_smoke.md`
  - 补充 radar status continuity/lifecycle 只读合同与边界
- `docs/product/pc_tools_workstation.md`
  - 补充 PC 侧消费到的新 radar status 字段语义
- `pc-tools/README.md`
  - 补充 Robot Control 对新 radar continuity 状态的说明
- `sprints/2026.06.11_15-15_radar_continuity_status_contract/tech-plan.md`
  - 先落设计再实现

## 验证结果

### 本地

- `python3 -m unittest onboard.tests.test_upper_robot_api`
  - 通过，`Ran 27 tests in 0.126s`
- `python3 -m py_compile onboard/scripts/upper_robot_api.py`
  - 通过，无输出
- `cd pc-tools/workstation && npm run test -- test/App.test.ts -t "renders Robot Control V1"`
  - 通过，`Test Files 1 passed (1)`，`Tests 1 passed | 12 skipped (13)`
- `git diff --check`
  - 通过，无输出

### 真实上位机 smoke

目标：`root@192.168.1.11:37878`，上位机 API `http://127.0.0.1:8787`

执行顺序：

1. 部署 `onboard/scripts/upper_robot_api.py`
2. `systemctl restart trashbot-upper-robot-api.service`
3. `POST /api/radar/start`
4. `GET /api/radar/status`
5. `POST /api/radar/scan-proof/refresh`，body
   `{"timeout_s":12,"runtime_warmup_s":0,"start_runtime":false}`
6. `GET /api/radar/status`
7. `POST /api/radar/stop`
8. `GET /api/radar/status`
9. cleanup：检查 lifecycle stopped、service active、`/dev/ttyACM0` /
   `/dev/ttyS5` 无残留占用

关键结果：

- start 后 status：
  - `continuous_scan_status=latest_proof_stale_while_lifecycle_running`
  - `lifecycle_running=true`
  - `lifecycle_state=running`
  - `latest_scan_proof_fresh=false`
  - `continuous_blocked_reasons=["latest_scan_proof_stale"]`
- refresh(`start_runtime=false`) 后 status：
  - `continuous_scan_status=latest_proof_fresh_while_lifecycle_running`
  - `continuous_window_observed=true`
  - `lifecycle_running=true`
  - `latest_scan_proof_fresh=true`
  - `continuous_blocked_reasons=[]`
- stop 后 status：
  - `continuous_scan_status=latest_proof_present_but_lifecycle_not_running`
  - `lifecycle_running=false`
  - `lifecycle_state=stopped`
  - `continuous_blocked_reasons=["lidar_lifecycle_not_running"]`
- 全程：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - 未发送底盘运动命令

cleanup 结果：

- `trashbot-upper-robot-api.service=active`
- `o1_lidar_lifecycle.sh status` 回显 `running=false`、`state=stopped`
- `lsof /dev/ttyACM0 /dev/ttyS5` 无输出
- `fuser -v /dev/ttyACM0 /dev/ttyS5` 无输出

artifact：

- `sprints/2026.06.11_15-15_radar_continuity_status_contract/artifacts/live_smoke/01_radar_start.json`
- `sprints/2026.06.11_15-15_radar_continuity_status_contract/artifacts/live_smoke/02_radar_status_after_start.json`
- `sprints/2026.06.11_15-15_radar_continuity_status_contract/artifacts/live_smoke/03_radar_refresh_readonly.json`
- `sprints/2026.06.11_15-15_radar_continuity_status_contract/artifacts/live_smoke/04_radar_status_after_refresh.json`
- `sprints/2026.06.11_15-15_radar_continuity_status_contract/artifacts/live_smoke/05_radar_stop.json`
- `sprints/2026.06.11_15-15_radar_continuity_status_contract/artifacts/live_smoke/06_radar_status_after_stop.json`
- `sprints/2026.06.11_15-15_radar_continuity_status_contract/artifacts/live_smoke/07_cleanup.log`

## 失败定位

- 第一次远端 smoke 在 service restart 后立即 `curl 127.0.0.1:8787`，命中短暂启动窗口，
  返回 `connection refused`
- 复查 `systemctl status`、`journalctl` 与 `ss -ltnp` 后确认服务已正常监听 8787，
  第二次 smoke 增加 API ready 等待后通过

## 剩余风险

- 当前 `continuous_scan_status=latest_proof_fresh_while_lifecycle_running` 只表示
  “当前窗口 lifecycle 正在运行且 latest proof 新鲜”，不是长时间连续扫描统计证明
- latest proof freshness 仍按 artifact 文件年龄判定，适合当前 read-only status 合同，
  不等于 HIL、运动安全或长期稳定性 SLA
- 本轮未改 PC summary 代码；当前无需改动，因为 PC 已可消费新 status 字段且普通用户首屏
  不暴露工程细节
- 不需要 Product、Hardware、Autonomy 或 Full-Stack 协同；本轮是单 owner 的上位机
  只读状态合同补强
