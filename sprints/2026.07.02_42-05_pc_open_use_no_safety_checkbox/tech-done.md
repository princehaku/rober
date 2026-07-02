# PC 普通页默认可用

## sprint_type

micro

## 实际改动

- PC 普通控制页默认现场安全已确认，移除可见安全确认 checkbox 门禁；旧 DOM/test/script 需要的 checkbox 仅保留为隐藏兼容 input，并始终回读已确认。
- 行程准备/执行入口、键盘启用、自由移动、低速试动不再因为未点击 checkbox 被禁用；仍保留停止按钮、键盘松开停、失焦停、切页停。
- 相机和雷达缺口继续只影响建图启动/验收，不阻塞底盘试动、键盘连续手控或自由移动。
- 普通用户地图口径保持：PC 首页大地图和 `/map` 大屏为主；ROS2 配套工具是 RViz2（本地工程观察）和 Foxglove bridge/Web（远程浏览器观察），只用于看地图/雷达/TF/路径/costmap，不替代普通控制页。

## 验证结果

- `npm test -- test/App.test.ts` 通过：237 tests passed。
- `npm run build` 通过：TypeScript、Vite build、server TypeScript 均通过；仍有既有 bundle size warning。

## 剩余风险

- 本轮验证是 PC 前端和 Node 构建/测试；未执行真实小车物理运动 HIL。
- 摄像头无首帧和自动驾驶现场不可动的硬件/上车端根因不在本 micro sprint 内闭环，仍需现场联调验证。
