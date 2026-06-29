# pc-tools

`pc-tools` 是 rober 的 PC 侧工作站目录，当前主架构是 Node.js + Vue：

```text
pc-tools/workstation/
```

本目录不安装到 Orange Pi，不进入 onboard Docker/Humble 镜像，不直接访问真实硬件、ROS graph、Nav2 runtime、串口设备或云端生产链路。当前 `workstation/` 已从纯只读 proof workstation 进入 **Robot API 控制台 V1**：可以通过 Node 代理读取上位机 Robot API 的 status/latest/readback 短摘要，并把 O6 consumer detail / Mock field evidence 作为 task_id 证据视图；危险动作仍全部 fail-closed。当前默认首屏锁定为面向普通用户的 `Rober 小车控制台`：`.simple-user-console` 只保留“小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航”五个卡片、短状态和少量普通按钮；`Route Debug`、O7、证据、硬件、数据和安全边界等工程入口统一收进默认关闭的 `高级工具`，`source=software_proof` / `proof_status=not_proven` 这类 proof flags 也下沉到高级区。

## 当前入口

- `workstation/`：Node API + Vue UI，是 PC Tools 的主入口。
- `evidence/fixtures/`：保留脱敏 JSON fixture，由 Node API 和 Node 测试读取。
- `route/`：保留 fixed-route 调试说明；实际读取能力在 `workstation/src/server/routeDebugLoader.ts`。
- `training/`、`labeling/`：保留占位目录和后续工作入口，不代表真实训练或标注流水线已接入。

`workstation/` 构建后可直接用 `npm run api` 启动 Node/Express 工作站；默认监听
`0.0.0.0:7001`，方便同局域网设备访问。需要临时换地址或端口时，在启动前设置
`HOST=<host> PORT=<port>`；`api:public` 只是复用 `npm run api` 的兼容旧入口。该 HTTP 入口只暴露 PC
工作站，不会自动执行 Nav2、manual、delivery complete、keyboard pulse、stop 或
`/cmd_vel`。

开发热更新入口用 `npm run dev`，默认监听 `0.0.0.0:7002`，并把 `/api` 代理到本机
Node 工作站 `http://127.0.0.1:7001`。因此开发时先让 `npm run api` 守住 7001，
再打开 7002 看热更新页；`dev:public` 只是复用 `npm run dev` 的兼容旧入口，正式现场访问仍优先使用 7001 的 Node/Express 工作站。

若启动时报 `0.0.0.0:7001: address already in use`，先查
`netstat -anv | rg '[.:]7001 .*LISTEN|7001'`。2026-06-25 起 PC 工作站默认避开
Clash Verge 常用的 `7071`，Node 代码按 `0.0.0.0:7001` 绑定。

## Robot Control Console V1

`workstation/` 默认直接展示 `RobotControlConsolePanel` 和 `GET /api/robot-control/summary?baseUrl=<robot-api-base-url>`，不再把普通控制台放在 tab 导航后面。Vue 不直接跨域访问上位机；Robot API base URL 只交给 Node server 代理。代理只读取 `/api/status`、O3 proof latest、Camera/LiDAR/Base status/latest/readback 类 GET endpoint，并拒绝 unsafe URL、credentials、query/hash、非回环或非 RFC1918 局域网 host、schema drift 和危险 true 字段。为避免真实上位机慢一点的状态聚合被误判成离线，`/api/status`、`/api/camera/health`、`/api/camera/devices` 采用更宽的只读超时窗口；其余 endpoint 继续保持短超时。当前首屏已经回到普通用户可读的简易风格：五个普通卡片只给短状态、少量按钮和可停止入口；前端测试会阻止默认可见首屏再次出现 `检查路径`、`现场材料`、`HIL`、`Nav2`、`proof`、`key values`、`/cmd_vel`、`/api/base/manual`、`可点动`、`task_id`、`O6`、`O7`、`Mock`、`field manifest`。定位重置、导航目标预检、O6 base URL、peer/ICE/SDP、readback table、O3 proof summary、route replay、非 stop 点动、HIL checklist、现场材料和 evidence 细节都收进 `<details>` 折叠区，工程 tabs 只在默认关闭的 `高级工具` 中出现。

`高级诊断` 至少保留 task_id selector、Robot API connection、O3 proof summary、route replay/Mock fallback summary、evidence/keyframe/labeling readiness、manual/nav safe command boundary、Camera/LiDAR/Base readback 七区块。`task_id` detail 通过既有 O6 consumer adapter 获取；本地 field manifest 只作为显式 Mock/field evidence fallback。

所有真实控制入口默认 locked/disabled：`/api/base/manual`、`/cmd_vel`、Nav2 goal、map start、radar start、keyboard control、map click goal。V1 固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，不发布 `/cmd_vel`，不调用 `/api/base/manual`。

