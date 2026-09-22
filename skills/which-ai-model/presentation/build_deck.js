// Builds the "Which AI Model Should You Use?" deck in the House of Ichigo brand.
//   node build_deck.js
// Output: which-ai-model-explained.pptx
const pptxgen = require("pptxgenjs");
const path = require("node:path");

// ── House of Ichigo 3.2 tokens ──────────────────────────────
const INK    = "0A0E27";
const COBALT = "1231D6";
const COBALT_LIGHT = "7FA0FF";   // accent word on Ink only
const SLATE  = "5A6478";
const LINE   = "E3E8EF";
const WHITE  = "FFFFFF";
// White blended over Ink — the brand's "white at 55-70%" on a dark ground,
// as solid hex so no renderer has to composite it.
const ON_INK_70 = "B5B6BC";   // subtitles on Ink
const ON_INK_58 = "989AA4";   // footers and fine print on Ink
const D = "Manrope";        // display + headings
const S = "Inter Tight";    // body, never above 20px
const M = "JetBrains Mono"; // eyebrows, labels, all numerals

const DATE = "2026-09-22";

// Slide geometry — brand margins: 72px side, 56 top, 72 foot on 1280x720
const W = 13.333, H = 7.5;
const ML = 0.75, MR = 0.75, MT = 0.58, MB = 0.75;
const CW = W - ML - MR;

const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "House of Ichigo";
p.company = "House of Ichigo";
p.title = "Which AI Model Should You Use?";

// ── helpers ─────────────────────────────────────────────────
function eyebrow(s, text, opts = {}) {
  s.addText(text.toUpperCase(), {
    isTextBox: true, x: ML, y: opts.y || MT, w: CW, h: 0.26,
    fontFace: M, fontSize: 10, charSpacing: 2,
    color: opts.color || COBALT, margin: 0, valign: "top",
  });
}

// Title with one Cobalt accent word (brand: exactly one per display heading)
function title(s, parts, opts = {}) {
  const onInk = opts.onInk;
  const runs = parts.map((t) =>
    typeof t === "string"
      ? { text: t, options: { color: onInk ? WHITE : INK, bold: false } }
      : { text: t.a, options: { color: onInk ? COBALT_LIGHT : COBALT, bold: true } }
  );
  s.addText(runs, {
    isTextBox: true, x: ML, y: opts.y || MT + 0.34, w: opts.w || CW, h: opts.h || 0.95,
    fontFace: D, fontSize: opts.size || 34, charSpacing: -0.6,
    lineSpacing: opts.lineSpacing || 40, margin: 0, valign: "top",
  });
}

function rule(s, y, opts = {}) {
  s.addShape(p.ShapeType.rect, {
    x: opts.x !== undefined ? opts.x : ML, y,
    w: opts.w || CW, h: opts.weight || 0.022,
    fill: { color: opts.color || INK }, line: { type: "none" },
  });
}

function foot(s, n, label) {
  s.addText(`House of Ichigo · ${label}`, {
    isTextBox: true, x: ML, y: H - MB + 0.16, w: CW - 0.6, h: 0.24,
    fontFace: M, fontSize: 9, charSpacing: 1.2, color: SLATE, margin: 0,
  });
  s.addText(String(n), {
    isTextBox: true, x: W - MR - 0.8, y: H - MB + 0.16, w: 0.8, h: 0.24,
    fontFace: M, fontSize: 9, color: SLATE, align: "right", margin: 0,
  });
}

function inkSlide() {
  const s = p.addSlide();
  s.background = { color: INK };
  return s;
}

let n = 0;
const LABEL = "Learn AI · model selection";

// ════════════════════════════════════════════════════════════
// 01 · COVER
// ════════════════════════════════════════════════════════════
{
  const s = inkSlide();
  s.addText("AI CAPABILITY · DECISION GUIDE", {
    isTextBox: true, x: ML, y: 1.5, w: CW, h: 0.3,
    fontFace: M, fontSize: 11, charSpacing: 2.4, color: COBALT_LIGHT, margin: 0,
  });
  s.addText([
    { text: "Which AI should you ", options: { color: WHITE } },
    { text: "actually", options: { color: COBALT_LIGHT, bold: true } },
    { text: " use?", options: { color: WHITE } },
  ], {
    isTextBox: true, x: ML, y: 2.0, w: 10.6, h: 2.0,
    fontFace: D, fontSize: 54, charSpacing: -1.4, lineSpacing: 62, margin: 0, valign: "top",
  });
  s.addText("Choosing the product, the mode and the model — in that order.", {
    isTextBox: true, x: ML, y: 4.15, w: 9.6, h: 0.5,
    fontFace: S, fontSize: 17, color: ON_INK_70, margin: 0,
  });
  s.addText(`Snapshot ${DATE} · verify current model names before use`, {
    isTextBox: true, x: ML, y: H - MB + 0.1, w: CW, h: 0.3,
    fontFace: M, fontSize: 9.5, charSpacing: 1.2, color: ON_INK_58, margin: 0,
  });
  s.addNotes("Frame: this deck teaches a durable decision process, not a list of model names. Any list of names is stale within weeks.");
  n++;
}

