# Map Radar Overlay Pose Gate

sprint_type: micro

## 实际改动

- PC 普通首屏地图视口中的雷达 marker 从右上角状态贴片改为地图内 overlay。
- 当 `amcl_pose_observed` 或 `localization_tf_observed` 为 true 时，雷达运行态会在机器人 marker 坐标上显示 `雷达` 标签和脉冲圈。
- 当雷达 lifecycle 已运行但定位未读到时，地图中央显示 `雷达已运行，位置未读到` 或 `雷达待刷新，位置未读到`，不再画假坐标。
- 补充 Vue 测试：默认无定位状态不显示脉冲圈；有 map-frame pose 时才显示 `plain-map-radar-pulse`。
- 同步更新 PC 产品文档和 fixed-route 工作流文档。

## 验证结果

- 已通过 targeted 测试：`npm test -- -t "renders Robot Control V1|radar pulse|stale Nav2 rerun|shows plain radar start"`。
- 已通过完整 `npm test`：2 个测试文件、153 个测试全部通过。
- 已通过 `npm run lint`。
- 已通过 `npm run build`。
- 已通过 `git diff --check`。
- 已重启 PC workstation 到 `0.0.0.0:7001` 并做真实页面 DOM 验证：地图 PNG 已加载，地图视口为 `地图可见`，雷达 marker 为 `mode-known-pose-pending`、文本 `雷达待刷新`，机器人 marker 可见；当前雷达 proof stale，因此不显示 `plain-map-radar-pulse`。
- 真实上位机只读状态显示 radar lifecycle 正在运行，但 `latest_scan_proof_fresh=false`；PC summary 当前读到 AMCL/TF 为 true，所以真实页面进入“地图内已定位但雷达待刷新”的 overlay 状态。

## 剩余风险

- 当前真实上位机没有稳定 AMCL/map-frame pose，因此真实现场仍会显示“位置未读到”；这是正确缺口，不会伪造成雷达坐标。
- 本轮没有新增 scan 点云绘制，也没有触发雷达启动、Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