Robot Control 现在还包含 `Camera Preview` 卡片，但首屏只显示“打开画面/关闭画面”和一句简单状态；`peer_id`、`ICE`、`SDP`、`cleanup` 和会话细节都收进 `<details>`。Vue 只通过 workstation Node 代理调用 `POST /api/robot-control/camera/offer?baseUrl=<robot-api-base-url>` 和 `POST /api/robot-control/camera/peers/:peerId/close?baseUrl=<robot-api-base-url>`；浏览器不直接访问上位机 `/api/camera/offer` 或 `/api/camera/peers/{peer_id}/close`。代理继承既有 `baseUrl` 安全围栏：仅允许 HTTP、loopback/RFC1918、拒绝 credentials/query/hash，且只暴露 camera offer/close 两个固定路径。当前上位机真实 contract 返回的是顶层 `type/sdp/peer_id` answer，workstation proxy 同时兼容这一路径和设计稿中的嵌套 `answer` 形态。页面默认 `preview_status=idle_not_started`，只在用户显式点击 `打开画面` 后创建 `RTCPeerConnection`、以 `recvonly video` 协商远端视频；发送 offer 前会等待 `iceGatheringState=complete` 或短超时，因为上位机当前按非 trickle SDP 处理，需要 offer 内包含 host candidates。收到远端 track 后优先绑定 `RTCTrackEvent.streams[0]` 到 `data-testid="robot-camera-preview-video"` 的 `<video>`，主动 `play()`，并在高级诊断暴露真实元素的 `srcObject`、`readyState`、尺寸和帧回调/播放质量采样。2026-06-11 15:50 起，前端还会在浏览器本地把该 `<video>` 缩放绘制到临时 canvas，并只在内存里计算 `mean_luma`、`max_luma`、`non_black_ratio_ge16`。普通首屏只允许显示 `已打开 / 画面可见 / 画面偏暗` 这类普通话结论；只有三项指标都过保守阈值才显示 `画面可见`，否则在会话已打开但像素近黑时显示 `画面偏暗`，提示先检查镜头/光线。`sample_status`、`sampled_at`、`sample_attempts`、canvas 尺寸和采样失败原因只留在高级诊断，不会把 `luma`、`canvas`、`peer`、`ICE`、`SDP` 放回首屏。点击 `关闭画面`、切换 `baseUrl`、重复打开或组件卸载时，都会先清理旧 peer。若打开失败，最终 `preview_status` 保留 `start_failed`，不会被 cleanup 覆盖成 `stopped_by_user`。真实浏览器 smoke 必须证明 video 元素绑定、帧流到达和本地亮度采样结论，不能只用 `streaming/live` 或尺寸间接状态替代。即使图传链路活跃，所有控制入口仍保持 disabled，`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 不变。

2026-06-29 起，普通首屏行程卡也会显示 `自动驾驶诊断`：Nav2 stack、规划/控制服务、定位、`/scan`/AMCL/TF 等缺口会直接落在行程操作区，并明确相机/雷达不挡底盘试动或键盘手控。摄像头共享预览继续走 PC 单上游 MJPEG relay，多页面共享同一条流；无首帧时按 UVC/输入/供电排查，不按“页面独占”处理。

同日起，固定路线 autonomous launch 默认按真实 Nav2 路线执行：`navigation_mode:=fixed_route` 时
`fixed_route_dry_run=false`，`enable_visual_gate=false`。这修掉“默认 dry-run / 相机 keyframe gate
导致自动驾驶看起来启动但不动”的配置阻塞；需要软件演练或相机 checkpoint gate 时再显式传
`fixed_route_dry_run:=true` 或 `enable_visual_gate:=true`。PC 侧仍只按 operator 点击固定代理执行，
不会因为刷新页面自动发 Nav2、manual、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 13:38 CST 起，普通用户首屏和只读 Robot Control API 的建图、雷达、自由移动、目标总览文案统一使用“就绪/未就绪”，不再在普通状态句里显示 `ready`。字段名、状态枚举和高级诊断里的技术 token 仍保持兼容；该变化只修正文案，不启动雷达、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 13:48 CST 起，上位机 `GET /api/status` 改为按相机、雷达、地图、Nav2、自由移动和电梯分区并发读取，并给每个区块设置软超时。某个 ROS2/status 区块卡住时，聚合 status 会先返回其他可用事实，并把慢区块标成 `status_section_unavailable/status_section_timeout_*`；顶层聚合也有 fail-closed 超时兜底。完整底盘读数不再阻塞聚合 status，而是显示 `base.status=deferred_to_base_status_endpoint` 并指向独立只读 `/api/base/status`。PC 首屏不会再因为一个只读诊断命令或底盘慢读卡住而把整车状态误判为不可读。该变化只改只读状态聚合，不启动 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 14:55 CST 起，普通首屏实时画面卡在已知 `source_first_frame_failed` / `uvc_no_frame_not_exclusive` 或共享 MJPEG 上游 502/503 时，业务状态直接显示失败原因：不是页面独占，而是 UVC 没有输出视频帧或上游无画面。页面仍保留自动共享 MJPEG `<img>` 和只读共享预览链接，后进页面继续复用同一条上游流并低频重试；该变化只修正 WYSIWYG 状态文案，不新建独占采集、不重启相机、不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 14:00 CST 起，普通首屏 `本轮目标检查` 在存在可现场收口项时，主摘要和 `next_action_plain` 优先指向可操作的运动项，例如“先做：自由自助移动”；相机、雷达和建图仍列在“未就绪项”。这避免摄像头首帧硬件缺口把自由移动、键盘连续手控和完整图上行程复验压到后面。该变化只改只读目标总览排序和文案，不自动勾选安全确认、不启用键盘、不启动自由移动、不执行 Nav2、不发送 `/cmd_vel`。

2026-06-29 15:02 CST 起，普通首屏“下一步选一个”的 `补画面/雷达` 快捷入口改为优先消费 `action_status_cards` 的结构化状态。画面卡是否已显示、地图雷达点是否贴到当前图，不再靠中文文案前缀猜测；即使画面文案从“画面已可见”改成“已经看到画面”，快捷入口也只把真正未完成的雷达点指向雷达卡。该变化只改页面内聚焦和展示，不自动打开画面、不启动雷达、不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

同日起，共享 MJPEG status 请求尚未返回时，首屏会保留 summary 里已有的共享流事实，例如观看页面数、上游是否已连接、是否已有视频边界和最近缓存帧；但仍明确 status 返回前不证明本页已经出图。

2026-06-28 07:35 CST 起，地图画面或地图 proof 刷新中时，行程前确认继续保持最小化：勾选安全确认后只提示等待地图画面/状态刷新，并明确这不是额外预检，而是避免按旧地图发车的所见即所得保护。

2026-06-28 08:50 CST 起，上述提示进一步避免把地图刷新写成“预检步骤”：安全确认完成后，行程前确认只说明地图画面同步完成即可执行，当前等待地图画面/状态刷新属于所见即所得同步，不新增发车前预检，也不会自动执行 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。

2026-06-28 07:49 CST 起，送达最终确认沿用同一口径：地图画面或 proof 刷新中时只提示等待刷新，并明确这是避免按旧地图或旧行程材料确认送达，不是额外送达预检，也不会发车。

2026-06-28 07:54 CST 起，普通首屏启动/恢复自动驾驶服务成功后，不再只写“按地图画面确认路线”；状态会按当前 WYSIWYG 结果给下一步：等待图上路线检查、刷新地图画面确认路线、确认当前地图上的起终点后执行，或继续处理雷达/定位缺口。该恢复动作仍只走固定 `/api/nav2/start` 和 no-motion Nav2 proof refresh，不发 NavigateToPose、不调用 manual/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 02:00 CST 起，普通首屏在自动驾驶服务启动/恢复请求未返回时也会所见即所得：
行程卡、执行按钮和当前事实都会显示“正在启动/恢复自动驾驶服务，不会发车”，并明确返回前不把旧服务状态当作已恢复。
该 pending 状态只覆盖固定 `/api/robot-control/nav2/start` 请求，不会提前调用 Nav2 goal execute、manual、free-roam 或 `/cmd_vel`。

2026-06-29 16:50 CST 起，当路线已经画到地图上、`nav2_goal_ready=true`，但 Nav2 runtime 当前停着时，普通首屏行程卡摘要和行程状态会直接写明“执行会自动启动自动驾驶 runtime”。这只是把既有 managed execute 合同前置到普通用户能看到的位置；仍然必须勾选现场安全确认并显式点击执行按钮，页面刷新不会自动执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-28 07:55 CST 起，如果共享 MJPEG relay 已有最近帧缓存但本页还在接入，首屏“当前事实”会直接提示新页面会先显示最近画面，并继续接入实时流；这不等于本页已证明出图。

2026-06-28 08:15 CST 起，如果相机首帧和雷达都就绪、建图验收只差地图记录，首屏会把下一步写成“启动扫图记录”；这只是建图流程提示，不会自动启动自由移动或发 `/cmd_vel`。

2026-06-28 07:59 CST 起，同一就绪场景下，建图卡主按钮、自动扫图补证按钮和下一步统一显示 `开始扫图记录（不发车）`，键盘/刷新前置提示也显示 `先开始扫图记录`；相机或雷达未就绪时仍保留普通 `开始记录（不发车）`，自由移动入口不被传感器门禁锁死。

2026-06-28 08:04 CST 起，自动扫图/自由移动状态机 stop 成功后，PC 会自动刷新一次停止后的地图画面；刷新成功则直接显示可保存，刷新失败仍保留重试刷新入口。该自动刷新只读 map preview 和 radar status，不发送 manual、Nav2、delivery、free-roam start 或 `/cmd_vel`。

2026-06-28 08:10 CST 起，自动扫图/自由移动 stop 后的首屏“当前事实”也会和地图 marker 同步：停止后的地图画面已刷新时直接提示可以保存地图；刷新失败时提示先重试刷新再保存。该显示只消费 stop 结果和只读 map preview 结果，不发送 manual、Nav2、delivery、free-roam start/stop 或 `/cmd_vel`。

2026-06-28 08:13 CST 起，Nav2/行程执行失败原因里若带 `wheel`、`base_feedback`、`lr_zero`、`L/R=0` 或 `nonzero` 等 wheel raw L/R 线索，普通首屏地图 marker、行程状态和进度会显示 `轮速未响应`，不再泛化为 `执行失败`。这只翻译已有执行回包，不重放 Nav2、不调用 manual/delivery/free-roam/stop 或 `/cmd_vel`。

2026-06-28 08:16 CST 起，本页 MJPEG 共享预览真正出图后，首屏 `当前事实` 会同步显示 `N 个页面共享同一条上游流，不是浏览器独占`。这只消费 PC 共享流 status 和本页 `<img>` load 结果，不新建额外 camera capture、不重启相机、不发送 manual、Nav2、delivery、free-roam、stop 或 `/cmd_vel`。

2026-06-28 08:29 CST 起，PC 共享 MJPEG 响应头也会声明 `X-Robber-Camera-Shared-Capture: single_shared_capture_for_multiple_clients` 和 `X-Robber-Camera-Exclusive-Claim: false`。这样普通页面、抓包和后进浏览器都能直接确认画面是同一个只读共享上游，不是每个页面独占摄像头；该 header 不新增 camera capture、不重启相机、不发送 manual、Nav2、delivery、free-roam、stop 或 `/cmd_vel`。

2026-06-28 08:53 CST 起，普通首屏地图在雷达启动请求未返回时，marker 和扫描范围说明会直接写明“旧点不当新点”；启动中、启动后自动刷新中、启动失败三段都不会把历史雷达点误标成实时地图点。

2026-06-29 14:46 CST 起，普通首屏 `启动雷达` 或 `重启雷达` 成功后，会显式连续刷新 no-motion scan proof 和同轮 `/api/robot-control/map/preview`。地图 marker 只消费这次地图预览返回的 `radar_overlay`：有 map-frame 小车位置和 overlay 点时显示已贴到地图的雷达点；没有点数组或没有定位时继续显示局部点/最近距离并说明未贴图。该链路只刷新雷达 proof 和只读地图预览，不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 起，雷达停止请求未返回时，地图只保留“雷达停止请求中”marker，不再画实时扫描范围占位，也不显示最近距离读数；返回前不证明雷达已停止，也不把旧点当作停止后的地图点。该展示不触发 manual、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-28 08:57 CST 起，PC 屏幕方向键的普通说明明确写出拖出按钮也会停；测试锁定 `pointerleave` 会走固定 stop 代理，和松开、触控取消、窗口失焦、页面隐藏同一停止边界。

2026-06-28 09:03 CST 起，Nav2 图上路线执行请求未返回时，普通首屏会把自由移动、扫图记录、自动扫图和自由移动键盘入口统一锁成 `行程中`，下一步提示等待行程返回或先停止行程；即使按钮事件被强行触发，也不会调用 map start 或 free-roam autonomy start。

2026-06-28 09:26 CST 起，PC summary 与普通首屏的行程口径对齐：只要路线已生成且点数大于 0，`nav2_goal_ready` 不再因为小车地图位置未显示而变成 false；页面仍会建议先重新定位或刷新地图，但这不再是发车前硬挡。真正执行仍必须勾现场安全确认，并走固定 `/api/robot-control/nav2/goal/execute`。

2026-06-28 09:38 CST 起，普通首屏 `连接/刷新` 会同时刷新共享 MJPEG 画面状态、地图画面和雷达只读状态；画面卡里的观看人数、上游连接、最近失败和缓存帧不再停留在旧读数。该刷新只调用只读 `/api/robot-control/camera/mjpeg/status`，不会新建 camera offer，不发送 manual、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-28 08:24 CST 起，轮速卡的 `试动读轮速` 普通入口不再因为缺现场画面材料而卡住：first-jog 材料足够时仍走固定 first-jog；材料不足但已勾现场安全确认时，退到已有固定底盘试动入口读取 wheel raw L/R。画面只影响旧 first-jog 材料和建图验收，不再作为底盘试动或轮速读取前置；该入口仍走 workstation `/api/robot-control/base/manual` 固定代理，不直连 `/cmd_vel`。

2026-06-29 17:10 CST 起，当主体状态已读到但 `base_status` 或 `base_feedback_samples_latest` 只读端点超时、返回格式异常或读取失败时，普通首屏 `当前事实` 会把它显示成轮速分项问题：“当前底盘反馈读取超时 / 返回格式异常 / 读取失败；旧 L/R 不能当当前轮速结论”。这不会暴露 `fetch_timeout_*`、`response_json_parse_failed` 等内部 token，也不会自动发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 17:50 CST 起，`GET /api/robot-control/summary` HTTP route 不再用全局 2.4s 覆盖相机/底盘慢读窗口；`/api/base/status`、`/api/base/feedback-samples/latest` 和 `/api/camera/health` 继续使用各自端点级预算，避免直连上位机合法 JSON 在 PC 汇总层被误报为 timeout/bad readback。free-roam summary 同时把 `external_stop_requested=true` 单独显示成停止请求，不再让雷达 stale 看起来像“车不能动”；雷达和相机只影响建图验收，低速自由移动仍看现场安全确认和停止兜底。Nav2 行程仍按上次执行窗口拆开显示：PWM/ROS/speed 模式、非零底盘命令、wheel raw L/R 和 IMU 姿态变化分开呈现，当前 live 形态应归因到“PWM 已发命令但 T=1001 L/R 未非零，下一次按 ROS 重跑复验”，不是相机或雷达阻塞。

2026-06-29 18:10 CST 起，`/api/camera/devices` 也使用 camera 慢读预算。该端点只做 v4l2/UVC 枚举，不创建 preview、offer 或 capture；并发 summary 刷新时即使设备枚举慢一拍，也不能把已经有 `camera_health.source_diagnosis=uvc_no_frame_not_exclusive` 的页面写成整车连接 degraded。普通用户仍看到“不是页面独占，检查 USB/输入/供电或换 known-good UVC”，不会因此发 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 18:30 CST 起，地图雷达点的下一步同时返回机器 token 和普通用户白话：`radar_overlay_next_action_plain` / `next_action_plain` 会把启动雷达、刷新雷达扫描、刷新定位、刷新地图画面等动作写成可执行短句。普通首屏优先显示白话字段，旧响应缺字段时才本地翻译 token，避免 live 的 `start_radar_then_refresh_map_preview`、`refresh_radar_scan_for_map_overlay` 等内部名字回到用户界面。该变化只修正只读 summary/map preview 和 UI 文案，不自动启动雷达、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 18:50 CST 起，相机共享预览的下一步也同时返回 token 和普通用户白话：Robot Control summary 与 `/api/robot-control/camera/mjpeg/status` 新增 `preview_next_action_plain` 和 `source_diagnosis_next_action_plain`。当 live 状态是 `uvc_no_frame_not_exclusive` 时，普通首屏和只读接口直接显示“检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占”，不再把 `check_usb_camera_input_power_or_known_good_uvc` 暴露给普通用户。该变化只读 camera health/relay status，不新建额外 capture、不重启相机、不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 14:22 CST 起，普通首屏的共享 MJPEG `<img>` 预览与 WebRTC 自动连接抑制解耦。用户点击“关闭画面”仍会释放本页 WebRTC peer，但只读共享 MJPEG 入口继续按 `cameraMjpegSharedPreviewVisible` 展示和低频重试；后来打开页面的用户仍会接入同一条 PC Node 上游流，而不会因为某个页面手动关闭 peer 就看不到共享预览。该变化只影响浏览器展示和只读 MJPEG GET，不新建额外摄像头采集、不发 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 19:10 CST 起，自动驾驶行程边界也新增白话下一步：`safe_command_boundary.nav2_goal_next_action_plain` 会把 `wheel raw L/R`、`ROS/PWM/SPEED` 和 `controller` 等工程词翻译成“执行窗口轮速 L/R”“ROS 模式”和“控制服务”。live 上旧行程 action 成功但 L/R 仍为 `0/0` 时，summary 会同时保留工程字段和普通字段，普通首屏优先用普通字段说明下一步是勾安全确认后重跑图上路线，并确认同窗口轮速非零；相机和雷达仍不会被写成自动驾驶阻塞。该变化只修正只读 summary/UI 文案，不执行 Nav2 goal、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 19:30 CST 起，自由移动 readback 也带白话下一步：`readback_summary.free_roam.next_action_plain` 与 `safe_command_boundary.free_roam_autonomy_next_action` 对齐。外部脚本或普通首屏只读 `readback_summary.free_roam` 时，也能直接看到“勾选现场安全确认后可先自由移动；建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面”，不会再出现 `status=start_ready` 但下一步为空。该变化只补只读 summary 字段，不启动自由移动、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

2026-06-29 19:50 CST 起，键盘连续手控 summary 增加 teleop alias：`safe_command_boundary.keyboard_teleop_start_ready`、`keyboard_teleop_status` 和 `keyboard_teleop_next_action_plain` 镜像既有 `keyboard_control_*` 字段。普通脚本或外部面板按 teleop 叫法读取时，也能直接看到“勾安全确认后启用键盘，按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停”。该变化只补只读字段，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。

2026-06-29 20:10 CST 起，地图预览响应也在顶层返回 `robot_pose_status`。`/api/robot-control/map/preview` 如果同轮 overlay 读到 map-frame 小车位置，会返回 `map_pose_observed`；否则返回 `not_observed`。外部脚本不用再自行判断 `robot_pose` 是否为 null，就能一眼知道图上小车位置是否可见。该变化只补只读 map preview 字段，不刷新定位、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 20:30 CST 起，地图预览响应顶层也返回 `path_preview_status`。`/api/robot-control/map/preview` 同轮读到当前路线点时返回 `path_preview_observed`，否则返回 `not_observed`。这样外部脚本可以直接判断“图上路线是否可见”，再结合 `robot_pose_status` 和 `radar_overlay_status` 做 WYSIWYG 验收。该变化只补只读 map preview 字段，不准备路线、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 20:50 CST 起，地图预览响应顶层新增 `path_preview_next_action_plain`。路线和小车位置都可见时返回“确认起点、终点和路线后，再勾选安全确认执行”；路线不可见时返回“先准备图上路线，再刷新地图画面”；路线可见但小车位置不可见时提示刷新定位或地图。该变化只补只读 map preview 下一步文案，不准备路线、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 21:10 CST 起，地图预览响应顶层 `next_action_plain` 与 `path_preview_next_action_plain` 对齐。外部脚本或普通面板只读取统一下一步字段时，也能直接看到“先准备图上路线 / 路线已显示但小车位置未显示 / 确认起点终点和路线后再勾选安全确认执行”。雷达贴图仍使用独立的 `radar_overlay_next_action_plain`，避免把路线确认和雷达刷新混成一个动作。该变化只补只读 map preview alias，不准备路线、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 21:30 CST 起，Robot Control summary 的 `readback_summary.map` 也返回 `path_preview_status`、`path_preview_point_count`、`path_preview_frame_id` 和 `path_preview_next_action_plain`。这样普通首屏或外部脚本只读 summary，就能同时看到地图质量、图上路线、雷达贴图和小车 map 位姿状态；不必从 `readback_summary.nav2` 手动拼路线点数，也不必额外调用 map preview 才知道路线是否所见即所得。该变化只补只读 summary 字段，不准备路线、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 08:36 CST 起，`safe_command_boundary.nav2_goal_label` 也消费同一份所见即所得路线事实：只有路线读数就绪 但地图还没显示路线时保留“路线读数已准备，等待地图画面确认”；地图上已显示路线时显示“图上路线已显示，等待安全确认”；路线和小车位置都可见时显示“图上路线和小车位置已显示，等待安全确认”。该变化只修正只读 summary label，不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 21:50 CST 起，`/api/robot-control/camera/mjpeg/status` 也返回与 summary 对齐的共享预览别名：`shared_preview_client_count`、`shared_preview_upstream_active`、`shared_preview_content_type_loaded`、`shared_preview_cached_frame_loaded`、`shared_preview_cached_frame_age_ms`、`shared_preview_shared_capture`、`shared_preview_exclusive_camera_claim`、`shared_preview_contract` 和最近失败字段。独立相机状态接口现在也能直接证明“多个页面共享同一条上游流，不是浏览器独占”，不会再让只读 `shared_preview_*` 的脚本拿到 null。该变化只补本机 relay 只读状态，不新开 camera capture、不重启相机、不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 04:30 CST 起，Robot Control summary 的 `readback_summary.camera` 与
`/api/robot-control/camera/mjpeg/status` 同步新增更直观的共享预览别名：`viewer_count`、`upstream_connected`
和 `has_recent_frame`。它们分别镜像 `client_count/shared_preview_client_count`、`upstream_active` 和
`cached_frame_loaded`，方便普通脚本直接判断“几个页面在看、是否连着同一条上游、是否已有最近帧”。该变化只补只读状态，
不创建 MJPEG client、不重启相机、不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 04:37 CST 起，`GET /api/robot-control/summary` 顶层新增 `current_fact_plain`。该字段把本轮只读
readback 中的画面、地图、地图雷达点、Nav2 路线复验、键盘连续手控、自由移动和建图 readiness 合成一段普通话事实；
连接失败时也会直接说明未读到当前事实。它只消费同一轮 summary 内部字段，不额外请求上位机、不准备或执行 Nav2、
不启用键盘、不启动 free-roam、不发送 manual、delivery、stop 或 `/cmd_vel`。

2026-06-29 16:40 CST 起，`GET /api/robot-control/summary` 的 `readback_summary.nav2.planner_server_active`、`controller_server_requested` 和 `controller_server_active` 会优先消费 O11 `nav2_goal_execution_latest.latest_result.managed_runtime.lifecycle_ready`。这样完整 NavigateToPose 执行 artifact 已证明 controller 在本轮托管 runtime 中被请求并 active 时，不会再被 O10 planner-only proof 或旧 lifecycle 读数误写成“控制服务未运行”。这只修正只读证据合并和下一步判断；仍然要求下一次勾选行程前安全确认后用 ROS 模式重跑，并用同窗口执行窗口轮速 L/R 非零证明自动驾驶真正带动车。

2026-06-30 09:30 CST 起，`GET /api/robot-control/summary` 顶层新增 `action_status_cards[]`，把画面、地图、地图雷达点、图上路线、键盘手控、自由移动和建图启动拆成结构化状态卡。普通首屏在当前事实下方直接展示“已显示/未显示/可启用/可启动/未就绪”、下一步、是否需要安全确认、是否影响建图以及是否不挡自由移动；前端仍把“路线”翻译成“行程”，不把 `marker/overlay` 放回普通首屏。该字段只派生同一轮只读 summary，不新增按钮，不启动雷达/建图/自由移动，不执行 Nav2，不发送 manual、keyboard、delivery、stop 或 `/cmd_vel`。

2026-06-29 22:10 CST 起，键盘连续手控 summary 增加普通用户白话字段：`keyboard_hold_to_move_plain`、`keyboard_stop_triggers_plain` 和 `keyboard_pulse_timing_plain`。外部脚本或普通面板只读 summary 时，可以直接展示“必须按住才移动；只启用键盘不发车；松开/失焦/切页/换方向/点停止都会停；按住时约每 0.26 秒发送一次 0.24 秒低速脉冲”。该变化只补只读安全边界说明，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。

2026-06-29 22:30 CST 起，`readback_summary.nav2` 增加 `execution_status_plain` 和 `next_action_plain`。外部脚本只读 Nav2 区块时，也能直接看到“上次路线结果成功但执行窗口轮速 L/R=0/0 未非零；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或控制服务；下一步勾安全确认后用 ROS 模式重跑图上路线并同窗口确认轮速 L/R 非零”。该变化只补只读 readback summary 文案，不执行 Nav2 goal、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 22:50 CST 起，`readback_summary.free_roam` 把下一步拆成 `motion_next_action_plain` 和 `mapping_next_action_plain`。脚本只读 free-roam 区块时也能直接区分：“勾安全确认后可先自由移动；相机和雷达只影响建图验收”和“建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动”。该变化只补只读 summary 文案，不启动自由移动、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

2026-06-29 23:10 CST 起，相机共享预览的默认只读口径改为“页面会自动接入共享 MJPEG 预览”。`/api/robot-control/summary` 和 `/api/robot-control/camera/mjpeg/status` 在 idle 状态下返回 `preview_next_action=auto_join_shared_mjpeg_preview`，普通页面、脚本和后进浏览器都能直接理解：谁打开页面都会复用同一条上游 MJPEG 流；未出帧前不能把黑框当作画面可见，若仍无画面再点只读检查复测首帧。该变化只修正 PC 共享预览 readback，不新开独占采集、不重启相机、不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 02:35 CST 起，`safe_command_boundary` 增加最小门禁白话字段：`nav2_goal_minimal_precheck_plain`、`keyboard_minimal_precheck_plain`、`free_roam_motion_minimal_precheck_plain` 和 `free_roam_mapping_acceptance_plain`。脚本只读 summary 时可以直接知道：执行图上路线只复核现场安全确认和固定白名单；键盘启用本身不发车，只有按住方向键/WASD 才发低速短脉冲；自由移动只要求安全确认和停止兜底；画面首帧、雷达新鲜、地图记录和地图画面只影响建图验收。该变化只补只读 summary 字段，不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 02:42 CST 起，`readback_summary.map` 增加 `map_wysiwyg_status_plain` 和 `map_wysiwyg_next_action_plain`。只读 summary 会把地图图片、图上路线、小车 map 位置和地图雷达点合成一个普通用户可读总判断：例如 live 形态“地图画面、图上路线和小车位置已显示；雷达来源点存在但当前不贴到地图：已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图”。这样脚本不用拼多个字段就能判定地图雷达点是否真正所见即所得。该变化只补只读 map summary，不启动雷达、不刷新地图、不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 02:48 CST 起，`readback_summary.keyboard` 直接返回键盘连续手控 readback：`status/start_ready/enabled/control_mode/manual_command_mode/manual_proxy_endpoint/stop_proxy_endpoint` 以及按住才移动、停止触发、脉冲节奏、下一步和最小门禁白话。外部脚本不用再从 `safe_command_boundary` 拼键盘事实，也能直接知道“启用键盘不发车，只有按住方向键/WASD 才发送 ROS 低速短脉冲”。该变化只补只读 summary 字段，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。

2026-06-29 02:54 CST 起，`readback_summary.nav2` 增加 `goal_execution_wheel_raw_lr_status_plain` 和 `goal_execution_wheel_raw_lr_next_action_plain`。2026-06-29 08:24 CST 起，这两个 plain 字段内容统一使用“执行窗口轮速 L/R”，字段名保留旧接口以兼容脚本。外部脚本只关心完整路线执行验收时，不需要从长句里解析 `execution_status_plain`；可以直接读取“上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零；已看到非零底盘命令，IMU 姿态有变化”以及“勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零”。该变化只补只读 Nav2 readback 字段，不执行 Nav2 goal、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:00 CST 起，`readback_summary.free_roam` 增加 `motion_readiness_plain` 和 `mapping_readiness_plain`。前者只回答“能否先低速自由移动”，例如“可先自由移动；只需要现场安全确认和停止兜底”；后者只回答“能否按建图验收”，例如“建图验收未就绪；还差：画面首帧、雷达新鲜、地图记录、地图画面；不影响先低速自由移动”。普通首屏自由移动/建图事实和上车建议优先使用这两个短字段，避免把相机/雷达缺口误写成车不能动。该变化只补只读 summary/UI 文案，不启动 free-roam、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

2026-06-30 08:36 CST 起，`readback_summary.free_roam` 与 `safe_command_boundary` 增加建图启动专用字段：`mapping_start_ready`、`mapping_start_missing`、`mapping_start_readiness_plain`、`mapping_start_next_action_plain`、`free_roam_mapping_start_ready`、`free_roam_mapping_start_missing_reasons`、`free_roam_mapping_start_plain` 和 `free_roam_mapping_start_next_action`。这些字段只回答“相机首帧和雷达新鲜是否足够启动建图记录”；旧 `mapping_ready/free_roam_mapping_ready` 仍表示“建图验收是否完成”，继续要求地图记录和地图画面。该变化只补只读 summary 字段，不启动 free-roam、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

2026-06-30 08:49 CST 起，普通首屏会把 `建图启动` 和 `建图验收` 两层同时展示在 `当前事实` 与自由移动/建图卡片：相机首帧和雷达新鲜 就绪时提示可启动扫图记录；地图记录和地图画面仍只用于建图验收。旧 7001 或旧 fixture 没有 `mapping_start_*` 时，页面按当前画面/雷达事实 fallback。该变化只改只读展示，不自动启动建图、不启动自由移动、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:47 CST 起，`/api/robot-control/free-roam/autonomy/latest` 顶层也返回自由移动和建图 readiness：`free_move_start_ready`、`motion_ready`、`mapping_readiness_ready`、`mapping_blocked_reasons`、`motion_readiness_plain`、`mapping_readiness_plain`、`motion_next_action_plain` 和 `mapping_next_action_plain`。外部脚本只读 latest endpoint 时即可看到“可先自由移动；相机和雷达只影响建图验收”以及“建图验收还差哪些材料”，不必解析 `latest_key_values.mapping_missing`。该变化只读 runtime artifact，不启动 free-roam、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

2026-06-29 04:12 CST 起，`/api/robot-control/free-roam/autonomy/latest` 额外返回 `free_move_start_status_plain`、`motion_runtime_status_plain` 和 `mapping_acceptance_status_plain`。这三个字段把“能不能启动自由移动”“当前是否已经在发布低速运动”和“建图是否可验收”拆开；当 `free_move_start_ready=true` 但 `motion_ready=false` 时，接口会明确说明 `motion_ready=false` 只表示尚未开始发布运动，不是启动阻塞。该变化只补只读 latest 响应，不启动 free-roam、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

2026-06-29 04:18 CST 起，普通 PC 首屏的 `刷新自由移动状态（只读）` 摘要优先展示 `free_move_start_status_plain`、`motion_runtime_status_plain` 和 `mapping_acceptance_status_plain`。现场点击只读刷新后，不用打开高级 JSON 也能看到“自由移动可启动”“当前未发布运动不是启动阻塞”“建图验收未就绪 但不阻止低速自由移动”。该变化只改前端只读展示，不启动 free-roam、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:08 CST 起，`readback_summary.map` 增加所见即所得短别名：`robot_pose_status`、`radar_overlay_point_count`、`radar_overlay_source_point_count` 和 `radar_overlay_frame_id`。这些字段完全复用既有 `radar_overlay_robot_pose_status` / `radar_overlay_scan_preview_*` 事实，方便外部脚本直接判断“图上小车是否可见、当前地图雷达点真正画了几个点、旧雷达来源点是否只作诊断”。该变化只补只读 summary alias，不刷新地图、不启动雷达、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:31 CST 起，`readback_summary.map` 增加 `radar_overlay_wysiwyg_status_plain` 和 `radar_overlay_wysiwyg_next_action_plain`。脚本和普通首屏不用再把 `radar_overlay_point_count=0` 与 `radar_overlay_source_point_count=81` 自己拼起来；live 形态会直接显示“地图雷达点未贴到当前地图：当前显示 0 个点；旧来源点 81 个只作诊断”，下一步仍是“先启动雷达，再刷新地图画面”。该变化只补只读地图/雷达贴图诊断，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 04:05 CST 起，`/api/robot-control/radar/status` 顶层返回雷达本体和地图雷达点验收白话：`continuous_scan_status`、`lifecycle_running`、`lifecycle_state`、`latest_scan_proof_fresh`、`scan_point_count`、`latest_scan_age_ms`、`radar_status_plain`、`radar_next_action_plain`、`radar_overlay_point_count`、`radar_overlay_source_point_count`、`radar_overlay_wysiwyg_status_plain` 和 `radar_overlay_wysiwyg_next_action_plain`。其中 radar status 只证明雷达本体；地图雷达点是否所见即所得仍以 `/api/robot-control/map/preview` 的 `radar_overlay_point_count` 和 WYSIWYG 文案为准。该变化只补只读 radar status 字段，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:36 CST 起，`/api/robot-control/map/preview` 的 `radar_overlay` 嵌套对象和顶层 alias 也返回同一组 WYSIWYG 白话：`wysiwyg_status_plain`、`wysiwyg_next_action_plain`、`radar_overlay_wysiwyg_status_plain`、`radar_overlay_wysiwyg_next_action_plain`。外部脚本只看地图预览响应时，也能直接确认“地图上实际画了几个地图雷达点”和“旧来源点是否只作诊断”。该变化只补只读 map preview 合同，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:58 CST 起，`/api/robot-control/map/preview` 顶层同步返回与 summary 同名的雷达数值 alias：`radar_overlay_point_count`、`radar_overlay_source_point_count`、`radar_overlay_scan_preview_point_count` 和 `radar_overlay_scan_preview_source_point_count`。外部脚本不用再把 `radar_overlay.count/source_count/scan_preview_*` 自己转换成 summary 口径；当前地图真正显示几个 marker 和旧来源点数量都能直接读取。该变化只补只读 map preview 字段，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:15 CST 起，`readback_summary.camera` 增加 `preview_visible_status`、`preview_visible_plain`、`camera_wysiwyg_status_plain` 和 `camera_wysiwyg_next_action_plain`。脚本不用再从 `preview_status=idle_not_started` 和 `source_diagnosis_status=uvc_no_frame_not_exclusive` 拼判断；可以直接看到“当前没有实时画面；不是页面独占，UVC 设备没有输出视频帧”或“画面已可见：共享实时画面已有缓存帧”。该变化只补只读 summary 字段，不新开独占采集、不重启相机、不发送 manual/keyboard/Nav2/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:41 CST 起，`/api/robot-control/camera/mjpeg/status` 也返回同一组画面 WYSIWYG 字段：`preview_visible_status`、`preview_visible_plain`、`camera_wysiwyg_status_plain` 和 `camera_wysiwyg_next_action_plain`。只读 camera status 现在能直接说明“当前有共享缓存帧可见”或“当前没有实时画面；不是页面独占而是 UVC 无首帧”，不必再旁路读取 summary。该变化只消费本机 MJPEG relay 状态和只读 camera health，不创建 MJPEG client、不打开额外 camera stream、不发送 manual/keyboard/Nav2/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:19 CST 起，`readback_summary.nav2` 增加 `route_execution_readiness_plain` 和 `route_execution_precheck_plain`。外部脚本只读 Nav2 区块时，可以直接看到“图上路线可重跑复验；上次路线结果成功但同窗口轮速 L/R=0/0 未非零”和“只需勾选行程前安全确认；相机、雷达和 operator report 不作为额外发车前置；执行会用 ROS 模式跑图上路线”。该变化只补只读 summary 字段，不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:53 CST 起，`/api/robot-control/nav2/goal/execution/latest` 顶层也返回 `route_execution_readiness_plain`、`route_execution_precheck_plain`、`goal_execution_wheel_raw_lr_status_plain` 和 `goal_execution_wheel_raw_lr_next_action_plain`。脚本直接读取 latest endpoint 时，也能看出完整路线是否已证明、发车前只需勾选安全确认，以及 action 成功但执行窗口轮速 L/R 仍为 `0/0` 时下一步用 ROS 模式重跑图上路线复验。该变化只补只读 latest 响应，不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

2026-06-29 03:24 CST 起，`readback_summary.keyboard` 增加 `readiness_plain` 和 `continuous_control_contract_plain`。外部脚本不用再从 `start_ready/enabled/hold_to_move/stop_triggers/pulse_timing` 多字段拼判断，可以直接显示“可启用键盘；启用本身不发车，按住方向键/WASD 才连续低速移动”和“按住时约每 0.26 秒发送一次 0.24 秒 ROS 低速脉冲；松开、失焦、切页、换方向或点击停止都会停”。该变化只补只读 summary 字段，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。

2026-06-11 15:15 起，Robot Control 继续保持普通用户简易首屏不变，但上位机
`GET /api/radar/status` 的只读合同更精确了：除了既有 latest scan proof 状态，还会额外
只读 `o1_lidar_lifecycle.sh status`，输出 `lifecycle_status`、
`lifecycle_running`、`lifecycle_state`、`lifecycle_pid`、
`continuous_window_observed`、`continuity_window_status`、
`continuity_blocked_reasons`。当 lifecycle 正在运行且 latest proof 四项观测齐全、
artifact freshness 为 `fresh` 时，`continuous_scan_status` 会返回
`latest_proof_fresh_while_lifecycle_running`，说明“当前连续窗口已观察到 lifecycle
running + fresh proof”，避免 UI 再误报“雷达根本没跑起来”。这仍然只是只读雷达证据，
不是运动许可；`safe_to_control=false`、`primary_actions_enabled=false`、
`robot_control_executed=false`、`delivery_success=false` 保持不变。

2026-06-11 15:25 起，workstation 也真正消费了这组字段：`robotControlSummary.ts`
会把 `continuous_scan_status`、`lifecycle_running`、`lifecycle_state`、
`continuous_window_observed`、`continuity_window_status`、`latest_scan_proof_fresh`
压到 `readback_summary.lidar` 和 radar refresh `latest_readback_key_values`。
普通用户首屏雷达卡只显示 `雷达已运行 / 雷达未运行 / 刷新中 / 刷新失败`，不会把
`proof`、`HIL`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、
`启动雷达`、`停止雷达` 放回默认可见首屏；完整 continuity/lifecycle 细节继续留在
默认关闭的 `高级诊断`。

Robot Control 也已经接入 Radar/Map proof refresh V2。Vue 通过 workstation Node 固定 POST 代理调用 `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=<robot-api-base-url>` 和 `POST /api/robot-control/map/proof/refresh?baseUrl=<robot-api-base-url>`，上位机 body 分别固定为 `{ timeout_s: 20, runtime_warmup_s: 15, start_runtime: true }` 与 `{ timeout_s: 45 }`。Radar body 使用更长的真实冷启动 no-motion 证据窗口，给 LiDAR driver、raw packet、scan hz 和 TF 同时稳定的时间；这不开放浏览器自定义参数，也不改变 vendor/hardware facts。这两个动作只刷新 no-motion 证据窗，允许出现 `sends_commands=true`、`starts_ros2=true` 这类证据级 helper 行为，但首屏只显示“刷新雷达/刷新地图”、一个短状态和 `scan/tf` 或 `map/evidence` 的人话摘要；`latest_readback_key_values`、`non_motion_evidence_actions`、`hard_dangerous_true_fields`、`last refreshed time` 和 blocked reasons 都收进高级诊断区。它仍然不会打开 `/cmd_vel`、`/api/base/manual`、Radar start、Map start、Nav2 goal、keyboard control 或 map click goal；动作结束后会自动回刷 Robot Control summary。只有 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`robot_control_executed=true`、`command_dispatch_enabled=true`、`manual_control_enabled=true`、`navigate_goal_enabled=true`、`keyboard_control_enabled=true`、`sends_motion_commands=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`opens_base_uart=true`、`uses_base_uart=true`、`hil_pass=true` 等硬危险 true 字段才会 fail closed。

