"""Draws static/figures/mockroot-canyon.svg (desert varnish post, Figure 1)."""
import math, random
random.seed(11)
W, H = 1000, 540
K = "#111"
F = 'font-family="Helvetica, Arial, sans-serif"'
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
     f'<rect width="{W}" height="{H}" fill="#fff"/>',
     '<style>text{paint-order:stroke;stroke:#fff;stroke-width:4px;stroke-linejoin:round}</style>',
     '<defs><pattern id="bed" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="10" stroke="#111" stroke-width="0.8"/></pattern>',
     '<marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,1 L9,5 L0,9" fill="none" stroke="#111" stroke-width="1.4"/></marker></defs>']
top, base, etop = 150, 465, 118
def wl(y): return 600 + 7 * math.sin(y / 21) + (y - top) * 0.025
def wr(y): return 670 + 6 * math.sin(y / 17 + 1.3) - (y - top) * 0.02
ys = list(range(top, base + 1, 5))
west = f'M40,{base} L40,{top+6} C220,{top-2} 430,{top+4} {wl(top):.1f},{top} ' + " ".join(f'L{wl(y):.1f},{y}' for y in ys) + ' Z'
east = (f'M{wr(top):.1f},{top} L{wr(top)-2:.1f},{etop+20} L690,{etop+2} '
        f'C694,{etop+16} 712,{etop+26} 716,{etop+2} C800,{etop-2} 900,{etop+4} 960,{etop} L960,{base} '
        + " ".join(f'L{wr(y):.1f},{y}' for y in reversed(ys)) + ' Z')
o.append(f'<clipPath id="cw"><path d="{west}"/></clipPath><clipPath id="ce"><path d="{east}"/></clipPath>')
def strata(clip, xa, xb, y0, y1):
    out = []
    for yy in range(y0, y1, 34):
        out.append(f'<path clip-path="url(#{clip})" d="M{xa},{yy} C{xa+150},{yy-3} {xb-150},{yy+4} {xb},{yy+1}" fill="none" stroke="{K}" stroke-width="0.9"/>')
        x = xa + random.uniform(0, 30)
        while x < xb:
            L = random.uniform(22, 40)
            out.append(f'<line clip-path="url(#{clip})" x1="{x:.1f}" y1="{yy+1:.1f}" x2="{x+L:.1f}" y2="{yy+33:.1f}" stroke="{K}" stroke-width="0.45" stroke-opacity="0.7"/>')
            x += random.uniform(9, 15)
    return out
o.append(f'<path d="{west}" fill="#fff"/>'); o.append(f'<path d="{east}" fill="#fff"/>')
o += strata("cw", 40, 640, top + 8, base); o += strata("ce", 640, 960, etop + 12, base)

# light geometry: sun -> through waterfall -> through the aperture, straight on into the room
sx, sy = 915, 52
wx = 642
ay = 252; ax = wl(ay)
px, py = wx, 198                      # where the ray crosses the waterfall
dx, dy = ax - px, ay - py             # direction of the ray after the waterfall
# room: ceiling and floor run from the aperture down-left, the ray enters between them
ang = math.atan2(dy, dx)
gap = 30                              # floor-to-ceiling separation (drawn, not to scale)
tunnel_len = 34
ex, ey = ax + tunnel_len * math.cos(ang) * 0 - tunnel_len, ay + 6       # inner end of the aperture tunnel
c2 = (ax - tunnel_len, ay + 16); f2 = (ax - tunnel_len, ay + 16 + gap)
c1 = (120, c2[1] + 62); f1 = (120, f2[1] + 62)
room = f'M{c1[0]},{c1[1]} L{c2[0]:.1f},{c2[1]} L{ax+1:.1f},{ay-7} L{ax+1:.1f},{ay+7} L{f2[0]:.1f},{f2[1]} L{f1[0]},{f1[1]} Z'
o.append(f'<path d="{room}" fill="#fff"/>')
o.append(f'<path d="{west}" fill="none" stroke="{K}" stroke-width="1.6"/>')
o.append(f'<path d="{east}" fill="none" stroke="{K}" stroke-width="1.6"/>')
# open the wall face at the aperture
o.append(f'<rect x="{ax-5:.1f}" y="{ay-6.5:.1f}" width="12" height="13" fill="#fff"/>')
o.append(f'<path d="M{c2[0]:.1f},{c2[1]} L{ax+1:.1f},{ay-7} M{f2[0]:.1f},{f2[1]} L{ax+1:.1f},{ay+7}" stroke="{K}" stroke-width="1.1"/>')
for (a, b) in ((c1, c2), (f1, f2)):
    o.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]:.1f}" y2="{b[1]}" stroke="{K}" stroke-width="3.2"/>')
