# Field Acceptance Parallel Action Packet

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增并行动作包 alias：`field_acceptance_parallel_status_plain`、`field_acceptance_parallel_no_motion_action_*`、`field_acceptance_parallel_safety_action_*`、`field_acceptance_parallel_hardware_action_*`、`field_acceptance_parallel_mapping_missing_evidence`、`field_acceptance_parallel_free_move_allowed_while_mapping_blocked` 和 `field_acceptance_parallel_sends_motion_when_clicked=false`。
- 普通首屏 `plain-field-acceptance-packet` DOM 同步暴露 `data-parallel-*`，现场脚本不用同时解析 primary no-motion、safety action、hardware action 和 mapping 字段。
- 更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，明确该包只回答“现在可先做什么只读复验 / 勾安全确认后跑什么 / 硬件处理什么 / 建图还差什么”，不新增按钮，不自动刷新，不发车，不提交送达，不 stop。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts`，结果 `2 passed (2)`、`246 passed (246)`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`，生成 `dist/assets/index-C1CSWybP.js`；Vite 仅保留既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001`，`lsof` 显示 `node ... TCP *:7001 (LISTEN)`。
- 通过：运行实例 summary 读到 `field_acceptance_parallel_status_plain=只读复验：刷新雷达贴图；安全确认后动作：完整行程执行；设备处理：换高速USB后复测；建图缺口：camera_first_frame、lidar_fresh；自由移动：可在安全确认后先做`。
- 通过：运行实例 summary 读到 `field_acceptance_parallel_no_motion_action_id=refresh_radar_map_overlay`，sequence 为 `/api/robot-control/radar/scan-proof/refresh -> /api/robot-control/radar/status -> /api/robot-control/map/preview -> /api/robot-control/summary`。
- 通过：运行实例 summary 读到 `field_acceptance_parallel_safety_action_id=run_nav2_route`，acceptance endpoints 为 `/api/robot-control/map/preview -> /api/robot-control/nav2/goal/execution/latest -> /api/robot-control/base/feedback-samples -> /api/robot-control/delivery/latest -> /api/robot-control/summary`。
- 通过：前端 bundle grep 到 `data-parallel-status-plain`、`data-parallel-no-motion-action-id`、`data-parallel-safety-action-id`、`data-parallel-hardware-action-id`、`data-parallel-mapping-missing-evidence` 和 `data-parallel-free-move-allowed-while-mapping-blocked`。

## 剩余风险

- 本轮仍未获得新的现场安全确认，未发送 Nav2、keyboard、free-roam、mapping、delivery、stop 或 `/cmd_vel`；真实 wheel L/R 非零、delivery success、键盘运动闭环、自由移动运行和建图启动仍需现场安全确认后验证。
- 当前运行实例显示雷达贴图和建图雷达 fresh 也需要 no-motion 复验；相机仍是 USB full-speed / UVC 无首帧，需要现场换高速 USB 口/线或带供电 Hub 后再复验。
