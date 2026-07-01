# PC 现场验收全量只读复验

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在 `plain-field-acceptance-packet` 顶部新增 `plain-field-acceptance-readback-all`。
  - 按钮文案为“只读复验全部”，可见标题用“复验读回”，避免普通首屏出现工程词。
  - 新增 `refreshFieldAcceptanceAllReadbacks()`，顺序复用既有 no-motion 读回：
    - 完整行程：地图预览、Nav2 latest、底盘轮速、delivery latest、summary。
    - 键盘：底盘轮速、summary。
    - 自由移动：free-roam latest、summary。
    - 建图/WYSIWYG：相机首帧、MJPEG 状态、雷达 scan proof、雷达状态、地图预览、summary。
  - DOM 固定声明不执行 Nav2/manual/keyboard/free-roam/建图、不开 radar lifecycle、不提交 delivery、不 stop。
- `pc-tools/workstation/src/styles.css`
  - 新增全量读回横条样式。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖全量读回按钮文案、端点列表、readback-only 和 no-motion DOM 边界。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `plain-field-acceptance-readback-all` 合同。

## 验证结果

- 已通过：`git diff --check`。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。Vite 仍提示单 bundle 超过 500 kB，这是既有体积警告，不影响本轮验收。
- 已通过：`cd pc-tools/workstation && npm test`，3 files / 421 tests passed。
- 已通过：重启 PC workstation 到 `0.0.0.0:7001`，新 listener PID `63959`。
- 已通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `status=needs_wheel_rerun`、`field_acceptance_packet.next_step_id=run_nav2_route`、`ready_step_ids=[run_nav2_route,hold_keyboard,start_free_move]`、`blocked_step_ids=[start_mapping_when_sensors_ready]`、`next_step_requires_safety_confirm=true`、`field_acceptance_packet.sends_motion_when_clicked=false`。
- 已通过：只读检查 `http://127.0.0.1:7001/assets/index-BsQUxIKo.js`，bundle 包含 `plain-field-acceptance-readback-all`、`只读复验全部`、`复验读回` 和 `data-starts-radar-lifecycle`。

## 剩余风险

- 本轮只新增只读复验入口，不执行真实运动命令。
- 完整目标仍缺现场运动证据：Nav2 路线同窗口轮速 L/R 非零、键盘按住窗口轮速、自由移动 latest 运行读数，以及相机首帧 ready 后建图。
