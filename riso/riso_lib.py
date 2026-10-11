"""riso_lib —— 孔版印刷（Riso）模拟引擎
每个颜色是一张「版」（浓度图 0..1）。画：往版上涂浓度。印：浓度 → 网点/颗粒 → 墨不匀、白点、滚筒条纹、绒面、擦痕
→ 整版偏一点转一点 → 半透明乘法叠印到纸上。颜色是印出来的：粉叠黄=红，蓝叠黄=绿，蓝叠粉=紫，三色全叠≈黑。

依赖：pip install pillow numpy scipy
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

# Riso 真实油墨色（近似 sRGB）
INKS = {
    "fluo_pink": (255, 72, 176),
    "medium_blue": (50, 85, 164),
    "blue": (0, 120, 191),
    "bright_blue": (0, 94, 200),
    "aqua": (94, 200, 229),
    "yellow": (255, 232, 0),
    "sunflower": (255, 181, 17),
    "orange": (255, 108, 47),
    "teal": (0, 131, 138),
    "green": (0, 169, 92),
    "red": (255, 102, 94),
    "gold": (178, 148, 98),
    "black": (24, 24, 26),
}
PAPER = (246, 241, 230)


def _find_font(cands):
    for p in cands:
        if os.path.exists(p):
            return p
    return None


# 中文字体自动找：Noto CJK → 苹方 → 冬青黑；想指定就改 R.FONT_BOLD / R.FONT_REG
FONT_BOLD = _find_font([
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
])
FONT_REG = _find_font([
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]) or FONT_BOLD

W = H = 0
SS = 2  # 超采样：内部按 2 倍画，最后缩小


def setup(w, h, ss=2, seed=0):
    """每张画开头调一次：定尺寸、超采样倍数、随机种子。"""
    global W, H, SS
    SS = ss
    W, H = w * ss, h * ss
    random.seed(seed)
    np.random.seed(seed)


def _font(path, size):
    if path:
        return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


# ---------------------------------------------------------------- 版
class Plate:
    """一张版：float 浓度图。坐标用最终尺寸写，内部自动乘 SS。"""

    def __init__(self, ink, name=""):
        self.ink = INKS.get(ink, ink) if isinstance(ink, str) else ink
        self.d = np.zeros((H, W), np.float32)
        self.name = name

    def _merge(self, mask, density, mode):
        m = np.asarray(mask, np.float32) / 255.0
        if mode == "max":
            self.d = np.maximum(self.d, m * density)
        elif mode == "set":
            self.d = self.d * (1 - m) + m * density
        elif mode == "knock":  # 挖掉：留纸
            self.d = self.d * (1 - m)
        elif mode == "add":
            self.d = np.clip(self.d + m * density, 0, 1)

    def _canvas(self):
        return Image.new("L", (W, H), 0)

    def poly(self, pts, density=1.0, mode="max", feather=0):
        im = self._canvas()
        ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        if feather:
            im = im.filter(ImageFilter.GaussianBlur(feather * SS))
        self._merge(im, density, mode)

    def line(self, pts, width=4, density=1.0, mode="max"):
        im = self._canvas()
        dr = ImageDraw.Draw(im)
        p = [(x * SS, y * SS) for x, y in pts]
        dr.line(p, fill=255, width=int(width * SS), joint="curve")
        r = width * SS / 2
        for x, y in (p[0], p[-1]):
            dr.ellipse([x - r, y - r, x + r, y + r], fill=255)
        self._merge(im, density, mode)

    def text(self, s, xy, size, density=1.0, mode="max", font=None, rot=0, anchor="la"):
        f = _font(font or FONT_BOLD, int(size * SS))
        im = self._canvas()
        ImageDraw.Draw(im).text((xy[0] * SS, xy[1] * SS), s, font=f, fill=255, anchor=anchor)
        if rot:
            bb = im.getbbox()
            if bb:
                im = im.rotate(rot, resample=Image.BICUBIC, center=((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2))
        self._merge(im, density, mode)

    def gradient(self, pts, d0, d1, p0, p1, mode="max"):
        """多边形内线性渐变：p0 处浓度 d0 → p1 处 d1。"""
        im = self._canvas()
        ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        ax, ay, bx, by = p0[0] * SS, p0[1] * SS, p1[0] * SS, p1[1] * SS
        vx, vy = bx - ax, by - ay
        t = np.clip(((xx - ax) * vx + (yy - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        g = d0 + (d1 - d0) * t
        m = np.asarray(im, np.float32) / 255.0
        self.d = np.maximum(self.d, m * g) if mode == "max" else self.d * (1 - m) + m * g

    def radial(self, cx, cy, r, d0, d1, mode="max", wobble=0.0):
        """圆内径向渐变：中心 d0 → 边缘 d1。"""
        pts = blob(cx, cy, r, r, rough=wobble) if wobble else ellipse_pts(cx, cy, r, r, 90)
        im = self._canvas()
        ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        t = np.clip(np.hypot(xx - cx * SS, yy - cy * SS) / (r * SS), 0, 1)
        g = d0 + (d1 - d0) * t
        m = np.asarray(im, np.float32) / 255.0
        self.d = np.maximum(self.d, m * g) if mode == "max" else self.d * (1 - m) + m * g


# ---------------------------------------------------------------- 几何（手画感）
def _smooth_noise(n, scale=0.3, octaves=3):
    out = np.zeros(n)
    for o in range(octaves):
        k = max(2, int(n * scale * (2 ** o) / 10))
        pts = np.random.randn(k + 1)
        out += np.interp(np.linspace(0, k, n), np.arange(k + 1), pts) / (2 ** o)
    return out


def ellipse_pts(cx, cy, rx, ry, n=64, rot=0.0, rough=0.0, start=0.0, end=2 * math.pi):
    ts = np.linspace(start, end, n, endpoint=(end - start) < 2 * math.pi - 1e-6)
    noise = _smooth_noise(len(ts)) * rough if rough else np.zeros(len(ts))
    pts = []
    for t, e in zip(ts, noise):
        x, y = rx * (1 + e) * math.cos(t), ry * (1 + e) * math.sin(t)
        pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return pts


def blob(cx, cy, rx, ry, rough=0.06, n=72, rot=0.0):
    return ellipse_pts(cx, cy, rx, ry, n=n, rough=rough, rot=rot)


def scallop(cx, cy, rx, ry, bumps=18, depth=0.12, rough=0.03, n=720):
    """毛团/云/爆米花的边：一圈小鼓包。"""
    ph = random.uniform(0, math.pi)
    noise = _smooth_noise(n, 0.2) * rough
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 1 + depth * (abs(math.sin(bumps * t / 2 + ph)) ** 0.6 - 0.6) + noise[i]
        pts.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
    return pts


def wobble_line(pts, amp=1.5, per=6):
    """折线重采样 + 一点手抖。"""
    out = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        k = max(2, int(math.hypot(x1 - x0, y1 - y0) / per))
        for i in range(k):
            t = i / k
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append(pts[-1])
    n = np.array(out, dtype=float)
    if len(n) > 4:
        n[:, 0] += _smooth_noise(len(n), 0.5) * amp
        n[:, 1] += _smooth_noise(len(n), 0.5) * amp
    return [tuple(p) for p in n]


# ---------------------------------------------------------------- 网屏
def _lowfreq(scale_px, amp=1.0):
    sw, sh = max(2, W // scale_px), max(2, H // scale_px)
    small = Image.fromarray((np.random.rand(sh, sw) * 255).astype(np.uint8))
    big = np.asarray(small.resize((W, H), Image.BICUBIC), np.float32) / 255.0
    return (big - 0.5) * 2 * amp


def screen_grain(d, grain=1.0):
    """颗粒网（调频）。低浓度时像灰尘——浅色别用它。"""
    noise = ndimage.gaussian_filter(np.random.rand(H, W).astype(np.float32), 0.55 * SS * grain)
    flat = noise.ravel()
    ranks = np.empty_like(flat)
    ranks[np.argsort(flat)] = np.linspace(0, 1, flat.size, dtype=np.float32)
    thr = ranks.reshape(H, W)
    return np.clip((d - thr) * 6 + 0.5, 0, 1) * (d > 0.002)


def screen_dots(d, cell=4.0, angle=45.0):
    """调幅圆点网：浓度 → 点的大小。浅色、阴影、毛卷都用它。"""
    c = cell * SS
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = math.radians(angle)
    u = xx * math.cos(a) + yy * math.sin(a)
    v = -xx * math.sin(a) + yy * math.cos(a)
    fu, fv = (u / c) % 1.0 - 0.5, (v / c) % 1.0 - 0.5
    dist = np.sqrt(fu * fu + fv * fv) * c
    r = c * np.sqrt(np.clip(d, 0, 1) / math.pi) * 1.08
    cov = np.clip(r - dist + 0.5, 0, 1)
    cov[d > 0.96] = 1.0
    return cov


# ---------------------------------------------------------------- 印
def print_plate(paper, plate, *, screen="dots", cell=4.0, angle=45.0, grain=1.0,
                offset=(0.0, 0.0), rot=0.0, ink_density=0.94, mottle=0.10, streak=0.04,
                specks=0.012, edge_rough=0.18, gain=0.0, velvet=0.0, scuffs=0, sparkle=0.0):
    """把一张版印到纸上（就地改 paper: float HxWx3 0..1）。
    offset/rot 套色不准；mottle 墨色斑驳；streak 滚筒条纹；specks 漏墨白点；edge_rough 边缘毛；
    velvet 实地绒面；scuffs 擦痕条数；sparkle 金属墨亮点。"""
    d = plate.d.copy()
    if gain:
        d = np.clip(d + gain * d * (1 - d) * 2, 0, 1)
    if edge_rough:
        n = ndimage.gaussian_filter(np.random.randn(H, W).astype(np.float32), 1.2 * SS)
        n = n / (n.std() + 1e-6)
        edge = (d > 0.02) & (d < 0.995)
        d = np.where(edge | (d >= 0.995), np.clip(d + n * edge_rough * 0.25, 0, 1), d)
    if screen == "grain":
        cov = screen_grain(d, grain)
    elif screen == "dots":
        cov = screen_dots(d, cell, angle)
    else:
        cov = np.clip(d, 0, 1)
    if offset != (0, 0) or rot:
        im = Image.fromarray((cov * 255).astype(np.uint8))
        im = im.rotate(rot, resample=Image.BICUBIC, center=(W / 2, H / 2), translate=(offset[0] * SS, offset[1] * SS))
        cov = np.asarray(im, np.float32) / 255.0
    amt = ink_density + _lowfreq(90 * SS, mottle)
    if streak:
        band = _smooth_noise(H, 0.6, 3)
        band = (band - band.mean()) / (band.std() + 1e-6)
        amt = amt + band[:, None].astype(np.float32) * streak
    if specks:
        sp = ndimage.binary_dilation(np.random.rand(H, W) < specks / 6, iterations=max(1, SS - 1))
        amt = np.where(sp, amt * 0.15, amt)
    if velvet:
        fib = ndimage.gaussian_filter(np.random.randn(H, W).astype(np.float32), (0.6 * SS, 2.2 * SS))
        fib = fib / (fib.std() + 1e-6)
        amt = amt - np.clip(fib - 0.9, 0, None) * velvet * 0.35 + fib * velvet * 0.04
    if scuffs:
        sm = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(sm)
        for _ in range(scuffs):
            x0, y0 = random.uniform(0, W), random.uniform(0, H)
            a0 = random.uniform(-0.5, 0.5) + random.choice((0, math.pi / 2))
            L = random.uniform(0.15, 0.4) * W
            dr.line([(x0, y0), (x0 + L * math.cos(a0), y0 + L * math.sin(a0))],
                    fill=random.randint(90, 200), width=random.randint(2, 7) * SS)
        amt = amt * (1 - ndimage.gaussian_filter(np.asarray(sm, np.float32) / 255.0, 2 * SS) * 0.45)
    amt = np.clip(amt, 0, 1)
    a = (cov * amt)[..., None]
    ink = np.array(plate.ink, np.float32) / 255.0
    paper *= (1 - a) + a * ink  # 乘法叠印：半透明油墨
    if sparkle:
        sp = (np.random.rand(H, W) < sparkle) & (cov * amt > 0.5)
        spk = ndimage.gaussian_filter(sp.astype(np.float32), 0.6 * SS) * 3
        paper += np.clip(spk, 0, 0.5)[..., None] * np.array([1.0, 0.9, 0.7], np.float32)
    return paper


def roller_ghost(paper, plate, shift=-420, alpha=0.06, patchy=0.6):
    """輪印：滚轮蹭到湿墨再压回纸上，在别处留下淡淡的、断断续续的影子。shift 用最终尺寸像素。"""
    g = ndimage.gaussian_filter(np.roll(plate.d, int(shift * SS), axis=0), (1.5 * SS, 4 * SS))
    mask = np.clip(_lowfreq(60 * SS, 1.0) + (1 - patchy), 0, 1)
    st = ndimage.gaussian_filter(np.random.rand(H, W).astype(np.float32), (0.5 * SS, 12 * SS))
    st = (st - st.min()) / (np.ptp(st) + 1e-6)
    a = (g * mask * (0.4 + st) * alpha)[..., None]
    paper *= (1 - a) + a * (np.array(plate.ink, np.float32) / 255.0)
    return paper


def new_paper(color=PAPER, grain=0.025):
    p = np.ones((H, W, 3), np.float32) * (np.array(color, np.float32) / 255.0)
    n = ndimage.gaussian_filter(np.random.randn(H, W).astype(np.float32), 0.8 * SS)
    p += (n / (n.std() + 1e-6) * grain)[..., None] * 0.6
    p += _lowfreq(40 * SS, grain * 0.8)[..., None]
    return np.clip(p, 0, 1)


def finish(paper, path, size=None):
    im = Image.fromarray((np.clip(paper, 0, 1) * 255).astype(np.uint8))
    if SS != 1:
        im = im.resize((W // SS, H // SS), Image.LANCZOS)
    im.save(path, quality=95)
    return path


def preview_plates(plates, path, scale=0.25):
    """每张版单独印出来排一排，检查分色。"""
    tiles = []
    for p in plates:
        pa = new_paper(grain=0)
        print_plate(pa, p, specks=0, mottle=0, streak=0, edge_rough=0)
        tiles.append(Image.fromarray((pa * 255).astype(np.uint8)).resize((int(W * scale), int(H * scale))))
    out = Image.new("RGB", (sum(t.width for t in tiles) + 10 * (len(tiles) - 1), tiles[0].height), (255, 255, 255))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.width + 10
    out.save(path)
    return path
