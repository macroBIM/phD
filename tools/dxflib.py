#!/usr/bin/env python3
"""
dxflib.py — 철근 배근도 DXF(R12 / AC1009) 출력. 표준 라이브러리만 사용.

macroBIM 의 bim_dxf.js 와 같은 플랫(AC1009)을 낸다. R12 에는 LWPOLYLINE 이
없으므로 철근은 LINE + ARC 로 그린다 — 실무 배근도 관례(중심선 1개)와도 일치하고,
굽힘 원호를 실제 엔티티로 넣으므로 rebarlib.length_true() 와 기하가 일치한다.

fillet(): 폴리라인 정점 + 굽힘반지름 → (LINE, ARC) 목록
"""
import math

def g(code, val):
    return f"{code}\n{val}\n"

class Dxf:
    def __init__(self):
        self.layers = []          # (name, aci color, ltype)
        self.ents = []

    def layer(self, name, color, ltype="CONTINUOUS"):
        self.layers.append((name, color, ltype.upper())); return self

    def line(self, x1, y1, x2, y2, lay="0"):
        self.ents.append(g(0,"LINE")+g(8,lay)+g(10,f"{x1:.4f}")+g(20,f"{y1:.4f}")
                         +g(11,f"{x2:.4f}")+g(21,f"{y2:.4f}"))

    def circle(self, cx, cy, r, lay="0"):
        self.ents.append(g(0,"CIRCLE")+g(8,lay)+g(10,f"{cx:.4f}")+g(20,f"{cy:.4f}")
                         +g(40,f"{r:.4f}"))

    def arc(self, cx, cy, r, a0, a1, lay="0"):
        """a0,a1 = degree, DXF 는 항상 a0 -> a1 반시계"""
        self.ents.append(g(0,"ARC")+g(8,lay)+g(10,f"{cx:.4f}")+g(20,f"{cy:.4f}")
                         +g(40,f"{r:.4f}")+g(50,f"{a0:.4f}")+g(51,f"{a1:.4f}"))

    def text(self, x, y, h, s, lay="0", rot=0.0):
        self.ents.append(g(0,"TEXT")+g(8,lay)+g(10,f"{x:.4f}")+g(20,f"{y:.4f}")
                         +g(40,f"{h:.4f}")+g(1,str(s))+g(50,f"{rot:.4f}"))

    def polyline(self, pts, lay="0", closed=False):
        n = len(pts)
        for i in range(n-1 if not closed else n):
            a, b = pts[i], pts[(i+1) % n]
            self.line(a[0], a[1], b[0], b[1], lay)

    def bar(self, pts, r_bend, lay="0"):
        """굽힘 원호를 실제 ARC 로 넣어 철근 1본을 그린다."""
        for kind, d in fillet(pts, r_bend):
            if kind == 'L': self.line(*d, lay)
            else:           self.arc(*d, lay)

    def save(self, path):
        s  = g(0,"SECTION")+g(2,"HEADER")+g(9,"$ACADVER")+g(1,"AC1009")+g(0,"ENDSEC")
        t  = g(0,"SECTION")+g(2,"TABLES")
        t += g(0,"TABLE")+g(2,"LTYPE")+g(70,1)
        t += g(0,"LTYPE")+g(2,"CONTINUOUS")+g(70,0)+g(3,"Solid")+g(72,65)+g(73,0)+g(40,0.0)
        t += g(0,"ENDTAB")
        t += g(0,"TABLE")+g(2,"LAYER")+g(70,len(self.layers))
        for nm, col, lt in self.layers:
            t += g(0,"LAYER")+g(2,nm)+g(70,0)+g(62,col)+g(6,lt)
        t += g(0,"ENDTAB")+g(0,"ENDSEC")
        b  = g(0,"SECTION")+g(2,"ENTITIES") + "".join(self.ents) + g(0,"ENDSEC")
        open(path,'w').write(s+t+b+g(0,"EOF"))
        return path

# ── 굽힘 필렛 ────────────────────────────────────────────────────────────
def fillet(pts, r):
    """폴리라인 → [('L',(x1,y1,x2,y2)), ('A',(cx,cy,r,a0,a1)), ...]
       r<=0 이거나 정점 2개면 직선만."""
    out = []
    n = len(pts)
    if n < 2: return out
    if r <= 0 or n == 2:
        for i in range(n-1):
            out.append(('L', (pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])))
        return out

    cur = pts[0]
    for i in range(1, n-1):
        A, B, C = pts[i-1], pts[i], pts[i+1]
        ux, uy = A[0]-B[0], A[1]-B[1]; nu = math.hypot(ux,uy)
        vx, vy = C[0]-B[0], C[1]-B[1]; nv = math.hypot(vx,vy)
        if nu < 1e-9 or nv < 1e-9: continue
        ux, uy = ux/nu, uy/nu; vx, vy = vx/nv, vy/nv
        cost = max(-1.0, min(1.0, ux*vx + uy*vy))
        t = math.acos(cost)                              # 내각
        if t < 1e-6 or abs(t-math.pi) < 1e-6:            # 직선 — 필렛 없음
            continue
        d  = r / math.tan(t/2.0)                          # 코너→접점
        d  = min(d, nu*0.999, nv*0.999)                   # 인접 변보다 길면 축소
        rr = d * math.tan(t/2.0)
        P1 = (B[0]+ux*d, B[1]+uy*d)                       # A 쪽 접점
        P2 = (B[0]+vx*d, B[1]+vy*d)                       # C 쪽 접점
        bx, by = ux+vx, uy+vy; nb = math.hypot(bx,by)
        if nb < 1e-9: continue
        bx, by = bx/nb, by/nb
        O = (B[0]+bx*rr/math.sin(t/2.0), B[1]+by*rr/math.sin(t/2.0))
        a0 = math.degrees(math.atan2(P1[1]-O[1], P1[0]-O[0])) % 360.0
        a1 = math.degrees(math.atan2(P2[1]-O[1], P2[0]-O[0])) % 360.0
        # DXF ARC 는 a0->a1 반시계. 짧은 호(=pi-t)가 되도록 방향 선택
        cross = (P1[0]-O[0])*(P2[1]-O[1]) - (P1[1]-O[1])*(P2[0]-O[0])
        if cross < 0: a0, a1 = a1, a0
        out.append(('L', (cur[0], cur[1], P1[0], P1[1])))
        out.append(('A', (O[0], O[1], rr, a0, a1)))
        cur = P2
    out.append(('L', (cur[0], cur[1], pts[-1][0], pts[-1][1])))
    return out

