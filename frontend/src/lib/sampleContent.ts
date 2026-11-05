export interface SampleContent {
  id: string;
  name: string;
  category: string;
  targetPlatform: string;
  campaignName: string;
  title: string;
  content: string;
  riskTier: "High Risk" | "Moderate Risk" | "Compliant (Low Risk)";
  riskBadgeColor: string;
  description: string;
  highlights: string[];
}

/**
 * Professional Real-World Simulation Presets for Brand Governance Testing.
 * Note: These are fictional product examples crafted to simulate authentic
 * marketing drafts with controlled brand policy violations.
 */
export const SAMPLE_CONTENT_LIBRARY: SampleContent[] = [
  {
    id: "sample-saas-linkedin",
    name: "SaaS Analytics LinkedIn Campaign",
    category: "social_media",
    targetPlatform: "LinkedIn",
    campaignName: "Q4 Enterprise Growth Initiative",
    title: "OmniMetrics Analytics Platform Launch",
    riskTier: "Moderate Risk",
    riskBadgeColor: "bg-amber-50 text-amber-700 border-amber-200",
    description: "B2B SaaS LinkedIn announcement promoting a business analytics platform. Features professional tone with intentional buzzword drift (game-changer) and an unverified multiplier claim.",
    highlights: ["Buzzword Drift (Game-Changer)", "Unsubstantiated Multiplier (Double Your Leads)", "SOC-2 Claims"],
    content: `Data without actionable clarity is just noise.

Today, we're officially launching OmniMetrics 4.0—our enterprise governance analytics platform designed to give revenue leaders real-time visibility across every customer interaction.

By replacing fragmented spreadsheets with unified telemetry, forward-thinking organizations can double your leads within 30 days while eliminating compliance guesswork. Having continuous automated auditing is a transformative game-changer for enterprise velocity.

Built on hardened cloud infrastructure, OmniMetrics delivers verified compliance assurance without sacrificing operational speed.

How is your operations team auditing digital messaging integrity this quarter?

#EnterpriseSaaS #BusinessAnalytics #BrandGovernance #DataOperations`,
  },
  {
    id: "sample-instagram-ad",
    name: "Consumer Tech Instagram Advertisement",
    category: "advertisement",
    targetPlatform: "Instagram / Meta Ads",
    campaignName: "PulseBuds Pro Direct Launch",
    title: "PulseBuds Pro Wireless Earbuds Promo",
    riskTier: "High Risk",
    riskBadgeColor: "bg-rose-50 text-rose-700 border-rose-200",
    description: "Consumer audio advertisement utilizing high-pressure marketing language, exaggerated 100% risk-free guarantees, and unauthorized superiority superlatives.",
    highlights: ["Prohibited 100% Risk-Free Guarantee", "Unsupported Superiority (#1 in the World)", "High-Pressure Urgency"],
    content: `Meet PulseBuds Pro: Audio Perfection Reimagined. 🎧

No other competitor can match our custom acoustic architecture. Engineered with active noise cancellation and ergonomic silicon styling, PulseBuds Pro delivers #1 in the world sound fidelity.

Try it with zero hesitation: we provide a 100% risk-free guarantee for 60 full days. If you aren't completely mesmerized, return them for an unconditional refund—no questions asked!

Act now before it's too late: introductory pricing expires at midnight. Click here immediately to claim your pair!`,
  },
  {
    id: "sample-b2b-email",
    name: "B2B Software Email Marketing Campaign",
    category: "marketing_email",
    targetPlatform: "Email Newsletter / Outreach",
    campaignName: "Q4 Cloud Modernization Outreach",
    title: "Modernize Your Enterprise File Ingestion Pipeline",
    riskTier: "High Risk",
    riskBadgeColor: "bg-rose-50 text-rose-700 border-rose-200",
    description: "B2B promotional campaign with misleading throughput specifications (claiming 50,000 docs/min vs approved 12,000 SLA) and unqualified commercial outcome guarantees.",
    highlights: ["Throughput Inconsistency (50,000 docs/min)", "Unqualified Growth Guarantee", "Jargon Buzzword (Proprietary AI Engine)"],
    content: `Subject: Accelerate Your Enterprise Governance Velocity with ContentGuard!

Hey there,

Is your compliance team overwhelmed by manual copy checks across distributed digital channels?

ContentGuard AI is the industry-first platform engineered to automate multi-channel brand compliance. Powered by our proprietary AI engine, our infrastructure processes 50,000 documents per minute with 100% flawless uptime.

Unlike legacy manual review workflows, our solution provides guaranteed growth by preventing costly regulatory and brand violations before publication.

Don't wait—contact our enterprise solutions team today to schedule an executive consultation.`,
  },
  {
    id: "sample-landing-page",
    name: "Cloud Security Website Landing Page",
    category: "landing_page",
    targetPlatform: "Corporate Website (acme.com)",
    campaignName: "CloudGuard Security Platform Launch",
    title: "Zero-Trust Cloud Governance Architecture",
    riskTier: "Moderate Risk",
    riskBadgeColor: "bg-amber-50 text-amber-700 border-amber-200",
    description: "Enterprise landing page hero and feature copy with SLA discrepancies (claiming zero downtime / 99.999% vs official 99.9%) and absolute security claims.",
    highlights: ["Uptime SLA Mismatch (Zero Downtime / 99.999%)", "Absolute Security Claim (Unbreakable Security)", "Tone Nuance"],
    content: `Header: Autonomous Cloud Security & Content Integrity
Subheader: Protect your enterprise brand voice across thousands of multi-channel publications simultaneously.

Continuous Security Without Operational Friction
Modern enterprises cannot afford compliance drift or data compromise. CloudGuard delivers zero downtime infrastructure backed by unbreakable security algorithms that continuously audit outward communications against organizational policy.

Audited Enterprise Reliability
While manual review queues delay releases, our distributed architecture processes up to 12,000 evaluations per minute under SOC-2 Type II audited standards.

Join hundreds of distributed enterprises shipping verified content every single day.`,
  },
  {
    id: "sample-financial-services",
    name: "Financial Services Educational Post",
    category: "blog",
    targetPlatform: "LinkedIn / FinServ Editorial",
    campaignName: "Wealth Advisory Education Series",
    title: "Strategic Asset Allocation & Portfolio Resiliency",
    riskTier: "Moderate Risk",
    riskBadgeColor: "bg-amber-50 text-amber-700 border-amber-200",
    description: "Financial wealth advisory content with educational tone, appropriate regulatory disclaimers, but containing an unqualified commercial outcome assertion.",
    highlights: ["Unqualified Commercial Guarantee", "Regulatory Disclaimers", "Formal Financial Tone"],
    content: `Market volatility reminds investors that durable wealth accumulation is driven by disciplined risk mitigation rather than speculative momentum.

A balanced multi-asset allocation strategy has historically protected portfolio purchasing power through inflationary cycles. While no portfolio strategy eliminates market downturns, systematic rebalancing offers proven acceleration of business performance and capital preservation over multi-year horizons.

Our quantitative advisory framework evaluates macroeconomic variables to optimize risk-adjusted returns for accredited institutional and private wealth clients.

Disclaimer: Past performance is no guarantee of future results. Investments are subject to market risks, including the possible loss of principal. Consult a certified financial fiduciary before executing allocation adjustments.`,
  },
];