// ════════════════════════════════════════════════════════════
// 02 · AGENDA
// ════════════════════════════════════════════════════════════
{
  const s = p.addSlide();
  eyebrow(s, "Agenda");
  title(s, ["What this ", { a: "covers" }]);
  rule(s, MT + 1.42);

  const items = [
    ["01", "Why “which model is best?” is the wrong question"],
    ["02", "The four layers — task, capability, product, model"],
    ["03", "Seven questions that decide it"],
    ["04", "Three practical rungs and why price gaps vary"],
    ["05", "What people get wrong, and how to test properly"],
  ];
  let y = MT + 1.75;
  items.forEach(([num, text]) => {
    s.addText(num, { isTextBox: true, x: ML, y, w: 0.6, h: 0.42,
      fontFace: M, fontSize: 15, color: COBALT, margin: 0, valign: "middle" });
    s.addText(text, { isTextBox: true, x: ML + 0.75, y, w: CW - 0.75, h: 0.42,
      fontFace: S, fontSize: 16, color: INK, margin: 0, valign: "middle" });
    y += 0.52;
    rule(s, y - 0.06, { weight: 0.008, color: LINE });
  });
  foot(s, ++n, LABEL);
}

// ════════════════════════════════════════════════════════════
// 03 · THE WRONG QUESTION
// ════════════════════════════════════════════════════════════
{
  const s = p.addSlide();
  eyebrow(s, "The premise");
  title(s, ["The strongest model is often the ", { a: "wrong" }, " one"], { h: 1.1 });
  rule(s, MT + 1.5);

  const cols = [
    ["Product", "Where the work happens", "A chat window, a research mode, a coding agent, an automated pipeline."],
    ["Model", "How capable the engine is", "Fast, balanced or frontier. The part everyone argues about."],
    ["Tool", "What the system can actually do", "Search the web, open your files, run code, edit a repository."],
  ];
  const cw = (CW - 1.0) / 3;
  cols.forEach(([h1, h2, body], i) => {
    const x = ML + i * (cw + 0.5);
    s.addText(h1, { isTextBox: true, x, y: MT + 1.85, w: cw, h: 0.4,
      fontFace: D, fontSize: 22, bold: true, color: INK, charSpacing: -0.3, margin: 0 });
    s.addText(h2, { isTextBox: true, x, y: MT + 2.26, w: cw, h: 0.3,
      fontFace: M, fontSize: 9.5, charSpacing: 1.4, color: SLATE, margin: 0 });
    s.addText(body, { isTextBox: true, x, y: MT + 2.62, w: cw, h: 1.2,
      fontFace: S, fontSize: 14, color: INK, lineSpacing: 20, margin: 0, valign: "top" });
  });

  s.addShape(p.ShapeType.rect, { x: ML, y: MT + 4.15, w: 0.035, h: 0.85,
    fill: { color: COBALT }, line: { type: "none" } });
  s.addText("A weaker model inside the right product beats a stronger model in the wrong one.", {
    isTextBox: true, x: ML + 0.28, y: MT + 4.15, w: CW - 0.28, h: 0.85,
    fontFace: D, fontSize: 19, color: INK, charSpacing: -0.3, lineSpacing: 26, margin: 0, valign: "middle" });

  s.addNotes("The classic failure: someone buys the most expensive subscription and still cannot do the task, because the task needed a connector or a file tool, not more intelligence.");
  foot(s, ++n, LABEL);
}

