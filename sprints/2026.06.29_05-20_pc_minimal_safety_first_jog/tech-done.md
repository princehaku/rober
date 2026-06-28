# 2026.06.29 05:20 PC minimal safety first-jog

sprint_type: micro

## 实际改动

- PC 普通首屏 `试动一下`、轮速卡 `低速试动读轮速` 不再被外部视频、可见相机、旧 first-jog 恢复材料或雷达状态阻塞；前端硬门禁收敛为小车地址、请求未忙和“人在旁边、周围安全、停止手段就绪”安全确认。
- workstation `POST /api/robot-control/base/first-jog` 不再读取 `/api/operator/report` 做视觉材料 preflight；安全确认后转发固定 `/api/base/manual`，保留速度/时长 clamp、`command_mode=ros` 和 stop 兜底口径。
- `first_jog_readiness_summary` 改为只反映基础安全状态；视觉材料仍作为参考字段展示，但不再进入 missing fields 或阻止 first-jog。
- 恢复试动确认按钮仍保留为可选补材料动作，但不再影响试动按钮、轮速目标进度或键盘下一步。
- 同步更新 PC 产品文档和 fixed-route 文档，明确摄像头/雷达/外部视频只影响建图、验收和材料，不影响低速移动。

## 验证结果

- `cd pc-tools/workstation && npm run test -- App.test.ts` 通过：210 tests。
- `cd pc-tools/workstation && npm run test -- catalog.test.ts` 通过：150 tests。
- `cd pc-tools/workstation && npm run test` 通过：2 files / 360 tests。
- `cd pc-tools/workstation && npm run build` 通过；Vite 仍提示单 chunk 大于 500 kB，这是既有前端体积 warning，不影响本轮功能。

## 剩余风险

- 本轮没有执行真实底盘运动、Nav2 发车或摄像头 HIL；真实车是否 wheel raw L/R 非零、自动驾驶是否完整路线执行成功，仍需要现场在安全确认后用 PC 首屏复验。
- 当前摄像头共享预览链路不是浏览器独占问题，但 `/dev/video1` 仍可能无首帧；这只影响实时预览/建图验收，不影响本轮低速试动门禁。
