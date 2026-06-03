# O1/O7 Realtime Scan Map Split Final

sprint_type: epic

status: closed_software_done_runtime_pending

## 收口结论

本 sprint 已完成软件侧收口：

- PC live panel 已拆成 `实时雷达 (/scan)` 与 `实时图 (SLAM/map)`。
- `GET /api/o7/live-operator-panel` 已新增 `realtime_radar` 与 `realtime_map`。
- 8787 `GET /api/radar/status` 已补齐 `/scan` hz、TF 和 required observations 摘要。
- raw packet proof 继续只作为诊断详情，不参与主状态灯。

本 sprint 自身未重复采集现场 LiDAR-only smoke `summary.json`；真实 `/scan` 首个 smoke
证据来自并行的 `2026.06.04_00-01_o1-upper-ros2-bootstrap-continue` micro sprint。
因此本 sprint 可以声明 PC/8787 软件合同与 UI 拆分完成，不能声明长稳、SLAM/map、HIL 或 production workflow 完成。

## 验证汇总

- PC unit：`npm test -- --run`，2 files / 81 tests passed。
- PC build：`npm run build` 通过。
- PC lint：`npm run lint` 通过。
- PC rendered smoke：Playwright 通过，截图 `/tmp/o7-live-operator-panel-final-20260604.png`。
- Onboard unit：LiDAR collector/readiness probe 14 tests passed。
- Onboard integration unit：upper robot API + collector + readiness probe 30 tests passed。
- Onboard compileall：相关脚本 compileall 通过。
- Hardware source review：已按 `docs/vendor/VENDOR_INDEX.md` 复核 LiDAR 串口、baudrate、start/stop bytes、`/scan` topic 和 raw packet 边界。

## OKR 影响

- 更新 `OKR.md`。
- O1 从约 96% 保守调到约 97%：依据并行 O1 micro 的真实上位机 ROS2 LiDAR `/scan` smoke observed、`/lidar/raw_packet` once observed 和静态 TF observed。
- O7 从约 98.8% 保守调到约 98.9%：依据本 sprint Full-Stack `tech-done.md` 的 PC test/build/lint/rendered smoke，通过 realtime radar/map split 软件验收。
- 不进入历史完成归档：O1 尚非 HIL/SLAM/Nav2/长稳，O7 尚非 production operator workflow。

## 下一步

1. O1 继续补 driver 优雅退出、production udev、长稳 smoke、SLAM/Nav2 消费和地图质量。
2. O1 底盘线在现场看护、物理净空、人工急停可用时补低速短 pulse、ACK/`T=1001`、post-status 和 HIL 证据。
3. O7 继续补真实 8787/browser 复跑、真实 SLAM/map artifact、production path 和完整 operator workflow。
4. O5/O6 作为当前最低完成度 Objective，补真实生产 TLS、公网 HTTPS、4G/SIM、DB/queue、OSS/CDN 和 phone/browser 材料。

## 剩余风险

- 首个真实 LiDAR `/scan` smoke 已由并行 O1 micro 验证；长稳、production udev、SLAM/map 和 Nav2 消费未在本 sprint 验证。
- `safe_to_control`、底盘 ACK、HIL、真实任务闭环仍未证明。
- 当前 PC ready 逻辑严格依赖 8787 summary 字段；如果现场继续产出旧 artifact，新增 hz/TF 字段会保持 `null`，UI 会继续显示等待 `/scan`，这是预期 fail-closed 行为。
