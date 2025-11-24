"use client";

import React, { useEffect, useState } from "react";

function getColor(value) {
  if (value === null || value === undefined || value < 0) return "#9ca3af"; // grey
  if (value >= 70) return "#16a34a"; // green
  if (value >= 50) return "#f97316"; // amber
  return "#dc2626"; // red
}

function ScoreCircle({ label, value }) {
  const color = getColor(value ?? -1);
  const displayValue = value !== null && value !== undefined ? value : "-";

  return (
    <div
      style={{
        display: "inline-flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "0.25rem",
        padding: "0.25rem 0.5rem",
      }}
    >
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: "999px",
          border: `3px solid ${color}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: 700,
          fontSize: "1.2rem",
          color,
          backgroundColor: "#ffffff",
        }}
      >
        {displayValue}
      </div>
      <div style={{ fontSize: "0.8rem", fontWeight: 600 }}>{label}</div>
    </div>
  );
}

function SummaryCard({ title, bullets }) {
  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: "0.75rem 0.9rem",
        backgroundColor: "#f9fafb",
        boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
      }}
    >
      <h2
        style={{
          fontSize: "1rem",
          fontWeight: 600,
          marginBottom: "0.5rem",
        }}
      >
        {title}
      </h2>
      <ul
        style={{
          margin: 0,
          paddingLeft: "1.1rem",
          fontSize: "0.85rem",
          color: "#4b5563",
        }}
      >
        {bullets.map((b, idx) => (
          <li key={idx}>{b}</li>
        ))}
      </ul>
    </div>
  );
}

export default function LLMSEODashboardRootPage() {
  const [scores, setScores] = useState(null);
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [siteUrl, setSiteUrl] = useState("https://onoxygen.co.uk");

  const [selectedPage, setSelectedPage] = useState(null);
  const [pageDetail, setPageDetail] = useState(null);
  const [pageDetailLoading, setPageDetailLoading] = useState(false);
  const [pageDetailError, setPageDetailError] = useState(null);

  useEffect(() => {
    runAnalysis(siteUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runAnalysis(url) {
    try {
      setLoading(true);
      setError(null);
      setSelectedPage(null);
      setPageDetail(null);
      setPageDetailError(null);

      // 1) site-level scores
      const scoreRes = await fetch("http://127.0.0.1:8000/api/v3/scores", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!scoreRes.ok) {
        throw new Error(`Backend responded with ${scoreRes.status}`);
      }

      const scoreData = await scoreRes.json();
      setScores(scoreData);

      // 2) crawl for page-level scores
      const crawlRes = await fetch("http://127.0.0.1:8000/api/v3/crawl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!crawlRes.ok) {
        throw new Error(`Crawl endpoint responded with ${crawlRes.status}`);
      }

      const crawlData = await crawlRes.json();
      setPages(crawlData);
    } catch (e) {
      console.error("Error running analysis:", e);
      setError(e.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function loadPageDetail(url) {
    try {
      setPageDetailLoading(true);
      setPageDetailError(null);

      const res = await fetch("http://127.0.0.1:8000/api/v3/page-detail", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        throw new Error(`Page detail responded with ${res.status}`);
      }

      const data = await res.json();
      setPageDetail(data);
    } catch (e) {
      console.error("Error loading page detail:", e);
      setPageDetailError(e.message || "Unknown error");
    } finally {
      setPageDetailLoading(false);
    }
  }

  const overall = scores?.overall ?? null;
  const content = scores?.content ?? null;
  const aeo = scores?.aeo ?? null;
  const tech = scores?.tech ?? null;
  const mobile = scores?.mobile ?? null;

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#f3f4f6",
        fontFamily:
          "system-ui, -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: 1100,
          margin: "0 auto",
          padding: "1.5rem 1rem 3rem",
        }}
      >
        {/* Header */}
        <header
          style={{
            marginBottom: "1.5rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.25rem",
          }}
        >
          <h1
            style={{
              fontSize: "1.9rem",
              fontWeight: 700,
              letterSpacing: "-0.02em",
            }}
          >
            LLMSEO V3 – Site Overview
          </h1>
          <p style={{ color: "#4b5563", maxWidth: 700 }}>
            This dashboard shows a high-level scoring of your website&apos;s
            visibility and readiness for AI and search engines. Higher scores
            mean better performance.
          </p>

          {/* Simple site URL box + button */}
          <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
            <input
              type="text"
              value={siteUrl}
              onChange={(e) => setSiteUrl(e.target.value)}
              style={{
                flex: 1,
                padding: "0.4rem 0.6rem",
                borderRadius: 6,
                border: "1px solid #d1d5db",
                fontSize: "0.9rem",
              }}
              placeholder="https://example.com"
            />
            <button
              onClick={() => runAnalysis(siteUrl)}
              style={{
                padding: "0.4rem 0.9rem",
                borderRadius: 6,
                border: "none",
                backgroundColor: "#2563eb",
                color: "#ffffff",
                fontSize: "0.9rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {loading ? "Analysing…" : "Run scan"}
            </button>
          </div>

          {/* Error display */}
          {error && (
            <p style={{ color: "#b91c1c", fontSize: "0.85rem", marginTop: "0.4rem" }}>
              Backend error: {error}
            </p>
          )}
        </header>

        {/* Score circles row */}
        <section
          style={{
            display: "flex",
            gap: "1.5rem",
            flexWrap: "wrap",
            alignItems: "flex-start",
            marginBottom: "1.5rem",
          }}
        >
          <ScoreCircle label="Overall" value={overall} />
          <ScoreCircle label="Content" value={content} />
          <ScoreCircle label="AI / AEO" value={aeo} />
          <ScoreCircle label="Tech" value={tech} />
          <ScoreCircle label="Mobile" value={mobile} />
        </section>

        {/* Summary grid – static text for now */}
        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "1rem",
            marginBottom: "2rem",
          }}
        >
          <SummaryCard
            title="Content"
            bullets={[
              "✔ Clear service pages in navigation.",
              "❌ Some important pages are quite short.",
              "⚠ Add FAQs for key services to deepen content.",
            ]}
          />
          <SummaryCard
            title="AI / AEO (Answer Engine Optimisation)"
            bullets={[
              "✔ Good use of headings and structure.",
              "❌ Few question-based sections (How/What/Why).",
              "⚠ Create structured Q&A blocks on main pages.",
            ]}
          />
          <SummaryCard
            title="Technical"
            bullets={[
              "✔ Clean URLs and HTTPS in place.",
              "⚠ Check image sizes & caching for speed.",
              "❌ Missing schema markup for LocalBusiness/FAQ.",
            ]}
          />
          <SummaryCard
            title="Mobile"
            bullets={[
              "✔ Layout adapts on smaller screens.",
              "❌ Primary CTA may sit below the fold on mobile.",
              "⚠ Review tap target sizes for menu and buttons.",
            ]}
          />
        </section>

        {/* Sitemap / page-level scores + detail */}
        <section
          style={{
            borderTop: "1px solid #e5e7eb",
            paddingTop: "1.2rem",
            marginTop: "0.5rem",
          }}
        >
          <h2
            style={{
              fontSize: "1.1rem",
              fontWeight: 600,
              marginBottom: "0.5rem",
            }}
          >
            Site pages & page-level scores
          </h2>

          {pages.length === 0 ? (
            <p style={{ fontSize: "0.85rem", color: "#6b7280" }}>
              No crawl data yet. Run a scan to see page-level scores.
            </p>
          ) : (
            <div
              style={{
                maxHeight: "320px",
                overflowY: "auto",
                borderRadius: 8,
                border: "1px solid #e5e7eb",
                backgroundColor: "#ffffff",
              }}
            >
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: "0.8rem",
                }}
              >
                <thead>
                  <tr
                    style={{
                      backgroundColor: "#f9fafb",
                      borderBottom: "1px solid #e5e7eb",
                      textAlign: "left",
                    }}
                  >
                    <th style={{ padding: "0.4rem 0.6rem" }}>URL</th>
                    <th style={{ padding: "0.4rem 0.6rem" }}>Depth</th>
                    <th style={{ padding: "0.4rem 0.6rem" }}>Words</th>
                    <th style={{ padding: "0.4rem 0.6rem" }}>Overall</th>
                    <th style={{ padding: "0.4rem 0.6rem" }}>Content</th>
                    <th style={{ padding: "0.4rem 0.6rem" }}>AEO</th>
                    <th style={{ padding: "0.4rem 0.6rem" }}>Tech</th>
                    <th style={{ padding: "0.4rem 0.6rem" }}>Mobile</th>
                  </tr>
                </thead>
                <tbody>
                  {pages.map((p, idx) => {
                    const shortUrl =
                      p.url.replace(siteUrl.replace(/\/$/, ""), "") || "/";
                    return (
                      <tr
                        key={idx}
                        style={{
                          borderBottom: "1px solid #f3f4f6",
                          cursor: "pointer",
                          backgroundColor:
                            selectedPage && selectedPage.url === p.url
                              ? "#eef2ff"
                              : "transparent",
                        }}
                        onClick={() => {
                          setSelectedPage(p);
                          loadPageDetail(p.url);
                        }}
                      >
                        <td style={{ padding: "0.35rem 0.6rem" }}>
                          <span style={{ paddingLeft: p.depth * 12 }}>
                            {shortUrl}
                          </span>
                        </td>
                        <td style={{ padding: "0.35rem 0.6rem" }}>{p.depth}</td>
                        <td style={{ padding: "0.35rem 0.6rem" }}>
                          {p.word_count}
                        </td>
                        <td style={{ padding: "0.35rem 0.6rem" }}>
                          {p.overall}
                        </td>
                        <td style={{ padding: "0.35rem 0.6rem" }}>
                          {p.content}
                        </td>
                        <td style={{ padding: "0.35rem 0.6rem" }}>{p.aeo}</td>
                        <td style={{ padding: "0.35rem 0.6rem" }}>{p.tech}</td>
                        <td style={{ padding: "0.35rem 0.6rem" }}>
                          {p.mobile}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Page detail panel */}
          <div
            style={{
              marginTop: "1rem",
              borderRadius: 8,
              border: "1px solid #e5e7eb",
              backgroundColor: "#ffffff",
              padding: "0.75rem 0.9rem",
            }}
          >
            <h3
              style={{
                fontSize: "1rem",
                fontWeight: 600,
                marginBottom: "0.5rem",
              }}
            >
              Page detail
            </h3>

            {!selectedPage && !pageDetailLoading && !pageDetailError && (
              <p style={{ fontSize: "0.85rem", color: "#6b7280" }}>
                Click a row in the table above to see detailed insights for a specific
                page.
              </p>
            )}

            {pageDetailLoading && (
              <p style={{ fontSize: "0.85rem", color: "#6b7280" }}>
                Loading page detail…
              </p>
            )}

            {pageDetailError && (
              <p style={{ fontSize: "0.85rem", color: "#b91c1c" }}>
                Error loading page detail: {pageDetailError}
              </p>
            )}

            {pageDetail && (
              <div style={{ fontSize: "0.85rem", color: "#374151" }}>
                <p
                  style={{
                    marginBottom: "0.3rem",
                    wordBreak: "break-all",
                  }}
                >
                  <strong>URL:</strong> {pageDetail.url}
                </p>
                {pageDetail.title && (
                  <p style={{ marginBottom: "0.3rem" }}>
                    <strong>Title:</strong> {pageDetail.title}
                  </p>
                )}
                <p style={{ marginBottom: "0.3rem" }}>
                  <strong>Word count:</strong> {pageDetail.word_count}
                </p>
                <p style={{ marginBottom: "0.3rem" }}>
                  <strong>Scores:</strong>{" "}
                  Overall {pageDetail.overall} • Content {pageDetail.content} • AEO{" "}
                  {pageDetail.aeo} • Tech {pageDetail.tech} • Mobile{" "}
                  {pageDetail.mobile}
                </p>

                <div style={{ marginTop: "0.5rem" }}>
                  <strong>Key issues / opportunities:</strong>
                  <ul style={{ marginTop: "0.25rem", paddingLeft: "1.1rem" }}>
                    {pageDetail.issues.map((issue, idx) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                </div>

                {pageDetail.headings && pageDetail.headings.length > 0 && (
                  <div style={{ marginTop: "0.5rem" }}>
                    <strong>Top headings (H1–H3):</strong>
                    <ul style={{ marginTop: "0.25rem", paddingLeft: "1.1rem" }}>
                      {pageDetail.headings.map((h, idx) => (
                        <li key={idx}>{h}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        <section
          style={{
            borderTop: "1px solid #e5e7eb",
            paddingTop: "1rem",
            fontSize: "0.85rem",
            color: "#6b7280",
            marginTop: "1rem",
          }}
        >
          <p style={{ marginBottom: "0.25rem" }}>
            Next steps in V3 (coming soon on this screen):
          </p>
          <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
            <li>Competitor comparison and radar chart</li>
            <li>Mobile audit details and SERP opportunity insights</li>
          </ul>
        </section>
      </div>
    </div>
  );
}

