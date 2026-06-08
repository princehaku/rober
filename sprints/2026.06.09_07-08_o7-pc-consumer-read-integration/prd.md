# O7 PC Consumer Read Integration PRD

## 需求目标

本轮目标是把 O7 PC 端从“零散消费底层 O6 endpoint”切到“统一消费 O6 consumer read endpoint”，并把这条统一路径作为 O7 里程碑的默认读取入口。  
这轮只做产品/技术设计，不做实现。

## 为什么先接 O7（不先做 O6 production）

- O6 的 consumer read API 已经把 `tasks/event/evidence/labels/inference/tunnel` 聚合为可消费读模型，并明确了软件 proof 边界。
- O7 的后续模块（回放/标注/ASR-TTS/手控预览）仍主要依赖“任务/轨迹/证据可读链路”，不要求本轮引入真实云 DB 即可开始。
- 继续 O6 production 化会把注意力从“消费面统一”转移到“DB/网络/鉴权改造”，当前缺少可复用的真实生产链路证据，不利于 1 小时迭代交付。

## 用户价值

1. PC 运维与研发不再做重复 join：只调用 `consumer/tasks` 获取任务摘要，点击任务再调用 `consumer/tasks/<task_id>` 获取详情。
2. 统一状态口径，避免 O7 各 tab（轨迹回放、标注、ASR、控制预览）对缺失数据出现不同解释。
3. 缩短迭代路径：后续 O7 的真实生产化只需稳定 `consumer read contract`，而不是重写多个低层消费逻辑。

## 需求范围内（P0）

- O7 文档化消费优先级：`GET /api/o6/consumer/tasks` 与 `GET /api/o6/consumer/tasks/<task_id>`
- PC 页面与组件消费字段定义：
  - 列表：`task_id、robot_id、started_at_ms、finished_at_ms、task_status_summary、latest_event_at_ms、trajectory_frame_count、event_count、evidence_count、labeling_status、inference_status、tunnel_status_summary、selected、query、proof_boundary`
  - 详情：`task_summary、proof_boundary、trajectory、events、evidence、labeling、inference、tunnel_status`
- 手机/PC 轻量读取策略：PC 默认 `view=default`；summary 场景 `view=summary`。
- 失败边界：task 不存在、非法查询、limit 超限、未知 include、query 风险字段（token、/cmd_vel、串口路径、凭证）都必须进入 fail-closed，不可伪造成功态。
- 交互约束：不得在 UI 或文案中解释为真实云生产可控、真实控制可执行、真实 delivery 成功。

## 需求范围外

- 不新增真实 DB/OSS/CDN 路径、真实 4G/公网、真实鉴权体系。
- 不实现真实手控（manual turn）/寻路下发（navigate goal）/robot ACK 处理。
- 不改变 WAVE ROVER、串口、Nav2、ROS2 runtime 或电梯实际控制链路。
- 不新增 Python/Py 文件或老旧脚本执行路径。

## 需求拆解（功能点）

### F1 O7 任务列表统一入口

PC 首屏/任务中心/调试列表默认从 `GET /api/o6/consumer/tasks` 拉取，不再从：
- `/api/o7/route-replay-preview?fixtureJson=...` 直接拼接历史低层
- `GET /api/o6/archive/*` + `GET /api/o6/tunnel/*` 逐条 join

### F2 O7 任务详情统一入口

点击某任务详情时，优先从 `GET /api/o6/consumer/tasks/<task_id>` 一次性读取聚合详情（含轨迹和事件）。

### F3 视图裁剪与可控缺失

当 O7 某 tab 仅需摘要时，使用 `view=summary`。当 PC 需要完整字段时，按 `include=trajectory,events,evidence,labeling,inference,tunnel` 请求并展示。

### F4 统一状态语义映射

在界面中共享统一状态含义：
- `completed_mock / failed_mock / in_progress_mock / unknown_not_proven`
- `labeling_status: pending / partial / labeled / not_available`
- `inference_status: present / absent / not_available`
- `tunnel_status_summary: online / offline / unknown_not_proven`

### F5 fail-closed 文案护栏

任何 `proof_status=not_proven`、`safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false` 条件，不显示“可下发/可控制/已成功交付”类文案；错误态给出阻塞原因。

## O7-KR 映射

- 本轮与 O7 的关系是：`O7-KR3`（历史路线回放）、`O7-KR4`（标注）、`O7-KR5`（ASR/TTS）和 `O7-KR6`（手控预览）都以统一消费面作为数据前提。
- `O6-KR6` 在本轮作为消费层基础，支持 O7 统一读取。

## 验收边界（设计完成判定）

工程可开始前，以下定义必须完成并共享给实施队：
- 完整 endpoint 读取优先级（推荐/备用）
- list/detail 字段映射表
- fail-closed 与证据边界（not_proven / safe_to_control / proof_status）
- 手机/PC 默认查询参数策略
- owner 与文件范围确认

以上全部完成后，`full-stack-software-engineer` 方可进入实现。 
