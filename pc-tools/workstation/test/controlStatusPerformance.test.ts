import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterAll, afterEach, describe, expect, it, vi } from "vitest";
import { writeFileSync } from "node:fs";
import App from "../src/App.vue";
import O7LiveOperatorPanel from "../src/components/O7LiveOperatorPanel.vue";
import { buildO7LiveOperatorPanel } from "../src/server/o7LiveOperatorPanel";
import { buildO7LocalWebrtcCamera } from "../src/server/o7LocalWebrtcCamera";
import {
  buildO7DirectUpperStatus, proxyO7DirectUpperManual,
  proxyO7DirectUpperStop, proxyO7DirectUpperRadarScanProofRefresh,
} from "../src/server/o7DirectUpperApi";

// 全链路仅使用假 fetch 和假媒体，禁止连接局域网或打开任何设备。
enableAutoUnmount(afterEach);
const observations: Record<string, unknown> = {};
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });
afterAll(() => {
  // 只有显式 probe 才写软件证据；正常测试不生成仓库杂项。
  if (process.env.ROBER_PC_PERFORMANCE_OUTPUT) {
    writeFileSync(process.env.ROBER_PC_PERFORMANCE_OUTPUT, JSON.stringify(observations));
  }
});

function deferred<T>() {
  // 可控释放点比固定 sleep 更稳定，也能证明停车发生在旧请求结束前。
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const env = { ROBER_UPPER_API_BASE_URL: "http://mock-upper.invalid" };

async function harness() {
  // 模拟健康数据只用于页面交互；其余安全字段沿用生产 builder。
  const camera = { ...await buildO7LocalWebrtcCamera({ env: {} }), status: "ready" };
  // 记录浏览器和代理两段路径，能分别核对本地与远端重复读取。
  const calls: string[] = [];
  // 延迟点按 URL 隔离，Stop 的返回不受普通请求承诺影响。
  const gates = new Map<string, Promise<Response>>();
  const mockFetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = String(input);
    calls.push(url);
    // 允许延迟任意本地或上位机响应，避免仅 mock 组件方法漏掉 API 契约。
    const gate = gates.get(url);
    if (gate) return gate;
    // 所有绝对地址都在此截断，任何遗漏都无法进入真实网络。
    if (url.startsWith("http")) return json({ status: "ready", accepted: true });
    // 按真实客户端编码解析请求体，使方向、确认材料和限幅继续经过代理。
    const body = init?.body ? JSON.parse(String(init.body)) : {};
    if (url === "/api/o7/live-operator-panel") return json(await buildO7LiveOperatorPanel());
    if (url === "/api/o7/direct-upper/status") return json(await buildO7DirectUpperStatus({ env }));
    if (url === "/api/o7/local-webrtc-camera") return json(camera);
    // 媒体模拟提供稳定的会话标识，便于验证刷新是否误发 close。
    if (url.endsWith("/offer")) return json({ type: "answer", sdp: "mock", peer_id: "mock-peer" });
    if (url.endsWith("/close")) return json({ closed: true });
    // 本地 POST 真实调用代理函数，覆盖客户端 JSON、代理与上位机结果三层。
    const result = url.endsWith("/base/manual") ? await proxyO7DirectUpperManual({ env, body })
      : url.endsWith("/base/stop") ? await proxyO7DirectUpperStop({ env, body })
        : await proxyO7DirectUpperRadarScanProofRefresh({ env, body });
    return json(result.payload, result.status);
  });
  vi.stubGlobal("fetch", mockFetch);
  return { calls, gates, mockFetch };
}

async function ready() {
  const api = await harness();
  // 挂载实际 App 和组件，不使用替代子组件掩盖生命周期错误。
  const wrapper = mount(App);
  await flushPromises();
  // 保留现有人工确认门，性能优化不放宽控制许可。
  await wrapper.get('input[aria-label="operator confirmation"]').setValue(true);
  return { ...api, wrapper };
}

class FakePeer {
  // 真实组件持有该媒体对象；刷新时断开会直接触发 close 断言。
  static instances: FakePeer[] = [];
  iceGatheringState = "complete";
  connectionState = "connected";
  localDescription: RTCSessionDescriptionInit | null = null;
  ontrack: ((event: { streams: object[] }) => void) | null = null;
  onconnectionstatechange: (() => void) | null = null;
  constructor() { FakePeer.instances.push(this); }
  addTransceiver = vi.fn();
  getReceivers = () => [];
  getSenders = () => [];
  // 关闭行为独立计数，持续挂载之外还需保证媒体资源存活。
  close = vi.fn();
  // 完整模拟 offer/answer 进入 playing 状态，避免空壳组件挂载检查。
  createOffer = async () => ({ type: "offer", sdp: "mock" }) as RTCSessionDescriptionInit;
  setLocalDescription = async (description: RTCSessionDescriptionInit) => { this.localDescription = description; };
  setRemoteDescription = async () => { this.ontrack?.({ streams: [{}] }); };
}

