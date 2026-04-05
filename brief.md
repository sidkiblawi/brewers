# Tailored Marketing Engine: Technical Brief

**Prepared for:** Milwaukee Brewers, Marketing & Analytics  
**Author:** Sid Kiblawi  
**Date:** March 2026  

---

## 1. What This Prototype Does

The prototype is a Streamlit app where a marketer picks an upcoming home game and a fan segment, hits generate, and gets a fully rendered email preview with differentiated copy, a hero image, and a CRM-ready CSV they can upload to Salesforce. It works out of the box with no API key (templated copy), and optionally connects to OpenAI for dynamic generation.

The four segments (Die-Hard Danny, Foodie Frank, Parent Patty, Tailgate Tammy) each get meaningfully different emails for the same game, all targeting Individual ticket sales. The rest of this brief is about how I'd take it from prototype to production.

---

## 2. Where AI Belongs (and Where It Doesn't)

I think the most important thing to get right is the boundary between what the AI touches and what stays deterministic.

**Keep rules-based:**

- **Segmentation.** Fan segments should come from a scoring model built on behavioral data (ticket history, concession spend, app usage, family pack purchases). The rules for who qualifies as a "Die-Hard Danny" need to be transparent and tunable by the analytics team, not buried inside a model.
- **Template structure.** The email skeleton (header, hero, body, CTA, footer with legal) is fixed. Brand guidelines don't change per segment.
- **Game data.** Opponent, date, time, venue, promos. These come straight from the schedule API. AI should never be inventing a game time.
- **Send timing and frequency caps.** When emails go out, how often a fan can be contacted. This is Journey Builder territory.

**Let AI handle:**

- **Copy.** This is where the leverage is. Writing four tonally different emails for 81 home games is hundreds of creative variations. An LLM can shift from stats-heavy (Danny) to sensory/foodie (Frank) to warm/family (Patty) to FOMO/social (Tammy) in seconds. A copywriter doing that manually would burn out by May.
- **CTA language.** "Get Your Tickets" vs. "Rally Your Crew" vs. "Plan Your Family Day." Small differences that matter for conversion, easy for AI to vary, easy to A/B test.
- **Individual-level personalization.** This is where it gets interesting with more data. Right now the system generates 4 versions (one per segment). But the architecture already accepts structured context in the prompt. If we had richer CRM data (purchase history, favorite player, seat preferences, concession patterns), we could feed that per-fan into the same pipeline and generate truly individualized emails. Danny Mueller, who last came to the June Cubs game and always buys terrace seats, gets a different subject line than Danny who came once for a bobblehead. The jump from 4 versions to thousands is an input change, not an architecture change.

My rule of thumb: structure is deterministic, content is AI. A marketer should never wonder if the email will have a CTA button. But what the button says is where AI pulls its weight.

---

## 3. Dealing with Messy Fan Data

Real fan data is going to have gaps. Lots of fans won't have clean behavioral signals. A few things I'd do:

**Score, don't label.** Every fan gets a probability across all four segments, not a hard assignment. Someone might be 60% Die-Hard, 25% Social, 15% Foodie. The CRM uses the top score, but when no segment clears 50%, they get a general-audience version. That's not a failure, it's the baseline.

**Cold-start fans** (new subscribers, no purchase history) default to the general version. After one game, even basic signals (day of week, family pack purchase, which section they sat in) start feeding the model. The system needs to degrade gracefully.

**Use engagement as signal.** Every email we send generates data. A fan who consistently opens Foodie emails but ignores Die-Hard ones is telling us something, even if their purchase data is thin. Feed open/click data back into segment scores on a weekly cycle.

**Ask directly.** A preference center or in-app question ("What do you care about most at the ballpark?") is cheap, high-signal data that supplements the behavioral model.

---

## 4. Marketer Review and Control

AI-generated copy for a professional sports team needs human eyes on it before it goes out. Here's what I'd build:

**Preview before send.** The prototype already does this. The marketer sees the full email for each segment, can read the copy, and decides whether to approve, edit inline, or regenerate. In production, this moves into Salesforce Content Builder or a similar tool.

**Guardrails in the prompts.** Each segment has explicit "avoid" rules baked into the system prompt. The Family segment won't get beer-focused messaging. The Die-Hard segment won't get generic fluff. These are editable by the marketing team without touching code.

