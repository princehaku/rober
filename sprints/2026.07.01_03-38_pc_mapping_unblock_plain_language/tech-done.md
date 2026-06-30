# PC 建图解锁文案标点收口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `mapping_start_unblock_plain` 复用普通句子清理逻辑，先去掉相机诊断末尾标点，再拼接“只读复测相机首帧和 MJPEG 状态”。
  - 建图解锁口径保持不变：相机首帧/雷达新鲜只阻塞建图，不阻塞安全确认后的自由移动。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 live closure fixture，普通首屏建图提示不再出现 `。；`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 新增 `mapping_start_unblock_plain` 不含 `。；` 的回归断言。
- `docs/product/pc_tools_workstation.md`
  - 同步记录建图解锁文案必须清理机械标点拼接，且不改变任何 motion/control 门禁。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，6 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Robot Control V1|mapping|live closure"`，1 file passed，8 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，Vite chunk size warning 仍为既有提示，构建成功。
- 通过：`cd pc-tools/workstation && npm test -- --run`，3 files passed，413 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`，0 errors，0 warnings。
- 通过：`git diff --check`。
- 通过：7001 只读 smoke，listener PID `40555`，`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `live_status=needs_wheel_rerun`、`free_move_ready=true`、`mapping_ready=false`、`mapping_missing=camera_first_frame`；`mapping_start_unblock_plain` 不含 `。；`，并继续显示“自由移动仍可先做”，`mapping_unblock_sends_motion_when_clicked=false`、`map_display_starts_ros2=false`、`map_display_starts_nav2=false`。

## 剩余风险

- 本轮只修普通用户文案，不修真实相机 USB/UVC 链路，也不执行自由移动、Nav2、键盘或建图动作。
- 当前建图仍因相机首帧失败未就绪；自由移动仍可在现场安全确认后先做。
