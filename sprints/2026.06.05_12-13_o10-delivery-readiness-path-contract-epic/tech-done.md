# Tech Done: O10 Delivery Readiness Path Contract Epic

## sprint_type

sprint_type: epic

## 收口时间

- 2026-06-05 12-13 CST

## 实际改动汇总

本轮完成 O10 第一段 `KR-O10-Path-Contract-Lock` 的交付收口：Robot Software 已把 map lifecycle proof latest JSON 的 canonical 路径锁定到 `/root/rober/onboard/runtime/map_lifecycle_latest.json`，map artifacts 锁定到 `/root/rober/onboard/runtime/maps`，旧 `/root/rober/runtime/map_lifecycle_latest.json` 只作为 `legacy_exists=true` 与 compatibility path 暴露。

| Owner | 实际结果 | evidence type | 结论 |
| --- | --- | --- | --- |
| Robot Software Engineer | 修正并远端部署 upper map proof latest path contract；8787 `POST /api/map/proof/refresh` 与 `GET /api/map/proof/latest` 均通过，latest proof 为 `map_once_artifact_metadata_observed`，`root_causes=[]`。 | `robot_runtime_material` | 通过，计入 O10/O3/O9 的路径契约材料。 |
| Full-stack Software Engineer | 新增 PC same-origin `GET /api/o7/direct-upper/map/proof/latest`，direct status 可展示 canonical/resolved/configured/compatibility path、fail-closed 和 safety false。 | `software_guard` + API readback | 通过，计入 O7/O10 workflow 前置，但不是 browser/user acceptance。 |
| Robot Algorithm Engineer | AMCL/Nav2 readiness 仍 blocked：等待 canonical path 对应真实 map/waypoint 后再跑 map quality 与 no-motion AMCL/Nav2 readiness；电梯 OpenCV field eval 缺真实/受控图片 manifest。 | `blocked_with_root_cause` | 不涨 AMCL/Nav2 或 O2/O10 elevator eval。 |
| Hardware Infra Engineer | 确认本轮 no-motion，不触碰 WAVE ROVER、UART、`/cmd_vel` 或 `/api/base/manual`；stop-first HIL 缺现场看护、净空、急停/断电和 CEO/现场授权。 | `blocked_with_root_cause` | 不涨 O1/HIL，不证明 `safe_to_control=true`。 |

## 关键证据

- canonical latest JSON：`/root/rober/onboard/runtime/map_lifecycle_latest.json`
- canonical map artifacts：`/root/rober/onboard/runtime/maps`
- legacy latest JSON：`/root/rober/runtime/map_lifecycle_latest.json`，仍存在但只作为 `legacy_exists=true` / compatibility。
- 8787 map proof refresh/latest：HTTP 200，`artifact.path`、`resolved_path`、`canonical_path` 均指向 canonical latest JSON。
- latest proof：`status=map_once_artifact_metadata_observed`，`root_causes=[]`。
- PC 8788 API：status、scan latest、map latest curl 通过；map latest path 指向 canonical latest JSON。
- safety：`safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。

## 验证结果

Robot Software:

```text
python3 -m unittest onboard/scripts/test_upper_robot_api.py
35 tests OK, skipped=3

python3 -m unittest onboard/scripts/test_o3_map_lifecycle_proof.py
失败：仓库没有 onboard/scripts/test_o3_map_lifecycle_proof.py，本轮文件范围未授权新增。

python3 -m compileall -q onboard/scripts onboard/src
通过

远端 8787 POST /api/map/proof/refresh
HTTP 200, --output /root/rober/onboard/runtime/map_lifecycle_latest.json, --map-dir /root/rober/onboard/runtime/maps

远端 8787 GET /api/map/proof/latest
HTTP 200, status=map_once_artifact_metadata_observed, root_causes=[]
```

Full-stack:

```text
cd pc-tools/workstation && TMPDIR=/tmp npm test -- --run test/App.test.ts
Test Files 1 passed (1), Tests 30 passed (30)

cd pc-tools/workstation && TMPDIR=/tmp npm run build
通过

curl http://127.0.0.1:8788/api/o7/direct-upper/status
status=ready, map_proof_artifact_path=/root/rober/onboard/runtime/map_lifecycle_latest.json

curl http://127.0.0.1:8788/api/o7/direct-upper/map/proof/latest
upper_request.ok=true, artifact_status=loaded, fail_closed=true, safe_to_control=false
```

Algorithm:

```text
PYTHONPATH=onboard/src/ros2_trashbot_nav python3 -m ros2_trashbot_nav.map_quality_metrics ... || test $? -eq 1
通过；fixture 预期 fail-closed，software_guard_pass=false，reachable_ratio=0.25

python3 -m unittest onboard/src/ros2_trashbot_vision/test/test_elevator_opencv_baseline.py
Ran 7 tests, OK
```

Hardware:

```text
sed -n '1,220p' docs/vendor/VENDOR_INDEX.md
通过，确认 vendor source-of-truth 入口。

python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
Ran 18 tests, OK
```

## 偏差与失败定位

- `onboard/scripts/test_o3_map_lifecycle_proof.py` 不存在，Robot Software 未在本轮授权范围内新增；该缺口不影响已完成的 upper API path contract 回归和远端 readback，但下一轮若继续推进 AMCL/Nav2 readiness，应补 helper 单测或明确替代验收。
- Full-stack 第一轮测试因旧 mock 缺少新增 map proof 字段导致渲染错误，已用空数组默认值修复；第二轮曾误改 scan proof token，已恢复既有口径。
- Algorithm 侧 map quality fixture 预期失败，说明当前 waypoint fixture 不是可导航材料。
- Hardware 侧没有现场安全前提，stop-first HIL 保持 blocked。

## OKR 影响

- O10：0% -> 约 7%。理由：`KR-O10-Path-Contract-Lock` 形成远端 `robot_runtime_material`，并能被 PC same-origin API 读取；但 delivery-readiness chain 仍有 AMCL/Nav2、电梯图片、HIL、浏览器点击四个未完成段。
- O3：约 76% -> 约 77%。理由：latest JSON 路径契约已从漂移修正为 canonical onboard runtime，可支撑下一步 AMCL/Nav2 readiness；不证明地图可导航。
- O7：约 92% -> 约 93%。理由：PC 新增 map proof latest same-origin API/readback，operator 能看到 canonical path 和 fail-closed 边界；没有浏览器点击或 PC 控车。
- O8：约 48% -> 约 49%。理由：本轮按 O10 Epic 收口，四 owner evidence type 与 blocker 边界清楚；这是治理进展，不是产品能力。
- O9：约 20% -> 约 22%。理由：短周期真实材料战役中的 latest path root cause 被修正并远端验证；仍不证明 continuous radar、AMCL/Nav2、HIL 或 delivery success。

## 剩余风险

- 不证明 continuous radar、AMCL/Nav2 consumption、PC WASD、HIL、robot ACK、`T=1001` 同场反馈、真实电梯识别、真实送达或 `safe_to_control=true`。
- Full-stack 没有浏览器点击/Playwright 证据，只能算 software guard/API readback。
- Algorithm 缺真实 map + waypoint manifest，AMCL/Nav2 readiness 仍不能启动。
- 电梯 OpenCV field eval 缺真实/受控图片 manifest。
- stop-first HIL 缺现场看护、净空、急停/断电和 CEO/现场授权。
