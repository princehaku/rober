# PC Nav2 只读端点失败下一步修正

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中新增 Nav2 只读端点不可读 blocker：
  - `robot_api_nav2_read_failed`：`/api/nav2/status` 或 `/api/nav2/proof/latest` 读取失败；
  - `robot_api_map_localize_read_failed`：`/api/map/proof/latest` 或 `/api/localize/proof/latest` 读取失败。
- 在普通文案中把这类 blocker 翻译为“自动驾驶状态读取失败”和“地图/定位读取失败”，并把下一步改成先确认小车地址和上位机 API 可读，再刷新地图/自动驾驶状态并准备图上路线。
- 在 `pc-tools/workstation/test/catalog.test.ts` 中新增 live-like 场景测试：小车 base URL 可访问但 Nav2/地图/定位 readback 返回失败时，summary 不再只提示“先生成图上路线”。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 已通过定向验证：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "fix API readback|Robot Control summary proxies Robot API readback endpoints"`，结果 `2 passed | 160 skipped`。
- 已通过 Nav2 相关回归验证：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "fix API readback|stopped Nav2 stack|latest Nav2 command mode|nested nav2 status proof|controller is inactive|managed runtime can start lifecycle"`，结果 `6 passed | 156 skipped`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `2 files / 377 tests passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，监听 Node PID 为 `18961`。
- 已通过 7001 只读 summary live 验证：
  - `safe_command_boundary.nav2_goal_ready=false`；
  - `nav2_goal_blockers=["robot_api_nav2_read_failed","robot_api_map_localize_read_failed","path_generation_not_observed","path_point_count_not_positive"]`；
  - `nav2_goal_next_action_plain="先确认小车地址和上位机 API 可读，再刷新地图/自动驾驶状态并准备图上路线。"`；
  - `readback_summary.nav2.current_blocker_labels="自动驾驶状态读取失败、地图/定位读取失败"`。

## 剩余风险

- 本轮只改只读 summary 文案和测试，不自动刷新 proof、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- live 上如果上位机 Nav2/地图/定位 endpoint 持续不可读，完整 Nav2 路线执行仍需要先恢复上位机 API 可读性。
- 本轮没有调用 Nav2 execute、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；live 验证只读 `GET /api/robot-control/summary`。
