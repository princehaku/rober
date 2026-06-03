# 2026.06.03 24-25 OKR Control State Refresh

sprint_type: micro

## 用户价值和产品北极星

用户价值是让后续迭代按真实证据更新 OKR，而不是把 PC/8787 软件入口、HTTP 200 或 vendor feedback material 误写成 HIL、ACK、真实 ROS topic 或完整上车闭环。

产品北极星仍是：普通手机用户把垃圾交给低成本小车后，小车可验证地送到垃圾站/垃圾桶点位，并能安全返回或等待下一次任务。

## OKR 映射和方向判断

- O1 方向判断：继续。当前只做保守小幅上调到约 96%，理由是 `/dev/ttyS5 @115200` 可写、manual forward/back/left/right HTTP 200、auto-stop observed、stop-only manual 后 `T=130/T=1001 observed`、PC/8787 材料入口已更完整；但 HIL、robot ACK 语义、真实 ROS `/odom`、`/imu/data`、`/battery`、真实 `/scan` 和左右转现场效果闭环仍 `not_proven`。
- O7 方向判断：继续。当前只做保守小幅上调到约 98.8%，理由是 PC direct manual 按钮、WASD、direct API path 和 camera 首屏不自动抢 offer 已进入 operator 软件入口口径；但 production path、真实 complete operator workflow、真实手控/Nav2 和完整任务闭环仍 `not_proven`。
- O5/O6 方向判断：继续但本轮不调整，仍约 96%。

## KR 拆解和更新

- O1 KR 已拆成软件协议入口、材料入口、现场底盘部分 observed、真实 ROS feedback topic、真实 LiDAR `/scan`、HIL/安全准入六段，便于后续逐项更新。
- O7 KR 已拆出 PC direct manual/WASD 软件入口和 production operator workflow 缺口，避免把 operator UI 入口当作真实控制完成。
- 本轮没有 KR 进入历史完成归档区；所有完成项仍是软件入口或材料入口，不是业务闭环结果。

## 本轮核心抓手

把 OKR 从“长段混合证据”改成“已完成软件/材料入口”和“未证明真实现场闭环”分层表达，并同步当前比例。

## 需要做什么

- 下一轮 O1 优先补真实 `/scan`、真实 `/odom`/`/imu/data`/`/battery`、ACK/HIL 和左右转现场效果闭环。
- 下一轮 O7 优先补 production path、真实 operator workflow、真实 manual/Nav2 与完整任务闭环。

## 优先级和验收口径

- P0：O1 真实硬件证据。验收必须包含现场看护、物理净空、人工急停、status/manual/stop/post-status 同源日志、ACK 或 `T=1001`、真实 ROS topic 或 HIL packet。
- P1：O7 真实 operator workflow。验收必须包含 production path、真实浏览器/网络链路、真实控制结果、失败提示和恢复路径。
- P2：O5/O6 真实生产材料。验收必须继续补真实公网、4G/SIM、DB/queue、OSS/CDN 和 phone/browser 材料。

## 对应责任 Engineer

- O1：`robot-hardware-engineer` 主责真实底盘/ACK/HIL；`robot-software-engineer` 主责 ROS topic/bridge 消费链路。
- O7：`full-stack-software-engineer` 主责 PC/operator/production path；必要时由 `robot-software-engineer` 补 ROS2 接口事实。
- `/scan` 和 Nav2：`robot-algorithm-engineer` 在 ROS2 runtime 可用后补 SLAM/Nav2 消费证据。

## 实际改动

- `OKR.md`
  - O1 当前进度从约 95.5% 保守调整到约 96%，并明确不越过 HIL 门槛。
  - O7 当前进度从约 98.6% 保守调整到约 98.8%，并明确不等于 production path 或真实 operator workflow。
  - 拆分 O1/O7 KR 文案，增加已完成软件/材料入口与未证明现场闭环的边界。
  - 更新 4.1 当前 OKR 快照和第 5 节当前最高优先级。
