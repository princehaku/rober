# PC 自动扫图运动 gate 所见即所得修正

## Sprint 类型

sprint_type: micro

## 实际改动

- 更新 `pc-tools/workstation/src/server/robotControlSummary.ts`：
  - `motion_hil_unlock` gate 现在区分三种状态：
    - `ready`：上车 runtime 已报告 `cmd_vel_publish_enabled=true`。
    - `not_proven`：stop 兜底已 ready，但自动扫图尚未启动，点击 start 后才会打开运动双锁。
    - `blocked`：stop 兜底或自动扫图 runtime 本身还没满足。
  - live 形态 `free_roam_autonomy_start_ready=true`、runtime `artifact_only=true/cmd_vel_publish_enabled=false` 不再显示“完成 HIL 后再解锁”，避免把“尚未启动”误写成“不能启动”。
- 更新 `pc-tools/workstation/test/catalog.test.ts`：
  - 锁定 start-ready 但尚未启动时 `motion_hil_unlock=not_proven`，并显示下一步 `勾选现场安全确认后点击开始自动扫图（低速）`。
- 更新 `docs/product/pc_free_roam_mapping_design.md`：
  - 记录 PC summary 对“尚未启动/不能启动”的区分合同。

## 验证结果

- `cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "free-roam|free roam|autonomy|自动扫图"`：通过，5 tests。
- `cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "free-roam|free roam|自动扫图|扫图"`：通过，19 tests。
- `cd pc-tools/workstation && npm run build`：通过，保留既有 Vite chunk size warning。
- `git diff --check`：通过。
- live PC 7001 已重启；`GET /api/robot-control/summary` 显示：
  - `free_roam_autonomy_start_ready=true`
  - `free_roam_autonomy=locked`
  - `motion_hil_unlock.state=not_proven`
  - `motion_hil_unlock.evidence=当前尚未启动自动扫图，点击开始后由上车端打开运动双锁`
  - `stop_available.state=ready`

## 剩余风险

- 本轮仍没有代替现场人员勾选安全确认，也没有发送 `confirm_operator_safety=true`，因此没有真实发布非零 `/cmd_vel` 或证明 wheel raw L/R 非零。
- 摄像头仍是 `/dev/video1` UVC 节点存在但首帧读取失败；雷达 lifecycle 当前 stopped。它们不阻止自由移动，但仍阻止“可验收建图”。
