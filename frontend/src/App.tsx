import React from "react";
import "./App.css";
import "./index.css";
import Analyzer from "./Analyzer";
import ThemeToggle from "./ThemeToggle";

export default function MarkovOrderMVP(): React.ReactElement {
  return (
    <div className="min-h-screen bg-background text-text relative overflow-x-hidden flex flex-row items-center justify-center">
      <div className="hidden sm:block w-1/5 max-w-[200px] items-start absolute top-0 left-5">
        <img src="/logo.png" alt="logo" className="w-full h-auto" />
      </div>

      <main className="w-full sm:w-3/5 max-w-4xl px-4 py-10 items-center">
        <header className="flex flex-col items-center mb-8">
          <img
            src="/favicon.png"
            alt=""
            className="w-35 block md:hidden mt-4"
          />
          <div className="w-full flex items-center justify-between">
            <h1 className="text-4xl font-bold text-text mt-4">
              Order of Markov
            </h1>
            <ThemeToggle />
          </div>
        </header>

        <div className="mx-auto">
          <Analyzer />
        </div>

        <footer className="mt-12 text-center text-text text-sm">
          <p>
            <a
              href="https://github.com/s4nj1th/order-of-markov"
              target="_blank"
              rel="noreferrer"
            >
              Source Code
            </a>
          </p>
        </footer>
      </main>

      <div className="hidden md:block w-1/5 max-w-[200px] items-end absolute bottom-10 right-5">
        <img src="/ccru.svg" alt="logo" className="w-full h-auto" />
      </div>
    </div>
  );
}
