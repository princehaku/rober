# 2026.06.03 20-21 O7 raw packet PC visibility

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/o7LiveOperatorPanel.ts`
  - 从 8787 `GET /api/status.radar.raw_packet_proof_latest` 消费 LiDAR raw packet proof latest 摘要。
  - 在 `lidar_radar.raw_packet_proof_latest` 透传 artifact status、freshness/age、proof status、raw bytes、sync header、packet parse 和 point 统计。
  - 字段缺失时兼容降级为 `not_loaded`、`unknown`、`null` 或 `false`，不让 PC UI/API 500。
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
  - 在 `GET /api/o7/direct-upper/status.upper_status_summary` 增加 `radar_raw_packet_proof_*` 摘要字段。
  - 未配置或 8787 不可读时仍返回完整 fail-closed 结构。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 O7 Live Operator Panel 与 Direct Upper Status TypeScript 合同。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - 首屏地图区新增 `Raw packet proof` 紧凑状态，展示 artifact/freshness/age/proof status、bytes、sync、packets、points。
  - Direct upper 卡片新增 raw packet proof 状态灯。
  - 文案明确 PC 只消费只读材料，`safe_to_control=false`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖首屏文本包含 raw packet proof、bytes/sync/packets/points 和 fail-closed 边界。
  - 覆盖 live panel API 与 direct upper status 对 raw packet proof summary 的结构透传。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 catalog/server 生成的 live operator payload 带 raw packet proof summary。
- `docs/interfaces/o7_upper_robot_api.md`
  - 补充 `/api/radar/raw-packet-proof/latest` 与 `radar.raw_packet_proof_latest` 摘要字段和只读边界。
- `docs/interfaces/o7_live_operator_panel.md`
  - 补充 O7 首屏 raw packet proof 展示合同。
- `docs/interfaces/o7_direct_upper_pc_api.md`
  - 补充 direct upper status 的 raw packet proof summary 字段。
- `docs/interfaces/o7_realtime_hardware_sources.md`
  - 补充 raw packet proof 可见性来源与安全边界。

## 接口影响

- PC `GET /api/o7/live-operator-panel` 新增：
  - `lidar_radar.raw_packet_proof_latest.endpoint="/api/radar/raw-packet-proof/latest"`
  - `http_status`
  - `artifact_status`
  - `freshness_status`
  - `age_seconds`
  - `latest_proof_status`
  - `latest_raw_bytes_observed`
  - `latest_sync_header_observed`
  - `latest_packet_parse_ok`
  - `latest_points_observed`
  - `latest_bytes_read`
  - `latest_sync_header_count`
  - `latest_packets_parse_ok`
  - `latest_points_total`
  - `sends_commands=false`
  - `sends_motion_commands=false`
  - `robot_control_executed=false`
  - `safe_to_control=false`
  - `hil_pass=false`
  - `collector_executed_by_pc=false`
- PC `GET /api/o7/direct-upper/status.upper_status_summary` 新增 `radar_raw_packet_proof_*` 摘要字段。
- PC 没有新增 POST，也没有新增任何会执行 collector、串口、ROS2 或底盘控制的路径。

## 安全边界

- PC 不执行 `onboard/scripts/o1_lidar_raw_packet_proof_collector.py`。
- PC 不启动 ROS2 driver 或 launch。
- PC 不打开 `/dev/ttyACM0`、`/dev/lidar` 或 `/dev/ttyS5`。
- PC 不发送 vendor `A5 60` 启动命令或停止序列。
- PC 不发送 `T=1/T=13/T=130/T=131`、`/cmd_vel` 或任何底盘命令。
- raw packet proof 可见只证明材料可被 operator 消费，不证明真实 ROS2 `/scan`、TF、SLAM/Nav2、HIL、ACK、`safe_to_control=true`、真实手控或 delivery success。

## 验证结果

```text
npm run test --prefix pc-tools/workstation
Test Files  2 passed (2)
Tests  76 passed (76)
```

```text
npm run build --prefix pc-tools/workstation
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
vite v7.3.3 building client environment for production...
✓ built in 1.82s
```

```text
npm run lint --prefix pc-tools/workstation
eslint .
exit 0
```

```text
npm run dev --prefix pc-tools/workstation -- --host 127.0.0.1 --port 5173
Port 5173 is in use, trying another one...
Local: http://127.0.0.1:5174/
```

```text
Playwright rendered smoke at http://127.0.0.1:5174/
title: Rober PC Tools Workstation
hasConsole: true
hasRawPacketProof: true
hasRawEndpoint: true
hasSafeBoundary: true
hasFrameworkOverlay: false
consoleMessages: []
screenshot: /tmp/rober-o7-raw-packet-proof.png
```

```text
git diff --check -- pc-tools/workstation docs/interfaces docs/product sprints/2026.06.03_20-21_o7-raw-packet-pc-visibility/tech-done.md
exit 0
```

## 剩余风险

- Hardware agent 并行实现的 8787 `/api/radar/raw-packet-proof/latest` 与 `radar.raw_packet_proof_latest` 尚需合并后用真实上位机 readback 再做一次端到端验证。
- 本轮 Playwright 只做本地 dev server 首屏 smoke；未连接真实 8787 raw packet proof endpoint 做端到端 readback。
- raw packet proof 材料仍不是 ROS2 `/scan`、TF、Nav2/SLAM、HIL、ACK 或真实安全控制证据。
