# PRD: O9 PC + SLAM Runtime Epic

## sprint_type

sprint_type: epic

## O9 最低优先级核对

- 最低 Objective：O9，约 18%。
- 本轮命中：是。
- 产品判断：继续推进 O9，目标是把 05-06 的 fresh proof/readback 变成 PC 可读现场证据，并把 SLAM `/map` 或 continuous radar blocker 收敛到新证据或明确 root cause。

## 需求

1. Full-stack：PC same-origin refresh 必须展示 fresh proof 的 hz、TF、`runtime_summary_fallback`、`continuous_scan_status=not_proven` 和 blocker，不把 fresh artifact 包装成 continuous radar ready。
2. Full-stack：尽量跑 PC 本机 API live smoke 到 `http://192.168.1.11:8787`，证明 PC path 不是纯 fixture。
3. Robot Software：通过 `root@192.168.1.11 -p 37878` 推进 SLAM `/map` lifecycle 或 continuous radar root cause。
4. Robot Software：至少形成新的 `/map`、map artifact、radar continuity evidence，或写清阻塞在 ROS2 topic、slam_toolbox lifecycle、map artifact path、service/API、TF 或 runtime 权限哪个根因。

## 最近两轮 blocker 与防重复

- 04-05 blocker：继续 Micro/status/readback 会偏离 O9，不允许。
- 05-06 blocker：PC 字段展示和 live smoke 未完成；SLAM `/map` artifact 缺失，continuous radar not_proven。
- 防重复：不得只交 `fresh_scan_proof_observed=true`、hz `257.987` 或 latest artifact loaded 的复读材料。

## 验收口径

- Full-stack 验收：PC UI/API 输出必须含 hz、TF、`runtime_summary_fallback_used`、fresh proof、continuous not_proven、blockers；live smoke 成功或失败 root cause 必须记录。
- Robot Software 验收：必须有新 map/radar runtime evidence 或 root cause；不能只引用 05-06 latest proof。
- 证据边界：可计为 `robot_runtime_material`、`software_guard` 或 `blocked_with_root_cause`；不得声明 HIL、PC WASD、Nav2 ready、`safe_to_control=true` 或真实送达。

## 责任 Engineer

- Full-stack Software Engineer：O7 PC 同源 operator workflow。
- Robot Software Engineer：O3/O9 upper 8787、ROS2 SLAM/map/radar runtime。