2026-06-11 12:45 clean-baseline refresh 继续只通过本机 PC proxy `http://127.0.0.1:18788`
触发真实上位机 `http://192.168.1.11:8787` 的 radar/map proof refresh。artifact 位于
`sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/artifacts/`。
本轮 radar proxy 返回 `scan_once_observed=true`、`scan_hz_observed=true`、
`raw_packet_once_observed=true`、`tf_observed=true`，`hard_dangerous_true_fields=[]`；
direct latest readback 里的 `latest_result.generated_at=2026-06-11T05:06:46.418393Z`
晚于本轮 `run_started_at=2026-06-11T05:05:22.613Z`，证明不是旧 radar proof。
2026-06-11 13:35 起，radar latest/refresh/status 合同补齐独立 evidence ref：
若 LiDAR artifact 自带 `evidence_ref` 则保持原值，否则从 `generated_at_ms`
稳定派生 `o1-lidar-scan-proof-<generated_at_ms>`，旧 ISO `generated_at` 则派生
安全可读 ref；artifact 缺失、坏 JSON 或根节点非 object 时不伪造成功 ref。
PC proxy 的 `last_result_evidence_ref` 会直接读取上位机 refresh 回包的
`evidence_ref/latest_evidence_ref`。Map proxy 返回
`map_once_observed=true`、`map_file_observed=true`、`map_metadata_observed=true`，
`evidence_ref=o3-map-lifecycle-1781154452321`，direct latest `generated_at_ms`
晚于本轮开始时间，且 `safe_to_control=false`、`delivery_success=false`、
`primary_actions_enabled=false`、`robot_control_executed=false`、
`sends_motion_commands=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`uses_base_uart=false`。cleanup readback 显示本机 18788 已停止，上位机 helper
无残留，`/dev/ttyS5` 与 `/dev/ttyACM0` 无 `lsof`/`fuser` 占用。

Robot Control 的 `检查路径（高级）` 只在默认关闭的高级诊断中出现。它通过固定代理调用上位机 `/api/nav2/proof/refresh`，body 固定为 managed no-motion path proof：`timeout_s=30`、`managed_runtime_opt_in=true`、`managed_timeout_s=30`、`managed_map_yaml=/root/rober/onboard/runtime/maps/trashbot_map.yaml`、`initialpose_opt_in=true`、`initialpose_x/y/yaw=0`、`path_generation_opt_in=true`、`path_generation_timeout_s=30`、默认目标点 `map:(0.8,0,0)`。30s 是 clean-baseline direct Robot API 在同一 no-motion contract 下实测稳定窗口：20s 首轮可能 timeout，30s 可 fresh pass。2026-06-12 起，上位机 helper 会读取当前 map yaml/PGM 的 bounds；如果默认 start/goal 已被新地图裁剪到地图外，只在 planner-only proof 中把 start/goal 夹到地图内侧，并在 `path_goal_request.map_goal_diagnostics` 中保留原始点、地图范围和 `map_bounds_adapted_no_motion_planner_probe`。最新真实上位机复测观测到 `path_generated=true`、`path_point_count=30`、`root_causes=[]`，同时记录当前 `trashbot_map` 没有 free cell 且原始 `(0,0)->(0.8,0)` 在 map bounds 外。2026-06-25 起，上位机 helper 会把 managed runtime 的 planner 节点观测提升为 `planner_server_observed/managed_runtime_wait_result`，当 lifecycle CLI 在板端超时时，允许 no-motion `ComputePathToPose` 自己给出成功、action unavailable 或 timeout 证据，但仍不允许 controller/BT/NavigateToPose。2026-06-11 19:45 起，workstation fetch timeout 按固定 body 加 60s 余量计算并由 150s cap 封顶；上位机 helper cap 为 132s，fixed body 的 120s raw 预算不会被 upper wrapper 截断，且 PC proxy 等待窗口明确更长。这个动作只允许上位机拉起 no-motion ROS2 证据 runtime、发布一次 `/initialpose` 并调用 planner 计算接口；它不是 NavigateToPose，不调用 `/api/nav2/start` 或 `/api/nav2/stop`，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 `/dev/ttyS5`，不代表真实运动或 delivery success。普通首屏仍不得出现 `检查路径`、Nav2/proof/key-values、`/cmd_vel` 或 `/api/base/manual`。

2026-06-11 10:35 真实 PC proxy gate smoke 继续证明非 stop 手动点动必须 fail closed。
当前真实上位机 `/api/operator/report` 已确认现场有人、周围清空和急停准备，但仍缺
`external_video_recorded`、`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`
和 `physical_motion_lidar_delta_proven`。因此 PC proxy 只转发 stop；一次
`forward speed=0.12 duration_ms=800` manual request 被本机 HTTP 400 拒绝，
`remote_http_status=null`，未调用远端 `/api/base/manual`。这不是 PC 首屏或代理 bug，
而是当前真实 HIL 材料不足；`visible_content_proven=false` 会继续阻止真实手动运动，
直到现场补齐外部视频和可见相机 artifact refs 等材料。

## O7 Operator Console

`workstation/` 现在包含 O7 Operator Console tab。该 tab 只消费 `GET /api/o7/operator-console` 返回的 `trashbot.o7.operator_console.v1` 契约，展示 O7 六个 KR 的 draft/blocked/not_proven 状态：实时地图/机器人位置、电梯状态、历史路线回放、数据标注、ASR/TTS、手控/寻路。

O7 cloud runtime 现在由 `python -m ros2_trashbot_cloud_relay.remote_cloud_relay` 暴露 `GET /api/o7/operator-console`；实际 HTTP handler 和 `build_o7_operator_console_contract()` 在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`，`cloud-relay/` wrapper 只 re-export，避免部署入口和 runtime handler 漂移。PC 端保持 `operator_mode=observe_only`、`command_dispatch_enabled=false`、`sends_to_robot=false`，不直连小车、不发送真实控制、不声明真实实时流或成功。

