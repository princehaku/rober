# PRD: Runtime Material Epic

## 用户价值

普通用户需要的是把垃圾交给小车后，小车能在真实上位机、真实传感器和可解释状态下完成送达准备，
异常时能安全停下并告诉用户原因。本轮不追求新增漂亮入口，而是把已有入口跑到真实材料或明确阻塞。

## 北极星对齐

- O2：跨楼层 assisted delivery 必须从 JSON adapter 走向真实/受控电梯图片和状态链证据。
- O3：建图、定位、Nav2 必须从 API 合同走向上位机 runtime 和 artifact。
- O7：PC operator 必须能连真实 8787，上报同一 evidence ref 和失败原因。
- O1：底盘硬件必须 stop-first，任何运动前先证明安全准入和停止路径。
- O8：本轮必须完整 Epic 留档，不能再用 Micro/software guard 包装涨分。

## 本轮结果定义

本轮接受三类结果：

1. `robot_runtime_material`：从上位机或本地真实 runtime 采集到 `/scan`、map/localize/Nav2、8787 endpoint 或 operator report artifact。
2. `field_hil_material`：在安全前提成立时，采集 stop-first HIL 或非运动 vendor feedback 同场证据。
3. `blocked_with_root_cause`：真实入口不可用或安全条件不满足时，保留命令、日志、配置缺口和下一步解法。

本轮不接受：

- 只新增 UI 文案、runbook、fixture、collector 或 mock，然后声称产品能力涨分。
- 把 O5/O6 production blocker 继续作为本轮主线。
- 在没有安全准入时执行底盘运动。

## 验收口径

- 每个 owner 必须写 `owner_notes/<role>.md`，包含实际动作、命令输出摘要、证据类型、not_proven 边界。
- `tech-done.md` 聚合 owner 结果，区分 `software_guard`、`robot_runtime_material`、`field_hil_material`、`blocked_with_root_cause`。
- `side2side_check.md` 对照 PRD 验收项。
- `final.md` 判断 OKR 是否涨分；没有真实材料时明确不涨分。
