# PC Map Preview Plain Hint

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- started_at: 2026-06-29 04:57 CST
- status: done

## 实际改动

- 扩展 PC Node 只读 `GET /api/robot-control/map/preview` 响应合同，新增顶层 `plain_hint`。
- `plain_hint` 直接对齐 `map_wysiwyg_status_plain`，让现场脚本或普通页面只看顶层字段时，也能知道当前地图画面、图上路线、小车位置和雷达 marker 是否所见即所得。
- 成功响应与 blocked/fallback 响应都填充 `plain_hint`，避免地图读取失败、JSON 异常或安全拦截时出现空顶层提示。
- 补充 map preview 回归测试，锁定完整地图/路线/雷达显示、定位缺失的局部雷达、旧雷达来源点不贴图三类场景中，`plain_hint` 与 `map_wysiwyg_status_plain` 一致。
- 同步 `docs/product/pc_tools_workstation.md`，说明该字段仍然只消费只读 map preview 和 overlay，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map preview"`：通过，2 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个测试文件、375 个测试通过。
- 重启 PC API 到 `0.0.0.0:7001` 后执行只读 `GET /api/robot-control/map/preview`：通过，返回 `plain_hint=地图画面、图上路线和小车位置已显示；雷达来源点存在但当前不贴到地图...`，且与 `map_wysiwyg_status_plain` 一致；`radar_overlay_point_count=0`、`radar_overlay_source_point_count=81`、`robot_control_executed=false`。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只增强 map preview 的只读顶层可读性；真实地图所见即所得仍取决于上车端 map preview、定位、Nav2 path 和雷达 overlay 是否返回当前材料。
