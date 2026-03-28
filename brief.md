# Tailored Marketing Engine — Technical Brief

**Prepared for:** Milwaukee Brewers, Marketing & Analytics  
**Author:** Sid Kiblawi  
**Date:** March 2026  

---

## 1. What This Prototype Demonstrates

This prototype shows an end-to-end workflow: a marketer selects an upcoming home game and a fan segment, the system generates differentiated email creative (subject line, body copy, CTA, and image direction), previews it in a realistic email template, and exports a CRM-ready CSV that maps the right fans to the right creative version.

It works today with zero API keys (templated mode) and can optionally call OpenAI for dynamic copy generation. The four segments — Die-Hard Danny, Foodie Frank, Parent Patty, and Tailgate Tammy — each receive meaningfully different messaging for the same game, all focused on Individual ticket sales.

The rest of this brief outlines how I'd build the production version.

---

## 2. AI-Driven vs. Rule-Based — Where Each Belongs

The most important architectural decision is knowing where AI adds value and where deterministic rules are safer.

**Rule-based (deterministic):**

- **Segment assignment.** Fan segmentation should be driven by a scoring model based on behavioral data (ticket purchase history, concession spend, app usage, family pack purchases, social media engagement). These scores update nightly via a batch job. The rules for "who is a Die-Hard Danny" should be transparent, auditable, and tunable by the analytics team — not a black box.
- **Template structure.** The email layout (header, hero image area, body, CTA button, footer with legal/unsubscribe) is fixed. Brand guidelines, logo placement, and compliance elements don't change per segment.
- **Game context injection.** Opponent name, date, time, venue, and promo-night details come from the schedule API and are injected deterministically. AI should never hallucinate a game time.
- **Send timing and frequency caps.** Business rules determine when emails send (e.g., 3 days before game day, no more than 2 emails per fan per week). These belong in Salesforce Journey Builder, not in an AI model.
- **CRM field mapping.** The export schema (which columns, which Data Extension) is fixed infrastructure.

**AI-driven (generative):**

- **Email copy.** Subject lines, headlines, and body copy are the highest-value AI application. An LLM can adapt tone (stats-heavy for Danny, sensory for Frank, warm for Patty, FOMO for Tammy) in ways that would take a human copywriter hours to do across four segments for 81 home games.
- **Image concept direction.** AI generates a one-sentence creative brief for the hero image (e.g., "dramatic low-angle pitching shot under lights"). In production, this feeds into an asset-selection system that matches against an approved image library — or, longer-term, into Adobe Firefly for generative image creation within brand guidelines.
- **CTA language.** Small variations in button text ("Get Your Tickets" vs. "Rally Your Crew") can be AI-generated and A/B tested automatically.
- **Personalization at the individual level.** Beyond segment-level copy, AI can further customize: "Danny — Burnes vs. the Cubs under the lights" using the fan's first name and their favorite player (if we have that data).

The principle: **structure is rules, content is AI.** A marketer should never wonder *whether* the email will have a CTA button. But *what* the CTA says is where AI earns its keep.

---

## 3. Handling Imperfect or Limited Fan Data

Real fan data will be messy. Many fans won't have clear behavioral signals. Here's how I'd handle it:

**Score, don't classify.** Every fan gets a probability score across all four segments, not a hard label. A fan might be 60% Die-Hard, 25% Social, 15% Foodie. The CRM export uses the top segment, but the score is visible — and low-confidence fans (no segment above 50%) get a "general" creative version that's a safe, broad appeal.

**Cold-start fans (new email subscribers, no purchase history):** Default to a general creative version. After their first game, even minimal data (which game they bought, day of week, whether they bought a family pack) starts building a signal. The system should be designed to degrade gracefully — general creative is not a failure, it's the baseline.

**Progressively enrich.** Each email send generates engagement data (opens, clicks, conversions). A fan who consistently opens Foodie Frank emails but ignores Die-Hard Danny emails is providing implicit segment signal, even if their purchase data is sparse. This feedback loop should update segment scores weekly.

**Explicit preference capture.** The Brewers app or a preference center can ask fans directly: "What matters most to you at the ballpark?" This is cheap, high-signal data that supplements behavioral modeling.

---

## 4. Marketer Review and Control

AI-generated content in a professional sports context requires human oversight. Here's the control framework:

**Pre-send review.** The Streamlit interface (or its production equivalent in Salesforce Content Builder) shows the marketer a full preview of each segment's email before any send is triggered. They can edit copy inline, swap image concepts, or reject and regenerate.

**Prompt guardrails.** Each segment's system prompt includes explicit `avoid` rules (e.g., the Family segment avoids beer-focused messaging; the Die-Hard segment avoids generic hype). These are configurable by the marketing team without touching code.

**Approval workflow.** In production, generated creative would enter a two-step approval: (1) automated checks (profanity filter, brand term validation, character limits) and (2) human approval by a marketing manager. Only approved creative flows into the send pipeline.

