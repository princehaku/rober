# O3 AMCL TF Bringup Repair Tech Done

## sprint_type

sprint_type: epic

## 自主能力目标和本轮抓手

- 目标：在 no-motion 安全边界内，把 AMCL 初始化从易超时的 CLI publish 推进到更稳定、可观测的进程内 publisher，并让同轮 artifact 能直接说明 `/initialpose`、`/amcl_pose`、`map->odom` 与 planner-only path generation 的真实状态。
- 抓手：优先修改 `o10_amcl_nav2_runtime_proof.py` 的 `/initialpose` 发布路径，补足 publish method / subscriber count / attempts / elapsed / error 字段；同时复用现有 preflight/测试/文档改动完成本地验收，并对真实板执行一次受控 live 预检。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增进程内 `rclpy` `/initialpose` burst publisher，优先等待订阅者后短窗口重复发布，避免 `ros2 topic pub --once` 冷启动和 QoS 抖动。
  - 顶层 proof / phase snapshot 新增 `initialpose_publish_method`、`initialpose_subscriber_count`、`initialpose_publish_attempts`、`initialpose_publish_elapsed_ms`、`initialpose_publish_error`。
  - 保留 CLI fallback，但 fallback 只作为次级路径，不能覆盖 rclpy 成功事实；同时把 rclpy 尝试细节写入 fallback detail。
  - root cause 分类新增 `AMCL initialpose` 层，允许把 `subscriber_missing`、`rclpy_initialpose_import_failed`、`cli_initialpose_publish_failed` 等 publish 根因直接写进 artifact。
  - planner lifecycle / node info 探针延后到 localization ready 之后，避免 AMCL/TF 还没成立时先把 proof 预算耗在 planner CLI 上。
- `onboard/scripts/field_route_evidence_preflight.py`
  - 为 `/api/nav2/proof/refresh` 新增由请求预算推导的硬超时链：`curl --max-time`、进程级 `process_timeout_s` 和 fail-closed summary 统一从同一预算推导，不再使用 `args.timeout_s + 62` 这种长等待。
  - timeout / 非零返回 / JSON 解析失败统一落成结构化 `summary`，包含 `status`、`timed_out`、`naturally_returned`、`returncode`、`curl_max_time_s`、`process_timeout_s` 与固定 no-motion false flags。
  - `root_cause_summary.nav2_refresh` 同步携带 refresh summary，保证 live timeout/readback fail 也能直接落到主 packet JSON。
- `onboard/tests/test_field_route_evidence_preflight.py`
  - 新增 remote refresh timeout / command failed 回归，确保 timeout 和非零返回都 fail-closed，且不会抛异常或丢失安全字段。
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
  - 上述文件在进入本轮前已存在与 O3 no-motion 预检相关的工作树改动；本轮验收直接沿用这些改动完成测试和 dry-run，不额外扩大文件范围。

## 验证结果

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py`
  - 通过。
- `python3 -m unittest onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api`
  - `Ran 125 tests in 0.266s`, `OK (skipped=1)`。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test`
  - `Ran 23 tests in 0.042s`, `OK`。
- `python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/local_preflight.raw.json`
  - 输出 `status=dry_run_template_only_not_proven`。
  - 安全字段保持 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。
- `python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.raw.json`
  - 已执行，并自然返回。
  - 产出 [`/Users/m1/apps/rober/sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.raw.json)。
  - 顶层 `status=blocked_live_localization_chain_not_ready`，说明这次没有再被 refresh SSH readback 吞掉整轮 JSON。
  - refresh summary 自然返回：`status=blocked_with_root_cause`、`timed_out=false`、`naturally_returned=true`、`returncode=0`、`curl_max_time_s=38`、`process_timeout_s=42`。
- `git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_upper_robot_api.py onboard/src/ros2_trashbot_nav/config/nav2_params.yaml onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair`
  - 通过。

## 真实板 artifact 摘要

- live raw JSON 已生成：
  - [`/Users/m1/apps/rober/sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.raw.json)
- 顶层状态：
  - `status=blocked_live_localization_chain_not_ready`
  - `blocked_reason=blocked_live_localization_chain_not_ready`
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `hil_pass=false`
- localization smoke blocker：
  - `blocked_scan_not_observed`
  - `blocked_amcl_pose_not_observed`
  - `blocked_map_to_odom_not_observed`
  - `blocked_map_to_base_link_not_observed`
- refresh/readback 摘要：
  - `status=blocked_with_root_cause`
  - `timed_out=false`
  - `naturally_returned=true`
  - `returncode=0`
  - `curl_max_time_s=38`
  - `process_timeout_s=42`
  - `path_generated=false`
  - `path_generation_succeeded=false`
  - `path_point_count=0`
  - `dangerous_true_fields=[]`
- 这说明返工目标已达成：即使现场仍然 blocked，refresh/readback 也会在硬上限内自然返回，并留下可消费 raw JSON，而不是再靠人工中断收口。

## 失败定位

- 本轮软件面已经把 `/initialpose` publish 从“单次 CLI 盲发”推进到“进程内 rclpy burst + 结构化 publish 诊断”，这是当前 AMCL 初始化链上新增的可复验修复。
- 这轮返工已经修掉“refresh SSH readback 吞掉整轮 automation”这一层 blocker。
- 当前 live 主 blocker 回到现场定位链本身，而不是 timeout 机制：
  - `/scan` 未在当前窗口 healthy observed；
  - `/amcl_pose` 未 observed；
  - `map->odom`、`map->base_link` 未 observed；
  - refresh 虽然自然返回，但仍是 `blocked_with_root_cause`，还没有给出 path/material success。

## OKR 结论

- 本轮没有 same-run `path_generated=true`，也没有新的 live localization/path material 可供 O1/O6/O7 消费。
- 不调整 O1/O3/O5/O6/O7 百分比，不归档 KR。
- 本轮价值有两层：
  - 把 AMCL initialpose 发布链修到更稳定、可观测；
  - 把 live refresh/readback 从“会吞掉整轮 JSON 的挂起点”修成“硬超时/自然返回/fail-closed raw JSON”。

## 剩余风险和下一步能力建设建议

- 风险：
  - 真实板仍未产出本轮 `initialpose` / AMCL / TF / planner 成功事实。
  - 当前 live 入口不再被 refresh readback 吞掉，但现场 localization smoke 依然全链 blocked。
  - 所有现场结论仍必须保持 no-motion 边界：不发送 `/cmd_vel`、不调用 `/api/base/manual`、不执行 NavigateToPose goal。
- 下一步建议：
  - 继续围绕当前 live raw JSON 的 localization smoke blocker，下钻 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 为何在 no-motion 窗口仍全链未 observed。
  - 在真实板上把 `/initialpose` publish、`/amcl_pose` 观测和 `map->odom` 观测拆成独立 stop/start/status/refresh 证据，优先确认 refresh 之外的同轮定位事实。
  - 只有当 live artifact 明确给出 `initialpose_published=true`、`amcl_pose_observed=true`、`map_to_odom=true` 之后，才继续判断 planner-only `path_generated`。
