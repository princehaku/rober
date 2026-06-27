# PC 送达地图刷新 WYSIWYG 文案收口

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏送达最终确认在地图 preview/proof 刷新中时，下一步改为“等待地图画面刷新，避免按旧地图确认送达”。
  - 最终确认提示补充“这不是额外预检，是避免按旧地图或旧行程材料确认送达”，避免普通用户把只读刷新保护误解成新的送达预检。
- `pc-tools/workstation/test/App.test.ts`
  - 更新既有送达确认 pending 场景断言，继续覆盖地图刷新中禁用送达确认、材料保存、latest 和缺口复查，且不新增 delivery complete/operator report/latest/check 请求。
- `pc-tools/README.md`
  - 同步普通首屏送达最终确认的地图刷新 WYSIWYG 口径。
- `docs/product/pc_tools_workstation.md`
  - 同步产品文档，说明该状态不调用 delivery complete、operator report、Nav2、manual、keyboard、free-roam、stop 或 `/cmd_vel`。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "shows delivery confirmation pending on the map while final completion is in flight"`
  - 通过：`1 passed | 202 skipped (203)`。
- `cd pc-tools/workstation && npm test`
  - 通过：`2 passed (2)`，`351 passed (351)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过：`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功；保留既有 Vite chunk size warning。
- `git diff --check`
  - 通过：无 trailing whitespace 或 patch 格式问题。

## 剩余风险

- 本轮只改 PC 普通首屏文案和测试，不触发真实机器人运动，也不验证真实上位机送达确认。
- 旧的 `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/*.json` 脏文件不是本轮改动，提交时保持不纳入。
