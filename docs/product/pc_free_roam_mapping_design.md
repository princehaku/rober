# PC 扫地式建图向导设计

## 目标

PC 普通用户首屏需要把“建图”和“移动”串成一个像扫地机开荒一样的工作流：先确认现场安全，再启动建图，再低速让小车扫一圈，最后保存并刷新地图画面。

## 当前阶段边界

本阶段实现的是“受控扫图向导”，不是无人值守自动探索：

- 建图启动只走固定 PC 代理 `/api/robot-control/map/start`。
- 保存地图只走固定 PC 代理 `/api/robot-control/map/save`。
- 小车移动有两条入口：键盘连续手控仍是低速、短时、按住才走、松开即停；自动扫图 start 在现场安全确认后只通过上车状态机参数服务打开受限 free-roam 双锁。
- 2026-06-25 16:06 起，扫图卡片自己的安全确认可直接作为键盘扫图的最小预检；不再要求先补 operator report、轮速非零或 LiDAR delta 材料才允许低速键盘扫图。
- 停止按钮始终可见，继续走固定 PC 代理 `/api/robot-control/base/stop`。
- 浏览器不允许传入串口、ROS 参数、任意 Robot API endpoint、`/cmd_vel` 或 Nav2 自动目标。
- 2026-06-25 起，PC 卡片新增“自动扫图准备”只读区：它读取 `safe_command_boundary.free_roam_autonomy`、policy 和逐项 gates，展示上车端 watchdog、LiDAR 避障、停止兜底、地图刷新和真车验证记录缺口；按钮固定显示“自动扫图（未开放）”且禁用，不绑定任何发车动作。
- 2026-06-25 21:07 起，`ros2_trashbot_nav.free_roam_autonomy` 提供上车端自动扫图策略内核：默认 fail-closed，只在现场安全确认、地图记录和停止兜底满足时允许进入低速自移动；相机首帧和雷达新鲜度进入 `mapping_readiness`，用于判断本轮是否可建图，不再阻止低速自由移动。遇障碍原地换向，覆盖停滞时原地扫描，超时或未知区域达标时输出停止。
- 2026-06-25 21:18 起，`free_roam_autonomy_node` 已接 `/scan`、`/map`、runtime artifact 和 `/trashbot/stop` 兜底；默认 `enable_cmd_vel_publish=false` 且 `motion_hil_unlocked=false`，不会自动发 `/cmd_vel`，PC 自动扫图按钮仍锁定。
- 2026-06-25 21:24 起，上位机 `GET /api/free-roam/autonomy/latest` 和 `GET /api/status.free_roam_autonomy` 会只读 runtime artifact；PC summary 会把 `decision.gates` 显示成“自动扫图准备”门禁。该读回只改变所见即所得状态，不开放按钮、不触发 `/cmd_vel`。
- 2026-06-26 23:59 起，上位机 free-roam latest/status 会把已加载的 `trashbot.free_roam_autonomy.runtime.v1` artifact 明确标为 `free_roam_state_machine_observed=true` 与 `ros2_runtime_proven=true`，PC summary 同步显示 `readback_summary.free_roam.state_machine_observed/ros2_runtime_proven`。这只说明上车端 free-roam 状态机已经在写 runtime，不等于已解锁运动；`artifact_only`、`cmd_vel_publish_enabled`、`publishes_cmd_vel` 仍决定当前是否真的发布运动。
- 2026-06-25 21:44 起，地图画面会叠加只读“自动扫图”runtime 标记，把上车端状态机最近判断直接放到地图上；缺机器人地图位姿时标记固定在角落且不代表坐标。
- 2026-06-25 23:25 起，普通首屏点击“开始扫地式建图”并且上位机确认地图记录启动后，PC 会自动进入“键盘已启用”状态；
  这一步只打开全局 W/A/S/D/方向键手控窗口，不发送 manual pulse、不调用 `/cmd_vel`。小车仍必须由 operator 按住方向键才会低速移动，松开或停止按钮会收口。
