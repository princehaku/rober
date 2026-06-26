# PC 自动扫图步骤条同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“扫地式建图”步骤条识别自动扫图 start/stop/failure。
  - 自动扫图运行时，步骤条显示 `自动扫图中`、`可停止`，避免继续按人工键盘流程提示 operator。
  - 自动扫图 stop 成功后，步骤条提示已停止并引导刷新画面后保存。
  - 自动扫图 stop 失败时，`下一步` 指向红色停止，保存按钮保持禁用，避免未证明停止时保存地图。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展自动扫图正常、启动失败和停止失败用例，锁定步骤条、下一步、保存 gate 和不触发运动/导航端点。
- `docs/product/pc_tools_workstation.md`
  - 记录自动扫图步骤条 WYSIWYG 口径和 stop 失败保存禁用边界。

## 验证结果

- `npm test -- -t "free-roam autonomy"`：通过，2 个测试文件，8 个用例通过，194 个用例按过滤条件跳过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍输出既有 chunk size warning，未新增构建错误。
- `npm test`：通过，2 个测试文件，202 个用例全部通过。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 仍监听 `*:7001`。
- 完整 `npm test` 会刷新两个旧 smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免提交无关测试副作用。

## 剩余风险

- 当前为 PC 前端 mock 验证，没有触发真实自动扫图、真实地图保存、manual、keyboard pulse、Nav2、delivery complete、stop 或 `/cmd_vel`。
