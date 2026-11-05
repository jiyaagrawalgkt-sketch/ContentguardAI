"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, Heart } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-midnight-950 text-midnight-400 border-t border-midnight-900 py-12 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 pb-8 border-b border-midnight-900">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-midnight-900 border border-midnight-800 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-brand-400" />
            </div>
            <span className="font-bold text-white text-base">
              ContentGuard<span className="text-brand-500">.ai</span>
            </span>
          </div>

          <p className="text-xs text-midnight-400 text-center">
            AI-Powered Brand Governance & Content Compliance Platform. Built for Enterprise Teams.
          </p>

          <div className="flex items-center gap-6 text-xs">
            <Link href="/login" className="hover:text-white transition-colors">
              Demo Access
            </Link>
            <a href="#how-it-works" className="hover:text-white transition-colors">
              Workflow
            </a>
            <a href="#features" className="hover:text-white transition-colors">
              Engine Modules
            </a>
          </div>
        </div>

        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-midnight-500">
          <p>© 2026 ContentGuard AI. All rights reserved.</p>
          <p className="flex items-center gap-1">
            <span>Tagline:</span>
            <strong className="text-midnight-300">Review it before it ships.</strong>
          </p>
        </div>
      </div>
    </footer>
  );
}
