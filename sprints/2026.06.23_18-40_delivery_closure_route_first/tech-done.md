# 2026-06-23 18:40 Micro Sprint: delivery 收口先指向本轮行程

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 高级 `目标收口进度` 的 `delivery success` 未完成项在本轮完整行程未完成时，先提示完成本轮行程；雷达未运行时提示 `送达确认前先启动雷达并完成本轮完整行程`。
  - 只调整只读验收提示，不自动启动雷达、不执行 Nav2、不提交 delivery complete、不发送 manual 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展雷达未运行时的回归测试，确认 `delivery success` 收口项保持 `data-ready=false` 并指向雷达/行程前置。
- `docs/product/pc_tools_workstation.md`
  - 同步记录高级 `delivery success` 收口项的路线前置提示。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "blocks plain trip actions on the first screen until radar is running"`：通过，`1 passed | 141 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed`、`142 passed`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 产物生成成功。
- `git diff --check`：通过。
- 附加 7071 访问检查：
  - `cd pc-tools/workstation && npm run api`：代码尝试监听 `0.0.0.0:7071`，但当前本机返回 `EADDRINUSE`。
  - `netstat -anv -p tcp | rg '7071|Proto'`：`*.7071 LISTEN` 属于 PID `2183`。
  - `ps -p 2183 -o pid,user,stat,command`：PID `2183` 是 root 用户的 `/Applications/Clash Verge.app/Contents/MacOS/verge-mihomo`。

## 剩余风险

- 当前改动只修正 PC 只读收口提示，不证明 delivery success、完整 Nav2 路线执行、wheel raw L/R 非零或 PC 键盘连续手控。
- 真实上位机仍显示雷达 lifecycle 未运行、当前 wheel L/R 为 `0/0`、Nav2 latest 未证明、delivery 未成功；真实动作仍需现场 operator 明确确认。
- PC 工作站 Node API 默认绑定已经是 `0.0.0.0:7071`，但当前开发机 7071 被 Clash Verge 占用；必须先关闭/改端口 Clash，或临时使用 `PORT=<free-port> npm run api`。
