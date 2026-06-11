#!/usr/bin/env python3
"""
TradeCards — Cloud-ready flashcard server.
All spaced-repetition progress is stored in the browser (localStorage).
Images and card data are cached by the service worker for full offline support.
"""

import re, hashlib, os, socket
from pathlib import Path
from flask import Flask, jsonify, render_template, send_file, abort

try:
    from markdown import markdown as md_to_html
except ImportError:
    def md_to_html(t): return f"<p>{t}</p>"

app = Flask(__name__, static_folder="static")
OUTPUT_DIR = Path("./output")


# ─────────────────────────────────────────────────────────────────────────────
# Card data
# ─────────────────────────────────────────────────────────────────────────────
def uid(seed): return hashlib.md5(seed.encode()).hexdigest()[:12]

def parse_md(path):
    t = path.read_text(encoding="utf-8", errors="ignore")
    d = re.search(r"\*\*Date:\*\* (.+?)  ", t)
    c = re.search(r"\*\*Caption:\*\* (.+?)(?:  |\n)", t, re.DOTALL)
    body = t.split("---\n", 1)[-1].strip() if "---" in t else t
    return {
        "date":     d.group(1).strip() if d else "",
        "caption":  c.group(1).strip() if c else "",
        "body_html": md_to_html(body),
    }

