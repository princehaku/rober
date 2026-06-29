# PC 扫地式建图向导设计

## 目标

PC 普通用户首屏需要把“建图”和“移动”串成一个像扫地机开荒一样的工作流：先确认现场安全，再启动建图，再低速让小车扫一圈，最后保存并刷新地图画面。

## 当前阶段边界

本阶段实现的是“受控扫图向导”，不是无人值守自动探索：

- 建图启动只走固定 PC 代理 `/api/robot-control/map/start`。
- 保存地图只走固定 PC 代理 `/api/robot-control/map/save`。
- 小车移动有两条入口：键盘连续手控仍是低速、短时、按住才走、松开即停；自动扫图 start 在现场安全确认后只通过上车状态机参数服务打开受限 free-roam 双锁。
- 2026-06-25 16:06 起，扫图卡片自己的安全确认可直接作为键盘扫图的最小预检；不再要求先补 operator report、轮速非零或 LiDAR delta 材料才允许低速键盘扫图。
- 2026-06-27 03:16 起，普通首屏、行程操作、键盘手控、自动扫图和高级点动区全部复用同一个
  “人在旁边、周围安全、停止手段就绪”安全确认；旧的四项 HIL checklist 不再出现在点动区，避免 operator
  误以为发车前还要完成额外预检。底层请求字段仍沿用 `confirm_hil_checklist` 兼容上位机合同，但 UI 只展示一个安全勾选。
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
- 2026-06-28 02:25 起，普通首屏点击“启用键盘”会把键盘控制框滚动到可见区域并重新聚焦该框；
  这一步只改变页面可见性和焦点，不发送 manual、stop、Nav2、free-roam、delivery 或 `/cmd_vel` 请求，避免 operator 点完启用后仍在别的页面区域按键而误以为键盘无效。
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
- 2026-06-28 16:40 起，普通首屏 `当前事实` 的自由移动/自动扫图行也同步消费本地 start/stop pending、停止排队和
  start/stop 回包：启动未返回时显示“正在启动状态机”，停止排队时显示“启动返回后会立刻请求停止”，停止回包成功后显示
  “停止请求已发送”。该改动只修正所见即所得文案，不新增 free-roam、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel` 调用。
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
- 2026-06-27 03:13 起，地图刷新顺带读取的 `/api/robot-control/radar/status` 若返回
  `scan_preview_point_count`，地图雷达 marker、雷达点口径和坐标口径优先展示这个最新点数；只有没有点数组时明确写
  “仅点数，没有点数组，未贴到地图/未显示局部轮廓”。这样不会被自动扫图门禁里的“最近障碍距离”旧 fallback 覆盖，
  雷达开始或刷新后的地图标记和最新只读雷达状态保持一致。
- 2026-06-28 02:32 起，当 summary 明确 `radar_overlay_status=not_current`，或雷达 lifecycle 已停且 runtime scan stale 时，
  普通地图仍不会回画旧雷达点，但 marker、雷达点口径和坐标口径会说明“旧雷达点 N 个已判定为不当前，未贴到地图”。
  这样 operator 能看到为什么 scan preview 有旧点数但地图上没有雷达轮廓，同时不会把旧点误当成当前雷达。
- 2026-06-28 04:36 起，`当前事实` 的地图行也同步该 not-current overlay 事实：如果已经显示真实地图画面或已读到地图材料，
  但雷达 overlay 被 summary 判定为 `not_current`，地图行直接追加“旧雷达点 N 个已判定为不当前，未贴到地图”。
  这样 operator 不必看地图 marker 小字，也能在首屏事实条里知道为什么地图上没有雷达点。
- 2026-06-28 04:42 起，`当前事实` 的雷达行也同步该 not-current 旧点事实：当雷达 lifecycle stopped/stale
  但 summary 仍带旧 scan point count 时，雷达行显示“雷达未运行；旧雷达点 N 个已判定为不当前，未贴到地图”，
  与地图行、地图 marker 和雷达点口径保持同一结论。
- 2026-06-29 起，雷达停止请求 pending 时，地图只显示“雷达停止请求中”marker，不再画实时扫描范围占位或最近距离读数。
  停止请求返回前既不证明雷达已停止，也不把旧点当作停止后的地图点；下一轮只读雷达状态返回后再决定是否显示 stopped、running 或 failed。
  该规则只修正 PC 地图所见即所得显示，不发送 manual、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-28 04:49 起，建图 readiness 的“雷达未刷新”缺口也复用 not-current overlay 事实：
  若没有更具体的旧 `/scan` 距离过期说明，则显示“雷达未刷新（旧雷达点 N 个已判定为不当前，未贴到地图）”。
  这样“能自由移动但不能按建图验收”的原因和地图上没有雷达点的原因保持同一口径。
- 2026-06-28 04:55 起，`当前事实` 的雷达行在雷达未运行时也会显示旧 `/scan` 距离过期说明：
  例如“雷达未运行，旧 /scan 距离 0.04m，约 N 小时前，已过期，不贴到地图；旧雷达点 N 个已判定为不当前，未贴到地图”。
  这样雷达行、建图缺口和地图 marker 都能解释“有旧距离/旧点，但不是当前雷达”。
- 2026-06-29 18:30 起，地图雷达 overlay 的下一步新增白话字段：
  `radar_overlay_next_action_plain` / `next_action_plain` 会把启动雷达、刷新雷达扫描、刷新定位和刷新地图画面翻译成现场可执行短句。
  普通首屏优先显示该字段，旧响应才 fallback 到本地 token 翻译；这样地图、雷达卡和直连 map preview 不再把内部
  `start_radar_then_refresh_map_preview` 或 `refresh_radar_scan_for_map_overlay` 暴露给普通用户。
  该变化只影响只读展示，不启动雷达、不刷新定位、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 21:05 起，建图雷达 freshness 的底层驱动按 WAVE ROVER/STC vendor 资料对齐：
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` 采用 `/dev/ttyACM* @ 230400` 和 `0x54` 固定 47 字节帧。
  `ros2_trashbot_hardware` 的 LiDAR parser 新增真实 STC `0x54` 帧支持，同时保留旧 `0xAA55` mock/回放路径；
  lifecycle、learn/bringup/autonomous launch 和上位机默认雷达命令统一改成 230400。该变化只为恢复 `/scan` fresh
  和地图雷达贴图证据，不把雷达重新变成低速自由移动前置，也不发送任何底盘运动命令。
  同轮上位机部署后，默认 proof refresh 改为 12 秒只读观察窗口，`scan_once`、`scan_hz`、`raw_packet_once` 和
  `base_link->laser_frame` TF 均已观察到，雷达状态进入 `fresh_scan_proof_observed`；PC 地图 summary 已能显示
  雷达标记按当前读数贴到地图。摄像头首帧仍未恢复，自动驾驶真实移动仍需在安全确认后复验 wheel raw L/R。
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
- 2026-06-27 03:10 起，PC 普通首屏把“能尝试共享实时预览”和“画面已经可见”拆开：即使上车 summary
  报 `source_first_frame_failed`，只要设备已加载或已选中 `/dev/video1`，页面仍会挂载只读
  `/api/robot-control/camera/mjpeg` 共享预览，让后来进入的页面也能复用同一条上游流并看到真实画面或真实失败原因；
  只有浏览器 `load`/真实帧证据出现后才把状态提升为“画面可见”，因此不会把无帧误报成可建图。
- 2026-06-28 06:05 起，PC Node 共享 MJPEG relay 会保存最近一次广播的 frame chunk；后进入的浏览器页面如果已经有
  上游共享流，会先收到这份最近帧，再继续跟随实时流。`/api/robot-control/camera/mjpeg/status` 同步返回
  `cached_frame_loaded/cached_frame_age_ms` 作为只读证据；这不会新开第二条相机上游，也不会改变建图 camera ready gate。
- 2026-06-28 06:50 起，PC summary 也会带出
  `shared_preview_cached_frame_loaded/shared_preview_cached_frame_age_ms`，普通首屏“共享画面”行在上游已连接且已有最近帧时
  明确显示“后进页面会先显示最近帧”。这样 status 轮询失败时仍能从 summary 读到缓存帧事实，同时不把缓存帧当成建图
  camera ready 或浏览器已绘制新帧。
- 2026-06-28 02:28 起，PC summary 的相机字段会把最终 `status` 与 `source_readiness` 对齐：
  如果 health 超时但共享 relay 或最近失败已经证明 `source_first_frame_failed`，返回给首屏和高级诊断的
  `source_readiness` 也会同步为 `first_frame_failed`，不再出现“状态无首帧、readiness 仍 not_loaded”的矛盾口径。
- 2026-06-29 20:38 起，`/api/robot-control/camera/mjpeg/status` 顶层也补齐
  `source_readiness` 和 `source_failure_reason`，并与 summary 的相机诊断同源。现场脚本只读共享预览 status 时，
  如果 health 已确认 `source_first_frame_failed`，会直接看到 `source_readiness=first_frame_failed` 和具体失败原因，
  不再出现 status 已说无首帧但 readiness 为空的分裂口径。该入口仍只读 health/relay 内存，不创建 MJPEG client、
  不打开额外 camera stream、不发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-28 12:25 起，上述对齐也覆盖 camera health 返回 `bad_json/not_object` 的情况：只要 PC 共享 MJPEG relay
  已明确 `camera_source_first_frame_failed` 并带出 `uvc_no_frame_not_exclusive` 诊断，summary 就显示
  `status=source_first_frame_failed`、`source_readiness=first_frame_failed`。单纯坏 JSON 仍保留读取异常；
  只有已有 relay 事实能证明无首帧时才归并，避免普通首屏一边说坏 JSON、一边又说不是独占。
- 2026-06-28 12:45 起，PC summary 的 `schema_mismatch_count` 只统计已成功读取但 schema 前缀不在允许列表里的真实合同错配。
  `fetch_failed`、optional latest missing、`schema_missing/not_loaded` 和合法的本地相机 schema
  `trashbot.local_webrtc_camera_*` 不再计入 mismatch。这样 live 上 `/api/status` 或 camera health 偶发超时只显示为部分读取降级，
  不再额外制造“schema mismatch”噪音。
- 2026-06-27 13:35 起，共享预览 status 不再只返回 relay 计数和最近失败 token；它会短读只读 camera health，并在不创建新
  MJPEG client 的前提下透出 `source_diagnosis_status/plain_hint/next_action/not_exclusive`。当真实状态是“设备没人占用但无首帧”时，
  后进入的页面也能直接看到不是独占原因，而不是空白预览或内部 token。
- 2026-06-27 16:01 起，PC 普通首屏的相机无首帧提示分层：当前事实条、画面 overlay 和 `画面状态`
  只显示短句，说明共享预览不是独占、UVC 无帧和下一步检查 USB/输入/供电；完整格式尝试只保留在
  `只读检查`。这保持“画面所见即所得”，同时让后进入页面能快速判断是硬件/输入无帧而不是页面抢占。
- 2026-06-27 21:05 起，`/api/robot-control/camera/mjpeg/status` 在只读 health 返回
  `source_first_frame_failed` 且 `source_usage.status=not_in_use` 或 `owner_count=0` 时，会把诊断统一提升为
  `uvc_no_frame_not_exclusive`，并返回 `source_diagnosis_not_exclusive=true`。这样 summary、MJPEG status
  和普通首屏都一致说明“不是页面独占，是 UVC 没有输出真实帧”，同时 status 查询仍不会打开 MJPEG 上游流。
