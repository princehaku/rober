# PC Plain Check Robot Button

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通用户首屏 `小车连接` 卡片新增 `检查小车` 按钮，复用既有一键巡检流程。
  - 新增 `plainEvidenceSweepSummary`，把高级巡检结果压成 `待检查 / 检查中 / 已检查 / 需要处理 / 检查失败` 这类普通短状态。
  - 首屏仍不展示 `proof`、`Nav2`、`HIL`、endpoint、raw/readback、`/cmd_vel` 或 `/api/base/manual` 等工程/危险词。
- `docs/product/pc_tools_workstation.md`
  - 同步普通首屏契约，明确 `检查小车` 是允许的普通动作，但完整结果仍只进默认关闭的高级诊断。

## 验证结果

- `cd pc-tools/workstation && npm run test`
  - 通过，`92 passed`。
  - 首次验证发现首屏初始文案 `未检查` 命中既有普通首屏禁词，已改为 `待检查` 后复跑通过。
- `cd pc-tools/workstation && npm run build`
  - 通过，Vite production build 完成。
- `cd pc-tools/workstation && npm run lint`
  - 通过，ESLint 无报错。
- `git diff --check`
  - 通过，无 whitespace error。

## 剩余风险

- 本轮是 PC 首屏入口修正，未新增真实运动能力，也未放宽 non-stop manual gate。
- 真实上位机最新证据仍显示 `/dev/video1` first-frame timeout；实时画面可见内容需要现场继续处理。
- 非 stop 运动仍需要真实 operator report、可见图传、轮速反馈、LiDAR delta 和外部视频材料全部满足后，才能在高级诊断中执行受控低速短时 jog。
