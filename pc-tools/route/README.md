# pc-tools/route

`pc-tools/route/` 是 PC 工作站上的 fixed-route 调试工具目录。这里的工具只读消费 onboard 产出的 JSON 材料，不安装到 Orange Pi，不进入云端，也不访问硬件、serial/UART、Nav2 runtime、ROS graph 或网络外部服务。

## PC route debug console

`route_debug_web.py` 提供 `software_proof_docker_pc_route_debug_console_gate`：

```bash
python3 pc-tools/route/route_debug_web.py \
  --status-json /tmp/trashbot_fixed_route_status.json \
  --task-record /tmp/task_record.json \
  --elevator-route-reconciliation /tmp/elevator_route_evidence_reconciliation.json \
  --once-json
```

也可以启动本地只读 HTML/API：

```bash
python3 pc-tools/route/route_debug_web.py \
  --status-json /tmp/trashbot_fixed_route_status.json \
  --task-record-dir ~/.ros/trashbot_tasks \
  --elevator-route-reconciliation /tmp/elevator_route_evidence_reconciliation_summary.json \
  --host 127.0.0.1 \
  --port 8766
```

页面入口：

- `/` 或 `/index.html`：只读 HTML console。
- `/api/status` 或 `/api/summary`：同一份 JSON summary。

JSON summary schema 为 `trashbot.pc_route_debug_console.v1`，固定包含：

- `evidence_boundary=software_proof_docker_pc_route_debug_console_gate`
- `route_progress`
- `keyframe_preflight`
- `current_position`
- `current_checkpoint`
- `target`
- `match_status`
- `failure`
- `recent_task`
- `route_elevator_reconciliation`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

`--task-record` 用显式 task/task_record JSON。`--task-record-dir` 会按 fixed-route status 里的 `route_progress.evidence_ref` 或顶层 `evidence_ref` 查找同 run task record；找不到时保持 blocked/not_proven 摘要，而不是猜测任务成功。

`--elevator-route-reconciliation` 可选读取上一轮 `elevator_route_evidence_reconciliation` artifact 或 summary。支持的输入 schema 仅限 `trashbot.elevator_route_evidence_reconciliation.v1` 与 `trashbot.elevator_route_evidence_reconciliation_summary.v1`，且输入必须保持 `source=software_proof`、`evidence_boundary=software_proof_docker_elevator_route_evidence_reconciliation_gate`、`same_evidence_ref_required=true`、`delivery_success=false` 和 `primary_actions_enabled=false`。输出字段 `route_elevator_reconciliation.evidence_boundary=software_proof_docker_pc_route_elevator_console_integration_gate`，并以 `source_evidence_boundary` 保留输入复账边界；该字段只展示 safe `evidence_ref`、status/verdict、same-evidence-ref 状态、source states、missing/mismatch 摘要、operator next steps、boundary、`not_proven` 与 `safe_copy`；缺文件、坏 JSON、unsupported schema/boundary、unsafe copy、success/control claim 都会 fail closed。

## 证据边界

该 console 顶层仍只证明 PC/local/Docker 环境能把 fixed-route status JSON 与可选 task record 归一成可读 API/HTML，即 `software_proof_docker_pc_route_debug_console_gate`。嵌套 `route_elevator_reconciliation` 额外证明同一 console 可读入电梯路线复账摘要，即 `software_proof_docker_pc_route_elevator_console_integration_gate`。它不证明真实 Nav2/fixed-route、真实路线采集、关键帧实景验证、真实电梯、WAVE ROVER 运动、真实 serial/UART feedback、真实 HIL、dropoff/cancel completion 或 delivery success。

HTML 和 API 会隐藏本机完整路径、凭证、serial/UART、baudrate、WAVE ROVER 字样、ROS 控制 topic、traceback 与 checksum 类内容。页面是 read-only，不提供 Start、Confirm、Cancel、dropoff、collect 或 `/cmd_vel` 控制入口。