def fillet_length(pts, r):
    """fillet 결과의 총 길이 — rebarlib.length_true() 와 대조용"""
    L = 0.0
    for kind, d in fillet(pts, r):
        if kind == 'L':
            L += math.hypot(d[2]-d[0], d[3]-d[1])
        else:
            cx, cy, rr, a0, a1 = d
            sweep = (a1 - a0) % 360.0
            L += math.radians(sweep) * rr
    return L

# ── 3D: 철근을 진짜 원통 메시로 ─────────────────────────────────────────
def _unit(v):
    n = math.sqrt(sum(c*c for c in v)) or 1.0
    return tuple(c/n for c in v)

def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def path3d(pts, r_bend, z=0.0, arc_seg=6):
    """2D 폴리라인 + 굽힘반지름 → 3D 중심선 점열 (원호를 arc_seg 등분)"""
    P = []
    for kind, d in fillet(pts, r_bend):
        if kind == 'L':
            x1,y1,x2,y2 = d
            if not P: P.append((x1,y1,z))
            P.append((x2,y2,z))
        else:
            cx,cy,rr,a0,a1 = d
            sweep = (a1-a0) % 360.0
            for i in range(arc_seg+1):
                a = math.radians(a0 + sweep*i/arc_seg)
                p = (cx+rr*math.cos(a), cy+rr*math.sin(a), z)
                if not P or math.dist(P[-1], p) > 1e-9: P.append(p)
    # 중복 제거
    Q = [P[0]]
    for p in P[1:]:
        if math.dist(Q[-1], p) > 1e-9: Q.append(p)
    return Q

def tube_faces(path, radius, sides=8):
    """중심선 점열 → 원통 표면 사각형 목록. 평행이송 프레임으로 비틀림 방지."""
    n = len(path)
    if n < 2: return []
    # 초기 프레임
    t0 = _unit(tuple(path[1][i]-path[0][i] for i in range(3)))
    ref = (0.0,0.0,1.0) if abs(t0[2]) < 0.9 else (1.0,0.0,0.0)
    u = _unit(_cross(t0, ref)); v = _cross(t0, u)
    rings, prev_t = [], t0
    for k in range(n):
        if k == 0:                 t = t0
        elif k == n-1:             t = _unit(tuple(path[k][i]-path[k-1][i] for i in range(3)))
        else:                      t = _unit(tuple(path[k+1][i]-path[k-1][i] for i in range(3)))
        # 평행이송: 이전 접선 -> 현재 접선 회전을 u,v 에 적용 (로드리게스)
        ax = _cross(prev_t, t); s = math.sqrt(sum(c*c for c in ax))
        if s > 1e-9:
            ax = tuple(c/s for c in ax)
            ang = math.atan2(s, sum(prev_t[i]*t[i] for i in range(3)))
            ca, sa = math.cos(ang), math.sin(ang)
            def rot(w):
                d = sum(ax[i]*w[i] for i in range(3)); cr = _cross(ax, w)
                return tuple(w[i]*ca + cr[i]*sa + ax[i]*d*(1-ca) for i in range(3))
            u, v = rot(u), rot(v)
        prev_t = t
        ring = []
        for j in range(sides):
            a = 2*math.pi*j/sides
            ring.append(tuple(path[k][i] + radius*(math.cos(a)*u[i] + math.sin(a)*v[i])
                              for i in range(3)))
        rings.append(ring)
    faces = []
    for k in range(n-1):
        for j in range(sides):
            j2 = (j+1) % sides
            faces.append((rings[k][j], rings[k][j2], rings[k+1][j2], rings[k+1][j]))
    return faces

def _face3d(f, lay):
    s = g(0,"3DFACE")+g(8,lay)
    for i,p in enumerate(f):
        s += g(10+i, f"{p[0]:.3f}") + g(20+i, f"{p[1]:.3f}") + g(30+i, f"{p[2]:.3f}")
    return s

class Dxf3D(Dxf):
    def tube(self, pts2d, r_bend, dia, z=0.0, lay="0", sides=8):
        P = path3d(pts2d, r_bend, z)
        for f in tube_faces(P, dia/2.0, sides):
            self.ents.append(_face3d(f, lay))
        return self

    def prism(self, ring2d, z0, z1, lay="0"):
        """2D 링을 z0~z1 로 압출 (콘크리트 형상)"""
        n = len(ring2d)
        for i in range(n):
            a, b = ring2d[i], ring2d[(i+1) % n]
            self.ents.append(_face3d([(a[0],a[1],z0),(b[0],b[1],z0),
                                      (b[0],b[1],z1),(a[0],a[1],z1)], lay))
        return self
