# Algorithm Worker Report

## 自主能力目标和本轮抓手

- 目标：把 clean-baseline Nav2 no-motion path proof 安全收敛成 `trashbot.clean_baseline_nav2_path_material.v1` additive，供 O6/O7 同 task 读取。
- 抓手：单 CLI 入口 `--clean-baseline-nav2-path-json` 自动归并同目录 refresh/retry/latest/status/cleanup artifacts，只输出 first failure、retry success、path/material 摘要和固定 false safety flags。

## 改动文件和接口影响

- `onboard/scripts/field_route_evidence_manifest.py`
  - 新增 `trashbot.clean_baseline_nav2_path_material.v1`
  - 新增 `--clean-baseline-nav2-path-json`
  - manifest 顶层与 `field_motion_evidence_packet.clean_baseline_nav2_path_material` 同步写入
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 新增 ready / fail-closed 回归
- `docs/navigation/field_route_evidence_manifest.md`
  - 补充 clean-baseline additive contract

## 实现内容

- 兼容 `nav2_refresh_summary.json`、`nav2_retry_summary.json`、`nav2_latest_after_success.json`、`nav2_status_after_success.json`、`nav2_success_readback_summary.txt`。
- txt 入口只解析顶部 JSON 段落，忽略后续长 readback/log 正文，避免把 traceback、绝对路径或 response body 带进 additive。
- 对 bad schema、task mismatch、dangerous true、unsafe key/text、raw/base64/token/traceback/绝对路径统一 fail-closed。
- 固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。

## 验证结果

- `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
  - 通过
- `python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
  - `Ran 71 tests in 0.523s`
  - `OK`
- `git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/artifacts/algorithm_worker_report.md`
  - 待主节点统一复核；当前前三个目标文件已 scoped `diff --check` 通过

## 数据、样本或调试输出变化

- 新 additive 输出：
  - `first_attempt_status`
  - `retry_status`
  - `retry_success`
  - `path_generation_succeeded`
  - `path_generated`
  - `path_point_count`
  - `planner_server_active`
  - `managed_runtime_started`
  - `managed_runtime_cleanup_ok`
  - `initialpose_published`
  - `amcl_pose_observed`
  - `map_server_active`
  - `amcl_active`
  - `cleanup_readback_clean`
  - `first_failure`
  - `retry_success_summary`
  - `material_sample_refs`

## 剩余风险

- 当前只证明 clean-baseline no-motion path material 被安全消费，不证明真实 Nav2 route execution、真实机器人运动、delivery record、operator confirmation 或 HIL。
- cleanup readback 目前依赖现有日志标记的“空残留”文本模式；如果后续日志模板变更，需要同步扩充 parser 白名单。
