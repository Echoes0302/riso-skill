"""起手模板：蓝底 + 金月亮 + 毛团小羊 + 乌鸦。拷这个改，别从空白起。
跑出来的 example.png 和包里的一模一样（seed 固定）——一致就说明环境对了。"""
import math, os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import riso_lib as R
CW, CH, M = 600, 840, 26
class Card:
    def __init__(self, inks, seed):
        R.setup(CW, CH, ss=2, seed=seed); self.p = [R.Plate(i) for i in inks]
    def knock(self, pts, keep=()):
        for pl in self.p:
            if pl not in keep: pl.poly(pts, mode="knock")
    def solid(self, pts, plate, d=1.0): self.knock(pts, keep=(plate,)); plate.poly(pts, d)
    def dark(self, pts):
        for pl in self.p: pl.poly(pts, 1.0)
    def text_ink(self, s, xy, size, plate, font=None, anchor="la", rot=0):
        tmp = R.Plate("black"); tmp.text(s, xy, size, font=font or R.FONT_BOLD, anchor=anchor, rot=rot)
        for pl in self.p: pl.d = np.maximum(pl.d, tmp.d) if pl is plate else pl.d * (1 - tmp.d)
    def text_knock(self, s, xy, size, font=None, anchor="la"):
        tmp = R.Plate("black"); tmp.text(s, xy, size, font=font or R.FONT_REG, anchor=anchor)
        for pl in self.p: pl.d = pl.d * (1 - tmp.d)
    def frame(self): self.p[0].poly([(M, M), (CW - M, M), (CW - M, CH - M), (M, CH - M)], 1.0)
    def print(self, path, offsets=((0, 0), (2, -2), (-2, 2)), rots=(0, 0.05, -0.06)):
        paper = R.new_paper()
        for k, i in enumerate([1, 2, 0]):
            if i >= len(self.p):
                continue
            R.print_plate(paper, self.p[i], screen="dots", cell=4.0, angle=(15, 75, 45)[k], offset=offsets[i], rot=rots[i], ink_density=0.94, velvet=0.38 if i == 0 else 0.25, scuffs=2 if i == 0 else 0, streak=0.04)
        R.roller_ghost(paper, self.p[0], shift=-300, alpha=0.05)
        return R.finish(paper, path)
def T(ox, oy, s, flip, pts):
    f = -1 if flip else 1
    return [(ox + f * x * s, oy + y * s) for x, y in pts]
def crow_stand(c, ox, oy, s=1.0, flip=False, sleep=False):
    t = lambda pts: T(ox, oy, s, flip, pts)
    for p in (t(R.ellipse_pts(8, -62, 52, 32, 40, rot=0.5)), t(R.ellipse_pts(-20, -90, 27, 25, 30)),
              t([(-62, -112), (-52, -128), (-30, -133), (-14, -128), (-8, -112), (-14, -94), (-34, -88), (-56, -96)]),
              t([(-56, -124), (-76, -123), (-95, -116), (-106, -106), (-88, -101), (-66, -98), (-54, -100)]),
              t([(40, -54), (106, -16), (100, 2), (34, -34)])):
        c.dark(p)
    for x0, x1 in ((-4, -9), (16, 13)):
        c.dark(t([(x0 - 2.5, -36), (x0 + 2.5, -36), (x1 + 2.5, 2), (x1 - 2.5, 2)]))
    c.knock(t(R.ellipse_pts(-36, -114, 6, 6, 20))); c.dark(t(R.ellipse_pts(-37.5, -114, 3.2, 3.4, 16)))
def sheep_face(c, fx, fy, s, face_pl, rot=12, bangs=True):
    c.solid(R.blob(fx, fy, 42 * s, 52 * s, rough=0.03, rot=math.radians(rot)), face_pl)
    for ex, er in ((fx - 52 * s, -12), (fx + 50 * s, 14)):
        c.solid(R.blob(ex, fy - 14 * s, 25 * s, 10 * s, rough=0.04, rot=math.radians(er)), face_pl)
    for ex in (fx - 15 * s, fx + 15 * s):
        c.knock(R.ellipse_pts(ex, fy + 2 * s, 10 * s, 10 * s, 24)); c.dark(R.ellipse_pts(ex + 2 * s, fy + 1 * s, 5 * s, 5.5 * s, 18))
    for pl in c.p: pl.line(R.ellipse_pts(fx, fy + 24 * s, 9 * s, 6 * s, 12, start=0.4, end=2.7), width=3.2 * s, mode="knock")
    if bangs:
        for dx in (-30, -10, 10, 30): c.knock(R.ellipse_pts(fx + dx * s, fy - 44 * s, 16 * s, 14 * s, 30))
c = Card(["bright_blue", "fluo_pink", "gold"], seed=1)
BL, PK, G = c.p
c.frame()
c.solid(R.blob(450, 170, 60, 60, rough=0.015), G)
ball = R.scallop(300, 520, 200, 160, bumps=22, depth=0.11)
c.knock(ball)
sh = R.Plate("black"); sh.poly(ball, 0.2); sh.poly(R.blob(270, 490, 192, 154, rough=0.02), mode="knock")
BL.d = np.maximum(BL.d, sh.d)
sheep_face(c, 300 - 200 + 40, 540, 0.7, PK)
crow_stand(c, 330, 372, s=0.8)
c.text_ink("咩！", (M + 30, M + 30), 90, PK)
c.text_knock("RISO · 起手模板", (CW - M - 18, CH - M - 30), 14, anchor="ra")
print(c.print(os.path.join(os.path.dirname(os.path.abspath(__file__)), "example.png")))
