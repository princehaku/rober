# PC Readonly Map Default Robot Address

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/map/list` 与 `GET /api/robot-control/map/preview` 改用 `robotControlReadOnlyQueryBaseUrl()`。
  - 不带 `baseUrl` 的只读地图列表和地图画面请求现在默认读取固定小车 `http://192.168.1.11:8787`，和 summary、Nav2 latest、delivery latest 口径一致。
  - 地图 start/save/reset 等会动作的 POST 仍保持显式 `baseUrl` 与原有 gate，不因默认地址自动启动建图或保存。
- `pc-tools/workstation/test/catalog.test.ts`
  - 扩展默认地址回归测试，断言无 query 的 `map/list` 与 `map/preview` 会拼到 `http://192.168.1.11:8787/api/map/list` 和 `/api/map/preview`。
  - 测试 stub Node `fetch`，不连接真实小车。
- `docs/product/pc_tools_workstation.md`
  - 同步记录只读地图查询默认固定小车地址，以及控制类 POST 不被放宽。

## 验证结果

- 先失败后修复：`npm test -- test/catalog.test.ts -t "defaults Robot Control read-only"` 第一次失败于 map preview fixture 缺少合法 `image_data_url`，后补齐最小 PNG data URL 和地图字段。
- 通过：`npm test -- test/catalog.test.ts -t "defaults Robot Control read-only"`，`1 passed | 95 skipped`。
- 通过：`npm test -- test/catalog.test.ts`，`96 passed`。
- 通过：`npm test`，`214 passed`。
- 通过：`npm run build`。
- 通过：`npm run lint`。
- 通过：`git diff --check`。
- 通过：重启项目自己的 `npm run api` 后，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
- 通过：live `GET http://127.0.0.1:7001/api/robot-control/map/preview` 不带 `baseUrl` 返回 `proxy_status=preview_forwarded`、`source_base_url=http://192.168.1.11:8787`、`map_name=trashbot_map`、`width=241`、`height=119`、`has_image=true`。
- 通过：live `GET http://127.0.0.1:7001/api/robot-control/map/list` 不带 `baseUrl` 返回 `proxy_status=lifecycle_forwarded`、`source_base_url=http://192.168.1.11:8787`、`map_count=32`。

## 剩余风险

- 本轮只修正只读地图 API 默认地址，不证明真实地图质量、自动扫图 HIL、wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或真实 PC 键盘连续手控。
- 未修改 Clash、系统代理或任何系统网络配置。
