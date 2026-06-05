# PRD: O10 Delivery Readiness Path Contract Epic

## 用户价值

普通用户最终只看手机/PC 上的“能不能进入受控送达准备”。如果 map proof latest 的路径漂移，operator workflow 可能读到旧材料或读不到材料，后续 AMCL/Nav2、PC 建图控制和 readiness chain 都会建立在不稳定证据上。本轮先修这条契约，避免继续用重复 readback 刷进度。

## 产品目标

把 O10 的第一段 `KR-O10-Path-Contract-Lock` 从风险项推进为可验收材料：

- upper API、helper、PC/文档都明确唯一 map proof latest JSON 路径口径。
- 远端同一命令链能证明 refresh、latest 和文件 readback 一致。
- 安全字段继续 fail-closed，不把 no-motion map proof 写成 Nav2 可跑。

## 非目标

- 不做真实送垃圾。
- 不做 PC WASD 或底盘点动。
- 不做真实电梯图片采集，除非现场材料已经存在。
- 不把 `/map` once、PGM/YAML 落盘或 latest readback 外推为地图可导航、AMCL ready、Nav2 ready 或 HIL pass。

## 验收口径

| 验收项 | 通过标准 | evidence type |
| --- | --- | --- |
| 路径契约 | `POST /api/map/proof/refresh` 和 `GET /api/map/proof/latest` 读写同一个 canonical path，回包暴露 canonical/legacy/compat 边界。 | `robot_runtime_material` 或 `software_guard` |
| 本地护栏 | upper API/map proof 相关 unittest、compileall、diff-check 通过。 | `software_guard` |
| 远端 readback | `ssh root@192.168.1.11 -p 37878` 同一命令链能显示 canonical latest 文件、latest endpoint、map artifact 状态。 | `robot_runtime_material` |
| PC 消费边界 | PC API/按钮契约能显示 map proof latest/path/fail-closed 边界；若未浏览器验收，必须写明不是 `user_acceptance_material`。 | `software_guard` |
| HIL/elevator 边界 | 无现场安全/图片材料时，只能记录 blocker 和 CEO 决策点。 | `blocked_with_root_cause` |

## OKR 最低优先级核对

当前 `OKR.md` 4.1 中最低完成度是 O10：0%。本 sprint 直接针对 O10，且选择其第一个 P0 KR：`KR-O10-Path-Contract-Lock`。O8 约 48% 也偏低，但本轮不把流程治理作为主任务；O8 只随 Epic 执行和证据边界小幅受益。
