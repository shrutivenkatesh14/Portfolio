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
    problem: "For a supply chain analytics course, Carlos Henríquez and I set out to explain why Apple's supply chain is built the way it is — a company that launches on a fixed calendar, commits semiconductor capacity months before demand is known, and concentrates final assembly in a handful of facilities.",
    approach: [
      "Mapped Apple's end-to-end network — sourcing, semiconductor fabrication, contract assembly (Foxconn, Pegatron), warehousing, and distribution — from public filings and supplier reports",
      "Applied newsvendor logic to launch-window forecasting, showing why underage costs (lost sales, ecosystem revenue) push Apple toward high service levels over pure cost minimization",
      "Used the 2022 Zhengzhou lockdowns as a case study in how assembly concentration turns a localized disruption into a global shortage (Reuters reported iPhone output could fall by as much as 30%)",
      "Connected course frameworks — multi-echelon inventory, risk pooling, the bullwhip effect — to where they hold and where Apple's scale breaks their textbook assumptions",
      "Delivered a written report and class presentation, citing 10-K filings, supplier responsibility reports, and news coverage throughout"
    ],
    result: "Report and presentation for OMG 411 (Supply Chain Analytics), Simon Business School — argued Apple deliberately absorbs inventory risk in exchange for low stockout risk during peak weeks, hedged by vertical integration and supplier diversification.",
    diagram: {
      steps: [
        { kind: "plan",  title: "Commit early",    lines: ["Component orders set", "up to 150 days out"], src: "Apple 10-K, FY2025" },
        { kind: "plan",  title: "Launch spike",    lines: ["iPhone is about", "half of net sales"],        src: "Apple 10-K, FY2025" },
        { kind: "plan",  title: "Stock high",      lines: ["Stockouts cost", "more than excess"],          src: "Our analysis (newsvendor)" },
        { kind: "shock", title: "Zhengzhou, 2022", lines: ["iPhone output could", "fall as much as 30%"],  src: "Reuters projection" },
        { kind: "shock", title: "Q1 FY2023",       lines: ["Revenue down", "about 5%"],                    src: "Apple 10-Q" }
      ],
      legend: [
        { kind: "plan",  label: "Apple's design choices" },
        { kind: "shock", label: "2022 disruption and result" }
      ],
      takeaway: "Concentrated assembly cuts cost but raises disruption risk.",
      note: "The Q1 FY2023 decline also reflected a weak macro environment, per Apple's CFO."
    },
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

/* Hero stamp collage (home page, right of the intro text).
   One array per row, left to right. f = file in assets/stamps/, a = width / height of that stamp.
   Rows fill the collage width on their own, so swap, reorder or move a stamp between rows
   without touching any CSS. Keep the whole block about as tall as the intro text. */
const HERO_STAMPS = [
  [{ f: "bermuda-flower.jpg", a: 1.475 }, { f: "togolaise-hibiscus.jpg", a: 0.764 }, { f: "seychelles-fish.jpg", a: 1.536 }],
  [{ f: "indonesia-flower.jpg", a: 0.658 }, { f: "romania-woman-in-green-dress.jpg", a: 0.694 }, { f: "peru-statue.jpg", a: 1.329 }, { f: "usa-circus.jpg", a: 0.639 }, { f: "sharjah-cat.jpg", a: 0.812 }],
  [{ f: "soviet-union-dancers.jpg", a: 1.401 }, { f: "scenery-2.jpg", a: 0.756 }, { f: "seychelles-turtle.jpg", a: 1.521 }],
  [{ f: "india-ajanta-caves.jpg", a: 0.853 }, { f: "woman-on-horseback.jpg", a: 1.328 }, { f: "seychelles-eagle.jpg", a: 0.674 }, { f: "lady-by-the-river.jpg", a: 1.346 }],
  [{ f: "monet-sailing-boat.jpg", a: 1.371 }, { f: "van-gogh-sunflowers.jpg", a: 0.749 }, { f: "car-1.jpg", a: 1.365 }],
  [{ f: "peru-pottery.jpg", a: 0.872 }, { f: "seychelles-owl.jpg", a: 0.674 }, { f: "rwanda-flower-and-mountain.jpg", a: 1.552 }, { f: "seychelles-vanilla-flower.jpg", a: 0.636 }]
];
