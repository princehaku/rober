# 2026.06.11 15:50 PC Camera Frame Quality Indicator

## sprint_type

micro

## 本轮功能点设计

- 目标：在不改 `onboard/**`、不增加首屏工程控件、不上传任何画面的前提下，让 PC workstation 首屏把“video 元素已打开”和“画面内容可见/过暗”分开。
- 采样范围：
  - 只允许浏览器前端本地读取 `<video data-testid="robot-camera-preview-video">`。
  - 只允许把 video 当前帧缩放绘制到临时 canvas，并立刻在内存里计算亮度指标。
  - 不上传图片、不保存截图、不写本地图片文件、不改 camera hardware/config。
- 采样指标：
  - `mean_luma`
  - `max_luma`
  - `non_black_ratio_ge16`
  - `sample_status`
  - `sampled_at`
- 采样节奏：
  - 在 video `loadeddata` / `playing` 后触发。
  - 每个会话最多做 1-3 次低频重试采样，用来覆盖“元素已绑流但首帧还没准备好”的窗口。
- 首屏状态词边界：
  - 只允许 `未打开`、`连接中`、`已打开`、`画面可见`、`画面偏暗`、`失败`。
  - 普通用户提示只允许普通话短句，例如 `画面太暗，先检查镜头/光线。`
  - 禁止把 `luma`、`canvas`、`peer`、`ICE`、`SDP`、`proof`、`HIL`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、`启动雷达`、`停止雷达` 放回首屏。
- 保守阈值：
  - 只有同时满足 `mean_luma`、`max_luma`、`non_black_ratio_ge16` 的保守门槛，才允许首屏显示 `画面可见`。
  - 其它已完成采样但不满足门槛的情况，一律按 `画面偏暗` fail-closed，而不是乐观显示 `已打开`。
- fail-closed 规则：
  - 采样结果绝不能把 `safe_to_control`、`primary_actions_enabled`、`delivery_success`、`robot_control_executed` 置为 `true`。
  - `sample_failed` 只进入高级诊断，不自动升级为“画面可见”。
  - 即使 video 尺寸是 `640x480` 且帧流在推进，只要像素内容近黑，也必须在首屏给出更真实的 `画面偏暗`。
- 验收命令：
  1. `cd pc-tools/workstation && npm run build`
  2. `cd pc-tools/workstation && npm run test -- --run`
  3. `cd pc-tools/workstation && npm run lint`
  4. `git diff --check`
  5. 真实 PC / 上位机 smoke：打开本机 workstation UI/API，连接真实上位机 `http://192.168.1.11:8787`，采集 video 元素状态和新增 frame quality metrics，保存 JSON artifact 到本 sprint；关闭 peer 后确认 `/api/camera/health` 的 active peers 回到 0。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增前端本地 video -> canvas 亮度采样状态机，只在浏览器内存里计算 `mean_luma`、`max_luma`、`non_black_ratio_ge16`。
  - 首屏“实时画面”从单一 `已打开` 拆成 `已打开 / 画面可见 / 画面偏暗`，并保持 `失败` 只用于会话打开失败或 cleanup 失败。
  - 高级诊断新增 `sample_status`、`sampled_at`、`sample_attempts`、`sample_canvas_size` 和采样失败原因，便于后续 HIL 材料复核。
- `pc-tools/workstation/test/App.test.ts`
  - sprint artifact 路径切到本轮目录。
  - 新增可见画面和 near-black 两类 UI 测试，覆盖普通首屏状态词与高级诊断亮度字段。
  - 继续输出普通首屏 DOM smoke artifact。
- `docs/product/pc_tools_workstation.md`
  - 记录首屏“实时画面”卡片的新文案边界、采样指标、保守阈值策略和高级诊断字段。
- `pc-tools/README.md`
  - 同步记录本地 canvas 采样机制，以及它只用于可见内容诊断、不用于控制放行。
- Sprint artifact
  - `sprints/2026.06.11_15-50_pc_camera_frame_quality_indicator/artifacts/camera_frame_quality_dom_smoke.json`
  - `sprints/2026.06.11_15-50_pc_camera_frame_quality_indicator/artifacts/live_camera_frame_quality_smoke.json`

## 设计落地摘要

- 指标：
  - `mean_luma`
  - `max_luma`
  - `non_black_ratio_ge16`
  - `sample_status`
  - `sampled_at`
- 采样节奏：
  - `loadeddata` / `playing` 后触发。
  - 每会话最多 3 次低频补采样，避免首帧尚未 ready 时误报。
