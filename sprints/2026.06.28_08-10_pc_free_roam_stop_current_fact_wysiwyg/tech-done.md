# PC 自动扫图停止当前事实 WYSIWYG Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：自动扫图/自由移动 stop 成功后，首屏 `当前事实` 会继续看停止后的地图刷新结果；地图画面已刷新时直接提示可以保存地图，刷新失败时提示先重试刷新再保存，避免顶部事实仍停在“停止请求已发送”。
- `pc-tools/workstation/test/App.test.ts`：补充自动扫图 start/stop 和 queued stop 用例，锁定 stop 后地图 marker 与 `当前事实` 同步显示 `已停止，停止后的地图画面已刷新，可以保存地图`，并继续断言不会触发 manual、Nav2 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 stop 后当前事实消费 map preview 刷新结果的用户口径和只读边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "free-roam autonomy"`，结果 `1 passed (1)`，`10 passed | 193 skipped (203)`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`，`351 passed (351)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有 chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC 普通首屏 stop 后的文案状态和测试，不触发真实 free-roam stop、真实 Nav2、真实键盘手控或 `/cmd_vel`。
- 摄像头共享预览、雷达连续 freshness、wheel raw L/R 非零和自动驾驶真实发车仍需要继续用上位机/实车证据单独闭环。
