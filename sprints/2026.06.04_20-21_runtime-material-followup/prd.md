# PRD: Runtime Material Followup

## sprint_type

sprint_type: epic

## 用户价值

普通用户需要的是小车能跨楼层送垃圾、能被 PC/手机安全接管、失败时能留下证据。当前最大问题不是入口不够，而是真实材料不足。本轮只推进能把真实材料链路往前推的一步，不能用 fixture、文案或 dry-run 包装完成度。

## OKR 对齐

- O2: 电梯 assisted delivery 必须有真实/受控图片进入 OpenCV eval 才能涨分。
- O3: 建图/定位/Nav2 必须有 fresh ROS2 runtime topic、map、AMCL 或明确 blocker。
- O7: PC operator workflow 必须能写入并回读同一 evidence ref。
- O1: HIL 前必须证明安全前提；非运动 `T=130 -> T=1001` 只能作为 vendor feedback material。
- O8: 本轮必须修正上一轮 owner 超时问题，形成可审计 evidence chain。

## 验收口径

- 每个 owner 必须输出 owner note、命令证据、失败定位和 not_proven 边界。
- 有真实 runtime material 才能考虑产品 Objective 涨分；blocked material 只推动下一步决策。
- 任何底盘运动都必须有现场安全条件和明确授权；否则 fail closed。
