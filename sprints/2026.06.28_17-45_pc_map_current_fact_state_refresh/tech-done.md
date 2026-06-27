# 2026-06-28 17:45 PC 地图状态刷新当前事实同步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的地图行优先消费 `mapRefreshPending`。
  - 地图状态刷新中且旧真实地图仍显示时，事实行明确写出“当前仍显示上次真实地图画面，刷新完成后再按最新状态判断”。
  - 该改动只调整只读展示，不新增地图 proof/preview、manual、keyboard、Nav2、delivery、free-roam、stop 或 `/cmd_vel` 请求。
- `pc-tools/workstation/test/App.test.ts`
  - 在地图状态刷新中阻止图上路线执行的测试里，锁定 `当前事实` 同步显示地图状态刷新中。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首屏地图事实行 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "blocks visible-route execution while the map preview is refreshing"`
  - 结果：1 个测试文件通过，1 个目标测试通过，191 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，339 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮未做真实地图/真实小车 HIL；变更限定在 PC 首屏只读展示，不作为真实地图状态或真实运动成功证明。
- 未发送任何真实地图 proof/preview、manual、keyboard、Nav2、delivery、free-roam、base stop 或 `/cmd_vel` 请求；真实地图和真实小车状态仍需现场按安全流程验收。
