
"use client";

import React, { useMemo } from "react";
import { 
  FileScan, 
  Network, 
  ShieldCheck, 
  CheckCircle2, 
  Loader2, 
  Circle,
  Play
} from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface ReviewProgressProps {
  currentStep: string;
  status: string; // "PROCESSING" | "COMPLETED" | "FAILED" | "SKIPPED"
}

// ==================================================================================
// CONFIGURATION NOTE:
// To add more steps to the progress bar:
// 1. Add a new entry to the STEPS array below.
// 2. Ensure the 'id' matches the 'step' field sent by the backend WebSocket message.
// 3. Import a suitable icon from 'lucide-react'.
// 4. The order in the array determines the display order.
// ==================================================================================
const STEPS = [
  { id: "REVIEW_START", label: "Initialization", icon: Play },
  { id: "OCR", label: "Smart OCR", icon: FileScan },
  { id: "KG_BUILD", label: "Knowledge Graph", icon: Network },
  { id: "REVIEW_ALL", label: "Risk Analysis", icon: ShieldCheck },
  // Example: { id: "NEW_STEP", label: "New Step Name", icon: NewIcon },
];

export default function ReviewProgress({ currentStep, status }: ReviewProgressProps) {
  // Determine the active index
  const activeIndex = useMemo(() => {
    if (!currentStep) return -1;
    const index = STEPS.findIndex(s => s.id === currentStep);
    // If step not found but we have started, maybe default to 0?
    // If REVIEW_ALL is COMPLETED, we are at the end
    if (currentStep === "REVIEW_ALL" && status === "COMPLETED") return STEPS.length;
    return index;
  }, [currentStep, status]);

  const isComplete = currentStep === "REVIEW_ALL" && status === "COMPLETED";

  return (
    <div className="w-full py-4 px-8 bg-background/50 backdrop-blur-sm border rounded-lg shadow-sm">
      <div className="relative flex items-start justify-between">
        {/* Progress Line Background - Centered on icons */}
        <div className="absolute left-0 top-5 w-full h-1 bg-muted rounded-full -z-10" />
        
        {/* Animated Progress Line */}
        <div 
          className="absolute left-0 top-5 h-1 bg-primary rounded-full -z-10 transition-all duration-500 ease-out"
          style={{ 
            width: `${Math.min(100, Math.max(0, (activeIndex / (STEPS.length - 1)) * 100))}%` 
          }}
        />

        {STEPS.map((step, index) => {
          const isActive = index === activeIndex;
          const isPast = index < activeIndex || isComplete;
          const isProcessing = isActive && status === "PROCESSING";
          const isFailed = isActive && status === "FAILED";

          return (
            <div key={step.id} className="flex flex-col items-center gap-2 group relative z-10 w-24">
              {/* Icon Circle */}
              <div 
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 bg-background",
                  isPast ? "border-primary bg-primary text-primary-foreground scale-100" :
                  isActive ? "border-primary text-primary ring-4 ring-primary/20 scale-110" :
                  "border-muted text-muted-foreground scale-90"
                )}
              >
                {isPast ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : isProcessing ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <step.icon className="w-4 h-4" />
                )}
              </div>

              {/* Label */}
              <div className="flex flex-col items-center gap-1 text-center">
                <span className={cn(
                    "text-xs font-medium transition-colors duration-300",
                    isActive || isPast ? "text-primary" : "text-muted-foreground"
                )}>
                    {step.label}
                </span>

                {/* Status Text (visible only for active step) */}
                {isActive && (
                    <span className="text-[10px] text-muted-foreground animate-pulse whitespace-nowrap">
                    {status === "PROCESSING" ? "Processing..." : status}
                    </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
