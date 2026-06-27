# 2026.06.28 04:07 普通首屏自动驾驶术语收敛

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增普通首屏专用 `plainNav2UserFacingText()`，把自动驾驶当前事实里的 `Nav2 planner/controller` 翻成 `规划服务/控制服务`，把 `wheel raw L/R` 翻成 `执行窗口轮速 L/R`，把 `路线 action 成功` 翻成 `路线结果成功`。
  - 仅作用在普通用户可见的 current facts / 下一步文案；高级诊断、合同字段和机器 token 不改。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 Nav2 旧成功但轮速未闭环场景的普通首屏断言，锁定 current facts 不再出现 `Nav2 planner`、`Nav2 controller` 或 `wheel raw L/R`。
  - 同步 stopped stack fixture 的普通 label 为 `自动驾驶服务未启动`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录普通首屏自动驾驶术语翻译规则，并把旧 `Nav2 服务未启动` 说明更新为 `自动驾驶服务未启动`。

## 验证结果

- 首轮全量测试发现 2 处旧断言仍期待 `wheel raw L/R`；已同步为普通首屏 `执行窗口轮速 L/R` 口径后复验通过。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Nav2 success with nonzero base commands|SPEED 重跑|IMU motion signal|no-motion Nav2 start action"`，3 passed / 185 skipped。
- 通过：`cd pc-tools/workstation && npm test`，335 passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
  - Vite 仍提示生产包 chunk 大于 500 kB，这是既有前端体积提示，不影响本轮构建通过。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后，live 只读
  `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回
  `nav2_goal_label=自动驾驶服务未启动`、`nav2_stack_running=false`、`nav2_stack_lifecycle_state=stopped`、
  `free_roam_motion_start_ready=true`、`free_roam_mapping_ready=false`、
  `free_roam_mapping_missing_reasons=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`、
  `camera=source_first_frame_failed`、`lidar=latest_proof_present_but_lifecycle_not_running`、`robot_control_executed=false`。

## 剩余风险

- 本轮只修正普通 PC 文案，不启动自动驾驶服务、不执行 Nav2 路线、不证明 wheel L/R 非零、delivery success 或摄像头/雷达恢复。
- 完整目标仍需现场安全确认后继续验证真实 Nav2 route、PC 键盘连续控制、自由移动与建图闭环。
