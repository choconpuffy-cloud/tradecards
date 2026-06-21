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

# ── Setup SVG diagrams (schematic price charts) ──────────────────────────────
def _svg(body, hint=""):
    hint_el = f'<text x="8" y="13" fill="#8b949e" font-size="9" font-family="sans-serif">{hint}</text>' if hint else ""
    return f'<svg viewBox="0 0 280 130" style="display:block;margin:0 0 10px;max-width:100%;border-radius:8px;background:#0d1117">{hint_el}{body}</svg>'

def _lvl(y, color, label, x1=8, x2=270):
    side = max(x1, x2-32)
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width=".85" stroke-dasharray="4,3"/><text x="{side}" y="{y-2}" fill="{color}" font-size="8" font-family="sans-serif">{label}</text>'

def _pl(pts, color, w=2.5):
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'

def _zone(x, y, w, h, color="#58a6ff"):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" opacity=".1" rx="2"/>'

def _lbl(x, y, txt, color="#8b949e"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="8.5" font-family="sans-serif">{txt}</text>'

G="#3fb950"; R="#f85149"; B="#58a6ff"; O="#f0883e"; M="#8b949e"

_SETUP_SVGS = {
"dd": _svg(
    _pl("10,115 30,104 48,93 62,84",G)+
    _pl("62,84 74,89 84,93",R)+
    _pl("84,93 96,88 110,88",M)+
    _zone(82,82,30,12)+
    _lbl(84,104,"DD")+
    _pl("8,110 60,100 110,92 160,84 220,79 272,76",O,1.2)+
    _lbl(210,92,"EMA",O)+
    _pl("110,88 128,76 148,64 168,51",G)+
    _lvl(82,B,"Entry↑",82)+
    _lvl(93,R,"Stop",82)+
    _lvl(53,G,"Target",82),
    "2 narrow candles at EMA → break direction"),

"sb": _svg(
    _lvl(68,B,"Resistance",8,270)+
    _lbl(34,66,"✗",R)+_lbl(100,66,"✓",G)+
    _pl("10,115 35,95 55,70",G)+
    _pl("55,70 70,82",R)+
    _pl("70,82 85,70 100,70",O)+
    _pl("100,70 120,58 145,44 170,34",G)+
    _zone(97,64,26,12)+
    _lvl(82,R,"Stop",82)+
    _lvl(36,G,"Target",82)+
    _lbl(46,80,"1st break",M)+
    _lbl(88,80,"2nd",M),
    "fail first break → pullback → 2nd attempt succeeds"),

"bb": _svg(
    _lvl(70,B,"Block high",8,270)+
    _lvl(96,R,"Block low",8,270)+
    _zone(14,70,100,26,M)+
    _pl("14,88 28,72 42,90 56,72 70,90 82,72 96,82",M)+
    _pl("96,82 116,66 138,52 160,40",G)+
    _zone(94,62,26,12)+
    _lvl(62,B,"Entry↑",94)+
    _lvl(100,R,"Stop",94)+
    _lvl(42,G,"Target",114),
    "price coils in block → energy releases on breakout"),

"squeeze": _svg(
    _lvl(62,B,"Barrier",8,270)+
    _pl("8,108 50,100 90,92 130,82 170,74 210,68 240,65",O,1.2)+
    _lbl(200,79,"EMA",O)+
    _pl("10,100 28,92 46,84 64,78 82,74 100,70 118,68",M)+
    _pl("118,68 138,55 160,43 184,33",G)+
    _zone(112,58,12,14)+
    _lvl(58,B,"Entry↑",114)+
    _lvl(72,R,"Stop",114)+
    _lvl(35,G,"Target",136),
    "price trapped between barrier & rising EMA → explosive break"),

"combi": _svg(
    _lbl(50,125,"Powerbar",M)+_lbl(96,125,"Inside bar",M)+
    _pl("10,110 35,100 55,88",M)+
    _lvl(78,M,"",52,80)+
    _lvl(108,M,"",52,80)+
    _zone(50,78,32,30,M)+
    '<line x1="66" y1="80" x2="66" y2="108" stroke="'+M+'" stroke-width=".5"/>'+
    '<rect x="52" y="80" width="28" height="28" fill="none" stroke="'+O+'" stroke-width=".8" stroke-dasharray="2,2" rx="1"/>'+
    '<rect x="58" y="88" width="16" height="14" fill="'+G+'" rx="1" opacity=".9"/>'+
    _pl("80,84 100,71 120,58 140,44",G)+
    _zone(78,74,10,16,B)+
    _lvl(74,B,"Entry↑",80)+
    _lvl(112,R,"Stop",80)+
    _lvl(46,G,"Target",100),
    "Powerbar + inside bar → enter on inside bar break"),

"fb": _svg(
    _lvl(68,B,"Key Level",8,270)+
    _pl("10,112 30,100 50,70",G)+
    _pl("50,70 60,82",R)+
    _pl("60,82 72,100 88,70",G)+
    _pl("88,70 98,84",R)+
    _pl("98,84 112,110 125,70",G)+
    _lbl(42,92,"Touch 1",M)+_lbl(76,112,"Touch 2",M)+_lbl(108,122,"Touch 3",M)+
    _pl("125,70 145,56 165,42 188,30",G)+
    _zone(122,60,18,12)+
    _lvl(60,B,"Entry↑",122)+
    _lvl(73,R,"Stop",122)+
    _lvl(32,G,"Target",140),
    "level tested multiple times → first clean breakout"),

"tipping": _svg(
    _pl("10,118 30,106 50,90 70,75 90,60 108,50",G)+
    '<line x1="108" y1="38" x2="108" y2="66" stroke="'+R+'" stroke-width="1.5" stroke-linecap="round"/>'+
    '<line x1="122" y1="42" x2="122" y2="62" stroke="'+R+'" stroke-width="1.5" stroke-linecap="round"/>'+
    _lbl(100,36,"Exhaustion",R)+
    _pl("108,50 122,56 138,68 155,80 172,94 190,108",R)+
    _zone(104,44,24,22,R)+
    _lvl(55,R,"Entry↓",130)+
    _lvl(40,R,"Stop",130)+
    _lvl(110,G,"Target",150),
    "trend extends too far → rejection wicks → counter-trend entry"),

"ema_sr": _svg(
    _pl("8,108 50,100 110,90 170,82 230,76 272,72",O,1.2)+
    _lbl(224,86,"20 EMA",O)+
    _pl("10,96 30,84 50,74",G)+
    _pl("50,74 65,82 78,90",R)+
    _pl("78,90 98,80 118,68",G)+
    _pl("118,68 132,76 144,84",R)+
    _pl("144,84 162,72 180,60 200,48",G)+
    _lbl(58,100,"Buy",B)+_lbl(132,94,"Buy",B)+
    _zone(62,82,16,10,B)+_zone(134,76,12,10,B)+
    _lvl(90,M,"Pullback zone",62)+
    _lvl(84,M,"",132),
    "20 EMA = dynamic support in uptrend — buy the dip to it"),
}

_CHART_SVGS = {
"double_top": _svg(
    _lvl(50,R,"Resistance",8,270)+
    _lvl(85,B,"Neckline",8,270)+
    _pl("10,110 45,52 70,85 100,52 130,90 160,108",M)+
    _zone(126,85,40,12,R)+
    _lbl(28,44,"Peak 1",M)+_lbl(92,44,"Peak 2",M)+
    _pl("130,90 150,100 172,115",R)+
    _lvl(110,G,"Target",148)+
    _lbl(140,88,"Entry↓",B),
    "2 peaks at same resistance → bearish reversal"),

"double_bottom": _svg(
    _lvl(95,G,"Support",8,270)+
    _lvl(65,B,"Neckline",8,270)+
    _pl("10,40 42,92 68,65 98,92 128,60 158,38",M)+
    _zone(124,58,16,12,G)+
    _lbl(28,106,"Trough 1",M)+_lbl(88,106,"Trough 2",M)+
    _pl("128,60 148,48 170,36 192,24",G)+
    _lvl(25,G,"Target",148)+
    _lbl(130,56,"Entry↑",B),
    "2 troughs at same support → bullish reversal"),

"head_shoulders": _svg(
    _lvl(85,B,"Neckline",8,270)+
    _pl("10,105 35,70 55,85 80,48 105,85 128,70 148,90 175,112",M)+
    _lbl(28,66,"LS",M)+_lbl(74,42,"Head",M)+_lbl(122,66,"RS",M)+
    _zone(144,85,36,14,R)+
    _pl("148,90 162,100 178,115",R)+
    _lvl(110,G,"Target",170)+
    _lbl(150,88,"Entry↓",B),
    "3 peaks (head highest) → breakdown below neckline"),

"asc_triangle": _svg(
    _lvl(58,R,"Resistance",8,270)+
    _pl("15,105 40,60 60,92 85,60 108,80 132,60 152,75",M)+
    '<line x1="15" y1="105" x2="155" y2="73" stroke="'+G+'" stroke-width="1" stroke-dasharray="4,3"/>'+
    _pl("155,70 175,55 196,40",G)+
    _lbl(20,116,"Rising lows",G)+
    _zone(152,55,20,18,G)+
    _lvl(42,G,"Target",170)+
    _lbl(154,68,"Entry↑",B),
    "flat resistance + rising lows → bullish breakout"),

"desc_triangle": _svg(
    _lvl(96,G,"Support",8,270)+
    _pl("15,55 40,94 60,70 85,94 108,78 132,94 150,82",M)+
    '<line x1="15" y1="55" x2="155" y2="84" stroke="'+R+'" stroke-width="1" stroke-dasharray="4,3"/>'+
    _pl("155,90 172,100 192,115",R)+
    _lbl(20,48,"Falling highs",R)+
    _zone(150,90,20,18,R)+
    _lvl(115,R,"Target",168)+
    _lbl(153,100,"Entry↓",B),
    "flat support + falling highs → bearish breakdown"),

"sym_triangle": _svg(
    '<line x1="15" y1="50" x2="148" y2="78" stroke="'+R+'" stroke-width="1" stroke-dasharray="4,3"/>'+
    '<line x1="15" y1="105" x2="148" y2="78" stroke="'+G+'" stroke-width="1" stroke-dasharray="4,3"/>'+
    _pl("15,55 38,98 60,65 84,95 106,72 128,85 148,78",M)+
    _pl("148,78 168,62 190,46 212,32",G)+
    _lbl(20,44,"Lower highs",R)+_lbl(20,120,"Higher lows",G)+
    _zone(144,62,20,18,G)+
    _lvl(32,G,"Target",188)+
    _lbl(148,72,"Entry↑",B),
    "converging highs & lows → breakout on compression"),

"bull_flag": _svg(
    _lbl(20,122,"Pole",G)+_lbl(80,122,"Flag",M)+_lbl(152,122,"Target",G)+
    '<line x1="62" y1="20" x2="62" y2="110" stroke="'+M+'" stroke-width=".6" stroke-dasharray="2,2"/>'+
    '<line x1="118" y1="20" x2="118" y2="110" stroke="'+M+'" stroke-width=".6" stroke-dasharray="2,2"/>'+
    _pl("10,112 34,80 58,42",G)+
    _pl("58,42 72,55 86,50 100,62 118,55",M)+
    _pl("118,55 138,40 160,25 182,12",G)+
    _zone(114,46,14,18,G)+
    _lvl(26,G,"Target",136)+
    _lvl(66,R,"Stop",120)+
    _lbl(118,50,"Entry↑",B),
    "strong pole + pullback flag → continuation breakout"),

"bear_flag": _svg(
    _lbl(20,14,"Pole",R)+_lbl(80,14,"Flag",M)+_lbl(152,14,"Target",R)+
    '<line x1="62" y1="20" x2="62" y2="120" stroke="'+M+'" stroke-width=".6" stroke-dasharray="2,2"/>'+
    '<line x1="118" y1="20" x2="118" y2="120" stroke="'+M+'" stroke-width=".6" stroke-dasharray="2,2"/>'+
    _pl("10,28 34,58 58,96",R)+
    _pl("58,96 72,82 86,88 100,75 118,82",M)+
    _pl("118,82 140,96 162,112 182,124",R)+
    _zone(114,78,14,16,R)+
    _lvl(104,R,"Stop",120)+
    _lvl(122,R,"Entry↓",120)+
    _lvl(124,G,"Target",140),
    "strong pole down + bounce flag → continuation breakdown"),

"cup_handle": _svg(
    _lbl(42,116,"Cup",M)+_lbl(140,116,"Handle",M)+
    _pl("10,52 28,68 46,88 64,105 84,112 104,108 122,92 140,68 158,52",G)+
    _pl("158,52 168,62 178,58",M)+
    _pl("178,58 196,44 214,30 232,18",G)+
    _lvl(52,B,"Rim level",8,240)+
    _zone(174,50,14,16,G)+
    _lvl(20,G,"Target",192)+
    _lbl(178,48,"Entry↑",B),
    "U-shaped base + small handle → breakout above rim"),

"support_resistance": _svg(
    _pl("10,58 32,80 50,52 70,80 90,50 110,80 132,48",G)+
    _pl("132,48 155,80 176,96 198,80 218,100",M)+
    _lvl(80,B,"Level",8,270)+
    _lbl(18,75,"Support",G)+_lbl(158,75,"Resistance",R)+
    '<line x1="138" y1="50" x2="138" y2="115" stroke="'+M+'" stroke-width=".6" stroke-dasharray="2,2"/>'+
    _lbl(138,120,"Break →",M)+
    _lbl(140,75,"Flip",B),
    "support flips to resistance once broken — roles reverse"),
}

VOLMAN_SETUPS = [
    ("Double Doji (DD)", ["volman","with-trend"],
     "What is the <b>Double Doji (DD)</b> setup?",
     f"""<span class='tag'>Volman · With-Trend</span><h3>Double Doji (DD)</h3>
{_SETUP_SVGS['dd']}
<p>Two consecutive <b>doji or narrow-range candles</b> forming a tight pause in a trend.</p>
<ul><li>Best used <b>with the trend</b> — forms after a pullback to EMA</li>
<li>Signals buyer/seller balance before momentum resumes</li>
<li>Tighter dojis = more compressed energy = stronger break</li></ul>
<table><tr><th>Entry</th><td>Break of DD high (buy) / low (sell)</td></tr>
<tr><th>Stop</th><td>Other side of DD formation</td></tr>
<tr><th>Target</th><td>Next swing level or 2R</td></tr></table>"""),

    ("Second Break (SB)", ["volman","with-trend"],
     "What is the <b>Second Break (SB)</b> setup?",
     f"""<span class='tag'>Volman · With-Trend</span><h3>Second Break (SB)</h3>
{_SETUP_SVGS['sb']}
<p>Price tests a level, <b>fails</b>, pulls back, then makes a <b>second attempt</b> that succeeds.</p>
<ul><li>First break shakes out weak hands</li>
<li>Second break powered by stronger momentum</li>
<li>Usually more reliable than the first break</li></ul>
<table><tr><th>Entry</th><td>On break of second attempt</td></tr>
<tr><th>Stop</th><td>Below the pullback between the two attempts</td></tr>
<tr><th>Target</th><td>Measured move from consolidation</td></tr></table>"""),

    ("Block Break (BB)", ["volman","breakout"],
     "What is the <b>Block Break (BB)</b> setup?",
     f"""<span class='tag'>Volman · Breakout</span><h3>Block Break (BB)</h3>
{_SETUP_SVGS['bb']}
<p>Price consolidates in a <b>tight rectangular block</b> — clearly defined highs and lows.</p>
<ul><li>Draw a rectangle — price coils like a spring</li>
<li>Longer block = more potential energy</li>
<li>More traders see the same level → self-fulfilling breakout</li></ul>
<table><tr><th>Entry</th><td>Immediate break of block boundary</td></tr>
<tr><th>Stop</th><td>Opposite side of the block</td></tr>
<tr><th>Target</th><td>Block height projected from breakout</td></tr></table>"""),

    ("BB Squeeze", ["volman","breakout"],
     "What is the <b>BB Squeeze</b> (Bollinger Band Squeeze)?",
     f"""<span class='tag'>Volman · Breakout</span><h3>BB Squeeze</h3>
{_SETUP_SVGS['squeeze']}
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
     f"""<span class='tag'>Volman · Breakout</span><h3>Pattern Break Combi</h3>
{_SETUP_SVGS['combi']}
<p>A <b>Powerbar</b> (large directional candle) followed by an <b>inside bar</b> closing in the same direction.</p>
<ul><li>Powerbar = decisive momentum candle</li>
<li>Inside bar = pause and reload</li>
<li>Enter on break of inside bar in Powerbar's direction</li></ul>
<table><tr><th>Entry</th><td>Break of inside bar</td></tr>
<tr><th>Stop</th><td>Opposite side of inside bar</td></tr>
<tr><th>Target</th><td>Next key level, 1.5–2R</td></tr></table>"""),

    ("First Break (FB)", ["volman","breakout"],
     "What is the <b>First Break (FB)</b> setup?",
     f"""<span class='tag'>Volman · Breakout</span><h3>First Break (FB)</h3>
{_SETUP_SVGS['fb']}
<p>The <b>initial breakout</b> of a key support, resistance, or consolidation boundary.</p>
<ul><li>Works best with a clean, obvious level</li>
<li>Higher success when level has been tested multiple times</li>
<li>Lower probability than SB — first breaks often fail</li>
<li>A failed FB sets up the SB trade</li></ul>"""),

    ("Tipping Point", ["volman","reversal"],
     "What is the <b>Tipping Point</b> technique?",
     f"""<span class='tag'>Volman · Reversal</span><h3>Tipping Point</h3>
{_SETUP_SVGS['tipping']}
<p>A <b>price exhaustion signal</b> — the market has pushed too far and is about to reverse.</p>
<ul><li>Occurs at major S/R after an extended move</li>
<li>Signs: long wicks, doji at extremes, failed continuation</li>
<li>Counter-trend — use sparingly, higher risk</li></ul>
<blockquote>Volman uses this sparingly. The trend is your friend until the tipping point proves otherwise.</blockquote>"""),

    ("EMA as Dynamic S/R", ["volman","concept"],
     "How does Volman use the <b>EMA</b> in his setups?",
     f"""<span class='tag'>Volman · Core Concept</span><h3>EMA as Dynamic Support/Resistance</h3>
{_SETUP_SVGS['ema_sr']}
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

    # ── Chart Patterns ────────────────────────────────────────────────────────
    ("Double Top",["chart-patterns","bearish"],
     "<h2>📊 Double Top</h2><p class='hint'>What does this pattern signal?</p>",
     f"""<span class='tag bearish'>▼ Bearish Reversal</span><h3>Double Top</h3>
{_CHART_SVGS['double_top']}
<p>Two peaks at the <b>same resistance</b> — sellers reject price twice at the same level.</p>
<ul><li>Entry: break <b>below neckline</b> (valley between peaks)</li><li>Stop: above second peak</li><li>Target: neckline − (resistance − neckline)</li></ul>
<a href="https://www.tradingview.com/ideas/doubletop/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),

    ("Double Bottom",["chart-patterns","bullish"],
     "<h2>📊 Double Bottom</h2><p class='hint'>What does this pattern signal?</p>",
     f"""<span class='tag bullish'>▲ Bullish Reversal</span><h3>Double Bottom</h3>
{_CHART_SVGS['double_bottom']}
<p>Two troughs at the <b>same support</b> — buyers defend the same floor twice.</p>
<ul><li>Entry: break <b>above neckline</b></li><li>Stop: below second trough</li><li>Target: neckline + (neckline − support)</li></ul>
<a href="https://www.tradingview.com/ideas/doublebottom/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),

    ("Head & Shoulders",["chart-patterns","bearish"],
     "<h2>📊 Head & Shoulders</h2><p class='hint'>What does this pattern signal?</p>",
     f"""<span class='tag bearish'>▼ Bearish Reversal</span><h3>Head & Shoulders</h3>
{_CHART_SVGS['head_shoulders']}
<p>3 peaks: left shoulder, higher head, right shoulder. Signals end of uptrend.</p>
<ul><li>Entry: neckline break (LS/RS valley)</li><li>Stop: above right shoulder</li><li>Target: head height below neckline</li></ul>
<a href="https://www.tradingview.com/ideas/headandshoulders/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),

    ("Ascending Triangle",["chart-patterns","bullish"],
     "<h2>📊 Ascending Triangle</h2><p class='hint'>What does this pattern signal?</p>",
     f"""<span class='tag bullish'>▲ Bullish Continuation</span><h3>Ascending Triangle</h3>
{_CHART_SVGS['asc_triangle']}
<p>Flat resistance top + rising lows. Buyers making higher lows = increasing pressure.</p>
<ul><li>Entry: break above flat resistance</li><li>Stop: below last higher low</li><li>Target: triangle height added to breakout</li></ul>
<a href="https://www.tradingview.com/ideas/ascendingtriangle/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),

    ("Descending Triangle",["chart-patterns","bearish"],
     "<h2>📊 Descending Triangle</h2><p class='hint'>What does this pattern signal?</p>",
     f"""<span class='tag bearish'>▼ Bearish Continuation</span><h3>Descending Triangle</h3>
{_CHART_SVGS['desc_triangle']}
<p>Flat support bottom + falling highs. Sellers making lower highs = increasing pressure down.</p>
<ul><li>Entry: break below flat support</li><li>Stop: above last lower high</li><li>Target: triangle height subtracted from breakdown</li></ul>
<a href="https://www.tradingview.com/ideas/descendingtriangle/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),

    ("Symmetrical Triangle",["chart-patterns","neutral"],
     "<h2>📊 Symmetrical Triangle</h2><p class='hint'>What does this pattern signal?</p>",
     f"""<span class='tag'>◆ Continuation / Breakout</span><h3>Symmetrical Triangle</h3>
{_CHART_SVGS['sym_triangle']}
<p>Converging highs and lows. Neither side wins until the breakout — direction follows prior trend.</p>
<ul><li>Entry: break of either trendline (bias = prior trend)</li><li>Stop: opposite trendline</li><li>Target: widest point of triangle added to break</li></ul>
<a href="https://www.tradingview.com/ideas/symmetricaltriangle/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),

    ("Bull Flag",["chart-patterns","bullish"],
     "<h2>📊 Bull Flag</h2><p class='hint'>What does this pattern signal?</p>",
     f"""<span class='tag bullish'>▲ Bullish Continuation</span><h3>Bull Flag</h3>
{_CHART_SVGS['bull_flag']}
<p>Strong pole up + brief consolidation (flag). Breakout continues the up move.</p>
<ul><li>Entry: break above flag upper boundary</li><li>Stop: below flag lower boundary</li><li>Target: pole height added to breakout point</li></ul>
<a href="https://www.tradingview.com/ideas/bullflag/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),

    ("Bear Flag",["chart-patterns","bearish"],
     "<h2>📊 Bear Flag</h2><p class='hint'>What does this pattern signal?</p>",
     f"""<span class='tag bearish'>▼ Bearish Continuation</span><h3>Bear Flag</h3>
{_CHART_SVGS['bear_flag']}
<p>Strong pole down + brief consolidation (flag). Breakdown continues the down move.</p>
<ul><li>Entry: break below flag lower boundary</li><li>Stop: above flag upper boundary</li><li>Target: pole height subtracted from breakdown</li></ul>
<a href="https://www.tradingview.com/ideas/bearflag/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),

    ("Cup & Handle",["chart-patterns","bullish"],
     "<h2>📊 Cup & Handle</h2><p class='hint'>What does this pattern signal?</p>",
     f"""<span class='tag bullish'>▲ Bullish Continuation</span><h3>Cup &amp; Handle</h3>
{_CHART_SVGS['cup_handle']}
<p>U-shaped base (cup) + small pullback (handle). Breakout above cup rim signals continuation.</p>
<ul><li>Entry: break above rim level</li><li>Stop: below handle low</li><li>Target: cup depth added to rim</li></ul>
<a href="https://www.tradingview.com/ideas/cupandhandle/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),

    ("S/R Role Reversal",["chart-patterns","neutral"],
     "<h2>📊 S/R Role Reversal</h2><p class='hint'>What happens when support breaks?</p>",
     f"""<span class='tag'>◆ Key Concept</span><h3>Support/Resistance Role Reversal</h3>
{_CHART_SVGS['support_resistance']}
<p>Once a support breaks, it <b>flips to resistance</b>. Once resistance breaks, it becomes support.</p>
<ul><li>Retest of the flipped level = high-probability entry</li><li>The more times a level was tested, the stronger it becomes when flipped</li></ul>
<a href="https://www.tradingview.com/ideas/supportandresistance/" target="_blank" class="tv-btn">See Real Examples ↗</a>"""),
]


COMPARISONS = [
    # (display name, left pattern key, right pattern key, back_html)
    ("Tweezer Tops vs Tweezer Bottoms",
     "Tweezer Tops", "Tweezer Bottoms",
     """<h3>Tweezer Tops vs Tweezer Bottoms</h3>
<table><tr><th></th><th>🔴 Tweezer Tops</th><th>🟢 Tweezer Bottoms</th></tr>
<tr><td>Appears after</td><td>Uptrend</td><td>Downtrend</td></tr>
<tr><td>Shared feature</td><td colspan='2'>Two candles touching the same level</td></tr>
<tr><td>Shared level</td><td>Same <b>high</b> (resistance)</td><td>Same <b>low</b> (support)</td></tr>
<tr><td>Signal</td><td>Bearish reversal ↓</td><td>Bullish reversal ↑</td></tr>
<tr><td>Why it works</td><td>Sellers reject the high twice</td><td>Buyers defend the low twice</td></tr></table>
<blockquote>Memory: <b>Tops = ceiling</b> (can't go higher) → sell. <b>Bottoms = floor</b> (can't go lower) → buy.</blockquote>"""),

    ("Hammer vs Hanging Man",
     "Hammer", "Hanging Man",
     """<h3>Hammer vs Hanging Man</h3>
<p>Identical shape — the difference is <b>where it appears</b> in the trend.</p>
<table><tr><th></th><th>🟢 Hammer</th><th>🔴 Hanging Man</th></tr>
<tr><td>Appears after</td><td>Downtrend</td><td>Uptrend</td></tr>
<tr><td>Shape</td><td colspan='2'>Small body at top, long lower wick (≥2×)</td></tr>
<tr><td>Signal</td><td>Bullish reversal ↑</td><td>Bearish warning ↓</td></tr>
<tr><td>Logic</td><td>Sellers pushed down, buyers recovered → strength</td><td>Sellers appeared — trend may be ending</td></tr></table>
<blockquote>Same candle, opposite meaning. Always check the <b>trend before the candle</b>.</blockquote>"""),

    ("Inverted Hammer vs Shooting Star",
     "Inverted Hammer", "Shooting Star",
     """<h3>Inverted Hammer vs Shooting Star</h3>
<p>Again — same shape, opposite contexts.</p>
<table><tr><th></th><th>🟢 Inverted Hammer</th><th>🔴 Shooting Star</th></tr>
<tr><td>Appears after</td><td>Downtrend</td><td>Uptrend</td></tr>
<tr><td>Shape</td><td colspan='2'>Small body at bottom, long upper wick</td></tr>
<tr><td>Signal</td><td>Bullish reversal ↑</td><td>Bearish reversal ↓</td></tr>
<tr><td>Logic</td><td>Buyers tested highs — interest returning</td><td>Buyers pushed up but sellers took over</td></tr></table>
<blockquote>Shooting Star: the price "shot up" but came back down — sellers won the session.</blockquote>"""),

    ("Dragonfly Doji vs Gravestone Doji",
     "Dragonfly Doji", "Gravestone Doji",
     """<h3>Dragonfly Doji vs Gravestone Doji</h3>
<table><tr><th></th><th>🟢 Dragonfly</th><th>🔴 Gravestone</th></tr>
<tr><td>Shape</td><td>T — long lower wick, no upper</td><td>⊥ — long upper wick, no lower</td></tr>
<tr><td>Signal</td><td>Bullish reversal (at lows)</td><td>Bearish reversal (at highs)</td></tr>
<tr><td>Story</td><td>Sellers pushed down, buyers recovered all</td><td>Buyers pushed up, sellers took all back</td></tr>
<tr><td>Best at</td><td>Support zones</td><td>Resistance zones</td></tr></table>
<blockquote>Memory: Dragonfly = <b>rising</b> creature → bullish. Gravestone = <b>death</b> of uptrend → bearish.</blockquote>"""),

    ("Bullish Engulfing vs Bearish Engulfing",
     "Bullish Engulfing", "Bearish Engulfing",
     """<h3>Bullish Engulfing vs Bearish Engulfing</h3>
<p>A large candle completely swallows the previous one — but direction is everything.</p>
<table><tr><th></th><th>🟢 Bullish Engulfing</th><th>🔴 Bearish Engulfing</th></tr>
<tr><td>Pattern</td><td>Small red → large green engulfs</td><td>Small green → large red engulfs</td></tr>
<tr><td>Appears after</td><td>Downtrend</td><td>Uptrend</td></tr>
<tr><td>Signal</td><td>Strong bullish reversal ↑</td><td>Strong bearish reversal ↓</td></tr>
<tr><td>Strength</td><td colspan='2'>Larger the engulfing body, stronger the signal</td></tr></table>
<blockquote>The engulfing candle = new side taking full control. Watch volume — high vol confirms.</blockquote>"""),

    ("Morning Star vs Evening Star",
     "Morning Star", "Evening Star",
     """<h3>Morning Star vs Evening Star</h3>
<p>3-candle reversal patterns — mirror images of each other.</p>
<table><tr><th></th><th>🟢 Morning Star</th><th>🔴 Evening Star</th></tr>
<tr><td>Candle 1</td><td>Long bearish</td><td>Long bullish</td></tr>
<tr><td>Candle 2</td><td>Small star (gap down)</td><td>Small star (gap up)</td></tr>
<tr><td>Candle 3</td><td>Long bullish recovery</td><td>Long bearish reversal</td></tr>
<tr><td>Signal</td><td>Bullish reversal ↑ at bottom</td><td>Bearish reversal ↓ at top</td></tr></table>
<blockquote>Morning Star = dawn after darkness → bullish. Evening Star = dusk before night → bearish.</blockquote>"""),

    ("Bullish Harami vs Bearish Harami",
     "Bullish Harami", "Bearish Harami",
     """<h3>Bullish Harami vs Bearish Harami</h3>
<p>"Harami" = pregnant in Japanese — small candle inside the large candle's body.</p>
<table><tr><th></th><th>🟢 Bullish Harami</th><th>🔴 Bearish Harami</th></tr>
<tr><td>Candle 1</td><td>Large bearish</td><td>Large bullish</td></tr>
<tr><td>Candle 2</td><td>Small bullish inside candle 1</td><td>Small bearish inside candle 1</td></tr>
<tr><td>Signal</td><td>Potential bullish reversal</td><td>Potential bearish reversal</td></tr>
<tr><td>vs Engulfing</td><td colspan='2'>Weaker signal — needs confirmation candle</td></tr></table>
<blockquote>Harami is a warning, not a trigger. Wait for the next candle to confirm direction.</blockquote>"""),

    ("Piercing Line vs Dark Cloud Cover",
     "Piercing Line", "Dark Cloud Cover",
     """<h3>Piercing Line vs Dark Cloud Cover</h3>
<p>Both are 2-candle reversals where the second candle closes past the <b>midpoint</b> of the first.</p>
<table><tr><th></th><th>🟢 Piercing Line</th><th>🔴 Dark Cloud Cover</th></tr>
<tr><td>Candle 1</td><td>Long bearish</td><td>Long bullish</td></tr>
<tr><td>Candle 2</td><td>Opens below low, closes <b>above midpoint</b> of candle 1</td><td>Opens above high, closes <b>below midpoint</b> of candle 1</td></tr>
<tr><td>Signal</td><td>Bullish reversal ↑</td><td>Bearish reversal ↓</td></tr>
<tr><td>Key rule</td><td colspan='2'>Must close past the 50% midpoint — otherwise ignore</td></tr></table>"""),

    ("Doji vs Spinning Top",
     "Doji", "Spinning Top",
     """<h3>Doji vs Spinning Top</h3>
<p>Both signal indecision — the difference is the <b>body size</b>.</p>
<table><tr><th></th><th>Doji</th><th>Spinning Top</th></tr>
<tr><td>Body</td><td>Nearly zero (open ≈ close)</td><td>Small but visible body</td></tr>
<tr><td>Wicks</td><td>Any length</td><td>Roughly equal length both sides</td></tr>
<tr><td>Signal strength</td><td>Stronger indecision</td><td>Moderate indecision</td></tr>
<tr><td>Meaning</td><td colspan='2'>Neither bulls nor bears in full control — reversal possible</td></tr></table>
<blockquote>Both matter most after a strong trend. Alone they're warnings — combine with S/R and volume.</blockquote>"""),
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
    for pair, left, right, back in COMPARISONS:
        cards.append({"id": uid(f"compare_{pair}"), "deck": "Compare", "deck_icon": "⚖️",
                      "front_type": "text",
                      "front_html": f'<h2>⚖️ {pair}</h2><p class="hint">What\'s the key difference — shape, context, or signal?</p>',
                      "back_html": back, "tags": ["comparison"],
                      "comparison": [left, right]})
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
