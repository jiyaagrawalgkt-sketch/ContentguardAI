import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

export const metadata: Metadata = {
  title: "ContentGuard AI — Brand Governance & Content Compliance",
  description: "Review it before it ships. Enterprise-grade AI-powered brand voice, factual consistency, and compliance governance platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-lavender-50 text-midnight-900 min-h-screen selection:bg-brand-500 selection:text-white">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
