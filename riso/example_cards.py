"""毛球球在哪里？ · Riso 小卡四张 · 2026.10.11
乌鸦叼着笔到处找毛球球。每张三色，乌鸦 = 三色全叠的最深色。"""
import math, os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import riso_lib as R
from PIL import Image

CW, CH, M = 600, 840, 26
HERE = os.path.dirname(os.path.abspath(__file__))


# ======================================================== 共用零件
class Card:
    def __init__(self, inks, seed):
        R.setup(CW, CH, ss=2, seed=seed)
        self.p = [R.Plate(i) for i in inks]  # 0=底色版 1,2=另两色

    def knock(self, pts, keep=()):
        for pl in self.p:
            if pl not in keep:
                pl.poly(pts, mode="knock")

    def solid(self, pts, plate, d=1.0):
        """只印这一色：别的版挖掉。"""
        self.knock(pts, keep=(plate,))
        plate.poly(pts, d)

    def dark(self, pts):
        """乌鸦色：三版全叠。"""
        for pl in self.p:
            pl.poly(pts, 1.0)

    def text_knock(self, s, xy, size, font=R.FONT_REG, anchor="la", keep=()):
        tmp = R.Plate("black")
        tmp.text(s, xy, size, font=font, anchor=anchor)
        for pl in self.p:
            if pl not in keep:
                pl.d = pl.d * (1 - tmp.d)
        return tmp

    def text_ink(self, s, xy, size, plate, font=R.FONT_BOLD, anchor="la", rot=0):
        tmp = R.Plate("black")
        tmp.text(s, xy, size, font=font, anchor=anchor, rot=rot)
        for pl in self.p:
            pl.d = pl.d * (1 - tmp.d) if pl is not plate else np.maximum(pl.d, tmp.d)

    def frame(self):
        self.p[0].poly([(M, M), (CW - M, M), (CW - M, CH - M), (M, CH - M)], 1.0)

    def print(self, name, offsets=((0, 0), (2, -2), (-2, 2)), rots=(0, 0.05, -0.06)):
        paper = R.new_paper()
        order = [1, 2, 0]  # 浅的两色先印，底色最后
        for k, i in enumerate(order):
            if i >= len(self.p):
                continue
            R.print_plate(paper, self.p[i], screen="dots", cell=4.0, angle=(15, 75, 45)[k],
                          offset=offsets[i], rot=rots[i], ink_density=0.94,
                          velvet=0.38 if i == 0 else 0.25, scuffs=2 if i == 0 else 0, streak=0.04)
        R.roller_ghost(paper, self.p[0], shift=-300, alpha=0.05)
        os.makedirs(os.path.join(HERE, "cards"), exist_ok=True)
        out = os.path.join(HERE, "cards", name)
        R.finish(paper, out)
        return out


def T(ox, oy, s, flip, pts):
    f = -1 if flip else 1
    return [(ox + f * x * s, oy + y * s) for x, y in pts]


def crow_stand(c, ox, oy, s=1.0, flip=False, accent=None, pencil=None, sleep=False):
    """站着的乌鸦，默认面朝左。pencil=(杆版, 尖版) 时嘴里叼笔。"""
    t = lambda pts: T(ox, oy, s, flip, pts)
    body = t(R.ellipse_pts(8, -62, 52, 32, 40, rot=0.5))
    parts = [body, t(R.ellipse_pts(-20, -90, 27, 25, 30)),
             t([(-62, -112), (-52, -128), (-30, -133), (-14, -128), (-8, -112), (-14, -94), (-34, -88), (-56, -96)]),
             t([(-56, -124), (-76, -123), (-95, -116), (-106, -106), (-88, -101), (-66, -98), (-54, -100)]),
             t([(40, -54), (106, -16), (100, 2), (34, -34)])]
    for p in parts:
        c.dark(p)
    for x0, x1 in ((-4, -9), (16, 13)):
        c.dark(t([(x0 - 2.5, -36), (x0 + 2.5, -36), (x1 + 2.5, 2), (x1 - 2.5, 2)]))
    if accent is not None:
        for pl in c.p:
            if pl is not accent:
                pl.line(R.wobble_line(t([(-16, -80), (18, -70), (58, -40)]), amp=0.5), width=3 * s, mode="knock")
    if sleep:
        for pl in c.p:
            pl.line(R.wobble_line(t(R.ellipse_pts(-36, -116, 7, 4, 10, start=0.2, end=2.9)), amp=0.2, per=2), width=2.6 * s, mode="knock")
    else:
        eye = t(R.ellipse_pts(-36, -114, 6, 6, 20))
        c.knock(eye)
        c.dark(t(R.ellipse_pts(-37.5, -114, 3.2, 3.4, 16)))
    if pencil:
        crow_pencil(c, t, s, flip, *pencil)


