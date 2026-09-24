export interface Env {
  AI: Ai;
  AI_MODEL?: string;
  SYSTEM_PROMPT?: string;
}

interface ChatRequest {
  message: string;
  conversationId?: string;
}

const DEFAULT_MODEL = "@cf/meta/llama-3.1-8b-instruct";
const DEFAULT_SYSTEM = "Jsi moje vlastní AI. Odpovídej česky, věcně a užitečně.";

function json(data: unknown, status = 200, origin = "*"): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": origin,
      "access-control-allow-methods": "GET,POST,OPTIONS",
      "access-control-allow-headers": "Content-Type, Authorization, X-Request-Id"
    }
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const origin = request.headers.get("Origin") || "*";
    if (request.method === "OPTIONS") return json({}, 204, origin);

    const url = new URL(request.url);
    if (url.pathname === "/api/health" && request.method === "GET") {
      return json({ok:true,service:"my-ai2",model:env.AI_MODEL || DEFAULT_MODEL},200,origin);
    }

    if (url.pathname === "/api/chat" && request.method === "POST") {
      const requestId = crypto.randomUUID();
      let body: ChatRequest;
      try { body = await request.json() as ChatRequest; }
      catch { return json({error:"Invalid JSON",requestId},400,origin); }

      if (!body.message || typeof body.message !== "string")
        return json({error:"message is required",requestId},400,origin);
      if (body.message.length > 12000)
        return json({error:"message is too long",requestId},413,origin);

      const model = env.AI_MODEL || DEFAULT_MODEL;
      const conversationId = body.conversationId?.trim() || crypto.randomUUID();

      try {
        const result = await env.AI.run(model,{
          messages:[
            {role:"system",content:env.SYSTEM_PROMPT || DEFAULT_SYSTEM},
            {role:"user",content:body.message}
          ]
        });
        const responseText = typeof result === "string"
          ? result
          : (result as {response?:string}).response;

        return json({message:responseText || "AI nevrátila textovou odpověď.",conversationId,model,requestId},200,origin);
      } catch (error) {
        return json({error:"AI request failed",requestId,detail:error instanceof Error ? error.message : "Unknown error"},502,origin);
      }
    }

    return json({error:"Not found"},404,origin);
  }
};
