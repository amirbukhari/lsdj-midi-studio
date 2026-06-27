#!/usr/bin/env python3
"""Hand-built delonix logo: real circle, radial-gradient glow, drawn phoenix-tree,
real-font wordmark + tagline. Geometry generated for clean, consistent curves."""
import math, random

W, H = 1448, 1086
CX, CY, R = 724, 367, 273          # emblem circle (measured from source)
ORANGE = "#EB4705"
ORANGE_HI = "#FF7A2A"
WHITE = "#FFFFFF"
random.seed(7)

def fmt(n): return f"{n:.1f}"

paths = []   # (d, attrs) collected into groups manually below
tree_branches = []
tree_nodes = []
root_paths = []
root_nodes = []
feathers = []

# ---------- TREE BRANCHES (upper-left, organic, white, orange berries) ----------
def branch(x, y, ang, length, width, depth):
    if depth <= 0 or length < 12:
        # berry at tip
        tree_nodes.append((x, y, max(3.0, width*1.6), depth))
        return
    # slight curve along the branch
    ex = x + math.cos(ang) * length
    ey = y + math.sin(ang) * length
    # control point bows the branch a little
    bow = length * 0.18 * random.uniform(-1, 1)
    mx = (x+ex)/2 + math.cos(ang+math.pi/2)*bow
    my = (y+ey)/2 + math.sin(ang+math.pi/2)*bow
    tree_branches.append((f"M{fmt(x)},{fmt(y)} Q{fmt(mx)},{fmt(my)} {fmt(ex)},{fmt(ey)}", width))
    # occasionally a small berry mid-branch
    n = random.randint(2, 3)
    for i in range(n):
        spread = random.uniform(0.35, 0.75)
        na = ang - spread + 2*spread*(i/(n-1) if n > 1 else 0.5)
        na += random.uniform(-0.12, 0.12)
        branch(ex, ey, na, length*random.uniform(0.62, 0.78), max(1.2, width*0.7), depth-1)

# trunk fork point where tree springs from the phoenix body (upper center-left)
fork = (700, 312)
# main upward-left sweep of branches (up and to the left only)
for a in (-2.7, -2.45, -2.2, -1.95, -1.72):
    branch(fork[0], fork[1], a, random.uniform(72, 94), 3.2, 4)

# ---------- ROOTS (lower, circuit-trace style, white, ring nodes) ----------
def root(x, y, ang, length, depth):
    # circuit trace: a couple of straight runs with a kink, ending in a ring node
    segs = []
    cx, cy = x, y
    runs = random.randint(2, 3)
    for r_i in range(runs):
        seg_len = length * (0.55 if r_i == 0 else random.uniform(0.4, 0.7))
        nx = cx + math.cos(ang) * seg_len
        ny = cy + math.sin(ang) * seg_len
        segs.append((nx, ny))
        cx, cy = nx, ny
        ang += random.uniform(-0.5, 0.5)
    d = f"M{fmt(x)},{fmt(y)} " + " ".join(f"L{fmt(px)},{fmt(py)}" for px, py in segs)
    root_paths.append(d)
    root_nodes.append((cx, cy))
    if depth > 0 and length > 60:
        branch_ang = ang + random.choice([-1, 1]) * random.uniform(0.4, 0.8)
        bx, by = segs[0]
        root(bx, by, branch_ang, length*0.6, depth-1)

base = (712, 518)   # where body meets roots
# angles in (0, pi) point downward (image y grows down); fan left->right
# kept short so the whole root system stays inside the ring (circle bottom y=640)
for a in (0.80, 1.05, 1.30, 1.84, 2.10, 2.34):
    root(base[0], base[1], a, random.uniform(80, 104), 1)
# straight central root drilling down
root_paths.append(f"M{fmt(base[0])},{fmt(base[1])} L713,590 L713,624")
root_nodes.append((713, 624))

