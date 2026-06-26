# 2026.06.27 16:55 PC Free-Roam Auto Guide Non-Motion Steps

sprint_type: micro

## 实际改动

- 修复普通首屏自动扫图按钮在 `free_roam_autonomy_start_ready=true` 但本地条件未齐时仍退回人工键盘扫图向导的问题。
- 自动扫图按钮现在会优先走自动扫图向导：未勾安全确认只聚焦 checkbox；已勾后若地图记录未启动，会调用固定 map start；地图记录启动后会刷新扫图画面，并把该 preview 计入本轮 `plainFreeRoamMapPreviewFreshForSession`。
- 当地图记录、地图画面、摄像头、雷达和停止兜底都满足后，才调用固定 `/api/robot-control/free-roam/autonomy/start`。
- 同步更新 `docs/product/pc_free_roam_mapping_design.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm run build`：通过。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 219 tests。
- `git diff --check`：通过。
- PC Node 已用新代码运行在 `0.0.0.0:7001`。
- 只读 smoke：PC summary 返回 `start_ready=true`、`free_roam=locked`、camera `ready`、LiDAR `running/fresh=true`。
- 真机只读 `/api/status`：camera `ready`、`video_source=/dev/video1`、radar `running=true/fresh=true`、free-roam 当前仍 `locked`。

## 剩余风险

- 本轮没有直接点击 start 让小车移动；真实移动仍需要现场勾选安全确认，并让 PC 固定 start 代理触发上车端 camera/radar 复检和运动双锁。
- 地图 start 和 preview refresh 在真实 UI 点击时会发生两次只读 preview 刷新，其中第二次用于明确计入本轮自动扫图 fresh gate；后续可优化为单次带标记刷新。
