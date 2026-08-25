"use strict";

// Self-contained, deterministic content moderation for The Dispatch Markets.
//
// The terminal's AI surfaces (Dispatch Expert chat, the committee, lens theses)
// accept free-form user text and emit model-generated text. This module lets the
// site auto-moderate itself: it screens user submissions before they reach the AI
// provider and screens model output before it is returned, with no external
// dependency or human in the loop.
//
// Design constraints specific to this product:
//   * It is a markets terminal, so ordinary trading jargon must NOT be flagged.
//     Words like "kill", "crash", "dump", "bomb", "bloodbath", "slaughter",
//     "nuke", "blow up", "murder" are routine market talk. Detectors therefore
//     require an explicit human target or an unambiguous harmful construction
//     rather than firing on a single ambiguous keyword.
//   * Detection is conservative and explainable: every hit maps to a category and
//     a matched span, so decisions can be logged and audited.

// Curated set of unambiguous slurs / hate terms. Kept intentionally small and
// targeted; matched on word boundaries to avoid substring false positives
// (e.g. inside tickers or ordinary words).
const HATE_TERMS = [
  "nigger", "nigga", "faggot", "fag", "kike", "spic", "chink", "gook",
  "wetback", "coon", "tranny", "retard", "retarded", "raghead", "beaner",
  "sandnigger", "paki",
];

