import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

const source = readFileSync(new URL("../src/lib/api.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
});

function client(fetch) {
  const scope = {
    exports: {},
    process: { env: { NEXT_PUBLIC_API_BASE: "http://catalog.test/api" } },
    URLSearchParams,
    fetch,
    // These tests cover the catalog boundary, independent of cache lifetime.
    require: () => ({ withCache: (_key, run) => run() }),
  };
  vm.runInNewContext(outputText, scope);
  return scope.exports;
}

test("loads all 25 videos across backend pages and keeps filters", async () => {
  const requestedPages = [];
  const api = client(async (url) => {
    const params = new URL(url).searchParams;
    assert.equal(params.get("category"), "creative");
    assert.equal(params.get("creator_id"), "vox");
    const page = Number(params.get("page"));
    requestedPages.push(page);
    const start = (page - 1) * 20;
    return {
      ok: true,
      json: async () => ({
        data: Array.from({ length: page === 1 ? 20 : 5 }, (_, i) => ({ id: String(start + i) })),
        total_pages: 2,
      }),
    };
  });
  const videos = await api.getVideos({ category: "creative", creatorId: "vox" });
  assert.equal(videos.length, 25);
  assert.equal(new Set(videos.map((video) => video.id)).size, 25);
  assert.deepEqual(requestedPages, [1, 2]);
});

test("accepts the unpaginated Next.js fallback", async () => {
  let requests = 0;
  const api = client(async () => {
    requests++;
    return { ok: true, json: async () => ({ data: [{ id: "one" }], total: 1 }) };
  });
  assert.equal((await api.getVideos()).length, 1);
  assert.equal(requests, 1);
});

test("does not return a partial catalog when a later page fails", async () => {
  const api = client(async (url) => new URL(url).searchParams.get("page") === "1"
    ? { ok: true, json: async () => ({ data: [{ id: "one" }], total_pages: 2 }) }
    : { ok: false });
  assert.equal((await api.getVideos()).length, 0);
});
