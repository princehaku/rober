# 键盘连续手控已验证态

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `键盘手控` 面板在同一次按住方向键达到 2/2 个成功 manual pulse 后，状态从“可手控/已启用”明确切到 `已验证`，live 文案显示 `键盘手控已验证，已连续 2/2 次`。按住期间仍显示 `手控中`，不改变 manual gate、pulse 间隔、stop 行为或任何控制接口。
- `pc-tools/workstation/src/server/index.ts`：CLI 启动时显式保留 HTTP server 引用，并对 listen error 写 stderr 与非零退出码，避免 `api:public` 端口被占用时误以为已经可访问。
- `pc-tools/workstation/test/App.test.ts`：扩展键盘连续手控验收用例，覆盖第二次连续 pulse 后松开时普通首屏直接显示 `已验证`，同时继续确认目标进度为 `键盘手控已验证`。
- `docs/product/pc_tools_workstation.md`：同步普通首屏键盘验证完成态说明，明确该文案变化不自动发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、136 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，完成 app/server TypeScript 与 Vite production build。
- 通过：`git diff --check`。
- 已恢复 `npm test` 改写的历史 smoke JSON `checked_at` 副作用，提交范围不包含旧 artifacts 噪声。
- `cd pc-tools/workstation && npm run api:public` 未能占用 `0.0.0.0:7071`：当前 `netstat -anv` 显示 `*.7071 LISTEN` 的 PID 为 `2183`，`curl http://127.0.0.1:7071/api/health` 返回 `HTTP/1.1 400 Bad Request` 且不是 PC API health 响应。按用户权限边界，本轮未杀 PID 2183。

## 剩余风险

- 本轮只改善 PC 普通首屏对“键盘连续手控已验证”的可见性，不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行或真实 delivery success。
- `api:public` 代码已固定 `HOST=0.0.0.0 PORT=7071`，但当前机器 7071 被 PID 2183 占用；释放该端口后需要重新运行 `npm run api:public` 才能让局域网访问 PC API。
- 真机运动、Nav2 路线执行、送达确认和键盘手控仍需要现场 operator 明确确认后才能触发；本轮验证默认不发送真实运动命令。
