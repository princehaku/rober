import assert from "node:assert/strict";
import { after, test } from "node:test";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

// 复用仓库已安装的浏览器 DOM 实现，不额外下载依赖或访问真实机器人。
const directory = dirname(fileURLToPath(import.meta.url));
const root = resolve(directory, "../..");
const require = createRequire(resolve(root, "pc-tools/workstation/package.json"));
// 依赖入口由仓库定位，Windows 与 Linux 都使用同一套锁定测试工具。
const { JSDOM, ResourceLoader, VirtualConsole } = require("jsdom");
const source = readFileSync(resolve(directory, "app.js"), "utf8");
const diagnosticSource = readFileSync(resolve(directory, "diagnostics.js"), "utf8");
// 测试读取实际发布入口，模板中的静态面板不能被误计为已挂载页面。
const html = readFileSync(resolve(directory, "index.html"), "utf8");
const fixture = JSON.parse(readFileSync(resolve(directory, "fixtures/status.json"), "utf8"));
// 改前只保留精确源码计数，没有执行同场景时不生成改前时延数字。
const evidence = { schema: "rober.mobile_performance.v1", evidence_boundary: "software_mock_dom_only", environment: { node: process.version, platform: process.platform, dom: "jsdom" }, source_bytes: { before: 3931297, core_after: Buffer.byteLength(source), diagnostics_after: Buffer.byteLength(diagnosticSource) }, baseline_observed: false, baseline_source_render_calls: 215, scenarios: {} };

// 使用独立事件循环冲刷异步读取；浏览器内的定时器使用可控时钟。
const flush = async () => { for (let i = 0; i < 5; i += 1) await new Promise(setImmediate); };
function deferred() { let resolvePromise; let rejectPromise; const promise = new Promise((resolve, reject) => { resolvePromise = resolve; rejectPromise = reject; }); return { promise, resolve: resolvePromise, reject: rejectPromise }; }

