# PC 送达动作地图刷新 Gate

## sprint_type

micro

## 实际改动

- 普通首屏送达材料准备、保存草稿、最终确认送达接入地图 WYSIWYG gate。
- 地图画面或地图 proof 正在刷新时，送达区按钮显示等待/刷新状态并禁用。
- 送达函数入口在地图刷新中直接早退，避免测试或异常触发绕过按钮禁用。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录该 gate 不提交 operator report、delivery complete 或任何运动接口。

## 验证结果

- 通过：`npm test -- -t "shows delivery confirmation pending on the map while final completion is in flight"`，1 passed / 190 skipped。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`npm test`，2 files / 191 tests passed。
- 通过：`git diff --check`。
- 已核对：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true` 显示 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 工作站前端/测试验证，没有触发真实 Nav2、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 未做真实上位机 HIL；地图刷新 gate 的硬件侧效果仍需现场按 UI 操作确认。
