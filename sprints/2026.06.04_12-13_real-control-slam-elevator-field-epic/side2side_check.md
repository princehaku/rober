# Side2Side Check: Real Control, SLAM, Elevator Field Epic

## sprint_type

sprint_type: epic

## 对照结论

本轮对照上一轮 `OKR.md` 要求的下一轮 Epic，没有继续堆 Micro sprint，也没有只停在计划。四个 L2 owner 已按文件边界并行交付 software guard：

| 要求 | 本轮结果 | 验收状态 |
| --- | --- | --- |
| PC operator workflow | PC workstation 增加 direct-upper radar/map/localize/operator report UI/API；manual/stop 仍走同源代理 | software_guard 通过 |
| 雷达一键 start/stop | 8787 新增 `/api/radar/start|stop`，PC 新增对应按钮/代理 | software_guard 通过，runtime 未证明 |
| 建图/定位控制 | 8787 新增 `/api/map/start|reset|save|load|list` 和 `/api/localize/reset`，PC 可消费 | software_guard 通过，SLAM/AMCL runtime 未证明 |
| OpenCV 电梯识别 | 新增 taxonomy、ROI/rule baseline、offline eval 和测试 | offline fixture eval 通过，真实图片未证明 |
| HIL/硬件边界 | 新增 vendor-sourced PC manual 与 LiDAR 串口隔离准入 | 文档护栏通过，现场 HIL 未证明 |

## 证据边界

- 可以声明：本轮 O2/O3/O7/O1 的软件护栏和执行入口已往前走，相关测试和 smoke 通过。
- 不能声明：真实控车、真实雷达开关、真实建图定位、真实电梯识别、真实跨楼层送达、HIL pass、robot ACK 或 OKR 完成度提升。

## OKR 对照

| Objective | 本轮是否推进 | 是否涨分 | 原因 |
| --- | --- | --- | --- |
| O2 | 是 | 否 | 有 OpenCV baseline/offline fixture eval，但没有真实图片 eval、状态机接入或受控电梯材料。 |
| O3 | 是 | 否 | 有 map/localize upper API 合同，但没有真实 `/map`、map artifact、AMCL pose 或 Nav2 runtime。 |
| O7 | 是 | 否 | PC operator workflow 已能消费新合同，但没有真实 8787/HIL/browser field material。 |
| O1 | 是 | 否 | HIL/串口隔离边界更清楚，但没有真实低速 pulse、post-status 或 ROS feedback topics。 |
| O5/O6 | 否 | 否 | 本轮按优先级没有抢占 O2/O3/O7/O1。 |

## 下一轮 Side-by-side 验收建议

1. 在上位机配置真实 `ROBER_RADAR_START_COMMAND` / `ROBER_RADAR_STOP_COMMAND`，采集 `/api/radar/start|stop` + `/scan` once/hz 证据。
2. 配置真实 map lifecycle command hook，采集 `/api/map/start|save|list` 与 map artifact。
3. 用真实电梯图片 manifest 跑 `elevator_opencv_baseline`，生成 offline eval artifact。
4. 按 `docs/hardware/o1_pc_manual_lidar_hil_boundary.md` 做一次 stop-first 低速 HIL drill，只采一条方向也可以，但必须有 operator report。
