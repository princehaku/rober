# PRD: Runtime Material Deploy Refresh

## 背景

O3/O7 当前卡点已经不是“是否有 refresh 合同”。上一轮已在本地完成 upper API route、PC 同源代理和 UI 入口，但现场上位机 `192.168.1.11:8787` 对 `POST /api/radar/scan-proof/refresh` 返回 405。只要 route 没有部署到真实 runtime，PC operator 看到的按钮仍只是 software guard，不能证明雷达/ROS2 正在产出 fresh `/scan` material。

## 用户价值

现场 operator 不应靠 SSH 登录和猜测旧 artifact 判断机器人是否具备建图/定位前置条件。普通用户最终需要的是可送达的固定路线任务；对工程侧来说，第一步是 PC/8787 能用一个只读按钮刷新雷达 scan proof，并把结果归类为 fresh material、ROS2 topic blocker 或 deployment blocker。

## OKR 映射和方向判断

| Objective | 当前判断 | 本轮关系 | 涨分边界 |
| --- | --- | --- | --- |
| O3：建图、定位、Nav2 与固定路线 | 调整，继续主线第一优先级 | 本轮只打通 fresh `/scan` proof，是 SLAM `/map`、AMCL 和 Nav2 前置材料 | 只有 live deployed route + fresh `/scan` once/hz artifact 可小幅支撑 O3；route 部署但无 topic 不涨产品分 |
| O7：PC 运营调试平台 | 继续，必须变成真实 operator workflow | PC 同源触发 refresh 并展示 fresh/stale/blocker | 只有 PC 经真实 8787 触发并回读 fresh artifact，才可支撑 O7；本地按钮/测试不涨 |
| O2：送垃圾任务 + 电梯 assisted delivery | 调整，保留风险 | 本轮不做图片 manifest，避免范围漂移 | 无真实/受控 manifest eval，不涨 |
| O1：硬件协议可信底盘 | 继续，HIL 仍是硬门槛 | 本轮仅保留安全边界，不做运动 | 无低速 pulse、ACK/T=1001 同场、ROS feedback topics，不涨 |
| O8：Epic 交付节奏与证据治理 | 继续 | 本轮继续按 Epic、Evidence Type Gate、最近 2 轮 blocker scan 留档 | 只有完整链路和收口复核可小幅支撑治理，不证明产品能力 |

方向判断：**继续，但收窄到 O3/O7 deploy refresh**。本轮不替换北极星，不暂停 O2/O1，只是把下一步执行顺序调整为“先部署 refresh route 拿 fresh scan proof，再推进 map/localize/Nav2、图片 manifest 和 HIL”。

## KR 拆解

### KR-O3/O7-Scan-Proof-Refresh-Deploy

- 用户价值：operator 能在真实 PC/8787 runtime 上刷新雷达 scan proof，不再依赖旧 artifact 或 SSH 手工判断。
- Owner：Robot Software Engineer 主责，User Touchpoint Full-Stack Engineer 配合，Hardware Infra Engineer 只读安全复核。
- 最小实现路径：
  1. 只读确认上位机 8787 进程、service、部署目录、reload/restart 命令和回滚路径。
  2. 同步本地已验证的 `upper_robot_api.py` refresh route 与 scan proof collector 到上位机。
  3. 安全 reload/restart 后验证 `POST /api/radar/scan-proof/refresh`、`GET /api/radar/scan-proof/latest` 和 PC 同源 refresh。
- 验收证据：live HTTP 响应、artifact path、fresh timestamp、topic summary、PC 同源触发日志、`safe_to_control=false`、`robot_control_executed=false`、部署/reload 记录。
- 证据边界：只证明 refresh route 和 scan proof；不证明 SLAM map、AMCL、Nav2、PC WASD、底盘 HIL 或 delivery success。

### 下一步保留项，不纳入本轮完成

- KR-O2-Real-Image-Manifest-Eval：继续等待真实或受控电梯图片 manifest。
- KR-O1/O7-Stop-First-HIL：继续等待现场看护、物理净空、急停路径和低速 pulse 条件。
- KR-O3-SLAM-Map-Lifecycle / KR-O3-Localization-Reset / KR-O3-Nav2-Consumption：等 fresh `/scan` proof 后再推进。

## 需求

1. 文档与派单必须明确本轮 deploy refresh 的安全边界：只读 LiDAR/ROS2 scan proof，不触碰底盘运动。
2. IC 需要先确认 reload/service 路径，不能盲目 kill 未知进程。
3. 部署后必须用 live `POST /api/radar/scan-proof/refresh` 复测，HTTP 405 必须消失或被定位为明确 root cause。
4. 必须回读 `/api/radar/scan-proof/latest`，证明 artifact 与本次 refresh 对齐。
5. 必须通过 PC 同源入口触发或写清 PC runtime 的具体 blocker。
6. `tech-done.md`、`side2side_check.md`、`final.md` 等收口文档必须等 IC 返回后再更新。

## 非目标

- 不新增产品 UI 需求，不把按钮文案优化当业务结果。
- 不执行底盘运动、手控、急停演练或 HIL。
- 不处理 O2 图片采集，不补 OpenCV eval。
- 不处理 O5/O6 生产云、4G、DB/queue、OSS/CDN 或 token。
- 不在没有 fresh runtime material 时更新 OKR 完成度。

## 优先级

1. P0：确认安全 reload/service 路径，并保留命令、进程、端口和回滚材料。
2. P0：部署 upper refresh route，使 live `POST /api/radar/scan-proof/refresh` 不再返回 405。
3. P0：取得 fresh `/api/radar/scan-proof/latest` artifact 或明确 ROS2 topic blocker。
4. P1：PC 同源触发 refresh，生成 operator 可读结果和同一 `evidence_ref`。
5. P2：记录 O2 图片 manifest 和 O1 HIL 的下一步风险，不扩大本轮执行。

## 验收

- `POST http://192.168.1.11:8787/api/radar/scan-proof/refresh` 返回 2xx/可解释 JSON，或给出非 405 的明确 blocker。
- `GET http://192.168.1.11:8787/api/radar/scan-proof/latest` 返回本轮 fresh artifact，包含 timestamp、freshness、topic summary 和 blockers。
- PC 同源 `POST /api/o7/direct-upper/radar/scan-proof/refresh` 能触发同一 upper route，或写清 adapter/runtime blocker。
- 所有材料均标注 evidence type，且保留 `safe_to_control=false`。
- 若仅部署成功但 `/scan` 不 fresh，O3/O7 不涨产品完成度。

## 风险

- 如果 service 路径未知，本轮可能只能把 root cause 从 HTTP 405 收敛为 reload/deploy 权限问题。
- 如果 `/scan` topic 不存在，本轮只能证明 route 部署，不证明建图/定位/Nav2 前置条件完成。
- 如果 PC runtime 未重启或 adapter 未更新，本轮只能涨 upper runtime 证据，不能涨 O7 operator workflow。
