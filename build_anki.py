#!/usr/bin/env python3
"""
Builds a comprehensive Anki deck for learning stock/forex trading.

Card sources:
  1. Your Telegram chart analyses  (chart image → Claude analysis)
  2. Bob Volman price action setups (9 core setups with rules)
  3. Candlestick pattern reference  (25 patterns)
  4. Price action core concepts     (20 concepts)

Run: python3 build_anki.py
Output: stock_trading_deck.apkg  (import into Anki desktop or AnkiMobile)
"""

import re
import hashlib
from pathlib import Path
import genanki

OUTPUT_DIR = Path("./output")
ANKI_OUTPUT = Path("./stock_trading_deck.apkg")

# ── Stable IDs — never change or Anki will duplicate your cards ──────────────
MODEL_IMAGE_ID   = 1_111_111_101
MODEL_TEXT_ID    = 1_111_111_102
DECK_CHARTS_ID   = 2_111_111_101
DECK_VOLMAN_ID   = 2_111_111_102
DECK_CANDLES_ID  = 2_111_111_103
DECK_CONCEPTS_ID = 2_111_111_104

# ── Shared CSS ────────────────────────────────────────────────────────────────
DARK_CSS = """
.card {
  font-family: 'Segoe UI', Arial, sans-serif;
  font-size: 15px;
  text-align: left;
  background: #0d1117;
  color: #e6edf3;
  padding: 18px;
  line-height: 1.6;
}
img { max-width: 100%; border-radius: 8px; margin-bottom: 10px; border: 1px solid #30363d; }
h2, h3 { color: #58a6ff; margin-top: 12px; }
b { color: #f0883e; }
.tag {
  display: inline-block;
  background: #21262d;
  color: #8b949e;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  margin-bottom: 10px;
  border: 1px solid #30363d;
}
table { width: 100%; border-collapse: collapse; margin: 8px 0; }
td, th { padding: 7px 12px; border: 1px solid #30363d; font-size: 14px; }
th { background: #161b22; color: #8b949e; text-transform: uppercase; font-size: 12px; }
ul, ol { padding-left: 22px; }
li { margin-bottom: 4px; }
blockquote {
  border-left: 3px solid #58a6ff;
  padding: 6px 12px;
  background: #161b22;
  border-radius: 0 6px 6px 0;
  color: #8b949e;
  margin: 10px 0;
}
hr { border: none; border-top: 1px solid #30363d; margin: 14px 0; }
.bullish { color: #3fb950; font-weight: bold; }
.bearish { color: #f85149; font-weight: bold; }
.neutral { color: #d29922; font-weight: bold; }
.front-hint { color: #8b949e; font-size: 13px; font-style: italic; margin-top: 10px; }
"""

# ── Models ────────────────────────────────────────────────────────────────────
image_model = genanki.Model(
    MODEL_IMAGE_ID, "Chart Analysis Card",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{"name": "Card", "qfmt": "{{Front}}", "afmt": "{{FrontSide}}<hr>{{Back}}"}],
    css=DARK_CSS,
)

text_model = genanki.Model(
    MODEL_TEXT_ID, "Trading Concept Card",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{"name": "Card", "qfmt": "{{Front}}", "afmt": "{{FrontSide}}<hr>{{Back}}"}],
    css=DARK_CSS,
)

# ── Decks ─────────────────────────────────────────────────────────────────────
deck_charts   = genanki.Deck(DECK_CHARTS_ID,   "Trading::1 - My Charts")
deck_volman   = genanki.Deck(DECK_VOLMAN_ID,   "Trading::2 - Bob Volman Setups")
deck_candles  = genanki.Deck(DECK_CANDLES_ID,  "Trading::3 - Candlestick Patterns")
deck_concepts = genanki.Deck(DECK_CONCEPTS_ID, "Trading::4 - Price Action Concepts")

media_files = []

def stable_guid(seed: str) -> str:
    """Generate a stable integer GUID from a string so reimports don't duplicate cards."""
    return str(int(hashlib.md5(seed.encode()).hexdigest()[:12], 16))


