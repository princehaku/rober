# PC 行程自动驾驶诊断 Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `行程操作` 卡片新增 `自动驾驶诊断` 行，复用 `当前事实` 的 Nav2/service/localization/root-cause 口径，直接说明服务未运行、路线未准备、定位或 `/scan`/AMCL/TF 缺口，并明确相机/雷达不挡底盘试动或键盘手控。
- `pc-tools/workstation/test/App.test.ts`：补充服务未运行和 blocker root-cause 两个用例断言，锁定诊断行不触发 Nav2 execute、manual、delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步记录普通首屏诊断行为、摄像头共享预览非独占口径，以及底盘自由移动不依赖雷达的边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Nav2 restore|current Nav2 blocker"`，结果 `1 passed (1)`，`2 passed | 200 skipped (202)`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`，`350 passed (350)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有 chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只做 PC 前端和文档闭环，没有触发真实小车运动、真实 Nav2 NavigateToPose、真实摄像头首帧或真实雷达 runtime。
- 摄像头“谁进来都能看”依赖既有 PC MJPEG relay 和上位机 `/api/camera/mjpeg` 输出首帧；如果 UVC 本身无帧，页面会继续按“不是独占，检查 USB/输入/供电”提示。
