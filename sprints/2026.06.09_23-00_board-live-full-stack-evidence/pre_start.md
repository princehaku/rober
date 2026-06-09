# Board Live Full Stack Evidence Pre Start

## sprint_type: epic

## 背景

CEO 已确认 `ssh root@192.168.1.11 -p 37878` 当前可从 Codex 主机连通。上一轮 SSH blocker 已解除，本轮恢复真实上车 evidence capture，覆盖雷达、摄像头、建图和运动 smoke。

本轮不是新增 UI 或 mock surface，而是产出真实上位机材料，供 O3 现场验证 lane、O6 archive、O7 route replay / labeling 后续消费。

## 目标

在真实上位机 `op-z3-b6.home` 上完成分层 evidence capture：

1. SSH / runtime gate：确认上位机、ROS2、工作区、trashbot package。
2. 传感器 gate：确认雷达 `/scan`、摄像头 `/camera/image_raw`、里程计 `/odom`、`/tf` 或可替代实际 topic。
3. 建图 gate：尝试启动或发现 SLAM / map 链路，产出 `map.yaml` 或明确缺口。
4. 运动 gate：在安全前提下执行低速、短时、可停止 motion smoke，并记录 `/cmd_vel`、`/odom`、硬件反馈或失败原因。
5. evidence packet gate：把真实材料整理成 artifact root，并生成 `trashbot.field_evidence_manifest.v1`。

## Owner

- `robot-hardware-engineer`：真实硬件和安全 gate，读取 vendor 资料，确认设备、串口、底盘/传感器状态和运动安全边界。
- `robot-algorithm-engineer`：雷达、摄像头、SLAM/建图、rosbag/topic capture。
- `robot-software-engineer`：证据目录、manifest gate、sprint 收口和必要脚本复用。

## 明确边界

- 必须先读 `docs/vendor/VENDOR_INDEX.md`。涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、反馈协议、引脚、电压、机械尺寸时，以 `docs/vendor/` 本地资料为准。
- 运动 smoke 只允许低速、短时、可停止；必须先记录安全前置条件，并在命令后立即 stop。
- 未证实运动成功前，不得把 `delivery_success`、`safe_to_control`、`primary_actions_enabled` 置为 true。
- 本轮不修改硬件配置、launch 默认参数或底盘协议，除非子 agent 证明现有入口阻塞且另起实现任务。

## 上轮 blocker 复盘

- 旧 blocker：Codex 主机到 `192.168.1.11:37878` `No route to host`。
- 当前状态：2026-06-09 22:52 CST SSH 探针成功，远端 `hostname=op-z3-b6.home`，Linux aarch64。
- 本轮不得继续把 SSH 不通作为默认结论；必须进入真实 runtime / sensor / capture 分层验证。
