// @vitest-environment node
import { runInNewContext } from "node:vm";
import { describe, expect, it, vi } from "vitest";

import {
  ACTIVATE_UPDATE,
  serviceWorkerScript,
} from "@/features/offline/service-worker";

const ORIGIN = "https://app.example";
type Handler = (event: Record<string, unknown>) => void;
type FakeRequest = { url: string; method: string; mode: string };

/** The script running in a sandbox, with caches and a network made of maps. */
function load(network: Record<string, string | null> = {}) {
  const stores = new Map<string, Map<string, Response>>();
  const key = (request: string | FakeRequest) =>
    new URL(typeof request === "string" ? request : request.url, ORIGIN).href;
  const open = async (name: string) => {
    const store = stores.get(name) ?? new Map<string, Response>();
    stores.set(name, store);
    return {
      match: async (request: string | FakeRequest) =>
        store.get(key(request))?.clone(),
      put: async (request: string | FakeRequest, response: Response) => {
        store.set(key(request), response);
      },
      addAll: async (urls: string[]) => {
        for (const url of urls)
          store.set(key(url), new Response(`kept ${url}`));
      },
    };
  };
  const fetch = vi.fn(async (request: string | FakeRequest) => {
    const body = network[key(request)];
    if (body === undefined || body === null) throw new TypeError("offline");
    return new Response(body);
  });
  const handlers = new Map<string, Handler>();
  const self = {
    location: { origin: ORIGIN },
    clients: { claim: vi.fn(async () => {}) },
    skipWaiting: vi.fn(),
    addEventListener: (type: string, handler: Handler) =>
      handlers.set(type, handler),
  };
  const caches = {
    open,
    keys: async () => [...stores.keys()],
    delete: async (name: string) => stores.delete(name),
  };
  runInNewContext(serviceWorkerScript("v2"), {
    self,
    caches,
    fetch,
    URL,
    Response,
    Set,
  });
  return { handlers, stores, fetch, self, open };
}

/** Sends one request through the fetch handler: undefined when it is left alone. */
async function request(
  sw: ReturnType<typeof load>,
  path: string,
  init: Partial<FakeRequest> = {},
) {
  let answer: Promise<Response> | undefined;
  sw.handlers.get("fetch")!({
    request: {
      url: new URL(path, ORIGIN).href,
      method: "GET",
      mode: "cors",
      ...init,
    },
    respondWith: (response: Promise<Response>) => (answer = response),
  });
  return answer && (await answer).text();
}

async function run(sw: ReturnType<typeof load>, type: string, data?: unknown) {
  let done: Promise<unknown> = Promise.resolve();
  sw.handlers.get(type)!({
    data,
    waitUntil: (work: Promise<unknown>) => (done = work),
  });
  await done;
}

describe("service worker", () => {
  it("never touches API calls, writes or other websites", async () => {
    const sw = load();

    expect(await request(sw, "/v1/entries")).toBeUndefined();
    expect(
      await request(sw, "/review", { method: "POST", mode: "navigate" }),
    ).toBeUndefined();
    expect(await request(sw, "https://elsewhere.example/x.js")).toBeUndefined();
  });

  it("serves build files from the device once they have been fetched", async () => {
    const sw = load({ [`${ORIGIN}/_next/static/app.js`]: "code" });

    expect(await request(sw, "/_next/static/app.js")).toBe("code");
    expect(await request(sw, "/_next/static/app.js")).toBe("code");
    expect(sw.fetch).toHaveBeenCalledTimes(1);
  });

  it("never keeps a signed-in page, and shows the offline page instead", async () => {
    const sw = load({
      [`${ORIGIN}/ledger`]: "my ledger",
      [`${ORIGIN}/offline`]: "offline page",
    });
    await run(sw, "install");

    expect(await request(sw, "/ledger", { mode: "navigate" })).toBe(
      "my ledger",
    );
    const kept = [...sw.stores.values()].flatMap((store) => [...store.keys()]);
    expect(kept).not.toContain(`${ORIGIN}/ledger`);
  });

  it("falls back to the offline page, or a kept public page, without a connection", async () => {
    const network: Record<string, string | null> = {
      [`${ORIGIN}/offline`]: '<script src="/_next/static/offline.js"></script>',
      [`${ORIGIN}/privacy`]: "privacy notice",
    };
    const sw = load(network);
    await run(sw, "install");
    await request(sw, "/privacy", { mode: "navigate" });
    network[`${ORIGIN}/privacy`] = null;

    expect(await request(sw, "/privacy", { mode: "navigate" })).toBe(
      "privacy notice",
    );
    expect(await request(sw, "/ledger", { mode: "navigate" })).toContain(
      "offline.js",
    );
  });

  it("keeps the offline page's own files when it installs", async () => {
    // Next.js also lists files inside escaped data, as \"/_next/static/data.js\".
    const page =
      '<link href="/_next/static/page.css"><script>"\\"/_next/static/data.js\\""</script>';
    const sw = load({ [`${ORIGIN}/offline`]: page });
    await run(sw, "install");

    const kept = [...(sw.stores.get("jalada-files")?.keys() ?? [])];
    expect(kept).toEqual(
      expect.arrayContaining([
        `${ORIGIN}/_next/static/page.css`,
        `${ORIGIN}/_next/static/data.js`,
        `${ORIGIN}/mark.webp`,
        `${ORIGIN}/logo.webp`,
      ]),
    );
    expect(kept.filter((url) => url.endsWith("/"))).toEqual([]);
  });

  it("drops the pages kept by older versions when it takes over", async () => {
    const sw = load();
    await sw.open("jalada-pages-v1");
    await sw.open("jalada-pages-v2");

    await run(sw, "activate");

    expect([...sw.stores.keys()]).toEqual(["jalada-pages-v2"]);
    expect(sw.self.clients.claim).toHaveBeenCalled();
  });

  it("waits for the person before a new version takes over", async () => {
    const sw = load();
    expect(sw.self.skipWaiting).not.toHaveBeenCalled();

    sw.handlers.get("message")!({ data: ACTIVATE_UPDATE });

    expect(sw.self.skipWaiting).toHaveBeenCalled();
  });
});
