# 2026-07-02 02:08 相机唯一缺口与雷达贴图完成别名

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 summary 顶层只读 alias：
    `radar_overlay_wysiwyg_complete`、`live_wysiwyg_only_camera_missing`、
    `mapping_start_only_camera_missing`。
  - 这些字段直接由现有 WYSIWYG 缺口、mapping 缺口和 radar overlay 读回推导，不新增控制入口。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐上述字段类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏 `plain-field-acceptance-packet` DOM 同步暴露：
    `data-radar-overlay-wysiwyg-complete`、`data-live-wysiwyg-only-camera-missing`、
    `data-mapping-start-only-camera-missing`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 增加 API 和 DOM 断言，覆盖雷达贴图未完成、雷达贴图已完成、建图只剩相机三种读回口径。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明这些字段只用于现场判断“雷达贴图已完成，只剩相机首帧”，不发车。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts`：通过，2 个测试文件、246 个测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 bundle 超过 500kB，这是既有体积提醒，不影响本轮只读别名。
- 重启 PC API 后，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
- `curl http://127.0.0.1:7001/` 读到当前 bundle `index-CL7AUyWj.js`。
- `curl http://127.0.0.1:7001/assets/index-CL7AUyWj.js | rg -o 'data-radar-overlay-wysiwyg-complete|data-live-wysiwyg-only-camera-missing|data-mapping-start-only-camera-missing' | sort | uniq -c`：
  - `data-live-wysiwyg-only-camera-missing`：2 处。
  - `data-mapping-start-only-camera-missing`：2 处。
  - `data-radar-overlay-wysiwyg-complete`：2 处。
- `curl 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787' | jq ...` 现场读回：
  - `status=needs_wheel_rerun`
  - `radar_overlay_wysiwyg_complete=true`
  - `live_wysiwyg_only_camera_missing=true`
  - `mapping_start_only_camera_missing=true`
  - `live_wysiwyg_missing_reasons=["camera"]`
  - `radar_overlay_status=loaded`
  - `mapping_start_missing_evidence=["camera_first_frame"]`

## 剩余风险

- 本轮只改只读 alias 和 DOM 合同，没有执行 Nav2、键盘、自由移动、建图或 `/cmd_vel`。
- 当前真实剩余能力缺口仍需要现场安全确认后的运动闭环，以及相机首帧硬件恢复。
