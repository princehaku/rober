# Robot Software Engineer Owner Note

## sprint_type

sprint_type: epic

## Path Contract

- canonical latest JSON: `/root/rober/onboard/runtime/map_lifecycle_latest.json`
- canonical map artifacts: `/root/rober/onboard/runtime/maps`
- legacy latest JSON: `/root/rober/runtime/map_lifecycle_latest.json`

本轮修正的根因是 upper API 进程 cwd 与 helper onboard workdir 不一致：相对
`runtime/map_lifecycle_latest.json` 在 8787 服务中可能落到 `/root/rober/runtime`。
API 默认值、helper 默认值和相对路径解析现在统一指向 onboard runtime；legacy path
只作为 `compatibility_paths`/`legacy_exists` 暴露，latest readback 不从 legacy path
兜底读取。

## Actual Changes

- `onboard/scripts/upper_robot_api.py`：锁定 map lifecycle proof canonical path，解析相对
  `runtime/*` 到 `/root/rober/onboard/runtime/*`，并在 artifact 元数据中暴露
  `configured_path`、`resolved_path`、`canonical_path`、`legacy_path`、
  `compatibility_paths` 和 `legacy_exists`。
- `onboard/scripts/o3_map_lifecycle_proof.py`：默认 `--output` 与 `--map-dir` 改为
  `/root/rober/onboard/runtime/...` 绝对路径，避免直接运行 helper 时受当前目录影响。
- `onboard/scripts/test_upper_robot_api.py`：增加 path contract 回归，验证相对路径不再漂到
  repo root runtime，且 readback 仍不启动 ROS2、不触碰底盘。
- `docs/navigation/nav2_map_quality_metrics.md`：同步 canonical/legacy 路径边界。

## Verification

本地已运行：

```bash
python3 -m unittest onboard/scripts/test_upper_robot_api.py
python3 -m compileall -q onboard/scripts/upper_robot_api.py onboard/scripts/o3_map_lifecycle_proof.py onboard/scripts/test_upper_robot_api.py
```

结果：

- `python3 -m unittest onboard/scripts/test_upper_robot_api.py`：35 tests OK，skipped=3。
- `python3 -m unittest onboard/scripts/test_o3_map_lifecycle_proof.py`：失败，当前仓库没有
  `onboard/scripts/test_o3_map_lifecycle_proof.py`，本轮文件范围未授权新增该文件。
- `python3 -m compileall -q onboard/scripts onboard/src`：通过。
- `git diff --check -- ...`：通过。

远端 8787 已部署 `upper_robot_api.py` 与 `o3_map_lifecycle_proof.py`，并重启
`trashbot-upper-robot-api.service`。远端验收命令结果：

- `POST /api/map/proof/refresh`：HTTP 200，helper argv 使用
  `--output /root/rober/onboard/runtime/map_lifecycle_latest.json` 和
  `--map-dir /root/rober/onboard/runtime/maps`。
- `GET /api/map/proof/latest`：HTTP 200，`artifact.path`、`resolved_path`、
  `canonical_path` 均为 `/root/rober/onboard/runtime/map_lifecycle_latest.json`。
- latest proof：`status=map_once_artifact_metadata_observed`，
  `evidence_ref=o3-map-lifecycle-1780633643849`，`root_causes=[]`。
- map artifacts：`/root/rober/onboard/runtime/maps/trashbot_map.yaml` 和
  `/root/rober/onboard/runtime/maps/trashbot_map.pgm` 存在。
- legacy file：`/root/rober/runtime/map_lifecycle_latest.json` 仍存在，readback 中
  `legacy_exists=true`，但不再作为 latest readback 来源。
- no-motion 安全边界保持：`publishes_cmd_vel=false`、`calls_base_manual=false`、
  `sends_base_motion_commands=false`、`robot_control_executed=false`、
  `safe_to_control=false`、`hil_pass=false`。

## Remaining Risk

- 该修正只锁定 latest JSON/map artifact 路径契约，不证明 continuous radar、AMCL、Nav2、
  PC WASD、HIL、WAVE ROVER ACK 或 delivery success。
- 本轮不发布 `/cmd_vel`，不调用 `/api/base/manual`，不写底盘 UART。
