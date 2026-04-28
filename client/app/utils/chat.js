import { apiClient } from "@/lib/apiClient";

export async function streamChat(
  message,
  checkpointId,
  model,
  onChunk,
  onCheckpoint,
  onStep,
) {
  let url = `/chat_stream/${encodeURIComponent(message)}?model=${model}`;
  if (checkpointId) url += `&thread_id=${checkpointId}`;

  const response = await apiClient(url);

  if (!response.ok) {
    const err = new Error("Request failed");
    err.status = response.status;
    throw err;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    let done, value;
    try {
      ({ done, value } = await reader.read());
    } catch (e) {
      console.warn("[stream] Input stream error, stopping:", e.message);
      break;
    }
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split("\n").filter((line) => line.startsWith("data: "));

    for (const line of lines) {
      let json;
      try {
        json = JSON.parse(line.replace("data: ", ""));
      } catch (e) {
        console.warn("[stream] Failed to parse line:", line);
        continue;
      }

      if (json.type === "thread_id") {
        onCheckpoint(json.thread_id);
      } else if (json.type === "content") {
        onChunk(json.content.replace(/\\n/g, "\n"));
      } else if (json.type === "blocked") {
        onChunk(`I cant help with that. ${json.reason}`);
      } else if (json.type === "thinking") {
        onStep({ type: "thinking", content: "Thinking" });
      } else if (json.type === "thought") {
        onStep({ type: "thought", content: json.content });
      } else if (json.type === "action") {
        onStep({ type: "action", content: json.content, task: json.task });
      } else if (json.type === "observation") {
        onStep({ type: "observation", content: json.content });
      } else if (json.type === "plan") {
        onStep({
          type: "plan",
          reasoning: json.reasoning,
          subtasks: json.subtasks,
        });
      } else if (json.type === "delegation") {
        onStep({ type: "delegation", content: json.content, task: json.task });
      } else if (json.type === "tool_call") {
        onStep({ type: "tool_call", content: json.content });
      } else if (json.type === "reading") {
        onStep({ type: "reading", urls: json.urls });
      } else if (json.type === "agent_done") {
        onStep({ type: "agent_done", content: json.content });
      } else if (json.type === "writing") {
        onStep({ type: "writing", content: "Responding to user" });
      } else if (json.type === "end") {
        return;
      }
    }
  }
}
