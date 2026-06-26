# Tech Done

sprint_type: micro

## 实际改动

- 将 PC Robot Control summary 的 `safe_command_boundary.hil_checklist` 从旧四项预检收敛为单项 `operator_safety_confirmed`，文案为“现场安全确认（人在旁边、周围安全、停止手段就绪）”。
- 更新共享 TypeScript 契约、App fixture 和 catalog 合同测试，明确旧 `operator_ready/clearance_confirmed/low_speed_only/not_autonomy_mode` 不再作为发车前 checklist 外露。
- 更新 `docs/product/pc_tools_workstation.md`，记录普通 manual/键盘 pulse 继续只要求 `confirm_hil_checklist=true`，高级 operator report 的细项仍只作为证据提交。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts -t "Robot Control summary"`，10 个相关用例通过。
- 通过：`npm test`，2 个测试文件、214 个用例通过。
- 通过：`npm run build`，TypeScript app/server 与 Vite production build 通过；Vite 仍提示单 chunk 超过 500 kB 的既有 warning。
- 通过：`npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 `npm run api` 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node 监听 `TCP *:7001`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `source_base_url=http://192.168.1.11:8787`、`robot_api_connection.status=readable`、`loaded_count=14`，且 `safe_command_boundary.hil_checklist` 仅包含 `operator_safety_confirmed`；`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 保持 fail-closed。

## 剩余风险

- 本轮只收敛 PC 发车前预检外露合同，不做真实 HIL、真实 wheel raw L/R 非零、完整 Nav2 路线执行或 delivery success 证明。
- 高级 operator report 表单仍保留更细现场材料字段，避免删除现场证据提交能力；这些字段不应被误解为普通发车前门禁。