// ════════════════════════════════════════════════════════════
// 04 · FOUR LAYERS
// ════════════════════════════════════════════════════════════
{
  const s = p.addSlide();
  eyebrow(s, "The route");
  title(s, ["Four layers. Pick the model ", { a: "last" }]);
  rule(s, MT + 1.42);

  const steps = [
    ["01", "Task", "What is the output, and who reads it?"],
    ["02", "Capability", "Search, long documents, vision, code execution."],
    ["03", "Product & tools", "Chat, research mode, coding agent, pipeline."],
    ["04", "Model tier", "Only now. And rarely the frontier."],
  ];
  const cw = (CW - 1.2) / 4;
  steps.forEach(([num, t, d], i) => {
    const x = ML + i * (cw + 0.4);
    if (i > 0) {
      s.addShape(p.ShapeType.rect, { x: x - 0.2, y: MT + 1.75, w: 0.008, h: 2.1,
        fill: { color: LINE }, line: { type: "none" } });
    }
    s.addText(num, { isTextBox: true, x, y: MT + 1.75, w: cw, h: 0.28,
      fontFace: M, fontSize: 10, charSpacing: 1.6, color: SLATE, margin: 0 });
    s.addText(t, { isTextBox: true, x, y: MT + 2.08, w: cw, h: 0.45,
      fontFace: D, fontSize: 21, bold: true, color: i === 3 ? COBALT : INK, charSpacing: -0.3, margin: 0 });
    s.addText(d, { isTextBox: true, x, y: MT + 2.6, w: cw, h: 1.2,
      fontFace: S, fontSize: 13.5, color: INK, lineSpacing: 19, margin: 0, valign: "top" });
  });

  rule(s, MT + 4.25, { weight: 0.008, color: LINE });
  s.addText("Each layer removes candidates. By the time you reach the model, most of the decision is already made.", {
    isTextBox: true, x: ML, y: MT + 4.45, w: CW, h: 0.5,
    fontFace: S, fontSize: 14.5, color: SLATE, margin: 0 });
  foot(s, ++n, LABEL);
}

// ════════════════════════════════════════════════════════════
// 05 · DIVIDER
// ════════════════════════════════════════════════════════════
{
  const s = inkSlide();
  s.addText("THE METHOD", { isTextBox: true, x: ML, y: 3.0, w: CW, h: 0.3,
    fontFace: M, fontSize: 11, charSpacing: 2.4, color: COBALT_LIGHT, margin: 0 });
  s.addText("Seven questions", { isTextBox: true, x: ML, y: 3.4, w: CW, h: 1.0,
    fontFace: D, fontSize: 44, color: WHITE, charSpacing: -1.2, margin: 0 });
  s.addText("Stop at the first one that decides it.", {
    isTextBox: true, x: ML, y: 4.45, w: CW, h: 0.4,
    fontFace: S, fontSize: 16, color: ON_INK_70, margin: 0 });
  n++;
}

// ════════════════════════════════════════════════════════════
// 06 · QUESTIONS 1–4
// ════════════════════════════════════════════════════════════
function questionSlide(sub, rows, noteText) {
  const s = p.addSlide();
  eyebrow(s, "The seven questions");
  title(s, [sub.a, { a: sub.b }, sub.c || ""]);
  rule(s, MT + 1.42);

  let y = MT + 1.72;
  rows.forEach(([num, q, ans, hard]) => {
    s.addText(num, { isTextBox: true, x: ML, y, w: 0.55, h: 0.35,
      fontFace: M, fontSize: 15, color: COBALT, margin: 0, valign: "top" });
    s.addText(q, { isTextBox: true, x: ML + 0.7, y: y - 0.04, w: 5.0, h: 0.75,
      fontFace: D, fontSize: 16, bold: true, color: INK, charSpacing: -0.2, lineSpacing: 21, margin: 0, valign: "top" });
    if (hard) {
      s.addShape(p.ShapeType.rect, { x: ML + 5.78, y: y - 0.02, w: 0.03, h: 0.78,
        fill: { color: COBALT }, line: { type: "none" } });
    }
    s.addText(ans, { isTextBox: true, x: ML + 6.0, y: y - 0.04,
      w: CW - 6.0, h: 0.8,
      fontFace: S, fontSize: 13.5, color: INK, lineSpacing: 19, margin: 0, valign: "top" });
    y += 1.02;
    if (num !== rows[rows.length - 1][0]) rule(s, y - 0.16, { weight: 0.008, color: LINE });
  });
  if (noteText) s.addNotes(noteText);
  foot(s, ++n, LABEL);
}

