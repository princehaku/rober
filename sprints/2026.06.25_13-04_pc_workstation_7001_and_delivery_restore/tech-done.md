# PC workstation 7001 and delivery restore

sprint_type: micro

## 设计

- PC 侧入口不能再抢用户本机 Clash 的 `7071`，本轮把 workstation 自己的默认公开端口改为 `7001`，仍保留 `HOST/PORT` 覆盖。
- 普通首屏继续保持面向普通用户的简易路径：当 summary 里 operator report 丢失或是旧报告，但 delivery latest 仍有画面草稿 ref 时，允许恢复 first-jog 前置确认；恢复只写回 operator report 材料，不发送任何运动命令。
- 轮速仍 fail-closed：当前只读 `wheel raw L/R=0/0` 时，即使恢复画面材料成功，也先让用户检查轮速卡点，不直接进入试动。

## 实际改动

- `pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/vite.config.ts`、`pc-tools/workstation/package.json`：默认公开监听从 `0.0.0.0:7071` 改为 `0.0.0.0:7001`，`api:public` / `dev:public` 同步改为 `PORT=7001`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 delivery latest 草稿画面 ref 恢复路径，避免 operator latest 缺失时让现场重复记录画面；恢复不伪造 wheel/LiDAR/delivery success。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：覆盖 delivery latest 草稿恢复、`L/R=0/0` 禁止直接试动、默认监听地址和端口占用提示。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步 PC 工作站 `7001` 入口与只读/不发车边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "delivery latest draft refs"`：通过，1 个目标用例通过，确认 delivery latest 草稿 ref 可恢复 first-jog 前置确认，且 `L/R=0/0` 时仍禁用直接试动。
- `cd pc-tools/workstation && npm test`：通过，2 个 test files / 151 个 tests 全部通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite production build 与 server TypeScript build 完成。
- `cd pc-tools/workstation && npm run api`：通过，输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- `curl -I http://127.0.0.1:7001/`：通过，返回 HTTP 200。
- `curl http://127.0.0.1:7001/api/robot-control/summary`：通过，返回 workstation summary JSON；未提供 baseUrl 时按预期 `not_configured` fail-closed。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：通过，Node 监听 `*:7001`。
- `git diff --check`：通过，无空白错误。
- 全量测试刷新了两个历史 DOM smoke artifact 的 `checked_at`；本轮已恢复为原始时间，未把旧证据时间戳变更纳入提交。

## 剩余风险

- 本轮不触发真实小车运动，不执行 first-jog/manual/keyboard pulse/stop/Nav2/delivery complete 或 `/cmd_vel`。
- 完整目标仍未闭环：真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和 PC 键盘连续手控还需要现场材料与上位机当前状态继续推进。
