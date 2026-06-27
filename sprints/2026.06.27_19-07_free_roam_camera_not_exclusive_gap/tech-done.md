# 2026-06-27 19:07 自由移动建图缺口显示相机非独占诊断

## sprint_type

micro

## 目标

- 继续推进“画面所见即所得”和“自由移动不被建图材料误挡”。
- live 状态已证明当前摄像头不是页面独占，而是 UVC 无首帧；普通自由移动 / 建图卡片也必须直接显示这个事实。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `cameraFirstFrameMissingPlainLabel()`。
  - 当建图缺口包含 `camera_first_frame` / `camera_first_frame_not_observed`，且 camera summary 显示 `uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`，或摄像头未被占用时，普通首屏显示 `画面首帧未出（不是页面独占）`。
  - 该标签用于当前事实、自由移动 / 建图 readiness、本地 fallback readiness，保持“可以低速自由移动”和“不能按建图验收”两层口径。
- `pc-tools/workstation/test/App.test.ts`
  - 更新自由移动 / 建图相关断言，锁定非独占相机无首帧的普通文案。
- `docs/product/pc_tools_workstation.md`
  - 同步记录该 WYSIWYG 行为边界。

## 验证结果

- `npm test -- --run test/App.test.ts -t "uses the visible map preview over stale fresh-map-preview missing tokens|free-roam"`
  - 通过：`21 passed | 155 skipped`
- `npm test -- --run`
  - 通过：`2 passed (2) / 305 passed (305)`
- `npm run build`
  - 通过：TypeScript、Vite client build、server TypeScript 均通过。
  - 剩余提示：Vite chunk size 超过 500 kB，为既有构建体积提示。
- `npm run lint`
  - 通过。
- `git diff --check`
  - 通过。

## 剩余风险

- 本轮没有触发真实 manual、keyboard、free-roam start、Nav2 execute、delivery、stop 或 `/cmd_vel`。
- 该改动只解决 PC 普通首屏诊断表达；真实摄像头仍需现场检查 USB、输入源、供电或更换 known-good UVC。
- 建图验收仍要求真实首帧、雷达材料、地图记录和新地图画面；低速自由移动继续按安全确认和停止兜底分层。