- 2026-06-28 04:13 起，普通首屏同样覆盖 live 的降级形状：即使 `source_usage_status/selected_name`
  暂时是 `not_loaded`，只要 summary 已返回 `source_diagnosis_status=uvc_no_frame_not_exclusive`，
  当前事实条仍显示“共享预览支持多人观看、不是独占、UVC 没有输出视频帧”，不会退回成“可能页面独占”或“等待画面”。
- 2026-06-28 04:25 起，如果首屏 summary 只有 `camera_health:fetch_timeout_2400ms` 降级，
  但共享预览/相机摘要已证明 `uvc_no_frame_not_exclusive` 或首帧失败，普通连接面板显示“已读到小车状态；
  画面健康读取较慢，具体看画面行的无帧诊断”，不再泛化成“部分项目未通过”。API 仍保留原始
  `robot_api_connection.status=degraded` 和 blocked reason 给高级诊断；该规则只修正普通首屏所见即所得文案。
  同轮补充：若已读到多项状态且剩余失败全是 `fetch_timeout`（例如 `status/camera_health/camera_devices`
  一拍读取较慢），普通连接面板提示“部分读取较慢，下面按画面、雷达、地图和行程分项显示已读事实”，
  仍不隐藏高级诊断里的原始 timeout。
- 2026-06-29 18:50 起，相机 source diagnosis 和共享预览 guidance 也新增白话下一步：
  `preview_next_action_plain` / `source_diagnosis_next_action_plain` 会把 `check_usb_camera_input_power_or_known_good_uvc`
  翻译为“检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占”。
  普通首屏优先显示白话字段，旧响应才 fallback 到本地 token 翻译；这样后来进入的页面看到的是“共享预览不是独占，但 UVC 源无首帧”的现场动作，
  不是内部状态名。该变化只消费只读 camera health 和 PC relay status，不打开额外相机、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:10 起，Nav2 行程边界新增 `nav2_goal_next_action_plain`：
  当 summary 已知道旧行程 action 成功但执行窗口 `wheel raw L/R=0/0` 未闭环时，普通字段会显示
  “路线结果成功但执行窗口轮速 L/R 未非零，勾安全确认后用 ROS 模式重跑并复验执行窗口轮速 L/R”。
  原始 `nav2_goal_next_action` 继续保留给工程诊断；普通首屏优先消费白话字段，避免把 `wheel raw`、`controller`
  或模式 token 当成普通用户说明。该变化只修正只读 summary 和 UI 文案，不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:15 起，PC Node 新增固定只读状态代理：
  `GET /api/robot-control/base/status` 转发上车 `/api/base/status`，`GET /api/robot-control/nav2/status` 转发上车 `/api/nav2/status`。
  两个接口都会返回 fail-closed 顶层控制 flag、`status_key_values` 和白话 `next_action_plain`：base 直出
  `base_command_mode/nav2_base_command_mode/wheel_feedback_lr_nonzero_proven/motion_signal_observed`，Nav2 直出
  `path_point_count/path_generated/planner_server_active/controller_server_active`。这样现场脚本不用再从 summary 间接拼状态，就能判断
  “底盘是否有 wheel raw L/R 证据”和“自动驾驶卡在 controller/lifecycle 还是路线生成”。该变化只读状态，不启动雷达、不执行 Nav2 goal、
  不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:24 起，PC summary 的 `readback_summary.nav2.planner_server_active/controller_server_active/controller_server_requested`
  优先来自当前 `/api/nav2/status` 和 `/api/nav2/proof/latest`，最近一次 `/api/nav2/goal/execution/latest` 的 managed runtime
  只保留为历史执行材料，不再覆盖当前服务状态。这样普通首屏和直连 `/api/robot-control/nav2/status` 会一致显示当前
  controller/lifecycle 是否 active，避免把旧执行窗口的 controller active 误当成“现在仍 active”。该变化只调整只读聚合优先级，
  不启动 Nav2 lifecycle、不执行 goal、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:27 起，直连 `GET /api/robot-control/nav2/status` 的 `next_action_plain` 也采用最小发车确认口径：
  当图上路线已生成但当前 controller/lifecycle 未 active 时，提示“执行图上路线只需勾现场安全确认，执行接口会托管启动自动驾驶 runtime，
  并在同窗口复验轮速 L/R”，而不是要求普通用户先手动恢复 runtime。该变化只修正只读诊断文案，不启动 Nav2 lifecycle、不执行 goal、
  不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:30 起，`readback_summary.free_roam` 增加 `next_action_plain`：
  它复用同一轮 `safe_command_boundary.free_roam_autonomy_next_action`，把“能先自由移动”和“建图验收还差什么”放进自由移动 readback 自身。
  因此 live 出现 `status=start_ready`、`motion_ready=true`、`mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview` 时，
  只读接口也会直接给出“勾选现场安全确认后可先自由移动；建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面”。
  该变化只补 summary 所见即所得字段，不启动自由移动、不启动建图、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:35 起，PC summary 与 `GET /api/robot-control/free-roam/autonomy/latest` 补齐自由移动/建图别名：
  `free_roam_motion_start_ready/free_move_ready/free_move_start_ready` 表示勾安全确认后可启动自由移动，
  `free_roam_motion_ready/motion_ready` 表示当前已经处于运行/发布运动态；
  `free_roam_mapping_ready/mapping_ready` 和 `free_roam_mapping_missing_reasons/mapping_missing_reasons` 表示建图验收材料是否齐备。
  这样外部脚本不再把 `motion_ready=false` 误读为“不能启动自由移动”，也不需要在 summary 和 latest 两套字段名之间猜测。
  该变化只补只读字段别名，不启动自由移动、不启动建图、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:50 起，键盘连续手控的安全边界增加 teleop alias：
  `keyboard_teleop_start_ready`、`keyboard_teleop_status` 和 `keyboard_teleop_next_action_plain` 镜像既有 `keyboard_control_*` 字段。
  外部脚本按“teleop”口径读取时，也能直接拿到“勾安全确认后启用键盘，按住才会连续低速移动，松开/失焦/切页会停”。
  该变化只补只读 summary 字段，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。
- 2026-06-29 19:55 起，`readback_summary.keyboard_control` 和 `readback_summary.keyboard_teleop` 镜像 `readback_summary.keyboard`，
  顶层也增加 `keyboard_control_summary` 和 `keyboard_teleop_summary`。外部脚本无论按 keyboard、keyboard_control 还是 teleop 命名读取，
  都能拿到同一份连续手控只读事实：可启用、必须按住才动、松开/失焦/切页/换方向/点停止都会停。
  该变化只补字段别名，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。
- 2026-06-29 20:18 起，键盘 readback 继续补齐脚本友好的 `continuous_control_ready=true`、
  `keyboard_control_start_ready=true` 和 `hold_to_move_required=true`。这三个字段只说明“勾安全确认后可启用，
  且必须按住才连续低速移动”，不代表键盘已经启用，也不发送 manual pulse、stop 或 `/cmd_vel`。
- 2026-06-29 20:00 起，`/api/robot-control/map/preview` 顶层 `next_action_plain` 明确等于 `path_preview_next_action_plain`：
  图上路线和小车位置已显示时，顶层下一步提示勾安全确认执行路线；雷达贴图缺口只保留在
  `radar_overlay_next_action_plain` / `radar_overlay_wysiwyg_next_action_plain`。这样外部脚本只读顶层下一步时，不会把“先启动雷达”误解成 Nav2 发车前置。
  该变化只修正只读字段别名，不准备路线、不执行 Nav2、不启动雷达、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 20:31 起，`/api/robot-control/summary` 的 `readback_summary.map` 同步补齐
  `next_action_plain` 和 `map_next_action_plain`：前者等于 `path_preview_next_action_plain`，用于表达“图上路线/小车位置下一步”；
  后者等于 `map_wysiwyg_next_action_plain`，用于表达“整张地图所见即所得下一步”。summary 和直连 map preview 不再出现
  顶层下一步一边有值、一边为空的情况。该变化只补只读 summary 字段，不准备路线、不执行 Nav2、不启动雷达、不发送
  manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 20:10 起，`/api/robot-control/map/preview` 顶层增加 `robot_pose_status`：
  同轮 overlay 读到 map-frame 小车位置时返回 `map_pose_observed`，没有读到时返回 `not_observed`。
  这样地图画面、路线点、小车位置和雷达贴图状态都能用顶层字段一眼判断，外部脚本不必自己解析 `robot_pose=null`。
  该变化只补只读 map preview 所见即所得字段，不刷新定位、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:41 起，`/api/robot-control/map/preview` 的地图雷达 overlay 状态与 summary 对齐：
  `partial` 只表示“有当前雷达点，但缺少小车 map pose 等贴图材料”；如果只有小车位置、没有新鲜雷达点，或雷达 lifecycle stopped/scan stale，
  直连 map preview 返回 `radar_overlay_status=not_loaded` 或 `not_current`，当前显示点数固定为 0，并提示先启动/刷新雷达后再刷新地图画面。
  这样不会因为地图上有小车位置，就把雷达层误报成 partial。该变化只修正只读地图预览判定，不启动雷达、不执行 Nav2、
  不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:47 起，PC 普通首屏和高级诊断里的“读取最近 Nav2 结果”会在 latest 读回后自动刷新一次地图预览：
  最近行程结果、地图底图、图上路线、小车位置和雷达贴图因此在同一轮用户动作后同步更新，避免 latest 已变化但地图仍停在旧画面。
  该变化只串联两个只读 GET 代理，不执行 Nav2 goal、不启动 Nav2 lifecycle、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 20:30 起，`/api/robot-control/map/preview` 顶层增加 `path_preview_status`：
  同轮 map preview 读到当前路线点时返回 `path_preview_observed`，否则返回 `not_observed`。
  外部脚本可以直接把 `path_preview_status`、`robot_pose_status`、`radar_overlay_status` 作为地图 WYSIWYG 三件套，不必手动推断点数和 frame。
  该变化只补只读 map preview 字段，不准备路线、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 20:50 起，`/api/robot-control/map/preview` 顶层增加 `path_preview_next_action_plain`：
  路线和小车 map-frame 位置都可见时提示“确认起点、终点和路线后，再勾选安全确认执行”；路线不可见时提示先准备图上路线并刷新地图画面；路线可见但小车位置不可见时提示刷新定位或地图。
  该变化只补只读 map preview 下一步文案，不准备路线、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 21:10 起，`/api/robot-control/map/preview` 顶层 `next_action_plain` 与 `path_preview_next_action_plain` 对齐：
  外部脚本或普通面板只读统一下一步字段时，也能直接看到图上路线的下一步。雷达贴图下一步继续放在 `radar_overlay_next_action_plain`，避免把路线执行确认和雷达刷新动作混在一起。
  该变化只补只读 map preview alias，不准备路线、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 21:30 起，`/api/robot-control/summary` 的 `readback_summary.map` 也增加路线 WYSIWYG 字段：
  `path_preview_status`、`path_preview_point_count`、`path_preview_frame_id` 和 `path_preview_next_action_plain`。summary 主链路现在能在同一个 map 区块里同时表达地图质量、图上路线、雷达贴图和小车 map 位姿状态，不再要求外部脚本从 nav2 区块手动拼路线点数。
  该变化只补只读 summary 字段，不准备路线、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 21:50 起，`/api/robot-control/camera/mjpeg/status` 顶层补齐与 summary 对齐的共享预览 alias：
  `shared_preview_client_count`、`shared_preview_upstream_active`、`shared_preview_content_type_loaded`、`shared_preview_cached_frame_loaded`、`shared_preview_cached_frame_age_ms`、`shared_preview_shared_capture`、`shared_preview_exclusive_camera_claim`、`shared_preview_contract` 和最近失败字段。只接相机状态接口的脚本也能直接确认多个页面共享同一条上游流、不是浏览器独占。
  该变化只补本机 relay 只读状态，不新开 camera capture、不重启相机、不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 22:10 起，键盘连续手控 summary 增加 `keyboard_hold_to_move_plain`、`keyboard_stop_triggers_plain` 和
  `keyboard_pulse_timing_plain`：summary 主链路直接说明必须按住才移动、只启用键盘不会发车、松开/失焦/切页/换方向/点停止都会停，以及当前短脉冲节奏。
  该变化只补只读安全边界说明，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。
