"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Overview", icon: "🌍" },
  { href: "/energy", label: "Energy", icon: "⚡" },
  { href: "/climate", label: "Climate", icon: "🌡" },
  { href: "/environment", label: "Environment", icon: "🌿" },
  { href: "/agriculture", label: "Agriculture", icon: "🌾" },
  { href: "/carbon", label: "Carbon", icon: "🏭" },
  { href: "/forecasts", label: "Forecasts", icon: "🤖" },
  { href: "/status", label: "API Status", icon: "📡" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
      <div className="flex h-16 items-center border-b border-gray-200 px-6 dark:border-gray-700">
        <h1 className="text-lg font-bold text-emerald-600">AI Sustainability</h1>
      </div>
      <nav className="mt-4 space-y-1 px-3">
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
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
