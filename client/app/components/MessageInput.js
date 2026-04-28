import ModelSelector from "./ModelSelector";

export default function MessageInput({ input, setInput, onSend, isLoading, selectedModel, setSelectedModel }) {
  return (
    <div className="w-full max-w-2xl mx-auto px-4">
      <div className="bg-[#2f2f2f] rounded-2xl px-6 py-6 min-h-[80px] flex flex-col gap-4">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !isLoading && onSend()}
          placeholder="How can I help you today?"
          disabled={isLoading}
          autoComplete="off"
          className="w-full bg-transparent outline-none text-white placeholder-gray-500 text-sm disabled:opacity-50"
        />
        <div className="flex justify-end">
          <ModelSelector selectedModel={selectedModel} setSelectedModel={setSelectedModel} />
        </div>
      </div>
    </div>
  );
}