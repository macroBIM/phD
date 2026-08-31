#!/usr/bin/env python3
"""
admissible.py — 부록 A.6 1단계: 덕트를 포함한 허용영역 A 의 계산과 진단

  A(phi) = { x in Omega : dist(x, 경계) >= c(경계) + phi/2 for all 경계 }

경계는 종류별로 자기 피복을 갖는다. 덕트·개구부는 특별 취급이 없다 —
경계 목록에 한 줄 더 들어갈 뿐이며, 그 결과로 A 에 구멍이 뚫린다(회피가
알고리즘이 아니라 정의역의 성질이 된다).

의존성 없음(표준 라이브러리만). 출력: 통계(stdout) + SVG.
"""
import math, json, sys

# ── 기하 원시 ────────────────────────────────────────────────────────────
def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx*dx + dy*dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy) / L2))
    qx, qy = x1 + t*dx, y1 + t*dy
    return math.hypot(px-qx, py-qy)

def in_ring(px, py, ring):
    """짝수-홀수 규칙(ray casting)."""
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i+1) % n]
        if (y1 > py) != (y2 > py):
            xin = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xin:
                inside = not inside
    return inside

def ring_edges(ring):
    n = len(ring)
    return [(ring[i][0], ring[i][1], ring[(i+1) % n][0], ring[(i+1) % n][1]) for i in range(n)]

# ── 단면 정의 ────────────────────────────────────────────────────────────
class Section:
    """outer: 콘크리트 외곽 링, voids: 중공(셀) 링들, ducts: (cx, cy, r)"""
    def __init__(self, outer, voids, ducts, cover):
        self.outer, self.voids, self.ducts = outer, voids, ducts
        self.cover = cover                      # {'outer':..,'void':..,'duct':..}
        self.e_out = ring_edges(outer)
        self.e_void = [ring_edges(v) for v in voids]

    def inside_concrete(self, x, y):
        if not in_ring(x, y, self.outer):
            return False
        for v in self.voids:
            if in_ring(x, y, v):
                return False
        for cx, cy, r in self.ducts:
            if math.hypot(x-cx, y-cy) <= r:
                return False
        return True

    def clearance(self, x, y, phi):
        """모든 경계에 대해 (거리 − 요구피복 − phi/2) 의 최소값. 0 이상이면 허용."""
        need = phi / 2.0
        m = min(seg_dist(x, y, *e) for e in self.e_out) - self.cover['outer'] - need
        for ev in self.e_void:
            m = min(m, min(seg_dist(x, y, *e) for e in ev) - self.cover['void'] - need)
        for cx, cy, r in self.ducts:
            m = min(m, (math.hypot(x-cx, y-cy) - r) - self.cover['duct'] - need)
        return m

# ── 격자 · 연결성분 · 진단 ───────────────────────────────────────────────
def admissible_grid(sec, phi, step):
    xs = [p[0] for p in sec.outer]; ys = [p[1] for p in sec.outer]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    nx = int((x1-x0)/step) + 1; ny = int((y1-y0)/step) + 1
    grid, clear = [], []
    for j in range(ny):
        y = y0 + j*step
        row, crow = [], []
        for i in range(nx):
            x = x0 + i*step
            if sec.inside_concrete(x, y):
                c = sec.clearance(x, y, phi)
                row.append(c >= 0.0); crow.append(c)
            else:
                row.append(False); crow.append(float('-inf'))
        grid.append(row); clear.append(crow)
    return grid, clear, (x0, y0, nx, ny)

def components(grid):
    ny, nx = len(grid), len(grid[0])
    seen = [[False]*nx for _ in range(ny)]
    comps = []
    for j in range(ny):
        for i in range(nx):
            if grid[j][i] and not seen[j][i]:
                stack, cells = [(i, j)], []
                seen[j][i] = True
                while stack:
                    a, b = stack.pop(); cells.append((a, b))
                    for da, db in ((1,0), (-1,0), (0,1), (0,-1)):
                        p, q = a+da, b+db
                        if 0 <= p < nx and 0 <= q < ny and grid[q][p] and not seen[q][p]:
                            seen[q][p] = True; stack.append((p, q))
                comps.append(cells)
    comps.sort(key=len, reverse=True)
    return comps

