# PC 自由移动/建图状态前置

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏当前卡点区新增 `plain-free-move-mapping-frontload` 只读提示，把“自由移动可先做、发车前只需要现场安全确认、相机/雷达不作为自由移动发车前预检、建图启动还差什么”前置展示；同步暴露固定 free-roam latest、free-roam start、map start 和 summary endpoint，以及不启动 Nav2/manual/keyboard/free-roam/map runtime/delivery/stop 的 DOM 合同。
- `pc-tools/workstation/test/App.test.ts`：补充普通用户首屏 DOM 测试，锁定自由移动/建图分层文案、建图缺口中文化和 no-motion 属性。
- `docs/product/pc_tools_workstation.md`：记录 `plain-free-move-mapping-frontload` 合同，明确该段落只读/只聚焦，不自动发车、不启动建图、不发布运动命令。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，`1 passed | 230 skipped`。第一轮发现前置文案使用可见态过滤导致 `data-mapping-lidar-blocks-start=true` 时可见文案未显示雷达缺口，已改为严格按 `live_closure_summary.mapping_start_missing_reasons` 中文化展示后复跑通过。
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，`7 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 构建通过；仍有既有 chunk size warning。
- 通过：`npm test`，`3 passed / 417 passed`。
- 通过：`git diff --check`。
- 通过：PC Node 监听 `*:7001`，进程为 `node ... src/server/index.ts` PID `56487`；只读 `GET http://127.0.0.1:7001/map` 返回 `200`。
- 通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `primary=nav2_route_execution`、`free_move_start_ready=true`、`free_move_minimal_precheck_safety_only=true`、`free_move_camera_preflight_required=false`、`free_move_radar_preflight_required=false`、`mapping_start_ready=false`、`mapping_start_missing_reasons=[camera_first_frame]`、`mapping_lidar_blocks_start=false`、`mapping_unblock_allows_free_move=true`、固定 `free_roam_start=/api/robot-control/free-roam/autonomy/start` 和 `map_start=/api/robot-control/map/start`。

## 剩余风险

- 本轮只改善 PC 普通用户界面的只读引导和验收合同，不发送任何运动/control POST；真实自由移动、Nav2 路线执行、建图启动仍需要现场勾安全确认后由用户触发并复验 wheel raw L/R、delivery success、相机首帧和雷达/地图材料。
