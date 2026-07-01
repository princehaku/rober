# PC 地图大屏进入即刷新雷达贴图

sprint_type: micro

## 实际改动

- `/map` 直达地图大屏进入后，从仅刷新地图预览/雷达状态升级为先刷新 no-motion 雷达 scan proof，再读取地图预览和雷达状态。
- 在 `plain-map-panel`、`plain-map-direct-view-link` 和 `plain-map-display-proof` 增加直达进入读回合同：刷新雷达 scan proof、刷新地图预览、刷新雷达状态，同时明确不启动雷达 lifecycle。
- 同步 App 测试、`pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`，把“地图大屏打开即按当前雷达读回验收 marker”的边界写清。

## 验证结果

- 已通过：`git diff --check`
- 已通过：`cd pc-tools/workstation && npm test -- App.test.ts`，1 个测试文件、235 个用例通过。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有大 chunk warning。
- 已通过：重启 `0.0.0.0:7001` 后，`curl -I http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`；summary 回读 `map_display_primary_url=/map`、默认缩放 `1000%`、最高 `3200%`，并保持 `map_display_sends_motion_when_clicked=false`、`map_display_starts_nav2=false`、`map_display_starts_map_runtime=false`、`map_display_starts_rviz2=false`、`map_display_starts_foxglove=false`。

## 剩余风险

- 本轮只保证 PC `/map` 打开时会触发 no-motion 雷达 scan proof 与地图读回链路，不证明真实雷达点一定已经可见；真实可见性仍取决于上车 `/api/radar/scan-proof/refresh`、`/api/map/preview` 和硬件雷达状态。
- 本轮不执行 Nav2、不启动自由移动、不启动建图、不提交送达，也不证明真实 wheel raw L/R 非零。
