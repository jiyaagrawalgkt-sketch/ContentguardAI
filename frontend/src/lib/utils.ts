import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number): string {
  return Number(score).toFixed(0);
}

export function getScoreBadge(score: number): {
  label: string;
  bgColor: string;
  textColor: string;
  borderColor: string;
} {
  if (score >= 90) {
    return {
      label: "Compliant",
      bgColor: "bg-emerald-50",
      textColor: "text-emerald-700",
      borderColor: "border-emerald-200",
    };
  }
  if (score >= 75) {
    return {
      label: "Minor Issues",
      bgColor: "bg-amber-50",
      textColor: "text-amber-700",
      borderColor: "border-amber-200",
    };
  }
  if (score >= 50) {
    return {
      label: "Needs Review",
      bgColor: "bg-orange-50",
      textColor: "text-orange-700",
      borderColor: "border-orange-200",
    };
  }
  return {
    label: "Critical Violations",
    bgColor: "bg-rose-50",
    textColor: "text-rose-700",
    borderColor: "border-rose-200",
  };
}

export function getSeverityStyle(severity: string) {
  switch (severity?.toLowerCase()) {
    case "critical":
      return {
        badge: "bg-rose-100 text-rose-800 border-rose-300",
        border: "border-l-rose-500",
        dot: "bg-rose-500",
      };
    case "high":
      return {
        badge: "bg-orange-100 text-orange-800 border-orange-300",
        border: "border-l-orange-500",
        dot: "bg-orange-500",
      };
    case "medium":
      return {
        badge: "bg-amber-100 text-amber-800 border-amber-300",
        border: "border-l-amber-500",
        dot: "bg-amber-500",
      };
    case "low":
    default:
      return {
        badge: "bg-blue-100 text-blue-800 border-blue-300",
        border: "border-l-blue-400",
        dot: "bg-blue-400",
      };
  }
}

export function getCategoryMeta(category: string = "brand_voice") {
  const norm = category?.toLowerCase();
  switch (norm) {
    case "confidentiality":
      return {
        label: "Confidentiality Risk",
        badge: "bg-purple-50 text-purple-700 border-purple-200",
        accent: "text-purple-600",
      };
    case "privacy":
      return {
        label: "Privacy & PII",
        badge: "bg-indigo-50 text-indigo-700 border-indigo-200",
        accent: "text-indigo-600",
      };
    case "misleading_claim":
      return {
        label: "Unsupported Claim",
        badge: "bg-rose-50 text-rose-700 border-rose-200",
        accent: "text-rose-600",
      };
    case "unnecessary_content":
      return {
        label: "Excessive / Redundant",
        badge: "bg-slate-100 text-slate-700 border-slate-300",
        accent: "text-slate-600",
      };
    case "security_technical":
      return {
        label: "Security & Credential",
        badge: "bg-red-100 text-red-800 border-red-300",
        accent: "text-red-600",
      };
    case "brand_voice":
    default:
      return {
        label: "Brand Voice & Tone",
        badge: "bg-amber-50 text-amber-800 border-amber-200",
        accent: "text-amber-600",
      };
  }
}

export function getActionMeta(action: string = "Replace") {
  const norm = action?.toLowerCase();
  switch (norm) {
    case "remove":
      return {
        label: "Remove",
        badge: "bg-rose-50 text-rose-700 border-rose-200",
      };
    case "shorten":
      return {
        label: "Shorten",
        badge: "bg-amber-50 text-amber-700 border-amber-200",
      };
    case "verify":
      return {
        label: "Verify Claim",
        badge: "bg-blue-50 text-blue-700 border-blue-200",
      };
    case "review":
      return {
        label: "Needs Review",
        badge: "bg-purple-50 text-purple-700 border-purple-200",
      };
    case "replace":
    default:
      return {
        label: "Replace",
        badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
      };
  }
}

export function maskSensitivePreview(text: string, category?: string): string {
  if (!text) return "";
  const cat = (category || "").toLowerCase();
  if (cat === "security_technical" || cat === "security") {
    if (text.startsWith("AKIA") && text.length >= 16) {
      return text.slice(0, 4) + "*".repeat(text.length - 4);
    }
    if (text.includes("://")) {
      return text.replace(/:\/\/[^:]+:[^@]+@/, "://user:****@");
    }
    if (text.length > 8) {
      return text.slice(0, 3) + "*".repeat(text.length - 6) + text.slice(-3);
    }
    return "*".repeat(text.length);
  }
  if (cat === "privacy") {
    if (text.includes("@")) {
      const parts = text.split("@");
      const u = parts[0];
      const masked = u.length > 2 ? u.slice(0, 2) + "****" : "****";
      return `${masked}@${parts[1]}`;
    }
    if (text.includes("-") && text.length === 11 && text.replace(/-/g, "").match(/^\d+$/)) {
      return `***-**-${text.slice(-4)}`;
    }
  }
  return text;
}
