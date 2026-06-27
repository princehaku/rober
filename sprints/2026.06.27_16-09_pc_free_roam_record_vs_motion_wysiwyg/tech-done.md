# 2026-06-27 16:09 PC free-roam record vs motion WYSIWYG

## sprint_type

micro

## 设计

本轮推进“勾了安全确认即可”和“自由自助移动”的 PC 易用性。live DOM 显示：勾选安全确认后，
`plain-free-roam-start` 文案是 `开始记录并低速移动`，但该按钮实际只调用地图记录，不会让小车移动；
真正低速自移动入口是 `开始自由移动（低速）`。同屏 readiness gate 还会继续展示旧 summary 的
`现场安全确认未满足`，和本地 checkbox 已勾选冲突。

设计口径：
- 地图记录按钮必须明确 `不发车`。
- 自由移动按钮才表达低速自移动。
- 本地 safety checkbox 已勾选后，free-roam readiness gate 的现场安全确认展示同步为已满足。
- 本轮只做 UI WYSIWYG 修正和只读 DOM 验证，不点击发车/执行/键盘启用按钮。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plainFreeRoamMappingStartLabel` 从 `开始记录并低速移动` 改为 `开始记录（不发车）`。
  - `plainFreeRoamNextActionLabel` 对应改为 `下一步：开始记录（不发车）`。
  - 传感器未 ready 的 hint 改为“地图记录不发车；低速自移动用开始自由移动（低速）”。
  - `operator_confirmed` gate 在本地安全确认已勾选时显示 `已满足` 和 `已勾选现场安全确认`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新自由移动/建图降级、雷达 stale、单一安全确认相关回归。
  - 新增断言：安全确认后 readiness gate 不再显示旧 blocked 口径。
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录地图记录按钮与自由移动按钮的行为边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "free-roam|safety confirmation|stale radar proof|source_selected_not_probed|one plain safety"`
  - 结果：1 个 test file passed，22 tests passed，147 skipped。
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - 结果：2 个 test files passed，297 tests passed。
- 已通过：`npm --prefix pc-tools/workstation run build`
  - 结果：Vite build 成功，产物 `dist/assets/index-hz4yXMKF.js`；仍有 500 kB chunk size warning，非本轮新增失败。
- 已通过：`npm --prefix pc-tools/workstation run lint`
- 已通过：`git diff --check`
- 已重启 PC Node：`node` PID `97349` 监听 `*:7001`，HTML 引用新 bundle `index-hz4yXMKF.js`。
- live DOM 只读验证 `http://127.0.0.1:7001`：
  - 仅勾选本地安全确认后，`plain-free-roam-start=开始记录（不发车）`，可点。
  - `plain-free-roam-auto-start=开始自由移动（低速）`，可点。
  - `plain-trip-execute=执行图上路线`，可点。
  - `keyboard-control-arm=启用键盘（按键才动）`，可点。
  - readiness gate 显示 `启动条件：现场安全确认 已满足；已勾选现场安全确认`。
  - 未触发 manual、`/cmd_vel`、Nav2 execute、free-roam start、delivery complete 或 radar start。

## 剩余风险

- 本轮没有执行真实自由移动、键盘连续手控或 Nav2 路线，只证明 UI 文案和本地安全确认后的可操作状态。
- 完整 Nav2 路线执行、wheel raw L/R 非零、delivery success、真实键盘连续运动仍需现场执行材料闭环。
- 摄像头仍无首帧；建图验收仍缺 `camera_first_frame`。
