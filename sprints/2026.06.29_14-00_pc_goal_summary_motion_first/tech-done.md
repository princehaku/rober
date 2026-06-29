# PC 目标总览先引导可动项 micro sprint

sprint_type: micro

## 实际改动

- 调整 `goal_checklist_summary.summary_plain`：当存在可现场收口项时，先显示“先做：<可操作项>”，不再默认把首个未完成项“画面所见即所得”作为主动作。
- 调整 `goal_checklist_summary.next_action_plain`：优先返回可现场收口的运动项下一步；当前 live 形态指向自由自助移动。
- 保留相机、雷达、建图缺口在“未就绪项”里，避免隐藏真正 blockers。

## 验证结果

- `npm --prefix pc-tools/workstation test`：通过，379 个 tests。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 仍提示现有 bundle 超过 500 kB。
- 已重启 PC Node 到 `0.0.0.0:7001`；新进程 PID `25947`。
- `GET http://127.0.0.1:7001/api/robot-control/summary`：只读验证通过，`goal_checklist_summary.summary_plain` 包含“先做：自由自助移动”和“未就绪项：画面所见即所得、雷达点贴到地图、传感器就绪后建图”，且不再包含“先补条件：画面所见即所得”。

## 剩余风险

- 摄像头仍未出首帧；当前证据是 UVC 设备没有输出视频帧，不是页面独占。
- 雷达仍未运行或扫描已停；地图雷达点仍为 0 个，旧来源点只作诊断。
- Nav2、键盘连续手控、自由自助移动仍需要现场安全确认和真实运动验证。
