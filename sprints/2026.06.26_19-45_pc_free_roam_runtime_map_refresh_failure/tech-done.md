# PC 扫图记录中地图刷新失败 WYSIWYG

## sprint_type

micro

## 实际改动

- 地图记录已启动后，如果只读 `map/preview` 刷新失败，扫图卡片状态显示 `待刷新` 并写明 `扫图画面刷新失败：<原因>`。
- 扫图状态、下一步、覆盖提示和地图流程 marker 同步显示同一失败原因，避免 operator 只在地图 caption 里找线索。
- 新增 `runtime_refresh_failed` 地图 marker 状态并接入失败色。
- 新增 PC 工作站回归测试，覆盖地图记录启动成功但扫图画面刷新失败的首屏状态，并验证不触发 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- 同步 `docs/product/pc_free_roam_mapping_design.md`，记录记录中地图刷新失败的用户口径和安全边界。

## 验证结果

- 已通过定向回归：`npm test -- -t "shows free-roam runtime map preview failure after map recording starts"`。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍提示产物 chunk 超过 500 kB，这是既有体积提示，不影响本轮构建。
- `npm test` 通过：`2 passed (2)`、`207 passed (207)`。
- `git diff --check` 通过，无空白错误。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN` 确认 `node` 仍监听 `TCP *:7001 (LISTEN)`，本轮未修改 Clash 或系统代理。

## 剩余风险

- 本轮验证边界是 PC 前端 mock DOM；未执行真实建图 runtime、真实地图 preview 失败、真实键盘手控或 HIL。