- 2026-06-25 23:45 起，PC summary 会从 `/api/free-roam/autonomy/latest` 的 runtime artifact 推导自动扫图 readiness：
  只有 `cmd_vel_publish_enabled=true` 且所有 `decision.gates` 加 PC 侧 `motion_hil_unlock` 门禁都为 `ready` 时，才把
  `safe_command_boundary.free_roam_autonomy` 显示为 `ready`。这只改变普通首屏“自动扫图准备”的所见即所得状态。
- 2026-06-25 23:52 起，上位机新增固定 `POST /api/free-roam/autonomy/start|stop`，PC 新增对应固定代理
  `/api/robot-control/free-roam/autonomy/start|stop`。start 必须带 `confirm_operator_safety=true`，`confirm_mapping_active` 只表示本轮是否尝试建图；
  2026-06-26 21:35 起，即使相机首帧或雷达 proof 不 ready，只要确认项满足也可设置 `free_roam_autonomy_node` 的
  `operator_confirmed/external_stop_requested` 状态机参数，并在回包中标明
  `free_move_ready=true`、`motion_without_radar_allowed=true`、`mapping_readiness.ready=false`。2026-06-26 23:22 起，上位机 API
  对直接调用也二次收紧：`confirm_mapping_active=true` 只是请求，只有 `mapping_readiness.ready=true` 时才真正写
  `mapping_active=true`；否则仍允许低速自由移动，但回包必须显示 `mapping_active_requested=true`、`mapping_active_applied=false`。
  HTTP start 只允许通过固定状态机参数序列写 `motion_hil_unlocked=true` 与 `enable_cmd_vel_publish=true`，
  不直接发布 `/cmd_vel`，也不允许 PC 或浏览器改写 `cmd_vel_topic`。stop 不要求相机/雷达 ready，只把
  `enable_cmd_vel_publish/motion_hil_unlocked` 收回为 false，并设置 `external_stop_requested=true`。
- 2026-06-26 23:40 起，上位机 free-roam start/stop 写 ROS 参数改为一次固定 `ros2 param load`
  临时 YAML；如果 `/free_roam_autonomy` 参数服务因重复 launch、ROS graph 抖动或 node 无响应而卡住，
  API 必须按专用超时返回结构化失败，不能让 PC 普通首屏一直等待。该行为不放宽安全确认，
  不新增任意 ROS 参数入口。
- 2026-06-26 23:55 起，PC Node 不再把 free-roam start/stop 的 `command_result` 压扁成
  `mode/executed/ok`：普通首屏会显示 `ros2_param_load` 是否一次写入、写入参数数量、是否保留
  `cmd_vel_topic` 未改，以及 `mapping_active_applied`。这样 operator 能看到“状态机参数已写入”
  还是“只请求了但未生效”，而不需要打开高级诊断看 raw JSON。
- 2026-06-26 01:05 起，PC 在自动扫图 start/stop 请求后把结果同步到普通首屏地图和“扫图状态”行：
  start 成功显示 `自动扫图已启动` / `自动扫图状态机已启动`，stop 成功显示停止请求已发送，失败则明确显示未证明启动或停止。
  这些反馈只来自固定 PC 代理返回值，不外推成真实自主运动成功，也不新增 `/cmd_vel`、manual 或 Nav2 调用。
- 2026-06-26 01:25 起，自动扫图 start 成功后，“下一步”流程按钮不再回到人工键盘扫图，而是显示
  `下一步：监看或停止自动扫图` 并聚焦 `停止自动扫图`；stop 请求转发后再回到 `刷新扫图画面/保存当前地图`。
  这只改变焦点和文案，不自动停止、不自动保存，也不发送 manual、Nav2、delivery 或 `/cmd_vel`。
