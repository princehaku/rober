# PC 扫地式建图向导设计

## 目标

PC 普通用户首屏需要把“建图”和“移动”串成一个像扫地机开荒一样的工作流：先确认现场安全，再启动建图，再低速让小车扫一圈，最后保存并刷新地图画面。

## 当前阶段边界

本阶段实现的是“受控扫图向导”，不是无人值守自动探索：

- 建图启动只走固定 PC 代理 `/api/robot-control/map/start`。
- 保存地图只走固定 PC 代理 `/api/robot-control/map/save`。
- 小车移动继续复用既有键盘连续手控 gate：低速、短时、按住才走、松开即停。
- 2026-06-25 16:06 起，扫图卡片自己的安全确认可直接作为键盘扫图的最小预检；不再要求先补 operator report、轮速非零或 LiDAR delta 材料才允许低速键盘扫图。
- 停止按钮始终可见，继续走固定 PC 代理 `/api/robot-control/base/stop`。
- 浏览器不允许传入串口、ROS 参数、任意 Robot API endpoint、`/cmd_vel` 或 Nav2 自动目标。
- 2026-06-25 起，PC 卡片新增“自动扫图准备”只读区：它读取 `safe_command_boundary.free_roam_autonomy`、policy 和逐项 gates，展示上车端 watchdog、LiDAR 避障、停止兜底、地图刷新和真车验证记录缺口；按钮固定显示“自动扫图（未开放）”且禁用，不绑定任何发车动作。
- 2026-06-25 21:07 起，`ros2_trashbot_nav.free_roam_autonomy` 提供上车端自动扫图策略内核：默认 fail-closed，只在现场安全确认、地图记录、停止兜底、雷达新鲜和障碍距离满足时输出低速前进；遇障碍原地换向，覆盖停滞时原地扫描，超时或未知区域达标时输出停止。
- 2026-06-25 21:18 起，`free_roam_autonomy_node` 已接 `/scan`、`/map`、runtime artifact 和 `/trashbot/stop` 兜底；默认 `enable_cmd_vel_publish=false` 且 `motion_hil_unlocked=false`，不会自动发 `/cmd_vel`，PC 自动扫图按钮仍锁定。
- 2026-06-25 21:24 起，上位机 `GET /api/free-roam/autonomy/latest` 和 `GET /api/status.free_roam_autonomy` 会只读 runtime artifact；PC summary 会把 `decision.gates` 显示成“自动扫图准备”门禁。该读回只改变所见即所得状态，不开放按钮、不触发 `/cmd_vel`。
- 2026-06-25 21:44 起，地图画面会叠加只读“自动扫图”runtime 标记，把上车端状态机最近判断直接放到地图上；缺机器人地图位姿时标记固定在角落且不代表坐标。
- 2026-06-25 23:25 起，普通首屏点击“开始扫地式建图”并且上位机确认地图记录启动后，PC 会自动进入“键盘已启用”状态；
  这一步只打开全局 W/A/S/D/方向键手控窗口，不发送 manual pulse、不调用 `/cmd_vel`。小车仍必须由 operator 按住方向键才会低速移动，松开或停止按钮会收口。
- 2026-06-25 23:45 起，PC summary 会从 `/api/free-roam/autonomy/latest` 的 runtime artifact 推导自动扫图 readiness：
  只有 `cmd_vel_publish_enabled=true` 且所有 `decision.gates` 加 PC 侧 `motion_hil_unlock` 门禁都为 `ready` 时，才把
  `safe_command_boundary.free_roam_autonomy` 显示为 `ready`。这只改变普通首屏“自动扫图准备”的所见即所得状态；PC 仍没有
  `/api/free-roam/autonomy/start` 固定代理，不会由这个按钮直接发车。

## 用户流程

1. 打开 PC 首屏，确认默认小车地址。
2. 查看地图、画面、雷达状态。
3. 在“扫地式建图”卡片勾选“人在旁边、周围安全、可以随时按停止”。
4. 点击“开始扫地式建图”，启动上位机建图 runtime。
5. 地图记录启动后键盘会自动启用；按住方向键或 W/A/S/D 低速移动。
6. 松开按键或点击“停止”收口。
7. 点击“保存当前地图”，再刷新地图画面检查 free cell、地图尺寸和可导航状态。

## 后续全自动探索要求

如果要升级成真正“像扫地机一样自己跑”的无人值守/半无人值守模式，需要新增上车端状态机，而不是把 PC 按钮直接变成无限运动：

- 实时 LiDAR/障碍物距离 gate：策略节点已接 `/scan` 并写 artifact，仍需真车低速 HIL。
- 最大运行时间、最大线速度、最大角速度限制：策略内核已有；最小电量限制仍待接底盘反馈。
- 自动 stop fallback 和 watchdog：策略节点已在 `stop_required=true` 时调用 `/trashbot/stop`，仍需真车响应时间 HIL。
- 探索覆盖策略：策略内核已有低速直行、遇障碍换向、覆盖停滞原地扫描；后续可升级边界沿墙或 frontier exploration。
- 地图质量实时指标：策略节点已消费 `/map` free cell 增量和 unknown 占比并写 artifact，仍需真实 map delta HIL。
- 完整验证记录：启动、每段速度命令、传感器状态、停止原因、保存地图结果。
- 真车低速验证通过后才能把 `safe_to_control` 或自动探索能力提升为真。

当前 PC 合同默认 `free_roam_autonomy=locked`。只有上车端 runtime artifact 明确报告双重解锁和逐项 gate ready 时，PC 才显示
`free_roam_autonomy=ready`；这仍不等于 PC 发车按钮已经接入，真正自动扫图 start/stop 还需要上车端提供固定 API 后再接。
