"""Builds the blog figures in the TwelveLabs diagram style (tl.css). Run: python3 build.py && ./render.sh"""
import pathlib

HEAD = '''<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fragment+Mono&family=Geist:wght@400;450;500;550;600&display=block" rel="stylesheet">
<link rel="stylesheet" href="tl.css"><style>body{{height:{h}px}}</style></head><body>
'''

def tag(x, y, text, kind="", mono=False):
    cls = ("tag " + kind).strip()
    style = f"left:{x}px;top:{y}px" + (';font-family:"Fragment Mono",monospace;font-size:14px' if mono else "")
    return f'<span class="{cls}" style="{style}">{text}</span>'

def item(x, y, w, h, title, sub="", fill=False, mono=False, extra="", kind=""):
    t = f'<div class="t{" mono" if mono else ""}">{title}</div>'
    s = f'<div class="s">{sub}</div>' if sub else ""
    return f'<div class="item{" fill" if fill else ""}{(" " + kind) if kind else ""}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{t}{s}{extra}</div>'

def group(x, y, w, h, label, dash=False, tagkind="fill", tint=""):
    cls = "grp" + (" dash" if dash else "") + ((" " + tint) if tint else "")
    return f'<div class="{cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>' + tag(x + 20, y - 15, label, tagkind)

def legend(x, y, w=None, only=None):
    keys = [("TwelveLabs", "var(--ink)"), ("Pixeltable", "var(--px)"), ("Python app code", "var(--py)"), ("Browser", "var(--fe)")]
    keys = [k for k in keys if only is None or k[0] in only]
    style = f"left:{x}px;top:{y}px" + (f";width:{w}px;flex-wrap:wrap;row-gap:10px" if w else "")
    return f'<div class="legend" style="{style}">' + "".join(f'<span><i style="background:{c}"></i>{k}</span>' for k, c in keys) + "</div>"

def note(x, y, w, text, size=16, color="var(--ink-2)"):
    return f'<div class="note" style="left:{x}px;top:{y}px;width:{w}px;font-size:{size}px;color:{color}">{text}</div>'

def line(*pts, dots=True):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    out = f'<path class="l" d="{d}"/>'
    if dots:
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        out += f'<circle class="d" cx="{x0}" cy="{y0}" r="3.5"/><circle class="d" cx="{x1}" cy="{y1}" r="3.5"/>'
    return out

def timeline(x, y, w, h, cuts, hot=(), play=True):
    """Outlined rounded bar split at relative cuts; scenes in `hot` are filled black. Returns svg and scene centers."""
    r = h / 2; out = []; px = x
    if play:
        out += [f'<circle class="o" cx="{x + r}" cy="{y + r}" r="{r - 1.5}"/>',
                f'<path class="d" d="M{x + r - h*.1},{y + r - h*.17} L{x + r + h*.17},{y + r} L{x + r - h*.1},{y + r + h*.17} Z"/>']
        px = x + h + h * .2
    bw = w - (px - x); pts = [0] + list(cuts) + [1]; centers = {}; fills = []
    out.append(f'<rect class="o" x="{px}" y="{y}" width="{bw}" height="{h}" rx="{r}"/>')
    for c in cuts:
        cx = px + c * bw
        out.append(f'<line class="l" x1="{cx}" y1="{y + h*.24}" x2="{cx}" y2="{y + h*.76}" style="stroke:#a9a5a2"/>')
    inset = max(2.5, h * .12)
    for i in range(len(pts) - 1):
        a, b = px + pts[i] * bw, px + pts[i + 1] * bw
        centers[i] = ((a + b) / 2, y, y + h)
        if i in hot:
            fh = h - 2 * inset
            fills.append(f'<rect class="f" x="{a + inset*.7}" y="{y + inset}" width="{b - a - 1.4*inset}" height="{fh}" rx="{fh/2}"/>')
    return "".join(out + fills), centers

