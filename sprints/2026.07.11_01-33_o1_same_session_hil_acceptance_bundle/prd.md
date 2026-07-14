# O1 Same-Session HIL Acceptance Bundle PRD

## 用户价值

普通手机用户最终只关心小车是否能安全、可验证地把垃圾送到目标点。本轮面向上车履约前的硬件证据整理：把同会话 WAVE ROVER `T=1001` L/R 非零轮速材料和 manual HIL gate 缺口放进同一个可复验 summary，让现场下一次短动 HIL 能直接看到“哪项已有材料，哪项仍阻止 safe-to-control”。

## 问题

O1 已有多个分散材料：

- motion-map/free-cell/localization bundle；
- bounded motion feedback material；
- manual HIL gate current evidence material；
- 单独的 same-session wheel feedback material。

但 composite O1 bundle 当前没有同屏输出 same-session L/R 非零材料与 HIL acceptance 缺口，导致后续现场执行仍要在多个工具和 sprint artifact 之间人工对照。

## 范围

本轮只做安全 intake 和 acceptance gap summary：

- 接入 `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json` 的 allowlisted summary。
- 只输出短状态、计数、速度符号、material status 和缺口列表。
- 不读取真实串口，不发送运动命令，不新增 launch 默认硬件假设。

## 非目标

- 不证明 current live HIL pass。
- 不证明 safe-to-control、delivery success、wheel direction calibration、IMU/battery calibration 或 Nav2 route execution success。
- 不归档 KR。
- 不上调 O1，除非本轮额外产生新 current live HIL/video/LiDAR/acceptance artifact。

## 验收

Hardware owner 必须提供：

1. 改动文件列表。
2. 单元测试和 CLI smoke 输出。
3. 失败定位与修复记录。
4. 已读 vendor 来源。
5. 剩余风险和下一轮 current live HIL 采集动作。
