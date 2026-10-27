# Feasibility: Gravity-Physics Teddy Bear Lock Screen Wallpaper for iPhone

**Date:** 2026-10-27  
**Status:** Investigation complete. **Phase 3 (proof of concept) was deliberately not built**: the brief says not to build a substitute and present it as the goal. A product-direction decision is needed (see §9–10).

---

## 1. Executive verdict

| Question | Verdict |
|---|---|
| Real, gravity-driven physics running **on the native iPhone Lock Screen**, with the system clock and notifications (Category A) | **NO.** There is no public API for it. |
| Doing it with private APIs or a jailbreak | Out of scope by your rules, and it violates App Review Guideline 2.5.1. |
| Delivering a *related* product legitimately on iPhone (Categories B, C or D) | **YES.** But each one is a materially different product (§2, §9). |
| Delivering the exact reference experience on **Android** | **YES.** Android has a public live-wallpaper API (`WallpaperService`). |

**Confidence: high.** This verdict rests on a documented *absence* plus documented constraints, not on a lack of effort. In Apple's architecture, Lock Screen wallpapers are rendered by Apple's own "poster" extensions (the private `PosterKit` framework), and no public extension point lets a third party run code there. Apple can change this at any WWDC. As of iOS 27.x it has not.

---

## 2. Reference video: what it actually shows

Source: `IMG_1194.mov`, 11.6 s, 1920×1080, 29.97 fps, stored rotated 180°. I reviewed 12 frames at 1 fps plus 2 frames at higher resolution.

**Directly observed:**
- **Device correction:** this is a **Galaxy Z Flip** (clamshell). It is *not* a Z Fold. The effect runs on the small square **cover screen (FlexWindow)**, next to the two outer cameras. This changes requirement 8: the closest analogue is a cover/outer display, not a large inner foldable screen.
- The display is the real Samsung lock screen. It shows a lock icon, a Samsung dual "Local / Home" roaming clock (01:38 PM / 03:38 PM, Tue Oct 27), and a Samsung **"Now brief"** card, which is a One UI system element.
- The objects are about 15 3D emoji-style items: bears, puppies, and a few hearts. They are **not only teddy bears**.
- Objects pile up along whichever edge is "down". They pile bottom-left while the phone is held rotated, and fall to the bottom when it is upright. They rotate individually and overlap each other.
- In at least one frame, a puppy is drawn *over* the clock digits ("01:38").

**Inferred, not confirmed:**
- The objects drawing over the system clock suggests a **first-party Samsung feature** (One UI FlexWindow emoji/interactive wallpapers), not a third-party live wallpaper. Android lets third parties render the wallpaper layer, which normally sits *beneath* the clock. Samsung's own Flip7 material mentions "interactive elements" and animated emoji wallpapers on FlexWindow ([Samsung Design](https://www.design.samsung.com/global/contents/flexwindow-wallpaper)). I found no Samsung source that specifically describes tilt physics.
- Bounce, collision response and shake behaviour cannot be measured reliably from 1 fps frames of a hand-held recording. They look physically plausible, but I am not claiming specific parameters.

---

## 3. What can and cannot run on the real iPhone Lock Screen

