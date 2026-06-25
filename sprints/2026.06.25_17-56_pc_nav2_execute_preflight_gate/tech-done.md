# PC Nav2 Execute Preflight Gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`POST /api/robot-control/nav2/goal/execute` 在转发上位机 `/api/nav2/goal/execute` 前，先复用 PC 本机导航预检读取定位、路线和 Nav2 状态；路线/定位缺项时返回 `execution_rejected`，不发送真实 NavigateToPose 请求。
- `pc-tools/workstation/test/catalog.test.ts`：新增回归测试，证明即使直接 POST 执行接口，只要 `path_generated=false` 且 `path_point_count=0`，PC 只读 `/api/localize/proof/latest`、`/api/nav2/proof/latest`、`/api/nav2/status`，不会调用上位机 `/api/nav2/goal/execute`。
- `docs/product/pc_tools_workstation.md`：同步记录执行代理的后端最小路线门禁，强调不重新引入 operator report/HIL 材料作为普通行程预检前置。

## 验证结果

- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test -- catalog.test.ts -t "Nav2 goal execution reuses PC preflight"`：通过，1 passed / 90 skipped。
- `cd pc-tools/workstation && npm test`：通过，160 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，当前路线 proof 为 `path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`；本轮没有调用 execute、manual、keyboard、delivery 或 `/cmd_vel`。

## 剩余风险

- 当前真实上位机路线 proof 仍未生成路径，真实完整 Nav2 行程尚未在本轮执行；本轮只保证 PC 后端执行入口在路线/定位缺项时不会绕过预检转发。
- 真实发车仍需要现场 operator 显式勾选确认，并在雷达运行、定位 TF、路径生成和路径点数都满足后再点击 `执行行程`。
