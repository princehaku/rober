# 2026.06.04 17-18 Runtime Material Epic Pre Start

## sprint_type

sprint_type: epic

## 背景

本轮接续 `2026.06.04_16-05_okr-six-sprint-strategy-rewrite` 的 OKR 打回口径和
`2026.06.04_16-17_o2-elevator-opencv-state-integration` 的 O2 software guard。
16-17 已把 OpenCV baseline artifact 接入电梯 assisted delivery 状态链，但证据边界仍是
`software_guard`，没有真实图片、ROS2 runtime、受控电梯、HIL 或地图材料，因此不涨分。

CEO 本轮要求“开始新一轮迭代，用 team 继续完成 OKR，重心放在功能往前走，测试只当护栏用”，
并提供上位机入口 `ssh root@192.168.1.11 -p 37878`。因此本轮必须从 software guard
切到 `robot_runtime_material` / `field_hil_material` / 明确 blocker 证据。

## 当前 OKR 入口

- O8：约 35%，最低 Objective；本轮作为治理和证据口径约束，不作为产品涨分目标。
- O2：约 72%，产品主线最低；需要真实/受控电梯图片 manifest、OpenCV eval、状态机 runtime 证据。
- O3：约 73%；需要上位机 ROS2 runtime 的 `/scan`、SLAM/map/localize/Nav2 证据。
- O7：约 88%；需要真实 8787/browser/operator workflow，而不是 mock UI。
- O1：约 95%；需要 stop-first HIL、`T=1001` 同场边界和 ROS feedback topic，安全不满足时不得下发运动。

## 最近 blocker 扫描

- O5/O6 已连续出现 PC base URL、cloud base URL、remote bearer token 等生产配置 blocker，本轮不继续消费。
- 12-13 Epic 的共同 blocker 是没有真实 runtime/HIL/现场图片/地图/控车材料，本轮直接围绕上位机和现场材料推进。
- 若上位机 SSH 不通、8787 不通、ROS2 runtime 不存在、真实图片不存在或安全条件不满足，必须写成明确 blocker，不得改写为完成度。

## Owner

- Robot Software Engineer：O3/O7 上位机 8787/ROS2 radar/map/localize runtime 主责。
- User Touchpoint Full-Stack Engineer：O7 PC/browser/operator workflow 与 8787 live evidence 主责。
- Robot Algorithm Engineer：O2 真实/受控电梯图片 manifest 与 OpenCV eval 主责。
- Hardware Infra Engineer：O1 stop-first HIL 准入、vendor 边界、非运动 feedback/安全证据主责。
- Product Manager / OKR Owner：收口证据类型、OKR 是否涨分、side2side/final 和 OKR 更新。

## 执行原则

- 允许使用 mock/stub 继续开发，但本轮只有真实 runtime/HIL/现场/图片材料才能推动当前 OKR 百分比。
- 不满足安全前提时，Hardware 不得执行底盘运动命令，只能输出 fail-closed 准入材料和下一步 blocker。
- 所有 owner 先产出自己范围的 owner note 和 evidence；Product 最后统一收口。
