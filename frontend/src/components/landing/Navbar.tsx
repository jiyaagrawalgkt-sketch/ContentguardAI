"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, ArrowRight, Sparkles } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-midnight-900/10 bg-white/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-midnight-900 flex items-center justify-center shadow-md shadow-midnight-900/10">
            <ShieldCheck className="w-6 h-6 text-brand-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-midnight-900">
                ContentGuard<span className="text-brand-500">.ai</span>
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200">
                Enterprise
              </span>
            </div>
            <p className="text-[11px] text-midnight-600 hidden sm:block">
              Review it before it ships.
            </p>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-midnight-700">
          <a href="#how-it-works" className="hover:text-brand-600 transition-colors">
            How It Works
          </a>
          <a href="#features" className="hover:text-brand-600 transition-colors">
            Features
          </a>
          <a href="#governance" className="hover:text-brand-600 transition-colors">
            Brand Hub
          </a>
          <a href="#compliance" className="hover:text-brand-600 transition-colors">
            Compliance Score
          </a>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-midnight-800 hover:text-midnight-950 hover:bg-lavender-100 rounded-lg transition-all"
          >
            Demo Access
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-midnight-900 hover:bg-midnight-800 rounded-lg shadow-sm hover:shadow transition-all"
          >
            <span>Launch App</span>
            <ArrowRight className="w-4 h-4 text-brand-400" />
          </Link>
        </div>
      </div>
    </header>
  );
}
