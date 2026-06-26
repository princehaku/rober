# PC 自动扫图停止后待刷新画面标注

## sprint_type

micro

## 实际改动

- 自动扫图 stop 成功但停止后的地图画面尚未刷新时，地图流程 marker 从 `自动扫图已停止，待刷新` 改为 `自动扫图已停止，待刷新画面`。
- 该文案与 `下一步：刷新扫图画面`、保存按钮 `先刷新画面` 对齐，避免用户误以为已经可以直接保存地图。
- 更新 PC 工作站回归测试，锁定 stop 成功后的待刷新 marker 文案和既有保存 gate。
- 同步 `docs/product/pc_tools_workstation.md`，明确本轮只改 WYSIWYG 文案，不改变 stop、refresh 或 save 流程。

## 验证结果

- 通过：`npm test -- -t "starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation"`，结果 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 203 skipped (204)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`、`Tests 204 passed (204)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。

## 剩余风险

- 本轮验证边界是 PC 前端和 mock DOM；未执行真实自动扫图停止、真实地图刷新、真实保存或 HIL。
