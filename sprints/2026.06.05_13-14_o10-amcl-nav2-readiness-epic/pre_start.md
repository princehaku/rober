# Pre Start: O10 AMCL/Nav2 Readiness Epic

## sprint_type

sprint_type: epic

## 收口时间与来源

- Sprint：`sprints/2026.06.05_13-14_o10-amcl-nav2-readiness-epic/`
- 计划时间：2026-06-05 13-14 CST
- Product owner：`product-okr-owner`
- 本轮角色：只负责产品计划、范围边界、验收口径和 owner 派单，不写产品代码、测试代码、硬件配置或上一轮 sprint 文件。
- 当前约束：上一轮 `12-13_o10-delivery-readiness-path-contract-epic` 仍有未提交改动，本轮不得覆盖、回滚或修改上一轮文件。

## 用户价值和产品北极星

本轮继续服务 `rober` 北极星：普通手机用户把垃圾交给低成本小车，小车沿固定路线送到垃圾站/垃圾桶点位，必要时通过 assisted elevator 完成跨楼层，并在不确定时安全停止、请求人工协助和留下可复盘证据。

本轮的用户价值不是再证明接口能读到 latest JSON，而是把 O10 从“路径契约已锁定”推进到下一段可执行材料：

- 地图材料能被 AMCL/Nav2 readiness 链消费，形成 no-motion 定位/规划前置证据。
- PC 运营端能用浏览器按钮级 workflow 触发和查看 proof，而不是只靠 curl/API smoke。
- 电梯 assisted delivery 有真实/受控图片 manifest 和 eval 决策门，不再只扩 taxonomy 或 fixture。
- stop-first HIL 明确现场安全前提；满足则低速 pulse，不满足则升级 CEO 决策 blocker。

## OKR 映射和方向判断

- 最低完成度 Objective：O10 受控送达闭环实战，约 7%。
- 方向判断：继续，且从 `KR-O10-Path-Contract-Lock` 调整到 `KR-O10-AMCL-Nav2-Readiness`、`KR-O10-PC-Button-Workflow`、`KR-O10-Elevator-Image-Eval`、`KR-O10-Stop-First-HIL-Gate` 和 `KR-O10-Delivery-Readiness-Chain`。
- 不更新 `OKR.md`：本轮只创建计划文件，待一线 owner 产生验证材料并完成 `tech-done.md / side2side_check.md / final.md` 后再由 Product 收口更新 OKR。

## 最近两轮 blocker / 剩余风险扫描

| Sprint | 已完成或已解决 | 剩余风险 | 本轮处理 |
| --- | --- | --- | --- |
| `2026.06.05_08-09_o9-pc-smoke-map-runtime-epic` | PC 8788 same-origin scan-proof live smoke；no-motion `/scan` once、`/map` once、map metadata、PGM/YAML 落盘；latest/readback clean success。 | latest JSON 实际路径漂到 `/root/rober/runtime/map_lifecycle_latest.json`；不证明 AMCL/Nav2、continuous radar、PC WASD、HIL。 | 路径 drift 已由 12-13 解决，本轮不得重复消费；只作为 AMCL/Nav2 readiness 前置材料。 |
| `2026.06.05_12-13_o10-delivery-readiness-path-contract-epic` | canonical latest JSON 锁定为 `/root/rober/onboard/runtime/map_lifecycle_latest.json`；canonical map artifacts 锁定为 `/root/rober/onboard/runtime/maps`；8787 refresh/latest 与 8788 map latest readback 通过。 | AMCL/Nav2、浏览器按钮级 workflow、电梯真实/受控图片、stop-first HIL 未完成。 | 本轮直接推进这四段；latest/readback/status 不再作为主任务。 |

重复 blocker 判断：

- `latest JSON path drift` 已在 12-13 完成，不允许成为 13-14 主 blocker。
- `refresh/latest/readback/status` 已有多轮材料，不再作为 O9/O10 涨分抓手。
- `tsx_ipc_pipe_enotsup` 已由 08-09 的 `TMPDIR=/tmp` 8788 启动口径解除，不允许重复消费。
- `AMCL/Nav2 等 canonical path + 真实 map/waypoint`、`缺真实/受控电梯图片 manifest`、`缺现场看护/净空/急停/授权` 是当前有效 blocker。

## 本轮核心抓手

本轮是跨 owner Epic，但不是扩大范围的“大而全”。核心抓手是四个窄口径功能材料和一个 Product 收口链：

1. AMCL/Nav2 readiness：基于 canonical latest 指向的真实 map artifact，形成 map quality、waypoint manifest、AMCL/Nav2 lifecycle 或 fixed-route dry-run 的 no-motion 证据。
2. PC browser workflow：把 PC proof 从 API smoke 推到浏览器按钮级触发与展示，含 fail-closed 字段、截图或 Playwright/浏览器日志。
3. Elevator image eval：真实/受控电梯图片 manifest + OpenCV eval，输出误判、漏判、不可判定和人工接管策略。
4. Stop-first HIL gate：现场安全条件满足才低速 pulse；否则产出 CEO 决策 blocker，不写成 HIL pass。
5. Delivery-readiness chain：Product 最后把各 owner 结果串成 pass/blocked、证据链接、证据边界和下一步低速受控送达条件。

## 优先级

| 优先级 | Owner | 任务 |
| --- | --- | --- |
| P0 | Robot Algorithm Engineer + Robot Software Engineer | AMCL/Nav2 readiness，主线第一优先级。 |
| P0 | Full-stack Software Engineer | PC browser button workflow，解除 API-only 证据缺口。 |
| P0 | Robot Algorithm Engineer | 真实/受控电梯图片 manifest 与 eval。 |
| P1 | Hardware Infra Engineer + Full-stack Software Engineer | stop-first HIL gate；若现场安全条件缺失，升级 CEO 决策。 |
| P0 | Product Manager / OKR Owner | `tech-done.md`、`side2side_check.md`、`final.md` 阶段收口与 OKR 更新。 |

## 风险、阻塞和证据链缺口

- AMCL/Nav2：如果 map artifact 太窄、map frame/waypoint 不一致或 lifecycle 不可启动，只能写 `blocked_with_root_cause`，不得写地图可导航。
- PC browser：如果只有 curl/API 通过而无浏览器点击、Playwright 或截图日志，只能算 software guard，不算 user/browser workflow。
- 电梯图片：如果没有真实/受控图片资源，必须升级 CEO 决策 blocker；不能继续扩 fixture 当作 field eval。
- HIL：缺现场看护、净空、急停/断电或授权时，不能低速 pulse，也不能写 HIL pass。
- 安全字段：所有 no-motion 材料必须保持 `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`，除非 Hardware 在受控 HIL 中用证据明确改写某个字段。

## 需要创建或更新的 sprint 文档

本轮已进入 Epic 计划阶段，必须按顺序完成：

- 已创建：`pre_start.md`
- 已创建：`prd.md`
- 已创建：`tech-plan.md`
- 待 Engineer 执行后更新：`tech-done.md`
- 待 Product 验收后更新：`side2side_check.md`
- 待阶段收口后更新：`final.md`