function boundaryPattern(terms) {
  const escaped = terms.map(term => term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  return new RegExp(`\\b(?:${escaped.join("|")})\\b`, "i");
}

const HATE_PATTERN = boundaryPattern(HATE_TERMS);

// Each rule: { category, severity, pattern, label }.
// severity "block" always blocks; it is used for both input and output.
const RULES = [
  {
    category: "hate",
    severity: "block",
    label: "hateful slur or dehumanizing language",
    pattern: HATE_PATTERN,
  },
  // Sexual content involving minors — always blocked, input or output.
  {
    category: "sexual_minors",
    severity: "block",
    label: "sexual content involving minors",
    pattern: /\b(child|children|minor|minors|underage|pre[- ]?teen|preteen|kid|kids|infant|toddler|(?:\d|1[0-7])\s*(?:yo|y\/o|years? old))\b[^.?!]{0,40}\b(sex|sexual|porn|nude|nudes|naked|explicit|molest|rape)\b/i,
  },
  {
    category: "sexual_minors",
    severity: "block",
    label: "sexual content involving minors",
    pattern: /\b(sex|sexual|porn|nude|nudes|naked|explicit|molest)\b[^.?!]{0,40}\b(child|children|minor|minors|underage|pre[- ]?teen|preteen|toddler|infant)\b/i,
  },
  // Direct threats or incitement of violence against a person/group. Requires a
  // human target so market phrases ("this stock will kill it") do not match.
  {
    category: "harassment_threat",
    severity: "block",
    label: "threat or incitement of violence against a person",
    pattern: /\b(kill|murder|shoot|stab|behead|lynch|rape|assault|hang|strangle|slaughter)\s+(you|u|him|her|them|themselves|yourself|yourselves|people|everyone|somebody|someone|that\s+guy|that\s+woman|that\s+man|these\s+people|those\s+people|my\s+\w+|your\s+\w+|his\s+\w+|her\s+\w+)\b/i,
  },
  {
    category: "harassment_threat",
    severity: "block",
    label: "encouragement of suicide directed at another person",
    pattern: /\b(kys|kill\s*yo?urself|kill\s*ur\s*self|go\s+(and\s+)?(die|kill\s+yourself)|neck\s+yourself|hang\s+yourself)\b/i,
  },
  {
    category: "harassment_threat",
    severity: "block",
    label: "wishing death or serious harm on a person",
    pattern: /\bi\s+(will|'ll|am\s+going\s+to|gonna|want\s+to|wanna)\s+(kill|murder|shoot|stab|hurt|rape|beat|bomb)\s+(you|u|him|her|them|yourself)\b/i,
  },
  // First-person self-harm / suicidal intent — flagged so the surface can respond
  // safely rather than continue as a market chat.
  {
    category: "self_harm",
    severity: "block",
    label: "self-harm or suicidal intent",
    pattern: /\b(i|i'?m|im)\s+(want|wanna|going|gonna|plan|planning|about)\s*(to|na)?\s*(kill\s+myself|end\s+(my\s+life|it\s+all)|commit\s+suicide|hurt\s+myself|harm\s+myself)\b/i,
  },
  {
    category: "self_harm",
    severity: "block",
    label: "self-harm or suicidal intent",
    pattern: /\b(kill\s+myself|end\s+my\s+life|commit\s+suicide|take\s+my\s+own\s+life)\b/i,
  },
  // Requests for instructions to build weapons or manufacture illegal drugs.
  // Requires an action verb + weapon/drug object to avoid flagging market talk
  // about defense stocks, "this news is a bomb", etc.
  {
    category: "illicit_instructions",
    severity: "block",
    label: "instructions for weapons or illegal drug manufacture",
    pattern: /\b(how\s+(to|do\s+i)|build|make|manufacture|synthesi[sz]e|create|construct|assemble)\b[^.?!]{0,40}\b(bomb|explosive|explosives|ied|pipe\s?bomb|nerve\s+agent|sarin|meth(amphetamine)?|fentanyl|nuclear\s+(weapon|bomb)|dirty\s+bomb|bioweapon|biological\s+weapon|ghost\s+gun)\b/i,
  },
  // Prompt-injection / jailbreak attempts against the assistant.
  {
    category: "prompt_injection",
    severity: "block",
    label: "prompt injection or jailbreak attempt",
    pattern: /\b(ignore|disregard|forget|override)\b[^.?!]{0,40}\b(previous|prior|above|earlier|all|your)\b[^.?!]{0,20}\b(instruction|instructions|prompt|prompts|rules|guardrails|directive|directives)\b/i,
  },
  {
    category: "prompt_injection",
    severity: "block",
    label: "prompt injection or jailbreak attempt",
    pattern: /\b(system\s+prompt|developer\s+prompt|reveal\s+your\s+(system\s+)?prompt|you\s+are\s+now\s+\w+|do\s+anything\s+now|dan\s+mode|jailbreak|act\s+as\s+(an?\s+)?(unfiltered|uncensored))\b/i,
  },
];

const CATEGORY_MESSAGES = {
  hate: "This request was blocked because it contains hateful or dehumanizing language.",
  sexual_minors: "This request was blocked because it involves sexual content concerning minors.",
  harassment_threat: "This request was blocked because it threatens or targets a person with violence.",
  self_harm: "It sounds like you may be going through something serious. This assistant can't help with self-harm. If you're in immediate danger, please contact your local emergency services or a crisis line such as 988 (US) or Samaritans on 116 123 (UK).",
  illicit_instructions: "This request was blocked because it asks for instructions to create weapons or illegal drugs.",
  prompt_injection: "This request was blocked because it attempts to override the assistant's safety instructions.",
};

const DEFAULT_BLOCK_MESSAGE = "This request was blocked by The Dispatch content policy.";

// Categories that should suppress AI OUTPUT if the model ever emits them. Kept to
// unambiguous, high-harm categories so legitimate market commentary is never
// discarded (e.g. we do not suppress output for "prompt_injection").
const OUTPUT_BLOCK_CATEGORIES = new Set([
  "hate",
  "sexual_minors",
  "harassment_threat",
  "self_harm",
  "illicit_instructions",
]);

const SAFE_OUTPUT_REPLACEMENT =
  "This response was withheld by The Dispatch content policy. Please rephrase your request and try again.";

function normalize(value) {
  return String(value == null ? "" : value)
    // Collapse whitespace so multi-word patterns match across newlines/tabs.
    .replace(/\s+/g, " ")
    .trim();
}

// Evaluate text against every rule. Returns { flagged, categories, matches }.
function evaluate(text, { categories } = {}) {
  const haystack = normalize(text);
  const matches = [];
  if (haystack) {
    for (const rule of RULES) {
      if (categories && !categories.has(rule.category)) continue;
      const match = rule.pattern.exec(haystack);
      if (match) {
        matches.push({ category: rule.category, label: rule.label, match: match[0] });
      }
    }
  }
  const uniqueCategories = [...new Set(matches.map(m => m.category))];
  return { flagged: matches.length > 0, categories: uniqueCategories, matches };
}

function messageForCategories(categories) {
  for (const category of categories) {
    if (CATEGORY_MESSAGES[category]) return CATEGORY_MESSAGES[category];
  }
  return DEFAULT_BLOCK_MESSAGE;
}

// Moderate an inbound user submission. `text` may be a string or an array of
// strings (e.g. chat turns); arrays are joined before evaluation.
function moderateInput(text) {
  const combined = Array.isArray(text) ? text.map(normalize).join("\n") : text;
  const result = evaluate(combined);
  return {
    allowed: !result.flagged,
    categories: result.categories,
    matches: result.matches,
    message: result.flagged ? messageForCategories(result.categories) : null,
  };
}

// Moderate model OUTPUT. Only high-harm categories cause suppression so ordinary
// market analysis (which may mention crashes, wipeouts, etc.) is preserved.
function moderateOutput(text) {
  const result = evaluate(text, { categories: OUTPUT_BLOCK_CATEGORIES });
  const blocked = result.flagged;
  return {
    allowed: !blocked,
    categories: result.categories,
    matches: result.matches,
    text: blocked ? SAFE_OUTPUT_REPLACEMENT : String(text == null ? "" : text),
    safeReplacement: SAFE_OUTPUT_REPLACEMENT,
  };
}

module.exports = {
  moderateInput,
  moderateOutput,
  evaluate,
  RULES,
  OUTPUT_BLOCK_CATEGORIES,
  SAFE_OUTPUT_REPLACEMENT,
};