`workstation/` 还包含 `GET /api/o7/cloud-operator-console-probe?baseUrl=<url>` 和 O7 Previews 内的 “Cloud operator console probe” 区域。probe 只允许 `http://127.0.0.1`、`http://localhost`、`http://[::1]` 回环 base URL，由 PC Node 后端只读拉取远端 `/api/o7/operator-console` 并检查 schema 与危险 true 字段。它只是 local HTTP contract proof，不是公网云、4G、生产云、机器人在线或 O7 完成证明。

O7 Previews 现在把 `O7 consumer read primary path` 作为历史回放和标注队列检查主入口。operator 先用 `Load consumer task list` 调用 PC 后端 `GET /api/o7/consumer-read/tasks?baseUrl=<loopback>`，再选择 task 并用 `Load consumer task detail` 调用 `GET /api/o7/consumer-read/tasks/<task_id>?baseUrl=<loopback>&fieldEvidenceManifestJson=<local-json>`；PC 后端固定请求 O6 `view=summary` 和 detail `include=trajectory,events,evidence,labeling,inference,tunnel`。若 O6 detail 已有合法 `trashbot.field_evidence_manifest.v1` 或 `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1`，PC adapter 优先使用远端 field evidence；只有远端缺失 field evidence 且本地 `fieldEvidenceManifestJson` 是合法 `trashbot.field_evidence_manifest.v1` 时，才用本地 manifest 补齐 `field_evidence`。本地 manifest 缺失、坏 JSON、顶层非 object、schema mismatch、unsafe copy 或 `safe_to_control=true` / `primary_actions_enabled=true` / `delivery_success=true` 等危险声明都会 fail closed。同一份 consumer detail 既驱动 route replay player，也驱动 `Consumer-detail labeling queue primary path`：前者只消费 `trajectory.sample_frames`、`events.sample_events`、`evidence.sample_evidence`、`labeling.sample_items`、`inference.sample_results` 和 `tunnel_status` 摘要，后者只读检查 `labeling/evidence/events/trajectory` 的白名单短摘要。两条主路径都支持本地 cursor / 只读浏览，但所有 cursor/playback 都只在浏览器内存中变化，不写后端、不重新下发机器人命令、不证明真实云 archive 或真实机器人运动；submit/export/rollback 继续关闭。缺 detail、unknown task、task id mismatch、轨迹缺失、blocked/not_proven/error/cancel 状态或危险 true 字段都会显示 `blocked_not_proven` / fail-closed reason；页面固定展示 `safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`、`robot_control_executed=false`。

