# DHH phrase bank for "google dev - omnigent"

Working notes for Chris. Speaker notes and the summary only, unless a line is marked ✅ below and
picked for a slide.

## Intro

**Tone.** Joy, urgency without fear, a bit irreverent. The DHH energy on Lex Fridman #501 is
excitement about the change, not fear of it. Use it that way: we are inviting people in, not
scolding them, and the demo is supposed to be fun.

**How to use this file.**
- Status is the quote-bank status, carried over unchanged unless a row says otherwise.
  ✅ safe for slides. 🟡 check the audio before a slide. ❌ paraphrase only.
- Timestamps are from the transcript at https://lexfridman.com/dhh-2-transcript/ (the `(hh:mm:ss)`
  markers). Wording was checked against the raw page text on 2026-11-03, not against the audio.
- Riffs in section 4 are Chris's own phrasing, inspired by the episode. They are not DHH's words
  and should never be attributed to him.
- Any product claim in a riff needs a row in `docs/research/facts.md` before it goes on stage.
  Riffs that depend on one are marked `[GAP]`.
- Slide numbers follow the current 22-slide Omnigent deck. N1–N4 are the new receipts, Antigravity,
  routing, and audit slides.

---

## 1. On-slide quotes (≤3, ✅ only)

| # | Quote | Timestamp | Status | Slide | Why it fits Omnigent |
|---|---|---|---|---|---|
| 1 | "At this moment in time, we are all token limited." | 01:01:16 | ✅ | **N3** (Route the work) | The routing story is a budget story: the cheap model for the easy task, the big one for the hard task, and usage you can see. Frank, not fearful. |
| 2 | "The agents are at once both too fast and too slow." | 01:33:15 | ✅ | **12** (Multi-agent team) | Parallel agents are the answer to the wait. One session, several agents running while you do something else. |
| 3 | "Software is product management." | 00:53:16 | ✅ | **20** (Scenario: Auto-Refund) | Auto-Refund is a product question before it is a code question: what it does, for whom, what version one includes. |

Quote 1 alt: "Be as vague as you can to manifest something, then interact with the something." (00:58:13,
✅) for slide 19 Act 1 if the prefix is too thin.

---

## 2. Speaker-note lines (12)

Status is the quote-bank status. Lines marked 🟡 are verbatim against the transcript text and still
need an audio check before going on a slide.

1. **"I'm telling it the problem I have. I'm telling it the fuzzy, vague idea I have."**
   00:11:11, ✅. **Slide 19, Act 1** (Debby debate from a fuzzy prompt).
   *Riff:* "I don't hand the debate a spec. I hand it the fuzzy version of the Auto-Refund problem, and
   the first pass shows me what I actually wanted."

2. **"There are decades where nothing happens and weeks where decades happen."**
   00:03:31 (DHH quoting it; he says "I think it's Lenin"), ✅. **Slide 2** (harness wall).
   *Riff:* "The harness wall is what a few weeks of decades looks like on one slide." Don't attribute
   the line to Lenin on the slide. Say "DHH quotes it."

3. **"Agents love the Unix philosophy."**
   01:40:37, ✅. **Slides 7 and 11** (harnesses as composable CLIs, one layer over many).
   *Riff:* "Omnigent is the Unix idea one layer up. Small harnesses, and one session layer that composes
   them."

4. **"At this moment in time, we are all token limited."**
   01:01:16, ✅. **N3 and N4** (model services, routing, budgets, usage table).
   *Riff:* "Every token is budget. Send the easy work to the cheap model and let the usage table show
   where the tokens went. [GAP: confirm Smart Routing is labelled Beta on N3.]"

5. **"The agents are at once both too fast and too slow."**
   01:33:15, ✅. **Slide 12** and **demo Act 3**.
   *Riff:* "Polly builds in the sandbox while I'm not watching. Close the laptop. That is how you stop
   waiting on one agent." (Label Databricks Sandbox as Beta.)

