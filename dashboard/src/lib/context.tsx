"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { type Lang } from "@/lib/i18n";

interface AppContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
}

const AppContext = createContext<AppContextValue>({
  lang: "en",
  setLang: () => {},
});

export function AppProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    // Restore language preference
    const savedLang = localStorage.getItem("lang") as Lang | null;
    if (savedLang === "zh" || savedLang === "en") {
      setLangState(savedLang);
    }

    // Restore theme preference
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else if (savedTheme === "light") {
      document.documentElement.classList.remove("dark");
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      document.documentElement.classList.add("dark");
    }
  }, []);

  const setLang = (newLang: Lang) => {
    setLangState(newLang);
    localStorage.setItem("lang", newLang);
  };

  return (
    <AppContext.Provider value={{ lang, setLang }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
