# Market & Audience Research: Cozy Bear Rescue Physics Puzzle (iOS)

**Date:** 2026-10-28  
**Question:** Does this game have a realistic chance on the App Store?  
**Concept tested:** Tilt (or touch-rotate) a small glass world. Stranded bears tumble and pile up, and you use their bodies to bridge gaps, balance platforms and reach a cozy home. Rescued bears move into a home you decorate, and each has a personality.

**Evidence quality:** Sensor Tower's primary reports could not be fetched (`sensortower.com` is blocked by this session's network policy), so market figures come from secondary write-ups of Sensor Tower data. Treat them as directional. Sales figures for comparable games are developer-reported via press. Psychology findings come from peer-reviewed papers, with sample sizes noted.

---

## 1. Verdict

**The concept is sound, but the odds are poor and depend on distribution, not on the idea.**

- **What the evidence supports:** the design aligns with well-established motivation psychology (§3). The closest comparable mechanic, World of Goo, sold well on iOS (§4). Puzzle is a large, growing revenue genre, and iPhone users account for most mobile spending (§2).
- **What it doesn't support:** every successful comparable had a **distribution event** that the concept alone doesn't give you. Examples: an Apple feature, a famous PC version first, streamers going viral, an established studio. Meanwhile, App Store supply is exploding while downloads are flat. The base rate for indie games is very low revenue (§5).
- **What desk research cannot answer:** whether *this* game is fun and whether people share it. That takes a prototype and a cheap audience test (§7). Desk research is not a substitute for either.

---

## 2. Market

