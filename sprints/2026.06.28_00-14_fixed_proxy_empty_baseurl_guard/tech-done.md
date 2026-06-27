# Fixed Proxy Empty BaseUrl Guard

sprint_type: micro

## 实际改动

- `robotControlFixedProxyQueryBaseUrl()` 保留 `undefined` query 默认固定小车地址，满足普通 UI 不手填地址；但显式空字符串 `?baseUrl=` 现在返回空值，让下游固定 POST 代理按 `baseUrl_not_provided` fail closed。
- `free-roam/autonomy/start|stop` 在 URL 规范化失败时前置返回 HTTP 400，不再落到 fetch 异常后统一 502。
- 回归测试覆盖：
  - free-roam start 无 query 仍默认 `http://192.168.1.11:8787`；
  - free-roam start 显式 `?baseUrl=` 返回 `baseUrl_not_provided` 且不触发 fetch；
  - Nav2 lifecycle start 显式 `?baseUrl=` 返回 `baseUrl_not_provided` 且不触达 upstream。
- `docs/product/pc_tools_workstation.md` 同步记录：默认地址和显式空值是两种不同语义。

## 验证结果

- `npm test -- test/catalog.test.ts -t "fixed POST proxies" --maxWorkers=1 --no-fileParallelism`：通过。
- `npm test -- test/catalog.test.ts -t "Nav2 lifecycle" --maxWorkers=1 --no-fileParallelism`：通过。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：通过，2 个 test file、320 条测试通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仍提示主 chunk 超过 500 kB，这是既有体积提醒，不影响构建成功。
- `git diff --check`：通过。
- live PC 7001 重启后安全 smoke：`POST http://127.0.0.1:7001/api/robot-control/nav2/start?baseUrl=` 返回 HTTP 400，
  `proxy_status=lifecycle_rejected`、`failure_reason=baseUrl_not_provided`、`remote_http_status=null`。

## 剩余风险

- 本轮发现该问题的过程中，曾用 live PC 7001 对显式空 `baseUrl=` 探测 `/api/robot-control/nav2/start`；旧代码回退到默认小车地址并实际转发了上位机 `/api/nav2/start`，返回 `command_result.ok=true`。该动作按当前上位机合同不发送 NavigateToPose goal 或 `/cmd_vel`，但仍属于未预期的服务 lifecycle 调用；本 sprint 的 guard 正是为防止该类误触发再次发生。
- 真实完整路线执行、wheel raw L/R 非零、delivery success 和建图 ready 仍未由本轮证明。