o.append(f'<path d="M{c1[0]},{c1[1]} L{f1[0]},{f1[1]}" stroke="{K}" stroke-width="1"/>')
o.append(f'<rect x="40" y="{base}" width="920" height="40" fill="url(#bed)" stroke="{K}" stroke-width="1.6"/>')
# waterfall
for i in range(160):
    y = random.uniform(etop + 10, 400); x = wx + random.uniform(-5, 5)
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="0.9" fill="{K}"/>')
o.append(f'<path d="M{wx-6},{etop+8} C{wx-8},230 {wx-3},330 {wx-6},400 M{wx+6},{etop+8} C{wx+8},230 {wx+3},330 {wx+6},400" fill="none" stroke="{K}" stroke-width="0.8"/>')
# sun
o.append(f'<circle cx="{sx}" cy="{sy}" r="11" fill="none" stroke="{K}" stroke-width="1.3"/>')
for k in range(8):
    a = k * math.pi / 4
    o.append(f'<line x1="{sx+16*math.cos(a):.1f}" y1="{sy+16*math.sin(a):.1f}" x2="{sx+24*math.cos(a):.1f}" y2="{sy+24*math.sin(a):.1f}" stroke="{K}" stroke-width="1.2"/>')
# ray: one continuous dashed path sun -> waterfall -> aperture -> straight into the room -> bounces
def on(x, a, b): return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
# first hit: continue the ray direction until it meets the floor line
t = 0.0
x, y = ax, ay
while True:
    x += math.cos(ang) * -1 * 0 + dx / math.hypot(dx, dy) * 1.0
    y += dy / math.hypot(dx, dy) * 1.0
    if x < f2[0] and y >= on(x, f1, f2) - 2:
        break
    if x < 120: break
pts = [(sx - 14, sy + 10), (px, py), (ax, ay), (x, y)]
step = 58; top_next = True; cx_ = x
while True:
    cx_ -= step
    if cx_ < c1[0] + 18: break
    pts.append((cx_, on(cx_, c1, c2) + 3 if top_next else on(cx_, f1, f2) - 3))
    top_next = not top_next
o.append('<polyline points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f'" fill="none" stroke="{K}" stroke-width="1.1" stroke-dasharray="6 4"/>')
# arrowheads along the path
for (x1, y1), (x2, y2) in [(pts[0], pts[1]), (pts[2], pts[3]), (pts[4], pts[5])]:
    mx, my = x1 + (x2 - x1) * 0.6, y1 + (y2 - y1) * 0.6
    o.append(f'<path d="M{x1+(x2-x1)*0.55:.1f},{y1+(y2-y1)*0.55:.1f} L{mx:.1f},{my:.1f}" stroke="{K}" stroke-width="1.1" marker-end="url(#ar)"/>')
# labels
def lab(tx, ty, lx, ly, lines, anchor="start"):
    o.append(f'<line x1="{tx}" y1="{ty}" x2="{lx:.1f}" y2="{ly:.1f}" stroke="{K}" stroke-width="0.7"/>')
    dx_ = 3 if anchor == "start" else -3
    for i, tt in enumerate(lines):
        o.append(f'<text x="{tx+dx_}" y="{ty-5-13*(len(lines)-1-i)}" {F} font-size="12" fill="{K}" text-anchor="{anchor}">{tt}</text>')
lab(520, 206, ax - 2, ay - 9, ["Western wall", "aperture (WWA)"], "end")
lab(560, 92, wx - 2, 180, ["Waterfall", "(hypothesized)"], "end")
lab(770, 92, 705, etop + 12, ["Southern aperture", "feature (SAF)"])
o.append(f'<text x="{sx}" y="{sy+42}" {F} font-size="12" fill="{K}" text-anchor="middle">Sun</text>')
lab(330, 236, 300, on(300, c1, c2) - 3, ["Ceiling (desert varnish coated)"], "end")
lab(250, 410, 300, on(300, f1, f2) + 3, ["Floor (desert varnish coated)"])
o.append(f'<text x="48" y="{base+30}" {F} font-size="11" fill="{K}">Bedrock</text>')
o.append(f'<text x="48" y="{top-10}" {F} font-size="11" fill="{K}" font-style="italic">Navajo Sandstone</text>')
o.append(f'<text x="{W-40}" y="{H-12}" {F} font-size="11" fill="{K}" text-anchor="end" font-style="italic">Not to scale</text>')
o.append('</svg>')
open(__file__.replace("tools/draw_canyon.py", "static/figures/mockroot-canyon.svg"), "w").write("\n".join(o))
