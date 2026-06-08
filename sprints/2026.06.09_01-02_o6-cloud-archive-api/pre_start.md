# O6 Cloud Archive API Epic Pre-Start

## sprint_type

sprint_type: epic

## 背景

Automation `1小时OKR` / ID `1-okr` 启动新一轮迭代。CEO 指令是：上位机可通过 `ssh root@192.168.1.11 -p 37878` 访问；开始新迭代，继续完成代码和功能；设计好才能开始写功能点；功能点不完善不允许开始写代码；代码不完美不允许提交；结束后需要 git commit 和 push。

本阶段只做设计与验收口径，不写产品代码。当前工作区已有未提交 O6 local/mock cloud archive API 雏形，涉及 `remote_cloud_relay.py`、测试、`cloud-relay/README.md`、`docs/product/pc_tools_workstation.md` 和 `docs/interfaces/o6_cloud_archive_api.md`。本 sprint 的产品定位是把该雏形收敛为 O6 MVP 的本地/mock file-backed archive API epic，先给 O7 route replay / labeling / voice / safe command 提供 O6-shaped 数据源。

## 用户价值

PC 运营调试平台和后续手机端不应继续依赖散落 fixture 或 UI 侧假数据。O6 MVP 先提供统一的任务归档数据形状，让 route replay、标注、语音、安全命令等 O7 能力都能从同一份任务记录、轨迹帧、事件和 evidence refs 开始消费。

这轮价值是"形成可测试的数据源契约"，不是"证明真实云后端上线"。用户和工程团队能明确知道：本地 mock API 已能支撑后续功能设计与软件测试，但真实云 DB、OSS、生产网络、4G 和机器人控制仍未证明。

## OKR 映射

- 主 Objective：O6 云端核心后端--数据存档、模型推理与打标平台。
- 当前最低 Objective：O6，OKR 4.1 快照为 0%。
- 本轮直接覆盖：
  - O6-KR2：任务记录和感知事件按 `robot_id / task_id / date` 查询的 MVP 入口，本轮先做本地 file-backed 查询而非真实云 DB。
  - O6-KR3：大对象只保留 `evidence_refs[]` 引用形状，本轮不连接真实 OSS。
  - O6-KR6：REST API 供 PC 端和手机端消费历史任务列表、任务详情、轨迹数据、事件流的最小形状。
- 本轮不覆盖：
  - O6-KR1 真实隧道接入和在线/离线感知。
  - O6-KR4 真实标注提交 API。
  - O6-KR5 真实或外部模型推理接口。
  - 真实 DB、真实 OSS、production cloud、4G、TLS、HIL 或 delivery success。

## 本轮核心抓手

把 O6 API 的最小数据契约、mock 边界、安全红线和 full-stack 执行验收写清楚，然后交给 `full-stack-software-engineer` 单线闭环实现和验证。API 必须明确：

- `POST /api/o6/archive/tasks`
- `GET /api/o6/archive/tasks`
- `GET /api/o6/archive/tasks/<task_id>`
- `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` file-backed store 注入入口。
- 响应固定 `real_cloud_db_connected=false`。
- 响应固定 `real_oss_connected=false`。
- 响应固定 `connects_cloud_production=false` 和 `robot_control_executed=false`。

## 优先级

P0：先把 O6 MVP archive API 作为 O7 数据源做成可验证 software proof，并保持所有真实云/控制能力 fail closed。

P1：同步接口和产品文档，让 O7 route replay / labeling / voice / safe command 后续可以明确消费这条 O6-shaped 数据源。

P2：真实云 DB、OSS、隧道、production deploy 和 git commit/push 只在工程实现验证全部通过后进入收口，不在本设计阶段冒进。

## Owner 与执行方式

- Product owner：`product-okr-owner`，负责本轮设计、验收口径和 sprint 文档。
- 主责 Engineer：`full-stack-software-engineer`，负责 API / 文档 / 测试单线闭环。
- 咨询角色：本轮不需要硬件、算法或 ROS2 平台并行咨询。任务不涉及 WAVE ROVER、Orange Pi 引脚、电压、UART 波特率、底盘协议、固件或机械尺寸事实。

## Sprint 文档

本 epic 需要按顺序形成：

- `pre_start.md`：本文件，记录启动背景、用户价值、OKR 映射、owner 和边界。
- `prd.md`：定义 O6 MVP archive API 的产品需求和验收口径。
- `tech-plan.md`：定义执行边界、接口影响、验收命令、风险边界和 OKR 最低优先级核对。
- `tech-done.md`：Engineer 完成代码和测试后补充实际改动、验证结果和偏差。
- `side2side_check.md`：验收阶段对照 CEO 需求、O6 边界和 O7 消费需求。
- `final.md`：收口阶段记录是否允许 commit/push、OKR 进度建议和剩余风险。

## 启动风险

- 当前工作区已有未提交代码和文档雏形，本轮设计不得误改或回滚这些文件。
- 本 sprint 的 API 是 local/mock file-backed store，不得在文档或 UI copy 中写成真实云存档、真实 DB、真实 OSS 或 production ready。
- 真实上位机 SSH 可达性是 CEO 给出的上下文；本设计阶段不 SSH、不操作真实硬件、不验证串口或底盘。
- 如果工程实现阶段测试失败，Engineer 必须定位、修复并复测；不得把第一轮失败直接作为收口。
