# Nav2 Minimal Precheck Contract

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：Nav2 preflight / execute 合同新增最小预检字段，明确相机、雷达、operator report、路线读回、定位读回和 Nav2 status 不作为发车前额外预检。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/server/index.ts`：PC Node preflight / execute 响应统一返回 `minimal_precheck_safety_only=true`、阻断项列表和各类 `*-preflight-required=false` 字段；operator report 对 Nav2 最小预检的 required fields 固定为空。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-trip-minimal-precheck` 增加机器可读 DOM 合同，现场脚本可直接确认“勾安全确认即可，其他读回只做显示/复验”。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：锁定后端响应字段和普通首屏 DOM 字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 PC 端最小预检口径。

## 验证结果

- 通过：`npm test -- test/App.test.ts -t "reuses one plain safety confirmation"`。
- 通过：`npm test -- test/catalog.test.ts -t "Nav2 goal preflight"`，2 tests。
- 通过：`npm test -- test/catalog.test.ts -t "Nav2 goal execution reuses minimal PC preflight"`。
- 通过：`npm test -- --run`，2 files / 392 tests。
- 通过：`npm run lint`，仅保留既有 4 个 Vue multiline warning。
- 通过：`npm run build`，生成 `dist/assets/index-BtUGeltn.js` 与 `dist/assets/index-1TFDR4Wy.css`。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，PID `79790`；只读访问 `/` 返回 `index-BtUGeltn.js` / `index-1TFDR4Wy.css`。
- 通过：只读调用 `POST /api/robot-control/nav2/goal/preflight` 且 `confirm_navigation_preflight=false`，返回 `minimal_precheck_safety_only=true`，相机/雷达/路线读回/定位读回/Nav2 status preflight 均为 `false`，`missing_requirements=["confirm_navigation_preflight_required"]`。

## 剩余风险

- 本轮只补软件合同和本地测试，不发送 Nav2 goal、不执行 keyboard/manual/free-roam/delivery/stop 或 `/cmd_vel`；真实完整路线执行、wheel raw L/R 非零和 delivery success 仍需现场勾选安全确认后验收。
