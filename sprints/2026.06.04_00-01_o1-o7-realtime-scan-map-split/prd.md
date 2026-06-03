# O1/O7 Realtime Scan Map Split PRD

## 用户问题

用户在 PC 右侧看到“雷达未接入 / 等待建图”，无法判断到底是雷达串口、ROS2 `/scan`、还是 SLAM/map 没起来。当前 raw packet proof 已有材料，但 UI 仍用一个组合标题表达，容易误导。

## 产品口径

CEO 已选择“只认 `/scan`”：

- 只有真实 ROS2 `/scan` 观测通过，才允许主 UI 显示实时雷达 ready。
- Raw packet proof 只能证明工程诊断材料，不能升级为实时雷达。
- 实时图必须依赖 `/scan` 和 map/SLAM 材料，不能用占位图暗示已经建图。

## 验收口径

- PC 首屏出现两个独立区块：`实时雷达 (/scan)`、`实时图 (SLAM/map)`。
- raw packet observed 但 `/scan` blocked 时：实时雷达仍显示 blocked / `/scan` 未观测，实时图显示等待雷达。
- `/scan` observed 但 map absent 时：实时雷达显示 ready，实时图显示等待建图。
- 原组合标题 `雷达未接入 / 等待建图` 不再出现在首屏。
- 状态灯“雷达”只根据 `/scan` once/hz 结果，不根据 raw packet proof。
- 文档明确 `raw_packet_proof_latest` 是诊断材料，不证明 `/scan`、TF、SLAM/map 或 HIL。

## 非目标

- 不做真实 SLAM 建图功能实现。
- 不启动 mock scan 或 fake map 来填 UI。
- 不改变底盘 manual/WASD/direct-upper 控制行为。
- 不更新 OKR 百分比，除非本轮真实采到 `/scan` smoke 证据。
