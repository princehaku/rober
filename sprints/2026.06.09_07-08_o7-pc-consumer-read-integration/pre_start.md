# O7 PC Consumer Read Integration Epic Pre-Start

## sprint_type

sprint_type: epic

## 背景

上轮 `sprints/2026.06.09_06-07_o6-consumer-read-api/` 已将 O6 统一消费侧 read contract 做成 local/mock software proof，并确认：

- `GET /api/o6/consumer/tasks` 已存在
- `GET /api/o6/consumer/tasks/<task_id>` 已存在
- `proof_status=not_proven`、`safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false` 已明确
- `docs/product/pc_tools_workstation.md` 与 `cloud-relay/README.md` 已更新为“新消费面优先”说明

PC 端当前仍有明显价值改造点：还未在 O7 实现中统一改为基于 consumer read 面的任务列表与详情聚合，仍存在 `archive/events/evidence/labels/tunnel` 分散读取与重复解释的风险。

## 方向判断

本轮方向为：**优先推进 O7（PC 运营调试）的接入可执行性，承接 O6-KR6 的统一消费侧能力；不继续 O6 production 化。**

不继续 O6 production 化的理由：

- 当前证据边界仍停留在 local/mock（无真实 cloud DB、OSS、生产证书、4G 隧道、手机/上车验证）。
- 本轮目标是降低 O7 前端/调试链路复杂度；生产化 O6 会引入更大链路前置（鉴权/持久层/网络），本轮最小目标无法闭环。
- O7 如果先不统一消费模型，会在后续标注/回放/ASR/TTS/Safe command 模块反复重复拼接低层 O6 endpoint，导致返工与状态语义漂移。

## 用户价值和产品北极星

产品北极星是“手机用户能稳定下达/查看送达任务，PC 运营能高质量复盘与排障”。  
本轮把 O6 已有历史任务/轨迹/事件/标注/推理/tunnel 信息，作为 O7 的单一消费入口，减少 PC 侧 join 成本，提高状态解释一致性，并为 O7 的真实化改造预留一条清晰升级路径。

## 最近 blocker 扫描

按规则扫描最近两轮 `final.md`：  

- `sprints/2026.06.09_06-07_o6-consumer-read-api/final.md`
- `sprints/2026.06.09_05-06_o6-event-evidence-archive/final.md`

结论：两份文档均是 software proof 收口，均未声明可复用的 `blocked root cause`；未出现同一 blocker 重复消费。

## 本轮核心抓手

1. 在 O7 产品边界层明确“PC 任务列表与任务详情首选消费 `GET /api/o6/consumer/tasks` + `GET /api/o6/consumer/tasks/<task_id>`”。
2. 指定 O7 前端显示字段映射与 `view=summary` 默认策略，避免手机/PC 直接感知不必要 payload 与未确认字段。
3. 锁定 O7 与 O6 消费层共享状态语义（`task_status_summary`、`labeling_status`、`inference_status`、`tunnel_status_summary`、`proof_boundary`）。
4. 明确失败时 fail-closed 输出，不把 `missing labels / inference / tunnel` 解释成真实“无异常”。
5. 明确本轮不改动真实控制、真实数据库、真实鉴权、真实机器人能力。

## 目标 KR 与范围

### 本轮直接推进（设计）

- `O6-KR6`：消费侧统一读模型稳定消费面（保持 local/mock proof 边界）
- `O7-KR1`：PC 实时图/轨迹字段读取前，明确消费路径前提
- `O7-KR2`：PC 电梯状态显示字段读取前，明确消费路径前提
- `O7-KR3`：PC 路线回放与轨迹任务列表/详情读取前，明确消费路径前提

### 本轮不推进（生产化）

- `O6-KR1~KR5` 的真实云化实现（真实 DB、真实 OSS、TLS、4G 生产链路）
- `O7-KR6` 的真实手控/寻路下发控制面

## 本轮优先级

- P0：明确 O7 全链路消费入口（list/detail）与字段契约
- P0：定义 O7 对 O6 consumer read 的容错与 fail-closed 行为
- P1：给 O7 增加 `summary/detail` 与 `include` 的数据裁剪规则
- P2：补齐 PC 文案边界（safe_to_control/proof status）

## 本轮目标收口与验收前置

本轮属于设计阶段。主节点在收到这三份文档后即可指派 `full-stack-software-engineer` 进入实现阶段。  
在未完成以下文件的最小设计齐备前不允许进入编码：

- `pre_start.md`（已生成）
- `prd.md`（已生成）
- `tech-plan.md`（已生成）

## 依赖与责任

- Product owner：`product-okr-owner`（本页）
- 主责实现 owner：`full-stack-software-engineer`（PC 接口消费与文档收口）
- 只读咨询：`robot-software-engineer`（确认 O6 consumer payload 语义与边界不漂移）

## 风险与残留

- 本轮改造只做消费层收敛，不改变 O6 实体能力来源的真实程度。
- 真实云 DB、真实 4G、真实手机生产验证缺位，仍属于上游阻塞，不在本轮 scope 内消除。
- 如果下一步代码把 consumer read contract 与旧分散接口混用，会造成 O7 页面状态冲突，需要 side2side 对照修复。
