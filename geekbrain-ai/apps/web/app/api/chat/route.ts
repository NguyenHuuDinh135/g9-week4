const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8080";
const MAX_MESSAGES = 50;
const MAX_CONTENT_LENGTH = 10_000;

export async function POST(request: Request) {
  const contentLength = request.headers.get("content-length");
  if (contentLength && parseInt(contentLength) > 1_048_576) {
    return new Response(
      JSON.stringify({ error: "Request body too large" }),
      { status: 413, headers: { "Content-Type": "application/json" } }
    );
  }

  const body = await request.json();

  if (!body.messages || !Array.isArray(body.messages) || body.messages.length === 0) {
    return new Response(
      JSON.stringify({ error: "messages array required" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  if (body.messages.length > MAX_MESSAGES) {
    return new Response(
      JSON.stringify({ error: "Too many messages" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  for (const msg of body.messages) {
    if (typeof msg.content === "string" && msg.content.length > MAX_CONTENT_LENGTH) {
      return new Response(
        JSON.stringify({ error: "Message content too long" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }
  }

  const response = await fetch(`${BACKEND_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    return new Response(
      JSON.stringify({ error: "Backend request failed" }),
      { status: response.status, headers: { "Content-Type": "application/json" } }
    );
  }

  return new Response(response.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
