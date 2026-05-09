# Sprint 2026.05.10 06-07 PRD

## 需求

fixed-route 当前已经能在 dry-run 下逐 checkpoint 做 visual gate，但路线级验收仍偏弱：用户或现场调试同学需要一个启动后即可读取的状态摘要，提前知道整条路线是否缺关键帧、是否存在不可读关键帧，以及视觉门控是否具备继续执行的最低证据。

## OKR 对齐

- Objective 3 KR3：dry-run 不只验证路线读取和单点匹配，还要能验证全路线关键帧覆盖。
- Objective 3 KR5：关键帧调试页面/状态文件能展示匹配准备度、失败原因和最近状态。
- Objective 5 KR4：远程诊断需要足够信息判断现场数据是否可用。

## 用户价值

现场学习路线后，普通调试流程可以先看状态文件或 debug web：如果 `missing_keyframes` 非空，就先补路线数据，不需要启动真实移动再逐点踩坑。

## 验收口径

- `debug_status_file` 写出 `keyframe_preflight`。
- 视觉门控开启时，缺 checkpoint keyframe 会在 preflight 中列出。
- 不可读或无 descriptor 的 keyframe 会在 preflight 中列出为 invalid。
- 视觉门控关闭时，preflight 不阻塞路线准备度。
- 回归测试和 smoke 通过。