questionSlide(
  { a: "First, what the task ", b: "requires" },
  [
    ["01", "Does the answer depend on information that can change?",
     "Yes → live search is mandatory, and citations if anyone checks the claims. A model without search answers confidently and wrongly.", true],
    ["02", "Is the work tied to a particular environment?",
     "Drive, SharePoint, a repository, a database. Whatever reaches the data wins — integration outweighs a modest quality difference.", false],
    ["03", "How many files, and how long?",
     "A few: attach them. One very long one: long-document handling. Dozens: file search. Thousands: an indexing project, not a chat.", false],
    ["04", "What is in the input besides text?",
     "Charts, scans, audio, video. Check this before comparing intelligence — a smarter model that cannot see the chart is useless.", false],
  ],
  "Questions 1 and 2 settle most real cases before model quality is ever discussed."
);

// ════════════════════════════════════════════════════════════
// 07 · QUESTIONS 5–7
// ════════════════════════════════════════════════════════════
questionSlide(
  { a: "Then, what you are ", b: "optimising for" },
  [
    ["05", "How hard is the thinking, honestly?",
     "Routine work on the flagship wastes money. Client-facing work on the cheap tier costs more the first time someone has to fix it.", false],
    ["06", "Which constraint actually binds — quality, speed or cost?",
     "One usually dominates. Name it, optimise for it, and say plainly what was traded away.", false],
    ["07", "Is the data sensitive or regulated?",
     "A hard gate, not a preference. Use what the organisation has approved, even when it is the weaker tool.", true],
  ],
  "Question 7 overrides everything above it. Getting this wrong is worse than using a slightly weaker model."
);

// ════════════════════════════════════════════════════════════
// 08 · THE THREE RUNGS
// ════════════════════════════════════════════════════════════
{
  const s = p.addSlide();
  eyebrow(s, "Tier translation");
  title(s, ["Three practical ", { a: "rungs" }, ", without fixed price bands"]);
  rule(s, MT + 1.42);

  const rows = [
    [{ text: "RUNG", options: { fontFace: M, fontSize: 9.5, charSpacing: 1.4, color: SLATE, bold: false } },
     { text: "WHAT IT IS FOR", options: { fontFace: M, fontSize: 9.5, charSpacing: 1.4, color: SLATE } },
     { text: "COST TENDENCY", options: { fontFace: M, fontSize: 9.5, charSpacing: 1.4, color: SLATE, align: "right" } }],
    [{ text: "Fast / light", options: { fontFace: D, fontSize: 16, bold: true, color: INK } },
     { text: "High volume and repetitive: classification, extraction, short summaries, quick answers.", options: { fontFace: S, fontSize: 13.5, color: INK } },
     { text: "LOWEST", options: { fontFace: M, fontSize: 12, color: COBALT, align: "right" } }],
    [{ text: "Balanced", options: { fontFace: D, fontSize: 16, bold: true, color: INK } },
     { text: "Most real work: drafting, analysis, everyday coding, document work. The working default.", options: { fontFace: S, fontSize: 13.5, color: INK } },
     { text: "HIGHER", options: { fontFace: M, fontSize: 12, color: COBALT, align: "right" } }],
    [{ text: "Frontier", options: { fontFace: D, fontSize: 16, bold: true, color: INK } },
     { text: "Hard reasoning, architecture, long autonomous runs, anything expensive to get wrong.", options: { fontFace: S, fontSize: 13.5, color: INK } },
     { text: "HIGHEST", options: { fontFace: M, fontSize: 12, color: COBALT, align: "right" } }],
  ];
  s.addTable(rows, {
    x: ML, y: MT + 1.72, w: CW, colW: [2.5, 7.33, 2.0],
    rowH: [0.34, 0.72, 0.72, 0.72], valign: "middle",
    border: [{ type: "none" }, { type: "none" },
             { type: "solid", color: LINE, pt: 0.75 }, { type: "none" }],
    margin: [4, 10, 4, 0], autoPage: false,
  });
  rule(s, MT + 2.06, { weight: 0.012 });

  s.addText("Provider price gaps vary too much for one multiplier. Verify current pricing, then measure cost per successful task. In consumer apps, use the thinking control: fast, think harder, maximum.", {
    isTextBox: true, x: ML, y: MT + 4.5, w: CW, h: 0.6,
    fontFace: S, fontSize: 14, color: SLATE, lineSpacing: 19, margin: 0 });

  s.addNotes("The ladder is durable. The names and price gaps change every few weeks — look them up before quoting them.");
  foot(s, ++n, LABEL);
}

