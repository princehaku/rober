# PC 自动驾驶轮速 plain 字段普通化

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/nav2/goal/execution/latest` 顶层 plain 字段保留旧字段名兼容脚本，但字段内容从 `wheel raw L/R` 改为“执行窗口轮速 L/R”；不改变 execute、start、manual、free-roam、delivery、stop 或 `/cmd_vel` 行为。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`readback_summary.nav2.route_execution_*_plain` 和 `goal_execution_wheel_raw_lr_*_plain` 同步使用“轮速 L/R”，避免普通首屏/API 继续暴露 raw 术语。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：更新回归断言，锁定 summary/latest plain 字段的普通文案。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明 plain 字段内容普通化，原始 key/value 仍保留 `wheel raw L/R` 用于高级排障。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "nav2"`：通过，`1 passed | 159 skipped`。
- `npm --prefix pc-tools/workstation test`：通过，`2 passed (2)`、`375 passed (375)`。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 仍提示现有单 chunk 大于 500 kB。
- 重启本机 `0.0.0.0:7001` workstation API 后，只读 `GET /api/robot-control/nav2/goal/execution/latest`：`route_execution_readiness_plain`、`goal_execution_wheel_raw_lr_status_plain`、`goal_execution_wheel_raw_lr_next_action_plain` 均显示“轮速 L/R”，`plain_has_raw=false`，`next_execution_base_command_mode=ros`。
- 只读 `GET /api/robot-control/summary`：Nav2 plain 字段同样 `plain_has_raw=false`；camera `source_diagnosis_status=uvc_no_frame_not_exclusive`；free-roam motion 提示“可先自由移动；当前有停止请求，开始自由移动会先清除停止请求”。

## 剩余风险

- 本轮只修普通文案和只读字段合同，不执行 Nav2 路线，不发布 `/cmd_vel`，不证明小车已经移动。
- live 当前事实显示：摄像头不是页面独占，而是 UVC 无首帧；自由移动/键盘/试动不依赖雷达；自动驾驶上次 action 成功但执行窗口轮速 L/R=`0/0` 未非零，下一次应在现场安全确认后用 ROS 模式重跑并复验轮速。
- 真实“修好能动”的最后一步仍需要现场显式安全确认后执行路线或键盘/底盘试动；本轮按安全边界只做只读验证，没有替用户发车。