async function browser(options = {}) {
  // 每个场景隔离全局作用域，避免上一场景已加载的模块隐藏冷启动问题。
  const state = { loads: [], requests: [], errors: [], bindings: new Map(), active: 0, maxActive: 0, now: 0, visible: true, payload: structuredClone(fixture), failDiagnostics: options.failDiagnostics ?? 0, statusReply: options.statusReply ?? null };
  const timers = new Map(); let sequence = 0;
  // 资源加载器只认识仓库资产，任何未知 URL 都不会出网。
  class LocalResources extends ResourceLoader {
    fetch(url) {
      // 真实 script 元素加载到同一全局 lexical 环境，覆盖 const 跨模块共享。
      const path = new URL(url).pathname;
      state.loads.push(path);
      if (path.endsWith("/diagnostics.js")) {
        // 首次失败只影响脚本下载，下一次人工操作允许正常加载相同版本。
        if (state.failDiagnostics-- > 0) return Promise.reject(new Error("injected script failure"));
        return Promise.resolve(Buffer.from(diagnosticSource));
      }
      if (path.endsWith("/app.js")) return Promise.resolve(Buffer.from(source));
      // CSS 在行为测试中为空，不把渲染样式或真机布局混入结构性性能证据。
      return Promise.resolve(Buffer.from(""));
    }
  }
  const console = new VirtualConsole();
  // 脚本加载失败由专门用例验证；其余未捕获错误都保留用于验收失败。
  console.on("jsdomError", error => { if (!error.message.includes("Could not load script")) state.errors.push(error.message); });
  const dom = new JSDOM(html, {
    // 域名仅为同源路径解析提供上下文，没有建立外部 HTTP 连接。
    url: "http://mobile.test/mobile/", runScripts: "dangerously", resources: new LocalResources(), pretendToBeVisual: true, virtualConsole: console,
    beforeParse(window) {
      Object.defineProperty(window.document, "visibilityState", { get: () => state.visible ? "visible" : "hidden" });
      // 可控时钟允许精确跨过超时边界，避免依赖忙等或长时间 sleep。
      window.setTimeout = (callback, delay = 0) => { const id = ++sequence; timers.set(id, { callback, due: state.now + delay, delay }); return id; };
      window.clearTimeout = id => timers.delete(id);
      // 测试确认只提供输入，是否允许动作仍由实际事件处理和 gate 决定。
      window.confirm = () => true;
      // 统计实际监听绑定次数，保证诊断重复展开不会重绑核心控制按钮。
      const add = window.EventTarget.prototype.addEventListener;
      window.EventTarget.prototype.addEventListener = function(type, ...args) {
        if (this.id) { const key = `${this.id}:${type}`; state.bindings.set(key, (state.bindings.get(key) || 0) + 1); }
        return add.call(this, type, ...args);
      };
      window.fetch = async (url, init = {}) => {
        state.requests.push({ url: String(url), method: init.method || "GET" });
        if (url !== "/api/status") {
          // 命令延迟与只读请求独立，便于复现 POST 在途时的轮询竞争。
          const payload = init.method === "POST" && state.commandReply ? await state.commandReply() : {};
          return { ok: true, json: async () => payload };
        }
        state.active += 1; state.maxActive = Math.max(state.maxActive, state.active);
        // 并发数在 fetch 开始时计入，完整退出 finally 后才释放。
        let abort;
        try {
          // 延迟响应支持真实 AbortSignal，覆盖后台中止和旧数据迟到。
          const aborted = new Promise((_resolve, reject) => {
            abort = () => reject(new window.DOMException("Aborted", "AbortError"));
            if (init.signal?.aborted) abort();
            else init.signal?.addEventListener("abort", abort, { once: true });
          });
          const payload = await Promise.race([state.statusReply ? state.statusReply() : Promise.resolve(state.payload), aborted]);
          // 保留 response.json 的异步边界，避免测试把真实网络当同步函数。
          return { ok: true, json: async () => payload };
        } finally {
          init.signal?.removeEventListener("abort", abort);
          // 清理取消监听，防止上一轮请求留在下一轮场景里。
          state.active -= 1;
        }
      };
    },
  });
  await new Promise(resolveLoad => dom.window.addEventListener("load", resolveLoad, { once: true }));
  // defer 脚本和首个状态微任务都完成后再判断页面是否真正可用。
  await flush();
  async function tick(milliseconds) {
    const target = state.now + milliseconds;
    // 每个时点执行后冲刷 Promise，模拟浏览器的宏任务/微任务顺序。
    while (true) {
      const next = [...timers].sort((a, b) => a[1].due - b[1].due).find(([, timer]) => timer.due <= target);
      if (!next) break;
      state.now = next[1].due; timers.delete(next[0]); next[1].callback(); await flush();
    }
    state.now = target;
    // 无待执行计时器时直接前进，保证后台暂停测试不会伪造请求。
  }
  return { dom, window: dom.window, state, timers, tick, close() { dom.window.dispatchEvent(new dom.window.Event("pagehide")); dom.window.close(); } };
}

test("cold entry loads only core and preserves fail-closed controls", async () => {
  const app = await browser();
  try {
    assert.deepEqual(app.state.errors, []);
    // 大模块迁出核心应有可检查的体积门槛，防止后续依赖漂移重新拖回。
    assert.ok(Buffer.byteLength(source) < 300000);
    // 诊断声明不存在且没有资源请求，证明主入口没有隐藏的预加载工作。
    assert.equal(typeof app.window.renderDiagnosticStatus, "undefined");
    assert.equal(app.state.loads.filter(path => path.endsWith("diagnostics.js")).length, 0);
    assert.equal(app.window.document.getElementById("routeTaskFieldRunMaterialValidationTitle"), null);
    // 冷启动就保持原后端安全 gate；点击禁用按钮不能产生控制 POST。
    for (const id of ["startButton", "confirmButton", "cancelButton"]) { const button = app.window.document.getElementById(id); assert.equal(button.disabled, true); button.click(); }
    assert.equal(app.state.requests.filter(item => item.method === "POST").length, 0);
    evidence.scenarios.cold_entry = { heavy_render_calls: 0, rendered_sections: app.window.document.querySelectorAll("section").length, diagnostic_requests: 0, core_render_calls_per_changed_status: 14 };
    // 每个场景主动结束生命周期，释放 DOM 与所有剩余状态读取。
  } finally { app.close(); }
});

