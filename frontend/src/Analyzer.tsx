import React, { useState } from "react";
import { AlertCircle, Loader2 } from "lucide-react";
import "./index.css";
import "./App.css";

export interface AnalysisResult {
  order: number;
  justification: string;
  confidence: number;
}

export default function Analyzer(): React.ReactElement {
  const [problem, setProblem] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analyzeProblem = async (
    problemText: string
  ): Promise<AnalysisResult> => {
    const apiBase =
      (import.meta.env.VITE_API_BASE as string) || "http://localhost:8000";
    const url = `${apiBase}/api/analyze`;

    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ problem: problemText }),
    });

    if (!resp.ok) {
      const errorData = await resp
        .json()
        .catch(() => ({ detail: "Unknown error" }));
      throw new Error(errorData.detail || `API error ${resp.status}`);
    }

    const data = (await resp.json()) as AnalysisResult;

    if (
      typeof data.order !== "number" ||
      typeof data.justification !== "string" ||
      typeof data.confidence !== "number"
    ) {
      throw new Error("Invalid response format from API");
    }

    return data;
  };

  const handleSubmit = async (): Promise<void> => {
    if (!problem.trim()) {
      setError("Please describe your problem");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeProblem(problem);
      setResult(data);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to analyze problem. Please try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const isMac =
    typeof navigator !== "undefined" &&
    /Mac|iPhone|iPad|iPod/.test(navigator.platform);

  const handleKeyPress = (
    e: React.KeyboardEvent<HTMLTextAreaElement>
  ): void => {
    if (e.key !== "Enter") return;
    const wantsMeta = isMac ? e.metaKey : false;
    const wantsCtrl = isMac ? false : e.ctrlKey;
    if (wantsMeta || wantsCtrl) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const getConfidenceColor = (conf: number): string => {
    if (conf >= 0.8) return "conf-high";
    if (conf >= 0.6) return "conf-mod";
    return "conf-low";
  };

  const getConfidenceLabel = (conf: number): string => {
    if (conf >= 0.8) return "High";
    if (conf >= 0.6) return "Moderate";
    return "Low";
  };

  return (
    <>
      <div className="bg-surface p-6 mb-6 text-muted">
        <label htmlFor="problem" className="block mb-2 font-semibold">
          Describe your problem
        </label>
        <textarea
          id="problem"
          value={problem}
          onChange={(e) => setProblem(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="E.g., I want to predict tomorrow's weather based on historical patterns..."
          className="w-full h-32 p-3 input rounded-md resize-none text"
          disabled={loading}
        />

        <button
          onClick={handleSubmit}
          disabled={loading || !problem.trim()}
          className={`mt-4 w-full btn group ${
            loading || !problem.trim() ? "btn-disabled" : "btn-primary"
          }`}
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <span>Analyze</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                className="w-5 h-5"
                stroke="currentColor"
                fill="none"
                strokeWidth={2}
              >
                <line
                  x1="5"
                  y1="12"
                  x2="19"
                  y2="12"
                  className="translate-x-3 group-hover:translate-x-0 scale-x-0 group-hover:scale-x-100 transition-transform duration-300 ease-in-out"
                />
                <polyline
                  points="12 5 19 12 12 19"
                  className="-translate-x-1 group-hover:translate-x-0 transition-transform duration-300 ease-in-out"
                />
              </svg>
            </div>
          )}
        </button>
        <p className="mt-2 text-center text-sm muted">
          Press {isMac ? "⌘" : "Ctrl"} + Enter to submit
        </p>
      </div>

      {error && (
        <div className="alert alert-error mb-6">
          <div className="flex gap-3 items-start">
            <AlertCircle className="w-5 h-5" />
            <p>{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-bold">Recommendation</h2>
          </div>

          <div className="result-hero mb-4">
            <p className="hero-order">
              <span className="">{result.order}</span>
              <sup>
                {result.order === 1
                  ? "st"
                  : result.order === 2
                  ? "nd"
                  : result.order === 3
                  ? "rd"
                  : "th"}
              </sup>
              -order Markov Model
            </p>
          </div>

          <div className="mb-4">
            {/* <h3 className="mb-2 font-semibold">Justification</h3> */}
            <p className="muted">{result.justification}</p>
          </div>

          <div
            className="flex items-center justify-between border-t"
            style={{
              borderColor: "var(--color-border)",
              paddingTop: "0.75rem",
            }}
          >
            <span className="font-semibold">Confidence Score</span>
            <div className="flex items-center gap-3">
              <span
                className={`text-3xl font-bold ${getConfidenceColor(
                  result.confidence
                )}`}
              >
                {(result.confidence * 100).toFixed(0)}%
              </span>
              <span
                className={`${getConfidenceColor(result.confidence)} text-sm`}
              >
                {`(${getConfidenceLabel(result.confidence)})`}
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
