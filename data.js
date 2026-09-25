/* ==========================================================================
   THE COLLECTION — data
   Edit these arrays to update the site. Nothing else needs to change —
   the project grid, the home page "featured" picks, the case-file overlay,
   and the writing page all render from here.
   ========================================================================== */

const PROJECTS = [
  {
    id: "apple-supply-chain",
    denom: "01¢",
    tag: "Supply Chain Analytics",
    title: "Designing for Volatility",
    outcome: "Mapped Apple's global supply chain to show how launch-driven demand and irreversible semiconductor capacity commitments drive its forecasting and risk strategy.",
    color: "sage",
    date: "Feb 2026",
    featured: true,
    problem: "For a supply chain analytics course, my teammate and I set out to explain why Apple's supply chain is built the way it is — a company that launches on a fixed calendar, commits semiconductor capacity months before demand is known, and concentrates final assembly in a handful of facilities.",
    approach: [
      "Mapped Apple's end-to-end network — sourcing, semiconductor fabrication, contract assembly (Foxconn, Pegatron), warehousing, and distribution — from public filings and supplier reports",
      "Applied newsvendor logic to launch-window forecasting, showing why underage costs (lost sales, ecosystem revenue) push Apple toward high service levels over pure cost minimization",
      "Used the 2022 Zhengzhou lockdowns as a case study in how assembly concentration turns a localized disruption into a global shortage",
      "Connected course frameworks — multi-echelon inventory, risk pooling, the bullwhip effect — to where they hold and where Apple's scale breaks their textbook assumptions",
      "Delivered a written report and class presentation, citing 10-K filings, supplier responsibility reports, and news coverage throughout"
    ],
    result: "Report and presentation for OMG 411 (Supply Chain Analytics), Simon Business School — argued Apple deliberately absorbs inventory risk in exchange for near-zero stockout risk during its highest-margin weeks, hedged by vertical integration and supplier diversification.",
    links: [
      { label: "Full report", url: "assets/apple-supply-chain/report.pdf" },
      { label: "Slides", url: "assets/apple-supply-chain/slides.pdf" }
    ]
  }
];

const POSTS = [
  {
    id: "post-1",
    tag: "SQL",
    title: "SQL Noir, Case #001: The Vanishing Briefcase",
    teaser: "A briefcase goes missing from a 1980s lounge, and the only way to find the culprit is by querying crime scenes, suspects, and interview transcripts.",
    date: "Aug 2026",
    links: [
      { platform: "Substack", url: "https://substack.com/home/post/p-213179638" },
      { platform: "Medium", url: "https://medium.com/@vshruti193/sql-noir-a-detective-sql-story-case-001-the-vanishing-briefcase-7f0cf78a3b8d" }
    ]
  }
];