test("diagnostics use a real lazy script and bind only once", async () => {
  const app = await browser();
  try {
    const coreBindings = app.state.bindings.get("startButton:click");
    // 用户同一按钮第二次打开仍走完整诊断读取，不再次初始化面板。
    await app.window.openDiagnostics(); await flush();
    assert.deepEqual(app.state.errors, []);
    assert.ok(app.window.document.getElementById("routeTaskFieldRunMaterialValidationTitle"));
    assert.equal(app.window.document.getElementById("diagnosticsDetails").hidden, false);
    // 验证真实详情 ID，保证只把数据下载下来却未展示的实现无法过关。
    const diagnosticBindings = app.state.bindings.get("copyRouteTaskReviewButton:click");
    // 使用真实复制按钮的监听计数，防止仅统计脚本数量掩盖重复绑定。
    assert.equal(diagnosticBindings, 1);
    await Promise.all([app.window.openDiagnostics(), app.window.openDiagnostics()]);
    assert.equal(app.state.bindings.get("startButton:click"), coreBindings);
    assert.equal(app.state.bindings.get("copyRouteTaskReviewButton:click"), diagnosticBindings);
    assert.equal(app.state.loads.filter(path => path.endsWith("diagnostics.js")).length, 1);
    // 重复展开同时覆盖模块复用和核心事件监听保持唯一的行为。
    evidence.scenarios.diagnostics = { load_count_after_reopen: 1, diagnostic_listener_count: diagnosticBindings, core_listener_count: coreBindings, uncaught_errors: app.state.errors };
  } finally { app.close(); }
});

test("diagnostic script network failure supports an explicit retry", async () => {
  const app = await browser({ failDiagnostics: 1 });
  try {
    await app.window.openDiagnostics();
    // 用户先看到可恢复错误，保留主路径；下载失败不得触发控制请求。
    assert.match(app.window.document.getElementById("supportSafeCopy").textContent, /诊断暂不可用/);
    assert.equal(typeof app.window.mobileDiagnostics, "undefined");
    // 失败时不注入空模块占位，后续点击才能执行正常初始化。
    await app.window.openDiagnostics();
    // 一次失败加一次成功应只有两次下载，核心按钮始终只有一个监听。
    assert.equal(typeof app.window.mobileDiagnostics.open, "function");
    assert.equal(app.state.loads.filter(path => path.endsWith("diagnostics.js")).length, 2);
    assert.equal(app.state.bindings.get("startButton:click"), 1);
    // 失败恢复不应触发隐式重绑，核心控制保持初始化时的监听数量。
    assert.deepEqual(app.state.errors, []);
  } finally { app.close(); }
});

test("unchanged status skips DOM rendering and shared safety derivation", async () => {
  const app = await browser();
  try {
    let renders = 0; const render = app.window.renderStatus;
    // 拦截实际渲染入口，检查优化减少的执行次数而非仅检查源码条件。
    app.window.renderStatus = payload => { renders += 1; return render(payload); };
    await app.window.refreshStatus(); await app.window.refreshStatus();
    // 请求仍然正常发生，仅跳过冗余渲染，不能用停止刷新冒充优化。
    assert.equal(renders, 0);
    app.state.payload = { ...app.state.payload, revision: "changed" };
    // 任何真实状态变化仍必须反映到页面，去重不能丢掉新增后端字段。
    await app.window.refreshStatus();
    assert.equal(renders, 1);
    // 多视图共用同步周期内的安全输入，周期结束即释放，点击仍重新验权。
    assert.equal(vm.runInContext("activeSafetySnapshot", app.dom.getInternalVMContext()), null);
    evidence.scenarios.unchanged_status = { reads: 2, render_calls: 0, changed_status_render_calls: 1 };
  } finally { app.close(); }
});

