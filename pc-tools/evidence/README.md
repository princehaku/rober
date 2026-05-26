# pc-tools/evidence

`pc-tools/evidence/` 现在保留非 Python 证据资产，主要入口是：

```text
pc-tools/evidence/fixtures/
```

旧 Python evidence gate 和 Python 测试文件已移除。Evidence Tools 页面不再扫描 `.py`，而是由 Node API 递归索引 `fixtures/**/*.json`，按 fixture 一级目录生成资产分组。

## JSON Fixture 语义

JSON fixture 是脱敏软件证明材料或测试样例。fixture 可读只表示工作站能索引并解析本地 JSON，不表示真实现场材料齐全，也不表示 HIL、手机、云端、ROS2、Nav2、WAVE ROVER 或交付成功通过。

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

旧 Python gate 命令不再作为 `pc-tools` 验收入口。
