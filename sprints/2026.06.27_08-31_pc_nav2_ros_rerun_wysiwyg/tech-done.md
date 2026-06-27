# PC Nav2 ROS 复跑提示 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将 PC summary 聚合的 `next_execution_base_command_mode` 纳入普通行程证据值。
  - 新增 `nav2NextExecutionRerunText()`：当上次执行模式与下一次执行模式不一致，且行程成功但 wheel raw L/R 未证明时，普通行程进度和证据摘要明确提示“下次将用 ros 重新执行这条图上路线”。
  - 保持执行入口、安全 checkbox、stop 兜底、送达 gate 不变；该改动只影响显示文案。
- `pc-tools/workstation/test/App.test.ts`
  - 加强 IMU-only / wheel L/R=0 场景断言，覆盖行程进度和行程证据里的 ROS 复跑提示。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 PC 普通首屏对旧 `pwm` 结果和下一次 `ros` 复跑的显示口径。

## 验证结果

- 已通过：
  - `cd pc-tools/workstation && npm test -- -t "keeps IMU-only route arrival visible while calling out zero wheel readback"`
- 已发现并修正：
  - 首次使用 `npm test -- --runInBand ...` 失败，原因是本项目 Vitest 不支持 `--runInBand` 参数；改用 `npm test -- -t ...` 后目标用例通过。

## 剩余风险

- 本轮没有执行真实 Nav2 发车、底盘运动或送达确认；仍需现场 operator 勾选安全确认后，手动触发下一次 ROS 模式图上路线执行。
- 当前 live 读数仍显示 camera `source_first_frame_failed`、LiDAR `missing`，以及上次 Nav2 execution wheel raw L/R 为 `0/0`；本改动只让 PC 端把复跑下一步说清楚，不证明完整自动驾驶已完成。
