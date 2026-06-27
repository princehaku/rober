# PC 共享画面 Status Pending 未证明口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 共享 MJPEG status 正在读取时，普通首屏 `共享画面` 行改为显示“正在读取 PC 共享流状态；返回前不证明本页已出图”。
  - 本改动只收紧摄像头共享预览的所见即所得文案，不新增 camera reader，不新增 WebRTC offer，也不触发 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 status pending 用例，锁定 status 未返回前不能显示本页已出图，并确认不发送底盘或自由移动命令。
- `docs/product/pc_tools_workstation.md`
  - 同步记录共享 MJPEG status pending 的未证明口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "keeps shared camera status pending unproven until status polling returns"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 200 skipped (201)`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 349 passed (349)`
- 通过：`npm run lint`
  - `eslint .`
- 通过：`npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍提示单 chunk 超过 500 kB，这是既有体积提示，不影响本轮构建通过。
- 通过：`git diff --check`

## 剩余风险

- 本轮没有连接真实小车，也没有发送真实 camera offer、manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`；仅验证 PC 前端共享 MJPEG status pending 的所见即所得呈现。
- 工作区已有两个旧 artifact JSON 文件处于 modified，本轮不修改、不提交。