// ════════════════════════════════════════════════════════════
// 09 · WHO CALLS IT WHAT (dated)
// ════════════════════════════════════════════════════════════
{
  const s = p.addSlide();
  eyebrow(s, `Snapshot · ${DATE}`);
  title(s, ["What each provider calls them ", { a: "today" }]);
  rule(s, MT + 1.42);

  const hdr = (t, align) => ({ text: t, options: { fontFace: M, fontSize: 9.5, charSpacing: 1.4, color: SLATE, align } });
  const cell = (t) => ({ text: t, options: { fontFace: S, fontSize: 13.5, color: INK } });
  const rung = (t) => ({ text: t, options: { fontFace: D, fontSize: 15, bold: true, color: INK } });

  s.addTable([
    [hdr("RUNG"), hdr("OPENAI"), hdr("ANTHROPIC"), hdr("GOOGLE")],
    [rung("Fast"), cell("GPT-5.6 Luna"), cell("Claude Haiku 4.5"), cell("Gemini 3.5 Flash-Lite")],
    [rung("Balanced"), cell("GPT-5.6 Terra"), cell("Claude Sonnet 5"), cell("Gemini 3.8 Flash")],
    [rung("Frontier"), cell("GPT-5.6 Sol · GPT-6 Astra"), cell("Claude Opus 5 · Fable 5.1"), cell("Gemini 3.1 Pro · Deep Think")],
  ], {
    x: ML, y: MT + 1.72, w: CW, colW: [2.2, 3.2, 3.2, 3.23],
    rowH: [0.34, 0.6, 0.6, 0.6], valign: "middle",
    border: [{ type: "none" }, { type: "none" },
             { type: "solid", color: LINE, pt: 0.75 }, { type: "none" }],
    margin: [4, 10, 4, 0], autoPage: false,
  });
  rule(s, MT + 2.06, { weight: 0.012 });

  s.addShape(p.ShapeType.rect, { x: ML, y: MT + 4.2, w: 0.035, h: 0.82,
    fill: { color: COBALT }, line: { type: "none" } });
  s.addText("This table is the part of the deck that goes stale. It was accurate on " + DATE + " and should be checked against each provider's own documentation before it is shown again.", {
    isTextBox: true, x: ML + 0.28, y: MT + 4.2, w: CW - 0.28, h: 0.82,
    fontFace: S, fontSize: 14, color: INK, lineSpacing: 20, margin: 0, valign: "middle" });

  s.addNotes("Deliberately placed late in the deck and marked as perishable. Everything before it stays true; this slide will not.");
  foot(s, ++n, LABEL);
}

