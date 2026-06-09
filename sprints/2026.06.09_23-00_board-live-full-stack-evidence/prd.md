# Board Live Full Stack Evidence PRD

## 用户价值

项目需要从 local/mock software proof 进入真实上车材料闭环。PC 端 route replay、标注、云端 archive 和后续手机验收都需要真实 `map.yaml`、轨迹、关键帧、rosbag 或 replay JSONL，而不是继续消费 fixture。

## 用户故事

作为研发/运营人员，我希望真实上位机能一次性完成雷达、摄像头、建图和运动 smoke 的 evidence capture，这样后续可以：

- 回放真实路线材料；
- 训练/标注真实关键帧；
- 判断硬件链路是否真的可用；
- 把失败定位到具体 gate，而不是“现场没跑通”。

## 验收标准

### P0

- SSH 成功证据：hostname/date/uname。
- ROS2 runtime 证据：`ros2` 可用、trashbot package 可发现，或明确缺失。
- 雷达证据：`/scan` 或实际雷达 topic 的 `topic list` / `hz` / `echo --once` 摘要。
- 摄像头证据：`/camera/image_raw` 或实际 image topic 的 `topic list` / `hz` / `echo --once` 摘要。
- 建图证据：`/map`、SLAM node、map save service 或 `map.yaml` 产物；若无法建图，写明缺少哪一层。
- 运动证据：低速 motion smoke 的命令、stop 命令、`/odom` 或硬件反馈变化；若未执行，必须写明安全 gate 或 runtime gate 阻断原因。
- artifact root：集中保存本轮输出，至少包含 preflight JSON、topic snapshot、rosbag 或文本证据。
- manifest：生成或尝试生成 `trashbot.field_evidence_manifest.v1`，并保持 fail-closed 字段。

### P1

- 30 秒以内 rosbag：优先 `/scan /camera/image_raw /odom /tf /map`，缺 topic 时记录替代 topic。
- keyframe 或图片快照：如果 camera topic 可用，保存至少一份可追溯样本或 topic echo metadata。
- route/replay：如果 route recorder 可用，产出 `route.csv` 或 dry-run replay JSONL。

## 非目标

- 不做无人值守长距离导航。
- 不做真实送垃圾任务验收。
- 不把短时 motion smoke 等同于 HIL 完整通过。
- 不新增 PC/手机 surface。
- 不修改 WAVE ROVER 固件或 Orange Pi 接线。

## 成功边界

本轮成功可以是“全部 gate 通过并产出真实 packet”，也可以是“某个真实 gate 明确失败但证据足够具体”。但不能只停留在 SSH 探针；必须至少推进到 runtime/sensor 层。
