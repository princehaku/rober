# Sprint 2026.05.10_01-02 PRD

## 需求

普通用户和远程支持人员需要在不接触 SSH、ROS2 CLI、串口工具的情况下，看到机器人最近一次任务和失败诊断。operator gateway 需要增加一个最小诊断 API，用于手机页面、4G 云桥或售后工具读取。

## OKR 对齐

| OKR | 对齐点 |
| --- | --- |
| Objective 5 KR4 | 建立远程诊断最小数据包：软件版本、地图/路线版本、最近任务状态、失败原因、关键日志、摄像头快照引用 |
| Objective 5 KR5 | 普通用户失败时能知道下一步，不需要理解 ROS2 |
| Objective 2 KR5 | 任务记录和失败原因继续可复盘 |

## 用户故事

1. 作为手机用户，我可以打开本地控制页背后的诊断接口，看到机器人是否卡在任务、失败或需要人工处理。
2. 作为远程支持，我可以拿到软件版本、地图/路线版本和任务记录路径，判断是配置、路线还是任务执行失败。
3. 作为研发，我可以把视觉样本 manifest 和日志路径挂进同一个诊断包，为后续 Objective 4 数据闭环留入口。

## 验收标准

- `GET /api/diagnostics` 返回 JSON。
- payload 包含 `software_version`、`map_version`、`route_version`、`latest_status`、`last_task`、`failure`、`log_refs`、`vision_sample_manifest_ref`。
- HTTP contract 测试覆盖新 endpoint。
- docs/interfaces 与 docs/product 记录该入口。