// ════════════════════════════════════════════════════════════
// 10 · RULES OF THUMB
// ════════════════════════════════════════════════════════════
{
  const s = p.addSlide();
  eyebrow(s, "What people get wrong");
  title(s, ["Six rules of ", { a: "thumb" }]);
  rule(s, MT + 1.42);

  const rules = [
    ["Cost per successful task, not per token", "A cheap model that retries twice and needs a human fix is the expensive one."],
    ["“Analyse this PDF” is not one task", "A summary, one exact fact, a table and a judgement route to four different setups."],
    ["A big context window is not comprehension", "Fitting the text in is not the same as reasoning well over all of it."],
    ["“Write code” is four different jobs", "One function, a bug hunt, a repo-wide refactor and an architecture review differ."],
    ["Benchmarks shortlist, they do not decide", "Run three real examples through two candidates. Ten minutes beats a leaderboard."],
    ["Do not switch provider for a few points", "Connectors, ecosystem fit and the subscription already paid for matter more."],
  ];
  const cw = (CW - 0.7) / 2;
  rules.forEach(([t, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = ML + col * (cw + 0.7);
    const y = MT + 1.75 + row * 1.2;
    s.addText(t, { isTextBox: true, x, y, w: cw, h: 0.4,
      fontFace: D, fontSize: 15.5, bold: true, color: INK, charSpacing: -0.2, lineSpacing: 20, margin: 0, valign: "top" });
    s.addText(d, { isTextBox: true, x, y: y + 0.42, w: cw, h: 0.52,
      fontFace: S, fontSize: 13, color: SLATE, lineSpacing: 18, margin: 0, valign: "top" });
    if (row < 2) rule(s, y + 1.02, { x, w: cw, weight: 0.008, color: LINE });
  });
  foot(s, ++n, LABEL);
}

// ════════════════════════════════════════════════════════════
// 11 · THE TEST
// ════════════════════════════════════════════════════════════
{
  const s = p.addSlide();
  eyebrow(s, "How to decide");
  title(s, ["The test that beats every ", { a: "leaderboard" }]);
  rule(s, MT + 1.42);

  const steps = [
    ["01", "Take three real examples", "Not a toy prompt. Three tasks from actual work, with the same files and constraints."],
    ["02", "Run them through two candidates", "Shortlisted from the decision tree — not from a ranking table."],
    ["03", "Judge blind, then pin the winner", "Fix the setup, fix the output format, and re-test when something changes."],
  ];
  const cw = (CW - 1.0) / 3;
  steps.forEach(([num, t, d], i) => {
    const x = ML + i * (cw + 0.5);
    s.addText(num, { isTextBox: true, x, y: MT + 1.85, w: cw, h: 0.3,
      fontFace: M, fontSize: 11, charSpacing: 1.6, color: COBALT, margin: 0 });
    s.addText(t, { isTextBox: true, x, y: MT + 2.2, w: cw, h: 0.7,
      fontFace: D, fontSize: 19, bold: true, color: INK, charSpacing: -0.3, lineSpacing: 24, margin: 0, valign: "top" });
    s.addText(d, { isTextBox: true, x, y: MT + 2.98, w: cw, h: 1.3,
      fontFace: S, fontSize: 13.5, color: INK, lineSpacing: 19, margin: 0, valign: "top" });
  });

  rule(s, MT + 4.4, { weight: 0.008, color: LINE });
  s.addText("Ten minutes of this reflects your own house style, your own data and your own quality bar. No published benchmark does.", {
    isTextBox: true, x: ML, y: MT + 4.6, w: CW, h: 0.5,
    fontFace: S, fontSize: 14.5, color: SLATE, margin: 0 });
  foot(s, ++n, LABEL);
}

// ════════════════════════════════════════════════════════════
// 12 · CONVICTION
// ════════════════════════════════════════════════════════════
{
  const s = inkSlide();
  s.addText([
    { text: "The strongest model is ", options: { color: WHITE } },
    { text: "rarely", options: { color: COBALT_LIGHT, bold: true } },
    { text: " the right one.", options: { color: WHITE } },
  ], {
    isTextBox: true, x: ML, y: 2.8, w: 12.0, h: 1.6,
    fontFace: D, fontSize: 40, charSpacing: -1.0, lineSpacing: 50, margin: 0, valign: "middle" });
  s.addText("Route by what the task requires, not by what scores highest.", {
    isTextBox: true, x: ML, y: 4.4, w: 10.0, h: 0.4,
    fontFace: S, fontSize: 16, color: ON_INK_70, margin: 0 });
  n++;
}

// ════════════════════════════════════════════════════════════
// 13 · CLOSE
// ════════════════════════════════════════════════════════════
{
  const s = inkSlide();
  s.addText("NEXT STEP", { isTextBox: true, x: ML, y: 2.5, w: CW, h: 0.3,
    fontFace: M, fontSize: 11, charSpacing: 2.4, color: COBALT_LIGHT, margin: 0 });
  s.addText([
    { text: "Install the skill. Ask it ", options: { color: WHITE } },
    { text: "your", options: { color: COBALT_LIGHT, bold: true } },
    { text: " question.", options: { color: WHITE } },
  ], {
    isTextBox: true, x: ML, y: 2.95, w: 11.0, h: 1.2,
    fontFace: D, fontSize: 36, charSpacing: -0.9, lineSpacing: 44, margin: 0 });
  s.addText("The which-ai-model skill runs this decision tree for you and verifies current model names by live search — so the answer is never read from a stale table.", {
    isTextBox: true, x: ML, y: 4.2, w: 9.8, h: 0.9,
    fontFace: S, fontSize: 15, color: ON_INK_70, lineSpacing: 22, margin: 0 });
  s.addText("github.com/houseofichigo/skill-resources/tree/main/skills/which-ai-model", {
    isTextBox: true, x: ML, y: 5.25, w: CW, h: 0.35,
    fontFace: M, fontSize: 13, color: COBALT_LIGHT, margin: 0 });
  s.addText("House of Ichigo · Equipped to run", {
    isTextBox: true, x: ML, y: H - MB + 0.16, w: CW, h: 0.3,
    fontFace: M, fontSize: 9.5, charSpacing: 1.2, color: ON_INK_58, margin: 0 });
  n++;
}

p.writeFile({ fileName: path.join(__dirname, "which-ai-model-explained.pptx") })
  .then((f) => console.log("Wrote", f, "·", n, "slides"));
