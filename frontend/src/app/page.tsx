import { Navbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { ProblemSolution } from "@/components/landing/ProblemSolution";
import { WorkflowVisualizer } from "@/components/landing/WorkflowVisualizer";
import { FeatureHighlights } from "@/components/landing/FeatureHighlights";
import { LiveAuditDemo } from "@/components/landing/LiveAuditDemo";
import { Footer } from "@/components/landing/Footer";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col bg-lavender-50">
      <Navbar />
      <main className="flex-1">
        <Hero />
        <ProblemSolution />
        <WorkflowVisualizer />
        <FeatureHighlights />
        <LiveAuditDemo />
      </main>
      <Footer />
    </div>
  );
}
