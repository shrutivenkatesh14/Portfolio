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
    sub: "Apple's global supply chain",
    outcome: "Apple has to order chips and parts months before it knows how many iPhones will sell. We mapped how that bet works, and what happened when lockdowns hit a key iPhone factory in 2022.",
    color: "sage",
    date: "Feb 2026",
    featured: true,
    problem: "For a supply chain analytics course, Carlos Henríquez and I set out to explain why Apple's supply chain is built the way it is, and where that design is fragile.",
    approach: [
      "Mapped Apple's end-to-end network — sourcing, semiconductor fabrication, contract assembly (Foxconn, Pegatron), warehousing, and distribution — from public filings and supplier reports",
      "Applied the newsvendor model to launch-window forecasting: running out of a new iPhone costs more (lost sales, ecosystem revenue) than having extra, which pushes Apple to stock high instead of minimizing cost",
      "Used the 2022 Zhengzhou lockdowns as a case study in how assembly concentration turns a localized disruption into a global shortage (Reuters reported iPhone output could fall by as much as 30%)",
      "Connected course frameworks — multi-echelon inventory, risk pooling, the bullwhip effect — to where they hold and where Apple's scale breaks their textbook assumptions",
      "Delivered a written report and class presentation, citing 10-K filings, supplier responsibility reports, and news coverage throughout"
    ],
    result: "Report and presentation for OMG 411 (Supply Chain Analytics), Simon Business School — argued Apple deliberately absorbs inventory risk in exchange for low stockout risk during peak weeks, hedged by vertical integration and supplier diversification.",
    diagram: {
      head: "The story, in five stamps",
      hand: "where the risk gets locked in",
      stops: [
        { n: "01", title: "Commit early", text: "Orders locked in up to 150 days ahead",                      tag: "Capacity commitment", src: "Apple 10-K",         color: "sage" },
        { n: "02", title: "Launch spike", text: "iPhone is about half of net sales",                          tag: "Demand volatility",   src: "Apple 10-K",         color: "sage" },
        { n: "03", title: "Stock high",   text: "Running out costs more than having extra",                   tag: "Newsvendor model",    src: "Our analysis",       color: "sage" },
        { n: "04", title: "Zhengzhou",    text: "Foxconn site hit by lockdowns. Output could fall up to 30%", tag: "Concentration risk",  src: "Reuters projection", color: "dusty-rose", postmark: ["Zhengzhou", "Oct 2022"], key: true },
        { n: "05", title: "Q1 FY2023",    text: "Revenue down about 5%, with supply limits and weak macro",   tag: "Result",              src: "Apple 10-Q",         color: "dusty-rose" }
      ],
      bar: { caption: "Up to 150 days of forecast uncertainty", left: "Capacity locked in", right: "Demand fully visible" },
      why:   { label: "Why commit so early?", text: "Chips and parts are ordered up to 150 days ahead, long before anyone knows how a launch will sell." },
      catch: { label: "The catch.", text: "Final assembly is concentrated in a small number of facilities, which cuts cost but raises the risk of disruption. Apple's hedges: designing its own chips (Apple Silicon), assembling in India, and using more suppliers." },
      takeaway: "Concentrated assembly cuts cost but raises disruption risk, the classic efficiency-versus-resilience tradeoff."
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
  },
  {
    id: "post-2",
    tag: "SQL",
    title: "SQL Noir, Case #002: The Stolen Sound",
    teaser: "A prized record vanishes from a neon-lit 1980s record store, and no two witnesses agree. Someone is lying, and only the data can tell who.",
    date: "Oct 2026",
    links: [
      { platform: "Substack", url: "https://vshruti.substack.com/p/sql-noir-a-detective-sql-story-case-c73" },
      { platform: "Medium", url: "https://medium.com/@vshruti193/sql-noir-a-detective-sql-story-case-002-the-stolen-sound-ec14c3aa5465" }
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
