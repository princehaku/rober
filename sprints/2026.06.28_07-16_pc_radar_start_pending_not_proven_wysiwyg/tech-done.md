# PC 雷达启动 Pending 未证明口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `POST /api/robot-control/radar/start` pending 时，雷达卡 hint 改为显示“返回前未证明雷达已运行或已有新点”。
  - 地图雷达 marker aria、扫描范围 aria 和雷达点口径同步说明启动请求返回前不能当作实时雷达已运行，也不能显示新点位。
  - 本改动只收紧 PC 前端 WYSIWYG 呈现，不新增 Nav2、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel` 调用。
- `pc-tools/workstation/test/App.test.ts`
  - 更新雷达 start pending 用例，锁定雷达卡、地图 marker、扫描范围和 freshness label 的未证明口径，并继续确认不发车、不执行 Nav2、不送达确认。
- `docs/product/pc_tools_workstation.md`
  - 同步记录雷达启动 pending 的未证明口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows a map radar-starting marker while the plain radar start request is in flight"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 201 skipped (202)`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 350 passed (350)`
- 通过：`npm run lint`
  - `eslint .`
- 通过：`npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍提示单 chunk 超过 500 kB，这是既有体积提示，不影响本轮构建通过。
- 通过：`git diff --check`

## 剩余风险

- 本轮没有连接真实小车，也没有发送真实 radar start、Nav2、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel`；仅验证 PC 前端 pending 状态呈现和 mock API 行为。
- 工作区已有两个旧 artifact JSON 文件处于 modified，本轮不修改、不提交。