VOLMAN_SETUPS = [
    ("Double Doji (DD)", ["volman","with-trend"],
     "What is the <b>Double Doji (DD)</b> setup?",
     """<span class='tag'>Volman · With-Trend</span><h3>Double Doji (DD)</h3>
<p>Two consecutive <b>doji or narrow-range candles</b> forming a tight pause in a trend.</p>
<ul><li>Best used <b>with the trend</b> — forms after a pullback to EMA</li>
<li>Signals buyer/seller balance before momentum resumes</li>
<li>Tighter dojis = more compressed energy = stronger break</li></ul>
<table><tr><th>Entry</th><td>Break of DD high (buy) / low (sell)</td></tr>
<tr><th>Stop</th><td>Other side of DD formation</td></tr>
<tr><th>Target</th><td>Next swing level or 2R</td></tr></table>"""),

    ("Second Break (SB)", ["volman","with-trend"],
     "What is the <b>Second Break (SB)</b> setup?",
     """<span class='tag'>Volman · With-Trend</span><h3>Second Break (SB)</h3>
<p>Price tests a level, <b>fails</b>, pulls back, then makes a <b>second attempt</b> that succeeds.</p>
<ul><li>First break shakes out weak hands</li>
<li>Second break powered by stronger momentum</li>
<li>Usually more reliable than the first break</li></ul>
<table><tr><th>Entry</th><td>On break of second attempt</td></tr>
<tr><th>Stop</th><td>Below the pullback between the two attempts</td></tr>
<tr><th>Target</th><td>Measured move from consolidation</td></tr></table>"""),

    ("Block Break (BB)", ["volman","breakout"],
     "What is the <b>Block Break (BB)</b> setup?",
     """<span class='tag'>Volman · Breakout</span><h3>Block Break (BB)</h3>
<p>Price consolidates in a <b>tight rectangular block</b> — clearly defined highs and lows.</p>
<ul><li>Draw a rectangle — price coils like a spring</li>
<li>Longer block = more potential energy</li>
<li>More traders see the same level → self-fulfilling breakout</li></ul>
<table><tr><th>Entry</th><td>Immediate break of block boundary</td></tr>
<tr><th>Stop</th><td>Opposite side of the block</td></tr>
<tr><th>Target</th><td>Block height projected from breakout</td></tr></table>"""),

    ("BB Squeeze", ["volman","breakout"],
     "What is the <b>BB Squeeze</b> (Bollinger Band Squeeze)?",
     """<span class='tag'>Volman · Breakout</span><h3>BB Squeeze</h3>
<p>Price sandwiched between the <b>20 EMA and a barrier</b> — volatility compressed.</p>
<ul><li>Bollinger Bands contract sharply</li>
<li>Longer squeeze = stronger eventual breakout</li>
<li>Direction follows the path of least resistance</li></ul>
<table><tr><th>Entry</th><td>Break out of squeeze range</td></tr>
<tr><th>Stop</th><td>Opposite boundary of squeeze</td></tr>
<tr><th>Target</th><td>Band width projected from breakout</td></tr></table>
<blockquote>"The longer it lasts and the more defined the barriers, the more players spot the same break." — Volman</blockquote>"""),

    ("Pattern Break Combi", ["volman","breakout"],
     "What is the <b>Pattern Break Combi</b> setup?",
     """<span class='tag'>Volman · Breakout</span><h3>Pattern Break Combi</h3>
<p>A <b>Powerbar</b> (large directional candle) followed by an <b>inside bar</b> closing in the same direction.</p>
<ul><li>Powerbar = decisive momentum candle</li>
<li>Inside bar = pause and reload</li>
<li>Enter on break of inside bar in Powerbar's direction</li></ul>
<table><tr><th>Entry</th><td>Break of inside bar</td></tr>
<tr><th>Stop</th><td>Opposite side of inside bar</td></tr>
<tr><th>Target</th><td>Next key level, 1.5–2R</td></tr></table>"""),

    ("First Break (FB)", ["volman","breakout"],
     "What is the <b>First Break (FB)</b> setup?",
     """<span class='tag'>Volman · Breakout</span><h3>First Break (FB)</h3>
<p>The <b>initial breakout</b> of a key support, resistance, or consolidation boundary.</p>
<ul><li>Works best with a clean, obvious level</li>
<li>Higher success when level has been tested multiple times</li>
<li>Lower probability than SB — first breaks often fail</li>
<li>A failed FB sets up the SB trade</li></ul>"""),

    ("Tipping Point", ["volman","reversal"],
     "What is the <b>Tipping Point</b> technique?",
     """<span class='tag'>Volman · Reversal</span><h3>Tipping Point</h3>
<p>A <b>price exhaustion signal</b> — the market has pushed too far and is about to reverse.</p>
<ul><li>Occurs at major S/R after an extended move</li>
<li>Signs: long wicks, doji at extremes, failed continuation</li>
<li>Counter-trend — use sparingly, higher risk</li></ul>
<blockquote>Volman uses this sparingly. The trend is your friend until the tipping point proves otherwise.</blockquote>"""),

    ("EMA as Dynamic S/R", ["volman","concept"],
     "How does Volman use the <b>EMA</b> in his setups?",
     """<span class='tag'>Volman · Core Concept</span><h3>EMA as Dynamic Support/Resistance</h3>
<p>Volman uses the <b>20-period EMA</b> as dynamic support/resistance — not a signal generator.</p>
<ul><li><b>Uptrend:</b> EMA = support → pullbacks = buy opportunities</li>
<li><b>Downtrend:</b> EMA = resistance → bounces = sell opportunities</li>
<li>DD/SB at EMA = highest probability setup</li>
<li>Price crossing EMA repeatedly = choppy market → avoid</li></ul>"""),

    ("R-Multiple & Risk", ["volman","risk"],
     "What is an <b>R-Multiple</b> and why does Volman use it?",
     """<span class='tag'>Risk Management</span><h3>R-Multiple</h3>
<p>All outcomes measured in units of <b>initial risk (R)</b> — removes emotion from dollar amounts.</p>
<table><tr><th>Result</th><th>Meaning</th></tr>
<tr><td class='bullish'>+2R</td><td>Made twice what you risked</td></tr>
<tr><td class='bullish'>+0.5R</td><td>Exited early, half profit</td></tr>
<tr><td class='bearish'>-1R</td><td>Full stop loss hit</td></tr></table>
<p>Your group uses this: <b>"+0.5R lợi nhuận"</b> = closed at half profit.</p>
<blockquote>At 1:2 R:R you only need to win 34% of trades to be profitable.</blockquote>"""),

    ("Patience & Trade Selection", ["volman","mindset"],
     "Why is <b>patience</b> the #1 skill in Volman's method?",
     """<span class='tag'>Mindset</span><h3>Patience & Trade Selection</h3>
<p>Volman: <b>not trading is a valid — and often correct — decision.</b></p>
<ul><li>Only take setups meeting ALL criteria — no "almost" trades</li>
<li>Best traders take 1–3 trades per day maximum</li>
<li>Overtrading is the #1 reason beginners lose money</li></ul>
<blockquote>"The market will always give another opportunity. A bad trade out of boredom costs you twice."</blockquote>"""),

    ("BB Squeeze vs Block Break", ["volman","comparison"],
     "What's the difference between <b>BB Squeeze</b> and <b>Block Break</b>?",
     """<span class='tag'>Volman · Comparison</span>
<table><tr><th></th><th>BB Squeeze</th><th>Block Break</th></tr>
<tr><td>Shape</td><td>Narrowing wedge between EMA + barrier</td><td>Flat rectangle</td></tr>
<tr><td>Key signal</td><td>Bollinger Bands contracting</td><td>Tight box of highs/lows</td></tr>
<tr><td>Best in</td><td>Trending market pausing</td><td>Any context</td></tr>
<tr><td>Entry</td><td>Break of squeeze boundary</td><td>Break of box boundary</td></tr></table>
<blockquote>Both exploit compressed energy. BB Squeeze leans on EMA; Block Break leans on pure price structure.</blockquote>"""),
]

