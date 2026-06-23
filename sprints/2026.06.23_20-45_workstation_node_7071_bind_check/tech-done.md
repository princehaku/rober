# 2026-06-23 20:45 Micro Sprint: workstation Node 7071 绑定核对

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/README.md`
  - 补充 `npm run api` 默认绑定 `0.0.0.0:7071` 时的端口占用排查说明。
  - 记录本机 2026-06-23 实测 `7071` 被 Clash Verge 的 root `verge-mihomo` 占用时，Node 代码无需改端口，但必须先释放该端口才能启动。

## 验证结果

- 只读代码核对：`pc-tools/workstation/src/server/index.ts` 当前 `DEFAULT_PUBLIC_HOST = "0.0.0.0"`、`DEFAULT_PUBLIC_PORT = 7071`，`npm run api` 会使用该默认地址。
- `lsof -nP -iTCP:7071 -sTCP:LISTEN || true`：未返回进程名。
- `netstat -anv | rg '[.:]7071 .*LISTEN|7071' || true`：显示 `*.7071 LISTEN`，PID `2183`。
- `ps -p 2183 -o pid,ppid,user,command`：PID `2183` 是 root 启动的 Clash Verge `verge-mihomo`。
- `cd pc-tools/workstation && npm run api`：启动失败，错误为 `pc-tools workstation API failed to listen on 0.0.0.0:7071: address already in use.`。
- `kill 2183 || true`：失败，`operation not permitted`，当前用户无法停止该 root 进程。

## 剩余风险

- 代码默认绑定目标已经是 `0.0.0.0:7071`，但本机当前不能实际启动在 7071，因为该端口被 Clash Verge 占用且当前用户无权限停止。
- 需要在 Clash Verge 配置或系统 helper 侧释放 7071 后，再运行 `cd pc-tools/workstation && npm run api`。
