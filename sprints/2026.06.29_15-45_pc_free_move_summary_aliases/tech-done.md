# PC 自由移动 summary alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`readback_summary.free_roam` 新增 `free_move_start_ready`、`free_move_start_status_plain`、`motion_runtime_status_plain`、`mapping_readiness_ready`、`mapping_blocked_reasons`、`mapping_acceptance_status_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 从只读 free-roam runtime 派生这些 alias，和独立 `/api/robot-control/free-roam/autonomy/latest` 的启动/运行/建图验收语义对齐。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：同步 fixture 和回归断言，覆盖“自由移动可启动但 motion_ready=false”和“readback 部分超时仍保留 free_move_start_ready=true”两类现场形态。
- `docs/product/pc_tools_workstation.md`：同步只读字段合同和无控制边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam"`，结果 `12 passed | 153 skipped`。
- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "HTTP first-screen budget"`，结果 `1 passed | 164 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed` test files，`382 passed` tests。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 成功；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提示，不影响本轮字段合同。
- 通过：`git diff --check`。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读检查 live `/api/robot-control/summary`，`readback_summary.free_roam.free_move_start_ready="true"`，`motion_runtime_status_plain="当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。"`，`mapping_blocked_reasons="camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview"`。

## 剩余风险

- 本轮只增加只读 summary 字段，不启动自由移动、不发送 keyboard/manual/Nav2/delivery/stop 或 `/cmd_vel`。
- 真实目标仍未完成：摄像头 UVC 无首帧；雷达当前已有 latest scan proof，但建图还缺新鲜雷达、地图记录和地图画面；Nav2 需要 ROS 模式重跑同窗口 wheel L/R 复验；建图需要相机和雷达 ready 后现场验证。
