"use client";

import { useState } from "react";

const models = [
  { id: "qwen-7b-instruct", label: "Qwen-7B-Instruct", description: "Free but slow" },
  { id: "gpt-4o-mini", label: "GPT-4o-Mini", description: "Fast but paid" },
];

export default function ModelSelector({ selectedModel, setSelectedModel }) {
  const [open, setOpen] = useState(false);
  const current = models.find((m) => m.id === selectedModel) ?? models[0];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-[#2f2f2f]"
      >
        {current.label}
        <span className="text-xs">▾</span>
      </button>

      {open && (
        <div className="absolute bottom-10 left-0 bg-[#2f2f2f] rounded-xl shadow-lg w-64 overflow-hidden z-10">
          {models.map((model) => (
            <button
              key={model.id}
              onClick={() => { setSelectedModel(model.id); setOpen(false); }}
              className={`w-full text-left px-4 py-3 hover:bg-[#3a3a3a] transition-colors flex justify-between items-center ${
                selectedModel === model.id ? "text-white" : "text-gray-400"
              }`}
            >
              <span className="text-sm font-medium">{model.label}</span>
              <span className="text-xs text-gray-500">{model.description}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}