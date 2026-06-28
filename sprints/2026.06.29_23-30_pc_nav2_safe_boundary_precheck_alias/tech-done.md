# PC Nav2 Safe Boundary Precheck Alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `safe_command_boundary` contract 中新增 `nav2_goal_precheck_plain` 和 `navigation_preflight_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：让两个新字段与 `nav2_goal_minimal_precheck_plain` 同源，保证普通页面或现场脚本只读安全边界时也能看到“执行图上路线只复核现场安全确认和固定白名单”的最小预检口径。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补 summary contract 与前端 fixture 断言，防止安全边界别名再次缺失。
- `docs/product/pc_tools_workstation.md`：同步记录 PC summary 安全边界新增只读预检别名。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies"`，1 个相关测试通过，159 个跳过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite 构建通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提醒。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部通过。
- 通过：重启本机 PC API 到 `0.0.0.0:7001` 后执行只读 `GET /api/robot-control/summary`，live 返回 `safe_command_boundary.nav2_goal_precheck_plain` 与 `safe_command_boundary.navigation_preflight_plain`，均为“执行图上路线只复核现场安全确认和固定白名单；相机、雷达和 operator report 不作为发车前额外预检。”；同次 live 返回 `nav2_goal_blockers=[]`。

## 剩余风险

- 本轮只修 PC 只读 summary/contract 可读性，验证没有触发真实 Nav2 执行，也没有发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；真实车体路线重跑仍需要现场人员勾选安全确认后操作。