CANDLESTICK_PATTERNS = [
    ("Doji","neutral","Open ≈ Close. Very small body, wicks either side.<br><b>Signals:</b> Indecision — neither bulls nor bears in control. Significant after a long trend: potential reversal warning."),
    ("Hammer","bullish","Bottom of downtrend. Short body at top, <b>long lower shadow</b> (≥2× body).<br><b>Signals:</b> Buyers pushed price back up after sellers drove it down → bullish reversal."),
    ("Inverted Hammer","bullish","Bottom of downtrend. Short body at bottom, <b>long upper shadow</b>.<br><b>Signals:</b> Buying interest emerging — potential reversal despite giving back gains."),
    ("Shooting Star","bearish","Top of uptrend. Short body at bottom, <b>long upper shadow</b>.<br><b>Signals:</b> Sellers rejected the highs → bearish reversal."),
    ("Hanging Man","bearish","Top of uptrend. Looks like a Hammer but at a <b>peak</b>.<br><b>Signals:</b> Despite the lower wick, sellers are gaining control. Bearish warning."),
    ("Bullish Engulfing","bullish","Small red candle → large green candle <b>completely engulfs</b> it.<br><b>Signals:</b> Buyers overwhelmed sellers → strong reversal from downtrend."),
    ("Bearish Engulfing","bearish","Small green candle → large red candle <b>completely engulfs</b> it.<br><b>Signals:</b> Sellers overwhelmed buyers → strong reversal from uptrend."),
    ("Morning Star","bullish","Long bearish → small star → long bullish.<br><b>Signals:</b> Middle candle = indecision; third confirms buyers took over. Reliable bottom reversal."),
    ("Evening Star","bearish","Long bullish → small star → long bearish.<br><b>Signals:</b> Reliable top reversal. Opposite of Morning Star."),
    ("Three White Soldiers","bullish","Three consecutive bullish candles, each closing near its high.<br><b>Signals:</b> Strong sustained buying. Reliable reversal or continuation."),
    ("Three Black Crows","bearish","Three consecutive bearish candles, each closing near its low.<br><b>Signals:</b> Strong sustained selling. Reliable downtrend reversal."),
    ("Spinning Top","neutral","Small body, <b>equal-length shadows</b> both sides.<br><b>Signals:</b> Battle between buyers and sellers — neither wins. Often before reversals or inside ranges."),
    ("Marubozu","neutral","<b>No shadows</b> — opens at one extreme, closes at the other.<br><b>Signals:</b> Complete dominance by one side. Very strong momentum signal."),
    ("Inside Bar","neutral","Entire range <b>fits within the previous candle</b>.<br><b>Signals:</b> Compression after a strong move. Volman uses this in Pattern Break Combi — break = entry."),
    ("Powerbar","neutral","Volman term for a <b>large full-bodied candle, minimal wicks</b>.<br><b>Signals:</b> Decisive control by one side. Key component of Pattern Break Combi."),
    ("Bullish Harami","bullish","Large bearish → small bullish candle <b>contained entirely inside</b> it.<br><b>Signals:</b> Decreasing sell pressure. Potential reversal, weaker than Engulfing."),
    ("Bearish Harami","bearish","Large bullish → small bearish candle <b>contained entirely inside</b> it.<br><b>Signals:</b> Decreasing buy pressure. Potential reversal, weaker signal."),
    ("Tweezer Tops","bearish","Two candles with <b>identical highs</b> at resistance after an uptrend.<br><b>Signals:</b> Price rejected at same high twice → strong resistance, bearish reversal."),
    ("Tweezer Bottoms","bullish","Two candles with <b>identical lows</b> at support after a downtrend.<br><b>Signals:</b> Price bounced at same low twice → strong support, bullish reversal."),
    ("Dragonfly Doji","bullish","Doji with <b>no upper shadow, long lower shadow</b>. Looks like a T.<br><b>Signals:</b> Sellers drove price down but buyers recovered everything. Bullish reversal at support."),
    ("Gravestone Doji","bearish","Doji with <b>no lower shadow, long upper shadow</b>. Upside-down T.<br><b>Signals:</b> Buyers pushed high but sellers reversed all gains. Bearish reversal at resistance."),
    ("Piercing Line","bullish","Long bearish → bullish opens below prior low, closes <b>above midpoint</b>.<br><b>Signals:</b> Buyers fought back strongly. Bullish reversal."),
    ("Dark Cloud Cover","bearish","Long bullish → bearish opens above prior high, closes <b>below midpoint</b>.<br><b>Signals:</b> Sellers fought back. Bearish reversal. Opposite of Piercing Line."),
    ("Long-Legged Doji","neutral","Doji with <b>very long equal shadows</b> both sides.<br><b>Signals:</b> Extreme indecision — wild swings, closed flat. Strong reversal warning."),
    ("Rising Three Methods","bullish","Long bullish → 3 small bearish (inside first) → long bullish above first.<br><b>Signals:</b> Brief pullback in uptrend — buyers still in control. Continuation."),
]