def report(name, sec, phi, step):
    grid, clear, (x0, y0, nx, ny) = admissible_grid(sec, phi, step)
    comps = components(grid)
    area = sum(len(c) for c in comps) * step * step
    conc = sum(1 for j in range(ny) for i in range(nx)
               if sec.inside_concrete(x0+i*step, y0+j*step)) * step * step
    print(f"[{name}] phi={phi:>4.1f}  격자={step}mm  "
          f"허용면적={area/1e6:8.3f} m²  (콘크리트의 {area/conc*100:5.1f}%)  "
          f"연결성분={len(comps):>3}개  최대성분={len(comps[0])*step*step/1e6 if comps else 0:.3f} m²")
    return grid, clear, (x0, y0, nx, ny), comps

# ── SVG 출력 (행 단위 run-length 로 사각형 수를 줄인다) ──────────────────
def svg(path, sec, grid, xywh, step, title, box=None):
    x0, y0, nx, ny = xywh
    xs = [p[0] for p in sec.outer]; ys = [p[1] for p in sec.outer]
    W, H = max(xs)-min(xs), max(ys)-min(ys)
    pad = 400
    vb = (f"{box[0]} {-box[1]-box[3]} {box[2]} {box[3]}" if box
          else f"{min(xs)-pad} {-max(ys)-pad} {W+2*pad} {H+2*pad}")
    def ring_path(r):
        return "M " + " L ".join(f"{x:.1f},{-y:.1f}" for x, y in r) + " Z"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="1100">',
           f'<rect x="{min(xs)-pad}" y="{-max(ys)-pad}" width="{W+2*pad}" height="{H+2*pad}" fill="#ffffff"/>',
           f'<path d="{ring_path(sec.outer)}" fill="#eceff3" stroke="#334" stroke-width="18"/>']
    for v in sec.voids:
        out.append(f'<path d="{ring_path(v)}" fill="#ffffff" stroke="#334" stroke-width="18"/>')
    out.append('<g fill="#1f6feb" fill-opacity="0.55">')
    for j in range(ny):
        if box and not (box[1]-step <= y0+j*step <= box[1]+box[3]):
            continue
        i = 0
        while i < nx:
            if grid[j][i]:
                k = i
                while k+1 < nx and grid[j][k+1]:
                    k += 1
                if not box or (x0+(k+1)*step >= box[0] and x0+i*step <= box[0]+box[2]):
                    out.append(f'<rect x="{x0+i*step:.1f}" y="{-(y0+j*step)-step:.1f}" '
                               f'width="{(k-i+1)*step:.1f}" height="{step:.1f}"/>')
                i = k+1
            else:
                i += 1
    out.append('</g>')
    for cx, cy, r in sec.ducts:
        out.append(f'<circle cx="{cx:.1f}" cy="{-cy:.1f}" r="{r:.1f}" fill="#d0d5dc" stroke="#8a9098" stroke-width="12"/>')
    tx, ty, fs = (box[0]+box[2]*0.03, -(box[1]+box[3])+box[3]*0.075, box[3]*0.038) if box else (min(xs), -max(ys)-120, 200)
    out.append(f'<text x="{tx:.0f}" y="{ty:.0f}" font-family="sans-serif" font-size="{fs:.0f}" fill="#23272f">{title}</text>')
    out.append('</svg>')
    open(path, "w").write("\n".join(out))

# ── 국소 진단 ────────────────────────────────────────────────────────────
def corridor(sec, i, j, phi, n=200):
    """덕트 i–j 를 잇는 선분 위에서 최대 여유를 본다.
    전역 연결성분은 '돌아가면 되므로' 막힘을 못 잡는다. 통로는 국소로 봐야 한다."""
    (x1, y1, _), (x2, y2, _) = sec.ducts[i], sec.ducts[j]
    best = float('-inf'); at = None
    for k in range(n+1):
        t = k/n
        x, y = x1 + t*(x2-x1), y1 + t*(y2-y1)
        if not sec.inside_concrete(x, y):
            continue
        c = sec.clearance(x, y, phi)
        if c > best:
            best, at = c, (x, y)
    return best, at

def components_in(sec, grid, xywh, step, keep):
    """관심 영역(keep(x,y)=True) 안에서만 연결성분을 센다 — 복부처럼 철근이
    반드시 지나야 하는 띠가 덕트에 의해 갈라지는지를 본다."""
    x0, y0, nx, ny = xywh
    sub = [[grid[j][i] and keep(x0+i*step, y0+j*step) for i in range(nx)] for j in range(ny)]
    return components(sub)
