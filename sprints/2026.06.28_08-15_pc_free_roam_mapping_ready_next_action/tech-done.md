# PC 自由移动建图 ready 下一步微迭代

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当画面首帧和雷达都 ready、建图验收只差地图记录时，首屏当前事实和自由移动准备区明确提示下一步启动扫图记录。
- `pc-tools/workstation/test/App.test.ts`：新增回归，锁定该状态下 `开始记录（不发车）` 可用、自动扫图 start 仍被地图记录 gate 挡住，点击只调用固定 map lifecycle，不触发 free-roam start、manual、Nav2 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明该提示不放宽 `free_roam_mapping_ready=false`，只改善普通用户下一步。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "points mapping-ready users to start the map recording when only mapping runtime is missing"`，结果 `1 passed | 202 skipped`。
- 发现并修复：完整回归发现旧 ready 用例里的按钮文案断言与新“先启动地图记录”口径冲突；已收敛为仅在地图记录缺失时显示 `开始记录（不发车）`，ready 后仍显示 `开始自动扫图（低速）`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "starts free-roam autonomy through the fixed proxy|starts map recording before auto sweep|points mapping-ready users"`，结果 `3 passed | 200 skipped`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed`、`351 passed`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；保留既有 Vite chunk size warning，产物构建成功。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修 PC 前端文案、测试和文档，不访问真实硬件，不证明真实自由移动、真实建图保存或真实 `/cmd_vel` 链路已经闭环。
