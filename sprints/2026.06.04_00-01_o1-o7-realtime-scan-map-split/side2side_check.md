# O1/O7 Realtime Scan Map Split Side2Side Check

sprint_type: epic

status: accepted_with_runtime_risk

## 验收结论

本 sprint 的软件侧验收通过：PC live operator panel 已把右侧原组合口径拆为
`实时雷达 (/scan)` 与 `实时图 (SLAM/map)`，8787 status compact summary 也已补齐
`/scan` hz 与 TF proof 摘要。

验收边界必须保持清楚：本 sprint 自身没有跑真实 ROS2 LiDAR smoke；真实 `/scan` 首个 smoke
证据来自并行的 `2026.06.04_00-01_o1-upper-ros2-bootstrap-continue` micro sprint。
因此本 sprint 可验收 PC/8787 软件合同和 UI 拆分，但不能外推为长稳、SLAM/map 或 HIL。

## 对照用户需求

- “PC 右边的雷达还不能用”：已修正 UI 和 contract，不再用固定组合标题掩盖根因。
- “雷达未接入 / 等待建图 可以分成实时雷达和实时图两部分”：已拆分。
- “只认 `/scan`”：已落实。raw packet observed 只能进入诊断详情，不能点亮实时雷达。
- “现在都没跑起来，看下怎么回事”：已把软件层原因分清：
  - PC 原先标题/状态口径硬编码和后端 summary 字段不足。
  - 上位机真实 `/scan`、TF 已由并行 O1 micro 首个 smoke observed；SLAM/map 和长稳仍未证明。

## 验收项

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| PC 首屏有 `实时雷达 (/scan)` | 通过 | Playwright rendered smoke |
| PC 首屏有 `实时图 (SLAM/map)` | 通过 | Playwright rendered smoke |
| 首屏不出现 `雷达未接入 / 等待建图` | 通过 | Playwright rendered smoke + unit test |
| raw packet observed 但 `/scan` blocked 时 radar blocked | 通过 | `pc-tools/workstation/test/App.test.ts` |
| `/scan` observed 但 map absent 时 radar ready、map waiting mapping | 通过 | `pc-tools/workstation/test/App.test.ts` |
| 8787 status 暴露 `latest_scan_hz_observed` | 通过 | `onboard/scripts/test_upper_robot_api.py` |
| 旧 artifact 缺 hz/TF 时不误判 ready | 通过 | `onboard/scripts/test_upper_robot_api.py` |
| 现场 LiDAR-only smoke summary.json | 外部证据通过 | 来自 `2026.06.04_00-01_o1-upper-ros2-bootstrap-continue`，本 sprint 不重复执行 |

## OKR 映射

- O1：本 sprint 补齐 `/scan` proof contract、collector/smoke summary 和 8787 summary；结合并行 O1 micro 的真实 LiDAR-only smoke，O1 从约 96% 保守调到约 97%。
- O7：PC UI/API 的实时雷达/实时图拆分已完成软件/渲染验收，O7 从约 98.8% 保守调到约 98.9%；不外推为真实 SLAM/map 或 production workflow。

## 剩余风险

- 首个真实 `/scan` once/hz、`/lidar/raw_packet`、`tf2_echo base_link laser_frame` 已由并行 O1 micro 确认；长稳、production udev、driver 优雅退出和 SLAM/map 仍需后续确认。
- `realtime_map` 当前只有 waiting 状态和 contract，尚无真实 map/SLAM artifact 接入。
- 真实 8787、真实 camera 8088、真实底盘 ACK/HIL、Nav2 和任务闭环仍不在本轮验收范围。
