# Robot Software Owner Note: Operator Report 405 Fix

## Sprint / Evidence

- sprint: `sprints/2026.06.04_17-18_runtime-material-epic/`
- owner: `robot-software-engineer`
- evidence_type: `software_guard`
- deployment_status: `not_deployed_to_upper_runtime`
- target blocker: PC 同源代理 POST `/api/o7/direct-upper/operator-report` 已转到上位机 `/api/operator/report`，但真实 8787 返回 HTTP 405。

## Actual Change

- `onboard/scripts/upper_robot_api.py`
  - 新增 `POST /api/operator/report`：接收 PC/operator JSON，归一化 `evidence_ref`、`note/operator_notes`、执行前安全字段和执行后观察字段，并原子写入 latest artifact。
  - 新增 `GET /api/operator/report`：只读回放 latest operator report artifact；缺失返回 `404`，坏 JSON / 非 object 返回 `422`。
  - 新增 `ROBER_OPERATOR_REPORT_ARTIFACT_PATH` / `--operator-report-artifact-path`，默认 `runtime/operator_report_latest.json`。
  - `/api/status.routes` 和 `operator_report` 摘要现在暴露 report readback 入口，便于 PC/operator 对齐同一 `evidence_ref`。
- `onboard/scripts/test_upper_robot_api.py`
  - 新增 POST 写入 + GET readback 回归，断言不打开 fake serial、不发送命令、不提升 `safe_to_control` / `hil_pass`。
  - 新增 missing / bad JSON fail-closed 回归。
  - 新增 aiohttp route smoke：环境有 `aiohttp` 时证明 POST/GET `/api/operator/report` 均不是 405；当前本机缺依赖，测试按 skip 记录。
- `docs/interfaces/o7_upper_robot_api.md`
  - 新增 operator report evidence contract，明确 POST/GET schema、artifact 路径、状态语义和安全边界。

## Safety Boundary

- operator report 只是人工现场材料 / evidence readback。
- POST 的唯一副作用是写 JSON artifact；GET 只读文件。
- 不调用 `/api/base/manual`、`/api/base/stop`、`/api/base/status` 或 feedback endpoints。
- 不打开 `/dev/ttyS5`，不发送 `T=1/T=13/T=130/T=131`，不发布 `/cmd_vel`，不启动 ROS2。
- 不替代 stop response、post-status、`T=1001` vendor material、robot ACK、真实 HIL、ROS `/odom`/`/imu/data`/`/battery` 或视频/现场记录。

## Verification

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
```

Result:

```text
Ran 26 tests in 1.685s
OK (skipped=1)
```

Skip reason: local Python lacks `aiohttp`, so route-level TestClient smoke was skipped. Class-level POST/GET artifact regression still ran and passed.

```bash
python3 -m compileall -q onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py
```

Result: passed with no output.

## Remaining Risk

- `not_deployed_to_upper_runtime`: 本次只在当前工作区完成软件 guard 和单测；尚未把更新后的 `upper_robot_api.py` 部署到真实 Orange Pi 8787，也未复测真实 `curl -X POST http://127.0.0.1:8787/api/operator/report`。
- 因本机缺 `aiohttp`，本地未实际启动 aiohttp server；route test 已保留，进入上位机/容器具备依赖后应复跑。
- 本修复不证明 O7 PC operator workflow 已现场闭环；仍需 Full-Stack 在真实 8787 部署后复测 PC 同源代理和 UI readback。
- 本修复不改变任何硬件运动参数、底盘 motion/manual 行为或串口配置。

## Coordination

- Product / OKR Owner: 不需要改 OKR 口径；本 note 只记录 O7 blocker 的 software guard 修复，不能作为 runtime/HIL 涨分材料。
- Hardware Infra Engineer: 真实上车短 pulse 仍需 Hardware 按净空、急停、stop-first、`T=1001` 和 operator report 同源 evidence 复核。
- Robot Algorithm Engineer: 无需协同。
- Full-Stack Engineer: 需要在部署后复测 `/api/o7/direct-upper/operator-report` -> `/api/operator/report`，确认不再 `upper_http_405`。