- 2026-06-26 12:00 起，自动扫图 stop 请求转发成功后，PC 会清掉启动前或运行中旧地图画面的 fresh 标记，
  地图 marker 显示 `自动扫图已停止，待刷新`，下一步聚焦 `刷新扫图画面`；只有停止后再次读到地图 preview，
  才显示 `自动扫图已停止，可保存` 并允许保存。这样不会把自动扫图运行前的地图画面当作停止后的覆盖结果。
- 2026-06-26 01:30 起，人工键盘/屏幕方向键扫图松开并完成 stop 收口后，地图上的扫图流程 marker 会保留上次方向、
  停止原因和轮速结论，例如 `已停可保存：前进，轮速非零`。这只帮助 operator 复核刚才的连续手控闭环，
  不新增请求、不自动保存，也不发送 manual、Nav2、delivery 或 `/cmd_vel`。
- 2026-06-26 01:35 起，自动扫图 start 成功后，PC 会立即做一次只读雷达 proof refresh 和地图 preview refresh，
  让“地图和雷达监看中”变成可见证据更新；该刷新不发送底盘 manual、不执行 Nav2、不提交送达，也不发布 `/cmd_vel`。
- 2026-06-26 12:15 起，如果自动扫图 start 成功后的只读雷达 proof refresh 失败，普通首屏扫图状态和地图扫图 marker
  会显示 `自动扫图已启动，雷达刷新失败：<原因>`，不再继续写成“地图和雷达监看中”。该状态只消费固定
  `/api/robot-control/radar/scan-proof/refresh` 回包，不自动重试、不停止自动扫图、不发送 manual、Nav2、delivery 或 `/cmd_vel`。
- 2026-06-26 12:30 起，如果自动扫图 start 成功后的只读地图 preview refresh 失败，普通首屏扫图状态和地图扫图 marker
  会显示 `自动扫图已启动，地图刷新失败：<原因>`，不再继续写成“地图监看中”。该状态只消费固定
  `/api/robot-control/map/preview` 回包，不自动重试、不停止自动扫图、不保存地图、不发送 manual、Nav2、delivery 或 `/cmd_vel`。
- 2026-06-26 02:05 起，点击“保存当前地图”并且固定 `/api/robot-control/map/save` 转发成功后，PC 会自动再读一次
  `/api/robot-control/map/preview`，并把首屏提示改成“地图已保存，已自动刷新最新画面”。这一步仍是只读地图预览刷新，
  不发送底盘 manual、不执行 Nav2、不提交送达，也不发布 `/cmd_vel`。
- 2026-06-26 03:05 起，保存后自动刷新成功也会同步到“扫图覆盖”提示：如果保存后的只读地图 preview 已成功转发，
  覆盖 guidance 会显示“地图已保存，地图画面已自动刷新；现在检查覆盖效果”，避免 operator 误以为保存后还必须手动刷新一次。
- 2026-06-26 03:20 起，保存后“扫地式建图”步骤条也按收口状态展示：低速扫图显示已收口，停止显示已停止并保存，
  保存地图显示已保存且地图画面已自动刷新，避免 operator 在保存后继续被引导去手控移动。
- 2026-06-26 04:05 起，保存成功但保存后的只读地图 preview 还没返回时，PC 首屏会显示“保存后刷新中”：
  扫图状态、地图画面新鲜度、地图 marker、下一步和覆盖提示都会说明正在自动刷新最新画面。该中间态只等待
  `/api/robot-control/map/preview`，不再次保存、不发送 manual、Nav2、delivery、stop 或 `/cmd_vel`。
- 2026-06-26 11:45 起，如果 `保存当前地图` 已成功但保存后的只读 `/api/robot-control/map/preview` 返回失败，
  普通首屏会明确显示“地图已保存，但最新画面刷新失败”，地图 marker 显示 `保存后画面刷新失败：<原因>`，
  覆盖提示进入失败态，下一步聚焦 `刷新扫图画面`。这样保存动作成功不会被误读成保存后的新图已经可见；
  该失败态只来自只读 preview 回包，不重试、不再次保存、不发送 manual、Nav2、delivery、stop 或 `/cmd_vel`。
