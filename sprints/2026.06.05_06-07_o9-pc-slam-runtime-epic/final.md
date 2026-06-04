# Final: O9 PC + SLAM Runtime Epic

## sprint_type

sprint_type: epic

## 收口结论

本轮继续执行 O9 窄 Epic，没有回到 Micro-only status/readback。

- PC direct-upper scan-proof refresh 已能在 API/UI/test/docs 中表达 fresh proof 的 hz、TF、runtime fallback 和 continuous not_proven 边界。
- PC 本机 live smoke 未通过，root cause 是 `tsx` 在当前 WSL 环境监听 Windows temp pipe 报 `ENOTSUP`，导致 8788 API 未启动。
- Robot Software 通过上位机 SSH 把 O3/O9 root cause 收敛：现场 ROS graph 只有 `/parameter_events`、`/rosout`，没有常驻 `/scan`、`/map`、SLAM、Nav2；map proof artifact 缺失。

## OKR 进度判断

| Objective | 本轮判断 |
| --- | --- |
| O1 | 保持约 95.5%；没有 HIL、ACK、ROS feedback topics 或 `safe_to_control=true`。 |
| O2 | 保持约 72%；没有真实/受控电梯图片 manifest 或 field eval。 |
| O3 | 保持约 75%；root cause 更清楚，但没有 continuous radar 或 SLAM `/map` material。 |
| O5 | 保持约 84%；未触达 production live material。 |
| O6 | 保持约 82%；未触达 production archive/query/inference。 |
| O7 | 保持约 91%；PC 软件护栏增强，但 live smoke blocked。 |
| O8 | 约 46% -> 约 47%；本轮完成超时处理、重派、证据收口和 blocker 归档。 |
| O9 | 保持约 18%；没有新增 field/HIL/continuous radar/SLAM map/user acceptance material。 |

## 证据边界

新增可计证据：

- `software_guard`：PC API/UI/test/docs 已展示 fresh proof 与 continuous not_proven 的分离边界。
- `blocked_with_root_cause`：PC live smoke blocked at `tsx_ipc_pipe_enotsup`。
- `blocked_with_root_cause`：远端 ROS graph 无常驻 LiDAR/SLAM runtime，map proof artifact missing。

不可越界：

- 不证明 PC 按钮 live same-origin refresh 已成功。
- 不证明 continuous radar ready、SLAM `/map`、AMCL、Nav2、PC WASD、WAVE ROVER ACK、HIL、真实电梯识别、真实手机用户验收或真实送达。

## 下一步

1. Full-stack：先修 PC API smoke 启动环境，建议设置 Linux-side `TMPDIR` 或替换 `tsx` 启动方式，再复跑 8788 -> 8787 same-origin refresh。
2. Robot Software + Algorithm：执行 no-motion LiDAR+SLAM runtime proof，目标是 `/map` once、map artifact、metadata、`runtime/map_lifecycle_latest.json` 和 `/api/map/proof/latest` readback。
3. Product：继续把 O9 作为最低优先级，不允许用更多状态/readback替代真实材料。
