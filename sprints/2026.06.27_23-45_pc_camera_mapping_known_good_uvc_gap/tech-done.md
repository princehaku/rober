# PC 摄像头建图缺口 known-good UVC 提示

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏自由移动 / 建图验收缺口在相机首帧失败且已证明不是页面独占时，继续追加现场可执行建议：检查 USB、输入、供电，必要时更换 known-good UVC。
  - 该改动只翻译已有 `readback_summary.camera` 诊断，不重新打开摄像头、不创建额外 capture，也不改变自由移动、Nav2、manual 或 stop 的触发条件。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 live not-in-use camera first-frame failure 场景，锁定 `当前事实` 与 `建图验收` 都显示“不是页面独占；检查 USB/输入/供电，必要时换 known-good UVC”。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏 camera_first_frame 缺口的 WYSIWYG 文案边界。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录多人共享预览与建图验收的同一归因口径：无首帧不是后来页面抢占，但仍不能按可验收建图收口。

## 验证结果

- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：2 个 test files，318 个 tests。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示主 chunk 超过 500 kB，这是既有体积提示，不影响本轮功能。

## 剩余风险

- 当前真实相机仍是上位机 DV20 UVC 无首帧问题，本轮只把原因和下一步更清楚地显示给普通用户，没有修复硬件输入、USB 线、供电或采集卡模式。
- 建图验收仍要求真实相机首帧、雷达 fresh、地图记录和新鲜地图画面；本轮不会把相机无帧状态提升为 ready。
- 未执行任何 motion/free-roam/Nav2/manual/stop 命令；没有新增 HIL 运动证据。

