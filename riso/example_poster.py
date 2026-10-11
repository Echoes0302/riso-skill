"""Riso No.02 · 毛球球与乌鸦 · 2026.10.10
三色：荧光粉 → 金 → 蓝（满版）。毛球是挖出来的纸；乌鸦 = 蓝叠粉叠金 → 近黑。
学到的：满版底色、少色、大剪影、留白点细节；挖空 + 错位 = 白缝；绒面、轮印、擦痕。"""
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import riso_lib as R

R.setup(900, 1200, ss=2, seed=1002)
PK = R.Plate("fluo_pink")
G = R.Plate("gold")
B = R.Plate("bright_blue")

M = 34  # Riso 印不到纸边：留白边
frame = [(M, M), (900 - M, M), (900 - M, 1200 - M), (M, 1200 - M)]
B.poly(frame, 1.0)

def knock_all_but(pts, keep, plates=None):
    for p in (plates or (PK, G, B)):
        if p is not keep:
            p.poly(pts, mode="knock")

def clip_frame(pts):
    return [(min(max(x, M), 900 - M), min(max(y, M), 1200 - M)) for x, y in pts]

# ---------------- 月亮 + 星星 ----------------
moon = R.blob(712, 214, 76, 76, rough=0.02)
G.poly(moon); knock_all_but(moon, G)
def sparkle(cx, cy, r, plate):
    pts = []
    for i in range(16):
        a = math.pi * i / 8
        rr = r if i % 4 == 0 else (r * 0.42 if i % 2 == 0 else r * 0.2)
        if i % 2: rr = r * 0.16
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    plate.poly(pts); knock_all_but(pts, plate)
for x, y, r, p in ((560, 120, 22, PK), (812, 380, 16, PK), (120, 470, 18, PK), (300, 360, 12, G), (780, 560, 11, G), (90, 860, 14, PK)):
    sparkle(x, y, r, p)
for _ in range(26):  # 白点：只挖蓝
    x, y = random.uniform(M + 20, 880 - M), random.uniform(M + 20, 960)
    r = random.choice((2.5, 3, 4))
    B.poly(R.ellipse_pts(x, y, r, r, 14), mode="knock")

# ---------------- 金色小山 ----------------
hill = clip_frame(R.ellipse_pts(450, 1340, 660, 335, 160, rough=0.01))
G.poly(hill); knock_all_but(hill, G)
for _ in range(14):  # 粉色小草：粉叠金 → 珊瑚
    x = random.uniform(80, 820); y = random.uniform(1040, 1150)
    PK.line([(x, y), (x - 4, y - 14)], width=4); PK.line([(x + 6, y), (x + 8, y - 12)], width=4)

# ---------------- 毛球球：挖出来的纸 ----------------
bx, by, brx, bry = 440, 742, 268, 214
ball = R.scallop(bx, by, brx, bry, bumps=24, depth=0.11)
knock_all_but(ball, None)
shade = R.Plate("bright_blue")  # 阴影：一块干净的月牙，不用渐变
shade.poly(R.scallop(bx, by, brx, bry, bumps=24, depth=0.11), 0.2)
shade.poly(R.blob(bx - 46, by - 40, brx - 10, bry - 6, rough=0.02), mode="knock")
B.d = B.d * 0 + B.d
for _ in range(24):
    a, rr = random.uniform(0, 2 * math.pi), random.uniform(0.12, 0.78)
    qx, qy = bx + rr * brx * math.cos(a), by + rr * bry * math.sin(a)
    if qx < bx - brx + 140 and abs(qy - by - 20) < 120: continue
    if qy < by - bry + 70 and abs(qx - 480) < 120: continue
    st = random.uniform(0, 2 * math.pi)
    B.line(R.wobble_line(R.ellipse_pts(qx, qy, 15, 12, 14, start=st, end=st + 4.4), amp=0.6, per=4), width=5, density=0.3, mode="set")
import numpy as _np
B.d = _np.maximum(B.d, shade.d)
# 腿：粉，挖蓝
for lx in (-128, -66, 70, 130):
    x = bx + lx
    leg = [(x - 7, by + bry - 40), (x + 7, by + bry - 40), (x + 7, 1032), (x - 7, 1032)]
    PK.poly(leg); knock_all_but(leg, PK)
    hoof = R.blob(x + 3, 1034, 12, 7, rough=0.05)
    B.poly(hoof, 1.0); G.poly(hoof, mode="knock")

# ---------------- 小脸：粉 ----------------
fx, fy = bx - brx + 52, by + 34
face = R.blob(fx, fy, 42, 52, rough=0.03, rot=math.radians(12))
PK.poly(face)
for ex, er in ((fx - 52, -12), (fx + 50, 14)):
    ear = R.blob(ex, fy - 14, 25, 10, rough=0.04, rot=math.radians(er))
    PK.poly(ear); knock_all_but(ear, PK)
    G.poly(R.blob(ex, fy - 14, 13, 4.5, rot=math.radians(er)))
