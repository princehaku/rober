# Radar Runtime Priority WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`effectiveLidarReadback` 在 `lidar_fresh` gate 明确来自 `free-roam runtime /scan 新鲜` 时，优先采用 runtime scan 派生的状态、新鲜度、lifecycle 和 point-count 口径。过期 `/api/radar/status` 或 summary proof 仍保留为诊断，但不能覆盖当前地图雷达 marker。
- `pc-tools/workstation/test/App.test.ts`：新增 `keeps runtime scan freshness after a stale radar status refresh` 回归，模拟 summary runtime `/scan` 新鲜，但点击刷新地图后 `/api/radar/status` 返回 stale proof，验证地图 marker、freshness label 和高级 `/api/radar/status=` 摘要仍保持 `free_roam_runtime_scan_fresh`。
- `docs/product/pc_tools_workstation.md`：同步记录雷达 WYSIWYG 优先级规则。

## 验证结果

- `npm test -- --run test/App.test.ts -t "keeps runtime scan freshness after a stale radar status refresh"`：通过，1 个用例通过。
- `npm test -- --run`：通过，2 个测试文件、300 个用例全部通过。
- `npm run build`：通过，产物为 `dist/assets/index-BK6wcOvd.js` 和 `dist/assets/index-DkzBjvNI.css`；Vite 仍提示主 chunk 超过 500 kB，这是既有体积告警。
- `npm run lint`：通过。
- `git diff --check`：通过。
- `curl -s http://127.0.0.1:7001/`：确认当前 7001 页面引用新构建产物 `assets/index-BK6wcOvd.js`，`lsof` 显示 Node 监听 `*:7001`。

## 剩余风险

- 本轮不启动雷达、不启动 free-roam、不发送任何运动控制；只修 PC 对已有 runtime `/scan` 新鲜事实的展示优先级。真实雷达点数组仍取决于上位机是否发布 scan preview points；没有点数组时 PC 仍只显示最近障碍距离，不能把距离伪造成地图坐标点。
