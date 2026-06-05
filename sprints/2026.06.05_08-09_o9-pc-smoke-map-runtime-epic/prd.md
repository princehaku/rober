# PRD: O9 PC Smoke + Map Runtime Epic

## sprint_type

sprint_type: epic

## 产品问题

O9 的价值不是继续证明“接口能读状态”，而是把用户可理解的运营调试链路推进到真实 runtime material：

- PC 端必须能从本机 same-origin API 触发上位机 8787 refresh，这样普通运营人员不用 SSH 也能看到 fresh scan proof 是否成立。
- 机器人侧必须开始形成 SLAM `/map` lifecycle material，这样后续固定路线、定位恢复、PC 地图控制和送垃圾任务才有实际地图基础。

上一轮已证明字段合同和 root cause，但还没有完成 PC live smoke 和 `/map` proof。本轮 PRD 要求直接补这两个功能证据。

## 用户价值

| 用户/角色 | 当前痛点 | 本轮要改善的可见结果 |
| --- | --- | --- |
| 普通用户背后的运营人员 | PC 面板无法通过本机 API 证明上位机 refresh 真的跑通。 | `8788 -> 8787` same-origin refresh curl 成功，失败时能看到明确 blocker。 |
| 机器人调试人员 | 远端只知道 ROS graph 空，缺少 map lifecycle artifact。 | 形成 `/map` once、map artifact、metadata、latest JSON 和 `/api/map/proof/latest` readback。 |
| CEO/Product | O9 约 18%，连续材料断点容易被 status/readback 稀释。 | 两条并行抓手都产出 runtime material 或更窄 root cause，避免 Micro-only 回退。 |

## 范围

### In Scope

- 修 PC `npm run api` 在当前 WSL/PC 环境的 live smoke 启动问题。
- 首选尝试 `TMPDIR=/tmp` 规避 `tsx_ipc_pipe_enotsup`；若不可行，允许 Full-stack 在不扩大 UI 面的前提下替换启动方式或补 smoke wrapper。
- 通过 PC 本机 8788 调上位机 8787：`POST /api/o7/direct-upper/radar/scan-proof/refresh`，并读取 refresh/latest 结果。
- 在 `root@192.168.1.11` 上执行 no-motion LiDAR+SLAM `/map` lifecycle proof。
- 生成或读取 map artifact、metadata、`runtime/map_lifecycle_latest.json`。
- 通过 `/api/map/proof/latest` 完成 readback。
- 更新后续 `tech-done.md`、`side2side_check.md`、`final.md` 时必须保留证据边界。

### Out of Scope

- 不做 PC WASD 或任何底盘运动控制。
- 不做 stop-first HIL、低速 pulse 或 WAVE ROVER ACK。
- 不做真实/受控电梯图片采集。
- 不宣称 continuous radar ready、AMCL ready、Nav2 ready 或 fixed-route real run。
- 本阶段不改 `OKR.md`；只有收口材料满足边界后再由 Product 更新。

## 成功标准

### Full-stack 成功标准

最低成功：

- `TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api` 或等价启动方式能让本机 8788 API live smoke 启动。
- `curl -fsS -X POST http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/refresh` 成功返回上位机 refresh 结果。
- evidence 中能看见 fresh proof、hz、TF、`runtime_summary_fallback_used`、same-origin 来源、`continuous_scan_status=not_proven` 或明确 blocker。

失败也可收口为有价值材料，但必须比上一轮更窄：

- 明确 `TMPDIR=/tmp` 是否无效。
- 给出 `npm run api`/`tsx`/Node/WSL 启动失败日志。
- 给出替代启动方式的下一步 patch 入口。

### Robot Software + Algorithm 成功标准

最低成功：

- 通过 SSH 到 `root@192.168.1.11` 执行 no-motion runtime proof。
- 采到 `/map` once。
- 产出 map artifact 和 metadata。
- 写入 `runtime/map_lifecycle_latest.json`。
- `curl -fsS http://127.0.0.1:8787/api/map/proof/latest` 能 readback 最新 proof。
- proof 明确包含 `safe_to_control=false`，且没有 `/cmd_vel`、没有 base motion。

失败也可收口为有价值材料，但必须比上一轮更窄：

- 明确是 LiDAR 不在线、SLAM 未安装、launch 缺失、map saver 缺失、API route 缺失、文件权限、ROS_DOMAIN_ID、topic remap、TF 或其他具体 root cause。
- 给出 `ros2 topic list`、`ros2 topic echo --once /scan`、`ros2 topic echo --once /map`、map artifact 目录和 API curl 日志。

## 验收边界

可计 evidence type：

- `robot_runtime_material`：真实上位机 runtime 下的 scan/map/proof artifact。
- `software_guard`：PC smoke 和 API 合同护栏。
- `blocked_with_root_cause`：失败但 root cause 更具体，且有日志证据。

不可越界：

- 不把 fresh scan proof 外推为 continuous radar ready。
- 不把 `/map` once 外推为可导航地图、AMCL/Nav2 ready 或固定路线可跑。
- 不把 `T=1001`、vendor feedback 或任何 non-motion material 写成底盘 ACK/HIL。
- 不把 `safe_to_control=false` 的材料写成可控车状态。

## Product 收口口径

收口时 Product 只看证据，不看努力：

- 两条并行抓手都完成，才考虑 O9/O3/O7 的窄幅证据更新。
- 仅 Full-stack 完成，则最多更新 O7/O8 和 O9 局部入口，不得声称 map/SLAM 进展。
- 仅 `/map` proof 完成，则最多更新 O3/O9 和 O8，不得声称 PC operator workflow 完整。
- 两条都失败但 root cause 变窄，则只更新 O8 blocker 治理，不上调产品 Objective。