6. **"Software is product management."**
   00:53:16, ✅. **Slide 20** (Auto-Refund scenario).
   *Riff:* "Auto-Refund is a product problem first: what should it do, for whom, and what goes in
   version one. The agents are good at the rest."

7. **"The modern terminal is just a good-looking place to work."**
   01:34:57, 🟡 (verbatim vs transcript; audio pending). **N1** (Receipts) or a "how this deck was built"
   aside.
   *Riff:* "This deck was built by agents across four harnesses, from a terminal. Terminal first, and
   the terminal still looks good."

8. **"I have had more fun with computers in the last three months than at any time previously."**
   01:31:30, 🟡 (full ending verified vs transcript; audio pending). **Slide 21** (close).
   *Riff:* "Fun is a legitimate reason to do this work. I'm not going to pretend otherwise."

9. **"Are you gonna look at yourself two years from now…"**
   01:30:41, ✅ (prefix only). **Slide 21** (close, before Q&A).
   *Riff:* "Two years from now, will you be proud you leaned in, or will you have spent the time being
   sour about the change?" Use the prefix on stage. The full line is 🟡.

10. **"If you're not recognizing the gravity of the moment, that's the delusion."**
    00:37:54, ✅ (wording confirmed; time confirmed in transcript). **Slide 21**, alternate closer.
    *Riff:* "Not feeling the size of this is the real risk. Being excited about it is the sane
    reaction." Keep the tone light. The source line is about "psychosis" too, so don't lean on it.

11. **"…let your gut drive…"** (full: "…simply let your gut drive, the agentic age is a revelation.")
    00:59:21, ✅ (fragment). **Close.**
    *Riff:* "Take the Auto-Refund debate home and let your gut drive which harness you open first."

12. **"Rust to me is like pouring acid in my eyes when I have to look at the code."**
    00:49:09, ✅ (prefix; full sentence verified). **Optional laugh line, not in the deck.**
    *Risk:* Rust is widely used inside Google, so this line could land badly in a Google room. Skip
    unless Chris wants it. [GAP: Chris decision on tone.]

---

## 3. Omnigent and Databricks riffs (Chris's own words, not DHH's)

Original phrasing, DHH-flavoured. Do not attribute to DHH. Product claims are flagged.

1. The harness will change. The session shouldn't have to.
2. Harness lock-in is a bet on this year's CLI. Put the session one layer up and the bet gets cheaper.
3. Guardrails the agent can't talk its way around. Not a system prompt that asks nicely.
   `[GAP: slide 13 contextual policies (ALLOW/ASK/DENY) need a facts.md row first.]`
4. Execution-level control on top, request-level governance underneath. Two layers, one trail.
   `[GAP: needs facts rows for the Omnigent policy layer and the usage table, if quoted.]`
5. One credential for every harness. `[GAP: per-harness effect of org-managed settings is OPEN in
   facts.md. Do not say "every harness" until it is verified.]`
6. Chat makes you sit and wait. A terminal with several agents in it doesn't.
7. Shared context means nobody on the team builds their own gas town.
8. The demo is supposed to be fun, and so is the work.

---

## 4. Opener options (under 60 seconds spoken)

**A. The decades line.** (~45 s)
"There are decades where nothing happens and weeks where decades happen. DHH quoted that on a podcast,
and the pace is the point. [GAP: one concrete moment from your own last few weeks. Keep it
small and specific.] Here's the weird part: the harnesses that made those weeks possible don't talk to
each other. So for the next twenty minutes I'm going to show you one layer that sits above all of
them."

**B. Show of hands.** (~50 s)
"Quick show of hands. Who has more than one coding agent open right now? Keep your hand up if one of
them is making you wait. That's the thing. The agents are at once too fast and too slow, and the
answer is not a fourteenth harness. It's an open layer above the 13+ we already have." (Slide 11 count; re-check against the deck.)

**C. The fuzzy idea.** (~40 s)
"I'm going to tell you the fuzzy, vague idea I have. Nobody needs a spec for this talk. One layer above
every coding agent, one session that different harnesses can share, and governance that the agent
can't talk its way around. Then I'm going to try it live, and we'll see what I actually wanted."