# ---------- PHOENIX WING (right, orange flame feathers) ----------
def feather(bx, by, tx, ty, w, curve):
    mx, my = (bx+tx)/2, (by+ty)/2
    dx, dy = tx-bx, ty-by
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy/L, dx/L
    # asymmetric: top edge bows more for a flame look
    c1x, c1y = mx + nx*w + dx*curve*0.15, my + ny*w + dy*curve*0.15
    c2x, c2y = mx - nx*(w*0.55), my - ny*(w*0.55)
    return (f"M{fmt(bx)},{fmt(by)} Q{fmt(c1x)},{fmt(c1y)} {fmt(tx)},{fmt(ty)} "
            f"Q{fmt(c2x)},{fmt(c2y)} {fmt(bx)},{fmt(by)} Z")

pivot = (728, 415)
# long sweeping flame feathers fanning up and to the right (strong upward curl)
feather_specs = [
    # (tipx, tipy, width, curve)
    (806, 168, 24, 1.6),
    (852, 198, 29, 1.5),
    (898, 240, 31, 1.4),
    (930, 296, 31, 1.25),
    (938, 356, 29, 1.1),
    (918, 408, 24, 0.95),
    (872, 446, 20, 0.8),
    (820, 462, 16, 0.7),
]
for tx, ty, w, c in feather_specs:
    feathers.append(feather(pivot[0], pivot[1], tx, ty, w, c))
# small inner feathers near the body
for tx, ty, w in [(792, 286, 10), (800, 330, 10), (786, 232, 9)]:
    feathers.append(feather(pivot[0]+2, pivot[1]-14, tx, ty, w, 1.0))

# head plumes (three thin orange/white streamers up from the head)
plumes = []
hx, hy = 732, 306
# three plumes that splay outward and curl back, tapering to a point
for sway, dx, dy in [(-26, -34, -150), (-10, 4, -168), (16, 40, -150)]:
    c1x, c1y = hx + sway, hy - 52          # initial outward sway
    c2x, c2y = hx + dx*0.7 + 10, hy + dy*0.7  # curl back toward vertical
    tx, ty = hx + dx, hy + dy
    plumes.append(f"M{fmt(hx)},{fmt(hy)} C{fmt(c1x)},{fmt(c1y)} {fmt(c2x)},{fmt(c2y)} {fmt(tx)},{fmt(ty)}")

# ---------- PHOENIX BODY (white, S-curve from base to head) ----------
body = (
    "M712,520 "                        # base at root convergence
    "C690,470 700,430 712,392 "        # lower body rising
    "C720,366 706,344 712,322 "        # chest/neck
    "C716,308 724,300 716,300 "        # to head
)
# A filled slender body silhouette: trunk -> slim curving neck -> small head
body_fill = (
    "M704,520 "                        # base left
    "C700,470 706,430 712,398 "        # trunk rising
    "C705,372 708,348 720,330 "        # neck curves up-right then back
    "C726,320 722,310 730,306 "        # to nape
    "C742,303 746,315 738,323 "        # head crown
    "C733,329 726,330 721,333 "        # under-head
    "C719,352 717,376 721,398 "        # back of neck down
    "C726,432 728,472 722,520 "        # trunk right side
    "Z"
)
# beak (small triangle pointing left from head)
beak = "M722,329 L704,332 L723,338 Z"
# head eye
eye = (730, 318, 2.0)

def circle(cx, cy, r, **kw):
    a = " ".join(f'{k.replace("_","-")}="{v}"' for k, v in kw.items())
    return f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" {a}/>'

