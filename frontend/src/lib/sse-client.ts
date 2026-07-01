export type SseMessageHandler = (eventName: string, data: string) => void;

/** Connect to an SSE endpoint via fetch (EventSource cannot set custom headers). */
export async function connectSse(
  url: string,
  onMessage: SseMessageHandler,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(url, {
    headers: { Accept: "text/event-stream" },
    signal,
  });
  if (!response.ok) {
    throw new Error(`SSE ${response.status}: ${response.statusText}`);
  }
  if (!response.body) {
    throw new Error("SSE response has no body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (!signal.aborted) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const rawBlock = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      let eventName = "message";
      const dataLines: string[] = [];

      for (const line of rawBlock.split("\n")) {
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trimStart());
        }
      }

      if (dataLines.length > 0) {
        onMessage(eventName, dataLines.join("\n"));
      }

      boundary = buffer.indexOf("\n\n");
    }
  }
}
