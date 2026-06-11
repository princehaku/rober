# Radar Continuity Status Contract

## sprint_type

micro

## 目标

为上位机 `GET /api/radar/status` 设计并实现只读的 LiDAR continuity/lifecycle 状态合同，
补上真实 smoke 已证明 lifecycle running + latest proof fresh，但 status 仍固定
`continuous_scan_status=not_proven` / `scan_continuity_not_observed` 的缺口。

本轮只做只读状态建模，不改变 PC 普通用户首屏，不发送任何底盘运动命令，不把
`safe_to_control`、`robot_control_executed`、`delivery_success` 或任何 HIL 相关字段置真。

## 生产者 / 消费者 / 兼容性

### 生产者

- `onboard/scripts/upper_robot_api.py`
  - 继续只读 `runtime/lidar_scan_proof_latest.json`
  - 新增只读 lifecycle status readback，优先调用：
    - `/root/rober/onboard/scripts/o1_lidar_lifecycle.sh status`
    - 若该绝对路径缺失，再 fallback 同目录 `o1_lidar_lifecycle.sh status`
- 真实 lifecycle JSON producer：
  - `onboard/scripts/o1_lidar_lifecycle.sh status`

### 消费者

- `GET /api/radar/status` 直接消费者
- PC workstation `robotControlSummary` 及其测试
- sprint/live smoke artifact 复盘
- 文档中的 status 合同说明

### 兼容性策略

- 保留现有字段：
  - `continuous_scan_status`
  - `continuous_blocked_reasons`
  - `blocked_reasons`
  - `latest_scan_proof*`
- 允许新增字段，不删除旧字段、不改变旧字段的 fail-closed 安全含义。
- 旧消费者即使完全忽略新字段，也仍可继续工作。

## 字段设计

### lifecycle 读回字段

- `lifecycle_status`
  - 面向 UI/人读的总状态
  - 候选值：
    - `running_latest_proof_fresh`
    - `running_latest_proof_stale_or_incomplete`
    - `stopped_latest_proof_present`
    - `stopped_no_latest_proof`
    - `status_read_failed`
- `lifecycle_running`
  - 布尔值；仅来自 lifecycle status JSON 的 `running`
- `lifecycle_state`
  - 透传 lifecycle status JSON 的 `state`
- `lifecycle_pid`
  - 透传 lifecycle status JSON 的 `pid`
- `lifecycle_status_readback`
  - 保留原始只读 readback 摘要，便于 SSH/PC 诊断

### continuity 语义字段

- `continuous_window_observed`
  - 本轮保守定义：只有当 lifecycle running 且 latest proof fresh 完整时为 `true`
  - 该字段明确表示“观察到当前窗口内正在运行且 fresh proof 新鲜”，
    不是“长时间稳定连续扫描已经被严格证明”
- `continuity_window_status`
  - 候选值：
    - `latest_proof_fresh_while_lifecycle_running`
    - `latest_proof_incomplete_while_lifecycle_running`
    - `latest_proof_missing_while_lifecycle_running`
    - `lifecycle_not_running`
    - `lifecycle_status_unavailable`
- `continuity_blocked_reasons`
  - 只描述 continuity window 未满足的真实 blocker，例如：
    - `lidar_lifecycle_not_running`
    - `lifecycle_status_read_failed`
    - `latest_scan_proof_missing`
    - `latest_scan_proof_required_observations_missing:...`
    - `latest_scan_proof_stale`

### 旧字段映射策略

- `continuous_scan_status`
  - 不再固定 `not_proven`
  - 新语义：
    - 当 lifecycle running 且 latest proof fresh 完整时：
      `latest_proof_fresh_while_lifecycle_running`
    - 否则保持 fail-closed 的 blocked/not_proven 语义
- `continuous_blocked_reasons`
  - 继续保留
  - 若 continuity window 已观察到，则为空数组
  - 若仅 latest proof fresh 但 lifecycle 未运行，必须包含
    `lidar_lifecycle_not_running`
- `blocked_reasons`
  - 继续聚合：
    - 设备缺口
    - latest proof 缺口
    - continuity/lifecycle 缺口

## fail-closed 规则

### lifecycle status 读取

- 若脚本不存在、不可执行、超时、退出码非 0、stdout 不是 JSON、JSON 根不是 object：
  - 不抛异常
  - `lifecycle_running=false`
  - `lifecycle_status=status_read_failed`
  - `continuity_window_status=lifecycle_status_unavailable`
  - `continuity_blocked_reasons` 必含 `lifecycle_status_read_failed`

### continuity 判定

- 只有 lifecycle `running=true` 且 `latest_scan_proof.observed=true` 时，
  才允许把 continuity window 标成 observed。
- 即使 observed：
  - 仍保留“这不是运动许可”的边界
  - `safe_to_control=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `sends_motion_commands=false`
  - `uses_base_uart=false`

### 旧 blocker 保留

- 若没有更精确的新 blocker，可继续保留 `scan_continuity_not_observed`
- 但当 lifecycle running + latest proof fresh 时，旧 blocker 必须从
  `continuous_blocked_reasons` 和 `blocked_reasons` 中移除，避免 UI 误读成
  “雷达仍完全没跑起来”

## 实现范围

- 必改：
  - `onboard/scripts/upper_robot_api.py`
  - `onboard/tests/test_upper_robot_api.py`
  - `docs/hardware/board_sensor_stack_smoke.md`
  - `docs/product/pc_tools_workstation.md`
  - `pc-tools/README.md`
- 条件修改：
  - `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `pc-tools/workstation/test/catalog.test.ts`
  - 仅当摘要消费确实需要读取新字段时再改

## 验收命令

1. `python3 -m unittest onboard.tests.test_upper_robot_api`
2. `python3 -m py_compile onboard/scripts/upper_robot_api.py`
3. 若改了 PC 文件：
   `cd pc-tools/workstation && npm run build && npm run test -- --run && npm run lint`
4. 若没改 PC 文件：
   `cd pc-tools/workstation && npm run test -- test/App.test.ts -t "renders Robot Control V1"`
5. `git diff --check`
6. 真实上位机 smoke：
   - 部署 `onboard/scripts/upper_robot_api.py`
   - `systemctl restart/verify trashbot-upper-robot-api.service`
   - `POST /api/radar/start`
   - `GET /api/radar/status`
   - `POST /api/radar/scan-proof/refresh` with `start_runtime=false`
   - `GET /api/radar/status`
   - `POST /api/radar/stop`
   - cleanup 检查 lifecycle stopped、`/dev/ttyACM0` / `/dev/ttyS5` 无残留占用、
     upper API service active

## 风险边界

- 本轮只能表达“lifecycle 正在运行且当前 latest proof 新鲜”，不能宣称
  “长稳连续扫描已被严格统计证明”
- lifecycle status 依赖远端脚本输出 JSON；若现场脚本漂移，API 会 fail-closed
- 本轮不涉及 `/api/base/manual`、`/cmd_vel`、WAVE ROVER UART、Nav2 或任何运动链路
