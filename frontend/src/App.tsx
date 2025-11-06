import React from "react";
import "./App.css";
import "./index.css";
import Analyzer from "./Analyzer";

export default function MarkovOrderMVP(): React.ReactElement {
  return (
    <div className="min-h-screen bg-background text-text relative overflow-x-hidden">
      <img
        src="/logo.png"
        alt="logo"
        className="w-40 absolute translate-x-10 md:translate-y-0 -translate-y-40"
      />
      <img
        src="/ccru.gif"
        alt="logo"
        className="w-50 absolute right-0 bottom-40 -translate-x-10 filter dark:invert invert-0 hidden md:block"
      />
      <div className="max-w-4xl mx-auto px-4 pb-12 flex flex-col">
        <div className="min-h-screen">
          <div className="flex flex-col items-center mb-12">
            <h1 className="text-4xl font-bold text-slate-800 mt-10">
              Order of Markov
            </h1>
          </div>

          <Analyzer />
        </div>

        <div className="mt-12 text-center text-slate-500 text-sm border-t-1 border-slate-200 pt-4">
          <p>
            <a
              href="https://github.com/s4nj1th/order-of-markov"
              target="_blank"
            >
              Source Code
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