def crow_pencil(c, t, s, flip, shaft_pl, tip_pl, center=(-84, -110), ang=8):
    f = -1 if flip else 1
    pa = math.radians(ang) * f
    ux, uy, vx, vy = math.cos(pa) * f, math.sin(pa) * f, -math.sin(pa), math.cos(pa)
    pcx, pcy = t([center])[0]
    pp = lambda a, w: (pcx + ux * a * s + vx * w * s, pcy + uy * a * s + vy * w * s)
    shaft = [pp(-40, -7), pp(40, -7), pp(40, 7), pp(-40, 7)]
    tip = [pp(-40, -7), pp(-60, 0), pp(-40, 7)]
    c.solid(shaft, shaft_pl)
    c.solid(tip, tip_pl)
    c.dark([pp(-52, -2.8), pp(-60, 0), pp(-52, 2.8)])


def crow_fly(c, ox, oy, s=1.0, flip=False, pencil=None):
    """飞着的乌鸦，面朝左。"""
    t = lambda pts: T(ox, oy, s, flip, pts)
    parts = [t(R.ellipse_pts(0, 0, 54, 22, 40, rot=-0.08)),
             t(R.ellipse_pts(-50, -8, 24, 21, 30)),
             t([(-66, -16), (-58, -26), (-40, -29), (-30, -22)]),
             t([(-68, -14), (-88, -12), (-104, -4), (-110, 4), (-90, 6), (-68, 6)]),
             t([(44, -6), (100, -20), (104, 4), (46, 12)]),
             t(R.ellipse_pts(14, -50, 50, 19, 40, rot=-1.2)),  # 翅膀抬起
             t(R.ellipse_pts(30, -88, 9, 22, 20, rot=0.2)), t(R.ellipse_pts(44, -82, 8, 20, 20, rot=0.5)), t(R.ellipse_pts(54, -70, 7, 17, 20, rot=0.8)),
             t([(-4, 6), (30, 46), (44, 44), (26, 4)])]  # 另一边翅膀
    for p in parts:
        c.dark(p)
    for (x0, y0), (x1, y1) in (((12, -40), (26, -70)),):
        for pl in c.p:
            pl.line(t([(x0, y0), (x1, y1)]), width=2.4 * s, mode="knock")
    c.knock(t(R.ellipse_pts(-56, -12, 5.5, 5.5, 18)))
    c.dark(t(R.ellipse_pts(-57.5, -12, 3, 3.2, 14)))
    if pencil:
        crow_pencil(c, t, s, flip, *pencil, center=(-88, -2), ang=4)


def sheep_face(c, fx, fy, s, face_pl, pupil_pl=None, rot=12, bangs=True, blush=None):
    face = R.blob(fx, fy, 42 * s, 52 * s, rough=0.03, rot=math.radians(rot))
    c.solid(face, face_pl)
    for ex, er in ((fx - 52 * s, -12), (fx + 50 * s, 14)):
        ear = R.blob(ex, fy - 14 * s, 25 * s, 10 * s, rough=0.04, rot=math.radians(er))
        c.solid(ear, face_pl)
    for ex in (fx - 15 * s, fx + 15 * s):
        c.knock(R.ellipse_pts(ex, fy + 2 * s, 10 * s, 10 * s, 24))
        c.dark(R.ellipse_pts(ex + 2 * s, fy + 1 * s, 5 * s, 5.5 * s, 18))
    for pl in c.p:
        pl.line(R.wobble_line(R.ellipse_pts(fx, fy + 24 * s, 9 * s, 6 * s, 12, start=0.4, end=2.7), amp=0.2, per=3), width=3.2 * s, mode="knock")
    if blush is not None:
        for ex in (fx - 26 * s, fx + 26 * s):
            blush.poly(R.ellipse_pts(ex, fy + 16 * s, 8 * s, 5 * s, 20), 1.0)
    if bangs:
        for dx in (-30, -10, 10, 30):
            c.knock(R.ellipse_pts(fx + dx * s, fy - 44 * s, 16 * s, 14 * s, 30))