# ================= ASSEMBLE SVG =================
out = []
out.append(f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
out.append('<title>delonix logo</title>')
out.append(f'''<defs>
  <radialGradient id="halo" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{ORANGE}" stop-opacity="0.28"/>
    <stop offset="45%" stop-color="{ORANGE}" stop-opacity="0.10"/>
    <stop offset="100%" stop-color="{ORANGE}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{ORANGE}" stop-opacity="0.35"/>
    <stop offset="55%" stop-color="{ORANGE}" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="{ORANGE_HI}" stop-opacity="1"/>
  </linearGradient>
  <linearGradient id="wing" x1="0" y1="1" x2="1" y2="0">
    <stop offset="0%" stop-color="#C2380A"/>
    <stop offset="55%" stop-color="{ORANGE}"/>
    <stop offset="100%" stop-color="{ORANGE_HI}"/>
  </linearGradient>
  <linearGradient id="body" x1="0" y1="1" x2="0" y2="0">
    <stop offset="0%" stop-color="#FFFFFF"/>
    <stop offset="100%" stop-color="#FFE9DC"/>
  </linearGradient>
  <radialGradient id="line" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#FFD9B0"/>
    <stop offset="20%" stop-color="{ORANGE_HI}"/>
    <stop offset="100%" stop-color="{ORANGE}" stop-opacity="0"/>
  </radialGradient>
  <filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="6"/>
  </filter>
  <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="2.2"/>
  </filter>
</defs>''')

# background
out.append(f'<rect width="{W}" height="{H}" fill="#000000"/>')
# halo glow behind emblem
out.append(f'<circle cx="{CX}" cy="{CY}" r="{R+40}" fill="url(#halo)"/>')

# ring (soft underlayer + crisp ring)
out.append('<g id="ring">')
out.append(circle(CX, CY, R, fill="none", stroke="url(#ring)", stroke_width=5, opacity=0.35, filter="url(#soft)"))
out.append(circle(CX, CY, R, fill="none", stroke="url(#ring)", stroke_width=2.4))
out.append('</g>')

# emblem group with subtle glow
out.append('<g id="emblem" filter="url(#glow)">')

# wing (behind body)
out.append('<g id="wing" fill="url(#wing)">')
for f in feathers:
    out.append(f'<path d="{f}"/>')
out.append('</g>')

# tree branches
out.append(f'<g id="tree" fill="none" stroke="{WHITE}" stroke-linecap="round">')
for d, w in tree_branches:
    out.append(f'<path d="{d}" stroke-width="{fmt(w)}"/>')
out.append('</g>')
# tree berries (orange)
out.append('<g id="berries">')
for x, y, r, depth in tree_nodes:
    col = ORANGE if depth <= 1 else ORANGE_HI
    out.append(circle(x, y, r, fill=col))
out.append('</g>')

# roots (circuit traces)
out.append(f'<g id="roots" fill="none" stroke="{WHITE}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.92">')
for d in root_paths:
    out.append(f'<path d="{d}"/>')
out.append('</g>')
out.append(f'<g id="root-nodes" fill="#000000" stroke="{WHITE}" stroke-width="2">')
for x, y in root_nodes:
    out.append(circle(x, y, 6))
out.append('</g>')

# plumes
out.append(f'<g id="plumes" fill="none" stroke="{ORANGE_HI}" stroke-width="3" stroke-linecap="round">')
for d in plumes:
    out.append(f'<path d="{d}"/>')
out.append('</g>')

# phoenix body
out.append(f'<path id="body" d="{body_fill}" fill="url(#body)"/>')
out.append(f'<path id="beak" d="{beak}" fill="{ORANGE_HI}"/>')
out.append(circle(eye[0], eye[1], eye[2], fill="#000000"))

out.append('</g>')  # emblem

# ---------- WORDMARK ----------
# real font, centered; dot on i recolored orange
out.append(f'''<text x="{CX}" y="838" text-anchor="middle"
  font-family="Helvetica Neue, Arial, sans-serif" font-size="170" font-weight="300"
  letter-spacing="14" fill="{WHITE}">delonix</text>''')
# orange dot on the i (measured center ~899,732, r~9)
out.append(circle(899, 732, 9, fill=ORANGE))

# glow line under wordmark
out.append(f'<rect x="478" y="869" width="478" height="3" fill="url(#line)"/>')
out.append(f'<ellipse cx="717" cy="871" rx="60" ry="6" fill="url(#line)"/>')

# ---------- TAGLINE ----------
out.append(f'''<text x="{CX}" y="945" text-anchor="middle"
  font-family="Helvetica Neue, Arial, sans-serif" font-size="33" font-weight="500"
  letter-spacing="6" fill="{ORANGE}">SIMPLE, SUSTAINABLE,</text>''')
out.append(f'''<text x="{CX}" y="985" text-anchor="middle"
  font-family="Helvetica Neue, Arial, sans-serif" font-size="33" font-weight="500"
  letter-spacing="6" fill="{ORANGE}">SCALABLE, BILLING SYSTEM</text>''')

out.append('</svg>')

open("logo.svg", "w").write("\n".join(out))
print("wrote logo.svg")
