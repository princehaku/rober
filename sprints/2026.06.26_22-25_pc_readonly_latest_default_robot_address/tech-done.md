# PC Readonly Latest Default Robot Address

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 新增 `robotControlReadOnlyQueryBaseUrl()`，让只读 Robot Control 查询在缺省 `baseUrl` 时复用固定小车地址 `http://192.168.1.11:8787`。
  - `GET /api/robot-control/nav2/goal/execution/latest` 和 `GET /api/robot-control/delivery/latest` 改用该 helper；两者仍只读，不发送 Nav2 goal、不提交 delivery complete、不调用 manual/first-jog/stop 或 `/cmd_vel`。
  - 会动作的 POST 路由仍保持原有显式 `baseUrl`、确认项和 fail-closed gate。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增只读 latest 默认地址回归：缺省 query 时后端会请求 `http://192.168.1.11:8787/api/nav2/goal/execution/latest` 和 `http://192.168.1.11:8787/api/delivery/latest`。
  - 测试使用本地 HTTP 调 workstation，并 stub Node `fetch`，不连接真实小车。
- `docs/product/pc_tools_workstation.md`
  - 同步记录只读 latest 默认小车地址边界，以及控制类 POST 不被放宽。

## 验证结果

- 失败后重跑通过：`npm test -- --runInBand test/catalog.test.ts -t "defaults Robot Control|public API port"` 失败，原因是 Vitest 不支持 Jest 的 `--runInBand` 参数；去掉该参数后通过。
- 通过：`npm test -- test/catalog.test.ts -t "defaults Robot Control|public API port"`，`3 passed | 93 skipped`。
- 通过：`npm test -- test/catalog.test.ts`，`96 passed`。
- 通过：`npm test`，`214 passed`。
- 通过：`npm run build`。
- 通过：`npm run lint`。
- 通过：`git diff --check`。
- 通过：重启项目自己的 `npm run api` 后，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
- 通过：live `GET http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest` 不带 `baseUrl` 返回 `proxy_status=latest_loaded`、`source_base_url=http://192.168.1.11:8787`、`nav2_status=goal_succeeded`、`feedback=8`。
- 通过：live `GET http://127.0.0.1:7001/api/robot-control/delivery/latest` 不带 `baseUrl` 返回 `proxy_status=latest_loaded`、`source_base_url=http://192.168.1.11:8787`、`delivery_success=false`，缺口仍为 `confirm_delivery_completion/operator_report_ready_for_review/operator_observed_motion/operator_observed_stop/structured_hil_claims.delivery_success`。

## 剩余风险

- 本轮只修正只读 latest 默认地址，不证明 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或真实 PC 键盘连续手控。
- 未修改 Clash、系统代理或任何系统网络配置。