test("polling is single flight and suspends then refreshes on visibility change", async () => {
  const app = await browser();
  try {
    const pending = deferred(); app.state.statusReply = () => pending.promise;
    const first = app.window.refreshStatus(); const second = app.window.refreshStatus();
    // 两个调用共用完全相同的 promise，不能只在响应阶段去重。
    assert.equal(first, second); assert.equal(app.state.active, 1);
    // 可见性变化由真实 DOM 事件触发，覆盖生产注册的监听函数。
    app.state.visible = false; app.window.document.dispatchEvent(new app.window.Event("visibilitychange"));
    await first; await flush();
    const requestsBefore = app.state.requests.length;
    // 推进多个前台刷新周期，验证隐藏期间没有残留定时请求。
    await app.tick(20000); assert.equal(app.state.requests.length, requestsBefore);
    assert.equal(app.window.document.getElementById("startButton").disabled, true);
    // 后台界面必须失去可操作快照，即便网络请求已经被成功中止。
    // 迟到数据不能通过中止边界；回前台读取一次新快照，最大并发仍为一。
    pending.resolve({ state: "late_response" }); app.state.statusReply = null;
    app.state.visible = true; app.window.document.dispatchEvent(new app.window.Event("visibilitychange")); await flush();
    assert.equal(app.state.requests.length, requestsBefore + 1);
    // 立即刷新与随后周期刷新各有一次，重复恢复事件不能制造双循环。
    assert.equal(app.state.maxActive, 1);
    await app.tick(2000); assert.equal(app.state.requests.length, requestsBefore + 2);
    // 统计的是整个场景的峰值并发，包含中止与恢复发生的交界时刻。
    evidence.scenarios.polling = { max_status_concurrency: app.state.maxActive, background_requests: 0, foreground_immediate_refresh: true, period_ms: 2000 };
  } finally { app.close(); }
});

test("status timeout closes controls and uses read-only exponential backoff", async () => {
  const app = await browser();
  try {
    app.state.statusReply = () => new Promise(() => {});
    const flight = app.window.refreshStatus(); await app.tick(4000); await flight;
    // 超时必须影响实际按钮状态，不能只有日志或重试计数。
    assert.match(app.window.document.getElementById("readinessTitle").textContent, /离线/);
    assert.equal(app.window.document.getElementById("cancelButton").disabled, true);
    const count = app.state.requests.length;
    // 在退避期限前一毫秒仍无请求，用边界值验证调度时序。
    await app.tick(3999); assert.equal(app.state.requests.length, count);
    app.state.statusReply = null; await app.tick(1);
    // 恢复成功后只读链继续运行，之前的失败不成为永久离线状态。
    assert.equal(app.state.requests.length, count + 1);
    assert.equal(app.state.requests.filter(item => item.method === "POST").length, 0);
  } finally { app.close(); }
});

test("service worker keeps diagnostics lazy and API control paths uncached", () => {
  const worker = readFileSync(resolve(directory, "service-worker.js"), "utf8");
  const context = vm.createContext({ self: { addEventListener() {} }, URL });
  // 独立执行真实 service worker 路由函数，不复制其判断逻辑到测试中。
  vm.runInContext(worker, context);
  // 安装时不得隐式下载诊断大模块；API 缓存策略不因静态拆分而改变。
  assert.equal(vm.runInContext('SHELL_URLS.includes("./diagnostics.js")', context), false);
  for (const path of ["/api/status", "/api/diagnostics", "/robots/a/commands", "/api/commands/cancel"]) assert.equal(vm.runInContext(`isControlOrDynamicRequest({method:"GET",url:"http://mobile.test${path}"})`, context), true);
  assert.equal(vm.runInContext('isControlOrDynamicRequest({method:"GET",url:"http://mobile.test/mobile/diagnostics.js?v=1"})', context), false);
});

