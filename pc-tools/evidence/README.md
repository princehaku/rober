# pc-tools/evidence

`pc-tools/evidence/` 保留非 Python 证据资产与只读辅助脚本，当前主要入口包括：

- `pc-tools/evidence/evidence_crosscheck.py`：fixed-route status、route replay 与 task record 的软件 proof 对账入口。
- `pc-tools/evidence/fixtures/`：Fixture 根目录，Node API 会递归索引 `fixtures/**/*.json` 生成资产分组。

`evidence_crosscheck.py` 是只读脚本，默认执行 status/replay/task_record 字段对账，并保持证据边界：

- `status` 与 `status.route_progress`、`replay` 的 `checkpoint/current_index/target/failure_code/evidence_ref` 对齐为软件侧一致性输入。
- `--hil-gate`（兼容 `--hil-gate-output`）与 `--output-artifact`（兼容 `--rehearsal-artifact`）用于分别注入 HIL 对齐输入和导出 `route_task_rehearsal_artifact`。
- `CHECK summary: mismatches=0` 表示软件侧一致性通过；任何软件侧 mismatch 返回非 0。
- `hil_alignment_status.alignment_status` 会独立给出真实 HIL 对齐状态，即使软件对账 pass 也不会自动转为现场完成。
- 生成的 artifact 继续保持 `source=software_proof`、`not_proven` 与 `delivery_success=false`，不宣称真实路线、真实 HIL、真实投递成功或串口/波特率已通过。

## JSON Fixture 语义

JSON fixture 可读只表示工作站能索引并解析本地 JSON，不表示真实现场材料齐全，也不表示 HIL、手机、云端、ROS2、Nav2、WAVE ROVER 或交付成功通过。

所有工作站响应仍固定：

- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## WAVE ROVER Material Coverage

工作站的 `GET /api/hardware/wave-rover/material-coverage` 是 Node-native 只读扫描入口，不执行 Python、不调用串口、不运行 ROS2/HIL。兼容旧路径 `GET /api/tools/hardware-materials` 只为已有页面和测试保留；新的产品 contract 以后者不作为主入口。

扫描范围只包含：

```text
pc-tools/evidence/fixtures/wave_rover_*
```

每个材料组的 required materials 精确为五件套：

- `feedback_T1001.log`
- `odom_once.jsonl`
- `imu_once.jsonl`
- `battery_once.jsonl`
- `operator_hil_report` 或 `operator_hil_report.json`

`execution_pack_ready.json`、`review_ready.json`、`intake_ready.json` 等 execution pack / review decision 只能作为辅助上下文，不替代上述五件套。即使某个 group 显示 `complete file/material coverage`，也仍然只是 `software_proof/not_proven`，不得解释为 HIL pass、WAVE ROVER 上电、真实 UART 连通、轮向正确、反馈频率达标、IMU/battery 标定通过或 `delivery_success=true`。

## 验证

Evidence fixture 索引由工作站测试覆盖：

```bash
cd pc-tools/workstation && npm run test
```
