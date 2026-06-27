# 2026-06-27 15:24 PC free-roam runtime scan WYSIWYG

## sprint_type: micro

## 设计结论

本轮推进“雷达开始后在地图/建图 gate 上所见即所得”。live 状态显示 free-roam runtime 已经读到实时
`/scan` 快照，但旧 `radar/scan-proof/latest` artifact 仍是 stale/incomplete；PC summary 因旧 proof
把 `lidar_fresh` 放进 `mapping_missing`，导致用户看到“雷达已在 runtime 里新鲜”与“建图还缺雷达”互相打架。

正确口径：

- 有 `free_roam_autonomy_latest.latest_result.snapshot.lidar_age_s <= 1.5` 且
  `lidar_min_distance_m` 有限时，建图雷达 gate 采用 runtime `/scan` 当前事实。
- 没有 runtime snapshot 时，旧 ready gate 仍必须被 stale proof 降级，避免历史记录误导。
- 该改动只修只读 summary，不启动雷达、不启动 free-roam、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `freeRoamRuntimeGatesFromReadbacks()` 新增 runtime lidar snapshot 判定。
  - 当 runtime scan 新鲜时，保留 `lidar_fresh=ready`，并写出
    `free-roam runtime /scan 新鲜：距离 Xm，延迟 Ys`。
  - 旧 proof stale 的降级逻辑仍保留，但只在没有实时 runtime scan snapshot 时生效。
- `pc-tools/workstation/test/catalog.test.ts`
  - 保留旧 ready gate + stale proof 降级测试。
  - 新增 live 形态回归：runtime scan 新鲜、proof latest stale 时，`mapping_missing` 不再包含 `lidar_fresh`。
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 runtime scan 优先级和安全边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "stale radar readback|fresh free-roam runtime scan"`
  - `Tests 2 passed | 125 skipped`
- 已通过：`cd pc-tools/workstation && npm test`
  - `Tests 293 passed`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 保留既有 Vite chunk size warning。
- 已通过：`git diff --check`

## Live 只读验证

- PC Node 已重启并监听 `0.0.0.0:7001`，进程命令为 `tsx src/server/index.ts`。
- `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回：
  - `free_roam.mapping_missing=camera_first_frame,mapping_active,fresh_map_preview`
  - `lidar_fresh.state=ready`
  - `lidar_fresh.evidence=free-roam runtime /scan 新鲜：距离 0.04m，延迟 0.03s`
  - `safe_to_control=false`
- 本轮没有调用任何运动 POST。

## 剩余风险

- 相机仍未读到首帧，因此建图验收仍缺 `camera_first_frame`。
- 地图记录未启动且 fresh map preview 未满足，因此 `mapping_ready=false` 是正确结果。
- 雷达点数组仍可能为空；本轮只修 runtime freshness 与建图 gate 的一致性，不伪造地图雷达点。
