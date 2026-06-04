# Side-To-Side Check: Runtime Material Runtime Hooks

## sprint_type

sprint_type: epic

## 对照验收

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 上位机有只读 scan proof refresh 合同 | 本地通过，现场未部署 | `upper_robot_api.py` 本地测试 28 OK；live 8787 controls 仍只有 `start/stop`。 |
| PC 可以代理 refresh 工作流 | 本地通过，现场遇到 upper 405 | PC 99 tests/build/lint OK；现场 `POST /api/radar/scan-proof/refresh` 返回 405。 |
| 不触发底盘运动 | 通过 | Hardware SSH 只读检查未调用 base/manual、未发送运动命令，payload 固定 `safe_to_control=false`。 |
| OKR 是否可涨产品分 | 不涨 | 缺 live deployed refresh 和 fresh `/scan` material；本轮是 `software_guard + blocked_with_root_cause`。 |

## 需求满足度

- 满足：功能从“只有旧 artifact readback”推进到“本地 upper API + PC UI/API 都有 refresh 合同”。
- 未满足：现场 8787 尚未部署新 route，无法产出 fresh scan proof runtime material。

## 反思

本轮比继续重复 SSH readback 更进一步，因为补齐了 operator 可触发的 refresh 合同。但它仍没有跨过部署边界：未验证 reload 路径时不能杀未知 8787 进程，所以正确收口是 blocked，不是产品涨分。
