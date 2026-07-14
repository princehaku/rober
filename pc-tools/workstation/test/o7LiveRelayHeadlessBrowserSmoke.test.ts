import { describe, expect, it } from "vitest";
import path from "node:path";
import {
  chromeDumpDomArgs,
  extractJsonFromChromeDumpDom,
  parseArgs,
} from "../src/server/o7LiveRelayHeadlessBrowserSmoke";

describe("o7LiveRelayHeadlessBrowserSmoke", () => {
  it("extracts JSON from the headless Chrome application/json DOM wrapper", () => {
    // Chrome 对 JSON 响应会包一层 pre；解析层必须消费浏览器 DOM，而不是要求 raw fetch JSON。
    const payload = extractJsonFromChromeDumpDom(
      '<html><head></head><body><pre style="word-wrap: break-word;">{"schema":"demo.v1","safe_to_control":false}</pre></body></html>',
      "/api/demo",
    );

    expect(payload).toEqual({
      schema: "demo.v1",
      safe_to_control: false,
    });
  });

  it("rejects non-object browser payloads", () => {
    // Artifact contract 只接受 object；数组或文本不能作为 endpoint schema/status proof。
    expect(() => extractJsonFromChromeDumpDom("<html><body><pre>[]</pre></body></html>", "/api/demo")).toThrow(
      "headless Chrome JSON payload is not an object",
    );
  });

  it("builds isolated headless Chrome dump-dom arguments", () => {
    // 独立 profile 和 --dump-dom 是区分真实 headless browser smoke 与 HTTP-only smoke 的核心锚点。
    const args = chromeDumpDomArgs("http://127.0.0.1:17002/api/health", "/tmp/rober-profile");

    expect(args).toContain("--headless=new");
    expect(args).toContain("--dump-dom");
    expect(args).toContain("--user-data-dir=/tmp/rober-profile");
    expect(args[args.length - 1]).toBe("http://127.0.0.1:17002/api/health");
  });

  it("uses the deterministic loopback defaults and explicit Chrome override", () => {
    // 默认端口与 Chrome override 写进 command summary，便于现场复验同一条命令。
    const args = parseArgs(["--artifact", "artifacts/out.json", "--chrome", "/tmp/Chrome"]);

    expect(args.artifact).toBe(path.resolve(process.cwd(), "artifacts/out.json"));
    expect(args.host).toBe("127.0.0.1");
    expect(args.port).toBe(17002);
    expect(args.chromePath).toBe("/tmp/Chrome");
  });
});