def sparkle(c, cx, cy, r, plate):
    pts = []
    for i in range(16):
        a = math.pi * i / 8
        rr = r if i % 4 == 0 else r * 0.18
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    c.solid(pts, plate)


def label(c, n, q, qpos, qsize=46, qplate=None, qrot=0):
    c.text_knock(f"毛球球在哪里？  {n}/4", (M + 18, CH - M - 34), 19)
    c.text_knock("RISO · 2026.10.11", (CW - M - 18, CH - M - 30), 14, anchor="ra")
    if qplate is not None:
        c.text_ink(q, qpos, qsize, qplate, rot=qrot)
    else:
        c.text_knock(q, qpos, qsize, font=R.FONT_BOLD)


# ======================================================== 1 云
def card1():
    c = Card(["blue", "fluo_pink", "yellow"], 11)
    B, PK, Y = c.p
    c.frame()
    c.solid(R.blob(470, 150, 64, 64, rough=0.015), Y)
    clouds = [(150, 300, 96, 50), (420, 420, 110, 54), (180, 560, 120, 58), (450, 660, 90, 46), (330, 225, 70, 34)]
    hide = 2
    for i, (x, y, rx, ry) in enumerate(clouds):
        cl = R.scallop(x, y, rx, ry, bumps=9 + i % 3, depth=0.26, rough=0.02)
        c.knock(cl)
        sh = R.Plate("black"); sh.poly(cl, 0.25); sh.poly(R.blob(x - 10, y - 14, rx, ry * 0.95, rough=0.02), mode="knock")
        B.d = np.maximum(B.d, sh.d)
        if i == hide:  # 这朵云有腿
            for lx in (-62, -26, 26, 60):
                c.solid([(x + lx - 5, y + ry - 6), (x + lx + 5, y + ry - 6), (x + lx + 5, y + ry + 30), (x + lx - 5, y + ry + 30)], PK)
            sheep_face(c, x - rx + 6, y + 8, 0.62, PK, bangs=False)
    crow_fly(c, 360, 330 - 40, s=0.95, flip=True, pencil=(Y, PK))  # 朝右飞，看反了
    for x, y, r in ((90, 130, 12), (530, 300, 10), (540, 560, 13), (90, 700, 9)):
        sparkle(c, x, y, r, PK)
    label(c, 1, "是这朵吗？", (M + 26, M + 30), 44, qplate=PK)
    return c.print("card1-云.png")


# ======================================================== 2 棉花糖
def card2():
    c = Card(["fluo_pink", "teal", "yellow"], 22)
    PK, TL, Y = c.p
    c.frame()
    # 条纹背景：粉底上的淡粉网点竖条
    for x in range(M + 20, CW - M, 70):
        PK.poly([(x, M), (x + 30, M), (x + 30, CH - M), (x, CH - M)], mode="knock")
        PK.poly([(x, M), (x + 30, M), (x + 30, CH - M), (x, CH - M)], 0.7)
    # 棍子
    c.solid([(300, 560), (314, 560), (320, 744), (306, 744)], Y)
    # 棉花糖：一大团纸色 + 淡粉网点
    cc = R.scallop(300, 400, 196, 178, bumps=15, depth=0.14, rough=0.03)
    c.knock(cc)
    sh = R.Plate("black"); sh.poly(cc, 0.28); sh.poly(R.blob(280, 380, 186, 168, rough=0.02), mode="knock")
    PK.d = np.maximum(PK.d, sh.d)
    for _ in range(18):
        a, rr = random.uniform(0, 2 * math.pi), random.uniform(0.15, 0.8)
        qx, qy = 300 + rr * 190 * math.cos(a), 400 + rr * 170 * math.sin(a)
        if abs(qx - 214) < 70 and abs(qy - 430) < 70: continue
        st = random.uniform(0, 2 * math.pi)
        PK.line(R.wobble_line(R.ellipse_pts(qx, qy, 16, 12, 14, start=st, end=st + 4.2), amp=0.5, per=4), width=4.5, density=0.32, mode="set")
    sheep_face(c, 214, 432, 0.55, TL, rot=-6)
    # 乌鸦站在棍子旁边的小凳？——站在框底，歪头看棉花糖
    crow_stand(c, 462, 742, s=0.9, flip=False, pencil=(Y, PK))
    c.solid([(M, 744), (CW - M, 744), (CW - M, 766), (M, 766)], TL)
    for x, y, r in ((520, 120, 12), (90, 640, 10), (530, 560, 9)):
        sparkle(c, x, y, r, Y)
    label(c, 2, "在这里吗？", (M + 26, M + 30), 44, qplate=Y)
    return c.print("card2-棉花糖.png")