def page(name, title, h, html, svg):
    doc = HEAD.format(title=title, h=h) + html + f'<svg class="art" width="1200" height="{h}">{svg}</svg></body></html>'
    pathlib.Path(name).write_text(doc)

# ---------------- Figure 1: architecture ----------------
h, s = [], []
h += [group(24, 40, 320, 470, "Browser", tagkind="fe"), group(424, 220, 352, 480, "Backend", tagkind=""), group(856, 40, 320, 660, "TwelveLabs")]
tl, _ = timeline(62, 154, 244, 26, [.18, .33, .5, .62, .8])
h += [item(44, 80, 280, 120, "Video player", "Plays each video over HLS", extra='<div style="height:34px"></div>', kind="fe")]
s.append(tl)
h += [item(44, 290, 280, 80, "Pages", "Home, Watch, Creator, Search", kind="fe"),
      item(44, 392, 280, 96, "Subscriptions and watch history", "Saved in the browser", kind="fe"),
      item(444, 280, 312, 90, "FastAPI routes", "Search, recommendations, ranking, and explanations", kind="py")]
h += [f'<div class="grp" style="left:444px;top:420px;width:312px;height:260px;background:var(--px)"></div>',
      tag(464, 405, "Pixeltable", "px"),
      '<div class="abs" style="left:464px;top:440px;width:272px">'
      '<div class="row"><div class="mono" style="font-size:16px">videos</div><div class="note" style="position:static;font-size:15px">One row per video, with its topic, style, tone, and scene cuts</div></div>'
      '<div class="row"><div class="mono" style="font-size:16px">video_scenes</div><div class="note" style="position:static;font-size:15px">One row per scene clip</div></div>'
      '<div class="row"><div style="font-size:16px;font-weight:550">Embedding indexes</div><div class="note" style="position:static;font-size:15px">Scene vectors and title vectors</div></div></div>']
h += [item(876, 96, 280, 88, "Assets", "Full videos and HLS streams", fill=True),
      item(876, 436, 280, 96, "Pegasus", "Topic, style, and tone, once per video", fill=True),
      item(876, 556, 280, 124, "Marengo", "A vector for each scene clip, each title, and each search query", fill=True)]
s += [line((876, 140), (324, 140)), line((324, 330), (444, 330)), line((600, 370), (600, 420)),
      line((756, 478), (876, 478)), line((756, 630), (876, 630))]
h += [tag(536, 125, "HLS stream"), tag(357, 315, "JSON")]
h += [note(614, 382, 120, "queries", 15), legend(44, 566, 300)]
page("fig1-architecture.html", "Figure 1", 724, "".join(h), "".join(s))

# ---------------- Figure 2: what happens on insert ----------------
h, s = [], []
h += [item(24, 270, 170, 96, "Assets", "TwelveLabs", fill=True),
      item(280, 254, 160, 128, "videos", "A new row with the video's metadata and its file", mono=True, kind="px"),
      group(462, 40, 714, 520, "Pixeltable runs these steps on insert", tagkind="px", tint="px")]
h += [note(204, 290, 76, '<span class="mono" style="font-size:13.5px;color:var(--ink)">load.py</span>', 14)]
h += [item(852, 112, 130, 92, "Pegasus", "Analyze API", fill=True),
      item(1006, 112, 150, 92, "Topic, style, tone", "Three columns", kind="px"),
      item(484, 274, 140, 88, "Scene detection", "Cut times", kind="px"),
      item(648, 262, 180, 112, "video_scenes", "One row per clip", mono=True, extra='<div style="height:22px"></div>', kind="px"),
      item(852, 274, 130, 250, "Marengo", "Embed API", fill=True),
      item(1006, 274, 150, 88, "Scene index", "A vector per clip", kind="px"),
      item(1006, 434, 150, 88, "Title index", "A vector per title", kind="px")]