CONCEPTS = [
    ("Support Level",["price-action"],"What is a <b>Support Level</b>?",
     "<span class='tag'>Price Action</span><h3>Support Level</h3><p>A <b>price floor</b> where buying overcomes selling — price bounces here historically.</p><ul><li>More touches = stronger (but eventually it breaks)</li><li>When broken → support flips to <b>resistance</b></li><li>Look for zones (clusters of wicks), not single lines</li></ul><blockquote>Round numbers (1.2000, 150.00) often act as psychological support.</blockquote>"),
    ("Resistance Level",["price-action"],"What is a <b>Resistance Level</b>?",
     "<span class='tag'>Price Action</span><h3>Resistance Level</h3><p>A <b>price ceiling</b> where selling overcomes buying — price falls here historically.</p><ul><li>Multiple tests = stronger resistance</li><li>When broken → resistance flips to <b>support</b></li><li>Previous highs and round numbers are common zones</li></ul>"),
    ("Trend Structure",["price-action"],"How do you identify an <b>Uptrend vs Downtrend</b>?",
     "<span class='tag'>Price Action</span><h3>Trend Structure</h3><table><tr><th>Type</th><th>Structure</th></tr><tr><td class='bullish'>Uptrend</td><td>Higher Highs (HH) + Higher Lows (HL)</td></tr><tr><td class='bearish'>Downtrend</td><td>Lower Highs (LH) + Lower Lows (LL)</td></tr><tr><td class='neutral'>Sideways</td><td>Equal highs and lows — ranging</td></tr></table><blockquote>\"The trend is your friend — until it ends.\" Always trade with it for higher probability.</blockquote>"),
    ("Breakout vs Fakeout",["price-action"],"How do you tell a real <b>Breakout</b> from a <b>Fakeout</b>?",
     "<span class='tag'>Price Action</span><h3>Breakout vs Fakeout</h3><table><tr><th></th><th>Real Breakout</th><th>Fakeout</th></tr><tr><td>Close</td><td>Convincingly beyond level</td><td>Briefly pierces, closes back inside</td></tr><tr><td>Follow-through</td><td>Next candle continues</td><td>Next candle reverses</td></tr></table><blockquote>Fakeouts create the SB setup — failed breakout traders must exit, fuelling the real move.</blockquote>"),
    ("Pullback",["price-action"],"What is a <b>Pullback</b> and why is it an opportunity?",
     "<span class='tag'>Price Action</span><h3>Pullback</h3><p>A <b>temporary counter-trend move</b> within a larger trend — price pauses before continuing.</p><ul><li>Normal and healthy — reloads momentum</li><li>Best entry: buy pullbacks in uptrend, sell bounces in downtrend</li><li>Volman setups (DD, SB, BB) form at the end of pullbacks</li></ul><blockquote>Waiting for a pullback gives better entry + tighter stop = better R:R.</blockquote>"),
    ("Consolidation",["price-action"],"What is <b>Consolidation</b> and how do you trade it?",
     "<span class='tag'>Price Action</span><h3>Consolidation</h3><p>Price moves <b>sideways in a tight range</b> — neither side dominates.</p><ul><li>Energy builds during consolidation → eventual breakout</li><li>Tighter + longer = more powerful breakout</li><li>Trade the <b>breakout of it</b>, not inside it</li></ul><blockquote>Consolidation is the market loading up. Patience is rewarded.</blockquote>"),
    ("Price Action vs Indicators",["volman"],"Why does Volman use <b>price action only</b>?",
     "<span class='tag'>Volman · Philosophy</span><h3>Price Action vs Indicators</h3><p>Indicators are derived from price — they <b>lag</b> and can't show anything the raw chart doesn't already show.</p><table><tr><th></th><th>Price Action</th><th>Indicators</th></tr><tr><td>Speed</td><td>Real-time</td><td>Lagging</td></tr><tr><td>Clarity</td><td>Direct</td><td>Indirect/noisy</td></tr></table><p>Volman's only tool: the <b>20 EMA</b> — as a dynamic S/R reference only.</p>"),
    ("Timeframes",["price-action"],"How does <b>timeframe</b> affect your trading?",
     "<span class='tag'>Price Action</span><h3>Timeframe Selection</h3><table><tr><th>Timeframe</th><th>Style</th><th>Noise</th></tr><tr><td>1m–5m</td><td>Scalping</td><td>Very high</td></tr><tr><td>15m–1H</td><td>Day trading</td><td>Medium</td></tr><tr><td>4H–Daily</td><td>Swing trading</td><td>Low</td></tr></table><p>Your group uses <b>H1</b> — same as Volman's books.</p><blockquote>Always check H4/Daily before acting on an H1 signal.</blockquote>"),
    ("Stop Loss Placement",["risk"],"Where should your <b>Stop Loss</b> go in Volman's method?",
     "<span class='tag'>Risk Management</span><h3>Stop Loss Placement</h3><p>Just beyond the point where the <b>trade idea is invalidated</b> — not an arbitrary pip distance.</p><ul><li>DD/SB: just beyond the pattern's opposite side</li><li>BB/Squeeze: just inside the broken boundary</li><li><b>Never widen a stop</b> to avoid a loss</li><li>Once at +1R → move stop to breakeven</li></ul><table><tr><th>Max risk</th><td>1–2% of account per trade</td></tr></table>"),
]