- 2026-06-26 04:29 起，地图记录中手动点击“刷新扫图画面”且只读 map preview 尚未返回时，PC 会把新键盘/屏幕方向移动锁住，
  提示“等待地图刷新”；如果已经按住方向键，则不硬切当前移动，松开仍按原 stop 流程收口。这保证扫地式建图继续按最新地图画面推进。
- 2026-06-26 19:45 起，地图记录已启动但只读 `/api/robot-control/map/preview` 刷新失败时，扫图卡片、扫图状态、覆盖提示和
  地图流程 marker 都会显示 `扫图画面刷新失败：<原因>`，下一步聚焦重新刷新扫图画面；该失败态不停止建图、不保存地图、
  不发送 manual、Nav2、delivery、stop 或 `/cmd_vel`。
- 2026-06-26 22:05 起，当上车端自动扫图门禁已报告 `ready`、地图记录和地图画面已满足，但 PC 读到 LiDAR proof stale
  或不完整时，“自动扫图准备”仍允许点击 `开始自动扫图（低速）`，并只调用固定 start 代理；雷达显示为“监看/可降级”，start 后再做一次只读雷达 proof refresh 和地图 preview refresh。
  该路径仍不会发送 manual、Nav2、delivery、stop 或浏览器侧 `/cmd_vel`。
- 2026-06-26 21:20 起，`learn.launch.py` 和 `bringup.launch.py` 默认启动 `free_roam_autonomy_node`，让上位机
  `/api/free-roam/autonomy/latest` 能读到真实 runtime artifact 和逐项门禁，而不是因为节点不存在一直 missing。launch 层仍显式传入
  `enable_cmd_vel_publish=false` 与 `motion_hil_unlocked=false`；节点只写 artifact、消费 `/scan` 和 `/map`，未进入自动扫图会话时
  不会调用 stop 兜底，也不会因为进入建图或 bringup 就发布 `/cmd_vel`。
- 2026-06-26 21:40 起，上车端自动扫图策略在 `operator_confirmed`、`mapping_active` 等会话门禁未通过时，优先把
  runtime artifact 写成 `state=locked` 和首个 blocked gate 原因；只有门禁都通过后，超时或未知区域达标才会显示
  `completed`。这样 PC 地图 marker 和“自动扫图准备”不会把尚未开始的会话误报成完成。
- 2026-06-27 14:10 起，产品口径拆成两层：小车“能低速移动”只依赖 PC 连接、现场安全确认、固定 keyboard/manual pulse
  合同和停止兜底，不把雷达作为手控前置；“可以进入自动/自助建图”才要求地图记录启动，并继续按上车端 runtime 检查
  camera/radar readiness、停止兜底和覆盖状态。同期摄像头 8088 服务已改为同源共享 capture，并会清理 0 帧 stale peer，
  避免旧页面独占 `/dev/video1` 后导致新页面看不到实时预览。
- 2026-06-26 22:05 起，“自动扫图准备”从只读状态机门禁推进到上车端受控发车门禁：PC 按钮仍只调用固定 start 代理，
  不直接发布 `/cmd_vel`，但上车端会打开 free-roam 节点双锁，让策略节点按 `/scan`、`/map`
  和 watchdog 决策低速移动。若摄像头不 ready，start 不再返回 `blocked_sensor_readiness`，而是在 `sensor_readiness.mapping_readiness`
  里标明 `camera_first_frame_not_observed`；雷达不 ready 同样只进入降级监看和 `mapping_readiness` 缺口。