| Fact | Figure | Implication |
|---|---|---|
| Mobile game IAP revenue, 2025 | ~$82B (+1%) ([Sensor Tower via press](https://sensortower.com/press/press-release-sensor-tower-state-of-gaming-gaming-drove-52-billion-downloads-82b-iap-revenue-on-mobile-and-12b-premium-revenue-on-steam)) | The market is big but flat. Growth comes from taking share. |
| Puzzle genre, H1 2026 | $8.1B IAP, ~+20% YoY, #2 genre. Downloads across genres fell ~12% ([GameDev Reports summary](https://gamedevreports.substack.com/p/sensor-tower-the-gaming-market-in)) | Revenue is growing while installs shrink. Spend is **concentrating in existing hits** that monetise heavily, not flowing to newcomers. |
| iOS share of app spending, 2025 (all apps) | iOS $117.6B vs Google Play $49.2B, about 70/30 ([Business of Apps via search summary](https://quashbugs.com/blog/app-store-statistics)) | iOS-first is the right call for a paid or premium game. |
| New app supply | iOS new-app releases +84% YoY in Q1 2026. Downloads grew only ~2–3% ([AppleWorld.Today](https://appleworld.today/2026/07/the-number-of-new-apps-released-in-the-app-store-grew-30-to-about-600000-last-year/), [MacStories](https://macstories.net/linked/app-store-chaos/)) | **Discoverability is getting worse.** AI-assisted development is flooding the store, and that includes us. Being "made with AI" is not an advantage. |
| Apple Arcade | Apple's 2026 Arcade lineup is led by cozy titles ([iDropNews](https://www.idropnews.com/news/new-apple-arcade-games-2026/257766/)). Arcade has historically offered upfront funding by invitation ([9to5Mac, 2019](https://9to5mac.com/2019/05/13/apple-arcade-developer-pitch/)) | This is a real alternative to the open market. Current terms and exclusivity are unverified. |

---

## 3. Audience and psychology

### Who plays cozy and puzzle games
- **Cozy players skew female (about 60%) and are aged 25–44** (Quantic Foundry, as reported by Euronews; directional). They mainly play to relax and pass time ([Bryter](https://www.bryter-global.com/blog/the-rise-of-cozy-gaming), [IndexBox](https://www.indexbox.io/blog/cozy-games-market-surpasses-855-million-why-slow-gentle-gaming-is-booming-in-2026/)). The exact percentages vary between vendors.
- **Design consequence:** the audience plays to *reduce* stress. Physics randomness, fail states and fiddly tilt directly fight that motive. This turns my earlier "deterministic physics plus rewind" point from a nice-to-have into a requirement for the audience.

### Why the concept should be motivating (and the limits of that)

| Theory / finding | Evidence strength | How the concept maps |
|---|---|---|
| **Self-determination theory:** games pull players to the extent they satisfy *competence, autonomy, relatedness*, and each independently predicts enjoyment and future play ([Ryan, Rigby & Przybylski 2006](https://www.rochester.edu/warner/lida/wp-content/uploads/2022/11/02bfe513dd59366750000000.pdf)) | Strong. Four studies, foundational and widely replicated in game research | Competence comes from solving physics puzzles. Autonomy comes from **emergent physics, which allows multiple solutions**. That's a genuine advantage over fixed-solution puzzles, but only if solutions are reliable. Relatedness comes from bear personalities and reunions. **All three needs are covered**, which most indie concepts don't manage. |
| **Baby schema:** large heads, big eyes and round faces raise perceived cuteness *and caretaking motivation* ([Glocker et al. 2009, Ethology](https://pmc.ncbi.nlm.nih.gov/articles/PMC3260535/), n=122) | Moderate to strong, an established ethology finding | The "rescue" framing taps caretaking motivation. **Art direction should follow baby-schema proportions deliberately**, not just "cute". |
| **Kawaii effect:** viewing cute images improved fine-motor accuracy (+43.9% vs +11.9%) and narrowed focus ([Nittono et al. 2012, PLOS ONE](https://journals.plos.org/plosone/article%3Fid=10.1371/journal.pone.0046362), n=132 across 3 experiments) | Weak to moderate. Small student samples, and I found no independent replication | Suggestive fit with precision physics puzzles. Don't build strategy on it. |

**Limit:** psychology explains why cute plus competence plus collecting is engaging. It is a **necessary condition, not evidence of sales**. Hundreds of cute puzzle games satisfy it and earn nothing.

### Tilt controls
- Lab studies found players *preferred* tilt for suitable games ([MacKenzie, York University](https://www.yorku.ca/mack/nordichi2012.html)). Player forums complain that tilt is imprecise and forces a fixed viewing angle ([TouchArcade thread](https://toucharcade.com/community/threads/reminders-to-devs.8675/)). Accessibility guidance says to always offer an alternative input.
- I found **no data on lying-down or bed play**. My earlier concern about cozy players in bed remains a reasoned hypothesis, not a finding. The fix is the same either way: touch must be a full equal, not a fallback.

---

## 4. Comparable games: what actually happened

| Game | Relevance | Outcome | Why it worked (and the catch) |
|---|---|---|---|
| **World of Goo** (2D Boy) | **Closest mechanic.** Creatures are the building material, and you rescue them to an exit | 125K iPad sales in the first month and 1M App Store downloads in about 13 months, at $2.99–$4.99 ([PocketGamer.biz](https://www.pocketgamer.biz/2d-boys-world-of-goo-does-million-downloads-on-apple-hardware), [MacStories](https://www.macstories.net/news/world-of-goo-sells-125k-in-first-month-2d-boy-talks-sales-strategies-and-consoles/)) | It was **already famous** from PC and Wii (an award-winning indie) and **Apple featured it prominently**. That makes it proof the mechanic sells, not proof a newcomer can launch it. |
| **Cut the Rope** (ZeptoLab) | Physics puzzle plus a cute character | 1M sales in 10 days (2010). Franchise passed 500M downloads by 2014 ([PocketGamer](https://www.pocketgamer.co.uk/articles/024267/r/), [TNW](https://www.thenextweb.com/news/cut-rope-2-arrives-android-franchise-downloads-hit-500-million)) | It launched in a 2010 App Store with a small fraction of today's competition, with a publisher (Chillingo). The era can't be repeated. |
| **Monument Valley 1 & 2** (ustwo) | Premium iOS puzzle with an art-first approach | MV1: $5.86M from 2.44M sales, **81.7% from iOS** ([MacRumors](https://macrumors.com/2015/01/15/monument-valley-ios-sales)). MV2: $10.4M in its first year on a ~$2.26M dev cost ([PocketGamer.biz](https://www.pocketgamer.biz/premium-isnt-dead-yet-monument-valley-2-makes-over-10-million-in-first-year)) | Proves **premium iOS puzzles can earn well**, but only at exceptional art quality, from an established design studio. |
| **Suika Game** (Aladdin X) | Physics piling in a container, cute fruit | **2,351 units in its first 636 days**, then streamers found it and it reached 8M+ (Switch plus 1.3M mobile) ([Perfectly Nintendo](https://www.perfectly-nintendo.com/?p=594946), [GoNintendo](https://www.gonintendo.com/contents/28411-suika-game-hits-3-66-million-units-sold)) | **The most important data point:** the same game was a near-total failure for almost two years until it went viral. Physics piling is highly *watchable*. Success was a distribution event. |
| **A Little to the Left** (Max Inferno) | Cozy puzzle | 500K sales in ~6 months, **396M TikTok views** ([Pocket Tactics](https://www.pockettactics.com/a-little-to-the-left/dlc)) | Short-form video drove it. Satisfying, cozy moments are shareable. |
| **Neko Atsume** (Hit-Point) | Collect cute animals, low effort, care for them | 10M downloads by Dec 2015. The series later passed 30M ([Wikipedia](https://en.wikipedia.org/wiki/Neko_Atsume), [Meta](https://www.meta.com/blog/neko-atsume-interview/)) | Validates hooks #2 and #3 (collecting and caring) as a standalone draw. Revenue figures are unreliable. |

**Direct competition.** Generic "rescue the cute animal" puzzles already exist, mostly hyper-casual pin-pull clones, and so do tilt-to-guide games (e.g. [Rescue Master!](https://mwm.ai/apps/rescue-master/1552177719), [Save The Fairies](https://apps.apple.com/us/app/-/id6670489408)). **The theme is not a differentiator.** The differentiator has to be the bears-as-physical-tools mechanic, plus art and character quality.

**Survivorship bias.** Every game in this table is a winner. I found no systematic data on the many similar games that failed, and the base-rate data in §5 says they are the majority.

---

## 5. Base rates and economics

- **Typical outcomes are poor.** On Steam, where data is most transparent, median lifetime indie revenue is estimated at roughly $5K–15K gross ([Steam Page Analyzer](https://www.steampageanalyzer.com/blog/indie-game-revenue-data)). For mobile I found **no credible systematic survey**. The circulating figures ("60% earn under $1K/month") have no verifiable source, so I'm not using them.
- **Retention benchmarks** (GameAnalytics medians, all genres): D1 about 22%, D7 about 4%, D30 under 1%. Top-quartile iOS D1 is 31–33% ([GameDev Reports summary](https://gamedevreports.substack.com/p/gameanalytics-mobile-gaming-benchmarks)). Puzzle runs higher, roughly D1 32%, D7 12%, D30 5% (Mistplay data via [Segwise](https://segwise.ai/blog/mobile-gaming-app-user-retention-strategies.md); secondary).
- **Paid acquisition:** US iOS cost per install for games is roughly **$1.50–$4.00** depending on source ([Liftoff via Statista](https://www.statista.com/statistics/1241651/global-cpi-casual-gaming-apps-genre-platform), [FoxData](https://foxdata.com/en/blogs/2026-mobile-game-user-acquisition-cost-benchmarks-how-much-should-you-spend/)). The break-even rule is simple: **revenue per install must exceed CPI**. Free-to-play puzzle games reach that through deep live-ops monetisation run by large teams. A solo, cozy, non-aggressive game is unlikely to beat a $2–4 CPI. That's my judgment, not measured data.
- **Platform fee:** 15% under Apple's Small Business Program (under $1M/yr), otherwise 30%.

**What follows:** paid user acquisition is not a viable primary channel for this project. Realistic channels are **(1) organic short-form video, (2) Apple editorial featuring, (3) Apple Arcade.** All three reward the same thing: a visually distinctive, highly watchable, polished game.

---

## 6. Strategic implications for the design

1. **Optimise for watchability, not only playability.** Bears tumbling into a pile is inherently clip-able, as Suika and A Little to the Left showed. Build in moments worth recording: big pile-ups, a satisfying settle, the reunion animation, and a one-tap "save replay" share button.
2. **Fairness is non-negotiable for this audience.** Use deterministic physics, tolerant level design, and rewind instead of fail screens.
3. **Business model:** premium or "free first chapter, then one-time unlock" rather than free-to-play with live ops. Monument Valley proves premium works on iOS when quality is high, and it avoids a CPI fight you can't win. Prices are untested hypotheses.
4. **Art is where the money gets made or lost.** Baby-schema proportions and character quality drive hooks #3 and watchability. Budget accordingly, and only *after* validation.
5. **An Asia angle is worth testing** (hypothesis). Japan dominated Suika's early sales (2.77M of 3.0M by Oct 2023), and cute-animal collecting games come from Japanese studios. Japanese and Korean localisation may be worth more than more Western marketing. That's unverified for this concept.

---

## 7. Recommendation: cheap validation with kill criteria, before any art spend

| Step | What | Cost | Pass if | Kill or rethink if |
|---|---|---|---|---|
| 1 | **Web prototype** (3 puzzles, placeholder bears, tilt + touch + rewind), playable in iPhone Safari | My time plus a few hours of yours | 5–10 testers, ideally including cozy-game players aged 25–44, solve levels by reasoning and **ask for more levels unprompted** | Testers describe solutions as luck, or stop after 1–2 levels |
| 2 | **Short-form video test:** 5–10 clips of bear pile-ups and reunions on TikTok, Reels and Shorts | ~$0, a few hours | Comments asking "what game is this" or "where can I download", and saves and shares above your account's baseline | No organic pull after 10 clips. The watchability thesis fails |
| 3 | Only then: **commission art** for the vertical slice, plus an Apple Arcade pitch and a TestFlight beta | Art budget TBD | – | – |

The kill thresholds are deliberately qualitative. With only a handful of testers, any numeric pass mark would be false precision.
