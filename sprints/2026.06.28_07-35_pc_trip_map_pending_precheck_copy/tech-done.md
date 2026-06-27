# PC 行程地图刷新等待文案微迭代

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏行程前确认在地图画面或地图 proof 刷新中时，改为提示“安全确认已完成；等待地图画面/状态刷新后再执行。这不是额外预检，是避免按旧地图发车。”
- `pc-tools/workstation/test/App.test.ts`：补齐地图画面刷新中、地图状态刷新中两条断言，锁定最小预检与地图所见即所得的关系。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明地图刷新等待不是额外人工预检，只是防止旧地图发车的 WYSIWYG 保护。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "blocks visible-route execution while the map preview is refreshing"`，结果 `1 passed | 201 skipped`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed`、`350 passed`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；保留既有 Vite chunk size warning，产物构建成功。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只做 PC 前端文案、测试和文档收口，不发送真实 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`，不证明真实车已经完成路线执行。