- 2026-06-27 16:25 起，PC summary 拆出 `free_roam_autonomy_start_ready`：它只表示上车端 stop 兜底与自动扫图基础门禁已满足，
  不要求 `cmd_vel_publish_enabled=true`。普通首屏是否真正能点 `开始自动扫图（低速）` 还要叠加本地安全确认、地图记录、
  地图画面刷新和停止兜底；点击后由上车端回传 camera/radar `mapping_readiness` 并打开双锁，雷达作为可选监看证据回传。这样避免“必须先解锁才能点击解锁”的循环，也避免把“不能建图”误当成“不能自由移动”。
- 2026-06-27 16:55 起，当 `free_roam_autonomy_start_ready=true` 但本地地图记录或扫图画面还没就绪时，普通首屏的
  `开始自动扫图（低速）` 按钮会走自动扫图向导：先启动地图记录，再把地图预览刷新计入本轮扫图 fresh gate，满足条件后再调用固定 start 代理。
  该向导仍不会自动勾选安全确认，也不会绕过上车端 camera 复检。
- 2026-06-26 18:10 起，当 live 形状为 `free_roam_autonomy_start_ready=true`、`free_roam_autonomy=locked` 且 runtime
  仍是 `artifact_only=true/cmd_vel_publish_enabled=false` 时，普通首屏不再把它解释成“自动扫图未开放”。这表示尚未点击 start，
  但已经可以发起固定 start 请求；UI 会显示 `开始自动扫图（低速）`，runtime 文案写明“当前尚未启动，所以仍是记录模式；
  点击开始后由上车端复检相机，再打开运动双锁”。这只修正所见即所得文案和按钮状态，不由浏览器或 Node 直接发布 `/cmd_vel`。
- 2026-06-27 17:30 起，上车端 `POST /api/free-roam/autonomy/start` 在 `confirm_operator_safety=true` 后会一次写入
  `operator_confirmed=true`、`external_stop_requested=false`、`enable_cmd_vel_publish=true` 与
  `motion_hil_unlocked=true`，并按 `confirm_mapping_active` 写入地图记录意图。`stop` 会收回
  `enable_cmd_vel_publish=false`、`motion_hil_unlocked=false` 并设置 `external_stop_requested=true`。
  HTTP 仍不直接发布 `/cmd_vel`，也不允许修改 `cmd_vel_topic`；真正运动只由上车 `free_roam_autonomy_node`
  在双锁打开后按策略输出 0.12m/s 以内的受限 Twist。
- 2026-06-27 17:45 起，PC summary 的 `motion_hil_unlock` gate 区分“尚未启动”和“不能启动”：
  当 `stop_available=ready` 且 runtime 仍是 `artifact_only=true/cmd_vel_publish_enabled=false` 时，gate 显示
  `not_proven` 和 `当前尚未启动自动扫图，点击开始后由上车端打开运动双锁`；只有停止兜底或 runtime 本身缺失时才显示
  blocked。这样 live 首屏不会在 `free_roam_autonomy_start_ready=true` 时又误提示“完成 HIL 后再解锁”。
