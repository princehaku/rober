# 2026.06.30 06:20 PC 自由移动主按钮语义合同

sprint_type: micro

## 实际改动

- 普通首屏自由移动主按钮新增按钮级 DOM 证据：
  - `data-primary-action-kind`
  - `data-target-source`
  - `data-primary-action-mapping-start-ready`
  - `data-camera-blocks-mapping-start`
  - `data-radar-blocks-mapping-start`
  - `data-camera-blocks-free-motion=false`
  - `data-radar-blocks-free-motion=false`
- 当相机首帧或雷达新鲜度不足时，按钮语义为 `start_free_move_only`，只启动低速自由移动，不请求建图记录。
- 当相机首帧和雷达新鲜都满足时，按钮语义为 `start_mapping_record_then_free_move`，点击顺序继续保持先固定 `/api/robot-control/map/start`，再固定 `/api/robot-control/free-roam/autonomy/start`。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- test/App.test.ts -t "points mapping-ready users to start the map recording when only mapping runtime is missing|allows free-roam recording when camera source is selected but not yet frame-proven|shows the simplified first-screen console"`：通过，`2 passed | 217 skipped`。
- `npm test -- --run`：通过，`2 passed` test files，`389 passed` tests。
- `npm run build`：通过，Vite 仅保留既有 chunk size warning。
- `git diff --check`：通过，无 whitespace error。
- dist/7001 smoke：`pc-tools/workstation/dist/assets/index-DgEFjPIn.js` 可检出 `primary-action-kind`、`target-source`、`camera-blocks-mapping-start`、`radar-blocks-mapping-start`、`start_mapping_record_then_free_move`、`start_free_move_only`；`127.0.0.1:7001` 返回同一新 bundle，`node` PID `90265` 监听 `*:7001`。

## 剩余风险

- 本轮只补 PC DOM 合同和测试，不发送真实 free-roam、map/start、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实建图闭环仍需上车 HIL：相机首帧、雷达新鲜、地图记录启动、自由移动轨迹和保存后的地图质量要在真实环境复验。