- `sprints/2026.06.03_24-25_okr-control-state-refresh/tech-done.md`
  - 创建本轮 micro sprint 留档。

## 验证结果

- `grep -n "O1\|O7\|95\|98\|WASD\|T=1001\|左右转\|safe_to_control" OKR.md | head -80`
  - 结果：通过，exit 0。
  - 关键输出包含：
    - `92:**当前进度：约 96% ... manual forward/back/left/right HTTP 200 ... T=130/T=1001 observed ... 左右转现场闭环 ... not_proven**`
    - `110:2026-06-03 24-25 保守调整 O1 当前比例 ... O1 从约 95.5% 小幅调到约 96% ...`
    - `116:- KR3（现场底盘材料部分 observed）... 左右转现场效果、robot ACK 语义和真实安全闭环仍未完成。`
    - `157:**当前进度：约 98.8% ... PC direct manual buttons/WASD/direct API path ready ...**`
    - `168:- KR6（PC 手控软件入口已完成）：PC direct manual 按钮与 WASD ... safe_to_control=false ...`
    - `179:| O1：硬件协议可信底盘 | 约 96% ...`
    - `189:| O7：PC 端运营调试平台 | 约 98.8% ...`
    - `191:补充：截至 2026.06.03_24-25 ... O1 当前口径调整为约 96% ... O7 当前口径调整为约 98.8% ...`
    - `221:1. **O1（约 96% ...）**：与 O5/O6 并列最低 ...`
    - `224:4. **O7（约 98.8% ...）** ...`
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.03_24-25_okr-control-state-refresh/tech-done.md`
  - 结果：通过，exit 0，无输出。

## 失败定位

无。两条验收命令均通过。

## 剩余风险

- O1：左右转现场效果、robot ACK 语义、HIL、真实 ROS `/odom`、`/imu/data`、`/battery`、真实 `/scan`、`safe_to_control=true` 和完整 delivery success 仍未证明。
- O7：PC direct manual/WASD 仍只是 operator 软件入口；production path、真实 complete operator workflow、真实手控/Nav2 和完整任务闭环仍未证明。
- 当前比例调整依赖已有 sprint 文档和本轮用户提供状态，没有新增工程验证或现场 HIL。

## 历史记录位置

本轮没有完成 KR 进入历史区。旧的已归档 Objective 仍以 `docs/process/okr_progress_log.md` 和 `OKR.md` 的“已归档 Objective”段为准。

## 需要创建或更新的 sprint 文档

- 已创建：`sprints/2026.06.03_24-25_okr-control-state-refresh/tech-done.md`
- 本 micro sprint 不需要 `pre_start.md` / `prd.md` / `tech-plan.md` / `side2side_check.md` / `final.md`。

## 2026-06-04 更正说明

最新 O1 硬件事实已经冲掉本 sprint 中“真实 `/scan` 仍 `not_proven`”这一当前状态口径。
该句在 2026-06-03 24-25 当时成立，但截至 `2026.06.04_00-01_o1-upper-ros2-bootstrap-continue`
已经更新为：首个上位机 ROS2 LiDAR `/scan` smoke observed。

可计入的新证据是 `/opt/ros/humble/setup.bash` exists、
`/root/rober/onboard/install/setup.bash` exists、`colcon build` 6 packages finished
[2min 8s]、`/scan` once、`/scan` hz 约 295-300 Hz、`/lidar/raw_packet` once、
`tf2_echo base_link laser_frame` observed，以及 smoke summary
`all_required_observations_observed=true`。

边界不变：本轮新证据只证明 LiDAR-only ROS2 smoke；没有发送底盘运动命令，只发送 LiDAR
`A5 60` start 和 stop sequence。HIL、SLAM/Nav2、长稳、production udev、ACK、
`/odom`、`/imu/data`、`/battery`、`safe_to_control=true` 和完整 delivery success
仍未证明。
