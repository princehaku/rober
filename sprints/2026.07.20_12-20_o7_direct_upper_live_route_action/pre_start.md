# O7 Direct Upper Live Route Action - Pre Start

## Sprint metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/`
- Product owner：`product-okr-owner`
- 唯一 Implementation owner：`full-stack-software-engineer`
- 执行方式：单 owner 串行闭环；本轮不派 `robot-algorithm-engineer` 或 `rober-hardware-engineer`
- 优先级：`P0`，主推 O7/O6，O1 supporting；O5 provider lane 暂停
- 计划状态：`ready_for_direct_upper_read_only_pre_gate_then_exactly_one_action`

## 用户价值与产品北极星

普通用户需要的不是更多 readiness、wrapper 或回执说明，而是一次在 operator 看护、路线清空、物理位置受限条件下，能追溯到同一 28-pose 固定路线 lineage 的真实动作与读回。本 sprint 的北极星是：把“PC 合同已存在”推进为“上位机真实接收一次受控 Nav2 动作，并留下可审计的 terminal、stop 与底盘反馈材料”，同时保留可停、no retry 和 fail-closed 边界。

## 开工事实与上轮承接

已读并采用：

- `AGENTS.md`、`OKR.md`；
- `docs/vendor/VENDOR_INDEX.md`；本轮不修改 UART、WAVE ROVER 指令、波特率、引脚、电压或硬件配置；
- 上轮 `tech-done.md`、`side2side_check.md`、`final.md`；
- `docs/product/pc_tools_workstation.md` 最新 `2026-07-20 O7 路线用户动作回执` 合同段。

上轮真实结论是 `local_loopback_interceptor_header_only_http_400`：7072 请求未进入 workstation handler，remote execute/stop 都是 `0`，因此上轮 `user_action_delta=false`，旧 action window 已消费且永久禁止补跑。本轮 CEO 已明确批准不经过该 loopback interceptor 的上位机/SSH 执行环境，并给出新的 fresh bounded-motion authorization，所以这是合法的新 action window，不是重试上轮 action。

## Fresh authorization 与冻结 identity

- SSH transport：`ssh root@192.168.1.11 -p 37878`
- 上位机服务：SSH 内部只访问 `http://127.0.0.1:8787`
- 现场条件：operator 全程看护、路线已清空、小车物理位置受限、允许本轮一次受控运动
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `run_id=run_o7_direct_upper_live_route_20260720_02`
- `action_id=action_o7_direct_upper_nav_20260720_02`
- `authorization_ref=ceo_20260720_1220_bounded_motion_operator_watch_route_clear_v2`

task/route 沿用已接受的 28-pose lineage；run/action/authorization 必须使用上述新值，不得复用上轮已消费的 `run_o7_full_stack_live_route_user_action_20260720_01`、`action_o7_live_nav_20260720_01` 或 v1 authorization。

## OKR 映射与方向判断

- O7（约 93%）：`继续`。核心缺口是 current live user action、route terminal 与用户可审计回执；本轮直接执行，不再新增 surface。
- O6（约 93%）：`继续`。以同 task/route 的 live action/readback artifacts 为后续归档消费输入，本轮不新增 O6 wrapper。
- O1（约 94%）：`supporting`。只用 stop 与 current base feedback 判断是否出现同窗口硬件反馈；没有 HIL 完整证据时保持 flat。
- O5（约 85%，当前最低）：`暂停`。provider blocker 已消费 `2/2`，禁止第三轮 wrapper、diagnostic、preflight 或 live tunnel 包装。
- KR 历史归档：本轮开工时没有新增已完成 KR；只有 Product acceptance 证明新 mission-grade delta 后才决定是否更新百分比或归档，证据位置将是本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md` 与真实 artifacts。

## 本轮核心抓手

唯一抓手是从上位机本机网络命名空间直连 `127.0.0.1:8787`：先只读 health、status、Nav2 latest，通过 pre-gate 后 exactly-one `POST /api/nav2/goal/execute`，请求显式包含 `confirm_navigation_execution=true`；动作返回、失败、超时或 unknown 后最多一次 `POST /api/base/stop`；最后只读 Nav2 latest 与 base feedback。SSH、health 或任何 wrapper 仅是 gate/transport，不是业务结果。

## 范围与责任边界

`full-stack-software-engineer` 单线负责远端只读 gate、唯一动作、stop、读回、artifact 固化、合同回归和 `tech-done.md`。Algorithm/Hardware 此前同类派单 stall，本轮不重复派发；只有真实 terminal/feedback 事实出现后，Product acceptance 再请求其专业判读。

默认 run-only：Engineer 不得修改 product code、上车配置、ROS2、hardware、UART 或已有产品文档。只有实际验证暴露可复现的明确合同 bug 时，才允许在 tech-plan 的条件范围内做最小修复，并必须先保存失败 artifact、写清根因、运行完整 workstation regression；不得为绕过 live 失败而修改合同。

## Go / no-go 与 anti-repeat

read-only pre-gate 必须同时满足：SSH 单次连接成功；`GET /health`（若部署合同只提供 `/api/health`，允许记录一次只读兼容探测但不得改服务）返回可解析 JSON；`GET /api/status` 与 `GET /api/nav2/goal/execution/latest` 返回可解析、安全、可关联当前 upper runtime 的 JSON；没有明确 unsafe/active-motion/route-not-ready blocker；fresh authorization 与 operator 条件仍成立。

任一 pre-gate 失败即 `no-go`：remote execute=`0`、remote stop=`0`，只保存失败事实并收口。通过后 execute invocation 必须 `exactly-one`、`no.retry=true`；禁止换 goal、换 mode、换 endpoint、第二次 execute、manual/free-roam/direct `/cmd_vel`、`/initialpose` 或 UART。stop 最多一次，不因 stop 失败而重发。

## 计划文档链与下一阶段

本轮先创建 `pre_start.md -> prd.md -> tech-plan.md`。计划验收后立即由唯一 owner 执行并更新：

1. `tech-done.md`：实际命令、artifact、调用计数、测试与失败修复循环；
2. `side2side_check.md`：Product 对 terminal、stop、feedback、proof/delta 的逐项裁决；
3. `final.md`：OKR/KR、历史区、风险和下一步收口。

规划文档本身不计业务结果，不提升 OKR，不归档 KR。
