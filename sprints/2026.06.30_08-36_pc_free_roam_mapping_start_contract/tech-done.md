# PC 自由移动/建图启动合同拆分

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中新增建图启动只读口径：`mapping_start_ready/mapping_start_missing/mapping_start_readiness_plain/mapping_start_next_action_plain` 与 `free_roam_mapping_start_*`，只以画面首帧和雷达新鲜判断能否启动建图记录。
- 保留旧 `mapping_ready/free_roam_mapping_ready` 作为建图验收口径，继续要求画面首帧、雷达新鲜、地图记录和地图画面，避免老脚本语义漂移。
- 在 `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/test/catalog.test.ts`、`docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md` 和 `pc-tools/README.md` 同步字段合同、测试和文档。

## 验证结果

- 已通过定向验证：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam"`，结果 `12 passed | 148 skipped`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `375 passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，新 PID 为 `28483`。
- 已通过 7001 只读 summary live 验证：`free_roam.motion_start_ready=true`，`free_roam.mapping_start_ready=false`，建图启动缺口为 `camera_first_frame,lidar_fresh`；相机返回“不是页面独占，是 UVC 设备没有输出视频帧”；雷达返回 `radar_stopped`。

## 剩余风险

- 本轮新增的是只读 summary/contract 字段，不调用 free-roam、建图、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实车当前相机首帧和雷达 fresh 仍需现场硬件恢复后复验；合同会明确显示建图启动缺口，不再把它误写成自由移动不能开始。
