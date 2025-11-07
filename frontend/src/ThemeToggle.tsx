import React, { useEffect, useState } from "react";

export default function ThemeToggle(): React.ReactElement {
  const [isDark, setIsDark] = useState<boolean>(() => {
    try {
      const stored = localStorage.getItem("theme-mode");
      if (stored === "dark") return true;
      if (stored === "light") return false;
      return (
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches
      );
    } catch (_) {
      return false;
    }
  });

  useEffect(() => {
    const el = document.documentElement;
    if (isDark) el.classList.add("dark");
    else el.classList.remove("dark");
    try {
      localStorage.setItem("theme-mode", isDark ? "dark" : "light");
    } catch (_) {}
  }, [isDark]);

  return (
    <button
      aria-label="Toggle theme"
      onClick={() => setIsDark((v) => !v)}
      className="w-8 h-8 rounded-full border border-[#8888] text-xs"
    >
      {isDark ? "🌙" : "☀️"}
    </button>
  );
}
