# 2026.06.29 03:00 PC free-roam runtime 地图指标 WYSIWYG

sprint_type: micro

## 实际改动

- PC fixed latest 只读代理从 `/api/free-roam/autonomy/latest` 的 `latest_result.map_metrics` / `snapshot` 提取 `map_free_cells` 和 `map_unknown_ratio` 短字段，不透出完整 raw artifact。
- PC 普通首屏的“刷新自由移动状态（只读）”摘要新增 runtime 地图指标展示，例如“可通行 421 格，未知 98.2%”。
- 当地图图片还没加载成功但 latest 已有 runtime 地图指标时，“扫图覆盖”卡显示 runtime 可通行格和未知区域，并提示需要刷新扫图画面后再按图片验收。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md`，记录本轮只读边界：不启动/停止 free-roam，不发送 manual/Nav2/delivery/stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts -t "free-roam autonomy latest proxy reads fixed runtime artifact without starting autonomy"`，1 passed。
- 通过：`npm test -- --run test/App.test.ts -t "refreshes free-roam autonomy latest as a read-only first-screen action"`，1 passed。
- 通过：`npm test -- --run test/App.test.ts -t "shows runtime free-roam map metrics when map preview image is not loaded yet"`，1 passed。
- 通过：`npm test -- --run`，2 files / 359 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 输出 chunk size warning，构建成功。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只做 PC 只读呈现和代理短字段，不代表相机首帧、雷达 lifecycle、Nav2 planner/controller 或真实发车 HIL 已恢复。
