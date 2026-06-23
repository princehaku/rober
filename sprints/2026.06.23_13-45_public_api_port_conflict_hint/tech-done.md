# 2026-06-23 13:45 public API 端口冲突提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - Node API CLI 启动前新增监听地址预检，`HOST=0.0.0.0 PORT=7071 npm run api:public` 在端口被占用时直接失败并输出可操作提示。
  - 新增 `listenFailureHint()`，把 `EADDRINUSE` 压成 `address already in use`、占用进程排查命令和临时换端口兜底命令。
  - 保留 `safe_to_control=false`、`delivery_success=false`、不触发任何机器人控制接口；该改动只改善 PC 工作站访问入口。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加端口冲突提示测试，锁定 `0.0.0.0:7071`、`lsof` 和 `PORT=<free-port> npm run api:public` 提示。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 public Node API 启动诊断行为和安全边界。

## 验证结果

- `npm test -- --runInBand test/catalog.test.ts -t "public API port conflict"`：
  - 失败，Vitest 不支持 Jest 风格 `--runInBand` 参数；不是产品代码失败。
- `npm test -- test/catalog.test.ts -t "public API port conflict"`：
  - 通过，`1 passed | 86 skipped`。
- `npm run api:public`：
  - 在 `7071` 被占用时按预期失败，输出 `address already in use`、`lsof/netstat` 排查命令和 `PORT=<free-port> npm run api:public` 兜底命令。
- `npm test`：
  - 通过，`2 files / 138 tests`。
- `npm run lint`：
  - 通过。
- `npm run build`：
  - 通过，Vite 产物生成完成。
- `git diff --check`：
  - 通过。
- 真实本机状态：
  - `0.0.0.0:7071` 当前由 Clash Verge `verge-mihomo` PID 2183 占用；本轮不擅自 kill 进程。
  - 本轮改动应让 `npm run api:public` 在该状态下给出明确冲突提示，而不是误导性启动日志。

## 剩余风险

- 这轮没有执行真实底盘运动、Nav2 goal、delivery complete 或键盘连续手控。
- `wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控` 仍需要真实现场材料和操作确认后继续验证。
