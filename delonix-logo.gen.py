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

# ---------- PHOENIX WING (right, overlapping flame feathers) ----------
def flame(bx, by, tx, ty, w, curl):
    """A tapered feather with a bulging leading edge curving to a clean pointed tip."""
    dx, dy = tx-bx, ty-by
    L = math.hypot(dx, dy) or 1
    ux, uy = dx/L, dy/L          # along feather
    nx, ny = -uy, ux             # perpendicular (leading-edge side = +n)
    # leading edge: bows out, then sweeps up into the tip with an upward curl
    l1x, l1y = bx + ux*L*0.28 + nx*w,        by + uy*L*0.28 + ny*w
    l2x, l2y = bx + ux*L*0.78 + nx*w*0.42,   by + uy*L*0.78 + ny*w*0.42 - curl
    # trailing edge: sweeps back to base with a gentle inward scoop
    t1x, t1y = bx + ux*L*0.55 - nx*w*0.16,   by + uy*L*0.55 - ny*w*0.16
    t2x, t2y = bx + ux*L*0.16 - nx*w*0.06,   by + uy*L*0.16 - ny*w*0.06
    return (f"M{fmt(bx)},{fmt(by)} "
            f"C{fmt(l1x)},{fmt(l1y)} {fmt(l2x)},{fmt(l2y)} {fmt(tx)},{fmt(ty)} "
            f"C{fmt(t1x)},{fmt(t1y)} {fmt(t2x)},{fmt(t2y)} {fmt(bx)},{fmt(by)} Z")

# Wide overlapping feathers fanning from a common shoulder; drawn back-to-front
# so each tucks under the next — together they tile into a gapless flame wing.
shoulder = (728, 392)
attach = [   # (tip_x, tip_y, width, curl)
    (806, 462, 30, 6),     # lowest / most horizontal
    (878, 446, 34, 12),
    (930, 404, 38, 18),
    (952, 344, 40, 24),    # mid, longest
    (944, 282, 40, 28),
    (910, 226, 38, 30),
    (858, 188, 34, 28),
    (804, 168, 28, 24),    # top, most vertical
    (760, 162, 22, 18),
]
# thin connective membrane hugging the shoulder so the roots converge cleanly
wing_base = ("M724,360 C724,330 726,308 728,300 "
             "C742,300 754,318 756,360 "
             "C758,404 748,440 730,452 "
             "C720,420 722,392 724,360 Z")
# slight vertical offset of bases so feathers don't all pinch one point
for i, (tx, ty, w, c) in enumerate(attach):
    by = shoulder[1] + (i - len(attach)/2) * 4
    feathers.append(flame(shoulder[0], by, tx, ty, w, c))

# head plumes (three thin orange/white streamers up from the head)
plumes = []
hx, hy = 744, 286
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
# Filled phoenix body with motion: tail base -> forward chest -> arched neck -> head
# Drawn as a single flowing silhouette (left edge = breast, right edge = back).
body_fill = (
    "M718,522 "                        # tail base, right
    "C700,486 690,452 696,416 "        # back lower, sweeping up
    "C699,398 706,386 700,372 "        # toward breast
    "C694,356 692,340 700,326 "        # breast pushes forward (left)
    "C705,316 712,312 716,304 "        # up the front of the neck
    "C719,298 716,290 721,286 "        # throat to chin
    "C725,280 736,278 742,282 "        # head: rises up-right
    "C751,287 752,298 746,304 "        # crown / back of head
    "C742,308 735,308 731,312 "        # nape
    "C726,322 729,340 726,356 "        # back of neck descending
    "C732,378 730,396 724,414 "        # back of body
    "C730,452 732,488 726,522 "        # back lower to tail
    "Z"
)
# open beak pointing up-left from the head
beak = "M721,289 L705,280 L722,296 Z"
# small crest tuft at the back of the head
crest = "M746,288 C758,278 766,280 770,272 C764,286 757,292 748,296 Z"
# head eye
eye = (732, 294, 2.0)

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

# wing (behind body): dark membrane base + overlapping flame feathers
out.append('<g id="wing">')
out.append(f'<path d="{wing_base}" fill="#8A2706"/>')
for i, f in enumerate(feathers):
    # alternate tone so overlapping feathers read as distinct licks of flame
    fill = "url(#wing)" if i % 2 == 0 else ORANGE
    out.append(f'<path d="{f}" fill="{fill}"/>')
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
out.append(f'<path id="crest" d="{crest}" fill="{ORANGE_HI}"/>')
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