describe("PC control/status performance contracts", () => {
  it.each(["manual", "operator"])("dispatches Stop while %s is pending and ignores its late result", async (kind) => {
    // 每例新建确认状态和请求表，避免跨测试共享在途工作。
    const { wrapper, calls, gates } = await ready();
    const pending = deferred<Response>();
    const path = kind === "manual" ? "/api/base/manual" : "/api/radar/scan-proof/refresh";
    gates.set(`${env.ROBER_UPPER_API_BASE_URL}${path}`, pending.promise);
    // 普通动作保持未返回，停车按钮仍须可用且立即进入独立代理。
    const start = kind === "manual" ? wrapper.get(".forward")
      : wrapper.findAll(".operator-button").find((button) => button.text() === "Refresh scan proof")!;
    await start.trigger("click");
    await flushPromises();
    expect(wrapper.get(".stop").attributes("disabled")).toBeUndefined();
    await wrapper.get(".stop").trigger("click");
    await flushPromises();
    // 此断言发生在 pending.resolve 之前，直接证明停车未排队。
    expect(calls).toContain(`${env.ROBER_UPPER_API_BASE_URL}/api/base/stop`);
    const stopMessage = wrapper.get(".lock-message").text();
    expect(stopMessage).toContain("Stop 已发送");
    // 旧的抢占响应随后返回，不能盖掉较新的停车回执或声明运动成功。
    // 主动结束旧请求，兼顾抢占回执校验与测试资源清理。
    pending.resolve(json({ accepted: true, preempted: true }));
    await flushPromises();
    expect(wrapper.get(".lock-message").text()).toBe(stopMessage);
    observations[`${kind}_pending_stop_dispatched`] = true;
    observations[`${kind}_late_result_overwrote_stop`] = false;
  });

  it("routes Space to Stop while manual is pending and keeps confirmation", async () => {
    // 每例新建确认状态和请求表，避免跨测试共享在途工作。
    const { wrapper, calls, gates } = await ready();
    const pending = deferred<Response>();
    gates.set(`${env.ROBER_UPPER_API_BASE_URL}/api/base/manual`, pending.promise);
    await wrapper.get(".forward").trigger("click");
    // 键盘停车复用独立 Stop；不借道 manual，也不受 manual busy 约束。
    window.dispatchEvent(new KeyboardEvent("keydown", { key: " ", code: "Space" }));
    await flushPromises();
    expect(calls.filter((url) => url === "/api/o7/direct-upper/base/manual")).toHaveLength(1);
    expect(calls).toContain("/api/o7/direct-upper/base/stop");
    // 主动结束旧请求，兼顾抢占回执校验与测试资源清理。
    pending.resolve(json({ accepted: true, preempted: true }));
    await flushPromises();
    // 新会话仍需原有确认，避免通过快捷键跳过许可。
    await wrapper.get('input[aria-label="operator confirmation"]').setValue(false);
    const stops = calls.filter((url) => url.endsWith("/base/stop")).length;
    window.dispatchEvent(new KeyboardEvent("keydown", { key: " " }));
    await flushPromises();
    expect(calls.filter((url) => url.endsWith("/base/stop"))).toHaveLength(stops);
    observations.space_uses_independent_stop = true;
  });

  it("releases manual after ACK without awaiting status and preserves Stop during stale readback", async () => {
    const { wrapper, gates, calls } = await ready();
    // 单独卡住状态回读，用于区分动作 ACK 和展示更新关键路径。
    const pendingStatus = deferred<Response>();
    const oldStatus = await buildO7DirectUpperStatus({ env });
    gates.set("/api/o7/direct-upper/status", pendingStatus.promise);
    await wrapper.get(".forward").trigger("click");
    await flushPromises();
    // 状态仍在等待，但动作按钮已经释放，停车同样可立即发出。
    expect(wrapper.get(".forward").attributes("disabled")).toBeUndefined();
    await wrapper.get(".stop").trigger("click");
    await flushPromises();
    // manual 和 Stop 的后台刷新共享在途请求，不叠加读取压力。
    expect(calls.filter((url) => url === "/api/o7/direct-upper/status")).toHaveLength(1);
    observations.action_status_reads_max_inflight = 1;
    // 较旧状态到达只能更新状态区域，不能重写操作结果。
    const message = wrapper.get(".lock-message").text();
    pendingStatus.resolve(json(oldStatus));
    await flushPromises();
    expect(wrapper.get(".lock-message").text()).toBe(message);
    observations.ack_waits_for_status = false;
  });

  it("reads upper status once per refresh and preserves the existing media connection", async () => {
    FakePeer.instances = [];
    vi.stubGlobal("RTCPeerConnection", FakePeer);
    vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);
    // 每例新建确认状态和请求表，避免跨测试共享在途工作。
    const { wrapper, calls, gates } = await ready();
    const upperStatusCount = () => calls.filter((url) => url.startsWith("http") && url.endsWith("/api/status")).length;
    // 初次加载已捆绑 direct 摘要，不允许再启动第二次远端状态请求。
    expect(upperStatusCount()).toBe(1);
    expect(calls).not.toContain("/api/o7/direct-upper/status");
    await wrapper.findAll("button").find((button) => button.text() === "重新连接预览")!.trigger("click");
    await flushPromises();
    // 内部 uid 稳定标识组件；测试工具生成的 vm 包装代理不能比较身份。
    const panelId = wrapper.getComponent(O7LiveOperatorPanel).vm.$.uid;
    const video = wrapper.get("video").element;
    const peer = FakePeer.instances[0]!;
    expect(wrapper.text()).toContain("摄像头画面已连接");
    // 保持刷新请求在途，检查 loading 状态中的实例、视频节点和连接。
    const pending = deferred<Response>();
    gates.set("/api/o7/live-operator-panel", pending.promise);
    await wrapper.get(".console-refresh").trigger("click");
    await wrapper.get(".console-refresh").trigger("click");
    expect(wrapper.getComponent(O7LiveOperatorPanel).vm.$.uid).toBe(panelId);
    expect(wrapper.get("video").element).toBe(video);
    expect(peer.close).not.toHaveBeenCalled();
    expect(calls.filter((url) => url === "/api/o7/live-operator-panel")).toHaveLength(2);
    // 调用生产聚合 builder 生成刷新结果，统计一次真实逻辑链的远端读取。
    pending.resolve(json(await buildO7LiveOperatorPanel()));
    await flushPromises();
    expect(upperStatusCount()).toBe(2);
    expect(peer.close).not.toHaveBeenCalled();
    expect(calls.some((url) => url.endsWith("/close"))).toBe(false);
    // 计数仅对应这次通过断言的离线刷新，不推算设备 CPU 或媒体时延。
    observations.upper_status_requests_per_refresh = 1;
    observations.refresh_media_unmounts = 0;
    observations.refresh_media_close_requests = 0;
    observations.refresh_duplicate_click_requests = 1;
  });

  it.each(["busy", "preempted"])("preserves %s response through proxy and UI without changing safety fields", async (kind) => {
    const { wrapper, gates } = await ready();
    const remoteBody = kind === "busy"
      ? { accepted: false, preempted: false, error: { type: "serial_busy", message: "another request owns serial" }, sends_commands: false }
      : { accepted: true, preempted: true, auto_stop_executed: true };
    // 每个请求获得自己的 Response，避免读取同一个 body 引入假失败。
    const response = () => json(remoteBody, kind === "busy" ? 409 : 200);
    gates.set(`${env.ROBER_UPPER_API_BASE_URL}/api/base/manual`, Promise.resolve(response()));
    // 分别检查 HTTP 状态和业务字段，防止 409 被网关统一转换为 502。
    const proxy = await proxyO7DirectUpperManual({ env, body: { direction: "forward" } });
    expect(proxy.status).toBe(kind === "busy" ? 409 : 200);
    expect(proxy.payload.upper_accepted).toBe(remoteBody.accepted);
    expect(proxy.payload.preempted).toBe(remoteBody.preempted);
    // 拒绝与抢占都保持关闭的安全状态，HTTP200 不能覆盖该语义。
    expect(proxy.payload.fail_closed).toBe(true);
    // 固定安全边界不得因 HTTP 接受或优先停车而变成实机闭环证明。
    expect(proxy.payload.safe_to_control).toBe(false);
    expect(proxy.payload.sends_commands).toBe(false);
    expect(proxy.payload.robot_control_executed).toBe(false);
    expect(proxy.payload.robot_ack_connected).toBe(false);
    gates.set(`${env.ROBER_UPPER_API_BASE_URL}/api/base/manual`, Promise.resolve(response()));
    // 同一个真实 Vue 用户流程再消费代理结果，确保提示文案可见。
    await wrapper.get(".forward").trigger("click");
    await flushPromises();
    const message = wrapper.get(".lock-message").text();
    expect(message).toContain(kind === "busy" ? "串口忙（serial_busy）" : "已被 Stop 中断（preempted）");
    expect(message).toContain("safe_to_control=false");
    observations[`${kind}_contract_preserved`] = true;
  });
});