# ======================================================== 3 爆米花
def card3():
    c = Card(["red", "yellow", "medium_blue"], 33)
    RD, Y, BL = c.p
    c.frame()
    # 散落的小黄点背景
    for _ in range(40):
        x, y = random.uniform(M + 10, CW - M - 10), random.uniform(M + 10, CH - M - 10)
        c.solid(R.ellipse_pts(x, y, 4, 4, 12), Y)
    # 桶：梯形，红白条（白=纸，红=底色），桶口一圈蓝
    top, bot = 470, 790
    tl, tr, bl, br = 150, 450, 190, 410
    bucket = [(tl, top), (tr, top), (br, bot), (bl, bot)]
    c.knock(bucket)
    n = 5
    for i in range(n):
        if i % 2 == 0: continue
        a0, a1 = i / n, (i + 1) / n
        strip = [(tl + (tr - tl) * a0, top), (tl + (tr - tl) * a1, top), (bl + (br - bl) * a1, bot), (bl + (br - bl) * a0, bot)]
        c.solid(strip, RD)
    c.solid([(tl - 10, top - 6), (tr + 10, top - 6), (tr + 6, top + 22), (tl - 6, top + 22)], BL)
    # 爆米花：一堆纸色小云团，底部淡黄
    random.seed(3)
    pops = []
    for _ in range(26):
        x = random.uniform(tl + 10, tr - 10); y = random.uniform(300, top + 4)
        if abs(x - 300) > 150 - (top - y) * 0.25: continue
        pops.append((x, y, random.uniform(24, 34)))
    pops.append((300, 296, 36))
    pops.sort(key=lambda p: p[1])
    hide = (232, 380, 34)
    for x, y, r in pops + [hide]:
        pc = R.scallop(x, y, r, r * 0.86, bumps=6, depth=0.28, rough=0.04)
        c.knock(pc)
        Y.poly(R.blob(x + r * 0.2, y + r * 0.3, r * 0.6, r * 0.45, rough=0.08), 0.45)
    sheep_face(c, hide[0] + 4, hide[1] + 6, 0.42, RD, bangs=False)
    # 掉出来的几颗
    for x, y in ((470, 752), (548, 610), (110, 735)):
        c.knock(R.scallop(x, y, 20, 17, bumps=6, depth=0.28))
    crow_stand(c, 486, 726, s=0.76, flip=False, pencil=None)
    # 乌鸦叼着一颗爆米花（不是毛球球）
    c.knock(R.scallop(486 - 96 * 0.76, 726 - 106 * 0.76, 16, 14, bumps=6, depth=0.3))
    label(c, 3, "是这颗吗？", (M + 26, M + 30), 44, qplate=Y)
    return c.print("card3-爆米花.png", offsets=((0, 0), (2, 2), (-2, -1)))


