import { test } from "node:test";
import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import {
  requestId,
  matchesJobFilter,
  isPlaybackIncomplete,
  statusText,
  chatbotUrls,
  attendanceLabels,
} from "../src/lib/format.ts";

test("LAN HTTP generates distinct UUIDv4 idempotency keys without randomUUID", () => {
  const original = Object.getOwnPropertyDescriptor(globalThis, "crypto");
  Object.defineProperty(globalThis, "crypto", {
    configurable: true,
    value: { getRandomValues: webcrypto.getRandomValues.bind(webcrypto) },
  });
  try {
    const ids = Array.from({ length: 100 }, () => requestId());
    assert.equal(new Set(ids).size, 100);
    for (const id of ids)
      assert.match(
        id,
        /^[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}$/,
      );
  } finally {
    Object.defineProperty(globalThis, "crypto", original);
  }
});

test("cancelling jobs remain active and prompt-ready results remain completed", () => {
  assert.equal(
    matchesJobFilter({ status: "cancelling", retryable: false }, "active"),
    true,
  );
  const prompt = {
    status: "completed",
    result_kind: "manual_ready",
    retryable: false,
  };
  assert.equal(matchesJobFilter(prompt, "completed"), true);
  assert.equal(matchesJobFilter(prompt, "retryable"), false);
  assert.equal(statusText(prompt), "프롬프트 준비");
  for (const status of ["failed", "cancelled", "interrupted"])
    assert.equal(
      matchesJobFilter({ status, retryable: true }, "retryable"),
      true,
    );
  assert.equal(isPlaybackIncomplete("completed"), false);
  assert.equal(isPlaybackIncomplete("interrupted"), true);
});

test("web provider IDs and attendance statuses retain their intended destinations and labels", () => {
  assert.equal(chatbotUrls["gemini-web"], "https://gemini.google.com/app");
  assert.equal(chatbotUrls["claude-web"], "https://claude.ai/");
  assert.equal(chatbotUrls["grok-web"], "https://grok.com/");
  assert.equal(attendanceLabels.attendance, "출석");
  assert.equal(attendanceLabels.none, "미출석");
});
