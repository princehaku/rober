# Safety Confirm Action Queue

## sprint_type

micro

## 实际改动

- 在 PC workstation summary 顶层新增 `current_safety_confirm_queue_*` 短包，把安全确认后可手动执行的 `run_nav2_route -> hold_keyboard -> start_free_move` 顺序、start/stop、每项 acceptance endpoints、去重 readback endpoints 和 no-motion 边界集中输出。
- 在普通用户 PC 首页新增 `plain-current-safety-confirm-queue` DOM 节点，直接暴露队列顺序、主动作、最小预检、安全确认、相机/雷达/路线 WYSIWYG 非发车前置，以及 `auto_runs=false`。
- 更新 summary 与 App 单测，固定队列不自动发车、不自动启动 Nav2/manual/keyboard/free-roam/建图/delivery/stop，只作为安全确认后手动执行顺序和读回复验证入口。
- 更新 `docs/product/pc_tools_workstation.md`，同步说明该队列的只读边界和验收用途。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，10 tests passed。
- 通过：`npm test -- test/App.test.ts`，237 tests passed。
- 通过：`npm run build`，TypeScript 与 Vite build 均完成；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001`，新 PID `63821`。
- 通过：只读读取 `/api/robot-control/summary`，现场返回 `current_safety_confirm_queue_status=ready_for_safety_confirm`、`current_safety_confirm_queue_action_ids=[run_nav2_route,hold_keyboard,start_free_move]`、`current_safety_confirm_queue_action_count=3`、`current_safety_confirm_queue_requires_manual_action_per_step=true`、`current_safety_confirm_queue_auto_runs=false`、`current_safety_confirm_queue_sends_motion_when_clicked=false`、`current_safety_confirm_queue_minimal_precheck_safety_only=true`、`current_safety_confirm_queue_camera_preflight_required=false`、`current_safety_confirm_queue_radar_preflight_required=false`。
- 通过：雷达贴图一度过期为 `needs_readback_refresh` 后，只读调用 `/api/robot-control/radar/scan-proof/refresh`，回包 `sends_motion_when_clicked=false`、`starts_radar_lifecycle=false`、`starts_nav2=false`、`starts_map_runtime=false`；再次读取 summary 得到 `current_radar_map_wysiwyg_pack_status=loaded`、`current_goal_blocked_ids=[camera_wysiwyg,mapping_start]`、`current_goal_free_move_allowed_while_mapping_blocked=true`。

## 剩余风险

- 本轮不发送真实运动命令；完整 Nav2、键盘连续手控、自由移动仍需要现场人员勾安全确认后逐项执行并读回复验。
- 建图仍被相机首帧阻塞；自由移动不受该阻塞影响。
