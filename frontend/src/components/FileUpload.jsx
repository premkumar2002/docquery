import { useState } from "react";

async function uploadFile(file, token) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
    });

    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Upload failed");
    }

    return response.json();
}

export default function FileUpload({ onUploadSuccess, token }) {
    const [status, setStatus] = useState("idle");
    const [file, setFile] = useState(null);
    const [chunkCount, setChunkCount] = useState(null);
    const [error, setError] = useState("");

    const handleFileChange = (event) => {
        const selectedFile = event.target.files[0];
        setChunkCount(null);
        setError("");

        if (!selectedFile) {
            setFile(null);
            setStatus("idle");
            return;
        }

        if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
            setFile(null);
            setStatus("error");
            setError("Please choose a PDF file.");
            return;
        }

        setFile(selectedFile);
        setStatus("idle");
    };

    const handleUpload = async () => {
        if (!file) {
            setError("Please select a PDF file first.");
            setStatus("error");
            return;
        }

        setStatus("uploading");
        setError("");

        try {
            const result = await uploadFile(file, token);
            setChunkCount(result.chunks_created);
            onUploadSuccess(result.document_id);
            setStatus("success");
        } catch (error) {
            console.error(error);
            setStatus("error");
            setError(error.message || "Upload failed. Please try again.");
        }
    };

    return (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl shadow-black/10 sm:p-6">
            <div className="mb-5">
                <h2 className="text-lg font-semibold">Upload a document</h2>
                <p className="mt-1 text-sm text-slate-400">
                    Choose a PDF to add it to your searchable document collection.
                </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <label className="block min-w-0 flex-1">
                    <span className="sr-only">Choose a PDF file</span>
                    <input
                        type="file"
                        accept=".pdf,application/pdf"
                        onChange={handleFileChange}
                        disabled={status === "uploading"}
                        className="block w-full cursor-pointer rounded-lg border border-slate-700 bg-slate-950 text-sm text-slate-400 file:mr-4 file:cursor-pointer file:border-0 file:bg-slate-800 file:px-4 file:py-2.5 file:text-sm file:font-medium file:text-slate-200 hover:file:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                    />
                </label>
                <button
                    type="button"
                    onClick={handleUpload}
                    disabled={status === "uploading" || !file}
                    className="rounded-lg bg-blue-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                >
                    {status === "uploading" ? "Uploading..." : "Upload PDF"}
                </button>
            </div>

            {file && status !== "success" && (
                <p className="mt-3 text-sm text-slate-400">
                    Selected: <span className="text-slate-200">{file.name}</span>
                </p>
            )}

            <div className="mt-4" aria-live="polite">
                {status === "success" && chunkCount !== null && (
                    <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
                        Upload successful. Created {chunkCount} searchable chunks.
                    </p>
                )}
                {status === "error" && error && (
                    <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300" role="alert">
                        {error}
                    </p>
                )}
            </div>
        </section>
    );
}
