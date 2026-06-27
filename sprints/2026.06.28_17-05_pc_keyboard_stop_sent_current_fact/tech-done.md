# 2026-06-28 17:05 PC 键盘停止事实行同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的键盘行优先显示 `blocked_keyboard_pulse_failed`、`blocked_keyboard_stop_failed` 和未达连续验证的 `stop_sent` 状态。
  - 一次短按松开后，事实行不再退回“已启用，按住才动”，而是显示“已停止、上次方向、最佳连续 1/2 次、未达到连续验证”。
  - 该改动不改变键盘发送循环、速度/时长上限、安全确认、stop 兜底或任何运动代理。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 PC 键盘连续手控测试，覆盖短按松开后 `当前事实` 的 stop_sent 未验证文案。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首屏键盘事实行 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy"`
  - 结果：1 个测试文件通过，1 个目标测试通过，191 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，339 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实小车 HIL；变更限定在 PC 首屏只读展示，不作为真实运动成功证明。
- 未发送任何真实 free-roam、manual、keyboard、Nav2、delivery、base stop 或 `/cmd_vel` 请求；真实小车运动状态仍需现场按安全流程验收。
