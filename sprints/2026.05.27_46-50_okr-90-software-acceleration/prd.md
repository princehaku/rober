# OKR 90 Software Acceleration PRD

## 1. 背景

CEO 目标是“所有 OKR 必须完成到 90% 以上”。当前 `OKR.md` 的真实状态是：O6=0%、O7≈5%、O5≈80%、O1≈83%，O2/O3/O4 已按软件侧约 99% 归档但等待真实现场验证。

这意味着当前最有效的软件推进路径不是继续堆 O5 控制面 wrapper，也不是声称 O1 已硬件完成，而是先把 O6 建成云端数据底座，再让 O7 真实消费 O6 的任务、事件、轨迹、标注和推理结果。O5/O1 需要并行准备真实证据清单，但超过 90% 的判定必须等待真实材料。

## 2. 产品目标

本轮后续工程目标分三层：

1. O6 软件侧从 0% 推进到可验收 MVP：云端能接收、存档、查询任务记录和感知事件；大对象只保存 OSS `evidence_ref`；标注 API 和模型推理 API 有可测 contract；PC/手机能通过 REST 或 WebSocket 消费统一数据源。
2. Objective 7 软件侧从约 5% 推进到可运营的 mock/软件证据链：PC 端能看到实时地图状态、电梯状态、历史路线回放、标注工作流、ASR/TTS 状态、手控/寻路 draft 状态，所有数据来自云端 API 或明确 mock feed。
3. Objective 5 和 Objective 1 明确 90% 以上证据边界：没有真实公网/4G/production/OSS live traffic/真实手机/browser/真实 WAVE ROVER/UART/HIL，不允许把进度标成 90% 以上。

## 3. 用户价值

面向普通手机用户：

- 任务记录可追溯：用户和售后能查到任务何时开始、何时失败、失败原因和是否需要人工介入。
- 异常可解释：网络问题、机器人问题、路线问题、电梯问题和推理问题可以被区分。
- 不要求懂 ROS2：状态、历史、失败原因通过云端和 UI 展示。

面向运营和开发者：

- PC 端能回放历史轨迹和关键帧，定位问题不依赖现场口述。
- 标注链路形成训练数据飞轮，能持续改进电梯门状态、楼层识别和障碍物判断。
- 推理结果和人工标注都进入同一事件存档，便于对照模型误判。

## 4. O6 需求范围

O6 必须交付的软件侧能力：

- 安全隧道状态：Orange Pi 或 mock board 上报 tunnel online/offline/reconnecting 状态；真实 frp/WireGuard/ngrok 可后续替换。
- 任务存档：云端保存 `robot_id`、`task_id`、`date`、任务状态、开始/结束时间、失败原因。
- 感知事件存档：路线帧、关键帧、检测结果、电梯门状态、楼层证据、失败原因按时间线写入事件表或等价持久层。
- 大对象引用：摄像头帧/快照等只保存 `evidence_ref`、bucket/region/prefix 或 mock URI，云端数据库不直接存大文件。
- 标注 API：支持创建标注任务、查询待标注项、提交标注结果、导出训练数据描述。
- 推理 API：支持电梯门开/关、楼层识别等 CPU/mock/external-provider 模式；推理结果写入事件存档。
- 查询 API：历史任务列表、任务详情、轨迹数据、事件流、标注状态。

## 5. O7 需求范围

O7 必须消费 O6 数据底座，不绕过云端直连小车：

- 实时地图与机器人位置：展示当前位置、路线偏离状态、刷新延迟字段；无真实位置时显示 `mock_feed` 和 `not_proven`。
- 电梯状态展示：等待、进入、运行中、到达楼层、驶出、人工接管原因和楼层证据。
- 历史路线回放：从云端拉取任务轨迹和事件流，支持逐帧回放位置、速度、关键帧截图和状态转移。
- 数据标注界面：展示待标注帧/关键帧/检测截图，提交电梯门状态、楼层信息、障碍物类型。
- ASR/TTS 调试：展示 ASR 输入流状态和 TTS command draft；真实音频设备未验证时必须显示 `not_proven`。
- 手控/寻路下发：只能走云端 API，默认 `safe_to_control=false`；真实控制必须等 Robot/Hardware 安全准入。

## 6. Objective 5 和 Objective 1 的 90% 边界

Objective 5 只有在以下真实材料出现后，才允许超过 90%：

- 真实公网 HTTPS/TLS endpoint。
- 真实 4G/SIM 链路或等价公网移动网络证据。
- production DB/queue、production worker/cutover、备份恢复或故障降级证据。
- OSS/CDN live traffic 读写证据。
- 真实手机/browser 验收证据。

Objective 1 只有在以下真实材料出现后，才允许超过 90%：

- 真实 WAVE ROVER 上车 UART 链路。
- 串口路径、波特率、JSON 指令、反馈协议、速度映射以 `docs/vendor/VENDOR_INDEX.md` 及其指向资料为准。
- `/cmd_vel` 到左右轮命令、`T=1001` feedback、IMU/battery/odom 边界的 HIL 证据。
- PR #5 2D LiDAR / ToF 硬件材料和接入证据。

本 PRD 明确：`software_proof`、`software_proof_docker_only`、mock feed、local stub、UI contract 不能替代上述真实材料。

## 7. 非目标

- 不在本 sprint planning 中改产品代码、测试代码、硬件配置或 `OKR.md`。
- 不承诺真实生产部署已经完成。
- 不承诺真实 WAVE ROVER、真实 Orange Pi、真实 4G、真实公网、真实 RTC/视频或真实电梯路线已经跑通。
- 不把 O2/O3/O4 已归档的软件侧约 99% 重新计为现场完成。

## 8. 验收标准

后续工程完成后，允许更新 OKR 的前提是有可复验的命令输出和证据边界：

- O6：API/schema/test 能证明任务、事件、对象引用、标注、推理和查询链路闭环；证据可为 Docker/local software proof。
- O7：PC 端能消费 O6 API 并展示六类运营能力；真实能力不足处必须显示 `not_proven`。
- O5：若无真实公网/4G/production/live traffic，只能保持软件侧改进，不超过 90%。
- O1：若无真实 WAVE ROVER/UART/HIL/PR #5 硬件材料，只能保持软件侧或准备状态，不超过 90%。