for ex in (fx - 15, fx + 15):
    e = R.ellipse_pts(ex, fy + 2, 10, 10, 24)
    PK.poly(e, mode="knock")
    B.poly(R.ellipse_pts(ex + 2, fy + 1, 5, 5.5, 18), 1.0)
B.line(R.wobble_line(R.ellipse_pts(fx, fy + 24, 9, 6, 12, start=0.4, end=2.7), amp=0.3, per=3), width=3.2)
for dx in (-30, -10, 10, 30):  # 刘海：在脸上挖出几团毛
    PK.poly(R.ellipse_pts(fx + dx, fy - 44, 16, 14, 30), mode="knock")

# ---------------- 乌鸦：站着，粗嘴平头，蓝叠粉 = 深藏青 ----------------
ox, oy, s = 486, 540, 1.12
def T(pts): return [(ox + x * s, oy + y * s) for x, y in pts]
body = T(R.ellipse_pts(8, -62, 52, 32, 40, rot=0.5))
neck = T(R.ellipse_pts(-20, -90, 27, 25, 30))
head = T([(-62, -112), (-52, -128), (-30, -133), (-14, -128), (-8, -112), (-14, -94), (-34, -88), (-56, -96)])  # 平顶
beak = T([(-56, -124), (-76, -123), (-95, -116), (-106, -106), (-88, -101), (-66, -98), (-54, -100)])
tail = T([(40, -54), (106, -16), (100, 2), (34, -34)])
crow = [body, neck, head, beak, tail]
for p in crow:
    PK.poly(p, 1.0); B.poly(p, 1.0); G.poly(p, 0.9)
for x0, x1 in ((-4, -9), (16, 13)):
    leg = T([(x0 - 2.5, -36), (x0 + 2.5, -36), (x1 + 2.5, 2), (x1 - 2.5, 2)])
    PK.poly(leg); B.poly(leg)
G.line(R.wobble_line(T([(-16, -80), (18, -70), (58, -40)]), amp=0.6), width=3)
G.line(R.wobble_line(T([(10, -56), (44, -34)]), amp=0.5), width=2.5)
eye = T(R.ellipse_pts(-36, -114, 6, 6, 20))
PK.poly(eye, mode="knock"); B.poly(eye, mode="knock")
pup = T(R.ellipse_pts(-37.5, -114, 3.2, 3.4, 16))
PK.poly(pup); B.poly(pup)
# 嘴里叼的笔：金杆粉尖
pa = math.radians(8)
ux, uy, vx, vy = math.cos(pa), math.sin(pa), -math.sin(pa), math.cos(pa)
pcx, pcy = ox - 84 * s, oy - 110 * s
def pp(t, w): return (pcx + ux * t + vx * w, pcy + uy * t + vy * w)
shaft = [pp(-40, -7), pp(40, -7), pp(40, 7), pp(-40, 7)]
tip = [pp(-40, -7), pp(-60, 0), pp(-40, 7)]
G.poly(shaft); knock_all_but(shaft, G)
PK.poly(tip); knock_all_but(tip, PK)
B.poly([pp(-52, -2.8), pp(-60, 0), pp(-52, 2.8)], 1.0)
B.line([pp(30, -7), pp(30, 7)], width=2.4)
# 脚陷进毛里：前面几团毛盖住爪子
for x in (ox - 44, ox - 12, ox + 22, ox + 52):
    knock_all_but(R.ellipse_pts(x, oy + 10, 22, 16, 30), None)

# ---------------- 字：粉 + 金故意错开 ----------------
G.text("咩！", (74, 70), 190); PK.text("咩！", (70, 66), 190)
for p in (B,):
    tmp = R.Plate("black"); tmp.text("咩！", (74, 70), 190); tmp.text("咩！", (70, 66), 190)
    B.d = B.d * (1 - (tmp.d > 0.5))
G.d = G.d * (1 - (PK.d > 0.5) * 0)  # 粉金重叠处保留叠印
tmp = R.Plate("black")
tmp.text("毛球球与乌鸦", (70, 1124), 30, font=R.FONT_REG)
tmp.text("RISO No.02 · 2026.10.10", (830, 1132), 20, font=R.FONT_REG, anchor="ra")
G.d = G.d * (1 - tmp.d)

# ---------------- 印 ----------------
paper = R.new_paper()
R.print_plate(paper, PK, offset=(0, 0), ink_density=0.94, velvet=0.35)
R.print_plate(paper, G, offset=(3, -2), rot=0.06, ink_density=0.93, velvet=0.3, sparkle=0.0006)
R.print_plate(paper, B, screen="dots", cell=4.2, angle=45, offset=(-2, 3), rot=-0.07, ink_density=0.95, velvet=0.38, scuffs=4, streak=0.04)
R.roller_ghost(paper, B, shift=-470, alpha=0.06)

here = os.path.dirname(os.path.abspath(__file__))
R.preview_plates([PK, G, B], os.path.join(here, "example_poster_plates.png"))
print(R.finish(paper, os.path.join(here, "example_poster.png")))
