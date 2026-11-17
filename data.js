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
      "Used newsvendor logic to explain launch-window inventory: lost sales and ecosystem revenue cost more than excess stock, so Apple's service level sits above the median forecast",
      "Used the 2022 Zhengzhou lockdowns as a case study in how assembly concentration turns a localized disruption into a global shortage (Reuters reported iPhone output could fall by as much as 30%)",
      "Linked multi-echelon inventory, risk pooling, and the bullwhip effect to Apple's buffer placement, and to where its scale breaks textbook assumptions",
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
  },
  {
    id: "pokedex-viz",
    denom: "02¢",
    tag: "Data Visualization",
    title: "Shruti's Pokédex",
    sub: "137 picks vs 1,025 species, in Tableau",
    outcome: "I wondered if my favorite Pokémon were overpowered, so I checked. Next to the whole Pokédex, my team's base stats run 59.9 points higher. Next to fair peers, only 14.1.",
    color: "butter-yellow",
    date: "Nov 2026",
    featured: true,
    shot: {
      src: "assets/pokedex-viz/overview.png",
      alt: "The Overview dashboard: a ring of 1,025 dots with my 137 favorites in color, next to a Mewtwo dex entry, its six stat bars, and a chart of my picks by generation.",
      note: "psst, the real one is clickable"
    },
    problem: "I love Pokémon, and I had a feeling my favorites leaned strong. I wanted to find out if that was true, so I took my 137 favorites and compared them with all 1,025 species. I also wanted the answer to be something people could click around in, not a stack of charts.",
    approach: [
      "Put together a 15-sheet data set covering all 1,025 species: stats, color, generation, capture rate, legendary status, and evolution lines. Reshaped the stats into a long format to make the stat charts easier to build",
      "Compared my picks with the full dex on color, generation, stats, rarity, and evolution stage. I used ratios, so 2.07x means something shows up twice as often on my team as it does in the dex",
      "Added a fairer comparison group of fully evolved, non-legendary Pokémon. Nearly half the dex is still evolving, so measuring my team against everything made the gap look bigger",
      "Built 16 sheets in Tableau and assembled them into six fixed-size dashboards with floating layouts, custom background art, and a navigation button tray. Chart types include a ring of 1,025 dots, waffle charts, a dual-axis bar and sprite ladder, diverging ratio bars, a heat map, and a sprite wall",
      "Added two parameters (the selected Pokémon and the selected Eeveelution) and two Change Parameter actions. Clicking a dot on Overview or an Eeveelution on the wheel feeds calculated fields that update the sprite, dex card, and stat bars",
      "Wrote calculated fields for the dot highlighting and sizing, above and below the dex flags, top 10 and rarity filters, and the row and column math behind the waffle, club grid, and wall layouts. Added reference lines for the dex averages, custom shape palettes for each sprite set, and a tooltip on every chart"
    ],
    result: "It's live on Tableau Public. Against the full dex my team's base stats run 59.9 points higher; against fair peers only 14.1, because nearly half the dex is still evolving and only 22% of my team is. Another tell: 26 of my 137 picks (19%) are legendary or mythical, against 9% of the dex.",
    links: [
      { label: "View live viz", url: "https://public.tableau.com/views/ShrutisPokedex/Overview?:language=en-US&:sid=&:display_count=n&:origin=viz_share_link" }
    ]
  },
  {
    id: "bridge-strikes",
    denom: "03¢",
    tag: "Data Analysis",
    title: "Bridge Strikes",
    sub: "Which NYC bridges to fix first, in Python",
    outcome: "Trucks hit low bridges in New York City 943 times in 13 years, and 92% of the hits were on roads that are not truck routes. Fixing the 10 bridges hit most in earlier years would have covered 46% of the next year's strikes.",
    color: "powder-blue",
    date: "Nov 2026",
    featured: true,
    problem: "A city can only fix so many low bridges. I used New York City's public records of truck strikes to ask which bridges to fix first, and whether past strikes show where the next ones will be.",
    approach: [
      "Cleaned up 943 strike records with Python. I flagged 10 map points that looked wrong, filled in 8 missing bridge ID numbers from where the strike happened, and cleared the ID on 3 records that did not match their street. 35 records still have no ID, so they are not in the bridge counts. Every step is written down in the code",
      "Counted bridges that have two ID numbers as one. If two IDs were within 30 meters of each other on the same road, I merged them. That turned 140 IDs into 128 bridges",
      "Tested the idea. For each year from 2016 to 2025, I pretended I only knew the years before it, picked the bridges hit most so far, and counted how many of that year's strikes happened at them. I compared that with picking at random and with the best possible picks",
      "Checked which bridges changed over time, using a test that allows for luck. Three did",
      "Split the problem in two: the 92% of strikes on roads that are not truck routes, and the 78 on truck routes. For the first group I would look at how trucks end up on these roads, and at signs. For the second, the bridge or road itself may need a closer look. I also checked which direction the strikes come from at the busiest bridges",
      "Built an interactive page in Python with Plotly. It has a slider for how many bridges to fix, a table of strikes per year, and the truck-route split. It also says what the data cannot show"
    ],
    result: "Picking by every past year worked about as well as picking by only the last 3 years. Ten bridges picked at random would cover about 8% of the next year's strikes, and the best possible picks would cover 61%. Three bridges changed in ways luck does not explain. Two dropped, one rose, and I do not know why. The data has no bridge height, cost or traffic counts, so I make no claims about money saved. My advice: start with those 10 bridges, put a sign or sensor on the side where strikes come from, and look at how trucks end up on the roads that are not truck routes, and at the signs there.",
    diagram: {
      head: "The project, in five stamps",
      hand: "past strikes show where to look",
      stops: [
        { n: "01", title: "Clean",      text: "943 strike records cleaned up. 140 IDs became 128 bridges", tag: "Data",        src: "NYC Open Data", color: "powder-blue" },
        { n: "02", title: "Pick",       text: "Pick the bridges hit most in earlier years",                tag: "Idea",        src: "Python",        color: "powder-blue" },
        { n: "03", title: "Test",       text: "10 bridges cover 46% of next year's strikes. Random: 8%", tag: "Check",       src: "2016 to 2025",  color: "powder-blue" },
        { n: "04", title: "Off route",  text: "92% of strikes are on roads that are not truck routes",     tag: "Key finding", src: "My analysis",   color: "dusty-rose", postmark: ["NYC", "2013-25"], key: true },
        { n: "05", title: "Start here", text: "Start with those 10 bridges. Then check signs on the other roads", tag: "Result", src: "For NYC DOT", color: "dusty-rose" }
      ],
      bar: { caption: "Each year, the picks use only earlier years", left: "Past strikes", right: "Next year's strikes" },
      why:   { label: "Why test it?", text: "Picking bridges only helps if past strikes show where the next ones happen. So for each year from 2016 to 2025, I used only the earlier years to pick, then checked that year." },
      catch: { label: "The catch.", text: "The data has no bridge height, cost or traffic counts, so I cannot give rates or money saved. Some reports may be missing. Three bridges changed over time and I do not know why." },
      takeaway: "Most strikes are on roads that are not truck routes, so look at how trucks end up there before building taller bridges."
    },
    links: [
      { label: "Open the interactive analysis", url: "assets/bridge-strikes/index.html" },
      { label: "Code and data", url: "https://github.com/shrutivenkatesh14/Portfolio/tree/main/assets/bridge-strikes" }
    ]
  }
];

