import { useState } from "react";

export default function AuthPanel({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("loading");
    setError("");

    try {
      const response = await fetch(`http://localhost:8000/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || "Authentication failed.");
      }

      onAuthenticated(data);
    } catch (requestError) {
      setError(requestError.message);
      setStatus("error");
    }
  }

  return (
    <section className="mx-auto w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl shadow-black/10 sm:p-6">
      <div className="mb-5">
        <h2 className="text-lg font-semibold">
          {mode === "login" ? "Sign in to DocuQuery" : "Create your account"}
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Your documents are scoped to your account.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block text-sm text-slate-300">
          Username
          <input
            required
            minLength={3}
            maxLength={64}
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
          />
        </label>

        <label className="block text-sm text-slate-300">
          Password
          <input
            required
            minLength={8}
            maxLength={128}
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
          />
        </label>

        <button
          type="submit"
          disabled={status === "loading"}
          className="w-full rounded-lg bg-blue-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
        >
          {status === "loading"
            ? "Please wait..."
            : mode === "login"
              ? "Sign in"
              : "Create account"}
        </button>
      </form>

      {error && (
        <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300" role="alert">
          {error}
        </p>
      )}

      <button
        type="button"
        onClick={() => {
          setMode(mode === "login" ? "register" : "login");
          setError("");
        }}
        className="mt-4 text-sm text-blue-300 hover:text-blue-200"
      >
        {mode === "login"
          ? "Need an account? Create one"
          : "Already have an account? Sign in"}
      </button>
    </section>
  );
}
