# 控制与状态链路性能优化

## 本轮声明

- sprint_type: epic
- 状态：pre_start completed，2026-09-17。
- 用户授权：先要求“精简代码 性能第一 端到端时延&CPU性能”，在首批建议后明确“恩 改吧”。
- 目标：降低控制与停止请求等待、状态读取耗时和手机空闲 CPU，并修正 CPU 测量基线。
- 北极星：普通用户可以顺畅查看任务进度、及时停止小车；可靠的测量帮助控制低成本车端资源占用。
- Owner：Robot Software Engineer 负责车端与最终集成；Full-stack Software Engineer 负责 PC/手机；Product 负责范围与证据收口。

## 上轮遗留与 blocker 核对

- `2026.06.05_15-16_o10-amcl-nav2-runtime-epic` 的核心阻塞为 Nav2 包、lifecycle 和 ROS topics 缺失。
- `2026.06.05_13-14_o10-amcl-nav2-readiness-epic` 留有真实电梯图片及现场 HIL 缺口。
- 本轮采用本地 mock、回归测试及可复跑性能 artifact，不依赖以上材料，不再重复消费原硬件阻塞。
- 保留已有未跟踪目录 `sprints/2026.06.12_00-01_o10-amcl-nav2-bringup-epic/`，不读作本轮成果，不修改。

## 范围与证据边界

- 首批覆盖 CPU 采样、8787 控制/Stop、车端与 PC 状态链、手机首屏及轻量刷新。
- remote bridge 退避、operator gateway 写盘和导航进程移除留待独立测量，避免一次改动扩大回归面。
- 保留原有控制准入、自动停车、ACK 与送达语义；不打开真实串口、不执行控车、不部署。
- 初始 OKR 百分比保持；仅在工程证据产生后归档软件性能 KR，不外推 HIL 或真实端到端改善。
- 下一阶段：完成 PRD 与可执行 tech-plan 后直接派工程实现。