/* Multi-part writing, shown on the home page as a taped catalog card. It links
   to the Writing page, where each post offers its platforms, and does not open
   a case file. Add a case to `cases` when
   it is solved, and update `note` for whatever is in progress. */
const SERIES = [
  {
    id: "sql-noir",
    title: "SQL Noir",
    sub: "Detective SQL Stories",
    href: "writing.html",
    cta: "Read the series here",
    featured: true,
    cases: [
      { num: "001", name: "The Vanishing Briefcase" },
      { num: "002", name: "The Stolen Sound" }
    ],
    stamp: "Solved",
    note: "now cracking #003"
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
      { platform: "Medium", url: "https://medium.com/@vshruti193/sql-noir-a-detective-sql-story-case-001-the-vanishing-briefcase-7f0cf78a3b8d" },
      { platform: "Substack", url: "https://substack.com/home/post/p-213179638" }
    ]
  },
  {
    id: "post-2",
    tag: "SQL",
    title: "SQL Noir, Case #002: The Stolen Sound",
    teaser: "A prized record vanishes from a neon-lit 1980s record store, and no two witnesses agree. Someone is lying, and only the data can tell who.",
    date: "Oct 2026",
    links: [
      { platform: "Medium", url: "https://medium.com/@vshruti193/sql-noir-a-detective-sql-story-case-002-the-stolen-sound-ec14c3aa5465" },
      { platform: "Substack", url: "https://vshruti.substack.com/p/sql-noir-a-detective-sql-story-case-c73" }
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
