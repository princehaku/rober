# O3 Live Localization Sensor Smoke PRD

## 用户价值

当前用户最需要的是把“为什么 no-motion proof 还不能生成”变成一条新的现场可执行检查链，而不是继续消费 O5 production readiness 或 O1 historical/HIL wrapper。只有先确认真实上位机当前同窗是否真的有 `/scan`、`/amcl_pose` 和 map 相关 TF，后续 `/api/nav2/proof/refresh` 的失败才会从泛化 blocker 收敛成可修复的具体链路问题。

## 产品北极星

北极星不变：机器人最终要完成可复验的现场路线、定位、送达与返回闭环。本轮只补最前面的 live localization readiness 证据段，目标是让 no-motion path proof 进入“当前同窗可判定”状态，而不是继续围绕历史 latest、support packet 或 wrapper 解释。

## OKR 映射和方向判断

- O5：当前最低，约 `~85%`，但方向判断为 **暂停**。原因是最近 `2026-07-11 03:40` sprint 已证明当前没有新的真实 external production evidence，继续 O5 support-only 只会重复消费 blocker。
- O3 现场定位 smoke lane：方向判断为 **继续**。因为 `2026-07-11 04:36` sprint 已把 blocker 收敛到 `/scan`、`/amcl_pose` 和 TF/localization readiness，本轮是最短的下一跳。
- O1：方向判断为 **暂停**。原因是当前需要的是 live localization chain，而不是再消费 historical wheel feedback、map comparator 或 HIL-support-only 包装。
- O6/O7：方向判断为 **等待新 O3 材料**。本轮不新增 surface、readback 或 checklist。

## KR 拆解、更新和历史边界

1. 新增一条当前同窗 live localization smoke 任务，产出 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 的 ready / blocked 事实。
2. 在 no-motion 边界内重跑 `/api/nav2/proof/refresh`，把 planner/path proof 的 blocker 与 localization 链绑定起来。
3. 定义下一条现场执行命令，只允许是定位链 smoke 或 refresh readback，不允许进入任何运动控制。
4. 不归档任何 KR；本轮仍处于“为后续 route/path 证明准备真实输入”的阶段。

已完成 KR 的历史记录位置本轮不变，继续以既有 sprint `final.md` 为证据来源；本轮不会移动 `OKR.md` 历史区，因为尚无新的完成证据。

## 本轮核心抓手

核心抓手只有一个：把上一轮泛化的 `localization_not_ready_for_path_generation` 拆成真实上位机可复验的同窗 smoke 项，并以此决定 `/api/nav2/proof/refresh` 是否值得继续重跑。

## 需要做什么

- 在真实上位机 no-motion 环境执行 live topic/TF smoke；
- 只读确认 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link`；
- 在上述检查之后重跑 `/api/nav2/proof/refresh`；
- 输出安全摘要、blocked reasons、下一条命令和 proof boundary；
- 严禁任何控制面、导航执行或底盘运动。

## 优先级和验收口径

优先级从高到低：

1. `/scan` 同窗是否可观测；
2. `/amcl_pose` 同窗是否可观测；
3. `/tf map->odom` 是否存在；
4. `/tf map->base_link` 是否存在；
5. `/api/nav2/proof/refresh` 重跑结果；
6. blocker 分层与下一条命令。

验收通过最低标准：

- 计划文档明确 `sprint_type: epic`；
- `tech-plan.md` 包含 `OKR 最低优先级核对`；
- 文档明确包含 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link`、`/api/nav2/proof/refresh`；
- 文档明确包含 `safe_to_control=false`、`delivery_success=false`；
- 文档明确禁止 `/cmd_vel`、`/api/base/manual`、`NavigateToPose` 与真实运动；
- 文档为主责 Engineer 给出文件范围、接口边界、验收命令和 proof boundary。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- 只读咨询：`rober-hardware-engineer`
- 只读咨询：`robot-algorithm-engineer`

## 风险、阻塞和需要补齐的证据链

- 风险 1：live `/scan` 仍未出现，则本轮只能把 blocker 收敛到传感器/bringup 链，不能继续声称 localization ready。
- 风险 2：`/amcl_pose` 或 `map->odom` 缺失，则问题在 map source、AMCL lifecycle 或 TF 发布链，不是 planner 层单点故障。
- 风险 3：即使 smoke ready，`/api/nav2/proof/refresh` 仍可能因为 planner lifecycle 或 map 内容问题 fail-closed；那时下一轮应继续 O3/O2 前置修复，而不是回到 O5/O1 wrapper。

需要补齐的证据链：

- 当前同窗 `/scan` 观测事实；
- 当前同窗 `/amcl_pose` 观测事实；
- 当前同窗 `map->odom` / `map->base_link` TF 事实；
- 当前同窗 no-motion refresh summary；
- 若仍 blocked，则新的 root cause 分层。

## 需要创建或更新的 sprint 文档

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- 后续执行后由对应 Engineer 更新 `tech-done.md`
- 若形成可验收结果，再补 `side2side_check.md` 与 `final.md`
