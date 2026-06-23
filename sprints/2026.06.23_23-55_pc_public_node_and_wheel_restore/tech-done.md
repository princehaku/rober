# PC public node and wheel restore

sprint_type: micro

## 设计

本轮只处理两个已经明确的普通用户路径摩擦：

- `恢复试动确认` 成功后应继续服务 `wheel raw L/R 非零`，不能因为雷达未运行就把现场带去雷达卡点。轮速目标已经有统一的下一手控件选择逻辑，因此复用 `plainWheelGoalTarget()`，避免再写一套分支。
- PC 工作站默认入口要方便同局域网访问。Node/Express `npm run api` 已默认 `0.0.0.0:7071`，但 Vite `npm run dev` 仍是本机监听；本轮把开发入口也对齐到 `0.0.0.0:7071`，保留 `HOST/PORT` 覆盖和 `dev:public/api:public` 兼容入口。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`恢复试动确认` 成功后的焦点改为 `plainWheelGoalTarget()`，优先回到轮速复验/试动读非零 L/R，不再被雷达启动状态抢焦点。
- `pc-tools/workstation/test/App.test.ts`：补充恢复确认成功后聚焦 `plain-wheel-trial` 的断言，并确认该流程不会调用 radar start、first-jog 或 manual。
- `pc-tools/workstation/package.json`、`pc-tools/workstation/vite.config.ts`：`npm run dev` 默认使用 Vite config，Vite config 默认监听 `0.0.0.0:7071`，仍支持 `HOST/PORT` 覆盖。
- `docs/product/pc_tools_workstation.md`：同步记录 wheel 优先恢复焦点和 PC 工作站默认公开监听口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "restores first-jog material from existing visual refs without sending motion"`：通过，1 个目标用例通过，确认恢复后聚焦 `plain-wheel-trial`，且未调用 radar start、first-jog 或 manual。
- `cd pc-tools/workstation && npm test`：通过，2 个 test files / 147 个 tests 全部通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite production build 和 server TypeScript build 完成。
- `git diff --check`：通过，无空白错误。
- 全量测试会刷新两个历史 DOM smoke artifact 的 `checked_at`；本轮已恢复为原始时间，未把旧证据时间戳变更纳入提交。
- `lsof -nP -iTCP:7071 -sTCP:LISTEN || true`：命令无输出，但 `netstat -anv | rg '[.:]7071|7071'` 显示 `*.7071 LISTEN`，PID 为 `2183`。
- `ps -p 2183 -o pid,ppid,user,stat,command`：确认占用方是 root 进程 `/Applications/Clash Verge.app/Contents/MacOS/verge-mihomo ...`。
- `cd pc-tools/workstation && npm run api`：按预期 fail fast，输出 `pc-tools workstation API failed to listen on 0.0.0.0:7071: address already in use.`，并给出 `lsof/netstat` 与 `PORT=<free-port> npm run api` 兜底提示。

## 剩余风险

- 本轮不触发真实小车运动，不执行 first-jog/manual/keyboard pulse/stop/Nav2/delivery complete 或 `/cmd_vel`。
- 当前本机 `7071` 已被 Clash Verge 的 root `verge-mihomo` 占用；代码已默认绑定 `0.0.0.0:7071`，但真实启动前必须先从 Clash Verge 侧释放该端口，或临时用 `PORT=<free-port>`。