**Override and lock.** For high-stakes sends (Opening Day, playoff push, sponsor-integrated campaigns), the marketer can bypass AI entirely and manually author copy that gets slotted into the same template/export pipeline. The system should make AI the default, not the only option.

**Performance dashboard.** Post-send, the system surfaces per-segment metrics (open rate, CTR, ticket conversion) so the marketer can see which AI-generated angles are working and adjust segment definitions or prompt templates accordingly.

---

## 5. Integration into Adobe and Salesforce

The Brewers' existing stack likely includes Salesforce Marketing Cloud (SFMC) for email orchestration and Adobe tools for creative production. Here's how this system fits:

**Salesforce Marketing Cloud:**

- The CSV export from this prototype maps directly to an **SFMC Data Extension**. Each row is a fan record with their assigned segment, creative version ID, and all email content fields.
- **Journey Builder** consumes this Data Extension to trigger sends. The journey logic is simple: fan enters → match `creative_version_id` → send the corresponding email. Frequency capping, send-time optimization, and suppression lists all live in SFMC as they do today.
- In a production build, the CSV upload would be replaced by an **SFMC REST API integration** — the system pushes data directly into the Data Extension via API, triggered on a schedule (e.g., 3 days before each home game).
- **AMPscript** in the SFMC email template dynamically renders the right subject line, body, and image URL per row. One email template, four (or more) content variations.

**Adobe (Creative Cloud / Experience Platform):**

- **Asset management:** The image concepts generated by AI map to an approved asset library managed in Adobe Experience Manager (AEM) or Adobe DAM. A tagging system matches concepts ("tailgate scene," "family in stands") to pre-approved photography.
- **Adobe Firefly (longer-term):** For generative image creation within brand guidelines, Firefly's API could take the image concept string and produce a hero image that uses Brewers brand colors, fonts, and style — with human approval before use.
- **Adobe Campaign (if used alongside SFMC):** The same Data Extension schema can feed Adobe Campaign's delivery engine if the Brewers run campaigns across both platforms.

The key insight: **this system doesn't replace the existing stack — it feeds it.** The AI layer generates content; the existing tools handle delivery, compliance, and measurement.

---

## 6. Failure Case: Tone-Deaf Game Context

**The failure:** AI generates a chipper "Bring the family for a sunny Sunday funday!" email for a Parent Patty segment — but the game is actually a 7:10 PM Tuesday night game in September with playoff implications. The tone is wrong for the context.

**Why it happens:** The LLM has access to the game date and time, but it doesn't inherently understand that a Tuesday night game isn't a family-friendly outing, or that September games carry different weight than April games.

**How I'd fix it:**

1. **Structured context injection.** Before the LLM prompt, a rule-based layer annotates the game with derived context flags: `is_weekend: false`, `is_day_game: false`, `is_family_friendly: low`, `season_phase: stretch_run`, `series_significance: high`. These flags are computed deterministically from the schedule data and standings API.

2. **Prompt conditioning.** The system prompt includes these flags explicitly: "This is a weeknight evening game during the playoff stretch. Adjust tone accordingly — this is not a casual outing." The LLM adapts its output based on structured signals, not vibes.

3. **Segment-game compatibility scoring.** Some segment × game combinations are weak fits. A Tuesday 7:10 PM game is a great fit for Die-Hard Danny (meaningful game) but a poor fit for Parent Patty (school night). The system could flag low-compatibility pairings and suggest the marketer skip that segment for that game, or auto-select the best 2-3 segments per game instead of always running all four.

4. **Post-generation validation.** A lightweight rules check scans the generated copy for mismatches: if `is_day_game: false` but the copy mentions "sunny" or "afternoon," flag it for review. This catches the most obvious errors without requiring a human to read every email.

This layered approach — structured context → prompt conditioning → compatibility scoring → post-generation validation — makes the system progressively more robust without over-engineering any single layer.

---

## 7. What I'd Build Next

If this moved from prototype to production, the immediate next steps would be:

1. **Connect to the Brewers' actual fan database** (anonymized CRM export) and build a real segmentation scoring model based on ticket purchase history, concession data, and app engagement.
2. **SFMC API integration** — replace CSV download with direct Data Extension push.
3. **A/B testing framework** — for each segment, generate 2-3 subject line variants and let SFMC's built-in A/B testing pick the winner automatically.
4. **Feedback loop** — pipe open/click/conversion data back into the segment scoring model and the prompt templates. If Die-Hard Danny emails get higher CTR when they mention pitching matchups vs. standings, encode that learning.
5. **Image asset matching** — the prototype already demonstrates this: real Brewers photography from Wikimedia Commons (American Family Field, Sausage Race, fireworks nights, etc.) is automatically matched to each segment and embedded as the hero image. In production, this would connect to an Adobe DAM-tagged library with thousands of approved assets.

The goal is a system where a marketer can walk in on Monday morning, review the week's upcoming home games, approve (or tweak) the AI-generated creative for each segment, and have the sends scheduled in SFMC by lunch — a workflow that currently takes a full creative cycle for each variation.
