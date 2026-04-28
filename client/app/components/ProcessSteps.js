function groupSteps(steps) {
  const grouped = [];
  let readingUrls = [];

  for (const step of steps) {
    if (step.type === "delegation") {
      const existing = grouped.find(
        (s) => s.type === "delegation" && s.content === step.content
      );
      if (existing) {
        existing.tasks = [...(existing.tasks || []), step.task];
      } else {
        grouped.push({ ...step, tasks: step.task ? [step.task] : [] });
      }
    } else if (step.type === "agent_done") {
      if (readingUrls.length > 0) {
        const existingReading = grouped.find((s) => s.type === "reading");
        if (existingReading) {
          existingReading.urls = [...new Set([...existingReading.urls, ...readingUrls])].slice(0, 6);
        } else {
          grouped.push({ type: "reading", urls: [...new Set(readingUrls)].slice(0, 6) });
        }
        readingUrls = [];
      }
      const alreadyAdded = grouped.find(
        (s) => s.type === "agent_done" && s.content === step.content
      );
      if (!alreadyAdded) grouped.push(step);
    } else if (step.type === "reading") {
      readingUrls = [...readingUrls, ...step.urls];
    } else {
      grouped.push(step);
    }
  }

  return grouped;
}

const AGENT_COLORS = {
  research_agent: "text-blue-400",
  math_agent:     "text-purple-400",
  code_agent:     "text-emerald-400",
};

const YELLOW_TYPES = ["thought", "action", "observation"];

export default function ProcessSteps({ steps }) {
  const grouped = groupSteps(steps);

  return (
    <div className="flex justify-start w-full">
      <div className="max-w-xl w-full pl-2 py-2">
        {grouped.map((step, index) => {
          const isYellow = YELLOW_TYPES.includes(step.type);

          return (
            <div key={index} className="flex items-start gap-3">
              <div className="flex flex-col items-center">
                <div className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${
                  step.type === "plan" ? "bg-blue-500" :
                  isYellow ? "bg-yellow-500" : "bg-emerald-500"
                }`} />
                {index < grouped.length - 1 && (
                  <div className={`w-px flex-1 mt-1 mb-1 min-h-[12px] ${
                    step.type === "plan" ? "bg-blue-800" :
                    isYellow ? "bg-yellow-800" : "bg-emerald-700"
                  }`} />
                )}
              </div>
              <div className="pb-2 flex-1">
                {step.type === "thinking" ? (
                  <p className="text-sm text-gray-300">{step.content}</p>

                ) : step.type === "thought" ? (
                  <div className="bg-[#1a1a1a] border border-[#2f2f2f] rounded-lg px-3 py-2 text-xs text-gray-400 italic">
                    <span className="text-yellow-500 not-italic font-medium">Thought: </span>
                    {step.content}
                  </div>

                ) : step.type === "action" ? (
                  <div className="bg-[#1a1a1a] border border-[#2f2f2f] rounded-lg px-3 py-2 text-xs text-gray-400 italic">
                    <span className="text-yellow-500 not-italic font-medium">Action: </span>
                    {step.task || step.content}
                  </div>

                ) : step.type === "observation" ? (
                  <div className="bg-[#1a1a1a] border border-[#2f2f2f] rounded-lg px-3 py-2 text-xs text-gray-400 italic">
                    <span className="text-yellow-500 not-italic font-medium">Observation: </span>
                    {step.content}
                  </div>

                ) : step.type === "plan" ? (
                  <div className="bg-[#1a1a1a] border border-blue-900 rounded-lg px-3 py-2">
                    <p className="text-xs font-medium text-blue-400 mb-1.5">Plan</p>
                    <p className="text-xs text-gray-500 italic mb-2">{step.reasoning}</p>
                    <ol className="space-y-1.5">
                      {step.subtasks.map((st) => (
                        <li key={st.order} className="flex items-start gap-2">
                          <span className="text-xs text-blue-500 font-medium shrink-0 mt-0.5">
                            {st.order}.
                          </span>
                          <span className="text-xs text-gray-300">{st.description}</span>
                          {st.suggested_agent && (
                            <span className={`text-xs shrink-0 ml-auto ${AGENT_COLORS[st.suggested_agent] ?? "text-gray-400"}`}>
                              {st.suggested_agent.replace("_agent", "")}
                            </span>
                          )}
                        </li>
                      ))}
                    </ol>
                  </div>

                ) : step.type === "tool_call" ? (
                  <div className="flex items-center gap-2 bg-[#2a2a2a] border border-[#3a3a3a] rounded-lg px-3 py-2 text-sm text-gray-300 w-fit">
                    <span className="text-gray-400">🔍</span>
                    <span>{step.content.replace("Searching: ", "")}</span>
                  </div>

                ) : step.type === "reading" ? (
                  <div>
                    <p className="text-sm text-gray-400 mb-1">Reading</p>
                    <div className="flex flex-wrap gap-2">
                      {step.urls.map((url, i) => {
                        const domain = new URL(url).hostname.replace("www.", "");
                        return (
                          <a
                            key={i}
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs bg-[#2a2a2a] border border-[#3a3a3a] rounded-lg px-3 py-1.5 text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
                          >
                            {domain}
                          </a>
                        );
                      })}
                    </div>
                  </div>

                ) : step.type === "delegation" ? (
                  <div>
                    <p className="text-sm text-gray-300">{step.content}</p>
                    {step.tasks && step.tasks.length > 0 && (
                      <ul className="mt-1 ml-3 space-y-0.5">
                        {step.tasks.map((task, i) => (
                          <li key={i} className="text-xs text-gray-500 italic before:content-['→'] before:mr-1">
                            {task}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                ) : (
                  <p className="text-sm text-gray-300">{step.content}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}