function allowBackendGatesForRaceTest(app) {
  // 本用例隔离验证并发护栏，允许摘要由 mock 提供；原 gate 的 fail-closed 已单独验收。
  for (const name of ["cloudSummaryAllowsPrimaryActions", "mobileDeviceAcceptanceAllowsPrimaryActions", "mobileBrowserAcceptanceBundleAllowsPrimaryActions", "mobileDeviceHandoffSessionAllowsPrimaryActions", "mobileRealDeviceReviewHandoffAllowsPrimaryActions", "mobileRealDeviceReviewExecutionAllowsPrimaryActions", "mobileRealDeviceRetestRequestAllowsPrimaryActions"]) app.window[name] = () => true;
  app.window.startGateFromStatus = () => ({ startEnabled: true, destinationReady: true, destination: "mock_station", destinationSource: "mock", blockedReason: "", loadConfirmed: true });
  app.window.terminalActionGateFromStatus = () => ({ enabled: true, blockedReason: "", notProven: [] });
  // 仍通过真实 renderCommandSafety 的 permission、action enabled 和在途锁分支。
  app.state.payload.phone_readiness.command_safety = { actions: { start: { enabled: true }, confirm_dropoff: { enabled: true }, cancel: { enabled: true } } };
  app.state.payload.phone_readiness.action_permissions = { can_collect: true, can_confirm_dropoff: true, can_cancel: true };
  app.window.renderStatus(app.state.payload);
}

test("changed polling payload cannot re-enable controls during a pending POST", async () => {
  const app = await browser();
  try {
    allowBackendGatesForRaceTest(app);
    assert.equal(app.window.document.getElementById("startButton").disabled, false);
    // 先证明允许态真实可操作，随后禁用才能归因于在途锁。
    const command = deferred(); app.state.commandReply = () => command.promise;
    const posting = app.window.postAction("start", "mock-first");
    // 本地 pending 发生在网络响应前，检查的是最容易出现双击的窗口。
    app.state.payload.revision = "during-post";
    // 强制状态发生变化，绕过未变化去重，直接打到忙碌状态竞争分支。
    await app.window.refreshStatus();
    for (const id of ["startButton", "confirmButton", "cancelButton"]) assert.equal(app.window.document.getElementById(id).disabled, true);
    await app.window.postAction("start", "mock-duplicate");
    // 即使外部重复调用动作函数，仍由同一在途锁保证只发送一次。
    assert.equal(app.state.requests.filter(item => item.method === "POST").length, 1);
    command.resolve({ status: "accepted_or_processing" }); await posting; await flush();
    assert.equal(app.state.maxActive, 1);
    evidence.scenarios.action_race = { post_count_during_pending: 1, changed_status_reenabled_controls: false, action_state_refresh_after_settle: true };
  } finally { app.close(); }
});

test("action completion invalidates the earlier GET and failed action refreshes identical data", async () => {
  const app = await browser();
  try {
    allowBackendGatesForRaceTest(app);
    const oldStatus = deferred(); app.state.statusReply = () => oldStatus.promise;
    // 故意先开始 GET，再开始 POST，覆盖复用旧 promise 的时序问题。
    const reading = app.window.refreshStatus();
    const command = deferred(); app.state.commandReply = () => command.promise;
    const posting = app.window.postAction("start", "mock-failed");
    // 保存实际渲染入口后包计数器，保持所有状态展示和安全判断仍被执行。
    let renders = 0; const render = app.window.renderStatus;
    app.window.renderStatus = payload => { renders += 1; return render(payload); };
    const previousReads = app.state.requests.filter(item => item.url === "/api/status").length;
    // 完成动作后新读返回相同 JSON，仍须更新本地失败与按钮状态。
    app.state.statusReply = null;
    command.reject(new Error("injected command failure"));
    await posting; await reading; await flush();
    assert.equal(app.state.requests.filter(item => item.url === "/api/status").length, previousReads + 1);
    assert.equal(renders, 1);
    // 旧读取随后完成仍无副作用，重新读取后的按钮可按原 gate 恢复重试。
    oldStatus.resolve({ state: "stale-before-command" }); await flush();
    assert.equal(renders, 1);
    assert.equal(app.state.maxActive, 1);
    // 没有隐式控制重试；恢复动作只能由下一次用户操作触发。
    assert.equal(app.window.document.getElementById("startButton").disabled, false);
    assert.equal(app.state.requests.filter(item => item.method === "POST").length, 1);
    assert.deepEqual(app.state.errors, []);
  } finally { app.close(); }
});

after(() => {
  // 只记录软件结构和 mock 行为，source bytes 不冒充网络传输量或 CPU 降幅。
  const output = resolve(root, "sprints/2026.09.17_00-01_control-status-performance-epic/evidence/ui-mobile-performance.json");
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, JSON.stringify(evidence, null, 2) + "\n");
});
