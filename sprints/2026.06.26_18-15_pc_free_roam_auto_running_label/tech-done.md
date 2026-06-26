# PC 自动扫图运行态低速 WYSIWYG

## sprint_type

micro

## 实际改动

- 自动扫图 start 成功后，地图流程 marker 从 `自动扫图已启动` 改为 `自动扫图低速运行中`。
- 扫图状态行同步写明 `低速运行中，地图和雷达监看中`，与 ready 按钮 `开始自动扫图（低速）` 保持同口径。
- 更新 PC 工作站回归测试，锁定运行态 marker、aria 和状态行都包含低速语义。
- 同步 `docs/product/pc_tools_workstation.md`，明确本轮只改运行态 WYSIWYG 文案，不改变自动扫图状态机、速度、停止兜底或接口。

## 验证结果

- 通过：`npm test -- -t "starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation"`，结果 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 203 skipped (204)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`、`Tests 204 passed (204)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。

## 剩余风险

- 本轮验证边界是 PC 前端和 mock DOM；未执行真实自动扫图低速运动、真实避障、真实自由跑动建图或 HIL。
