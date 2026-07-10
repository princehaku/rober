# Algorithm Worker Report - Task A

运行时间：2026-07-10 02:18:56 CST

## 自主能力目标和本轮抓手

目标是把 O5 `trashbot.cloud_command_terminal_result.v1` 软件终态结果桥接成 O6/O7 既有 `trashbot.delivery_result_evidence.v1`，让同一 `task_id` 的 terminal result 可以被 field evidence manifest 安全消费。本轮抓手是 `onboard/scripts/field_route_evidence_manifest.py` 的只读 manifest 生成链路，不启动 ROS2/Nav2，不发布 `/cmd_vel`，不声明真实送达成功。

## 改动文件和接口影响

- `onboard/scripts/field_route_evidence_manifest.py`
  - 新增 `--cloud-terminal-result-json` 可选输入。
  - 当 `--delivery-result-json` 缺失且 cloud terminal result 存在时，转换输出 `delivery_result_evidence`，并同步写入 manifest 顶层与 `field_motion_evidence_packet.delivery_result_evidence`。
  - `source=cloud_command_terminal_result`，`source_schema=trashbot.cloud_command_terminal_result.v1`。
  - `command_id`、`task_record_ref`、`evidence_ref` 只输出短 safe ref；路径、URL、token、raw/base64、credential 会 fail-closed。
  - `delivery_success`、`safe_to_control`、`primary_actions_enabled`、`robot_control_executed` 始终为 `false`。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 新增 cloud terminal result fixture helper。
  - 覆盖 ready、schema mismatch、dangerous true/unsafe refs fail-closed。
- `docs/navigation/field_route_evidence_manifest.md`
  - 记录新参数、两输入同时提供时 `--delivery-result-json` 优先、转换字段、安全边界和示例命令。

## 实现内容

- 新增 O5 schema 常量 `trashbot.cloud_command_terminal_result.v1`。
- 新增 cloud terminal 完成态判断：`terminal_result_type` 必须是 `delivery_terminal` 或 `dropoff_terminal`，且 `result_code` 或 `task_terminal_state` 表达 completed/succeeded/dropoff completed，才允许 `delivery_result_claimed=true`。
- 新增 `completed_at` 时区归一化，输出 UTC `completed_at_utc`。
- 新增 safe ref 摘要：拒绝路径、URL、反斜杠、token/raw/base64/credential 文本；blocked 摘要只输出字段名与计数，不回显原始敏感值。
- 保持旧行为：没有 `--delivery-result-json` 且没有 `--cloud-terminal-result-json` 时，仍输出 `delivery_result_json_missing` blocked 摘要；两者同时存在时仍优先旧的 `--delivery-result-json`。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

结果片段：

```text
Ran 53 tests in 0.272s

OK
```

## 失败定位

本轮未出现失败；没有需要二次修复的测试或编译错误。

## 数据、样本或调试输出变化

- 新增测试 fixture `write_cloud_terminal_result_json`。
- ready 用例验证 cloud terminal result 会生成：
  - `delivery_result_evidence.source=cloud_command_terminal_result`
  - `source_schema=trashbot.cloud_command_terminal_result.v1`
  - `status=ready_not_delivery_proof`
  - `delivery_result_claimed=true`
  - `delivery_success=false`
- unsafe 用例验证路径、URL、raw/base64 和 dangerous true 不会回显到 manifest。

## 剩余风险和下一步

- 本轮是 `software_proof`：不证明真实 production cloud、真实 4G/SIM、真实 OSS/CDN、真实 live Nav2 route execution、真实 robot motion、真实 operator video 或真实 delivery success。
- O6/O7 读回侧需要继续由对应 owner 验证 `source_schema=trashbot.cloud_command_terminal_result.v1` 在 archive detail、consumer detail 和 `include=delivery_result_evidence` 中保留。
