# 轮速 latest 只读 alias

sprint_type: micro

## 实际改动

- `GET/POST /api/robot-control/base/feedback-samples` 顶层新增脚本友好 alias：`latest_raw_left`、`latest_raw_right`、`base_feedback_lr_nonzero_proven`。
- 新 alias 与既有 `wheel_raw_left/right` 和 `wheel_feedback_lr_nonzero_proven` 同源，只解决现场脚本读 `latest_*` 或 `base_feedback_*` 得到 `null` 的易用性问题。
- 产品文档同步说明这些字段只是只读轮速材料，不执行 Nav2/manual/keyboard/free-roam、delivery、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "base feedback samples"`，1 file passed，2 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 构建成功；保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，420 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读验证 `GET /api/robot-control/base/feedback-samples`：返回 `remote_endpoint=/api/base/feedback-samples/latest`、`wheel_raw_left/right=0/0`、`latest_raw_left/right=0/0`、`wheel_feedback_lr_nonzero_proven=false`、`base_feedback_lr_nonzero_proven=false`、`robot_control_executed=false`、`hard_dangerous_true_fields=[]`。
- 通过：同轮 no-motion 雷达恢复验证：`POST /api/robot-control/radar/scan-proof/refresh` 返回 remote 200 且 `robot_control_executed=false`；随后 `GET /api/robot-control/live-summary` 返回 `radar_map_points_visible=true`、`radar_overlay_status=loaded`、`live_wysiwyg_missing_surface_ids=["camera"]`。

## 剩余风险

- 本轮只补字段 alias，没有执行运动命令。
- 当前真实轮速材料仍未证明同窗口 L/R 非零；完整路线、键盘连续手控和自由移动仍需显式安全确认后的现场运动验收。
