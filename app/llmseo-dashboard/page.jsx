"use client";

import React from "react";

export default function LLMSEODashboardPage() {
  // TODO: Replace these with real data from your FastAPI backend
  const site = "https://onoxygen.co.uk";
  const lviScore = 58;
  const lviDelta = 5;
  const coverage = 40;
  const schemaScore = 35;
  const quickWinsCount = 7;
  const issuesCount = 27;
  const pagesAnalysed = 14;
  const criticalPages = 3;
  const needsWorkPages = 5;
  const okPages = 6;
  const competitorsCount = 5;
  const reportsCount = 4;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* TOP NAV */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 lg:px-0">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-emerald-400 text-slate-950 font-black">
              L
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-slate-100">
                LLMSEO
              </div>
              <div className="text-xs text-slate-400">
                Optimise for AI, not just Google
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <button className="rounded-full border border-slate-700 px-3 py-1 text-slate-200 hover:border-slate-500 hover:bg-slate-900">
              Docs
            </button>
            <button className="rounded-full bg-sky-500 px-4 py-1.5 text-xs font-semibold text-slate-950 hover:bg-sky-400">
              Sign in
            </button>
          </div>
        </div>
      </header>

      {/* MAIN */}
      <main className="mx-auto max-w-6xl px-4 pb-16 pt-6 lg:px-0">
        {/* TOP SITE + CONTROLS */}
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.8)]" />
              Live scan connected
            </div>
            <h1 className="mt-1 text-xl font-semibold text-slate-50 sm:text-2xl">
              AI Visibility Dashboard
            </h1>
            <p className="mt-1 text-xs text-slate-400 sm:text-sm">
              Site:{" "}
              <span className="font-mono text-slate-200">{site}</span>
              <span className="mx-2 text-slate-600">•</span>
              Last scan: Today 10:42
              <span className="mx-2 text-slate-600">•</span>
              Next auto-scan: Tonight 02:00
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <button className="rounded-full border border-slate-700 px-3 py-1 text-slate-200 hover:border-sky-500 hover:bg-slate-900">
              Change site
            </button>
            <button className="rounded-full border border-slate-700 px-3 py-1 text-slate-200 hover:border-sky-500 hover:bg-slate-900">
              Download PDF
            </button>
            <button className="rounded-full bg-emerald-400 px-4 py-1.5 text-xs font-semibold text-slate-950 hover:bg-emerald-300">
              Re-run scan
            </button>
          </div>
        </div>

        {/* GRID: LVI HERO + STATS */}
        <section className="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1.4fr)]">
          {/* LVI HERO CARD */}
          <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-950 to-slate-950 p-5 shadow-[0_0_40px_rgba(15,23,42,0.8)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-sky-400">
                  AI Visibility Score
                </p>
                <div className="mt-1 flex items-baseline gap-3">
                  <span className="text-4xl font-semibold text-slate-50">
                    {lviScore}
                  </span>
                  <span className="text-sm text-slate-400">/ 100</span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                    ↑ {lviDelta}
                    <span className="text-slate-400">since last scan</span>
                  </span>
                </div>
                <p className="mt-3 max-w-md text-xs text-slate-400">
                  This score reflects how easily AI assistants (ChatGPT,
                  Gemini, Perplexity) can read, understand, and recommend your
                  site. Higher is better.
                </p>
              </div>
              {/* Fake gauge */}
              <div className="relative flex h-28 w-28 items-center justify-center">
                <div className="absolute inset-0 rounded-full bg-slate-900" />
                <div
                  className="absolute inset-0 rounded-full border-[6px] border-slate-800"
                  aria-hidden="true"
                />
                <div
                  className="absolute inset-1 rounded-full border-[6px] border-transparent"
                  style={{
                    borderTopColor: "#22c55e",
                    borderRightColor: "#22c55e",
                    borderBottomColor: lviScore > 70 ? "#22c55e" : "#334155",
                    borderLeftColor: "#334155",
                  }}
                  aria-hidden="true"
                />
                <div className="relative flex flex-col items-center justify-center rounded-full bg-slate-950 px-3 py-2 text-center">
                  <span className="text-[10px] uppercase tracking-wide text-slate-400">
                    LVI
                  </span>
                  <span className="text-lg font-semibold text-slate-50">
                    {lviScore}
                  </span>
                  <span className="text-[10px] text-slate-500">/100</span>
                </div>
              </div>
            </div>

            {/* mini KPIs */}
            <div className="mt-4 grid gap-3 text-xs text-slate-300 sm:grid-cols-3">
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-slate-500">
                  Coverage
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-50">
                  {coverage}%
                </p>
                <p className="mt-1 text-[11px] text-slate-500">
                  Pages that are structurally AI-ready.
                </p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-slate-500">
                  Schema health
                </p>
                <p className="mt-1 text-sm font-semibold text-slate-50">
                  {schemaScore}%
                </p>
                <p className="mt-1 text-[11px] text-slate-500">
                  JSON-LD completeness on key pages.
                </p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-slate-500">
                  Quick wins
                </p>
                <p className="mt-1 text-sm font-semibold text-emerald-300">
                  {quickWinsCount}
                </p>
                <p className="mt-1 text-[11px] text-slate-500">
                  High-impact fixes you can ship this week.
                </p>
              </div>
            </div>
          </div>

          {/* SUMMARY CARDS SIDE COLUMN */}
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-1">
            {/* Site Plan card */}
            <DashboardCard
              title="Site plan (crawl)"
              subtitle={`${pagesAnalysed} pages analysed`}
            >
              <p className="text-xs text-slate-400">
                <StatusDot color="red" /> {criticalPages} critical
                <span className="mx-1 text-slate-600">•</span>
                <StatusDot color="amber" /> {needsWorkPages} need work
                <span className="mx-1 text-slate-600">•</span>
                <StatusDot color="green" /> {okPages} OK
              </p>
              <button className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-sky-400 hover:text-sky-300">
                View site map
                <span aria-hidden="true">→</span>
              </button>
            </DashboardCard>

            {/* Competitors card */}
            <DashboardCard
              title="Competitors"
              subtitle={`${competitorsCount} domains tracked`}
            >
              <ul className="mt-1 space-y-1 text-xs text-slate-400">
                <li>• Losing “oxygen travel uk” to competitor content.</li>
                <li>• No comparison page for “AnyO₂ vs Inogen” – easy win.</li>
              </ul>
              <button className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-sky-400 hover:text-sky-300">
                View competitor analysis
                <span aria-hidden="true">→</span>
              </button>
            </DashboardCard>

            {/* Fixes card */}
            <DashboardCard
              title="Issues & opportunities"
              subtitle={`${issuesCount} total items`}
            >
              <ul className="mt-1 space-y-1 text-xs text-slate-400">
                <li>• Missing FAQ schema on 4 key pages.</li>
                <li>• 3 pages with no clear H1/H2 structure.</li>
                <li>• 2 thin guides with low AI answerability.</li>
              </ul>
              <button className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-sky-400 hover:text-sky-300">
                Open recommendations
                <span aria-hidden="true">→</span>
              </button>
            </DashboardCard>

            {/* Reports card */}
            <DashboardCard
              title="Reports & history"
              subtitle={`${reportsCount} full reports`}
            >
              <ul className="mt-1 space-y-1 text-xs text-slate-400">
                <li>Today • LVI 58 • PDF generated</li>
                <li>Last week • LVI 53 • Baseline scan</li>
              </ul>
              <button className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-sky-400 hover:text-sky-300">
                View all reports
                <span aria-hidden="true">→</span>
              </button>
            </DashboardCard>
          </div>
        </section>

        {/* BOTTOM INSIGHTS */}
        <section className="mt-6 grid gap-4 md:grid-cols-2">
          {/* Insights feed */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
            <h2 className="text-sm font-semibold text-slate-100">
              Today&apos;s AI visibility summary
            </h2>
            <p className="mt-1 text-xs text-slate-400">
              Snapshot of what changed since your last scan.
            </p>
            <ul className="mt-3 space-y-2 text-xs text-slate-300">
              <li>
                • New competitor page detected for “oxygen travel uk” – you
                don&apos;t have a matching guide yet.
              </li>
              <li>
                • Structured data detected on /contact – LocalBusiness schema
                partially configured.
              </li>
              <li>
                • 2 pages improved H1/H2 structure after recent edits.
              </li>
            </ul>
          </div>

          {/* Upcoming actions */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
            <h2 className="text-sm font-semibold text-slate-100">
              7-day action plan (high impact)
            </h2>
            <p className="mt-1 text-xs text-slate-400">
              Focus on these items to move your LVI from 58 → 70+.
            </p>
            <ol className="mt-3 space-y-2 text-xs text-slate-300">
              <li>
                1. Publish a dedicated “Oxygen Travel Guide UK” with Q&A and
                table of airline rules.
              </li>
              <li>
                2. Add FAQ schema to home and product pages with 5 core
                questions per page.
              </li>
              <li>
                3. Create a comparison page: “AnyO₂ vs Inogen” optimised around
                decision-making queries.
              </li>
              <li>
                4. Strengthen About page with credentials and local trust
                signals (reviews, years in business).
              </li>
            </ol>
          </div>
        </section>
      </main>
    </div>
  );
}

function DashboardCard({ title, subtitle, children }) {
  return (
    <div className="flex h-full flex-col rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
        {subtitle && (
          <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
        )}
      </div>
      <div className="mt-3 flex-1">{children}</div>
    </div>
  );
}

function StatusDot({ color }) {
  const map = {
    red: "bg-red-500",
    amber: "bg-amber-400",
    green: "bg-emerald-400",
  };
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${map[color] || "bg-slate-500"}`}
    />
  );
}