- 保守阈值：
  - 仅当 `mean_luma >= 18`、`max_luma >= 96`、`non_black_ratio_ge16 >= 0.05` 同时满足时，首屏才显示 `画面可见`。
  - 其它完成采样但不满足阈值的情况，一律显示 `画面偏暗`。
- 首屏文案边界：
  - 保留 `打开画面 / 关闭画面` 两个按钮，不增加工程控件。
  - 普通状态只允许 `未打开 / 连接中 / 已打开 / 画面可见 / 画面偏暗 / 失败`。
  - 高级诊断才显示 `mean_luma`、`max_luma`、`non_black_ratio_ge16`、`sample_status`、`sampled_at`。
- fail-closed：
  - 采样不会把 `safe_to_control`、`primary_actions_enabled`、`delivery_success`、`robot_control_executed` 置 true。
  - `sample_failed` 不会被包装成 `画面可见`。
  - 即使 video 会话已建立，只要像素内容近黑，也优先显示 `画面偏暗`。

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 通过。
  - 关键输出：`vite v7.3.3 building client environment for production...`，`✓ built in 5.05s`。
- `cd pc-tools/workstation && npm run test -- --run`
  - 通过。
  - 关键输出：`Test Files  2 passed (2)`，`Tests  90 passed (90)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过，无输出。
- `git diff --check`
  - 通过，无输出。

## 真实 PC / 上位机 camera smoke

- 本机 workstation UI：`http://127.0.0.1:18794/`
- 本机 workstation API：`http://127.0.0.1:18794/`
- 真实上位机 Robot API：`http://192.168.1.11:8787`
- artifact：
  - `sprints/2026.06.11_15-50_pc_camera_frame_quality_indicator/artifacts/live_camera_frame_quality_smoke.json`

### 结果

- 本轮 in-app browser 真实点击 `打开画面` 后，普通首屏进入：
  - `实时画面=失败`
  - hint=`The operation was aborted due to timeout`
- 因为 preview 未进入 `streaming`，所以这轮真实浏览器采样结果是：
  - `sample_status=not_sampled`
  - `mean_luma=not_sampled`
  - `max_luma=not_sampled`
  - `non_black_ratio_ge16=not_sampled`
- DOM / video 事实：
  - `video_present=true`
  - `video_src_object_bound=false`
  - `video_ready_state=0`
  - `video_width=0`
  - `video_height=0`
- `/api/camera/health` 复核：
  - `status=ready`
  - `active_peer_count=0`
  - `active_peer_ids=[]`
  - `peer_cleanup_confirmed=true`
- `last_closed_peer` 关键字段：
  - `remote_sdp_has_video=true`
  - `remote_sdp_video_direction=a=recvonly`
  - `remote_sdp_candidate_count=2`
  - `frames_read=0`
  - `camera_opened=false`
  - `source_selection.failure_reason=no_candidate_opened_and_read_first_frame`
  - `attempts` 中 `/dev/video1` 为 `opened=true` 但 `read_ok=false`

## 失败定位

- 本轮前端代码路径本身已通过 build/test/lint，但 in-app browser 的真实图传 smoke 没进入可播放 `<video>`：
  - UI 侧是 `start_failed`
  - 普通首屏 failure reason 为 `The operation was aborted due to timeout`
- 结合 `/api/camera/health` 的 `last_closed_peer`，当前更像是板端相机源侧没有读到第一帧，而不是前端把成功播放误判成黑屏：
  - `remote_sdp_has_video=true` 说明 offer/answer 方向不是空的。
  - `frames_read=0`、`camera_opened=false`、`/dev/video1 opened=true 但 read_ok=false` 说明 peer 生命周期里没有拿到第一帧。
- 因此，本轮真实 smoke 只产出了“失败态 + peer 已清零 + 相机源未读到第一帧”的可复核材料，没有产出成功播放后的 luma metrics。

## 剩余风险

- 需要 Hardware / Robot 侧继续处理 `no_candidate_opened_and_read_first_frame`，否则前端新增的 `画面可见 / 画面偏暗` 只能在成功播放的浏览器会话里发挥作用。
- 本轮没有拿到真实 `near_black` 播放态，所以“首屏从 `已打开` 切到 `画面偏暗`”的现场证据仍缺一环；当前只有前端测试和历史硬件 near-black 证据支撑阈值设计。
- 已确认的安全边界保持不变：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
