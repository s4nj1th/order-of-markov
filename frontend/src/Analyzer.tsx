import React, { useState } from "react";
import { AlertCircle, Loader2 } from "lucide-react";

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
    const rawBase = (import.meta.env.VITE_API_BASE as string) || "";
    let apiBase: string;
    if (!rawBase) {
      apiBase = "/api";
    } else {
      const trimmed = rawBase.trim().replace(/\/+$/g, "");
      if (trimmed.startsWith("/")) {
        apiBase = trimmed;
      } else {
        apiBase = /\/api($|\/)/.test(trimmed) ? trimmed : `${trimmed}/api`;
      }
    }

    const url = `${apiBase.replace(/\/$/, "")}/analyze`;

    try {
      const body = { problem: problemText };
      console.debug(`[analyzeProblem] POST`, { url, body });

      const resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      console.debug(`[analyzeProblem] response status`, {
        status: resp.status,
        url,
      });

      if (!resp.ok) {
        const text = await resp.text().catch(() => "<no body>");
        console.error(`[analyzeProblem] API returned non-OK`, {
          status: resp.status,
          bodyText: text,
        });
        throw new Error(`API error ${resp.status}`);
      }

      const data = (await resp.json()) as AnalysisResult;
      console.debug(`[analyzeProblem] parsed response`, { data });

      if (
        typeof data.order === "number" &&
        typeof data.justification === "string" &&
        typeof data.confidence === "number"
      ) {
        return data;
      }
      console.error(`[analyzeProblem] invalid response shape`, { data });
      throw new Error("Invalid response shape from API");
    } catch (e) {
      console.error("API call failed, falling back to local mock:", e);
      await new Promise((resolve) => setTimeout(resolve, 600));

      let order = NaN;
      let justification = "Error analyzing problem.";
      let confidence = 0;

      // const lowerProblem = problemText.toLowerCase();
      // let order = 2;
      // let justification =
      //   "Based on the problem description, a 2nd-order model provides a good balance between capturing dependencies and computational efficiency. This order is suitable for most sequential prediction tasks.";
      // let confidence = 0.7;

      // if (
      //   lowerProblem.includes("weather") ||
      //   lowerProblem.includes("stock") ||
      //   lowerProblem.includes("time series")
      // ) {
      //   order = 2;
      //   justification =
      //     "Weather and financial data often show dependencies on the previous two states. Recent conditions strongly influence the next state, making a 2nd-order model appropriate for capturing these short-term patterns.";
      //   confidence = 0.85;
      // } else if (
      //   lowerProblem.includes("text") ||
      //   lowerProblem.includes("language") ||
      //   lowerProblem.includes("sentence")
      // ) {
      //   order = 3;
      //   justification =
      //     "Natural language generation benefits from higher-order context. A 3rd-order model captures grammatical patterns and word sequences effectively while remaining computationally feasible.";
      //   confidence = 0.82;
      // } else if (
      //   lowerProblem.includes("game") ||
      //   lowerProblem.includes("chess") ||
      //   lowerProblem.includes("strategy")
      // ) {
      //   order = 4;
      //   justification =
      //     "Strategic games require deeper history to make informed predictions. A 4th-order model captures complex patterns and strategic dependencies that span multiple moves.";
      //   confidence = 0.78;
      // } else if (
      //   lowerProblem.includes("simple") ||
      //   lowerProblem.includes("binary") ||
      //   lowerProblem.includes("coin")
      // ) {
      //   order = 1;
      //   justification =
      //     "Simple binary or memoryless processes are well-modeled with 1st-order Markov chains. The next state depends only on the current state, reducing complexity without sacrificing accuracy.";
      //   confidence = 0.92;
      // }

      const fallback = { order, justification, confidence };
      console.debug(`[analyzeProblem] returning fallback result`, { fallback });
      return fallback;
    }
  };

  const handleSubmit = async (): Promise<void> => {
    if (!problem.trim()) {
      setError("Please describe your problem");
      return;
    }
    console.debug(`[handleSubmit] submitting problem`, { problem });
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeProblem(problem);
      setResult(data);
    } catch (err) {
      setError("Failed to analyze problem. Please try again.");
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
    if (conf >= 0.8) return "text-green-600";
    if (conf >= 0.6) return "text-yellow-600";
    return "text-orange-600";
  };

  const getConfidenceLabel = (conf: number): string => {
    if (conf >= 0.8) return "High";
    if (conf >= 0.6) return "Moderate";
    return "Low";
  };

  return (
    <>
      <div className="bg-white rounded-xl border border-[#9994] p-6 mb-6">
        <label htmlFor="problem" className="block mb-2 font-semibold">
          Describe your problem
        </label>
        <textarea
          id="problem"
          value={problem}
          onChange={(e) => setProblem(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="E.g., I want to predict tomorrow's weather based on historical patterns..."
          className="w-full h-32 p-3 border border-slate-200 rounded-md resize-none"
          disabled={loading}
        />

        <button
          onClick={handleSubmit}
          disabled={loading || !problem.trim()}
          className={`mt-4 w-full inline-flex items-center justify-center gap-2 rounded-lg px-4 py-3 font-semibold group ${
            loading || !problem.trim()
              ? "bg-slate-300 text-slate-700 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700 cursor-pointer"
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
        <p className="mt-2 text-center text-sm text-slate-500">
          Press {isMac ? "⌘" : "Ctrl"} + Enter to submit
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex gap-3 items-start">
            <AlertCircle className="text-red-600 w-5 h-5" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="bg-white rounded-xl border border-[#9994] p-6">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-bold">Recommendation</h2>
          </div>

          <div className="bg-sky-50 border border-blue-600/20 rounded-md p-4 mb-4">
            <p className="text-3xl font-bold text-sky-900 text-center">
              <span className="underline">{result.order}</span>
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
            <h3 className="mb-2 font-semibold">Justification</h3>
            <p className="text-slate-600">{result.justification}</p>
          </div>

          <div className="flex items-center justify-between border-t border-slate-100 pt-3">
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
