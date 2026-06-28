# PC 建图 ready 场景扫图记录按钮收口

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainFreeRoamRecordStartButtonText`，在相机和雷达 ready、进入可验收建图流程时，地图记录入口统一显示 `开始扫图记录（不发车）`。
  - `plain-free-roam-start`、自动扫图补证按钮和 `plain-free-roam-next-action` 共用同一 ready 文案。
  - 键盘与扫图画面刷新按钮在 ready 场景下也显示 `先开始扫图记录`，避免同一流程混用“记录”和“扫图记录”。
  - 相机或雷达未 ready 时仍显示普通 `开始记录（不发车）`，自由移动入口不被传感器门禁锁死。
- `pc-tools/workstation/test/App.test.ts`
  - 更新相机/雷达 ready 的建图记录测试断言，锁定 `开始扫图记录（不发车）`。
  - 保留未 ready 场景仍可低速自由移动的既有断言。
- `pc-tools/README.md`
  - 同步 ready 场景下建图入口文案。
- `docs/product/pc_tools_workstation.md`
  - 同步产品文档，明确该变化不自动启动 free-roam，不发送 manual、Nav2、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "free-roam|map recording|mapping-ready|free movement|safety confirmation"`
  - 通过：`25 passed | 178 skipped (203)`。
- `cd pc-tools/workstation && npm test`
  - 通过：`2 passed (2)`，`351 passed (351)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过：`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功；保留既有 Vite chunk size warning。
- `git diff --check`
  - 通过：无 trailing whitespace 或 patch 格式问题。

## 剩余风险

- 本轮只改 PC 普通首屏文案和软件测试，未在真实上位机启动地图记录或自动扫图。
- 真实建图验收仍需要现场确认相机真实画面、雷达 fresh、地图记录启动、低速移动后地图画面刷新与保存结果。
- 旧的 `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/*.json` 脏文件不是本轮改动，提交时保持不纳入。