---

## 5. Closer options (under 60 seconds spoken)

**A. The regret question, then Chris's last line.** (~50 s)
"Two years from now. Are you gonna look at yourself and think, 'I spent my time being pissy about the
present'? Or will you be proud you leaned in? Here's the thing: the harness will change. The session
doesn't have to. So go take the thing you built this week and put it in the shared layer. Shake off the
AI psychosis and just have fun."

**B. Let your gut drive.** (~35 s)
"Software is product management, and the product here is your next hour. Let your gut drive. The
agentic age is a revelation if you let it be one. Thanks."

**C. The fun close, after the audio check.** (~40 s)
"I've had more fun with computers in the last three months than at any time previously. I'm not going
to apologise for that. [If the audio check passes, use the 🟡 line here.] Go open the demo, pick a
harness, and have fun with it. Thanks."

**Note.** "Pickling cool cucumbers" is not used in any option. See Gaps.

---

## Facts to add

Rows for the three ✅ on-slide quotes, in `docs/research/facts.md` row format. Do not add these to
facts.md until Chris has approved the slide placement.

| Claim | Quote / detail | URL | Status |
|---|---|---|---|
| DHH on token limits (talk N3 quote, ~01:01:16) | "At this moment in time, we are all token limited." | https://lexfridman.com/dhh-2-transcript/ (01:01:16) | verified (transcript text, 2026-11-03); audio check OPEN |
| DHH on fast and slow agents (talk slide 12, ~01:33:15) | "The agents are at once both too fast and too slow." | https://lexfridman.com/dhh-2-transcript/ (01:33:15) | verified (transcript text, 2026-11-03); audio check OPEN |
| DHH on product management (talk slide 20, ~00:53:16) | "Software is product management." | https://lexfridman.com/dhh-2-transcript/ (00:53:16) | verified (transcript text, 2026-11-03); audio check OPEN |

---

## Gaps

- **"Pickling cool cucumbers"** `[GAP: ask Chris what this refers to]`. Not used anywhere in this file.
- **Lenin attribution.** DHH says "I think it's Lenin" (00:03:31). Don't attribute the decades line to
  Lenin on a slide; say "DHH quotes it." `[GAP: Chris to confirm wording.]`
- **🟡 quotes need audio.** Terminal (01:34:57), "more fun" (01:31:30), and the full "two years from
  now" line (01:30:41) are verbatim in the transcript text, but not checked against the audio. They
  stay 🟡.
- **"Shrunk by 80%" claim (🟡, 00:56:14).** The wording is verbatim. The claim is secondhand (DHH relays
  it about a specific model's system prompt), and it names models that may not be in the talk. Keep it out
  of the deck. If it is ever used, it must be attributed as DHH's account.
- **"Agents love the Unix philosophy."** Verified verbatim at 01:40:37, ✅. Don't confuse it with the
  similar "agents love Linux" at 03:38:48, which is Lex Fridman's line, not DHH's.
- **"Be as vague…" (✅ prefix).** The full sentence is verified. The ✅ status covers the prefix only.
- **Rust line.** Optional. Tone risk for a Google audience. `[GAP: Chris decision]`.
- **Riff claims.** Riffs 3, 4 and 5 in section 3 each depend on a product claim that needs a facts row,
  and riff 5 depends on an OPEN item in facts.md.
- **Demo-act wording.** Act 1, Act 3 and the Polly/Sandbox references need the demo runbook to confirm
  the wording and the Beta labels. `[GAP: confirm against the demo runbook.]`

## Open threads

- Audio check for the three 🟡 quotes (terminal, more fun, two years).
- Whether the closer is A (regret question) or C (fun close). Chris to pick.
- Whether slide 2's "decades" line should be on the slide or only in notes. It is ✅, but it is
  Lenin-attributed and not DHH's own words.
- Final N1–N4 wording, so the N3 and N4 quotes match the slides once they land.
- Confirm the facts.md rows above before any on-slide use.
