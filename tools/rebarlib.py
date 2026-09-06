#!/usr/bin/env python3
"""
rebarlib.py — 철근 객체 · 물량 집계 · SVG 배근도. 표준 라이브러리만 사용.

Bar   : 폴리라인(굽힘 원호 포함) + 지름 + 부호. 길이는 원호를 반영해 계산한다.
BOM   : 부호별 집계 → 개수 · 단위길이 · 총연장 · 중량 (KS D 3504 단위중량)
draw  : 단면 윤곽 + 철근 + 부호를 SVG 로 출력
"""
import math

# KS D 3504 이형봉강 단위중량 (kg/m)
UNIT_W = {10: 0.560, 13: 0.995, 16: 1.560, 19: 2.250, 22: 3.040, 25: 3.980,
          29: 5.040, 32: 6.230, 35: 7.510, 38: 8.950, 41: 10.500}

def unit_weight(dia):
    if dia in UNIT_W: return UNIT_W[dia]
    return math.pi * (dia/2.0)**2 * 7850e-9 * 1000.0     # 근사(원형 환산)

class Bar:
    """pts: [(x,y), ...] 폴리라인 정점. bend_r: 중심선 굽힘반지름(0이면 직각)."""
    def __init__(self, mark, dia, pts, count=1, bend_r=0.0, note=""):
        self.mark, self.dia, self.pts = mark, dia, list(pts)
        self.count, self.bend_r, self.note = count, bend_r, note

    def length_sharp(self):
        """직선 교차점 기준 (굽힘 무시) — 현재 엔진이 내는 값"""
        return sum(math.dist(self.pts[i], self.pts[i+1])
                   for i in range(len(self.pts)-1))

    def length_true(self):
        """굽힘 원호를 반영한 실제 절단길이.
           내각 t 의 코너에서 반지름 r 원호를 넣으면
             보정 = r*(pi - t) - 2*r/tan(t/2)   (음수 = 짧아짐)"""
        L = self.length_sharp()
        if self.bend_r <= 0 or len(self.pts) < 3:
            return L
        r = self.bend_r
        for i in range(1, len(self.pts)-1):
            a, b, c = self.pts[i-1], self.pts[i], self.pts[i+1]
            u = (a[0]-b[0], a[1]-b[1]); v = (c[0]-b[0], c[1]-b[1])
            nu = math.hypot(*u); nv = math.hypot(*v)
            if nu < 1e-9 or nv < 1e-9: continue
            cos_t = max(-1.0, min(1.0, (u[0]*v[0]+u[1]*v[1])/(nu*nv)))
            t = math.acos(cos_t)                       # 내각
            if t < 1e-6 or abs(t - math.pi) < 1e-6: continue
            tangent = r / math.tan(t/2.0)              # 코너에서 접점까지
            arc = r * (math.pi - t)
            L += arc - 2.0*tangent
        return L

    def n_bends(self):
        return max(0, len(self.pts) - 2)

def bom(bars, use_true=True):
    """부호별 집계. 반환: rows, totals"""
    g = {}
    for b in bars:
        k = (b.mark, b.dia)
        L = b.length_true() if use_true else b.length_sharp()
        e = g.setdefault(k, {'mark': b.mark, 'dia': b.dia, 'n': 0,
                             'Lsum': 0.0, 'Lmin': 1e18, 'Lmax': 0.0, 'bends': 0})
        e['n'] += b.count
        e['Lsum'] += L * b.count
        e['Lmin'] = min(e['Lmin'], L); e['Lmax'] = max(e['Lmax'], L)
        e['bends'] += b.n_bends() * b.count
    rows = []
    for e in sorted(g.values(), key=lambda z: (z['mark'], z['dia'])):
        e['W'] = e['Lsum']/1000.0 * unit_weight(e['dia'])
        e['Lavg'] = e['Lsum']/e['n'] if e['n'] else 0.0
        rows.append(e)
    tot = {'n': sum(r['n'] for r in rows),
           'Lsum': sum(r['Lsum'] for r in rows),
           'W': sum(r['W'] for r in rows),
           'bends': sum(r['bends'] for r in rows)}
    return rows, tot

def bom_text(rows, tot, title=""):
    out = []
    if title: out.append(title)
    out.append(f"{'부호':>5} {'지름':>5} {'개수':>5} {'평균길이':>9} {'최소':>8} {'최대':>8} "
               f"{'총연장(m)':>10} {'중량(kg)':>10} {'굽힘':>5}")
    out.append("-"*82)
    for r in rows:
        out.append(f"{r['mark']:>5} {'D'+str(r['dia']):>5} {r['n']:>5} {r['Lavg']:>9.0f} "
                   f"{r['Lmin']:>8.0f} {r['Lmax']:>8.0f} {r['Lsum']/1000:>10.1f} "
                   f"{r['W']:>10.1f} {r['bends']:>5}")
    out.append("-"*82)
    out.append(f"{'합계':>5} {'':>5} {tot['n']:>5} {'':>9} {'':>8} {'':>8} "
               f"{tot['Lsum']/1000:>10.1f} {tot['W']:>10.1f} {tot['bends']:>5}")
    return "\n".join(out)

# ── SVG 배근도 ───────────────────────────────────────────────────────────
def svg(path, outline, holes, ducts, bars, title, w=1100, pad=90):
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sc = (w - 2*pad) / (x1-x0)
    h = int((y1-y0)*sc + 2*pad) + 70
    X = lambda x: pad + (x-x0)*sc
    Y = lambda y: h - 70 - pad - (y-y0)*sc          # y 위로

    def poly(pts, **kw):
        d = " ".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in pts)
        a = " ".join(f'{k.replace("_","-")}="{v}"' for k, v in kw.items())
        return f'<polygon points="{d}" {a}/>'
    def pline(pts, **kw):
        d = " ".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in pts)
        a = " ".join(f'{k.replace("_","-")}="{v}"' for k, v in kw.items())
        return f'<polyline points="{d}" fill="none" {a}/>'

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="#0f172a"/>']
    s.append(f'<text x="{pad}" y="34" fill="#e2e8f0" font-family="sans-serif" '
             f'font-size="17" font-weight="700">{title}</text>')
    s.append(poly(outline, fill="#1e293b", stroke="#64748b", stroke_width="2"))
    for hl in holes:
        s.append(poly(hl, fill="#0f172a", stroke="#64748b", stroke_width="2"))
    for cx, cy, r in ducts:
        s.append(f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="{r*sc:.1f}" '
                 f'fill="#0f172a" stroke="#f59e0b" stroke-width="1.4"/>')
    COL = {'H': '#38bdf8', 'V': '#4ade80', 'O': '#f472b6', 'S': '#fbbf24'}
    for b in bars:
        c = COL.get(b.mark[0], '#e2e8f0')
        s.append(pline(b.pts, stroke=c, stroke_width=f"{max(1.0, b.dia*sc):.1f}",
                       stroke_linecap="round", stroke_linejoin="round", opacity="0.9"))
    # 범례
    lx, ly = pad, h - 40
    for i, (k, c) in enumerate(COL.items()):
        s.append(f'<line x1="{lx+i*150}" y1="{ly}" x2="{lx+i*150+26}" y2="{ly}" '
                 f'stroke="{c}" stroke-width="4" stroke-linecap="round"/>')
        s.append(f'<text x="{lx+i*150+34}" y="{ly+5}" fill="#94a3b8" '
                 f'font-family="sans-serif" font-size="12">{k}</text>')
    s.append('</svg>')
    open(path, 'w').write("\n".join(s))
    return path