# ======================================================== 4 找到啦
def card4():
    c = Card(["medium_blue", "yellow", "fluo_pink"], 44)
    BL, Y, PK = c.p
    c.frame()
    c.solid(R.blob(470, 140, 54, 54, rough=0.015), Y)
    c.knock(R.blob(492, 128, 50, 50, rough=0.015))  # 月牙：挖掉一块
    BL.poly(R.blob(492, 128, 50, 50, rough=0.015), 1.0)
    # 小草地：蓝叠黄 = 绿
    ground = R.ellipse_pts(300, 1010, 420, 260, 120)
    ground = [(min(max(x, M), CW - M), min(max(y, M), CH - M)) for x, y in ground]
    Y.poly(ground, 1.0)
    def dandelion(x, y, r, stem_to):
        # 茎：蓝叠黄
        Y.line([(x, y + r * 0.6), (x + 6, stem_to)], width=5, density=1.0)
        n = 22
        for i in range(n):
            a = 2 * math.pi * i / n
            x1, y1 = x + r * math.cos(a), y + r * math.sin(a)
            c.knock_line = None
            for pl in c.p:
                pl.line([(x + r * 0.25 * math.cos(a), y + r * 0.25 * math.sin(a)), (x1, y1)], width=2.4, mode="knock")
            c.knock(R.ellipse_pts(x1, y1, 4.5, 4.5, 10))
        c.knock(R.ellipse_pts(x, y, r * 0.22, r * 0.22, 16))
    for x, y, r, st in ((110, 600, 36, 780), (520, 560, 30, 770), (470, 680, 22, 790), (80, 420, 20, 520)):
        dandelion(x, y, r, st)
    # 最大的那朵 = 毛球球
    bx, by = 290, 520
    Y.line([(bx, by + 110), (bx + 8, 800)], width=8)
    ball = R.scallop(bx, by, 150, 130, bumps=20, depth=0.12)
    c.knock(ball)
    for i in range(36):  # 放射的种子线，淡蓝
        a = 2 * math.pi * i / 36
        BL.line([(bx + 40 * math.cos(a), by + 36 * math.sin(a)), (bx + 128 * math.cos(a), by + 110 * math.sin(a))], width=2.4, density=0.32, mode="set")
    sheep_face(c, bx - 118, by + 22, 0.6, PK, rot=8, blush=None)
    for lx in (-60, -20, 30, 70):  # 小腿也在茎旁边
        pass
    crow_stand(c, bx + 30, by - 112, s=0.82, flip=False, sleep=True)
    for x, y, r in ((90, 120, 11), (300, 90, 9), (540, 330, 12), (60, 300, 8)):
        sparkle(c, x, y, r, PK)
    # zzz
    for i, (x, y, sz) in enumerate(((380, 330, 26), (406, 300, 20), (426, 276, 15))):
        c.text_ink("z", (x, y), sz, Y, font=R.FONT_BOLD)
    label(c, 4, "找到你啦！", (M + 26, M + 30), 44, qplate=PK)
    return c.print("card4-找到啦.png")


