# Sprint 2026.05.10 15-16 Integrity Status UI - Side2Side Check

## 状态

- 阶段：side2side_check completed。
- 时间：2026-05-10 15:45 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现主责：`full-stack-software-engineer`。

## 用户价值和产品北极星

本轮用户价值是把上一轮后端已有的 vision sample manifest 完整性诊断，推进到普通用户和现场支持能打开的 operator 页面。用户不需要 SSH、ROS2 CLI、manifest checker 知识或文件系统排查，也能看到 Vision evidence chain 是否健康、为什么不健康、下一步怎么恢复。

产品北极星保持不变：普通用户只靠手机完成垃圾投递任务，并在异常时看到清楚的人话提示和恢复路径。

## OKR 映射

| OKR | 本轮验收判断 | 证据 |
| --- | --- | --- |
| Objective 5 KR4 远程诊断最小数据包 | 通过本轮产品验收；诊断包不再只停留在 raw JSON，可被 operator 页面消费 | Vision evidence chain 卡片展示健康状态、缺失原因、context coverage、file counts 和恢复建议 |
| Objective 5 KR5 普通用户验收标准 | 部分推进；页面文案更接近普通用户可理解，但还没有真实手机浏览器截图和普通用户实测 | HTTP 页面静态测试覆盖 DOM id、状态映射函数和字段名 |
| Objective 4 KR3 视觉样本目录和 manifest contract | 部分推进；manifest checker 结果已经进入用户触点，但真实 camera/odom manifest 上车证据仍缺 | 页面消费 `integrity_summary`、missing refs、error/warning、context coverage 和 file counts |

## KR 拆解或更新

- Objective 5：当前进度从约 72% 更新为约 74%。本轮增量集中在手机本地 operator 页面的可读诊断，而不是完整手机产品、喇叭/TTS 或量产硬件实物验收。
- Objective 4：当前进度从约 67% 更新为约 68%。本轮增量是视觉证据链诊断进入用户触点，不代表视觉算法、真实数据集或上车采集闭环完成。
- Objective 1/2/3：本轮没有硬件、行为状态机、导航或固定路线实质改动，进度保持不变。

## 对照验收

| 计划验收口径 | 实际结果 | 产品判断 |
| --- | --- | --- |
| operator 页面能显示视觉证据链健康状态 | 已实现 Vision evidence chain 诊断卡片 | 通过 |
| `ok/warning/error/not_configured/checker_unavailable/checker_failed` 有清晰文案 | `tech-done.md` 记录映射为 Healthy、Needs review、Broken、Not configured、Checker unavailable、Checker failed | 通过 |
| 缺失原因和恢复建议可读 | 页面展示最多 3 条原因，并给出恢复建议 | 通过 |
| 旧 diagnostics JSON 和控制能力不回退 | `tech-done.md` 记录 raw status JSON、API failure path 和既有 diagnostics 元素保留 | 通过 |
| 有自动化验证证据 | Full-Stack Engineer 记录 HTTP 页面测试 16 OK、py_compile OK、git diff --check OK、完整 smoke 通过；Coordinator 复跑前三项通过 | 通过 |
| 真实手机浏览器或上车证据 | 本轮没有真实手机浏览器截图，也没有真实 camera/odom manifest 上车验证 | 未覆盖，进入剩余风险 |

## 做什么 / 不做什么

做了：

- 把 `/api/diagnostics.vision_samples.integrity_summary` 变成 operator 页面 Vision evidence chain 诊断卡片。
- 把 missing refs、integrity errors/warnings、read error、context coverage 和 file counts 从工程字段转成用户触点可读信息。
- 以 HTTP 页面测试、py_compile、diff check 和完整 smoke 作为本轮工程护栏。

没有做：

- 没有新增视觉算法、manifest checker 字段或 ROS2 contract。
- 没有做真实手机浏览器截图。
- 没有做真实 camera/odom manifest 上车验证。
- 没有验证喇叭/TTS、量产硬件实物或普通用户现场流程。

## 优先级和责任 Engineer

- 本轮优先级：P0，原因是 Objective 5 的手机诊断入口缺口直接影响普通用户和现场支持能否理解视觉证据链异常。
- 已完成责任 Engineer：`full-stack-software-engineer`。
- 后续如要补真实手机截图，仍归 `full-stack-software-engineer`。
- 后续如要补真实 camera/odom manifest 上车证据，需要 `autonomy-engineer` 和 `hardware-engineer` 参与，必要时由 `robot-software-engineer` 做 ROS2 主链路集成验收。

## 风险、阻塞和证据链

- 风险：当前证据主要来自 HTTP 静态测试和 smoke，不能替代真实手机浏览器视觉验收。
- 风险：当前页面只消费 diagnostics 字段，不能证明真实 camera/odom manifest 会持续产出。
- 风险：Vision evidence chain 的文案和状态依赖 diagnostics builder 与 manifest checker 语义，后续字段变化时需要同步页面映射。
- 阻塞：无产品方向阻塞；下一轮应优先补真实手机截图和一次真实 manifest 上车/采集证据。

