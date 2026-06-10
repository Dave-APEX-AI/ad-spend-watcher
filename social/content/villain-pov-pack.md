# Villain POV pack — "I'm your missed call" (Prompts 2 & 3 output)

Idea #2 from `pattern-breakers.md`, developed into hooks + 3 faceless executions.
Audience: UK/Irish trades owners. Tone: dark-cheeky, plain-spoken, trade-native.

## 15 hooks (Prompt 2)

**Curiosity**
1. Your most profitable employee? You've never met him. Neither have your customers.
2. There's something on your phone stealing from you every day. It isn't an app.
3. A plumber in Cork found out where his missing jobs went. He didn't like the answer.

**Contrarian**
4. You don't need more leads. You're already throwing away the ones you've got.
5. Your competitor isn't better than you. He's just awake when his phone rings.
6. Stop buying ads. You can't even answer the calls you're getting now.

**Emotional tension**
7. She rang you first. You'll never know that.
8. 11 missed calls this week. That's a holiday I funded — for the plumber down the road.
9. You did 11 hours on the tools today. Then your phone quietly cost you £680.

**Specificity**
10. 9 calls a week. £280 a job. 30% would've booked. Do the maths — I'll wait.
11. 9:42pm, burst pipe, EK16. She rang 3 plumbers. Job went to the one who answered in 2 rings.
12. Last Tuesday, 4:15pm: your phone rang for 23 seconds. That was a £1,200 rewire.

**Subtle authority**
13. We listened to 1,000 calls to trade businesses. 40% rang out. Here's what that costs.
14. Every trade we audit thinks they miss 2 calls a week. The real number is 9.
15. The busiest firms in your trade share one boring habit: the phone never rings twice.

**Top 5:** #8, #7, #11, #5, #14.

## 3 faceless executions (Prompt 3)

### A — Carousel "Confessions of a missed call" (8 slides)
S1 hook #8 (amber) → S2 "Hi. I'm your missed call. We've never spoken. That's the point."
→ S3 Mon 8:04am boiler quote (you were driving) → S4 Wed 1pm ring-round (first to answer won)
→ S5 Fri 9:42pm burst pipe £680 (you were asleep) → S6 "I don't leave voicemails. I move on."
→ S7 "I fear one thing: someone who always picks up." (green dot) → S8 audit CTA + save.
Visuals: ink bg, villain lines amber, hero turn emerald, buzzing face-down phone motif.
Caption: hook #8 → "Every missed call is a customer ringing your competitor next." → audit CTA.

### B — Text-only reel (12s)
6 hard-cut caption cards w/ phone-buzz SFX: "I'm your missed call." / "You've never heard me.
That's the point." / "This week I took: boiler quote… emergency call-out… rewire." /
"≈ £1,400. Gone." / "I only fear one thing." / green soundwave: "The receptionist that never
sleeps. CaillteAI." Caption: hook #7. Pinned comment: reply CAILLTE.

### C — Silent visual static
Realistic phone "Missed call (3)" notification mock, amber annotations pricing each
(£680 burst pipe / £240 service / ring-round gone). Footer: "Don't let leads go *caillte*."
Caption: hook #12 → "Your phone keeps the receipts. We just add the prices." → audit CTA.

## Production routing
- A → `caillte-carousel` spec → publish queue (Office Heroes episode).
- B → CapCut text cards (or Phase-2 `caillte-ugc-video`).
- C → `caillte-static-post` (Holo brief) or carousel template single slide.