# ======================================================== 0 封面
def card0():
    c = Card(["yellow", "fluo_pink", "medium_blue"], 7)
    Y, PK, BL = c.p
    c.frame()
    # 标题
    c.text_ink("毛球球", (M + 30, M + 34), 112, BL)
    c.text_ink("在哪里？", (M + 38, M + 172), 70, PK)
    c.text_ink("云 · 棉花糖 · 爆米花 · 蒲公英", (M + 42, M + 272), 20, BL, font=R.FONT_REG)
    c.text_ink("乌鸦 × 毛球球", (CW - M - 24, M + 36), 18, PK, font=R.FONT_REG, anchor="ra")
    c.text_ink("RISO 小卡 · 四张一套", (CW - M - 24, M + 62), 14, BL, font=R.FONT_REG, anchor="ra")
    # 一大团毛，从框底溢出去
    wx, wy, wrx, wry = 300, 640, 340, 250
    wool = R.scallop(wx, wy, wrx, wry, bumps=22, depth=0.09, rough=0.02)
    c.knock(wool)
    lx, ly, lr = 236, 620, 100
    random.seed(70)
    for _ in range(30):
        a, rr = random.uniform(0, 2 * math.pi), random.uniform(0.1, 0.85)
        qx, qy = wx + rr * wrx * math.cos(a), wy + rr * wry * math.sin(a)
        if math.hypot(qx - lx, qy - ly) < lr + 26 or qy > CH - M - 12: continue
        st = random.uniform(0, 2 * math.pi)
        BL.line(R.wobble_line(R.ellipse_pts(qx, qy, 12, 10, 12, start=st, end=st + 4.3), amp=0.4, per=4), width=4, density=0.3, mode="set")
    # 镜片里：放大的毛 + 毛球球的脸
    for k in range(5):
        a = k * 1.3 + 0.4
        qx, qy = lx + 62 * math.cos(a), ly + 58 * math.sin(a)
        if abs(qy - ly) < 30 and abs(qx - lx) < 70: continue
        st = random.uniform(0, 2 * math.pi)
        BL.line(R.wobble_line(R.ellipse_pts(qx, qy, 22, 18, 14, start=st, end=st + 4.3), amp=0.4, per=4), width=6, density=0.35, mode="set")
    sheep_face(c, lx - 4, ly + 6, 0.92, PK, rot=6, bangs=True)
    glass = R.Plate("black"); glass.poly(R.ellipse_pts(lx, ly, lr, lr, 80), 0.16)
    BL.d = np.maximum(BL.d, glass.d)
    for pl in c.p:  # 镜片高光
        pl.line(R.ellipse_pts(lx, ly, lr - 18, lr - 18, 20, start=3.6, end=4.5), width=7, mode="knock")
    # 镜框 + 手柄（蓝）
    ring_o = R.ellipse_pts(lx, ly, lr + 13, lr + 13, 100)
    ring_i = R.ellipse_pts(lx, ly, lr, lr, 100)
    rp = R.Plate("black"); rp.poly(ring_o, 1.0); rp.poly(ring_i, mode="knock")
    for pl in c.p:
        pl.d = pl.d * (1 - rp.d) if pl is not BL else np.maximum(pl.d, rp.d)
    ang = math.atan2(356 - ly, 414 - lx)
    hx0, hy0 = lx + (lr + 8) * math.cos(ang), ly + (lr + 8) * math.sin(ang)
    hx1, hy1 = 414, 356
    for pl in c.p:
        if pl is not BL: pl.line([(hx0, hy0), (hx1, hy1)], width=16, mode="knock")
    BL.line([(hx0, hy0), (hx1, hy1)], width=16)
    # 乌鸦：站在毛上，叼着放大镜手柄
    crow_stand(c, 488, 448, s=0.86, flip=False)
    # 笔插在毛里
    pa = math.radians(-62)
    ux, uy, vx, vy = math.cos(pa), math.sin(pa), -math.sin(pa), math.cos(pa)
    pcx, pcy = 470, 560
    pp = lambda a, w: (pcx + ux * a + vx * w, pcy + uy * a + vy * w)
    c.solid([pp(-36, -7), pp(40, -7), pp(40, 7), pp(-36, 7)], Y)
    c.solid([pp(40, -7), pp(58, 0), pp(40, 7)], PK)
    c.dark([pp(51, -2.6), pp(58, 0), pp(51, 2.6)])
    c.knock(R.scallop(pcx + ux * -30, pcy + uy * -30, 30, 18, bumps=5, depth=0.25))
    for x, y, r in ((520, 250, 12), (80, 330, 9), (556, 390, 8)):
        sparkle(c, x, y, r, PK)
    return c.print("card0-封面.png")


if __name__ == "__main__":
    which = sys.argv[1:] or ["0", "1", "2", "3", "4"]
    outs = []
    for w in which:
        outs.append({"0": card0, "1": card1, "2": card2, "3": card3, "4": card4}[w]())
        print(outs[-1])
    if len(outs) == 5:  # 五张拼一张合集
        ims = [Image.open(p) for p in outs]
        w, h = ims[0].size; g = 30; sc = 0.62
        cw, ch = int(w * sc), int(h * sc)
        sheet = Image.new("RGB", (g + w + g + 2 * (cw + g), g + 2 * (ch + g)), (70, 70, 74))
        sheet.paste(ims[0], (g, g + (2 * ch + g - h) // 2))
        for i, im in enumerate(ims[1:]):
            sheet.paste(im.resize((cw, ch), Image.LANCZOS), (g + w + g + (i % 2) * (cw + g), g + (i // 2) * (ch + g)))
        sheet.save(os.path.join(HERE, "example_cards.png"))
        print(os.path.join(HERE, "example_cards.png"))
