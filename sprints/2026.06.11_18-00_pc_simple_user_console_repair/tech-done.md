# 2026-06-11 18:00 PC Simple User Console Repair

- sprint_type: micro
- owner: full-stack-software-engineer
- goal: 按 CEO 反馈把 PC workstation 默认首屏恢复成面向普通用户的简易控制台风格。

## 实际改动

- `pc-tools/workstation/src/App.vue`：去掉首屏英文/工程提示，把顶部文案改为普通用户可读的中文说明。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：移除 Robot Control 内部重复标题和说明，默认首屏只保留连接输入和五个普通卡片。
- `pc-tools/workstation/src/styles.css`：收窄页面宽度，去掉 workstation 外壳卡片感，把 `.simple-user-console` 和五个卡片整理成更轻的普通控制台样式。
- `pc-tools/workstation/test/App.test.ts`：保留并扩展首屏 DOM smoke，断言普通首屏禁词不泄漏、内部重复 section head 不再出现。
- `pc-tools/README.md`：同步说明 PC 默认首屏只保留五个普通卡片、短状态和少量普通按钮。
- `docs/product/pc_tools_workstation.md`：同步说明普通用户首屏和默认关闭高级诊断的边界。

## 验证结果

- `cd pc-tools/workstation && npm run test`
  - 通过，`Test Files 2 passed (2)`，`Tests 92 passed (92)`。
- `cd pc-tools/workstation && npm run build`
  - 通过，`vite build` 完成，`dist/` 产物生成成功。
- `git diff --check -- pc-tools/workstation/src/App.vue pc-tools/workstation/src/components/RobotControlConsolePanel.vue pc-tools/workstation/src/styles.css pc-tools/workstation/src/components/WorkstationTabs.vue pc-tools/workstation/test/App.test.ts pc-tools/README.md docs/product/pc_tools_workstation.md sprints/2026.06.11_18-00_pc_simple_user_console_repair/tech-done.md`
  - 通过，无输出。

Smoke artifacts：

- `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`
- `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`

Browser DOM check:

- `http://127.0.0.1:5173/` 打开成功。
- `title=Rober 小车控制台`，`subtitle=连接小车、查看画面和地图，必要时一键停止。`
- 首屏卡片：`小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`
- `.simple-user-console` 内 `检查路径 / 现场材料 / HIL / Nav2 / proof / key values / /cmd_vel / /api/base/manual / task_id / O6 / O7 / Mock / field manifest` 均未出现。
- `advancedClosed=true`，`advancedToolsClosed=true`，`repeatedSectionHeadExists=false`。

## 剩余风险

- 本轮只修复 PC 默认首屏视觉与文案，不改变真实雷达、建图、定位、手动移动或图传能力边界。
- 其他未提交的旧改动仍留在工作树里，尤其是 `docs/hardware/field_hil_*` 和 `onboard/scripts|tests/motion_evidence_material_review.*`，本轮没有碰它们。