- 2026-06-29 22:30 起，`/api/robot-control/summary` 的 `readback_summary.nav2` 增加
  `execution_status_plain` 和 `next_action_plain`。只读 Nav2 区块现在能直接解释最近路线执行证明到哪一步：例如 live 上是路线结果成功但执行窗口轮速 L/R 未非零，已看到非零底盘命令和 IMU 姿态变化，下一步是勾安全确认后按 ROS 模式重跑图上路线并在同窗口确认轮速 L/R 非零。
  该变化只补只读 readback summary 文案，不执行 Nav2 goal、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 22:50 起，`readback_summary.free_roam` 新增 `motion_next_action_plain` 和
  `mapping_next_action_plain`：自由移动 readback 自己就能把“可先低速自由移动”和“本轮能否按建图验收”分开说清。
  live 形态下前者提示勾安全确认后可先自由移动，相机和雷达只影响建图验收；后者提示建图验收还差画面首帧、雷达新鲜、地图记录、地图画面。
  该变化只补只读 summary 文案，不启动自由移动、不启动建图、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 21:55 起，PC 普通首屏在“当前事实”下方新增“现在可以做什么”摘要条，直接展示
  `goal_checklist_summary.move_now_status_plain`、`safety_precheck_summary_plain` 和
  `mapping_blockers_plain` 三行：现在是否可先动、发车前是否只需安全确认、建图还差哪些传感器条件。
  摘要条按钮只滚动/聚焦到既有自由移动、安全确认或建图卡片，不自动勾选、不启动自由移动、不执行 Nav2、
  不发送 keyboard/manual/delivery/stop 或 `/cmd_vel`。
- 2026-06-28 04:31 起，上述部分读取 timeout 口径也同步到 `当前事实` 第一行：
  已读到多项状态但剩余全是 timeout 时显示“少数读取较慢，下面各项按已读事实显示”；相机 health timeout
  已被无首帧诊断解释时显示“画面健康读取较慢，画面行显示真实无帧诊断”。这样用户不用先打开连接卡片，
  也能知道当前事实不是全离线，也不是所有分项都实时完整。
- 2026-06-26 22:05 起，“自动扫图准备”从只读状态机门禁推进到上车端受控发车门禁：PC 按钮仍只调用固定 start 代理，
  不直接发布 `/cmd_vel`，但上车端会打开 free-roam 节点双锁，让策略节点按 `/scan`、`/map`
  和 watchdog 决策低速移动。若摄像头不 ready，start 不再返回 `blocked_sensor_readiness`，而是在 `sensor_readiness.mapping_readiness`
  里标明 `camera_first_frame_not_observed`；雷达不 ready 同样只进入降级监看和 `mapping_readiness` 缺口。
- 2026-06-27 16:25 起，PC summary 拆出 `free_roam_autonomy_start_ready`：它只表示上车端 stop 兜底与自动扫图基础门禁已满足，
  不要求 `cmd_vel_publish_enabled=true`。普通首屏是否真正能点 `开始自动扫图（低速）` 还要叠加本地安全确认、地图记录、
  地图画面刷新和停止兜底；点击后由上车端回传 camera/radar `mapping_readiness` 并打开双锁，雷达作为可选监看证据回传。这样避免“必须先解锁才能点击解锁”的循环，也避免把“不能建图”误当成“不能自由移动”。
- 2026-06-27 20:47 起，PC summary 的 `safe_command_boundary` 进一步显式暴露
  `free_roam_motion_start_ready`、`free_roam_mapping_ready` 和
  `free_roam_mapping_missing_reasons`。前者只表示勾安全确认后可请求低速自由移动；后两者只表示能否按建图验收收口，
  缺口会列出 `camera_first_frame/lidar_fresh/mapping_active/fresh_map_preview`。这样外部脚本、PC 首屏和现场人员不再需要从
  gates 文案里反推“能动”和“能建图”的区别。
- 2026-06-30 08:36 起，PC summary 在上述验收字段之外新增建图启动字段：
  `free_roam_mapping_start_ready`、`free_roam_mapping_start_missing_reasons`、`free_roam_mapping_start_plain` 和
  `free_roam_mapping_start_next_action`。启动建图只要求 `camera_first_frame/lidar_fresh`，也就是画面首帧与雷达新鲜；
  `mapping_active/fresh_map_preview` 继续只属于建图验收。这样“相机和雷达 ready 后可以启动建图记录”与“地图记录和地图画面 ready 后才能验收建图”在合同上不再共用同一个 ready 字段。
- 2026-06-27 20:58 起，普通首屏建图验收文案优先消费 `safe_command_boundary.free_roam_mapping_ready` 与
  `free_roam_mapping_missing_reasons`，只有旧上车端缺少该字段时才 fallback 到 `readback_summary.free_roam.mapping_missing`。
  若 PC 本地刚启动地图记录或已经显示真实地图画面，会过滤上一拍 summary 里的 `mapping_active/fresh_map_preview` 旧缺口；
  但相机首帧和雷达 fresh 仍必须由真实材料证明，不能被旧 readback 的 `mapping_ready=true` 翻案。
- 2026-06-28 03:56 起，PC 固定只读代理
  `GET /api/robot-control/free-roam/autonomy/latest` 会在 `latest_key_values` 中补齐
  `mapping_required_ids`、`mapping_missing`、`mapping_ready` 和 `runtime_gate_count`。即使上车 runtime 只返回部分
  gates，脚本和页面也能直接看到 `camera_first_frame/lidar_fresh/mapping_active/fresh_map_preview`
  哪几项还缺；该读回不启动 free-roam、不打开相机、不刷新雷达、不发布 `/cmd_vel`。
- 2026-06-28 04:01 起，普通首屏的 `刷新自由移动状态（只读）` 结果也会消费上述
  `mapping_missing/mapping_ready`，并结合页面已经显示的地图画面、雷达状态和地图记录会话过滤上一拍旧缺口；
  摘要会直接显示仍未满足的 `建图缺口：...`，或 `建图验收已 ready`。这样现场人员不用打开高级 JSON，
  就能从只读刷新结果判断当前是只能自由移动，还是可以按建图验收。
- 2026-06-29 18:51 起，上位机 `GET /api/free-roam/autonomy/latest` 也直接暴露同一套自由移动/建图分层字段：
  `free_roam_motion_start_ready`、`motion_without_radar_allowed`、`free_move_without_camera_allowed`、
  `mapping_readiness`、`free_roam_mapping_start_ready`、`free_roam_mapping_start_missing_reasons` 和普通下一步文案。
  因此直连 latest、`/api/status.free_roam_autonomy`、PC summary 三者都能看到同一事实：低速自由移动不依赖摄像头或雷达；
  只有建图启动才要求画面首帧和雷达新鲜扫描。该变化只做只读 camera/radar readiness 聚合，不启动自由移动、
  不启动建图、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 19:04 起，PC 代理 `GET /api/robot-control/free-roam/autonomy/latest` 也提升同一组字段，并把上车
  `camera_first_frame_not_observed/radar_scan_proof_not_fresh` 归一成 PC summary 使用的
  `camera_first_frame/lidar_fresh`。因此 PC 普通首屏、PC 只读刷新按钮、外部脚本和上车直连 latest
  都能看到同一判断：`motion_start_ready=true`，`mapping_start_ready=false`，建图启动缺口是画面首帧和雷达新鲜。
  该代理继续固定 `sends_motion_commands=false`，不启动 free-roam、不发送 stop/manual/Nav2/delivery 或 `/cmd_vel`。
- 2026-06-28 13:25 起，若上车端 free-roam runtime 没有返回完整建图验收 gates，PC summary 会补齐
  `camera_first_frame`、`mapping_active`、`lidar_fresh` 和 `fresh_map_preview` 的只读兜底 gate。这样
  `free_roam_mapping_missing_reasons` 里的每个必需缺口都能在 `free_roam_autonomy_gates` 中看到对应 evidence 和 next action；
  这只改善“能自由移动”和“能否按建图验收”之间的所见即所得解释，不新开摄像头、不刷新地图、不启动雷达、不发布 `/cmd_vel`。
- 2026-06-28 13:45 起，`free_roam_autonomy_gates` 的返回顺序也按产品分层固定：
  先显示自由移动启动条件 `operator_confirmed/stop_available/motion_hil_unlock`，再显示建图验收条件
  `camera_first_frame/lidar_fresh/mapping_active/fresh_map_preview/obstacle_clear`。这样外部脚本和高级诊断直接读数组时，
  不会把地图记录、相机或雷达误认为低速自由移动的前置条件；该变更仍只调整只读 summary 顺序。
- 2026-06-28 14:05 起，即使上车端 free-roam runtime 暂时缺失，PC summary 的 fallback gates 也复用同一顺序：
  `operator_confirmed/stop_available/motion_hil_unlock` 先出现，`camera_first_frame/lidar_fresh` 作为建图验收缺口随后出现。
  这样初始加载、runtime missing 或连接降级时也不会退回到“先看相机/雷达再看能不能动”的旧顺序。
- 2026-06-27 23:45 起，建图验收缺口里的 `camera_first_frame` 会复用相机 source diagnosis 的现场建议：
  当 live summary 已证明 `uvc_no_frame_not_exclusive`，并带有 known-good UVC 建议时，普通首屏显示
  `画面首帧未出（不是页面独占；检查 USB/输入/供电，必要时换 known-good UVC）`。这让多人共享预览和建图验收使用同一口径：
  画面失败不是后来页面抢占，但本轮仍不能按可验收建图收口，真实恢复需要处理 USB/输入/供电或换已知可用 UVC。
- 2026-06-27 16:55 起，当 `free_roam_autonomy_start_ready=true` 但本地地图记录或扫图画面还没就绪时，普通首屏的
  `开始自动扫图（低速）` 按钮会走自动扫图向导：先启动地图记录，再把地图预览刷新计入本轮扫图 fresh gate，满足条件后再调用固定 start 代理。
  该向导仍不会自动勾选安全确认，也不会绕过上车端 camera 复检。