# ════════════════════════════════════════════════════════════════════════════
# SOURCE 1 — Your Telegram chart analyses
# ════════════════════════════════════════════════════════════════════════════
def parse_md(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    date    = re.search(r"\*\*Date:\*\* (.+?)  ", text)
    caption = re.search(r"\*\*Caption:\*\* (.+?)(?:  |\n)", text, re.DOTALL)
    body    = text.split("---\n", 1)[-1].strip() if "---" in text else text
    return {
        "date":    date.group(1).strip()    if date    else "",
        "caption": caption.group(1).strip() if caption else "",
        "body":    body,
    }

chart_count = 0
for md_path in sorted(OUTPUT_DIR.rglob("*.md")):
    imgs = [f for f in md_path.parent.glob(md_path.stem + ".*")
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    if not imgs:
        continue
    img_path = imgs[0]
    info = parse_md(md_path)

    media_files.append(str(img_path.resolve()))
    img_ref = img_path.name  # Telethon names are unique via msg_id

    caption_html = f'<p><b>📝 {info["caption"][:120]}</b></p>' if info["caption"] else ""
    front = (
        f'<p style="color:#8b949e;font-size:12px">📅 {info["date"]}</p>'
        f'<img src="{img_ref}">'
        f'{caption_html}'
        f'<p class="front-hint">What setup is shown? Trend? Key levels?</p>'
    )
    deck_charts.add_note(genanki.Note(
        model=image_model,
        fields=[front, info["body"]],
        guid=stable_guid(f"chart_{img_path.name}"),
        tags=["chart", "telegram"],
    ))
    chart_count += 1

print(f"  ✓ Charts deck:     {chart_count} cards")


# ════════════════════════════════════════════════════════════════════════════
# SOURCE 2 — Bob Volman Setups
# ════════════════════════════════════════════════════════════════════════════
VOLMAN_SETUPS = [
    {
        "name": "Double Doji (DD)",
        "tags": ["volman", "with-trend"],
        "front": "What is the <b>Double Doji (DD)</b> setup?",
        "back": """
<div class="tag">Volman • With-Trend</div>
<h3>Double Doji (DD)</h3>
<p>Two consecutive <b>doji or narrow-range candles</b> forming a tight pause in a trend.</p>
<ul>
  <li>Best used <span class="bullish">with the trend</span> — forms after a pullback</li>
  <li>Signals buyer/seller balance before momentum resumes</li>
  <li>Higher probability when DD sits near EMA as dynamic support</li>
</ul>
<table>
  <tr><th>Entry</th><td>Break of the DD high (buy) / low (sell)</td></tr>
  <tr><th>Stop</th><td>Other side of the DD formation</td></tr>
  <tr><th>Target</th><td>Next swing high/low or 2R</td></tr>
</table>
<blockquote>Key: the tighter the dojis, the more compressed the energy — stronger breakout potential.</blockquote>
""",
    },
    {
        "name": "Second Break (SB)",
        "tags": ["volman", "with-trend"],
        "front": "What is the <b>Second Break (SB)</b> setup?",
        "back": """
<div class="tag">Volman • With-Trend</div>
<h3>Second Break (SB)</h3>
<p>Price tests a level, <b>fails to break through</b>, pulls back, then makes a <b>second attempt</b> that succeeds.</p>
<ul>
  <li>First break fails — shakes out weak hands</li>
  <li>Second break is confirmed by stronger momentum</li>
  <li>Often more reliable than the first break</li>
</ul>
<table>
  <tr><th>Entry</th><td>On the break of the second attempt</td></tr>
  <tr><th>Stop</th><td>Below the pullback between the two attempts</td></tr>
  <tr><th>Target</th><td>Measured move from the consolidation</td></tr>
</table>
<blockquote>The failed first break acts as a "spring" — weak sellers get squeezed out, making the second move more powerful.</blockquote>
""",
    },
    {
        "name": "Block Break (BB)",
        "tags": ["volman", "breakout"],
        "front": "What is the <b>Block Break (BB)</b> setup?",
        "back": """
<div class="tag">Volman • Breakout</div>
<h3>Block Break (BB)</h3>
<p>Price consolidates in a <b>tight rectangular "block"</b> with clearly defined highs and lows, building tension before a breakout.</p>
<ul>
  <li>Draw a rectangle around the block — price coils like a spring</li>
  <li>The longer the block, the more potential energy</li>
  <li>Break direction follows the <b>path of least resistance</b></li>
  <li>More traders see the same level → self-fulfilling breakout</li>
</ul>
<table>
  <tr><th>Entry</th><td>Immediate break of the block boundary</td></tr>
  <tr><th>Stop</th><td>Opposite side of the block</td></tr>
  <tr><th>Target</th><td>Block height projected from breakout point</td></tr>
</table>
<blockquote>The BB has "tension written all over it" — a large amount of contracts changed hands without moving price, like a compressed coil.</blockquote>
""",
    },
    {
        "name": "BB Squeeze",
        "tags": ["volman", "breakout"],
        "front": "What is the <b>BB Squeeze</b> (Bollinger Band Squeeze) setup?",
        "back": """
<div class="tag">Volman • Breakout</div>
<h3>BB Squeeze</h3>
<p>Price gets <b>sandwiched between the 20 EMA and a barrier line</b>, compressing volatility into a tight range.</p>
<ul>
  <li>Bollinger Bands contract — volatility at a low point</li>
  <li>The longer the squeeze, the stronger the eventual break</li>
  <li>More players spot the same compressed range → explosive breakout</li>
  <li>Direction of break follows prior trend or strongest pressure</li>
</ul>
<table>
  <tr><th>Entry</th><td>Break out of the squeeze range</td></tr>
  <tr><th>Stop</th><td>Inside the squeeze (opposite boundary)</td></tr>
  <tr><th>Target</th><td>Width of bands projected from breakout</td></tr>
</table>
<blockquote>"The longer it lasts and the more defined the barriers, the more players will spot the same break." — Volman</blockquote>
""",
    },
    {
        "name": "Pattern Break Combi",
        "tags": ["volman", "breakout"],
        "front": "What is the <b>Pattern Break Combi</b> setup?",
        "back": """
<div class="tag">Volman • Breakout</div>
<h3>Pattern Break Combi</h3>
<p>A <b>Powerbar</b> (strong directional candle) followed by an <b>inside bar</b> that closes near the Powerbar's direction.</p>
<ul>
  <li><b>Powerbar</b>: large-bodied candle showing strong momentum</li>
  <li><b>Inside bar</b>: next candle's range fits entirely inside the Powerbar</li>
  <li>Inside bar closing in direction of Powerbar = continuation signal</li>
  <li>Can enter on break of inside bar OR break of the Powerbar</li>
</ul>
<table>
  <tr><th>Entry</th><td>Break of inside bar in Powerbar's direction</td></tr>
  <tr><th>Stop</th><td>Low of inside bar (for longs) / high for shorts</td></tr>
  <tr><th>Target</th><td>Next key level, typically 1.5–2R</td></tr>
</table>
<blockquote>The inside bar acts as a "pause and reload" — the market takes a breath before continuing the Powerbar's move.</blockquote>
""",
    },
    {
        "name": "First Break (FB)",
        "tags": ["volman", "breakout"],
        "front": "What is the <b>First Break (FB)</b> setup?",
        "back": """
<div class="tag">Volman • Breakout</div>
<h3>First Break (FB)</h3>
<p>The <b>initial breakout</b> of a key level — support, resistance, or consolidation boundary.</p>
<ul>
  <li>Works best when the level is <b>clean and obvious</b> to most traders</li>
  <li>Higher success when there's been a long buildup / test of the level</li>
  <li>Volume or momentum should confirm the break</li>
  <li>Lower probability than SB — first breaks often fail (become SB setups)</li>
</ul>
<table>
  <tr><th>Entry</th><td>On confirmed close beyond the level</td></tr>
  <tr><th>Stop</th><td>Back inside the broken level</td></tr>
  <tr><th>Target</th><td>Next visible level</td></tr>
</table>
<blockquote>If FB fails → watch for SB. The failure teaches you where the real level is.</blockquote>
""",
    },
    {
        "name": "Range Break",
        "tags": ["volman", "breakout"],
        "front": "What is the <b>Range Break</b> setup?",
        "back": """
<div class="tag">Volman • Breakout</div>
<h3>Range Break</h3>
<p>Price breaks out of a well-defined <b>horizontal trading range</b> with clear support and resistance boundaries.</p>
<ul>
  <li>Range must be clearly visible — obvious highs and lows</li>
  <li>Multiple touches of the range boundaries = more reliable</li>
  <li>Break with strong momentum and close outside = confirmation</li>
  <li>Often leads to a measured move equal to the range's height</li>
</ul>
<table>
  <tr><th>Entry</th><td>Breakout candle close outside the range</td></tr>
  <tr><th>Stop</th><td>Mid-point or opposite side of range</td></tr>
  <tr><th>Target</th><td>Range height projected from breakout</td></tr>
</table>
""",
    },
    {
        "name": "Inside Range Break (IRB)",
        "tags": ["volman", "breakout"],
        "front": "What is the <b>Inside Range Break (IRB)</b> setup?",
        "back": """
<div class="tag">Volman • Breakout</div>
<h3>Inside Range Break (IRB)</h3>
<p>A <b>smaller consolidation forming inside a larger range</b>, breaking out in the direction of the anticipated larger breakout.</p>
<ul>
  <li>The inner range is a range-within-a-range</li>
  <li>Early entry on the inner break gives better risk/reward</li>
  <li>Confirms when the outer range eventually breaks</li>
  <li>Higher precision — smaller stop, larger potential reward</li>
</ul>
<table>
  <tr><th>Entry</th><td>Break of the inner consolidation</td></tr>
  <tr><th>Stop</th><td>Other side of inner range</td></tr>
  <tr><th>Target</th><td>Outer range boundary (and beyond)</td></tr>
</table>
""",
    },
    {
        "name": "Tipping Point",
        "tags": ["volman", "reversal"],
        "front": "What is the <b>Tipping Point</b> technique?",
        "back": """
<div class="tag">Volman • Reversal / Exhaustion</div>
<h3>Tipping Point</h3>
<p>A <b>price exhaustion signal</b> — the market has pushed too far in one direction and is about to reverse.</p>
<ul>
  <li>Typically occurs at major support/resistance or after extended moves</li>
  <li>Look for: long wicks, doji candles, divergence from trend</li>
  <li>Price "tips over" — buyers/sellers can no longer sustain the move</li>
  <li>Use with caution: counter-trend trades carry higher risk</li>
</ul>
<table>
  <tr><th>Signal</th><td>Exhaustion candle + failed continuation</td></tr>
  <tr><th>Entry</th><td>Reversal candle confirmation</td></tr>
  <tr><th>Stop</th><td>Beyond the exhaustion wick</td></tr>
</table>
<blockquote>Volman uses this sparingly — the trend is your friend until the tipping point proves otherwise.</blockquote>
""",
    },
    {
        "name": "EMA as Dynamic Support/Resistance",
        "tags": ["volman", "concept"],
        "front": "How does Bob Volman use the <b>EMA</b> in his setups?",
        "back": """
<div class="tag">Volman • Core Concept</div>
<h3>EMA as Dynamic Support/Resistance</h3>
<p>Volman primarily uses the <b>20-period EMA</b> (Exponential Moving Average) as a dynamic support/resistance line.</p>
<ul>
  <li>In an <span class="bullish">uptrend</span>: EMA acts as support — pullbacks to EMA = buy opportunities</li>
  <li>In a <span class="bearish">downtrend</span>: EMA acts as resistance — bounces to EMA = sell opportunities</li>
  <li>Price hovering at EMA + a DD/SB pattern = high-probability setup</li>
  <li>Price crossing EMA repeatedly = choppy/ranging market — avoid</li>
</ul>
<blockquote>The EMA is not a signal on its own — it gives <em>context</em> to other setups. A DD at the EMA in a strong trend is far more powerful than a DD floating in open space.</blockquote>
""",
    },
    {
        "name": "The 25-pip Stop Rule",
        "tags": ["volman", "risk-management"],
        "front": "What is Bob Volman's approach to <b>stop placement and risk</b>?",
        "back": """
<div class="tag">Volman • Risk Management</div>
<h3>Stop Placement Philosophy</h3>
<p>Volman's method uses <b>tight, precise stops</b> based on the pattern itself — not arbitrary pip values.</p>
<ul>
  <li>Stop goes just beyond the pattern's invalidation point</li>
  <li>For H1 charts: typically 10–25 pips beyond the setup</li>
  <li>The tighter the formation, the tighter the stop → better R:R</li>
  <li>Never widen a stop to "give it more room"</li>
</ul>
<table>
  <tr><th>R:R Target</th><td>Minimum 1:1.5, ideally 1:2 or better</td></tr>
  <tr><th>Risk per trade</th><td>Fixed % of account (e.g. 1%)</td></tr>
</table>
<blockquote>"A tight stop is not just about limiting loss — it tells you immediately if the setup is wrong, so you can move on."</blockquote>
""",
    },
]

for s in VOLMAN_SETUPS:
    deck_volman.add_note(genanki.Note(
        model=text_model,
        fields=[s["front"], s["back"]],
        guid=stable_guid(f"volman_{s['name']}"),
        tags=s["tags"],
    ))

print(f"  ✓ Volman deck:     {len(VOLMAN_SETUPS)} cards")


# ════════════════════════════════════════════════════════════════════════════
# SOURCE 3 — Candlestick Patterns
# ════════════════════════════════════════════════════════════════════════════
CANDLESTICK_PATTERNS = [
    ("Doji", "neutral", "Opening and closing price are <b>nearly equal</b>. Body is very small or nonexistent. Long wicks can appear either side.<br><br>Signals <b>indecision</b> — neither bulls nor bears in control. Especially significant after a long trend: potential reversal warning."),
    ("Hammer", "bullish", "Found at the <b>bottom of a downtrend</b>. Short body at the top, <b>long lower shadow</b> (2× body length minimum), tiny or no upper shadow.<br><br>Buyers pushed price back up after sellers drove it down → bullish reversal signal."),
    ("Inverted Hammer", "bullish", "Found at the <b>bottom of a downtrend</b>. Short body at the bottom, <b>long upper shadow</b>, tiny lower shadow.<br><br>Buyers tried to push higher; even though they gave back gains, it shows buying interest is emerging."),
    ("Shooting Star", "bearish", "Found at the <b>top of an uptrend</b>. Short body at the bottom, <b>long upper shadow</b>, tiny lower shadow.<br><br>Opposite of inverted hammer. Sellers rejected the highs → bearish reversal signal."),
    ("Hanging Man", "bearish", "Found at the <b>top of an uptrend</b>. Looks identical to a Hammer but context is different.<br><br>Long lower shadow despite being at a high = sellers are gaining control. Bearish warning."),
    ("Bullish Engulfing", "bullish", "Two candles: a small <span class='bearish'>red/bearish</span> candle followed by a large <span class='bullish'>green/bullish</span> candle whose body <b>completely engulfs</b> the first.<br><br>Buyers overwhelmed sellers in one candle → strong reversal signal from a downtrend."),
    ("Bearish Engulfing", "bearish", "Two candles: a small <span class='bullish'>green/bullish</span> candle followed by a large <span class='bearish'>red/bearish</span> candle whose body <b>completely engulfs</b> the first.<br><br>Sellers overwhelmed buyers → strong reversal signal from an uptrend."),
    ("Morning Star", "bullish", "Three candles: <span class='bearish'>long bearish</span> → small-bodied (doji/spinning top) → <span class='bullish'>long bullish</span>.<br><br>The middle 'star' shows indecision; the third candle confirms reversal. Reliable bottom signal."),
    ("Evening Star", "bearish", "Three candles: <span class='bullish'>long bullish</span> → small-bodied star → <span class='bearish'>long bearish</span>.<br><br>Opposite of Morning Star. Reliable top reversal signal."),
    ("Three White Soldiers", "bullish", "Three consecutive <span class='bullish'>bullish candles</span> each opening within the previous candle's body and closing near their high.<br><br>Strong sustained buying pressure. Reliable uptrend reversal or continuation signal."),
    ("Three Black Crows", "bearish", "Three consecutive <span class='bearish'>bearish candles</span> each opening within the previous body and closing near their low.<br><br>Strong sustained selling pressure. Reliable downtrend reversal signal."),
    ("Spinning Top", "neutral", "Small body with <b>upper and lower shadows of roughly equal length</b>.<br><br>Signals a <b>battle between buyers and sellers</b> with neither winning. Often appears before a reversal or inside a range."),
    ("Marubozu", "neutral", "<b>No shadows at all</b> — the candle opens at its low (bullish) or high (bearish) and closes at the opposite extreme.<br><br>A <span class='bullish'>bullish marubozu</span> shows complete buyer dominance. A <span class='bearish'>bearish marubozu</span> shows complete seller dominance. Strong momentum signal."),
    ("Bullish Harami", "bullish", "A large <span class='bearish'>bearish candle</span> followed by a small <span class='bullish'>bullish candle</span> whose body fits <b>entirely within</b> the previous candle's body.<br><br>Decreasing selling pressure — potential reversal. Weaker than Engulfing."),
    ("Bearish Harami", "bearish", "A large <span class='bullish'>bullish candle</span> followed by a small <span class='bearish'>bearish candle</span> whose body fits <b>entirely within</b> the previous candle's body.<br><br>Decreasing buying pressure — potential reversal. Weaker signal."),
    ("Tweezer Tops", "bearish", "Two candles with <b>identical or near-identical highs</b> at a resistance level, after an uptrend.<br><br>Price tested the same high twice and was rejected both times → strong resistance confirmed, bearish reversal likely."),
    ("Tweezer Bottoms", "bullish", "Two candles with <b>identical or near-identical lows</b> at a support level, after a downtrend.<br><br>Price tested the same low twice and bounced both times → strong support confirmed, bullish reversal likely."),
    ("Piercing Line", "bullish", "In a downtrend: a long <span class='bearish'>bearish candle</span> followed by a <span class='bullish'>bullish candle</span> that opens below the prior low and closes <b>above the midpoint</b> of the bearish candle.<br><br>Buyers fought back strongly mid-session. Bullish reversal signal."),
    ("Dark Cloud Cover", "bearish", "In an uptrend: a long <span class='bullish'>bullish candle</span> followed by a <span class='bearish'>bearish candle</span> that opens above the prior high and closes <b>below the midpoint</b> of the bullish candle.<br><br>Sellers fought back strongly. Bearish reversal signal. Opposite of Piercing Line."),
    ("Inside Bar", "neutral", "A candle whose <b>entire range (high to low) fits within the previous candle's range</b>.<br><br>Shows <b>compression and indecision</b> after a strong move. Volman uses this in the Pattern Break Combi. Break of the inside bar signals continuation."),
    ("Powerbar", "neutral", "<b>Bob Volman's term</b> for a large, strong directional candle with a full body and minimal wicks.<br><br>Represents one side (buyers or sellers) taking <b>decisive control</b>. Key building block in the Pattern Break Combi — the inside bar that follows is the entry trigger."),
    ("Long-Legged Doji", "neutral", "A doji with <b>very long upper and lower shadows</b> of roughly equal length.<br><br>Extreme indecision — price swung wildly in both directions but closed where it opened. Strong warning of potential trend reversal."),
    ("Dragonfly Doji", "bullish", "A doji with <b>no upper shadow and a long lower shadow</b>. Looks like a 'T'.<br><br>Sellers pushed price down aggressively but buyers recovered all losses. Often signals a bullish reversal at support."),
    ("Gravestone Doji", "bearish", "A doji with <b>no lower shadow and a long upper shadow</b>. Looks like an upside-down 'T'.<br><br>Buyers pushed price up but sellers reversed all gains. Often signals a bearish reversal at resistance."),
    ("Rising Three Methods", "bullish", "A long <span class='bullish'>bullish candle</span>, followed by <b>3 small bearish candles</b> (contained within the first), then another long bullish candle that closes above the first.<br><br>A brief consolidation/pullback within an uptrend — buyers still in control. Continuation signal."),
]

for name, bias, desc in CANDLESTICK_PATTERNS:
    bias_html = f'<span class="{bias}">{"▲ Bullish" if bias=="bullish" else "▼ Bearish" if bias=="bearish" else "◆ Neutral"}</span>'
    back = f'<div class="tag">Candlestick • {bias_html}</div><h3>{name}</h3><p>{desc}</p>'
    front = f'<h2>🕯 {name}</h2><p class="front-hint">What does this candlestick pattern mean?</p>'
    deck_candles.add_note(genanki.Note(
        model=text_model,
        fields=[front, back],
        guid=stable_guid(f"candle_{name}"),
        tags=["candlestick", bias],
    ))

print(f"  ✓ Candlestick deck: {len(CANDLESTICK_PATTERNS)} cards")


# ════════════════════════════════════════════════════════════════════════════
# SOURCE 4 — Price Action Core Concepts
# ════════════════════════════════════════════════════════════════════════════
CONCEPTS = [
    ("Support Level", ["price-action"], "What is a <b>Support Level</b>?", """
<div class="tag">Price Action • Foundation</div>
<h3>Support Level</h3>
<p>A <b>price floor</b> where buying pressure historically overcomes selling pressure, causing price to bounce.</p>
<ul>
  <li>More touches = stronger support (but eventually it breaks)</li>
  <li>When broken, support often becomes <b>resistance</b> (role reversal)</li>
  <li>Round numbers often act as psychological support</li>
</ul>
<blockquote>Support isn't a precise price — it's a <em>zone</em>. Look for clusters of wicks/closes rather than a single line.</blockquote>
"""),
    ("Resistance Level", ["price-action"], "What is a <b>Resistance Level</b>?", """
<div class="tag">Price Action • Foundation</div>
<h3>Resistance Level</h3>
<p>A <b>price ceiling</b> where selling pressure historically overcomes buying pressure, causing price to fall.</p>
<ul>
  <li>Multiple tests without breaking = strong resistance</li>
  <li>When broken, resistance often flips to <b>support</b></li>
  <li>Previous highs and round numbers are common resistance zones</li>
</ul>
<blockquote>The more times a level is tested without breaking, the more significant the eventual breakout will be.</blockquote>
"""),
    ("Trend Structure", ["price-action"], "What defines an <b>Uptrend vs Downtrend</b> in price action?", """
<div class="tag">Price Action • Foundation</div>
<h3>Trend Structure</h3>
<table>
  <tr><th>Type</th><th>Definition</th></tr>
  <tr><td><span class="bullish">Uptrend</span></td><td>Series of <b>Higher Highs (HH)</b> and <b>Higher Lows (HL)</b></td></tr>
  <tr><td><span class="bearish">Downtrend</span></td><td>Series of <b>Lower Highs (LH)</b> and <b>Lower Lows (LL)</b></td></tr>
  <tr><td><span class="neutral">Sideways</span></td><td>Highs and lows at roughly the same level — range-bound</td></tr>
</table>
<p><b>Trend change signal:</b> a break of the most recent HL (in uptrend) or LH (in downtrend) suggests the trend is weakening.</p>
<blockquote>"The trend is your friend — until it ends." Trade with the trend for higher probability setups.</blockquote>
"""),
    ("Breakout", ["price-action"], "What is a <b>Breakout</b> and how do you confirm it?", """
<div class="tag">Price Action • Breakout</div>
<h3>Breakout</h3>
<p>Price moves <b>decisively beyond a key support or resistance level</b> it previously could not cross.</p>
<ul>
  <li><b>True breakout:</b> candle closes convincingly beyond the level</li>
  <li><b>False breakout (fakeout):</b> price briefly pierces the level but closes back inside</li>
  <li>Higher timeframe breakouts are more significant</li>
  <li>Failed breakouts often lead to sharp moves in the opposite direction</li>
</ul>
<table>
  <tr><th>Confirmation</th><td>Close beyond level + follow-through candle</td></tr>
  <tr><th>Volume</th><td>Increased volume supports genuine breakout</td></tr>
</table>
"""),
    ("Pullback / Retracement", ["price-action"], "What is a <b>Pullback</b> and why does it matter?", """
<div class="tag">Price Action • Trend</div>
<h3>Pullback / Retracement</h3>
<p>A <b>temporary counter-trend move</b> within a larger trend — price pauses and partially reverses before continuing.</p>
<ul>
  <li>Pullbacks are <b>normal and healthy</b> — they reload momentum</li>
  <li>Key entry opportunity: buy pullbacks in an uptrend, sell bounces in a downtrend</li>
  <li>Volman setups (DD, SB, BB) often form at the end of pullbacks</li>
  <li>Common pullback levels: EMA, prior support/resistance, 50% of the move</li>
</ul>
<blockquote>Waiting for a pullback gives you a better entry price and a tighter stop — improving your R:R ratio.</blockquote>
"""),
    ("Risk/Reward Ratio (R:R)", ["risk-management"], "What is <b>Risk/Reward Ratio</b> and why is it critical?", """
<div class="tag">Risk Management • Core</div>
<h3>Risk/Reward Ratio (R:R)</h3>
<p>Compares how much you <b>risk</b> per trade vs how much you <b>aim to gain</b>.</p>
<table>
  <tr><th>R:R</th><th>Meaning</th><th>Win rate needed to break even</th></tr>
  <tr><td>1:1</td><td>Risk $1 to make $1</td><td>50%</td></tr>
  <tr><td>1:2</td><td>Risk $1 to make $2</td><td>33%</td></tr>
  <tr><td>1:3</td><td>Risk $1 to make $3</td><td>25%</td></tr>
</table>
<p>Volman recommends <b>minimum 1:1.5</b> for his setups. Higher R:R means you can be wrong more often and still profit.</p>
<blockquote>A trader with a 40% win rate and 1:2 R:R is more profitable than a 60% win rate trader with 1:0.8 R:R.</blockquote>
"""),
    ("R-Multiple", ["risk-management"], "What is an <b>R-Multiple</b>?", """
<div class="tag">Risk Management • Core</div>
<h3>R-Multiple</h3>
<p>A universal way to measure trade outcomes in units of <b>initial risk (R)</b>, regardless of dollar amounts.</p>
<table>
  <tr><th>Result</th><th>Meaning</th></tr>
  <tr><td><span class="bullish">+1R</span></td><td>Made exactly what you risked</td></tr>
  <tr><td><span class="bullish">+2R</span></td><td>Made twice what you risked</td></tr>
  <tr><td><span class="bearish">-1R</span></td><td>Full stop loss hit</td></tr>
  <tr><td><span class="bearish">-0.5R</span></td><td>Exited early for half a loss</td></tr>
</table>
<p>Your Telegram group uses this notation (e.g. "+0.5R lợi nhuận").</p>
<blockquote>Tracking in R-multiples removes emotional attachment to dollar amounts and reveals your true edge.</blockquote>
"""),
    ("Consolidation", ["price-action"], "What is <b>Consolidation</b> in a chart?", """
<div class="tag">Price Action • Pattern</div>
<h3>Consolidation</h3>
<p>A period where price moves <b>sideways in a tight range</b> — neither bulls nor bears dominate.</p>
<ul>
  <li>Energy builds up during consolidation → eventual breakout</li>
  <li>Tighter and longer consolidation = more powerful breakout</li>
  <li>Bob Volman's BB and BB Squeeze setups specifically trade this</li>
  <li>Trade the <em>breakout of</em> consolidation, not within it</li>
</ul>
<blockquote>Consolidation is the market "loading up" before the next move. Patience during this phase is rewarded.</blockquote>
"""),
    ("Market Structure", ["price-action"], "What is <b>Market Structure</b>?", """
<div class="tag">Price Action • Foundation</div>
<h3>Market Structure</h3>
<p>The overall framework of <b>highs, lows, trends, and ranges</b> that define the market's current state.</p>
<ul>
  <li><b>Bullish structure:</b> HH + HL sequence intact</li>
  <li><b>Bearish structure:</b> LH + LL sequence intact</li>
  <li><b>Break of structure (BOS):</b> price takes out a key swing point — potential trend change</li>
  <li>Always identify the bigger picture structure before zooming into setups</li>
</ul>
<blockquote>Before entering any trade, ask: "What is the current market structure?" Trading against it is fighting the tide.</blockquote>
"""),
    ("False Breakout / Fakeout", ["price-action"], "What is a <b>False Breakout (Fakeout)</b>?", """
<div class="tag">Price Action • Breakout</div>
<h3>False Breakout / Fakeout</h3>
<p>Price briefly moves beyond a key level but <b>quickly reverses back</b> inside, trapping breakout traders.</p>
<ul>
  <li>Common at obvious support/resistance where stops cluster</li>
  <li>Large players often push price through levels to trigger stops before reversing</li>
  <li>Volman's SB (Second Break) acknowledges this: the first break often fakes out, the second is real</li>
</ul>
<blockquote>When you spot a fakeout, it often becomes a high-probability trade in the <em>opposite</em> direction — trapped traders must cover their losses.</blockquote>
"""),
    ("Stop Loss", ["risk-management"], "What is a <b>Stop Loss</b> and where should it go?", """
<div class="tag">Risk Management • Core</div>
<h3>Stop Loss</h3>
<p>A pre-set order to <b>exit a losing trade</b> at a defined price — your "line in the sand."</p>
<ul>
  <li>Placed at the point where the <b>trade idea is invalidated</b></li>
  <li>For Volman: just beyond the pattern boundary (BB, DD, etc.)</li>
  <li>Never move a stop <em>wider</em> to avoid a loss — this is how small losses become account-killers</li>
  <li>Moving stop to breakeven (BE) after +1R = free trade</li>
</ul>
<table>
  <tr><th>Rule</th><td>Risk no more than 1–2% of account per trade</td></tr>
</table>
<blockquote>"A stop loss is not a sign of weakness — it's the tool that lets you trade another day."</blockquote>
"""),
    ("Price Action vs Indicators", ["price-action"], "Why does Bob Volman use <b>price action only</b> (no indicators)?", """
<div class="tag">Volman • Philosophy</div>
<h3>Price Action vs Indicators</h3>
<p>Indicators are <b>derived from price</b> — they lag behind and can't tell you anything the raw chart doesn't already show.</p>
<table>
  <tr><th></th><th>Price Action</th><th>Indicators</th></tr>
  <tr><td>Speed</td><td>Real-time</td><td>Lagging</td></tr>
  <tr><td>Clarity</td><td>Direct</td><td>Indirect / noisy</td></tr>
  <tr><td>Subjectivity</td><td>Low</td><td>Can vary with settings</td></tr>
</table>
<p>Volman's only "indicator" is the <b>20 EMA</b> — and he uses it purely as a dynamic S/R reference, not a signal generator.</p>
<blockquote>"Strip away the noise. The chart tells you everything — if you know how to read it."</blockquote>
"""),
    ("Timeframe", ["price-action"], "How does <b>timeframe selection</b> affect trading?", """
<div class="tag">Price Action • Concept</div>
<h3>Timeframe Selection</h3>
<table>
  <tr><th>Timeframe</th><th>Style</th><th>Noise level</th></tr>
  <tr><td>1m–5m</td><td>Scalping</td><td>Very high</td></tr>
  <tr><td>15m–1H</td><td>Day trading</td><td>Medium</td></tr>
  <tr><td>4H–Daily</td><td>Swing trading</td><td>Low</td></tr>
  <tr><td>Weekly</td><td>Position trading</td><td>Very low</td></tr>
</table>
<p>Your Telegram group uses <b>H1 (1-hour)</b> charts — Bob Volman's "Understanding Price Action" also uses H1.</p>
<blockquote>Higher timeframe setups carry more weight. Always check the H4/Daily before acting on an H1 signal.</blockquote>
"""),
    ("EUR/USD as a Learning Pair", ["volman", "concept"], "Why does Volman focus on <b>EUR/USD</b>?", """
<div class="tag">Volman • Philosophy</div>
<h3>EUR/USD — Volman's Instrument of Choice</h3>
<ul>
  <li><b>Tightest spread</b> — lowest transaction cost of any major pair</li>
  <li><b>Highest liquidity</b> — hardest to manipulate, cleanest price action</li>
  <li><b>Highly repetitive patterns</b> — Volman's setups appear consistently</li>
  <li>Active during London + New York session overlap (peak volume)</li>
</ul>
<blockquote>Volman spent years studying just ONE pair on ONE timeframe. Mastery of one beats mediocrity across many.</blockquote>
<p>Your group trades multiple pairs (USDJPY, GBPAUD, etc.) — the same principles apply, just with slightly wider spreads.</p>
"""),
    ("Patience and Trade Selection", ["mindset"], "Why is <b>trade selection and patience</b> so important in Volman's method?", """
<div class="tag">Mindset • Core</div>
<h3>Patience and Trade Selection</h3>
<p>Volman repeatedly emphasizes that <b>not trading is a valid decision</b>. Quality over quantity.</p>
<ul>
  <li>Only take setups that meet <em>all</em> criteria — no "almost" trades</li>
  <li>The best traders may only take 1–3 trades per day</li>
  <li>Overtrading is the #1 reason beginners lose money</li>
  <li>A day with no trades is often a winning day</li>
</ul>
<blockquote>"The market will always give you another opportunity. A bad trade taken out of boredom costs you twice — money lost and capital tied up when the real setup arrives."</blockquote>
"""),
]

for name, tags, front_html, back_html in CONCEPTS:
    deck_concepts.add_note(genanki.Note(
        model=text_model,
        fields=[front_html, back_html],
        guid=stable_guid(f"concept_{name}"),
        tags=tags,
    ))

print(f"  ✓ Concepts deck:   {len(CONCEPTS)} cards")


# ════════════════════════════════════════════════════════════════════════════
# EXPORT
# ════════════════════════════════════════════════════════════════════════════
package = genanki.Package([deck_charts, deck_volman, deck_candles, deck_concepts])
package.media_files = media_files
package.write_to_file(str(ANKI_OUTPUT))

total = chart_count + len(VOLMAN_SETUPS) + len(CANDLESTICK_PATTERNS) + len(CONCEPTS)
print(f"\n✅ Deck exported: {ANKI_OUTPUT.resolve()}")
print(f"   Total cards: {total}")
print(f"\nImport into Anki:")
print(f"  Desktop: File → Import → select stock_trading_deck.apkg")
print(f"  Mobile:  Share the .apkg file to AnkiMobile / AnkiDroid")
