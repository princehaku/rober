# PC 自动扫图 Ready 按钮低速标注

## sprint_type

micro

## 实际改动

- 自动扫图 gates 全部 ready 时，普通首屏按钮从 `自动扫图` 改为 `开始自动扫图（低速）`，让用户明确这是可能触发低速上车状态机的动作。
- 未 ready 的手动引导按钮、pending `启动中`、地图刷新 gate 和停止兜底不变。
- 更新 PC 工作站回归测试，锁定 ready 态按钮文案，并继续断言启动只调用固定 `free-roam/autonomy/start`，不调用 manual、Nav2、delivery 或 `/cmd_vel`。
- 同步 `docs/product/pc_tools_workstation.md`，明确本轮只改 ready 态文案，不改变自动扫图 gate、接口或停止兜底。

## 验证结果

- 通过：`npm test -- -t "starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation"`，结果 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 203 skipped (204)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`、`Tests 204 passed (204)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。
- 说明：曾运行一次错误 pattern 的定向测试，结果为全 skipped，未作为本轮通过证据。

## 剩余风险

- 本轮验证边界是 PC 前端和 mock DOM；未执行真实自动扫图低速运动、真实避障、真实自由跑动建图或 HIL。
