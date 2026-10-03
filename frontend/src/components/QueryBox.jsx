import { useState } from "react";

export default function QueryBox() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const cleanedQuestion = question.trim();

    if (!cleanedQuestion) {
      setError("Please enter a question.");
      return;
    }

    setStatus("loading");
    setError("");

    try {
      const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: cleanedQuestion }),
      });

      if (!response.ok) {
        throw new Error("Query failed");
      }

      const data = await response.json();
      setMessages((previousMessages) => [
        ...previousMessages,
        {
          question: cleanedQuestion,
          answer: data.answer,
        },
      ]);
      setQuestion("");
      setStatus("success");
    } catch {
      setError("Could not get an answer.");
      setStatus("error");
    }
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl shadow-black/10 sm:p-6">
      <div className="mb-5">
        <h2 className="text-lg font-semibold">Ask about your document</h2>
        <p className="mt-1 text-sm text-slate-400">
          Ask a question and DocuQuery will search your uploaded PDFs for context.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <textarea
          aria-label="Question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="What experience does this person have?"
          disabled={status === "loading"}
          rows={3}
          className="block w-full resize-y rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 disabled:cursor-not-allowed disabled:opacity-60"
        />

        <button
          type="submit"
          disabled={status === "loading"}
          className="rounded-lg bg-blue-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
        >
          {status === "loading" ? "Searching..." : "Ask question"}
        </button>
      </form>

      <div className="mt-6 space-y-4" aria-live="polite">
        {messages.map((message, index) => (
          <div key={index} className="space-y-3">
            <div className="ml-auto max-w-[90%] rounded-2xl rounded-br-md bg-blue-500/15 px-4 py-3 text-sm text-blue-100">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-blue-300">You</p>
              <p>{message.question}</p>
            </div>
            <div className="max-w-[90%] rounded-2xl rounded-bl-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm leading-6 text-slate-200">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">DocuQuery</p>
              <p className="whitespace-pre-wrap">{message.answer}</p>
            </div>
          </div>
        ))}
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
