import ReactMarkdown from "react-markdown";
import ProcessSteps from "./ProcessSteps";

export default function MessageList({ messages }) {
  return (
    <div className="p-6 space-y-4">
      {messages.map((msg, index) => {
        if (msg.role === "steps") {
          return <ProcessSteps key={index} steps={msg.steps} />;
        }

        return (
          <div
            key={index}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-xl px-4 py-3 rounded-2xl text-sm ${
                msg.role === "user"
                  ? "bg-[#2f2f2f] text-white"
                  : "text-gray-100"
              }`}
            >
              {msg.role === "ai" ? (
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => <h1 className="text-xl font-bold mb-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-bold mb-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-bold mb-1">{children}</h3>,
                    p: ({ children }) => <div className="mb-2 last:mb-0">{children}</div>,
                    ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
                    li: ({ children }) => <li className="text-sm">{children}</li>,
                    code: ({ inline, children }) => inline
                      ? <code className="bg-[#2a2a2a] px-1.5 py-0.5 rounded text-emerald-400 text-xs">{children}</code>
                      : <pre className="bg-[#2a2a2a] p-3 rounded-lg overflow-x-auto my-2"><code className="text-emerald-400 text-xs">{children}</code></pre>,
                    strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                    a: ({ href, children }) => <a href={href} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{children}</a>,
                    blockquote: ({ children }) => <blockquote className="border-l-2 border-gray-500 pl-3 italic text-gray-400 my-2">{children}</blockquote>,
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}