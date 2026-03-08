"use client";

import { type Lang } from "@/lib/i18n";

interface Props {
  lang: Lang;
  onLangChange: (lang: Lang) => void;
}

export default function ThemeLangToggle({ lang, onLangChange }: Props) {
  const toggleTheme = () => {
    const html = document.documentElement;
    const isDark = html.classList.contains("dark");
    if (isDark) {
      html.classList.remove("dark");
      localStorage.setItem("theme", "light");
    } else {
      html.classList.add("dark");
      localStorage.setItem("theme", "dark");
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={toggleTheme}
        className="rounded-lg border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700"
        title="Toggle theme"
      >
        ☀/🌙
      </button>
      <button
        onClick={() => onLangChange(lang === "en" ? "zh" : "en")}
        className="rounded-lg border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700"
      >
        {lang === "en" ? "中文" : "EN"}
      </button>
    </div>
  );
}