O7 Previews 还新增了 `Field evidence consumer ingest` 主入口。它从 `trashbot.field_evidence_manifest.v1` 出发，把 `route replay` 和 `labeling` 两条只读 preview 绑成同一份 `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1` 摘要，供本地/mock manifest、route replay fixture 和 labeling fixture 共享同一输出结构。该入口只接受本地文件路径，不会把 UI 直接升级成真实回放、真实标注提交或控制面；`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 始终关闭。manifest 缺失、schema 不匹配、unsafe copy、preview 缺文件或 SSH 不可达时都会 fail closed，并显式暴露 blocked reason 与 next required evidence。

`remote_cloud_relay.py` 现在还公开 `GET /api/o7/cloud-archive/tasks` 的 O7 cloud archive tasks 只读 contract。当前没有真实 archive store 时固定 `archive_status=blocked_not_proven`、空任务、`real_cloud_archive_connected=false`、`playback_available=false`、`submit_enabled=false` 和所有控制/语音/标注危险字段 false。relay runtime 可选通过 `TRASHBOT_O7_CLOUD_ARCHIVE_TASKS_JSON=/path/to/safe-fixture.json` 读取本机 `trashbot.o7.cloud_archive_fixture.v1` 脱敏 fixture，向 PC probe 暴露非空 task list、route replay sample、label/voice/command safe summaries；handler 不接受 query 任意路径，坏 JSON、不安全声明或未配置仍回到空 blocked response。`workstation/` 通过 `GET /api/o7/cloud-archive/tasks-probe?baseUrl=<url>` 从本机回环 base URL 探测该 contract，并在 O7 Previews 内展示 probe 状态、task count、selected/latest、inspector 状态、四条 inspector summary、dangerous true fields、blocked/not_proven。四条 summary 只压缩 KR3 route replay frame/sample 且固定 `playback_available=false`、KR4 labeling queue/schema 且固定 `submit_enabled=false`、KR5 ASR/TTS count/text length 且固定 `tts_send_enabled=false`、KR6 safe command envelope/ACK blocker 且固定 `command_dispatch_enabled=false` 和 `robot_control_executed=false`，不透传完整远端 JSON。该能力不是真实云 archive、真实路线回放、真实标注提交、真实 ASR/TTS、真实手控/寻路、机器人 ACK 或真实控制链路。

O7 Previews 的 `Cloud Archive Tasks` 区块仍保留 PC-only 本地 route replay player 作为次路径 / debug fallback。operator 加载本地 archive fixture 后，可以用 `Previous frame`、`Next frame`、`Reset cursor` 和本地 range cursor 检查 `route_replay_inspector.sample_frames` 的 timestamp、pose、velocity、state 和 evidence ref。该 cursor 与 consumer-detail 主路径 cursor 隔离，只改变浏览器内存，不调用 API、不写后端、不发送机器人命令；未加载 archive、无 selected task、无 sample frames、inspector blocked 或显式 `playback_available=false` 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实云历史路线回放、真实地图叠加、真实机器人运动或真实控制。

同一区块还提供只读 `Route replay trajectory minimap`。它只读取 `route_replay_inspector.sample_frames` 中有效数值型 `x_m/y_m`，用固定 SVG viewBox 归一化轨迹并把当前地图标记绑定到本地 route replay cursor；少于 2 个有效点或当前帧坐标无效时显示 blocked/unknown，不画成可用地图或确定机器人位置。面板持续显示 `trajectory_points=<n>`、`map_frame=<...>`、`current_marker=<...>`、`safe_to_control=false`、`playback_available=false` 和 `robot_control_executed=false`，不接真实地图、不发送控制命令、不声明机器人已运动。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 labeling review panel 作为 debug fallback。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `labeling_queue_inspector.sample_review_items`，可以用 `Previous item`、`Next item` 和 `Reset item` 只在浏览器内切换当前 item，查看 item/frame/media/evidence、current label sample、draft label sample、allowed label types 和 schema 摘要。该 cursor 不调用 API、不提交标注、不回滚、不写后端、不导出数据集、不发送机器人命令；未加载 archive、无 selected task、无 review items 或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实 annotation API、真实标注提交/回滚、真实 draft autosave 或真实训练集导出，而且与 consumer-detail labeling primary path 的 cursor/state 隔离。

同一区块还提供 `Local draft annotation editor`。operator 可以基于当前 review item 在浏览器内存中选择 allowed label type、填写 `0..1` confidence 和 note；前端只做本地校验并显示 `local_memory_draft_valid`、`blocked_invalid_confidence` 或 `blocked_label_type_not_allowed`。草稿按 `task_id:item_id` 隔离，`Reset draft` 只重置当前 item 的内存草稿。该 editor 固定 `submit_enabled=false`、`autosave_available=false`、`real_annotation_api_connected=false`、`dataset_export_available=false`、`cloud_write_executed=false`，不调用 API、不写后端、不导出训练集，也不新增 Submit/Save/Export 类入口。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 voice ASR/TTS monitor panel。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `voice_asr_tts_inspector.sample_asr_events`，可以用 `Previous ASR event`、`Next ASR event` 和 `Reset ASR cursor` 只在浏览器内切换当前 ASR event，查看 event type、timestamp、transcript、confidence、evidence ref、latest partial/final 对比和 `tts_draft.confirmation_required=true` 的只读 TTS 草稿摘要。该 cursor 不调用 API、不写后端、不连接真实 ASR stream、不发送 TTS、不播放音频、不调度喇叭；未加载 archive、无 selected task、ASR events 与 TTS draft 同时为空或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实 voice API、真实 ASR/TTS runtime、真实 TTS send/playback、speaker ACK、音频设备或 O7-KR5 完成。

同一区块还提供 `Local TTS draft editor`。operator 可以基于当前 `voice_asr_tts_inspector.tts_draft`、`voice_session` 和 latest partial/final 在浏览器内存中编辑 draft text、voice profile 和 language；前端只做本地校验并显示 `local_tts_draft_valid`、`blocked_tts_text_empty`、`blocked_tts_text_too_long`、`blocked_voice_profile_empty` 或 `blocked_language_empty`。archive 未加载、selected task 缺失、ASR/TTS 上下文缺失或 inspector blocked 时显示 `blocked_not_proven` 并禁用输入；切换 archive path 或重新加载 archive 会清掉本地覆盖值。`Reset TTS draft` 只重置浏览器内存。该 editor 固定 `confirmation_required=true`、`tts_send_enabled=false`、`playback_available=false`、`speaker_dispatch_enabled=false`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`、`speaker_dispatch.sends_to_robot=false`、`cloud_write_executed=false`，不调用 API、不发送 TTS、不播放音频、不调度喇叭、不写云端，也不新增 Send/Speak/Play/Dispatch/Save/Submit 类入口。

O7 Previews 的 `Cloud Archive Tasks` 区块还提供 PC-only 本地 safe command review panel。operator 加载本地 archive fixture 后，panel 默认聚焦第一条 `safe_command_inspector.sample_commands`，可以用 `Previous command`、`Next command` 和 `Reset command cursor` 只在浏览器内切换当前 command，查看 command id/type/status、envelope、idempotency、evidence、manual/navigate envelope、confirmation policy、robot ACK blocker 和 evidence gaps。该 cursor 不调用 API、不写后端、不发送手控或寻路命令、不绑定键盘、不连接真实 command API；未加载 archive、无 selected task、command sample 与 manual/navigate envelope 同时为空或 inspector blocked 时显示 `blocked_not_proven` 并禁用 navigation。它不等于真实手控、真实寻路下发、真实 robot ACK、真实 stop/cancel/recovery 或硬件安全。

同一区块还提供 `Local safe command draft editor`。operator 可以基于当前 `safe_command_inspector` 的 manual/navigate envelope、limits、map goal slot、idempotency 和 confirmation fixture 摘要，在浏览器内存中形成一条待确认手控或寻路草稿；前端只做本地校验并显示 `local_safe_command_draft_valid`、`blocked_manual_direction_not_allowed`、`blocked_invalid_navigate_goal` 或 `blocked_idempotency_key_missing`。archive 未加载、selected task 缺失、inspector blocked 或 manual/navigate 上下文不足时显示 `blocked_not_proven` 并禁用输入；切换 archive path 或重新加载 archive 会清掉本地草稿。`Reset command draft` 只重置浏览器内存。该 editor 固定 `confirmation_required=true`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`、`robot_control_executed=false`、`safe_to_control=false`、`cloud_write_executed=false`，不调用 API、不写云端、不发送手控或寻路、不绑定键盘，也不新增 Send/Run/Control/Navigate/Dispatch/Keyboard/Stop/Cancel/Recovery/Save/Submit 类入口。

`remote_cloud_relay.py` 同时公开 `GET /api/o7/realtime-elevator/snapshot` 的 O7 realtime/elevator 只读 contract。当前未接真实 ROS2 `/tf`、真实地图、实时流或电梯设备时固定 `realtime_status=blocked_not_proven`、`snapshot_status=blocked_not_proven`、`real_realtime_api_connected=false`、`real_ros2_tf_connected=false`、`latency_lt_2s_proven=false`、`route_membership.on_route=false`、`route_membership.in_elevator_zone=false`、`real_elevator_state_chain_connected=false`、`floor_recognition_proven=false`、`human_takeover_proven=false`、`safe_to_control=false`、`robot_control_executed=false`。relay runtime 可选通过 `TRASHBOT_O7_REALTIME_ELEVATOR_SNAPSHOT_JSON=/path/to/safe-fixture.json` 读取本机 `trashbot.o7.realtime_elevator_fixture.v1` 脱敏 fixture，向 PC probe 暴露非空 map/pose/elevator/floor/takeover safe summary；handler 不接受 query 任意路径，坏 JSON、不安全声明或未配置仍回到空 blocked response。`workstation/` 通过 `GET /api/o7/realtime-elevator-probe?baseUrl=<url>` 从本机回环 base URL 探测该 contract，并在 O7 Previews 内展示 map/frame、`robot_pose_summary`、pose freshness、最多 5 条 `elevator_state_samples_summary`、floor/takeover 摘要、dangerous true fields、blocked/not_proven。O7 Previews 同时提供只读 `Realtime map pose preview` 和 `Elevator state timeline preview`：前者只从 `robot_pose_summary` 安全字符串解析 `x_m/y_m/yaw_rad` 并用固定 SVG viewBox 展示 fixture/probe pose marker，解析失败显示 `blocked_pose_coordinate_unavailable`；后者只展示最多 5 条状态链摘要，空样本显示 `blocked_not_proven`。`robot_pose_summary` 固定包含 `real_ros2_tf_connected=false`，状态链 sample 只展示 `state/status/timestamp_ms/evidence_ref` 白名单字段。该能力不是真实 RTC/视频、真实实时地图、真实 ROS2 `/tf`、真实电梯状态、真实楼层识别、真实人工接管、机器人 ACK 或真实控制链路。

`workstation/` 现在还包含 `GET /api/o7/previews/acceptance` 和 O7 Previews 顶部的 “O7 previews acceptance guard”。该 guard 只汇总已存在的本地/HTTP preview surface：cloud operator console probe、cloud archive tasks probe、RTC signaling contract probe、realtime elevator probe、route replay player、Realtime map pose preview、Elevator state timeline preview、Route replay trajectory minimap、labeling review panel、Local draft annotation editor、voice monitor panel、Local TTS draft editor、safe command review panel、Local safe command draft editor。每个 surface 都明确 `evidence_boundary`、`blocked_reasons` 和 `not_proven`，仍是 software proof / `blocked_not_proven`。它固定 `reads_hardware=false`、`sends_commands=false`、`connects_cloud_production=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`playback_available=false`、`submit_enabled=false`、`tts_send_enabled=false`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`robot_control_executed=false` 和 `real_*_connected=false`，不读取 fixture、不触发 probe、不发送命令、不连接生产云、不提升 O7 完成度。它明确当前仍没有真实 RTC signaling/WebRTC/video/media transport、真实手控/寻路、真实 robot ACK 或硬件 HIL 证据。

同一 guard 区块还显示 `O7 real capability gap summary`。该 summary 是前端从已加载 acceptance guard 响应派生的只读视图，按 O7-KR1~KR6 聚合现有 `surfaces`，展示 matched surface count、surface ids、blocked/not_proven 摘要、`remaining_real_capability_gaps` 和关键 false 字段 `safe_to_control=false`、`sends_commands=false`、`connects_cloud_production=false`、`robot_control_executed=false`。未加载 guard 时显示 `not_loaded`；它不新增 fetch、不读取 fixture、不触发 probe、不发送命令，也不把 O7 完成度从 software proof 提升为真实能力。

`workstation/` 现在还包含 `GET /api/o7/live-endpoints/manifest` 和 O7 Previews 内的 “O7 live endpoints manifest” 手动加载区。该 manifest 只读取环境变量，覆盖 O7-KR1..KR6 的未来真实 API 配置状态：`O7_RTC_REALTIME_URL` / `O7_RTC_REALTIME_TOKEN`、`O7_CLOUD_ARCHIVE_URL` / `O7_CLOUD_ARCHIVE_TOKEN`、`O7_ROUTE_REPLAY_URL` / `O7_ROUTE_REPLAY_TOKEN`、`O7_ANNOTATION_API_URL` / `O7_ANNOTATION_API_TOKEN`、`O7_VOICE_API_URL` / `O7_VOICE_API_TOKEN`、`O7_SAFE_COMMAND_API_URL` / `O7_SAFE_COMMAND_TOKEN`。URL 摘要只展示 `protocol://host/path`，不展示 query、hash、用户名或密码；token 只展示 `present` / `absent`。URL 含 credentials、query 或 hash 时 capability 标记为 `blocked`，`display_url=blocked_unsafe_url`，不会采用该 URL。页面默认不自动加载 manifest；operator 点击 `Load live endpoints manifest` 后只读取本机 PC 后端摘要，不执行 ping/connect/send/test command，不连接生产云，不读取硬件，不暴露 token。

