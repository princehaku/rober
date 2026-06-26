# PC 送达材料偏暗画面 gate

## sprint_type

micro

## 实际改动

- 普通首屏实时画面已经绘帧但判定 `画面偏暗` 时，送达材料按钮改为 `先检查画面光线` 并禁用。
- 送达材料状态同步提示“当前画面偏暗，先检查镜头或光线后再准备送达材料”，避免把明显不可用的当前画面当送达材料。
- 更新 PC 工作站测试，锁定偏暗画面时不会触发 `camera/first-frame/probe` 预填送达材料。
- 同步 `docs/product/pc_tools_workstation.md`，明确该 gate 只拦截送达材料预填，不执行 Nav2、不发送手控/stop/delivery，不修改 Clash/系统代理，PC 入口保持 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "marks near-black preview as 画面偏暗 instead of optimistic 已打开"`，结果 `Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 201 skipped (202)`。
- 通过：`npm run lint`。
- 通过：`npm run build`。Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`，`Tests 202 passed (202)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端 gate 和 mock/单测验证，未做真实摄像头暗光现场复测或真实送达材料保存验证。