**Two-step approval.** For production: (1) automated checks (profanity filter, brand term validation, character count limits), then (2) human sign-off from a marketing manager. Only approved creative enters the send pipeline.

**Manual override.** For high-stakes moments (Opening Day, playoff push, sponsor-integrated campaigns), the marketer can write copy themselves and slot it into the same template and export pipeline. AI should be the default, not the only option.

**Post-send metrics.** Surface per-segment open rate, CTR, and ticket conversion so the team can see what's working and tweak the prompt templates or segment definitions based on actual performance.

---

## 5. Fitting into Adobe and Salesforce

The Brewers likely run Salesforce Marketing Cloud for email and Adobe tools for creative. Here's how this plugs in:

**Salesforce Marketing Cloud:**

- The CSV export maps directly to an SFMC Data Extension. Each row is one fan with their segment, creative version ID, and all the email content fields.
- Journey Builder picks up the Data Extension, matches each fan to their creative version, and sends. Frequency capping, send-time optimization, suppression lists all stay in SFMC where they already live.
- In production, the CSV upload becomes an SFMC REST API call. The system pushes data into the Data Extension on a schedule (3 days before each home game, for example).
- AMPscript in the SFMC email template renders the right subject, body, and image per row. One template, four (or more) content variations.

**Adobe:**

- Image concepts map to a tagged asset library in Adobe Experience Manager or Adobe DAM. A tagging system matches concepts ("tailgate scene," "family in stands") to approved photography.
- Longer-term, Adobe Firefly could take the concept string and generate a hero image within Brewers brand guidelines, with human approval before use.
- If the Brewers run Adobe Campaign alongside SFMC, the same data schema works for both.

The point is that this system doesn't replace what's already there. It feeds the existing stack with better content, faster.

---

## 6. A Failure Case (and How to Fix It)

Here's one that would definitely happen: the AI generates a "Bring the family for a sunny Sunday funday!" email for the Parent Patty segment, but the game is actually a 7:10 PM Tuesday night game in September with playoff implications. The tone completely misreads the context.

Why? The LLM knows the date and time, but it doesn't inherently know that a Tuesday night in September isn't a family outing, or that late-season games carry different weight.

How I'd fix it:

1. **Add derived context flags.** Before the prompt, a rules layer tags the game: `is_weekend: false`, `is_day_game: false`, `is_family_friendly: low`, `season_phase: stretch_run`. Computed from schedule data and standings.

2. **Inject them into the prompt.** "This is a weeknight evening game during the playoff stretch. Adjust accordingly." The LLM adapts based on structured signals instead of guessing.

3. **Score segment-game compatibility.** Some segment/game combos are just bad fits. A Tuesday 7:10 PM game is great for Die-Hard Danny but rough for Parent Patty (school night). Flag low-compatibility pairings and let the marketer skip that segment for that game.

4. **Post-generation check.** A simple rules scan: if `is_day_game` is false but the copy says "sunny" or "afternoon," flag it before it goes out.

Layer those together and you catch most of the obvious mistakes without requiring a human to read every single email.

---

## 7. What I'd Build Next

If this moved to production:

1. **Real fan data.** Connect to the actual CRM (anonymized) and build a proper segmentation model off ticket purchase history, concession data, and app engagement.
2. **SFMC API integration.** Replace the CSV download with a direct Data Extension push.
3. **A/B testing.** Generate 2-3 subject line variants per segment, let SFMC's built-in testing pick the winner.
4. **Feedback loop.** Pipe open/click/conversion data back into segment scores and prompt templates. If Die-Hard emails convert better when they mention pitching matchups vs. standings, encode that.
5. **Image asset library.** The prototype already pulls real Brewers photos from Wikimedia Commons and matches them to segments. In production, this connects to an Adobe DAM with thousands of tagged, approved assets.
6. **1:1 personalization.** With richer customer data, the OpenAI prompt gets enriched per-fan instead of per-segment. A fan who came to 15 games last year and always sits in the terrace gets a different email than someone who came once for a bobblehead. Same pipeline, different inputs.

The end state: a marketer walks in Monday morning, reviews the week's home games, approves or tweaks the AI-generated creative for each segment, and has sends scheduled in SFMC by lunch. Right now that takes a full creative cycle per variation.