- 2026-06-27 16:09 起，普通首屏把地图记录按钮和自由移动按钮拆清：`开始记录（不发车）` 只调用地图记录，
  不暗示小车会移动；真正低速自移动只能点 `开始自由移动（低速）`，且仍要求本地安全确认和停止兜底。
  readiness gate 在本地 safety checkbox 已勾选时同步显示“现场安全确认已满足”，避免继续展示旧 summary 的 blocked 文案。
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
  `not_proven` 和 `当前尚未启动自由移动，点击开始后由上车端打开运动双锁`；只有停止兜底或 runtime 本身缺失时才显示
  blocked。这样 live 首屏不会在 `free_roam_autonomy_start_ready=true` 时又误提示“完成 HIL 后再解锁”。
- 2026-06-27 00:42 起，上位机 `/api/base/manual` 的默认运动中反馈读窗按点动时长计算：
  500ms first-jog 默认读约 450ms，240ms 键盘连续 pulse 默认读约 190ms。依据
  `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER 本地资料，底盘通过换行 JSON `T=1 L/R`
  控制轮速、`T=130/T=1001` 回读反馈，固件 setpoint/feedback 节奏约 200ms；旧的 220ms
  上限容易在 first-jog 停车前漏掉非零 `T=1001 L/R`。新策略仍保留 stop 兜底，并且不要求雷达或摄像头
  ready 才能低速试动；雷达和摄像头只决定本轮是否可按“可建图”验收。
- 2026-06-28 12:05 起，PC summary 在 `readback_summary.base` 和只读 endpoint key_values 中同时暴露
  `wheel_feedback_latest_raw_left/right`，它们是最新 `T=1001 L/R` 读数的 `left_speed/right_speed` 只读别名。
  这只是让 API 字段名和普通首屏的 `wheel raw L/R` 文案保持一致，不新增运动命令，也不把 `0/0` 或历史非零样本外推为
  当前完整 Nav2 路线、delivery success 或 HIL 通过。
- 同轮后续真机复验确认：依据 vendor `json_cmd.h` 的 `T=11` PWM 示例，PC 手控、上位机
  `/api/base/manual` 和 O11 Nav2 托管 bridge 默认使用 `pwm_min_abs=164/pwm_max_abs=164`。手控
  `T=11 L=164/R=164` 已读到运动中 `T=1001 L/R=164/164`，停车后回到 `0/0`；Nav2 bounded
  执行已记录 `goal_succeeded`、`uses_base_uart=true`、`sends_base_motion_commands=true`、
  非零命令 `T=11 L=164/R=-164` 和 `imu_attitude_delta_observed=true`。接口会把
  `wheel_feedback_lr_nonzero_proven` 与 `motion_signal_observed` 分开展示：前者只代表同帧
  `T1001 L/R` 非零，后者还可以来自 `T1001 r/p` 姿态变化。底盘低速试动和 Nav2 执行不再以雷达或摄像头
  ready 为前置；雷达和摄像头只决定本轮是否可按“可建图/可验收画面”收口。
- 2026-06-27 03:06 的行程证据口径已在 2026-06-27 06:06 收紧：Nav2 action
  `goal_succeeded` 只能说明 action 返回成功；只有同时有执行反馈样本、`robot_control_executed`
  未被否定、`sends_base_motion_commands/uses_base_uart` 未被明确否定，并读到同窗口
  `wheel_feedback_lr_nonzero_proven=true` 时，才把“完整行程执行”展示为已完成。`base_feedback_imu_attitude_delta_observed=true`
  只能说明车身运动迹象可见，不能替代 wheel raw L/R 非零。若只发出非零底盘命令但
  L/R 仍为 `0/0`，UI 仍提示排查电机使能、供电、底盘模式和控制模式，并明确“不是雷达阻塞”；
  若 IMU 已证明运动但 wheel L/R 未非零，UI 保持“到达/完整路线未证明”，不会自动进入送达成功。
- 2026-06-27 04:19 起，若 Nav2 执行窗口内 `T1001 L/R` 仍是 `0/0`，但底盘全局只读样本已经出现过非零轮速，
  普通首屏行程证据会额外提示“底盘只读样本已出现非零轮速，Nav2 仍需同窗口复验”。这只用于区分“底盘轮速链路可读”
  和“Nav2 本次执行窗口没有采到同帧非零 L/R”，不把历史/全局底盘样本折算成完整 Nav2 route proof，也不提交
  delivery success。
- 2026-06-27 08:31 起，PC 普通首屏会把 summary 聚合出的 `next_execution_base_command_mode`
  带进行程证据文案：当上次 Nav2 结果是旧 `pwm` 执行、但下一次上位机策略已切到 `ros`，且同窗口
  wheel raw L/R 仍未非零时，行程进度和证据摘要明确显示“下次将用 ros 重新执行这条图上路线”。
  这只修正所见即所得文案，不触发执行、不放宽安全确认，也不把旧 `goal_succeeded` 外推为完整路线或送达成功。
- 2026-06-27 16:18 起，上述 `pwm -> ros` 复验口径也同步进入普通首屏行程操作区：即使最近
  `goal_succeeded` 已按时间判为旧记录，只要 summary 或 `safe_command_boundary` 明确
  `goal_succeeded_but_wheel_lr_zero` / `pending_ros_rerun_after_pwm`，行程状态、最小预检和主按钮都会显示
  `用 ROS 重跑图上路线`。勾选安全确认只解锁按钮文案和固定后端 gate，不会自动调用 Nav2 execute、manual、
  stop、free-roam 或 `/cmd_vel`。
- 2026-06-27 15:24 起，PC summary 的建图雷达 gate 会优先消费 free-roam runtime 的实时
  `/scan` 快照：只要 `snapshot.lidar_age_s <= 1.5` 且 `snapshot.lidar_min_distance_m` 有限，
  `lidar_fresh` 就按 runtime scan 显示 ready，即使旧 `radar/scan-proof/latest` artifact 已过期。
  没有 runtime snapshot 时仍按 proof freshness 降级，避免旧 ready gate 误导。该规则只修正只读
  所见即所得，不启动雷达、不发布 `/cmd_vel`。
- 2026-06-27 15:47 起，PC 普通地图 marker 会把 `lidar_fresh=ready` 的 runtime `/scan` gate 作为
  `readback_summary.lidar` 缺失时的只读兜底。若同时只有 `obstacle_clear` 的最近障碍距离、没有
  `scan_preview_points`，地图显示“雷达距离：最近障碍 Xm（非地图点）”，并在口径里声明这是距离读数、
  不是已贴到地图的雷达点。该规则只修正 PC 展示，不生成点云、不刷新雷达、不触发自由移动或 `/cmd_vel`。
- 2026-06-27 15:32 起，PC 普通首屏会把建图缺口和真实地图画面做本地对齐：当
  `/api/robot-control/map/preview` 已显示真实 `image_data_url` 时，即使 summary 里还带旧
  `fresh_map_preview`，界面也不再提示“地图画面未刷新”。这只移除已经被 PC 画面证明满足的缺口；
  `camera_first_frame`、`mapping_active`、`lidar_fresh` 仍按各自事实保留，且不自动启动地图记录、
  free-roam、manual、Nav2、delivery、stop 或 `/cmd_vel`。
- 2026-06-29 18:47 起，上位机新增只读 `GET /api/map/status`，返回既有 map lifecycle/material
  摘要，并在 `map_status.routes.status` 中自描述该入口。现场脚本不必再从 `/api/status` 聚合或
  POST action 猜地图状态；误用 GET 读地图事实也不会得到 405。该入口不启动建图、不保存地图、
  不刷新 proof、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-27 15:18 起，O11 Nav2 执行 artifact 的 `proof_status` 也按真实
  `base_command_mode` 标记缺口：ROS 重跑若仍只看到非零命令、但同窗口 `T1001 L/R=0/0`，
  会写成 `nav2_goal_succeeded_with_ros_commands_but_wheel_lr_zero`。这样自动驾驶排障会指向
  “ROS 控制命令已进 bridge、轮速闭环待复验”，不再沿用旧 PWM 诊断口径；这不触发发车，
  也不把 IMU 姿态变化折算成 wheel raw L/R 非零。
- 2026-06-27 19:40 起，PC summary 的 Nav2 下一次复验模式不再只照抄上位机默认 `ros`：
  若 `ros/T=13` 已经发出非零底盘命令但同窗口 `T1001 L/R=0/0`，下一次 `next_execution_base_command_mode`
  会切到 `speed`，普通首屏主按钮随之显示 `用 SPEED 重跑图上路线`，请求体也发送 `base_command_mode=speed`。
  这对应 `docs/vendor/VENDOR_INDEX.md` 的 WAVE ROVER 规则：`T=13` 未被硬件闭环证明时可回退 `T=1`
  差速控制；该变更只改变下一次显式确认后的固定 Nav2 execute 请求，不自动发车，不放宽安全确认。
- 2026-06-27 20:18 起，上位机 `/api/nav2/goal/execution/latest` 在只读回放旧 artifact 时也会派生
  `nav2_goal_execution_proven=false` 与 `nav2_goal_execution_not_proven=wheel_feedback_lr_nonzero,...`。
  这修正“旧 action succeeded 但 wheel raw L/R=0/0”被误读为自动驾驶完成的问题；它不重写 artifact、
  不启动 Nav2、不发送底盘命令，只让所有新打开 PC 页面的人看到同一根因。
- 2026-06-29 18:42 起，上位机 `/api/base/status` 和 `/api/nav2/status` 顶层直接暴露
  `base_command_mode`、`nav2_base_command_mode`，Nav2 status 额外暴露
  `nav2_goal_execute_default_base_command_mode`。PC summary 的 key-values 也收录
  `base_command_mode`，因此普通首屏和诊断脚本不用再从旧执行 artifact 反推下一次路线执行模式。
  协议口径仍采用 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER 本地资料：`T=13` 为 ROS 控制，
  `T=1` 为左右速度控制，`T=11` 为 PWM 输入。该变化只补只读状态字段，不执行 Nav2、不发送
  manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 2026-06-27 18:12 起，普通首屏执行图上 Nav2 路线后，会按固定顺序完成 `execute -> map preview -> execution latest -> summary`
  只读刷新。`execute` 请求体的 `base_command_mode` 会优先跟随 summary/latest 的 `next_execution_base_command_mode`，
  当前 live 的 `pending_ros_rerun_after_pwm` 因此会显式发送 `base_command_mode=ros` 和现场安全确认；如果 latest 和本次 execute 的
  `evidence_ref` 一致，行程证据摘要优先使用 latest 里的完整 wheel raw L/R 与反馈样本数，随后再刷新 PC summary，
  让“当前事实”、地图行程 marker 和送达 gate 看到同一轮 ROS 执行证据。该刷新链路不新增 `/cmd_vel`、manual 或 delivery
  调用，也不会把旧 latest 覆盖到新执行上。

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

2026-06-27 06:11 起，PC summary policy 名称也同步分层：`free_roam_autonomy_policy.mode=free_move_requires_safety_confirm_stop_fallback`
只描述自由移动启动门禁；`mapping_mode=mapping_acceptance_requires_camera_and_fresh_radar` 和
`mapping_required_gates=[camera_first_frame,fresh_radar_scan,map_recording_active,fresh_map_preview]`
才描述可验收建图门禁。这样普通 UI、Node API contract 和上车端 `sensor_readiness.mapping_readiness`
使用同一口径：车可以先低速自由移动，只有相机和雷达 ready 时才把本轮按建图收口。

2026-06-30 08:36 起，policy 同步增加
`mapping_start_required_gates=[camera_first_frame,fresh_radar_scan]`，专门描述“能否启动建图记录”的入口条件。
`mapping_required_gates` 不改名不收窄，继续描述验收条件，避免老脚本把地图记录和地图画面缺口误读成不能先启动建图。

2026-06-27 06:19 起，PC summary 的 `free_roam_autonomy_gates[]` 增加 `scope` 分层：
`free_move_start` 只包含现场安全确认和停止兜底，决定“能否请求低速自由移动”；
`mapping_acceptance` 包含相机、雷达、地图记录和地图画面，决定“能否按可验收建图收口”；
`runtime_diagnostic` 只解释上车端运动发布状态。普通首屏 gate 行按 scope 显示为“启动条件 / 建图验收 / 只读状态”，
不再让 `lidar_fresh=blocked`、`obstacle_clear=not_proven` 或 `motion_hil_unlock=not_proven`
在视觉上变成自由移动启动阻塞。

2026-06-27 16:28 起，普通首屏自由移动准备区的顶部摘要也和 `free_roam_autonomy_gates[]`
保持一致：一旦 summary 已返回结构化 gates，文案显示“已读到上车端自由移动门禁”，并按 scope 汇总
`启动条件 x/y 已满足` 与 `建图验收 x/y 已满足`。只有缺少结构化 gates 的旧上车端才显示固定 policy
前置项，避免 gate 列表已出现时顶部仍误写“正在读取”。

2026-06-27 16:37 起，顶部 `建图验收 x/y` 的分母改为 `free_roam_autonomy_policy.mapping_required_gates`
的真实数量，而不是当前 `mapping_acceptance` gate rows 的数量。这样 live 形态下即使结构化 gate rows
只返回 `mapping_active/lidar_fresh/obstacle_clear`，顶部仍按 policy 的
`camera_first_frame/fresh_radar_scan/map_recording_active/fresh_map_preview` 四项显示 `2/4`，并和下方
“缺口：画面首帧未出、地图记录未启动”对齐。

2026-06-27 16:47 起，普通首屏 `当前事实` 的自由移动行会消费 `obstacle_clear` gate：
当 gate 非 ready 且上车端 runtime 已给出 `最近障碍 0.04m` 这类证据时，文案直接追加
`当前雷达近障碍：最近障碍 ...，原地换向避让，不继续直行`。这条信息只解释现场预期动作，
不把雷达或近障碍反向变成自由移动启动硬门禁；`free_roam_autonomy_start_ready=true` 时仍显示可在安全确认后请求低速自由移动，
建图验收仍由 camera/radar/map preview 的 mapping gate 单独决定。

2026-06-27 03:50 起，PC `自动扫图准备` 明确新增一行 `建图验收`：`free_roam_autonomy_start_ready=true`
只表示可在安全确认后发起低速自由移动；如果 camera 没有首帧或雷达未达到 `雷达已运行`，本轮只能按自由移动记录，
不能按可验收建图收口。只有画面可见证据和雷达运行证据同时满足，才把本轮标成“可按建图记录监看”。

2026-06-27 04:20 起，PC 停止按钮、下一步和扫图状态文案按本轮模式分开：`mapping_active_applied=false`
或当前相机/雷达不满足建图验收时显示 `自由移动`，`mapping_active_applied=true` 且建图证据满足时显示
`自动扫图`。这只改变普通用户读到的文案；启动和停止仍走同一组固定上车端 free-roam 代理，不新增浏览器侧运动出口。

2026-06-27 04:32 现场通过 PC 固定代理验证雷达启动链路：`POST /api/robot-control/radar/start`
返回 `lifecycle_forwarded`，`command_result.executed=true/ok=true`，随后
`POST /api/robot-control/radar/scan-proof/refresh` 生成 `o1-lidar-scan-proof-1782505841325`。PC summary
读回 `lifecycle_running=true`、`continuous_window_observed=true`、`latest_scan_proof_fresh=true`、
`scan_preview_point_count=72`，且机器人 map pose 已读到。该证据证明雷达可以从 stopped 拉到 running/fresh，
地图雷达 marker 可以使用本轮真实点位；仍不等于 camera 首帧、Nav2 完整路线 HIL 或 delivery success 已完成。

2026-06-29 20:45 起，PC radar lifecycle 响应也显式带出地图贴图验收口径：
`sensor_lifecycle_only=true`、`map_preview_endpoint=/api/robot-control/map/preview`、
`post_start_map_preview_required=true` 和 `radar_overlay_wysiwyg_*`。`POST /api/robot-control/radar/start`
只证明雷达 lifecycle 请求已转发，不能直接等同“地图上已有雷达点”；启动后仍必须刷新 map preview，并以
`radar_overlay_status`、`radar_overlay_point_count` 和 `radar_overlay_wysiwyg_status_plain` 作为地图标记所见即所得证据。
该变化只补响应合同，不发送底盘、Nav2、free-roam、delivery、manual、keyboard、stop 或 `/cmd_vel`。

2026-06-29 21:10 起，PC 直连 `GET /api/robot-control/radar/status` 在 `radar_overlay_wysiwyg_*`
之外新增地图贴图前置缺口字段：`radar_scan_required_observations`、
`radar_scan_observation_status`、`radar_scan_observation_missing_reasons`、
`radar_scan_ready_for_map_overlay`、`radar_overlay_ready_for_map`、
`radar_map_overlay_readiness_status` 和 `radar_map_overlay_next_action_plain`。
当现场出现 `lifecycle_running=true` 但 `latest_scan_proof_fresh=false` 时，PC 会直接显示缺
`scan_once,scan_hz,raw_packet_once`，而不是只说雷达未就绪。该状态仍只证明扫描材料是否足够，
地图上是否真的画出雷达点必须继续以 `/api/robot-control/map/preview` 同轮 overlay 点数为准；
本变更不启动雷达、不刷新 proof、不发送底盘、Nav2、free-roam、delivery、manual、keyboard、stop 或 `/cmd_vel`。

2026-06-29 21:35 起，PC summary 首屏也消费同一组雷达扫描观测缺口：当上车端
`/api/radar/status.blocked_reasons` 带
`latest_scan_proof_required_observations_missing:scan_once,scan_hz,raw_packet_once,...` 时，
`readback_summary.lidar/radar` 会提升 `radar_scan_observation_status`、
`radar_scan_observation_missing_reasons`、`radar_map_overlay_readiness_status` 和
`radar_map_overlay_next_action_plain`。普通动作卡 `地图雷达点`、目标检查 `radar_next_action_plain`
会直接显示“缺 scan_once、scan_hz、raw_packet_once”，不再只提示刷新雷达状态。该变化仍只做
summary 只读聚合，不启动雷达、不刷新 proof、不发送底盘、Nav2、free-roam、delivery、manual、keyboard、stop 或 `/cmd_vel`。

2026-06-27 08:51 起，PC summary 在 `/api/radar/status` 已显示 `lifecycle_running=true` 时，优先把
`continuous_scan_status` 作为普通首屏雷达主状态；如果独立 latest proof endpoint 仍是 404/missing，地图和雷达卡片显示
`雷达无新点`，并说明“雷达驱动在运行，但当前没有读到新的雷达点”。这样现场点击启动雷达后不会把“驱动已运行但 proof
尚未写出/窗口无新点”误读成“雷达未运行”；同时仍不把无点云误报为可验收建图。

2026-06-27 12:26 起，上车端 `free_roam_motion_readiness()` 的建图雷达判断同时消费
`/api/radar/status` 的 proof freshness 和 `free_roam_autonomy_latest.json` 内的实时 `/scan` 快照。
当 radar proof artifact 因旧窗口而 stale，但 free-roam runtime 显示 `snapshot.lidar_age_s <= 1.5` 且
`snapshot.lidar_min_distance_m` 为有限值时，`sensor_readiness.mapping_readiness` 可把雷达项视为 ready；
返回体会保留 `radar.proof_ready=false`、`radar.runtime_scan_ready=true` 和 runtime scan 明细。这样“雷达已经开始并被
free-roam 节点实时读到”不会被旧 proof 文件卡成不能建图；若相机仍无首帧，mapping readiness 仍会缺
`camera_first_frame_not_observed`。该改动不改 WAVE ROVER UART/JSON 命令、不发布 `/cmd_vel`，只修正 start 代理进入建图会话前的只读 readiness 聚合。

2026-06-27 04:38 起，上车端 `camera_first_frame_probe.py` 的 backend smoke 使用进程组超时清理，并把
v4l2/ffmpeg 后端矩阵单次 timeout 压短，避免 PC deep probe 超时后遗留 `ffmpeg` 或 probe 进程占用
`/dev/video1`。现场复测 `backendSmoke=1` 在 23s 内结构化返回 `first_frame_timeout/capture_read_call_timeout`，
`backend_smoke_status=backend_no_frame_observed`，且远端无残留进程。该证据说明当前仍是硬件/驱动无首帧，
但 PC 画面失败态现在不会因为诊断工具残留而被二次污染。

2026-06-27 08:39 起，PC summary 会把最近一次 camera first-frame probe 的 backend smoke 短结论透传到
`readback_summary.camera`：`first_frame_probe_backend_smoke_status`、`first_frame_probe_backend_frame_observed`、
`first_frame_probe_backend_attempts` 和 `first_frame_probe_fallback_attempts_summary`。普通首屏在
`backend_no_frame_observed` 时优先显示“不是页面独占，摄像头能打开，后端多种方式也没有取到视频帧”，避免现场把
共享预览失败误判成某个浏览器独占。同期 SSH 只读复核确认 8088/8787 正常监听、`/dev/video1` 为 DV20 UVC capture、
无人占用，`v4l2-ctl --stream-mmap` 8 秒输出 0 字节；该证据不等于摄像头已修好，只把失败归因展示为所见即所得。

2026-06-27 09:08 起，普通首屏“当前事实”也消费同一套摄像头归因：当 live summary 是
`source_first_frame_failed + source_usage_status=not_in_use + capture_read_returned_false` 时，直接显示
`画面：不是独占，摄像头没人占用但没有输出视频帧`；如果 backend smoke 已证明多后端无帧，则显示
`画面：不是独占，后端多种方式也没有取到视频帧`。这样 operator 不用展开画面卡片也能知道问题不是后来进入的页面独占；
摄像头仍然必须读到真实帧后才可按可建图验收。

2026-06-27 19:23 起，PC summary 会把 free-roam runtime snapshot 中的 `/scan` 新鲜距离提升为
`readback_summary.lidar.runtime_*` 结构化字段。普通地图 marker 若没有雷达点数组，会显示
`雷达距离：最近障碍 Xm（非地图点）`；坐标口径继续说明这是距离读数，不是已贴到地图的雷达点。
这样 live 形态下 `radar/status` proof stale、`scan_preview_point_count=0`，但 free-roam runtime
已读到 `/scan` 距离时，地图仍能所见即所得地显示当前雷达距离。该变更不改变自由移动启动门禁，
不自动刷新雷达，不发布 `/cmd_vel`，不把距离读数当成可验收建图点云。

2026-06-27 20:09 起，PC `/api/robot-control/map/preview` 在转发地图图片时同步附带
`radar_overlay` 只读层：从固定的定位/Nav2/雷达 latest/status endpoint 聚合
`scan_preview_points`、`scan_preview_*_count`、`scan_preview_frame_id` 和 `robot_pose`。
地图图片失败或 overlay 读不到时不互相冒充：图片状态仍由 `/api/map/preview` 决定，雷达/位姿缺口只写入
`radar_overlay.overlay_status` 与 `radar_overlay.blocked_reasons`。这让 PC 地图预览响应本身具备
“图片 + 雷达点 + 小车位姿”的同轮只读材料，前端无需再靠多个接口异步猜测地图上应显示什么。

2026-06-27 20:26 起，PC 普通地图前端优先消费 `/api/robot-control/map/preview.radar_overlay`：
当 summary 暂时没有 `robot_pose` 或 `scan_preview_points`，但当前地图预览响应已随图返回位姿和雷达点时，
地图 marker、雷达点、雷达点口径和坐标口径都按这份同轮只读 overlay 展示，并明确标为“地图预览雷达点”。
该规则只修正所见即所得显示，不启动雷达、不刷新地图、不发送 manual/Nav2/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-27 20:41 起，`radar_overlay.overlay_status` 更严格区分完整与局部材料：只有地图预览同轮同时读到
`scan_preview_points` 和 map-frame `robot_pose` 时才返回 `loaded`；如果只有雷达点但缺机器人 map 坐标，
返回 `partial` 并带 `robot_pose_missing_for_map_radar_overlay`。普通地图仍可显示局部雷达轮廓和点数，
但不能把这些点冒充成已贴到地图坐标。该变更只修正只读状态，不触发定位、雷达或运动命令。

2026-06-27 20:52 起，PC 普通地图前端回归锁定 partial overlay 行为：当 map preview
随图返回雷达点但没有 `robot_pose` 时，页面只显示 `地图预览雷达局部点 ... 等待地图位置`，
不显示地图坐标雷达点 SVG，也不显示小车 marker；坐标口径必须写明雷达只显示车身局部轮廓、不贴到地图。
该规则对应当前 live 的 `robot_pose_missing_for_map_radar_overlay` 形态，仍不触发任何运动或定位命令。

2026-06-29 19:09 起，PC summary 的地图雷达 overlay 下一步也按真实缺口分流：当地图雷达点为 0 且
`radar_lifecycle_not_running_for_map_radar_overlay` 或 stale scan 存在时，`radar_overlay_next_action_plain`
显示“先启动雷达并等待新扫描，再刷新地图画面确认雷达点”或“刷新雷达扫描，再刷新地图画面”，不再 fallback 成
“确认小车地址可访问”。该变化只修正所见即所得文案，不启动雷达、不刷新地图、不发送 manual/Nav2/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-27 21:47 起，Robot Control summary 的 `readback_summary.map` 也暴露同一雷达 overlay 口径：
`radar_overlay_status`、`radar_overlay_blocked_reasons`、`radar_overlay_scan_preview_*` 和
`radar_overlay_robot_pose_status`。因此只读 summary、普通首屏和 `/api/robot-control/map/preview`
都能一致表达“有局部雷达点但没有机器人地图坐标，只能显示局部轮廓，不能贴到地图”。该改动不新增地图刷新、
雷达刷新、定位、Nav2、manual、free-roam、delivery、stop 或 `/cmd_vel` 调用。

2026-06-28 07:05 起，PC 普通地图前端不再只信 `readback_summary.map.radar_overlay_status`：
如果旧 7001 还把 overlay 报成 `partial/loaded`，但 `readback_summary.lidar.runtime_scan_status=stale`
或 `lifecycle_running=false/lifecycle_state=stopped`，前端会把 summary overlay 视为 not-current，
不从 `o3_proof_summary` 回捞旧点数组，也不显示 `雷达局部点 ...`。这让未重启到最新后端的现场页面也不会把旧雷达材料画成当前地图标记。

2026-06-27 23:20 起，PC 地图和自由移动卡片不会把 stale runtime `/scan` 距离当作当前障碍：
`runtime_scan_status=stale` 时，即使 `runtime_lidar_min_distance_m=0.04` 仍存在，也只显示为
`旧 /scan 距离 0.04m ... 已过期，不贴到地图`；只有 `runtime_scan_status=fresh` 或 ready 的 runtime gate
才能生成 `最近障碍 Xm`。这保持“雷达开始后地图标记所见即所得”：旧距离可以解释历史材料，但不能变成地图点、
当前近障碍或建图 ready 证据。低速自由移动仍只看安全确认和停止兜底，不新增任何运动命令。

2026-06-27 23:24 起，旧 `/scan` 距离的年龄不再直出大秒数：PC 会把 stale age 翻译为
`约 N 秒前 / 约 N 分钟前 / 约 N 小时 N 分前 / 约 N 天 N 小时前`。这避免现场看到
`10234.64s` 后难以判断距离有多旧；刷新、建图 ready 和地图贴点判定仍保持原来的结构化 freshness 口径。

2026-06-27 23:30 起，`free_roam_mapping_missing_reasons=lidar_fresh` 的普通文案也会带上 stale
runtime `/scan` 说明，例如 `雷达未刷新（旧 /scan 距离 0.04m，约 2 小时 51 分前，已过期，不贴到地图）`。
这让自由移动/建图分层更直观：小车仍可在安全确认后低速自由移动，但本轮不能用旧雷达距离按建图验收。

2026-06-27 23:35 起，Nav2 自动驾驶 readiness 的服务缺口也结构化到 PC summary：
`planner_server_active=false` 会进入 `nav2_goal_blockers=planner_server_inactive`，与
`controller_server_inactive` 同级展示。该变更只影响只读 readiness 和文案，不启动 Nav2、不生成路线、不发送底盘命令。

2026-06-27 23:39 起，普通首屏自动驾驶行也同步该结构化缺口：planner/controller 当前 inactive 时，
用户不需要打开高级诊断或读取 API，就能在 `当前事实` 里看到重跑前应先恢复 Nav2 planner/controller。
该提示只影响 PC 文案，不改变发车前安全确认、不绕过 Nav2 服务状态。

2026-06-28 07:20 起，普通首屏会把 planner/controller inactive 的下一步统一翻译为
`先恢复规划服务/控制服务，再准备图上行程并按地图画面确认`。如果两项都 inactive，恢复入口状态显示
`先恢复规划服务和控制服务（不发车）`，避免把自动驾驶不能动误导成相机、雷达或单纯路线未准备。
该规则只改变 PC 诊断文案和无运动恢复入口展示，不自动执行 Nav2 路线、不发送底盘命令。

2026-06-28 07:35 起，普通首屏 `当前事实` 会先声明连接读数是否可信：
当上位机 summary 返回 fail-closed timeout，或本次刷新直接失败但页面仍保留上一拍 summary 时，事实条首行显示
`当前事实不能当作实时读数` / `下面可能是上一次读数`。这样现场不会把旧相机、旧雷达、旧地图或旧 Nav2 状态误当成当前画面；
详细 timeout 字段仍留在 alert/高级诊断，普通首屏不暴露 `/api/*` 或 `fetch_timeout`。

2026-06-28 07:50 起，浏览器读取 PC Node `/api/robot-control/summary` 增加 3.5s 客户端超时。
如果 7001 自身间歇卡住，普通首屏会退出 loading 并进入 fail-closed 连接失败事实，而不是无限等待。
该超时只包住首屏只读 summary GET，不缩短地图刷新、Nav2 规划/执行、自由移动 start/stop 或任何 POST 控制代理的服务端等待窗口。

2026-06-28 08:05 起，键盘连续手控按住期间不再等待全量 summary 刷新：
每个 240ms manual pulse 成功后直接用回包 wheel raw L/R 更新手控状态，并允许 260ms 定时器继续发下一次固定低速脉冲；
完整 summary 刷新延后到松开、停止、失败或其他显式只读刷新。安全确认、速度/时长上限、stop 兜底和固定
`/api/robot-control/base/manual` 代理不变。

2026-06-29 01:40 起，统一安全确认被取消时，PC 会同步释放键盘控制权：
未按住方向时只撤销 armed 状态，不发送任何运动或停止命令；正在按住方向时先复用固定 stop 代理收口，
并把停止原因显示为“安全确认取消”。这保持“小车能低速移动只依赖现场确认和停止兜底”的口径，同时避免确认取消后
界面继续表现为已启用键盘。

2026-06-28 08:25 起，PC 行程执行前端门禁进一步收敛：
当前地图上已经显示路线且已勾选安全确认时，即使小车位置 marker 未显示，执行按钮仍可执行这条图上路线；
页面会继续提示“建议先重新定位或刷新地图”，但它不再作为发车前硬挡。执行请求仍发送地图上可见路线终点，
不回落到默认表单目标，后端继续复核安全确认和固定白名单。

2026-06-28 08:40 起，普通 PC 行程执行默认结果等待窗口从 8s 提升到 20s。
这只让已点击执行的 Nav2 路线有更完整的结果回传时间，减少长一点的真实路线被 PC 过早判定 timeout；
不新增自动发车，不改变安全确认、路线目标、ROS base command mode 或后端最小 preflight。

2026-06-27 20:15 起，PC summary 的 `readback_summary.nav2` 额外提升
`controller_server_active` 与 `controller_server_requested`。当最近一次 Nav2 action 已返回 succeeded、
但执行窗口 wheel raw L/R 仍为 `0/0`，且当前 Nav2 controller 读数为 inactive 时，
`safe_command_boundary.nav2_goal_next_action` 会同时说明“controller 当前未 active”和“下一次需用当前建议模式重跑并复验同窗口 L/R”。
这不改变安全门禁，不自动启动 Nav2，不发送 `/cmd_vel`；它只把“规划成功 / action 成功 / controller 未 active / wheel raw 未闭环”
四件事拆开展示，避免把自动驾驶没动误判成相机或雷达阻塞。

2026-06-27 20:35 起，上述 controller 诊断会避开已完成 O11 执行 artifact 的事后 inactive 状态：
如果最近 Nav2 执行已经 `goal_succeeded`、发出非零底盘命令、写入 WAVE ROVER UART command log 或读到 IMU 姿态变化，
PC 下一步文案会把“旧执行主因不是雷达或相机”和“当前 controller 未 active，重跑前需先恢复 controller”分开，
卡点仍是同窗口 `T=1001 L/R` 非零复验。该变更只修正诊断展示，不自动重跑 Nav2、不发送底盘命令。

2026-06-27 21:58 起，`controller_server_active=false` 也进入
`safe_command_boundary.nav2_goal_blockers=controller_server_inactive`。当路线读数和 map pose 已 ready 但 controller inactive 时，
`nav2_goal_ready=false` 且 label 显示 `Nav2 controller 未就绪`；当路线本身还未 ready 时，label 仍保持 `图上路线未就绪`，
但 blocker 列表会同时列出 controller 缺口。这样 PC 和自动化脚本不再需要从中文 `next_action` 里反推 controller 状态。

2026-06-27 22:05 起，前端普通地图和 `当前事实` 也消费同一个 controller blocker：
地图 `行程读数` 不再只显示规划服务状态，而是同时显示控制服务已运行、未运行或未读取；
旧 Nav2 action succeeded 但 wheel raw L/R 仍为 `0/0` 时，自动驾驶原因会把“不是相机或雷达阻塞”
和“Nav2 controller 未 active，重跑前先恢复”并列展示。该规则只影响 PC WYSIWYG 文案，
不自动恢复 controller、不重跑 Nav2、不发送 manual/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-27 20:19 起，PC 普通首屏在 `source_first_frame_failed` 但诊断明确不是外部独占时，
仍优先自动接入共享 MJPEG 只读预览，面板状态显示“连接中 / 正在接入共享实时画面”。
无帧根因不会丢失：当前事实和共享画面状态继续显示“不是页面独占、UVC 无帧、必要时检查 USB/供电或换 known-good UVC”。
如果确实是外部进程占用，相机卡片仍显示占用失败，不会误导用户继续抢设备。该调整只改变 PC 页面展示和只读 `<img>` 接入，
不发送运动命令，不把正在连接的流当作建图 camera ready；建图验收仍要求真实首帧或 MJPEG 帧已绘制。

2026-06-28 09:20 起，PC `/api/robot-control/summary` 的普通首屏 HTTP 路径使用短只读预算：
相机 source failure 覆盖最多等待 600ms，summary 每个只读 endpoint 最多等待 2400ms。慢 `camera/health`、`/api/status`
或其他只读端点只会把 `robot_api_connection.status` 标为 degraded，并在对应 readback 里记录 timeout；
不会再让已返回的自由移动、雷达、Nav2 或地图读数整页空壳。底层 `buildRobotControlSummary()` 默认宽超时仍保留给离线验证。
该规则不发送 free-roam、manual、Nav2、delivery、stop 或 `/cmd_vel`。

2026-06-28 09:20 现场只读复验口径：
共享相机预览仍是 `single_shared_capture_for_multiple_clients`，`exclusive=false`，所以“谁进来都能看”由 PC Node 单上游 MJPEG 广播承担；
当前无画面根因是摄像头源 `source_first_frame_failed/first_frame_total_timeout`，不是浏览器独占。自由移动读数为
`free_roam_motion_start_ready=true`，因此低速自由移动不依赖雷达 ready；建图验收仍因 `camera_first_frame`、`lidar_fresh`、
`mapping_active`、`fresh_map_preview` 缺失而未 ready。自动驾驶当前卡点是 Nav2 `planner_server_active=false`、
`controller_server_active=false`，并且图上路线/地图定位未 ready；普通入口应先点“恢复自动驾驶服务（不发车）”，再准备路线并显式安全确认执行。

2026-06-28 11:05 起，PC 普通行程入口在“恢复自动驾驶服务（不发车）”成功后会自动串联一次
`/api/robot-control/nav2/proof/refresh` 与地图预览刷新。该刷新仍是 no-motion planner proof，只检查服务、定位、路线点和图上显示；
不会调用 `/api/nav2/goal/execute`、`NavigateToPose`、`/cmd_vel`、`/api/base/manual` 或 free-roam。这样 operator 点恢复后能直接看到
“服务恢复成功且已重新检查图上路线”，不必在恢复服务和准备路线之间继续猜下一步。

2026-06-29 02:00 起，服务启动/恢复请求本身也进入普通首屏 WYSIWYG：
`/api/robot-control/nav2/start` 未返回时，行程卡状态、按钮和当前事实都显示正在启动或恢复自动驾驶服务，
并明确不会发车、返回前不把旧 stopped/inactive 状态当成已恢复。pending 期间不触发 Nav2 goal execute、manual、
free-roam 或 `/cmd_vel`；只有 start 返回成功后才继续串联 no-motion proof refresh。

2026-06-28 16:10 起，点击执行图上 Nav2 路线后，普通首屏 `当前事实` 也会同步显示
`行程：正在执行图上路线，目标 x=... y=...；人在旁边准备停止`。这与地图终点 marker、路线 polyline 和行程卡片共用同一个
pending 状态；只改变 WYSIWYG 文案，不新增 manual、free-roam、delivery、stop 或 `/cmd_vel` 调用，也不把 pending 状态当成已到达。

2026-06-28 02:36 起，当 Nav2 planner/controller inactive 且 operator 已勾选行程安全确认时，目标进度里的“去行程”
会直接聚焦“恢复自动驾驶服务（不发车）”按钮，而不是停在已禁用的执行/准备按钮。该跳转只移动焦点，不调用
Nav2 start、proof refresh、goal execute、manual、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-28 09:45 起，PC 相机只读诊断把 `first_frame_total_timeout` 纳入首帧失败同类原因：
summary 与 `/api/robot-control/camera/mjpeg/status` 都会把它解释为“相机源没有输出视频帧”。如果同时读到
`source_usage.status=not_in_use` 或 `owner_count=0`，普通首屏显示“不是页面独占，检查 USB/输入/供电或换 known-good UVC”，
而不是泛化成共享预览未知失败。该规则只修正相机状态文案与共享预览状态，不创建额外相机 reader，不发送运动、Nav2、free-roam、
delivery、stop 或 `/cmd_vel`。

2026-06-28 10:05 起，PC summary 的地图雷达 overlay 对 stopped/stale 雷达口径进一步收紧：
即使上位机 `radar/status` 没有填 `lifecycle_running=false`，只要 `lifecycle_state=stopped`，并且 runtime `/scan`
已经 stale，`readback_summary.map.radar_overlay_status` 就降级为 `not_current`，当前地图 overlay 点数置 0，
blocked reasons 带 `runtime_scan_stale_for_map_radar_overlay` 与 `radar_lifecycle_not_running_for_map_radar_overlay`。
旧 `scan_preview_points` 仍可作为 `readback_summary.lidar` 的历史材料解释，但不能再作为“地图上的当前雷达标记”。
该规则只修正只读 summary 和 WYSIWYG 口径，不启动雷达、不刷新地图、不发送运动命令。

2026-06-28 10:35 起，PC summary 的相机只读诊断增加共享预览覆盖兜底：
如果普通首屏短预算下 `/api/camera/health` 超时，但 summary handler 在 600ms source failure 检查或 MJPEG relay
内存里已经拿到 `camera_source_first_frame_failed` 与 `uvc_no_frame_not_exclusive`，`readback_summary.camera.status`
仍保持 `source_first_frame_failed`，并把 `source_diagnosis_*` 透传到普通首屏。这样页面不会在 camera health 慢时从
“不是页面独占，UVC 无帧”退回 `fetch_failed/not_loaded`。该规则只复用 PC Node 已有只读诊断，不创建新 camera reader，
不发送运动、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-28 01:46 起，上位机 free-roam start 合同再次收敛为“自由移动”和“建图验收”两层：
`POST /api/free-roam/autonomy/start` 的运动解锁只看 `confirm_operator_safety` 与
`free_move_ready/free_move_start_ready`，不再把相机首帧或雷达新鲜度误当成低速自由移动硬门禁。
相机首帧、雷达新鲜度和地图画面只决定 `mapping_active_applied`、`mapping_readiness_ready`
和 `mapping_blocked_reasons`；不 ready 时仍可 `mapping_active=false` 启动低速自由移动，回包必须明确
`free_move_blocked_reasons=[]` 与建图缺口。PC 代理同步透传这些字段，方便普通界面直接解释：
车能不能自己低速动，和本轮能不能按建图验收收口，是两件事。

2026-06-28 01:51 起，Nav2 普通首屏的“下一步”文案继续收紧 WYSIWYG：
当旧 `NavigateToPose` action 已经 `succeeded` 但同窗口 wheel raw L/R 仍为 `0/0`，并且当前
`nav2_goal_ready=false`（缺图上路线、路径点或小车 map 坐标）时，页面不再直接提示“勾安全确认后重跑图上路线”。
它必须先提示恢复 Nav2 planner/controller、重新生成图上路线并读到小车地图位置，再让 operator 勾安全确认后用建议模式重跑并复验
wheel raw L/R。只有图上路线和服务都 ready 时，才显示直接重跑路线。该规则只修正 PC summary/首屏引导，
不自动启动 Nav2、不发送 goal、不发布 `/cmd_vel`。

2026-06-28 11:20 起，上述引导的动作顺序按 live 根因再收紧：
当 Nav2 planner/controller inactive 且图上路线也未就绪时，`nav2_goal_next_action` 必须先写“恢复 Nav2 planner/controller”，
再写“生成图上路线并读到小车地图位置”。服务没起来时不应先引导用户准备路线，避免自动驾驶排障顺序反过来。
该改动仍只影响 PC summary/首屏文字，不自动调用 `/api/nav2/start`、goal execute、`/cmd_vel` 或底盘 manual。

2026-06-28 11:35 起，非旧 action 成功分支也使用同一顺序：
只要 summary 看到 `planner_server_inactive` 或 `controller_server_inactive`，并且路线读数未 ready，下一步统一写成
“先恢复 Nav2 planner/controller，再生成图上路线并读到小车地图位置”。页面不再出现“先生成路线；同时恢复服务”的反向顺序。

2026-06-28 13:05 起，结构化 `safe_command_boundary.nav2_goal_blockers` 也按同一操作顺序返回：
`planner_server_inactive/controller_server_inactive` 排在 `path_generation_not_observed`、`path_point_count_not_positive`
和 `robot_map_pose_not_observed` 前面。这样外部脚本、高级诊断和普通首屏都先看到“恢复 Nav2 服务”，
再处理路线和定位读数；该变更只调整只读 summary 顺序，不执行 Nav2、不发送 `/cmd_vel`、不放宽发车安全确认。

2026-06-28 11:50 起，普通雷达刷新/启动后的 WYSIWYG 闭环再收紧：
`refreshRadarProof()` 在完成固定 `/api/robot-control/radar/scan-proof/refresh` 和只读 `/api/robot-control/radar/status`
后，默认立即刷新一次 `/api/robot-control/map/preview`。这样雷达开始或刷新后的地图 marker、雷达点口径和真实地图画面同轮更新；
free-roam start 仍保留自己的建图会话地图刷新，避免重复计数。该路径不发送 manual、Nav2、delivery、stop 或 `/cmd_vel`。

2026-06-28 01:59 起，高级 Nav2 目标预检/执行入口也和普通首屏使用同一个“现场安全确认”：
预检按钮不再需要单独勾“确认仅做导航目标预检”，请求体固定发送兼容字段 `confirm_navigation_preflight=true`；
执行按钮不再维护独立 `confirmNavigationExecution`，而是读取全页面统一的 `plainUnifiedSafetyConfirmed`。
后端仍保留 `confirm_navigation_execution_required` 兜底，直接打 API 没带确认仍会拒绝。这样 UI 上的发车前确认只剩一个勾选，
符合“勾了安全确认即可”的普通用户口径，同时不放宽后端安全门禁。

2026-06-28 15:17 起，上位机 `/api/nav2/status` 会额外只读执行
`o11_nav2_lifecycle.sh status`，返回 `lifecycle_manager.running/state` 以及顶层
`lifecycle_running/lifecycle_state`。该 status 命令只读取受管 Nav2 stack-only manager 的 pid/state，不启动
ROS2、不发送 `NavigateToPose`、不发布 `/cmd_vel`、不碰底盘串口。PC summary 只有在该字段明确
`lifecycle_running=false` 时才把 `safe_command_boundary.nav2_goal_blockers` 首项标为
`nav2_stack_not_running`，并把下一步写成“先启动 Nav2 服务（不发车），再生成图上路线并读到小车地图位置”；
如果 status 读不到 JSON，则保持 `not_loaded`，不误报 stopped。同期 Nav2 最近路线执行摘要新增
`goal_execution_base_feedback_latest_raw_left/right`，和底盘摘要的 wheel raw L/R 同口径，便于现场排查
“旧 action succeeded 但轮速仍 0/0”。这次仍只改变只读诊断和首屏引导，不自动启动 Nav2、不发车。

2026-06-28 15:35 起，`o11_nav2_lifecycle.sh` 修复 stale running 回放：
`ros2 launch ... autonomous.launch.py nav2_stack_only:=true` 退出后会写 `failed/stopped` 并清理 pid 文件；
`status` 发现 pid 不存在时会覆盖旧 running status 文件。现场只读日志确认旧失败根因为
`package 'nav2_bringup' not found`，因此已在车上安装 `ros-humble-navigation2` 和 `ros-humble-nav2-bringup`，
并验证 `ros2 pkg prefix nav2_bringup`、`ros2 pkg prefix navigation2` 均可解析到 `/opt/ros/humble`。
安装依赖不等于发车或 Nav2 HIL 通过；没有现场安全确认前，PC 仍只显示 `自动驾驶服务未启动` 和恢复顺序，不自动调用
`/api/nav2/start`、`NavigateToPose` 或 `/cmd_vel`。

2026-06-29 04:00 现场复核把旧依赖失败和当前自动驾驶失败拆清：
`/api/nav2/start` 只启动 stack-only manager，不发送 `NavigateToPose`、`/cmd_vel`、manual、free-roam 或 delivery；
启动回包和脚本 status 均保留 `motion_requires_explicit_goal_execute=true`、`sends_base_motion_commands=false`。
当前车上 `nav2_bringup` 已存在，Nav2 bringup 可以加载 planner/controller/BT 等组件；但路线仍不能执行，
因为现场日志显示 local costmap 等待 `map -> base_link` 失败，`/api/nav2/status` 仍未证明
`map_to_base_link`、AMCL pose、当前 `/scan` 和 fresh route proof。同期 ESP32 bridge 还出现
`Serial read error ... device disconnected or multiple access on port?`，所以 start 后已立即 stop 释放串口。
本轮同步让 `o11_nav2_lifecycle.sh` 在 start 前显式 preflight `nav2_bringup`，如果依赖再次缺失会写
`failed_missing_dependency` 和安装建议，而不是只把根因埋在 launch log 里。

2026-06-28 15:50 起，普通 PC 行程入口也直接消费 `nav2_stack_not_running`：
当 summary 明确 `nav2_stack_running=false/lifecycle_state=stopped` 时，主执行按钮显示“先启动自动驾驶服务”，
可操作入口显示“启动自动驾驶服务（不发车）”，当前事实条写“自动驾驶服务未启动；先启动自动驾驶服务，再准备图上行程并按地图画面确认”。
planner/controller inactive 仍保留“恢复规划/控制服务”的文案。两者都只调用固定
`/api/robot-control/nav2/start`，成功后自动做 no-motion `/api/robot-control/nav2/proof/refresh` 和地图预览刷新；
不会调用 `NavigateToPose`、`/cmd_vel` 或底盘 manual。

2026-06-28 03:52 起，PC summary 的 `safe_command_boundary.nav2_goal_label/nav2_goal_next_action` 也采用普通用户口径：
`nav2_stack_not_running` 显示“自动驾驶服务未启动 / 先启动自动驾驶服务（不发车）”，planner/controller inactive
显示“规划服务 / 控制服务”。blocker id 仍保留 `nav2_stack_not_running`、`planner_server_inactive`、
`controller_server_inactive` 给自动化和高级诊断使用；改动只影响中文状态文案，不发送 Nav2 start、goal、manual 或 `/cmd_vel`。

2026-06-28 04:07 起，普通首屏的自动驾驶当前事实会把内部诊断词翻成现场口径：
`Nav2 planner/controller` 显示为 `规划服务/控制服务`，`wheel raw L/R` 显示为 `执行窗口轮速 L/R`，
`路线 action 成功` 显示为 `路线结果成功`。高级诊断和 API 字段仍保留原始 token；本变更只修正普通首屏文案，
不启动 Nav2、不执行路线、不发送 manual/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-28 04:20 起，live 若同时读到“旧 PWM 路线结果成功但执行窗口轮速 L/R=0/0”和
`nav2_stack_not_running`，普通行程卡状态优先显示“需恢复 / 先启动自动驾驶服务（不发车）”，
自动驾驶诊断也写成“自动驾驶服务未运行，重跑前先启动”。旧 PWM/ROS 复验建议仍保留为下一步说明，
但不会盖过当前服务未启动这一前置卡点，也不会触发 goal execute、manual 或 `/cmd_vel`。

2026-06-29 起，固定路线 autonomous launch 的默认运动边界也对齐普通用户预期：
`navigation_mode:=fixed_route` 默认 `fixed_route_dry_run:=false`，并且 `enable_visual_gate:=false`。
因此自动驾驶实跑不再被 dry-run 默认值或相机 keyframe gate 卡住；相机无首帧仍影响视觉验收和共享预览，
但不会成为固定路线发车的默认前置门禁。需要软件演练或视觉 gate 时，现场分别显式传
`fixed_route_dry_run:=true` 或 `enable_visual_gate:=true`。该变更只调整 launch 默认参数；
真实发车仍依赖现场安全确认、停止兜底、Nav2 服务、地图、定位和底盘 `/cmd_vel` 链路。

2026-06-29 02:40 起，PC summary 和普通首屏继续细化“自动驾驶为什么不能动”的只读根因：
`latest_map_consumed=false` 会显示为“地图未被自动驾驶服务消费”，
`latest_path_generation_service_available=false` 会显示为“路径生成服务不可用”，
`latest_path_generation_attempted=false` 会显示为“路径生成还没真正开始”。普通首屏下一步会按
“雷达/定位 -> 重新加载地图到自动驾驶服务 -> 恢复路径生成服务 -> 准备图上路线”的顺序展示，
避免现场只看到泛化的“路线未生成”。该变更只读取 `/api/nav2/status` / latest proof 字段，
不启动 Nav2、不执行路线、不发送 manual/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:00 起，PC 普通首屏的 free-roam latest 只读入口会透出上车 runtime 地图指标：
`/api/robot-control/free-roam/autonomy/latest` 从上车 `/api/free-roam/autonomy/latest` 的
`latest_result.map_metrics.free_cells` 和 `latest_result.map_metrics.unknown_ratio` 提取短字段
`map_free_cells`、`map_unknown_ratio`。当地图图片还没加载成功时，扫图覆盖卡优先显示
“runtime 已扫出 N 个可通行格 / runtime 未知区域 X%”，并明确提示这是 latest 的只读指标，
刷新扫图画面后才按图片验收。该变更只执行 GET latest，不启动/停止 free-roam、不发送 manual/Nav2/delivery/stop
或 `/cmd_vel`。

2026-06-29 20:07 起，PC free-roam latest 代理补齐 summary 同口径的结构化字段：
`stop_request_pending`、`start_will_clear_stop_request`、`motion_start_blocked_by_stop_request=false`、
`safety_confirmed`、`mapping_start_ready`、`mapping_start_missing_reasons` 和 `missing_capabilities`。
现场脚本读取 `/api/robot-control/free-roam/autonomy/latest` 时，即使 runtime 当前处于 `stopping/stop_required=true`，
也能明确看到“停止请求会由开始动作先清除，不是自由移动启动阻塞”；相机/雷达缺口继续只影响建图启动或验收。
该变更仍是只读 GET，不启动/停止 free-roam、不发送 manual/Nav2/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:20 起，`/api/robot-control/map/preview` 随图返回的 `radar_overlay` 也执行实时性门禁：
overlay 同轮读取 `/api/free-roam/autonomy/latest`、`/api/radar/status` 和 `/api/radar/scan-proof/latest`。
如果旧 scan proof 有点，但 free-roam runtime `/scan` 已 stale 或 radar lifecycle 是 stopped，overlay 返回
`overlay_status=not_current`，可绘制 `scan_preview_point_count=0`、`scan_preview_points=[]`，同时保留
`scan_preview_source_point_count` 和 `scan_preview_frame_id` 作为诊断。这样刷新地图画面时不会把旧雷达点冒充成当前地图标记；
该变更只做只读 GET，不启动雷达、不刷新 proof、不发送 manual/Nav2/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:40 起，PC 普通首屏和 latest 代理再次收紧 Nav2 完整路线口径：
`/api/robot-control/nav2/goal/execution/latest` 即使读到 `goal_succeeded`，只要同窗口 wheel L/R 非零未证明，
`goal_execution_key_values.nav2_goal_execution_proven=false` 并新增 `execution_proof_gap=wheel_lr_nonzero_not_proven`。
普通地图目标 marker 从“已到达”降级为“到达未证明”，行程卡显示“路线返回成功，真车未证明”，总进度提示重新执行完整行程并确认执行窗口轮速 L/R 非零。
该变更只读取和翻译历史/latest 证据，不执行 Nav2 goal、不发送 manual/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 20:18 起，PC 直连 `GET /api/robot-control/nav2/goal/execution/latest` 也把同一组关键执行事实提升到顶层：
`goal_execution_status`、`result_status`、`nav2_goal_execution_proven`、`execution_proof_gap`、
`goal_execution_robot_control_executed`、`goal_execution_feedback_sample_count` 和
`goal_execution_base_feedback_sample_count`。外部脚本不再需要只读 `goal_execution_key_values` 才能判断
“路线 action 成功但 wheel raw L/R 未证明”；顶层 `robot_control_executed` 仍固定表示 PC latest 本次只读请求没有发车。
该变更只读取和翻译历史/latest 证据，不执行 Nav2 goal、不发送 manual/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 04:40 起，自由移动、键盘手控和 Nav2 重跑共享同一个 bridge-owned UART 反馈读回口径：
`/esp32_bridge` 持有 `/dev/ttyS5` 并持续写
`/root/rober/onboard/runtime/wave_rover_feedback_debug.jsonl`，上位机只读该日志汇总 wheel raw L/R。
这让“小车能不能低速动”的排查不再依赖雷达，也不需要 PC 或 API 为了看轮速抢底盘串口；雷达和相机仍只影响
“能否按建图验收收口”。日志 fresh 时上位机 `base_status` 会跳过 direct `T=130` 串口读；
该日志读回不能把静止 `0/0`、IMU 姿态变化或电压读数升级为 wheel raw L/R 非零证明。

2026-06-29 18:35 起，free-roam 策略进一步收紧“无雷达也能低速自由移动”的执行口径：
近障碍避让只接受新鲜雷达距离；如果 `lidar_age_s` 已超过 `lidar_fresh_timeout_s`，即便旧快照里残留
`lidar_min_distance_m=0.04` 这类近距离值，也只把 `obstacle_clear` 标成 `not_proven`，
不再把策略切到原地避让。这样雷达停止或过期后，旧障碍值不会继续劫持低速自由移动；建图验收仍要求
相机首帧和雷达 fresh，真实运动发布仍要求现场安全确认、停止兜底和 `motion_hil_unlocked + enable_cmd_vel_publish`
双锁。
