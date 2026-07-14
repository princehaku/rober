# O3 Map Odom TF Path Recovery Side-to-Side Check

## 验收结论

本轮满足 Epic sprint 收口的最小验收，但结果仍是 fail-closed，不构成 same-run path success、route execution、delivery、HIL 或 production 证据。

对照 `pre_start.md` / `prd.md` / `tech-plan.md` 的目标，本轮结论如下：

1. `map->odom` 没有恢复成功：
   - live artifact `artifacts/live_nav2_direct_helper_partial_after_lazy_initialpose.raw.json` 仍是 `status=blocked_with_root_cause`；
   - `proof.localization_tf_observed.map_to_odom=false`；
   - `proof.localization_tf_observed.map_to_base_link=false`；
   - `proof.path_generated=false`。
2. root cause 比上一轮更具体，但还没有达到“恢复路径生成”：
   - 旧的 `/initialpose` verbose topic-info 卡点已越过；
   - 新的 direct helper 最终 root causes 收敛为 `/scan_once_not_observed`、`cli_initialpose_publish_failed`、`/amcl_pose_once_not_observed`、`map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom`、`localization_not_ready_for_path_generation`。
3. 外层 preflight 仍未自然落盘 final body：
   - `tech-done.md` 已记录主会话 live preflight 仍卡在 localization smoke 的远端 ROS 只读链；
   - 因此本轮真实板最终证据继续以 direct helper artifact 为准。

## 用户价值判断

这轮没有直接增加普通用户可见能力，但它继续把“为什么同 run 还拿不到路径”从笼统 runtime/refresh 问题推进到更窄的现场定位链问题。对 O1/O6/O7 的价值只体现在前置 blocker 收敛：

- O1 仍缺 `current same-run path generation success` 与 `Nav2 route execution success`；
- O6/O7 仍缺 current-run `route.csv`、keyframe、rosbag、replay JSONL、delivery/operator 或 production evidence；
- 因此本轮只能记作 O3 no-motion supporting evidence，不能转成主 Objective 百分比增量。

## 验收对照

- 通过：
  - `managed_runtime_started=true`
  - `map_server_active=true`
  - `amcl_active=true`
  - `initialpose_publish_method=ros2_topic_pub_once_cli_fallback`
  - `initialpose_subscriber_count=1`
  - lazy initialpose info probe 修复已在真实板上越过旧卡点
  - `py_compile`、目标 unittest、本地 dry-run、scoped diff hygiene 已有验证记录
- 未通过：
  - `initialpose_published=true`
  - `/amcl_pose_once` 观测恢复
  - `map_to_odom=true`
  - `map_to_base_link=true`
  - `path_generated=true`
  - outer preflight 自然回读 helper final body

## Product 判定

- OKR 方向：`继续`
- 百分比调整：`不调整`
- KR 归档：`不归档`
- 下一轮入口：继续现场 O3 lane，但不能再把“拉长等待时间”本身当成进展，必须先把 `/scan`、`/amcl_pose`、`/odom`、`/tf` 单条 probe 的耗时/新鲜度和 dynamic TF 缺口分层落盘。