- 2026-06-27 00:42 起，上位机 `/api/base/manual` 的默认运动中反馈读窗按点动时长计算：
  500ms first-jog 默认读约 450ms，240ms 键盘连续 pulse 默认读约 190ms。依据
  `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER 本地资料，底盘通过换行 JSON `T=1 L/R`
  控制轮速、`T=130/T=1001` 回读反馈，固件 setpoint/feedback 节奏约 200ms；旧的 220ms
  上限容易在 first-jog 停车前漏掉非零 `T=1001 L/R`。新策略仍保留 stop 兜底，并且不要求雷达或摄像头
  ready 才能低速试动；雷达和摄像头只决定本轮是否可按“可建图”验收。
- 同轮真机 smoke 进一步确认：`T=1 L/R=0.12` 与 `T=13 X=0.12/Z=0` 都能收到 `T=1001`，但轮速仍为
  `0/0`；vendor direct PWM `T=11 L=90/R=90` 能收到非零 `T=1001 L/R=90/90`。因此上位机
  `/api/base/manual` 默认切到 `base_command_mode=pwm`，非 stop 后同时发送 `T=11`、`T=1`、`T=13`
  零速兜底。ROS `esp32_bridge` 也新增 `command_mode=pwm`，bringup/autonomous 默认使用该模式，让 Nav2 和
  free-roam `/cmd_vel` 不再继续走当前真机无效的 `T=1/T=13` 路径。

## 用户流程

1. 打开 PC 首屏，确认默认小车地址。
2. 查看地图、画面、雷达状态。
3. 在“扫地式建图”卡片勾选“人在旁边、周围安全、可以随时按停止”。
4. 点击“开始扫地式建图”，启动上位机建图 runtime。
5. 地图记录启动后键盘会自动启用；按住方向键或 W/A/S/D 可低速移动。
6. 也可以点击 `开始自动扫图（低速）`，由上车状态机在双锁打开后低速自助移动；相机或雷达不 ready 时仍可自由移动，但本轮不能按可验收建图收口。
7. 松开按键、点击停止或点击 `停止自动扫图` 收口；stop 必须收回上车运动双锁。
8. 点击“保存当前地图”，保存完成后 PC 会自动刷新地图画面，并把步骤条收口成“已保存”；再检查 free cell、地图尺寸、覆盖提示和可导航状态。
9. 如果“自动扫图准备”显示相机或雷达缺口，仍可在安全确认后发起低速自由移动；PC 和上车回包必须同时显示 `mapping_readiness.ready=false`，提醒当前不是可验收建图。只有相机首帧和雷达 proof 都 ready 时，才把本轮自动扫图解释为可建图。PC 会在地图上显示 `自动扫图已启动`，并立即刷新一次雷达和地图画面，`下一步` 会带到 `停止自动扫图`，继续负责地图/雷达监看和停止兜底。

## 后续全自动探索要求

如果要升级成真正“像扫地机一样自己跑”的无人值守/半无人值守模式，需要新增上车端状态机，而不是把 PC 按钮直接变成无限运动：

- 实时 LiDAR/障碍物距离 gate：策略节点已接 `/scan` 并写 artifact，仍需真车低速 HIL。
- launch 接入：`learn.launch.py` 和 `bringup.launch.py` 已默认拉起 artifact-only runtime，并暴露
  `free_roam_autonomy_enable_cmd_vel_publish=false` 与 `free_roam_autonomy_motion_hil_unlocked=false` 两个显式初始参数。PC start/stop
  代理只对同名 `/free_roam_autonomy` 节点设置固定门禁参数和运动双锁；未点击 start 前保持 artifact-only，点击 stop 后必须回到双锁关闭。
- 最大运行时间、最大线速度、最大角速度限制：策略内核已有；最小电量限制仍待接底盘反馈。
- 自动 stop fallback 和 watchdog：策略节点已在 `stop_required=true` 时调用 `/trashbot/stop`，仍需真车响应时间 HIL。
- 探索覆盖策略：策略内核已有低速直行、遇障碍换向、覆盖停滞原地扫描；后续可升级边界沿墙或 frontier exploration。
- 地图质量实时指标：策略节点已消费 `/map` free cell 增量和 unknown 占比并写 artifact，仍需真实 map delta HIL。
- 完整验证记录：启动、每段速度命令、传感器状态、停止原因、保存地图结果。
- 真车低速验证通过后才能把 `safe_to_control` 或自动探索能力提升为真。

当前 PC 合同默认 `free_roam_autonomy=locked`。只有上车端 runtime artifact 明确报告双重解锁和逐项 gate ready 时，PC 才显示
`free_roam_autonomy=ready`；PC 自动扫图按钮只调用固定 start 代理。真正运动发布仍由上车端确认项、停止兜底与
`enable_cmd_vel_publish`、`motion_hil_unlocked` 双重锁共同决定，不由浏览器或 Node 代理直接发布；相机/雷达 readiness 只决定
`mapping_readiness`，不再决定“车能不能自由低速移动”。
