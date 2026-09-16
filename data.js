/* ==========================================================================
   THE COLLECTION — data
   Edit these arrays to update the site. Nothing else needs to change —
   the project grid, the home page "featured" picks, the case-file overlay,
   and the writing page all render from here.
   ========================================================================== */

const PROJECTS = [
  {
    id: "churn-model",
    denom: "01¢",
    tag: "Data Analysis",
    title: "Customer Churn Model",
    outcome: "Cut projected churn 12% by flagging at-risk accounts 30 days earlier.",
    color: "dusty-rose",
    date: "[Month Year]",
    featured: true,
    problem: "[What was the situation? e.g. \"Subscription cancellations had crept up quarter over quarter and the team had no early-warning system.\"]",
    approach: [
      "[Step, e.g. pulled and cleaned 18 months of usage data]",
      "[Step, e.g. built a logistic regression model in Python]",
      "[Step, e.g. presented findings to the retention team]"
    ],
    result: "[Quantified result, e.g. \"Model flagged at-risk accounts ~30 days earlier, contributing to a 12% drop in projected churn over two quarters.\"]"
  },
  {
    id: "ops-automation",
    denom: "02¢",
    tag: "Process Improvement",
    title: "Ops Reporting Automation",
    outcome: "Replaced a 6-hour manual report with a 10-minute automated build.",
    color: "sage",
    date: "[Month Year]",
    featured: true,
    problem: "[e.g. \"A weekly ops report took one analyst roughly 6 hours to assemble by hand from three systems.\"]",
    approach: [
      "[Mapped the manual process end to end]",
      "[Built an automated pipeline / template]",
      "[Trained the team on the new workflow]"
    ],
    result: "[e.g. \"Report build time dropped from 6 hours to about 10 minutes, freeing up roughly a full day a week.\"]"
  },
  {
    id: "market-entry",
    denom: "03¢",
    tag: "Strategy",
    title: "Market Entry Study",
    outcome: "Sized a new regional market and mapped a 3-phase entry plan.",
    color: "butter-yellow",
    date: "[Month Year]",
    featured: true,
    problem: "[e.g. \"Leadership wanted to know if a new region was worth entering, and how.\"]",
    approach: [
      "[Sized the market using top-down and bottom-up estimates]",
      "[Analysed competitors and regulatory constraints]",
      "[Proposed a phased entry plan]"
    ],
    result: "[e.g. \"Recommendation was adopted; phase one launched within [timeframe].\"]"
  },
  {
    id: "pricing-model",
    denom: "04¢",
    tag: "Financial Modelling",
    title: "Pricing Sensitivity Model",
    outcome: "Built a scenario model that guided a 2-tier pricing change.",
    color: "powder-blue",
    date: "[Month Year]",
    featured: false,
    problem: "[e.g. \"Pricing had not been revisited in [X] years despite rising costs.\"]",
    approach: [
      "[Built a scenario / sensitivity model in Excel]",
      "[Tested elasticity assumptions against historical data]",
      "[Presented a recommended tier structure]"
    ],
    result: "[e.g. \"A 2-tier structure was adopted, with a projected [X]% margin improvement.\"]"
  },
  {
    id: "dashboard",
    denom: "05¢",
    tag: "Data Visualisation",
    title: "Executive KPI Dashboard",
    outcome: "Gave leadership one live view instead of five weekly spreadsheets.",
    color: "lavender",
    date: "[Month Year]",
    featured: false,
    problem: "[e.g. \"Leadership tracked performance across five separate weekly spreadsheets.\"]",
    approach: [
      "[Interviewed stakeholders on what actually mattered]",
      "[Built a live dashboard in Power BI / Tableau]",
      "[Rolled it out with a short training session]"
    ],
    result: "[e.g. \"Replaced five reports with one live view, adopted in weekly leadership meetings.\"]"
  },
  {
    id: "capstone",
    denom: "06¢",
    tag: "Case Competition",
    title: "[Case Competition Name]",
    outcome: "[Placement / result] with a recommendation on [topic].",
    color: "dusty-rose",
    date: "[Month Year]",
    featured: false,
    problem: "[What was the case about?]",
    approach: [
      "[Your specific contribution to the team]",
      "[A method or framework you used]"
    ],
    result: "[Placement, feedback, or what you'd do differently.]"
  }
];

const POSTS = [
  {
    id: "post-1",
    platform: "Substack",
    tag: "Analytics",
    title: "[Article title — e.g. \"What three months of churn data taught me\"]",
    teaser: "[One or two sentences on what the piece is about — enough to make someone want to click through.]",
    date: "[Month Year]",
    url: "https://yourname.substack.com/"
  },
  {
    id: "post-2",
    platform: "Medium",
    tag: "Career",
    title: "[Article title — e.g. \"Why I collect stamps and data, for the same reason\"]",
    teaser: "[One or two sentences on what the piece is about.]",
    date: "[Month Year]",
    url: "https://medium.com/@yourname"
  },
  {
    id: "post-3",
    platform: "Substack",
    tag: "Case Study",
    title: "[Article title]",
    teaser: "[One or two sentences on what the piece is about.]",
    date: "[Month Year]",
    url: "https://yourname.substack.com/"
  }
];