manifest 顶层固定 `network_probe_executed=false`、`sends_commands=false`、`safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`reads_hardware=false`、`token_values_exposed=false`、`url_query_hash_credentials_exposed=false`。默认没有 env 时 6 个 capability 都是 `not_configured`、`proof_status=not_proven`，并用 `required_live_evidence` / `remaining_real_capability_gaps` 明确仍缺真实 RTC/视频、实时 pose、云归档、路线回放、标注提交、ASR/TTS、safe command API、robot ACK 和硬件安全证据。接口契约见 `docs/interfaces/o7_live_endpoints_manifest_api.md`。

`workstation/` 现在新增 `GET /api/o7/rtc-signaling-contract-probe?baseUrl=<local-loopback-url>` 和 O7 Previews 内的 “RTC signaling contract probe” 手动面板。该 probe 只允许 `http://127.0.0.1`、`http://localhost`、`http://[::1]` 这类本机回环 relay，不接受 HTTPS、外网 host、credentials、query 或 hash；它只拉取远端 `/api/o7/rtc-signaling/contract` 并校验 schema `trashbot.o7.rtc_signaling_contract.v1`。UI 只展示 remote schema、contract status、核心 false fields、protocol surface keys、required evidence refs、blocked/not_proven 和 dangerous true fields，不透传 token/auth/URL/credential-bearing payload。该 probe 固定 `network_probe_executed=false`、`connects_cloud_production=false`、`sends_commands=false`、`reads_hardware=false`，只是 HTTP contract probe，不证明真实 WebRTC、视频、media transport、RTC signaling session、实时 pose stream 或 ROS2 `/tf`。

## 旧 Python 移除状态

CEO 最新要求已将 `pc-tools` 下旧 Python 脚本、Python helper 和 Python 测试入口移除。`pc-tools` 不再保留 `.py` 作为产品入口、gate 入口或测试入口。

范围检查命令：

```powershell
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
```

该命令应返回空结果。`node_modules` 内依赖包不属于本轮清理范围。

## 运行与验证

工作站验证只使用 Node/Vue gate：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
```

这些验证只能证明 PC 工作站软件链路，不证明真实机器人、真实硬件、真实手机、真实云链路或真实交付成功。

## Fail-Closed 边界

所有 API/UI 响应必须保持：

- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`

即使本地 JSON 读取成功，工作站也不得声明真实 Nav2/fixed-route runtime pass、真实 HIL、真实 WAVE ROVER feedback、真实手机验收、dropoff/cancel completion 或 delivery success。

## 2026-06-11 PC Map Lifecycle Real Proxy Smoke

`sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/` 使用临时
workstation API `http://127.0.0.1:18790`，通过 PC 固定代理访问真实上位机
`http://192.168.1.11:8787`，完成一次 no-motion map lifecycle smoke。

执行顺序：

- `GET /api/robot-control/map/list?baseUrl=http://192.168.1.11:8787`
- `POST /api/robot-control/map/start?baseUrl=http://192.168.1.11:8787`
  body `{"map_name":"pc_map_lifecycle_20260611_1350"}`
- `POST /api/robot-control/map/save?baseUrl=http://192.168.1.11:8787`
  body `{"map_name":"pc_map_lifecycle_20260611_1350"}`
- save 后再次 `GET /api/robot-control/map/list?...`
- reset 未执行，原因是 destructive reset 可能影响既有地图或运行状态。

结果：四个 lifecycle 请求均由固定 PC endpoint 转发成功，
`proxy_status=lifecycle_forwarded`、`remote_http_status=200`。前置 list
`map_count=22`，后置 list `map_count=24`，并看到
`pc_map_lifecycle_20260611_1350.yaml`。`start/save` 返回
`command_result.mode=map_lifecycle_proof_helper`、`executed=true`、`ok=true`。
补充恶意字段 smoke 对 `arbitrary_endpoint=/api/base/manual` 返回本机 HTTP 400，
`failure_reason=request_body_unknown_fields:arbitrary_endpoint`，
`remote_http_status=null`，证明浏览器/请求不能把 map proxy 变成任意路径透传。

安全边界保持：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `sends_motion_commands=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

首屏 DOM smoke 仍证明 `.simple-user-console` 是 `Rober 小车控制台` + 五卡片：
`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。默认可见首屏未出现
`开始建图`、`保存地图`、`HIL`、`proof`、`Nav2`、`/cmd_vel`、
`/api/base/manual`、`task_id`、`Mock`、`检查路径`；高级诊断继续保留
`开始建图（高级）`、`保存地图` 和 `地图列表`。

Artifacts：

- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/map_lifecycle_smoke_summary.json`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/pc_plain_user_home_dom_smoke.json`
- `sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/cleanup_summary.json`

## 2026-06-11 PC Localize Reset Real Proxy Smoke

`sprints/2026.06.11_14-05_pc_localize_reset_real_proxy_smoke/` 使用临时
workstation API `http://127.0.0.1:18791`，通过 PC 固定代理访问真实上位机
`http://192.168.1.11:8787`，完成一次 no-motion localization reset smoke。

本轮没有改 PC 产品代码，也没有改普通用户首屏组件或样式。执行顺序：

- 前置 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
- 前置直接只读 `GET /api/localize/proof/latest`
- `POST /api/robot-control/localize/reset?baseUrl=http://192.168.1.11:8787`
- 后置 `GET /api/robot-control/summary?...`
- 后置直接只读 `GET /api/localize/proof/latest`

POST 故意携带 `endpoint=/api/base/manual`、`path_generation_opt_in=true`、
`sends_motion_commands=true`、`publishes_cmd_vel=true`、`calls_base_manual=true` 和伪造
`cmd_vel` 的恶意/无关 body。Workstation route 仍忽略浏览器 body，只调用固定上位机
`/api/localize/reset`，返回 `proxy_status=refresh_forwarded`、`remote_http_status=200`、
`evidence_ref=o10-amcl-nav2-runtime-1781157704384`。

定位材料结果：

- `initialpose_published=true`
- `amcl_pose_observed=true`
- `amcl_pose_frame_id=map`
- `amcl_frame_params={base_frame_id: base_link, global_frame_id: map, odom_frame_id: odom}`
- `root_causes=[]`
- `managed_runtime_cleanup_ok=true`
- `managed_runtime_remaining_processes=[]`

安全边界保持：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `sends_motion_commands=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

首屏 DOM smoke 继续证明 `.simple-user-console` 是 `Rober 小车控制台` + 五卡片：
`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。默认可见首屏未出现
`定位重置`、`initialpose`、`AMCL`、`HIL`、`proof`、`Nav2`、`/cmd_vel`、
`/api/base/manual`、`task_id`、`Mock`、`检查路径`；`定位重置（高级）` 仍只保留在
默认关闭的高级诊断中。

Cleanup：临时 API `127.0.0.1:18791` 已停止且端口无监听；SSH 只读检查显示
`trashbot-upper-robot-api.service=active`，无长期 localize/Nav2/AMCL/helper 进程残留，
`/dev/ttyS5` 和 `/dev/ttyACM0` 的 `lsof/fuser` 均无输出。

Artifacts：

- `sprints/2026.06.11_14-05_pc_localize_reset_real_proxy_smoke/artifacts/pc_proxy/localize_reset_smoke_corrected_summary.json`
- `sprints/2026.06.11_14-05_pc_localize_reset_real_proxy_smoke/artifacts/dom_smoke/pc_plain_user_home_dom_smoke.json`
- `sprints/2026.06.11_14-05_pc_localize_reset_real_proxy_smoke/artifacts/cleanup_summary.json`

## 2026-06-11 PC Camera Link Plain UI Current Smoke

`sprints/2026.06.11_14-20_pc_camera_plain_ui_current_smoke/` 使用本机
workstation UI `http://127.0.0.1:5173/` 和本机 API `http://127.0.0.1:8787`，
通过固定 PC 代理连接真实上位机 `http://192.168.1.11:8787`，只执行连接/刷新、
打开实时画面、关闭实时画面和 DOM/video stats 读取。

本轮没有改 PC 产品代码或样式。图传打开期间 DOM 统计只证明 video 元素与
`640x480` 帧流活跃，不证明画面内容可见；同轮硬件/OpenCV 证据仍显示
`/dev/video1` near-black。PC 侧统计如下：

- `video.present=true`
- `video.visible=true`
- `video.videoWidth=640`
- `video.videoHeight=480`
- `video.readyState=4`
- `video.paused=false`
- `video.currentTime=376.085`
- `canvases=[]`

关闭后 cleanup 统计显示 `preview_status=stopped_by_user`、
`ice_connection_state=closed`、`video_track_state=stopped`、
`cleanup_status=peer_closed:closed`，video 回到 `readyState=0` 和 `0x0`。

普通首屏边界仍保持：可见首屏组合包含 `Rober 小车控制台`，`.simple-user-console`
内五卡片为 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。默认可见文本未出现
`HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`定位重置`、`AMCL`、
`task_id`、`Mock`、`检查路径`。当前 DOM 事实是标题位于 `robot-console`
section head/topbar，五卡片位于 `.simple-user-console`；这与现有测试
`visiblePlainHomeText()` 的组合首屏口径一致。

安全边界保持：本轮未调用 `/api/base/manual`、未发布 `/cmd_vel`、未启动 Nav2、
未发送非零运动、未访问 WAVE ROVER UART。浏览器截图裁剪在 video clip 阶段超时，
因此本轮没有像素 luma 统计；证据边界是 video/canvas DOM stats、video intrinsic
size、readyState/currentTime 和 cleanup diagnostics，只能说明图传链路/视频元素活跃。

Artifacts：

- `sprints/2026.06.11_14-20_pc_camera_plain_ui_current_smoke/artifacts/pc_camera_visible_video_stats.json`

## 2026-06-11 PC Radar Lifecycle Continuity Smoke

`sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/` 使用本机
workstation API `http://127.0.0.1:18792` 通过固定 PC proxy 连接真实上位机
`http://192.168.1.11:8787`，只执行雷达 start/stop lifecycle 与 read-only proof
readback。

本轮没有改 PC 产品代码、普通首屏组件或样式。执行顺序：

- `POST /api/robot-control/radar/start?baseUrl=http://192.168.1.11:8787`
- SSH 只读检查 lifecycle 与 `/dev/ttyACM0`、`/dev/ttyS5` 占用。
- 4 轮 direct upper read-only `POST /api/radar/scan-proof/refresh`，
  body `{"start_runtime":false,"timeout_s":12}`。
- `POST /api/robot-control/radar/stop?baseUrl=http://192.168.1.11:8787`
- cleanup readback。

结果：

- PC proxy start/stop 均返回 `proxy_status=lifecycle_forwarded`、
  `remote_http_status=200`、`command_result.executed=true`、`command_result.ok=true`。
- during window 4 轮 refresh 均为 `status=refreshed`、
  `proof_state=scan_once_hz_raw_packet_tf_observed`。
- 新 evidence refs 为 `o1-lidar-scan-proof-1781160878302`、
  `o1-lidar-scan-proof-1781160901312`、`o1-lidar-scan-proof-1781160924388`、
  `o1-lidar-scan-proof-1781160947425`。
- scan hz 约 `14.555`、`15.807`、`15.532`、`15.925` Hz，raw packet once 和 TF
  均观测到。
- cleanup 后 LiDAR lifecycle `running=false`，`/dev/ttyACM0` 与 `/dev/ttyS5`
  的 `lsof/fuser` 均无占用输出，本机端口 `18792` 已释放。

重要 gap：`/api/radar/status` during 和 after stop 仍返回
`continuous_scan_status=not_proven` / `scan_continuity_not_observed`。所以当前 PC 侧
已经能通过固定代理完成雷达 start/stop 与 proof readback，但 status 合同尚不能表达
continuous lifecycle running 或窗口连续性。

安全边界保持：未调用 `/api/base/manual`，未发布 `/cmd_vel`，未启动 Nav2，未发送非零运动，
未写 WAVE ROVER UART `/dev/ttyS5`，未执行 `T=1/T=13/T=130/T=131`。

Artifacts：

- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/summary.json`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/pc_proxy/01_pc_proxy_radar_start.json`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/direct_upper/02_during_window.jsonl`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/pc_proxy/03_pc_proxy_radar_stop.json`

## 2026-06-11 PC Proxy Real Board Control Smoke

`sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/` 使用临时 workstation API
`http://127.0.0.1:18793`，通过固定 PC proxy 连接真实上位机
`http://192.168.1.11:8787`。本轮没有改 PC UI 代码、普通首屏组件或样式，只保存
artifacts 和证据边界。

执行结果：

