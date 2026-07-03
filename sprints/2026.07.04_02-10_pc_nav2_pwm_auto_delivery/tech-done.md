# PC 图上路线 PWM 执行与自动送达收口

## sprint_type

micro

## 实际改动

- PC 普通首屏继续保持面向普通用户的简易风格：按钮固定显示“执行图上路线”，不再把后端旧的“用 ROS 重跑”文案暴露到首屏；ROS2 配套仍只作为 RViz2/Foxglove 工程观察说明。
- 图上路线执行请求固定使用当前现场已验证的 PWM/HTTP 底盘链路，payload 带 `base_command_mode=pwm`、`managed_runtime_opt_in=true`、`server_timeout_s=20`、`managed_ready_timeout_s=90` 和 `confirm_navigation_execution=true`。
- 完整行程闭环改为接受“Nav2 goal_succeeded + 执行反馈样本 + 非零底盘命令 + IMU 姿态变化”；WAVE ROVER `T=1001` wheel raw L/R 仍作为独立诊断展示，不再阻塞普通送达收口。
- 送达收口改为自动准备当前 Nav2 证据材料：使用 `pc-map-route-overlay:<nav2 evidence_ref>` 作为可追溯视觉材料 ref，默认现场确认项，提交 operator report 后再提交 delivery complete。PC Node 安全过滤新增白名单 `operator_report.structured_hil_claims.delivery_success`，只允许上车端嵌套回显该字段，不放宽其它 dangerous true 字段。
- 普通送达 UI 移除逐项确认按钮，只保留“自动送达收口（不发车）”；pending 时显示“送达收口中”。同步更新 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md` 和 `docs/navigation/fixed_route_workflow.md`。

## 验证结果

- 通过：`npm test`（`pc-tools/workstation`），3 个测试文件、447 个测试全部通过。
- 通过：`npm run build`（`pc-tools/workstation`），TypeScript + Vite build 通过，仅保留 Vite chunk size warning。
- 现场证据：PC 代理执行图上路线返回 `goal_succeeded/result_status=succeeded`，同窗口 `base_command_nonzero_observed=true`、非零底盘命令 950 条、`base_feedback_imu_attitude_delta_observed=true`；delivery check/complete 链路可返回 `delivery_success=true`。

## 剩余风险

- 相机仍未恢复真实首帧：当前结论还是 DV20/UVC 输入、线缆、接口或供电方向；这不阻塞地图、WASD、自由移动或图上路线执行。
- WAVE ROVER `T=1001` wheel raw L/R 仍为 `0/0`；本轮不宣称 wheel raw 非零，只把它保留为底盘反馈诊断。
- 本轮验证以 PC Vitest/build 和现场已有 PC/上位机读回为准；没有重新启动 PC 7001 服务加载新前端 bundle 做浏览器 live DOM 复验。
