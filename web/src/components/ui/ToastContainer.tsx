"use client";
import { useToastStore } from "@/store/toast";
import { X, CheckCircle, AlertCircle, Info } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "pointer-events-auto flex items-center gap-3 min-w-[300px] max-w-[400px] p-4 rounded-md shadow-lg border animate-in slide-in-from-right-full transition-all duration-300",
            toast.type === 'success' && "bg-white border-green-200 text-green-800 dark:bg-green-950 dark:border-green-900 dark:text-green-300",
            toast.type === 'error' && "bg-white border-red-200 text-red-800 dark:bg-red-950 dark:border-red-900 dark:text-red-300",
            toast.type === 'info' && "bg-white border-blue-200 text-blue-800 dark:bg-blue-950 dark:border-blue-900 dark:text-blue-300"
          )}
        >
          {toast.type === 'success' && <CheckCircle className="h-5 w-5 shrink-0 text-green-600 dark:text-green-400" />}
          {toast.type === 'error' && <AlertCircle className="h-5 w-5 shrink-0 text-red-600 dark:text-red-400" />}
          {toast.type === 'info' && <Info className="h-5 w-5 shrink-0 text-blue-600 dark:text-blue-400" />}
          <span className="text-sm font-medium flex-1">{toast.message}</span>
          <button onClick={() => removeToast(toast.id)} className="hover:opacity-70 shrink-0">
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