| Capability | On the native Lock Screen? | Category | Evidence |
|---|---|---|---|
| Third-party code rendering the wallpaper continuously | **No** | A | No public wallpaper/poster extension point. Apple's wallpapers run as private `PosterKit` extensions (e.g. `MercuryPosterExtension`, seen in a public crash log) ([forum thread](https://developer.apple.com/forums/thread/805625)). Apple's own wallpaper instructions are user-only (Photos → Share → Use as Wallpaper) ([WWDC26 wallpaper page](https://developer.apple.com/wwdc26/wallpaper/)). |
| Apps setting the wallpaper programmatically | **No** | – | No public API. The user must apply the wallpaper manually in Settings or Photos. |
| Core Motion while the app is not in the foreground | **No, for this use** | A | `CMMotionManager` delivers data to a running app ([docs](https://developer.apple.com/documentation/coremotion/cmmotionmanager)). Suspended apps get no callbacks, and no background mode covers "render a wallpaper" (Guideline 2.5.4 limits background modes to their intended purposes). |
| Lock Screen widgets (WidgetKit) | Yes, but static | – | Timeline snapshots. Animations are limited to transitions with a **maximum duration of two seconds**, and there's no sensor access ([docs](https://developer.apple.com/documentation/widgetkit/animating-data-updates-in-widgets-and-live-activities)). |
| Live Activities | Yes, as a ≤160 pt card | – | Sandboxed, **4 KB data limit**, no network or location, ends after 8 h (12 h max on screen), and animations happen only on data updates ([docs](https://developer.apple.com/documentation/activitykit/displaying-live-data-with-live-activities)). No sensors and no frame loop, so physics is impossible. |
| Animated artwork (`MPMediaItemAnimatedArtwork`, iOS 26+) | Only during Now Playing | C | A pre-rendered **local video file** for a media item ([docs](https://developer.apple.com/documentation/mediaplayer/mpmediaitemanimatedartwork)). It's tied to audio playback, so using it as a fake wallpaper would also be a 2.5.1 "intended purpose" problem. |
| Live Photo wallpaper (iOS 17+) | Yes | **C** | A recorded clip plays **when the device wakes**. It does not react to tilt ([Apple Support](https://support.apple.com/120734)). |
| Spatial Scene wallpaper (iOS 26+) | Yes | **B** | A user-applied 3D depth effect that shifts with device motion. It is parallax, not physics, and there is no developer API. It works on photos the user picks. |
| Physics simulation inside an open app (SpriteKit + Core Motion) | Not on the Lock Screen | **D** | Fully supported, and straightforward to build. |
| StandBy | Shows widgets / Live Activities only | – | Same limits as above, so it can't run custom rendering. |

**Not on the Lock Screen at all:** shake-to-scatter (no sensor access there) and objects persisting while the phone is held at an angle (nothing runs).

**Foldable iPhone:** Apple announced **iPhone Duo** on 2026-09-09. Per secondary sources it ships on iOS 27.1, needs Xcode 27.1, and has an outer display that behaves like a standard iPhone ([TechTalk](https://developer.apple.com/videos/play/tech-talks/111461/), [MacTrast](https://www.mactrast.com/?p=173415)). I found **no new wallpaper API** for either of its displays, so the verdict is the same.

---

## 4. Official sources and SDK versions

- Current SDK: **iOS 27 / Xcode 27**. **iOS 27.1 / Xcode 27.1** adds iPhone Duo support. The versions come from secondary reporting; confirm them in Xcode → Settings → Platforms before any build.
- App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Core Motion `CMMotionManager`: https://developer.apple.com/documentation/coremotion/cmmotionmanager
- WidgetKit animation limits: https://developer.apple.com/documentation/widgetkit/animating-data-updates-in-widgets-and-live-activities
- ActivityKit Live Activities: https://developer.apple.com/documentation/activitykit/displaying-live-data-with-live-activities
- `MPMediaItemAnimatedArtwork`: https://developer.apple.com/documentation/mediaplayer/mpmediaitemanimatedartwork
- Live Photo wallpaper (Apple Support): https://support.apple.com/120734
- Android `WallpaperService.Engine`, the contrast case: https://developer.android.com/reference/android/service/wallpaper/WallpaperService.Engine
- iOS 27 Lock Screen changes are user-facing only (AI wallpapers, a movable clock, Extend): [9to5Mac](https://9to5mac.com/2026/08/05/ios-27-lock-screen-customization/)

**Limitation of this research:** I could not prove that something does not exist by reading every page. I searched Apple's documentation, the WWDC26 materials and the iOS 27 coverage, and found no wallpaper extension API. The `PosterKit` evidence shows the capability exists inside iOS but is private.

---

## 5. Comparable products

- **Verified category-A product on iPhone:** none found. The only real Lock Screen physics I found is *GravityLockScreen* (2012), a **jailbreak tweak** sold on Cydia ([iDownloadBlog](https://www.idownloadblog.com/?p=115307)). Its existence is consistent with the conclusion: it needed system modification.
- **What App Store "live wallpaper" apps actually sell:** Live Photo or video clips, which are category C. Examples: *Live Wallpapers for Me* ([App Store](https://apps.apple.com/us/app/-/id1069361548)) and *Video Wallpaper · Lock Screen* ([App Store](https://apps.apple.com/app/id1497777142)). *Frames* reportedly uses the Now Playing animated-artwork API to show video on the Lock Screen ([iThinkDiff](https://www.ithinkdiff.com/frames-lock-screen-videos-iphone/)). I have not verified its review status or how durable that approach is.
- **I did not download or test any of these.** Store listings can overstate what an app does. Treat any app claiming "interactive Lock Screen physics" as category C or D until it's proven on a device.

---

## 6. App Store risks (for the legitimate alternatives)

| Risk | Guideline | Severity | Mitigation |
|---|---|---|---|
| Wallpaper is a named saturated category: "we will not accept new submissions unless they offer a meaningfully different or improved experience" | 4.3(b) | **High** for a pure Live Photo/still catalog | Lead with real, original functionality (an in-app physics toy, personalised capture). Original art. Never use more than one bundle ID per theme (4.3(a)). |
| Thin functionality | 4.2 | Medium | The app needs lasting utility or entertainment *inside* the app, not just a download screen. |
| Misleading marketing ("interactive Lock Screen") | 2.3 (accurate metadata) | **High** if overstated | Screenshots and copy must show what actually happens on the Lock Screen (it plays on wake, or tilt-parallax). This is also a refund and review-score risk. |
| Misusing APIs (e.g. Now Playing artwork with no audio, background audio to stay alive) | 2.5.1 / 2.5.4 | **High**, rejection or removal | Don't do it. |
| Selling packs outside IAP | 3.1.1 | High | Use StoreKit non-consumables for theme packs. |

Developer-forum threads show 4.3 rejections and failed appeals even for apps that claimed originality ([example](https://developer.apple.com/forums/thread/841146)). These are anecdotes, not statistics, and **no approval is guaranteed.**

---

## 7. Recommended architecture (if you pick the iOS pivot, option P2 in §9)

- **App:** SwiftUI shell plus a SpriteKit `SKScene` with `SKPhysicsBody` for each object. Use convex or texture-based bodies, with restitution around 0.3, friction around 0.4 and angular damping tuned for tumbling. Gravity comes from `CMDeviceMotion.gravity`, mapped to scene axes and scaled. Shake comes from `userAcceleration` magnitude above a threshold, which applies random impulses.
- **Capture → wallpaper:** record N seconds of the simulation with `SKView.texture(from:)` or ReplayKit-free frame capture through AVAssetWriter, export it as a **Live Photo** (paired HEIC + MOV with matching content identifier), and save it with PhotoKit (add-only permission). Also export a high-resolution still for a **Spatial Scene**. The user applies it through Settings → Wallpaper. A guided in-app tutorial is mandatory, because the app cannot apply wallpapers itself.
- **Widget (optional):** a Lock Screen widget showing a small static bear pile that changes on a timeline. It's a nice extra, but it isn't the core product.
- **Content:** a theme manifest (JSON) plus on-demand resources or a backend for packs, with StoreKit 2 non-consumables.
- **Layout:** respect the clock and widget safe zones on all sizes, including the iPhone Duo outer and inner displays (size classes, not device checks).

Android, for the original product (option P1): `WallpaperService.Engine` with a Box2D/LiquidFun or JBox2D simulation, `SensorManager` gravity, and rendering paused in `onVisibilityChanged(false)` to protect the battery.

---

## 8. Effort estimates (assumptions, not commitments)

Assumes one experienced native developer, original art supplied separately, and no backend in v1.

| Work item | Estimate |
|---|---|
| In-app SpriteKit physics globe, 10 bears, tilt + shake, pastel UI | 1–2 weeks |
| Live Photo export pipeline + Photos save + on-device validation | 1–2 weeks (**highest technical risk**: see §10) |
| Theme system + StoreKit 2 packs + paywall/restore | 1–2 weeks |
| App Store assets, review prep, iPhone Duo layouts | 1 week |
| **iOS pivot total** | **~4–7 weeks** |
| Android live wallpaper (original product), physics + 1 theme + Play billing | ~3–5 weeks |
| Commercial-quality 3D art per theme pack (≈10–15 objects) | Outsourced. Cost and time unknown, quotes needed. |

Hard prerequisites: a **Mac with Xcode 27.x**, a **physical iPhone** (Core Motion and Live Photo wallpaper don't work in the Simulator), and an Apple Developer Program membership (US$99/yr). This session runs on **Linux, which has no Xcode**, so no iOS build could be verified here in any case.

---

## 9. Options, commercial risks and recommendation

### Recommendation: **PIVOT** (do **not** build the original spec on iOS)

| Option | What the customer gets | Matches the vision? | Main risk |
|---|---|---|---|
| **P1. Android first** | The *real* product: physics on the lock screen, tilt and shake | **Yes, fully** | Smaller paid-app spend than iOS. You'd need an Android build/test device. |
| **P2. iOS "snow globe + capture"** | An in-app physics toy (D). The user shakes and tilts, then saves *their own* tumble as a Live Photo wallpaper (C) or a still/Spatial Scene (B). | Partial: the motion on the Lock Screen is a replay on wake, **not** tilt-reactive | 4.3(b), plus disappointed buyers if marketing implies tilt physics |
| **P3. iOS pre-rendered Live Photo packs** | Category C only | No | Very high 4.3(b) risk, and commoditised |
| **P4. Wait for Apple** | – | – | Indefinite. File Feedback Assistant requests for a public wallpaper extension. |

My recommendation is **P1 + P2 together**, or P2 alone if you're committed to iOS. **Do not pursue P3**: it is the most saturated part of a saturated category.

**Commercial hypotheses (none validated):**
- Monetisation: free app with one free teddy theme. Theme packs (puppies, bunnies, hearts, seasonal) as non-consumable IAPs at about US$1.99–2.99 each, *or* an "all themes" unlock at about US$6.99. Avoid subscriptions in v1, because users expect a one-off purchase for wallpaper. Test both with a small paid-acquisition experiment before investing in art.
- Customisation: object count, size, bounciness, background pastel colour, and mixing objects from owned packs.
- The biggest commercial risk is **expectation mismatch**. People who saw the Samsung version will expect tilt physics on the Lock Screen. On iOS, P2 cannot provide that, which means refunds and 1-star reviews. Honest marketing reduces this but caps the appeal.
- Art is the real moat and the real cost. Physics code is easy to copy, and original, appealing characters are not.

---

## 10. Next concrete step

**Decision needed from you:** P1, P2, P1+P2, or stop.

If P2 is in scope, the first build should be a **1-week de-risking spike**, not the full app: generate a 3-second physics clip in-app, export it as a Live Photo, and confirm on a physical iPhone running iOS 27 that it (a) can be set as a Lock Screen wallpaper with motion enabled and (b) looks good with the clock and Duo outer display. iOS can refuse Live Photos for motion wallpaper. I have not verified what triggers that, so it's the single point of failure for P2.

No Xcode project was created, because the requested product is not technically possible through public APIs and the brief said to wait for a decision before building a different product.
