# OKR Strategy Reset: Real Control, SLAM, Elevator

## sprint_type

epic

## 背景

CEO 明确指出当前 OKR 与事实不符：

- PC 界面必须实际支持 WASD 前进、后退、左转、右转和停止，目前只证明软件入口，不能写成真实控车。
- 右侧雷达必须能一键开启/关闭，目前 PC 端只有状态/证据展示，没有 `POST /api/radar/start|stop`。
- 建图必须和 ROS2 联动，覆盖开启、重置、保存、加载、定位，而不是只有 `learn.launch.py` 和 `/trashbot/save_map`。
- 进出电梯需要 OpenCV 打标和识别，需要算法支持；现有 assisted delivery 停在合同、dry-run、fixture 和 ORB visual gate。
- 不能继续用 Micro Sprint 堆 `software_proof`，必须主动发现战略缺口，下一轮走跨 owner Epic。

## 用户价值和产品北极星

北极星保持不变：普通手机用户把垃圾交给低成本小车后，小车能沿固定路线送到垃圾站，必要时跨楼层进出电梯，并在异常时安全停止、请求人工协助和留下可复盘证据。

本轮用户价值是把 OKR 从“软件入口完成感”拉回“真实可用的现场闭环”：operator 必须能用 PC 真实控车、开关雷达、建图定位；算法必须开始承担电梯识别，而不是让 dry-run 冒充跨楼层能力。

## 本轮事实输入

| Owner | 已确认事实 | 不能外推 |
| --- | --- | --- |
| Full-stack | PC 已有 WASD/按钮软件入口，触发同源 API 再代理到 8787 `/api/base/manual|stop`；测试证明 UI/API 映射和 mock/fetch 链路 | 不证明真实小车能被 PC 控制，不证明 8787 motion、物理前后左右/stop、ACK/T=1001 或急停/operator report |
| Hardware | `/dev/ttyS5 @115200` 是当前 Orange Pi 底盘可写入口；`T=1` 是 vendor `CMD_SPEED_CTRL`；`T=130 -> T=1001` 是 vendor feedback material；LiDAR 有 `/scan` 首个 smoke | 不证明底盘 HIL、长期设备名、robot ACK、ROS `/cmd_vel` 接入、ROS `/odom`/`/imu/data`/`/battery`、LiDAR 长稳或一键开关 |
| Robot Software | `learn.launch.py` 有 SLAM Toolbox 入口，`map_recorder` 只有 `/trashbot/save_map`，8787 路由只有 camera/radar/base | 不证明 `/map`、reset/load map、PC/upper map API、AMCL 定位恢复、Nav2 消费 `/scan` 或路径执行 |
| Algorithm | 电梯 assisted delivery 停在合同和 dry-run；visual gate 是 ORB keyframe 匹配；`TrashDetector` 不是电梯识别 | 不证明 OpenCV 门线/轿厢/楼层语义识别，不证明真实训练/标注质量，不证明实景进出电梯 |

## 阻塞和打回原则

- O2/O3 不能继续放在历史归档区，必须回到当前推进区。
- O2/O3 的“软件完成 ~99%”不符合事实，按 70-75% 区间打回。
- O7 不能把 WASD UI/PC proxy ready 写成 PC 实际 WASD 控车完成，按 85-90% 区间打回。
- O1 若包含 SLAM/Nav2 预期，首个 LiDAR `/scan` smoke 不足以支撑 97%，打回到约 95%。
- O5/O6 保持不变，但下一轮不再抢占真实操控/建图/电梯 Epic。

## 本轮范围

允许修改：

- `OKR.md`
- 本 sprint 的 `pre_start.md`
- 本 sprint 的 `prd.md`
- 本 sprint 的 `tech-plan.md`
- 本 sprint 的 `tech-done.md`
- `docs/process/okr_progress_log.md`

禁止触碰：

- `pc-tools/**`
- `onboard/**`
- `cloud-relay/**`
- `.codex/**`
- `docs/interfaces/**`
- 除 `docs/process/okr_progress_log.md` 外的 `docs/**`

## 预期输出

- 重写当前 OKR：O2/O3 回当前推进区，O1/O2/O3/O7 打回百分比，新增真实 KR。
- 明确下一轮必须是 Epic，不再用 Micro sprint 堆 `software_proof`。
- 记录打回原因、证据来源、owner 切分、验收口径和剩余风险。