- `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 HTTP 200，
  顶层继续保持 `safe_to_control=false`、`delivery_success=false`、
  `primary_actions_enabled=false`。
- `POST /api/robot-control/radar/scan-proof/refresh?...` 返回 HTTP 200，
  `evidence_ref=o1-lidar-scan-proof-1781172841393`，一次性 scan/raw/tf 证据存在，
  但 continuous lifecycle/window 未证明。
- `POST /api/robot-control/map/proof/refresh?...` 返回 HTTP 200，
  `evidence_ref=o3-map-lifecycle-1781172868360`，map file/metadata 证据存在。
- `POST /api/robot-control/nav2/proof/refresh?...` 返回 HTTP 200，但真实上位机结果是
  `blocked_with_root_cause`，`path_generated=false`、`planner_server_active=false`；
  这不证明 Nav2 规划可用。
- camera 只读 readback 来自 summary 的 `camera_health` / `camera_devices`：
  `status=ready`、`devices_status=loaded`、`preview_status=idle_not_started`。
  本轮未打开 camera offer peer。
- `POST /api/robot-control/base/stop?...` 返回 HTTP 200，固定转发到 `/api/base/stop`。
- `POST /api/robot-control/base/manual?...` 的 forward 请求被本机 HTTP 400 拒绝，
  `remote_http_status=null`，原因是 operator report 仍缺外部视频、相机可见内容、
  轮速非零反馈和 LiDAR delta 材料。

安全边界保持：未执行非 stop motion，未调用真实 `/api/base/manual` 成功路径，未发布
`/cmd_vel`，未改变普通用户默认首屏。默认首屏仍是 `Rober 小车控制台` +
`.simple-user-console` 五卡片 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。

Artifacts：

- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/pc_proxy_smoke_key_conclusions.json`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/raw/*.json`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/logs/http_codes.log`
- `sprints/2026.06.11_19-05_pc_proxy_real_board_control_smoke/artifacts/logs/cleanup.log`

## 2026-06-28 PC Nav2 Wheel Raw L/R Readback

2026-06-28 08:37 CST 起，Nav2 goal execution/latest 的 PC key-values 同步输出
`base_feedback_latest_raw_left/right`。普通首屏显示行程执行窗口 L/R 时优先使用 raw 字段，
旧上位机或旧 artifact 没有 raw 字段时才退回 `left/right_speed` 别名。

该变化用于让“完整 Nav2 路线执行”和“wheel raw L/R 非零”口径对齐：路线执行返回成功但 raw L/R
仍未闭合时，PC 继续显示待复验；raw L/R 已出现时，地图行程标签和当前事实直接显示 raw 数值。
这只读取 Nav2 执行结果和 latest artifact，不触发 Nav2 execute、manual、keyboard、free-roam、
delivery、stop 或 `/cmd_vel`。

## 2026-06-28 PC Keyboard Free-Move Map Marker

2026-06-28 08:42 CST 起，普通首屏在用户已启用键盘并按住方向键/WASD 时，即使没有启动地图记录，
地图区域也会显示 `自由移动方向：前进/后退/左转/右转` marker，并继续带上最近 wheel raw L/R 结论。
如果已经进入地图记录，marker 仍显示为 `扫图方向`，并保留原有扫图短轨迹；未进入地图记录时不画扫图轨迹，
避免把普通自由移动伪造成建图材料。

该变化只同步本机键盘按住状态到 PC 地图显示，不自动启用键盘，不发送新的 manual pulse、free-roam start、
Nav2、delivery、stop 或 `/cmd_vel`。

2026-06-29 04:24 CST 起，`/api/robot-control/map/preview` 顶层新增
`map_wysiwyg_status_plain`、`map_wysiwyg_next_action_plain`、`path_wysiwyg_status_plain`、
`path_wysiwyg_next_action_plain`、`nav2_route_overlay_status`、`nav2_route_overlay_point_count` 和
`nav2_route_overlay_next_action_plain`。独立地图预览响应现在不用展开 summary 或内部 overlay，也能直接读到
当前地图画面、图上路线、小车位置和地图雷达点是否所见即所得；旧雷达来源点不贴图时，顶层总状态也会照实说明。
该变化只补只读 map preview 合同，不启动雷达、不准备或执行 Nav2、不发送 manual、keyboard、free-roam、delivery、
stop 或 `/cmd_vel`。

2026-06-29 01:40 CST 起，普通首屏的统一安全确认取消后会立即撤销 PC 键盘控制权：
如果只是点了“启用键盘”但没有按住方向，不会发送 manual 或 stop；如果正在按住方向键，则复用固定
`/api/robot-control/base/stop` 代理先停止，并在首屏显示“安全确认取消”。这样键盘连续手控、自由移动和扫图入口
继续共享一个最小安全确认，取消确认后不会残留 armed 状态。

2026-06-29 04:20 CST 起，上车默认 `command_mode=ros` 的 `/api/base/manual` 改为发布短时
`/cmd_vel` 给 `/esp32_bridge`，不再与 bridge 抢 `/dev/ttyS5`。PC 工作站仍只调用固定
`/api/robot-control/base/manual`，浏览器不直连 `/cmd_vel`；PWM/speed 只保留为显式诊断模式。

2026-06-29 04:40 CST 起，PC 轮速 readback 不再要求上位机临时打开底盘串口：`/esp32_bridge`
作为 `/dev/ttyS5` 的唯一 owner，会把解析到的 `T=1001` wheel raw L/R 反馈写入
`/root/rober/onboard/runtime/wave_rover_feedback_debug.jsonl`；上位机 `/api/base/status`
只读该日志并把 fresh `bridge_feedback_debug` 汇总给 PC。这样多人刷新 PC、键盘手控和 Nav2 重跑都不会因为
轮速刷新再抢 UART；日志 fresh 时 `feedback_readback` 明确返回 skipped/attempted=false，旧 direct `T=130`
只作为日志不 fresh 时的 fallback。该路径只读反馈，不发送 manual、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。

## 2026-06-28 PC Nav2 Current Fact Raw L/R

2026-06-28 08:46 CST 起，普通首屏 `当前事实` 的 Nav2 行程成功/待复验文案也统一使用
`base_feedback_latest_raw_left/right` 优先口径；旧 artifact 没有 raw 字段时才回退到
`base_feedback_latest_left_speed/right_speed`。因此行程卡、地图行程标签和当前事实不会再出现同一轮 Nav2
证据一个地方显示 raw、另一个地方显示旧 speed 的分裂。

该变化只修正 PC 只读文案，不触发 Nav2 execute、manual、keyboard、free-roam、delivery、stop 或
`/cmd_vel`。

2026-06-29 09:07 CST 起，Robot Control summary 的 Nav2 readback 会在“图上路线 ready 但
Nav2 lifecycle 已停止/未运行”的场景里同步写明：勾选安全确认后执行图上路线时会自动启动自动驾驶
runtime，并在同窗口复验轮速 L/R。`current_fact_plain` 也改为消费 Nav2 `plain_hint`，因此普通首屏和
外部脚本不会只看到“lifecycle stopped / 轮速未证明”，而是同时看到下一步动作。该变化只补只读
summary/首屏文案，不执行 Nav2 goal、不启动 runtime、不发送 manual、keyboard、free-roam、delivery、stop 或
`/cmd_vel`。

2026-06-29 14:11 CST 起，`POST /api/robot-control/nav2/goal/execute` 在请求体没有显式
`base_command_mode` / `nav2_base_command_mode` 时，会在本机最小 preflight 通过后先只读
`/api/nav2/goal/execution/latest`，并复用 latest 的 `next_execution_base_command_mode` 策略选择本次
执行模式。默认仍是 ROS；如果最近一次 ROS action 成功但执行窗口轮速 L/R 仍为 0/0，则下一次省略模式的
执行请求会自动转成 SPEED 复验。显式传入 `ros/speed/pwm` 时继续尊重请求体。该变化不放宽现场安全确认、
固定白名单或危险字段扫描，不自动执行 Nav2、不启用键盘、不发送 manual、free-roam、delivery、stop 或额外 `/cmd_vel`。

2026-06-29 09:14 CST 起，Robot Control summary 会从 camera health 的顶层字段、`source_diagnosis` 和
`source_usage` 回填结构化相机设备身份：`selected_path`、`selected_name`、`selected_is_uvc_or_usb`。
即使 `/api/camera/devices` 枚举为空，普通脚本也能直接读到当前 UVC 源是 `/dev/video1` 和对应设备名，
不再需要从“不是页面独占……”中文长句里解析。该变化只消费只读 health/devices/status，不打开第二条相机上游、
不重启 camera service、不发送 manual、Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 09:41 CST 起，普通首屏的动作状态卡带“去处理”按钮。按钮只在页面内滚动并聚焦到已有控件，
例如画面预览、地图刷新、雷达刷新、图上行程、键盘手控、自由移动或建图流程；不会自动触发这些控件，也不会替用户勾选
安全确认。该变化只改善普通用户定位下一步的体验，不发送 manual、Nav2、keyboard、free-roam、delivery、stop 或
`/cmd_vel`。

2026-06-29 09:50 CST 起，`GET /api/robot-control/summary` 顶层增加 `goal_checklist[]`，普通首屏同步展示
“本轮目标检查”。它把当前 OKR 目标拆成 7 个只读检查项：画面、地图、地图雷达点、完整行程、键盘连续手控、自由移动、
建图启动。运动相关项会显示“待安全确认/未就绪/运行中”，不会把可启动误写成完成；普通首屏展示使用中文读数，不泄露
`raw`、`marker` 或 `overlay`。该变化只读 summary，不发送 manual、Nav2、keyboard、free-roam、delivery、stop 或
`/cmd_vel`。

2026-06-29 10:00 CST 起，`GET /api/robot-control/summary` 顶层增加 `goal_checklist_summary`。普通首屏会在
“本轮目标检查”顶部显示已完成/剩余数量、需要安全确认和真实运动验证的数量，并给出第一项未完成目标的下一步。
“去处理下一项”只滚动并聚焦到已有控件，不自动发车、不启动服务、不勾选安全确认。该变化只读 summary，不发送
manual、Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 10:12 CST 起，`goal_checklist_summary` 额外拆出移动优先提示：
`first_motion_item_id`、`first_motion_source_card_id`、`motion_next_action_plain`、`motion_summary_plain`、
`mapping_next_action_plain` 和 `mapping_summary_plain`。普通首屏会同时显示“车可以先怎么动”和“建图还差什么”，
避免摄像头/雷达建图缺口遮住键盘连续手控或自由移动入口。“先动车”按钮只聚焦到已有运动控件，不发送 manual、
Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 10:28 CST 起，`goal_checklist_summary` 额外拆出 Nav2 行程提示：
`nav2_item_id`、`nav2_source_card_id`、`nav2_next_action_plain` 和 `nav2_summary_plain`。普通首屏在总目标、
移动优先和建图摘要之间直接显示完整图上行程是否已证明、是否只差安全确认复验，以及轮速 L/R 闭环下一步。
“去跑行程”按钮只聚焦到行程安全确认/执行区，不自动勾选、不执行 Nav2、不发送 manual、keyboard、free-roam、
delivery、stop 或 `/cmd_vel`。

2026-06-29 17:06 CST 起，`GET /api/robot-control/summary` 顶层新增 `nav2_summary`，内容与
`readback_summary.nav2` 完全一致。普通脚本、外部面板和现场排查不用再知道嵌套路径，也能直接读到完整行程状态、
图上路线点数、当前 lifecycle blocker、下一步、下次执行模式和执行窗口 L/R 证据。该字段只是同一份只读摘要别名，
不执行 Nav2、不启动 runtime、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 17:11 CST 起，`GET /api/robot-control/summary` 顶层新增 `camera_summary`、`map_summary`
和 `radar_summary`，内容分别与 `readback_summary.camera/map/radar` 完全一致。普通脚本、外部面板和现场排查可以
直接读到画面是否可见、共享预览是否独占、地图/路线/小车位置是否所见即所得，以及雷达点是否贴到当前地图。该字段只是同一份
只读摘要别名，不启动相机、不启动雷达、不刷新地图、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或
`/cmd_vel`。

2026-06-29 17:16 CST 起，`GET /api/robot-control/summary` 顶层新增 `keyboard_summary` 和
`free_roam_summary`，内容分别与 `readback_summary.keyboard/free_roam` 完全一致。普通脚本、外部面板和现场排查可以
直接读到“键盘连续手控是否只差安全确认”和“自由移动是否可先启动、建图是否还差相机/雷达”。该字段只是同一份只读摘要别名，
不替用户勾选安全确认、不启用键盘、不启动自由移动、不发送 manual、Nav2、delivery、stop 或 `/cmd_vel`。

2026-06-29 17:22 CST 起，summary 的 fail-closed 返回也保留 `camera_summary`、`map_summary`、
`radar_summary`、`nav2_summary`、`keyboard_summary` 和 `free_roam_summary`。当小车地址缺失、URL 不安全或
Robot API 不可读时，外部脚本和普通面板仍能拿到稳定字段，只是内容为 `not_loaded` 和恢复下一步；字段不会因为连接失败而消失。
该变化只修正合同稳定性，不重试控制、不启动服务、不发送 manual、Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 10:45 CST 起，普通首屏实时画面卡片新增“打开共享预览”直链。该链接指向 PC Node 的
`/api/robot-control/camera/mjpeg?baseUrl=...` 只读 relay，任何浏览器打开都会复用同一条上游 MJPEG 流；
页面同时显示“任何页面打开这个只读地址都会接入同一条上游流”和当前观看页面数。该入口只做 GET 预览，
不创建 WebRTC offer、不新开独占采集、不调用 manual、Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 11:02 CST 起，`goal_checklist_summary` 额外拆出雷达贴图提示：
`radar_item_id`、`radar_source_card_id`、`radar_next_action_plain` 和 `radar_summary_plain`。普通首屏会在
目标汇总顶部直接说明雷达点是否已经贴到当前地图；旧来源点只作诊断，不会被写成当前地图标记。“去看雷达点”
按钮只聚焦到雷达启动/刷新入口，不自动启动雷达、不刷新地图、不发送 manual、Nav2、keyboard、free-roam、delivery、
stop 或 `/cmd_vel`。

2026-06-29 11:18 CST 起，`goal_checklist_summary` 额外返回 `mapping_item_id` 和 `mapping_source_card_id`。
普通首屏目标汇总新增“去建图”按钮，直接聚焦到自由移动/建图流程的安全确认或下一步控件；建图仍只有在相机首帧和
雷达新鲜 就绪后才会显示可启动。该按钮只做 scroll/focus，不自动勾选、不启动建图、不启动自由移动、不发送
manual、Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 11:34 CST 起，`goal_checklist_summary` 新增 `safety_precheck_source_card_id`、
`safety_precheck_next_action_plain` 和 `safety_precheck_summary_plain`。普通首屏目标汇总会直接写明“发车前预检已精简：
只需要现场安全确认；相机和雷达不作为移动或行程发车前额外预检”，并提供“去勾确认”聚焦按钮。按钮只把焦点带到
共享安全确认或对应动作区，不自动勾选、不启动 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 11:50 CST 起，`goal_checklist_summary` 新增 `next_action_items[]`。该列表按本轮目标未完成顺序返回
标题、状态、下一步和来源卡片，普通首屏会直接展示“待处理动作”并提供每项“去处理”按钮。按钮只做页面内 scroll/focus，
方便用户从摄像头、雷达贴图、完整行程、键盘连续手控、自由移动和建图缺口之间切换；不会自动刷新地图、启动雷达、
勾选安全确认、执行 Nav2、发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:05 CST 起，普通首屏在“当前事实”下新增“当前所见”只读条，把画面、地图和雷达点三件事分开显示。
画面行只说明当前页面是否已经看到画面；地图行只说明地图画面、图上行程和小车位置是否已显示；雷达点行只说明
当前地图上实际显示了多少个雷达点，以及旧来源点仅作诊断。每行“去处理”只聚焦到对应已有控件，不自动打开画面、
刷新地图、启动雷达、勾选安全确认、执行 Nav2、发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:20 CST 起，普通首屏新增“勾确认后可做”只读条，把最小安全确认后的四类入口并排显示：
图上行程、键盘、自由移动和建图启动。图上行程 就绪时会写成“这里只需要勾安全确认，相机和雷达不再加门槛”；
键盘会强调“启用不发车，按住才动”；自由移动会说明当前是否可在安全确认后启动；建图启动仍单独看画面首帧和雷达新鲜。
每行按钮只聚焦到已有控件，不自动勾选、不执行 Nav2、不启用键盘、不启动自由移动/建图、不发送 manual、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:35 CST 起，普通首屏新增“下一步选一个”分流条，按用户意图提供 `先动车`、`跑行程`、`去建图`、
`补画面/雷达` 四个入口。该条只把当前 summary 里的 ready/缺口状态翻成短句，并把焦点带到对应控件；不会自动勾选、
不会执行 Nav2、不会启用键盘、不会启动雷达/自由移动/建图，也不会发送 manual、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:50 CST 起，普通首屏新增“目标总览”只读条，直接按本轮四个目标归并状态：
行程/键盘/自由移动、画面/地图/雷达点、发车前确认、自由移动到建图。每行只显示当前状态和卡点，按钮只聚焦到
对应已有控件，不自动勾选、不执行 Nav2、不启用键盘、不启动雷达/自由移动/建图，也不会发送 manual、delivery、stop 或 `/cmd_vel`。

2026-06-29 13:05 CST 起，`goal_checklist_summary` 新增 `ready_action_items[]` 和 `blocked_action_items[]`。
普通首屏同步新增“收口分组”：`现场可收口` 只放已经 ready 或只差现场安全确认的未完成项，`先补条件` 只放还需要先补
画面、雷达、路线、状态机或建图条件的未完成项。分组按钮仍只做页面内聚焦，不自动勾选、不执行 Nav2、不启用键盘、
不启动雷达/自由移动/建图，也不会发送 manual、delivery、stop 或 `/cmd_vel`。

2026-06-29 14:03 CST 起，`goal_checklist_summary.ready_action_items[]` 和“现场可先收口”摘要按现场低速运动优先级排序：
自由自助移动、键盘连续手控、完整行程执行、建图启动。这样摘要里的列表顺序和“先做：自由自助移动”保持一致，
不会让 operator 误以为必须先复验 Nav2 或键盘才能让车低速自助移动。该变化只改只读 summary 与首屏展示顺序，不自动勾选、
不执行 Nav2、不启用键盘、不启动自由移动/建图，也不会发送 manual、delivery、stop 或 `/cmd_vel`。

2026-06-29 11:38 CST 起，普通首屏“行程操作”新增“行程执行包”三行只读提示：执行模式、自动驾驶 runtime、
轮速验收。执行模式直接显示本次请求会用 ROS/SPEED/PWM 中哪一种；旧 PWM 成功但轮速 L/R 未证明时会明确写成
“上次 PWM，本次请求 ROS”。runtime 行说明自动驾驶服务停着时由执行接口托管启动，不再被误当成额外预检；轮速行说明
完整行程仍以同窗口轮速 L/R 非零为准，IMU 只作运动迹象。该条不新增按钮、不自动勾选、不执行 Nav2、不启用键盘、
不启动雷达/自由移动/建图，也不会发送 manual、delivery、stop 或 `/cmd_vel`。

2026-06-29 11:46 CST 起，普通首屏“自由移动准备”新增“建图解锁包”四行：先自由移动、画面首帧、雷达新鲜、建图启动。
该包把“可以先低速自由移动”和“传感器 就绪后才可建图”拆开显示：画面首帧或雷达新鲜缺失时，建图启动会显示未就绪，
但自由移动行仍按现场安全确认和停止兜底判断。每行“去处理”只聚焦到已有控件，不自动勾选、不执行 Nav2、不启用键盘、
不启动雷达/自由移动/建图，也不会发送 manual、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:01 CST 起，Robot Control summary 进一步把 `free_roam_motion_start_ready` 和
`free_roam_autonomy_start_ready` 分开：上车自由移动状态机尚未加载时，runtime 仍显示 `not_loaded`，
但 PC 已有安全确认 + 键盘/低速手控 fallback 时，低速移动事实显示为可先处理；相机、雷达只继续影响建图启动和验收。
该变化只修正只读 summary、首屏分组和测试夹具，不自动勾选、不执行 Nav2、不启用键盘、不启动雷达/自由移动/建图，
也不会发送 manual、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:10 CST 起，Nav2 行程 summary 会把自动驾驶、地图或定位只读端点读取失败作为普通用户可见根因。
当 `/api/nav2/status`、`/api/nav2/proof/latest`、`/api/map/proof/latest` 或 `/api/localize/proof/latest`
读不到时，`nav2_goal_next_action_plain` 和 `readback_summary.nav2.next_action_plain` 会先提示确认小车地址和上位机 API 可读，
再刷新地图/自动驾驶状态并准备图上路线；不再只写“先生成图上路线”。该变化只修正只读 summary 文案，不自动刷新 proof、
不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:17 CST 起，相机 source diagnosis 还没形成硬件结论时，`source_diagnosis_next_action_plain` 不再留空，
会回退到共享 MJPEG/首帧检查下一步：打开页面自动接入共享预览，若仍无画面则点只读检查复测首帧。已经明确为
`uvc_no_frame_not_exclusive` 时仍优先显示检查 USB、摄像头输入或供电、换 known-good UVC 复测。该变化只修正只读
summary 和 `/api/robot-control/camera/mjpeg/status` 文案，不新建额外 capture、不执行 Nav2、不发送 manual、
keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:24 CST 起，Robot Control summary 会识别现场常见端口漂移：PC Node 监听 `0.0.0.0:7001`，
小车上位机 Robot API 监听 `192.168.1.11:8787`，`7071` 不是 Robot API 端口。当显式传入
`baseUrl=http://192.168.1.11:7071` 且只读端点全失败时，`robot_api_connection.blocked_reasons` 和
`current_fact_plain` 会把 `robot_api_port_7071_mismatch_use_8787` 放在最前面，直接提示不要把 Robot API 填成
7071。该变化只修正只读诊断，不自动改写用户输入、不重启上位机、不执行 Nav2、不发送 manual、keyboard、
free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:32 CST 起，Robot Control summary 的 `/api/base/status` 和
`/api/base/feedback-samples/latest` 只读窗口从 4s 提升到 8s。现场直连这两个端点约 3.6s 返回，并发 summary
读取时旧 4s 窗口会偶发误报 `fetch_timeout_4000ms`，导致当前轮速和 T=1001 反馈不能进入首屏。该变化只延长
底盘反馈 GET readback 预算，帮助判断完整 Nav2 路线的 wheel L/R 证据，不发送 manual、Nav2、keyboard、
free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:39 CST 起，Robot Control summary 不再一次性并发请求全部 15 个上位机只读端点。PC Node 会先读取
地图、定位、Nav2、相机、雷达、free-roam 和底盘 feedback latest 等快端点，再把慢聚合 `/api/base/status` 与
`/api/status` 串行放到最后；返回给 UI 的 `read_endpoints[]` 顺序仍保持原契约。浏览器等待 summary 的窗口同步提升到
12s，避免真实上位机接近单 worker 时把所有端点误报成 `fetch_timeout_*`。该变化只调整 GET readback 调度和等待窗口，
不调用 manual、不执行 Nav2、不启用 keyboard/free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:48 CST 起，Nav2 图上路线已经 ready 且 execute 端会托管启动自动驾驶 runtime 时，
`safe_command_boundary.nav2_goal_blockers` 不再残留 `nav2_lifecycle_not_running`。普通首屏会继续保留
`readback_summary.nav2.current_blocker_reasons` 作为只读诊断，但发车边界只显示“等待安全确认/可重跑复验”，并在下一步里提示
“执行时会自动启动自动驾驶 runtime”。planner/controller 真实未就绪时仍会进入 blocker。该变化只修正只读 summary
和发车口径，不自动执行 Nav2、不调用 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 12:56 CST 起，普通首屏的“地图”动作卡不再把雷达点缺口当成地图下一步。只要地图画面已经显示，
`action_status_cards[].id=map_preview` 会提示“继续确认图上路线和小车位置，雷达点另看地图雷达点”；雷达启动、
新扫描和贴图仍由 `radar_map_points` 卡片承接。底层 `readback_summary.map.radar_overlay_*` 诊断不变，旧雷达点仍不会
冒充当前地图标记。该变化只修正普通首屏只读文案，不启动雷达、不刷新地图、不执行 Nav2、不调用 manual、keyboard、
free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 13:02 CST 起，`action_status_cards[].id=mapping_start` 的运动语义按建图启动 ready 状态返回。
相机首帧或雷达新鲜度缺失时，建图卡片仍显示未就绪，`can_start_after_safety_confirm=false` 且
`sends_motion_when_clicked=false`；只有画面首帧和雷达新鲜都就绪、建图启动可点时才会把它标成会进入运动/建图流程。
这不会影响“自由移动”和“键盘手控”卡片，它们仍只依赖现场安全确认和停止兜底。该变化只修正只读 summary
和测试夹具，不启动建图、不执行 Nav2、不调用 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 13:09 CST 起，`goal_checklist_summary.summary_plain` 会先列出现场已经可收口的项目，再提示还要补的条件。
例如 Nav2 重跑、键盘连续手控和自由移动都只差安全确认时，总览会写“现场可先收口 3 项”，而不是只写“先处理画面”。
相机、雷达和建图缺口仍保留在 `blocked_action_items[]`，但不会遮住已经可执行的移动入口。该变化只修正只读
summary 文案，不自动勾选安全确认、不执行 Nav2、不启用 keyboard/free-roam、不启动建图、delivery、stop 或 `/cmd_vel`。

2026-06-29 13:16 CST 起，目标检查里的 `mapping_start` 安全确认和运动计数也按建图启动 ready 状态返回。
相机首帧或雷达新鲜度缺失时，建图仍阻塞目标完成，但不会再计入“需要现场安全确认/需要真实运动验证”；只有画面和雷达
都就绪、建图启动可点时，才把它计为需要安全确认和会进入运动/建图流程。这样首屏总览会把当前可先收口的
Nav2 重跑、键盘连续手控、自由移动统计成 3 项，不把未就绪建图误导成第 4 个发车动作。该变化只修正只读
summary 结构和测试夹具，不启动建图、不执行 Nav2、不调用 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 13:22 CST 起，地图雷达 WYSIWYG 的白话字段不再输出英文 marker 叫法。`radar_overlay_wysiwyg_status_plain`
和地图/雷达 readback 会统一写成“雷达点已贴到当前地图 / 雷达点未贴到当前地图 / 地图雷达点未加载”，继续保留
`map_marker_*` 兼容字段给脚本读取。该变化只修正只读文案和 fixture，不启动雷达、不刷新地图、不执行 Nav2、
不调用 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 14:35 CST 起，上位机 `/api/nav2/goal/execution/latest` 修复 latest artifact 有内容时丢失 payload 的
只读包装问题，并把 `status`、`base_command_mode`、`next_base_command_mode`、执行窗口轮速 L/R 是否非零、
readback 运动字段提升到顶层。现场若上次 PWM action 成功但轮速未证明，latest 会直接给出下一轮建议 `ros`；
若上次 ROS 仍未证明，则建议 `speed`。顶层仍保持 `robot_control_executed=false`、`sends_motion_commands=false`、
`publishes_cmd_vel=false` 和 `safe_to_control=false`，只用于 PC 诊断和下一次显式安全确认后的执行模式选择，
不自动执行 Nav2、不调用 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

2026-06-29 14:48 CST 起，上位机 8088 共享 MJPEG 首帧短预算优先尝试低带宽真实离散模式：`MJPG@640x480@30`
之后先试 `MJPG@480x320@30` 和 `YUYV@320x240@25`，再试 `YUYV@640x480@22` 与 default。这样现场 DV20 UVC
在 640x480 大帧无首帧时，PC 普通首屏会尽快尝试更容易出图的小帧模式；多人仍共用同一个上游 capture。
8088 自己短暂持有 shared capture 且没有其他 owner 时，health 仍保持“不是页面独占”的归因。该变化只调整相机取帧尝试顺序
和只读诊断，不新建底盘控制、不执行 Nav2、不调用 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