def load_all_cards():
    cards = []
    for md_path in sorted(OUTPUT_DIR.rglob("*.md")):
        imgs = [f for f in md_path.parent.glob(md_path.stem + ".*")
                if f.suffix.lower() in (".jpg",".jpeg",".png",".webp")]
        if not imgs: continue
        img = imgs[0]
        info = parse_md(md_path)
        ticker = ""
        m = re.match(r"#([\w/]+)", info["caption"])
        if m: ticker = m.group(1)
        cards.append({
            "id": uid(f"chart_{img.name}"),
            "deck": "My Charts", "deck_icon": "📊",
            "front_type": "image",
            "front_caption": info["caption"][:120],
            "front_ticker": ticker,
            "image_name": img.name,
            "image_abs": str(img.resolve()),
            "back_html": info["body_html"],
            "tags": ["chart"],
        })
    for name, tags, front, back in VOLMAN_SETUPS:
        cards.append({"id": uid(f"volman_{name}"), "deck": "Bob Volman", "deck_icon": "📈",
                      "front_type": "text", "front_html": front, "back_html": back, "tags": tags})
    bi = {"bullish":"▲","bearish":"▼","neutral":"◆"}
    for name, bias, desc in CANDLESTICK_PATTERNS:
        cards.append({"id": uid(f"candle_{name}"), "deck": "Candlesticks", "deck_icon": "🕯",
                      "front_type": "text",
                      "front_html": f'<h2>🕯 {name}</h2><p class="hint">What does this pattern signal?</p>',
                      "back_html": f'<span class="tag {bias}">{bi[bias]} {bias.capitalize()}</span><h3>{name}</h3><p>{desc}</p>',
                      "tags": ["candlestick", bias]})
    for name, tags, front, back in CONCEPTS:
        cards.append({"id": uid(f"concept_{name}"), "deck": "Price Action", "deck_icon": "💡",
                      "front_type": "text", "front_html": front, "back_html": back, "tags": tags})
    return cards

ALL_CARDS = None
def get_cards():
    global ALL_CARDS
    if ALL_CARDS is None:
        ALL_CARDS = load_all_cards()
    return ALL_CARDS


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sw.js")
def service_worker():
    resp = app.send_static_file("sw.js")
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp

@app.route("/api/cards")
def api_cards():
    cards = [{k: v for k, v in c.items() if k != "image_abs"} for c in get_cards()]
    return jsonify(cards)

@app.route("/image/<path:filename>")
def image(filename):
    for c in get_cards():
        if c.get("image_name") == filename:
            return send_file(c["image_abs"])
    abort(404)

@app.route("/api/reload")
def reload_cards():
    global ALL_CARDS
    ALL_CARDS = None
    return jsonify({"ok": True, "count": len(get_cards())})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    cards = get_cards()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]; s.close()
    except: ip = "localhost"
    print(f"\n{'─'*50}")
    print(f"  🃏  TradeCards  —  {len(cards)} cards loaded")
    print(f"{'─'*50}")
    print(f"  Mac:    http://localhost:{port}")
    print(f"  iPhone: http://{ip}:{port}")
    print(f"{'─'*50}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
