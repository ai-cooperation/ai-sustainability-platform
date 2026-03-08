"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/lib/context";
import { t } from "@/lib/i18n";
import ThemeLangToggle from "@/components/ThemeLangToggle";

const navItems = [
  { href: "/", key: "nav.overview", icon: "🌍" },
  { href: "/energy", key: "nav.energy", icon: "⚡" },
  { href: "/climate", key: "nav.climate", icon: "🌡" },
  { href: "/environment", key: "nav.environment", icon: "🌿" },
  { href: "/agriculture", key: "nav.agriculture", icon: "🌾" },
  { href: "/carbon", key: "nav.carbon", icon: "🏭" },
  { href: "/forecasts", key: "nav.forecasts", icon: "🤖" },
  { href: "/status", key: "nav.status", icon: "📡" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { lang, setLang } = useApp();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
      <div className="flex h-16 items-center border-b border-gray-200 px-6 dark:border-gray-700">
        <h1 className="text-lg font-bold text-emerald-600">
          {lang === "zh" ? "AI 永續平台" : "AI Sustainability"}
        </h1>
      </div>
      <nav className="mt-4 flex-1 space-y-1 px-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400"
                  : "text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-800"
              }`}
            >
              <span>{item.icon}</span>
              {t(item.key, lang)}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-gray-200 p-4 dark:border-gray-700">
        <ThemeLangToggle lang={lang} onLangChange={setLang} />
      </div>
    </aside>
  );
}
