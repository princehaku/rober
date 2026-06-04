# Final: Runtime Material Runtime Hooks

## sprint_type

sprint_type: epic

## 收口结论

方向判断：**继续，但 O3/O7 产品进度不涨分**。

本轮把 O3/O7 的下一步从“人工 SSH 读旧 artifact”推进为“upper 8787 + PC workstation 都具备只读 scan proof refresh 合同”。Robot Software 和 Full-Stack 的本地验证通过，Hardware 复核安全边界通过。但现场 `192.168.1.11:8787` 尚未部署新 route：`GET /api/radar/status` 只暴露 `start/stop` controls，`POST /api/radar/scan-proof/refresh` 返回 HTTP 405。因此没有 fresh `/scan` runtime material，不能上调 O3/O7 产品完成度。

## OKR 进度

| Objective | 当前比例 | 本轮变化 | 说明 |
| --- | --- | --- | --- |
| O2：送垃圾任务 + 电梯 assisted delivery | 约 72% | 不变 | 本轮不处理图片 manifest；上一轮 blocker 仍成立。 |
| O3：建图、定位、Nav2 与固定路线 | 约 73% | 不变 | 本地 refresh 合同完成，但现场未部署，未形成 fresh `/scan`、map、AMCL 或 Nav2 material。 |
| O7：PC 运营调试平台 | 约 90% | 不变 | PC UI/API 已接 refresh 按钮和代理，但现场 upper 405，仍不是 operator runtime workflow 完成。 |
| O1：硬件协议可信底盘 | 约 95.5% | 不变 | 安全边界更清楚；没有 HIL、ACK 或新的 fresh feedback。 |
| O5：云中转控制面 | 约 84% | 不变 | 本轮未触达 production live material。 |
| O6：云端核心后端 | 约 82% | 不变 | 本轮未触达 production archive/runtime。 |
| O8：Epic 交付节奏与证据治理 | 约 43% | 从约 42% 小幅上调 | 连续 Epic 留档、owner notes、evidence type gate 和部署 blocker 收口完成。 |

## 未完成事项和风险

- 上位机 8787 未加载 `POST /api/radar/scan-proof/refresh`。
- 需要明确安全 reload/service 路径后同步 `upper_robot_api.py` 与 collector 文件，再重测 POST refresh 和 `/api/radar/scan-proof/latest`。
- 未证明 fresh `/scan` once/hz、`/lidar/raw_packet`、TF、SLAM `/map`、AMCL、Nav2 lifecycle、PC WASD、HIL、robot ACK 或 delivery success。

## 下一步

1. Robot Software：确认 `trashbot-upper-robot-api.service` 或实际 8787 启动命令，按安全 reload 路径部署新 route。
2. Full-Stack：重启 PC dev/runtime，确认 adapter version 为 `2026-06-04.scan-proof-refresh-v1`，再经 PC 同源触发 refresh。
3. Hardware：继续保持 LiDAR refresh 与底盘 `/dev/ttyS5` 隔离；HIL 只在现场看护、物理净空和急停路径满足后执行。
