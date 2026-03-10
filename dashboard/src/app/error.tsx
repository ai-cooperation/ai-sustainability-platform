"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="max-w-lg rounded-xl border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-900/20">
        <h2 className="text-lg font-bold text-red-700 dark:text-red-400">
          Something went wrong
        </h2>
        <pre className="mt-3 overflow-auto rounded bg-red-100 p-3 text-xs text-red-800 dark:bg-red-900/40 dark:text-red-300">
          {error.message}
        </pre>
        {error.stack && (
          <pre className="mt-2 max-h-40 overflow-auto rounded bg-gray-100 p-3 text-[10px] text-gray-600 dark:bg-gray-800 dark:text-gray-400">
            {error.stack}
          </pre>
        )}
        <button
          onClick={reset}
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
