# 2026-06-10 07:05 map proof API contract harden

sprint_type: micro

## 实际改动

- 更新 [`/Users/m1/apps/rober/onboard/scripts/upper_robot_api.py`](</Users/m1/apps/rober/onboard/scripts/upper_robot_api.py>)：
  - 新增 `MAP_LIFECYCLE_OBSERVED_STATUS = "map_once_artifact_metadata_observed"`。
  - 新增 `map_lifecycle_runtime_readback_contract()`，把 map proof 的顶层读回合同从通用 `software_guard_payload()` 中拆出来。
  - `GET /api/map/proof/latest` 现在会在 artifact 同时满足 `status=map_once_artifact_metadata_observed`、`scan_once_observed=true`、`map_once_observed=true`、`map_file_observed=true`、`map_metadata_observed=true` 时，直接暴露 `status` / `proof_state` / `ros2_runtime_proven` / `map_artifact_proven`。
  - `POST /api/map/proof/refresh` 现在只在 `command_result.ok=true` 且最新 artifact 同时满足上述 contract 时，才把这组 observed 字段晋升到顶层；否则继续 fail closed。
  - `map_status().proof_latest` 现在也跟随同一合同，供 PC 点灯。
- 更新 [`/Users/m1/apps/rober/onboard/tests/test_upper_robot_api.py`](</Users/m1/apps/rober/onboard/tests/test_upper_robot_api.py>)：
  - 增加 clean map proof readback 的顶层晋升断言。
  - 增加 bad JSON fail-closed 断言。
  - 增加 refresh success 时顶层不再保留 “still not attached” 话术的断言。
- 更新 [`/Users/m1/apps/rober/docs/hardware/board_sensor_stack_smoke.md`](</Users/m1/apps/rober/docs/hardware/board_sensor_stack_smoke.md>)：
  - 补充 2026-06-10 07:05 的 map proof contract harden 说明，明确 observed readback 与 safe-to-control 边界分离。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_upper_robot_api.py`
  - `Ran 7 tests in 0.008s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/upper_robot_api.py`
  - 通过，无输出。
- `rg -n "map_once_artifact_metadata_observed|map_artifact_proven|ros2_runtime_proven|safe_to_control|delivery_success" ...`
  - 命中新增合同字段与测试断言，未发现漏改。
- `git diff --check`
  - 通过，无 whitespace / patch 格式错误。
- 远端实机补充验证：
  - 已备份远端 `/root/rober/onboard/scripts/upper_robot_api.py` 到 `/tmp/upper_robot_api.py.bak.20260610050809`。
  - 已部署当前本地版本到远端正式路径并重启 `trashbot-upper-robot-api.service`，服务状态 `active`。
  - `GET /api/map/proof/latest` 读回：
    `status=map_once_artifact_metadata_observed`
    `proof_state=map_once_artifact_metadata_observed`
    `ros2_runtime_proven=True`
    `map_artifact_proven=True`
    `not_proven=False`
    `software_guard=False`
    `safe_to_control=False`
    `delivery_success=False`
  - `GET /api/status` 中的 `map.proof_latest` 摘要同样返回 observed 状态，并保持所有安全字段关闭。

## 剩余风险

- 这次只把 no-motion map lifecycle proof 的 artifact/readback 状态修正为可消费，没有把地图能力升级为 Nav2 可用、真实路线、发车许可、HIL 或 delivery 成功。
- 远端验证只覆盖 `GET /api/map/proof/latest` 和 `GET /api/status`；没有调用任何 motion endpoint，也没有重新证明地图质量、AMCL/Nav2 runtime 或实车路线。
- `POST /api/map/proof/refresh` 的成功判定仍依赖 helper 产物与本次 command result 同时成立；如果远端环境再次漂移，仍需要先定位 helper/服务侧证据链。
