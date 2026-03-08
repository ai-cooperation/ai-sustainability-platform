"use client";

import { t, type Lang } from "@/lib/i18n";

interface ApiDetailModalProps {
  apiId: string;
  lang: Lang;
  onClose: () => void;
}

export default function ApiDetailModal({ apiId, lang, onClose }: ApiDetailModalProps) {
  const name = t(`api.${apiId}.name`, lang);
  const desc = t(`api.${apiId}.desc`, lang);
  const source = t(`api.${apiId}.source`, lang);
  const format = t(`api.${apiId}.format`, lang);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="mx-4 w-full max-w-lg rounded-xl border border-gray-200 bg-white p-6 shadow-2xl dark:border-gray-600 dark:bg-gray-800"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">{name}</h3>
          <button
            onClick={onClose}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <p className="mt-3 text-sm text-gray-600 dark:text-gray-300">{desc}</p>

        <div className="mt-4 space-y-3">
          <div>
            <span className="text-xs font-semibold uppercase text-gray-400">{t("apiDetail.source", lang)}</span>
            <p className="mt-0.5 text-sm text-gray-700 dark:text-gray-300">{source}</p>
          </div>
          <div>
            <span className="text-xs font-semibold uppercase text-gray-400">{t("apiDetail.format", lang)}</span>
            <p className="mt-0.5 text-sm text-gray-700 dark:text-gray-300">{format}</p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="mt-5 w-full rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          {t("apiDetail.close", lang)}
        </button>
      </div>
    </div>
  );
}
