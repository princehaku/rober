# O3 ROS Daemon-safe Localization Recovery PRD

## 用户价值

普通用户的一键送垃圾体验依赖机器人能在固定地图里稳定定位并生成同轮路径。当前已经能远程触达真实上位机，但定位链被 ROS graph 查询/daemon 异常遮蔽，导致无法判断 `/scan`、AMCL、TF 和 planner 的真实状态。

## 问题陈述

上一轮 live raw JSON 中，`/map`、`/amcl_pose`、lifecycle 和 topic list 查询都返回同类错误：

```text
xmlrpc.client.Fault: RuntimeError: !rclpy.ok()
```

这说明当前 preflight 把 CLI/daemon 层故障误收敛为 topic 缺失，导致下一步行动不够精准。本轮需要先让 live probe 具备 daemon reset / retry / bypass 能力，再判断真实定位链缺口。

## 验收口径

本轮成功至少满足以下之一：

- live artifact 证明 ROS daemon/CLI graph 查询从 `!rclpy.ok()` 恢复，且 `/scan`、`/map`、`/amcl_pose`、lifecycle 或 TF 中至少一个关键观测点产生新事实；
- 或 live artifact 仍 fail-closed，但能把 root cause 从 `!rclpy.ok()` 细分到 daemon reset 失败、ROS graph unavailable、LiDAR missing、map server not active、AMCL not active、AMCL no pose、TF missing 等具体层。

不接受：

- 只改文案或只复用旧 raw JSON；
- 把 `path_generated=false` 包装成进展；
- 在没有新 live artifact 的情况下上调 OKR；
- 任何触发底盘运动的命令。

## 本轮不做

- 不推进 O5 production cloud readiness。
- 不接 O6/O7 新 readback wrapper。
- 不做真实 route execution 或 delivery success 声明。
- 不改 WAVE ROVER 运动控制、串口协议或速度映射。