tl, _ = timeline(664, 338, 148, 18, [.22, .4, .63, .8], play=False)
s.append(tl)
s += [line((194, 318), (280, 318)), line((440, 318), (448, 318), dots=False),
      '<path class="l" d="M448,158 V478"/>',
      line((448, 158), (852, 158)), line((448, 318), (484, 318)), line((448, 478), (852, 478)),
      line((624, 318), (648, 318)), line((828, 318), (852, 318)),
      line((982, 158), (1006, 158)), line((982, 318), (1006, 318)), line((982, 478), (1006, 478))]
h += [note(500, 128, 330, "sends the video's ID", 15), note(500, 448, 330, "sends the title text", 15)]
h += [legend(24, 470, only=("TwelveLabs", "Pixeltable")), note(484, 588, 690, "For each new video: one Analyze call, one title embedding, and one embedding per scene clip.", 16)]
page("fig2-insert.html", "Figure 2", 640, "".join(h), "".join(s))

# ---------------- Figure 4: how a For You row is built ----------------
h, s = [], []
cols = [24, 264, 504, 744, 984]; W = 192
heads = ["Watch history", "Stored scene vectors", "Similar scenes", "Creator mix", "Reason"]
caps = ["The browser sends the videos you watched. The app uses the last 5.",
        "Up to 2 per video, saved when the video was inserted. No TwelveLabs call.",
        "The scene index finds the closest scenes in the catalog. Each video keeps its best match.",
        "70% from creators you subscribe to, 30% from new ones. At most 2 per creator.",
        "Built from the stored topic, style, and tone of both videos."]
owners = ["Browser", "Pixeltable", "Pixeltable", "Python", "Python"]
for i, x in enumerate(cols):
    h += [f'<div class="num" style="left:{x}px;top:28px">{i + 1}</div>', f'<div class="head" style="left:{x + 38}px;top:30px">{heads[i]}</div>',
          note(x, 300, W, caps[i], 15.5), tag(x, 420, owners[i], {"Browser": "fe", "Pixeltable": "px", "Python": "py"}[owners[i]])]
watched_cuts = [[.2, .45, .7], [.3, .55, .8], [.15, .4, .62, .85], [.25, .5, .75], [.35, .6, .82]]
pairs = [{0, 2}, {1, 3}, {0, 3}, {1, 3}, {0, 2}]
for r in range(5):
    y = 86 + r * 40
    a, _ = timeline(cols[0], y, W, 24, watched_cuts[r]); s.append(a)
    b, _ = timeline(cols[1], y, W, 24, watched_cuts[r], pairs[r]); s.append(b)
cat_cuts = [[.3, .6], [.2, .5, .75], [.4, .7], [.25, .55, .8], [.35, .65]]
cat_hot = [{1}, {2}, {0}, {1}, {2}]
for r in range(5):
    c, _ = timeline(cols[2], 86 + r * 40, W, 24, cat_cuts[r], cat_hot[r]); s.append(c)
for k in range(10):
    x = cols[3] + (k % 5) * 38; y = 112 + (k // 5) * 44
    s.append(f'<rect class="o" x="{x}" y="{y}" width="30" height="30" rx="8"' + (' style="fill:var(--py)"' if k < 7 else '') + '/>')
h += [note(cols[3], 210, W, "7 subscribed (filled), 3 new", 14.5)]
h += [f'<div class="item py" style="left:{cols[4]}px;top:96px;width:{W}px;height:150px;justify-content:center">'
      '<div style="font-size:15px;line-height:1.45">Because you watched \'…\' — Similar interview format · Matching serious tone</div></div>']
for a, b in zip(cols, cols[1:]):
    s.append(line((a + W + 10, 176), (b - 10, 176)))
h += [note(24, 474, 1150, "A viewer with no watch history gets the newest videos instead, with subscribed creators first.", 16.5, "var(--ink)")]
page("fig4-for-you.html", "Figure 4", 516, "".join(h), "".join(s))
print("built fig1, fig2, fig4")
