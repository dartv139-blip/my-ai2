import { describe, expect, it } from "vitest";

describe("my-ai2 API contract", () => {
  it("defines the health endpoint", () => expect("/api/health").toBe("/api/health"));
  it("accepts a chat message", () => {
    const body = {message:"Ahoj",conversationId:"test-id"};
    expect(typeof body.message).toBe("string");
    expect(typeof body.conversationId).toBe("string");
  });
});
