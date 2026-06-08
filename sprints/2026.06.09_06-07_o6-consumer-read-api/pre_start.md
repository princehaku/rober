# O6 Consumer Read API Epic Pre-Start

## sprint_type

sprint_type: epic

## 背景

Automation ID `1-okr` 启动新一轮迭代。CEO 明确要求：上位机可通过 `ssh root@192.168.1.11 -p 37878` 访问；开始新一轮迭代；设计好才能开始写功能点；功能点不完善不允许开始写代码；代码不完美不允许提交；结束后需要 `git commit` 和 `git push`。

本阶段只做产品/设计，不写产品代码。最近几轮 O6 已完成 local/mock software proof：

- `sprints/2026.06.09_01-02_o6-cloud-archive-api/`：task archive list/detail/write
- `sprints/2026.06.09_02-03_o6-labeling-api/`：labeling write/list/detail
- `sprints/2026.06.09_03-04_o6-model-inference-api/`：inference write into events
- `sprints/2026.06.09_04-05_o6-tunnel-online-status/`：tunnel online/offline snapshot
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/`：event/evidence write/query

这些能力已经证明 O6 写入口和分散查询入口存在，但还没有形成给 PC/手机统一消费的读模型。当前 O7 和后续手机端如果直接拼接多个低层 endpoint，会把分页、筛选、状态解释、字段白名单和 fail-closed 逻辑重复实现一遍，后续返工风险高。

## 用户价值和产品北极星

产品北极星不变：普通用户最终只通过手机就能理解机器人当前是否在线、最近做了什么、任务是否失败、证据在哪里、哪些内容还只是软件 proof；PC 运营和研发则需要同一套后端查询面做回放、排障、标注和状态追踪。

本轮用户价值是把 O6 已有 task / event / evidence / label / inference / tunnel 数据整成一个统一 REST 查询面，让 PC/手机消费方不再自己拼多个底层接口，也不需要猜测哪些字段可展示、哪些状态仍是 `not_proven`。

## 最近事实与方向判断

- `OKR.md` 4.1 当前最低 Objective 是 O6，进度 0%。
- 最近连续 5 轮 sprint 已补齐 O6-KR1/KR2/KR3/KR4/KR5 的 local/mock 片段证据，但消费侧 O6-KR6 仍未单独成型。
- `docs/interfaces/o6_cloud_archive_api.md` 已存在 task/event/evidence/label/inference/tunnel 的低层 contract。
- `docs/product/pc_tools_workstation.md` 已明确 PC 需要历史任务、轨迹、事件、标注、语音和安全命令视图，但当前多为 preview/fixture 或分散 probe。

方向判断：**继续推进 O6，并优先落实 O6-KR6。**
原因不是再增加写能力，而是把现有 O6 software proof 收敛成统一读能力，降低 O7 和手机消费层的重复拼装成本。

## 本轮聚焦 KR

- 直接推进：`O6-KR6`
  - 给 PC/手机提供统一 REST 查询面。
  - 覆盖历史任务列表、任务详情、轨迹数据、事件/证据/标注/推理状态、隧道在线状态。
- 依赖但不新增完成声明：
  - `O6-KR1`：仅复用 tunnel online status 的既有 local/mock 数据。
  - `O6-KR2`：仅复用 task/event archive 的既有 local/mock 数据。
  - `O6-KR3`：仅复用 evidence refs 摘要。
  - `O6-KR4`：仅复用 labeling summary。
  - `O6-KR5`：仅复用 inference event summary。

## 本轮核心抓手

定义一个 O6 consumer read model，让消费方优先调用聚合查询接口，而不是直接面向多条底层写/读接口。该 read model 必须同时满足：

- PC 和手机共享同一份任务摘要字段；
- 任务详情一次返回 timeline、evidence、labeling、inference、tunnel 状态摘要；
- 所有成功响应继续固定 `proof_status=not_proven`、`safe_to_control=false`、`connects_cloud_production=false`；
- 缺底层数据时 fail-closed 返回 `blocked_not_proven` 或空集合，不伪造成功态。

## Owner 与执行方式

- Product owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 咨询角色：`robot-software-engineer`
  - 仅在需要确认 `remote_cloud_relay.py` 内聚合方式是否破坏现有 O6 store 语义时提供只读咨询。
  - 不作为并行实现 owner。

本轮采用单 owner 单线闭环，因为目标集中在云 relay REST API 和消费侧 contract，不涉及硬件、算法或 ROS2 主链路耦合改动。

## 优先级

- P0：统一任务列表和详情查询 contract
- P0：统一返回 tunnel / labeling / inference / evidence / event / trajectory 摘要
- P0：定义筛选、排序、分页上限和 fail-closed 规则
- P1：为后续 PC/手机保留 `include=` 与 `view=` 之类的轻量查询模式，避免一次返回过大 payload
- P2：真实云 DB、WebSocket、真实分页 cursor、真实生产鉴权、真实手机/UI 验收留待后续 sprint

## 需要创建或更新的 sprint 文档

- `pre_start.md`：本文件，锁定本轮目标、价值、方向判断和 owner
- `prd.md`：定义用户场景、接口能力、验收口径和范围边界
- `tech-plan.md`：定义主责 Engineer、文件范围、接口影响、验收命令、风险边界和 OKR 最低优先级核对
- `tech-done.md`：实现完成后由 Engineer 补充
- `side2side_check.md`：验收阶段补充
- `final.md`：收口阶段补充

## 风险、阻塞与证据链缺口

- 当前没有真实 production cloud、真实 DB、真实 OSS、真实公网 TLS、真实 4G 或真实手机设备证据。
- O6 现有能力大多是 local/mock proof，本轮必须把这一点写进所有聚合返回边界，不能被 UI 误解成真实线上能力。
- CEO 给出的 SSH 可达性是环境上下文，不构成本轮产品设计的验收证据；本阶段不 SSH、不改硬件、不跑真实板端验证。
- `git commit` / `git push` 是工程收口动作，本设计阶段只输出可执行设计，不提前提交。
