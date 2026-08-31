#!/usr/bin/env python3
"""
case_holesweep.py — "중공이 크던 작던 무관한가"를 수치로 확인한다.

직사각 단면 가운데에 원형 중공을 두고 반경을 키우면서 허용영역 A 의
면적과 연결성분을 본다. I형(충실) → 박스(중공)로 가는 연속 변형이다.
"""
import sys; sys.path.insert(0, ".")
from admissible import Section, admissible_grid, components

W, H = 3000.0, 2000.0
COVER = {'outer': 50.0, 'void': 40.0, 'duct': 40.0}
OUTER = [(-W/2, 0), (W/2, 0), (W/2, H), (-W/2, H)]
PHI = 31.8                                    # D32

def run(r, step=10.0):
    ducts = [] if r <= 0 else [(0.0, H/2, r)]
    sec = Section(OUTER, [], ducts, COVER)
    grid, _, xywh = admissible_grid(sec, PHI, step)
    comps = components(grid)
    return sum(len(c) for c in comps)*step*step/1e6, len(comps)

# 닫힌형 예측: 중공 피복대와 외곽 피복대가 만나는 반경
r_pred = (H/2 - COVER['outer'] - PHI/2) - (COVER['duct'] + PHI/2)
print(f"닫힌형 임계반경 예측  r_c = (H/2 − c_out − φ/2) − (c_hole + φ/2) = {r_pred:.1f} mm\n")
print(f"{'중공 반경 r':>12} {'중공/높이':>10} {'허용면적(m²)':>14} {'연결성분':>9}  비고")
prev = None
for r in [0, 25, 50, 100, 200, 400, 600, 800, 860, 870, 875, 880, 885, 890, 900, 930]:
    a, n = run(r)
    note = ""
    if prev is not None and n != prev:
        note = f"← 위상 전이 ({prev}→{n})"
    prev = n
    print(f"{r:12.0f} {2*r/H:10.2f} {a:14.3f} {n:9d}  {note}")

def band_clearance(r, phi=PHI):
    """중공 위쪽 띠에서 남는 여유(해석적). 0 이 되는 r 이 위상 전이 임계."""
    top_limit = H - COVER['outer'] - phi/2          # 외곽 피복대 안쪽 한계
    hole_limit = H/2 + r + COVER['duct'] + phi/2    # 중공 피복대 바깥 한계
    return top_limit - hole_limit

if __name__ == "__main__" and "--refine" in sys.argv:
    print("\n해석적 확인 — 중공 위 띠의 여유 (격자 없이)")
    print(f"{'r':>10} {'여유(mm)':>12} {'격자(10mm) 성분':>16}")
    for r in (860, 870, 875, 878, 878.2, 879, 885):
        _, n = run(r)
        print(f"{r:10.1f} {band_clearance(r):12.2f} {n:16d}")
    print(f"\n여유 = 0 인 반경 = {H/2 - COVER['outer'] - COVER['duct'] - PHI:.1f} mm  (닫힌형)")
    print("격자는 이보다 이르게 끊긴다 — 남은 띠가 격자 간격보다 얇으면 셀이 잡히지 않는다.")
    for st in (10.0, 5.0, 2.0):
        _, n = run(876.0, st)
        print(f"   r=876.0 (여유 {band_clearance(876.0):.1f}mm) 에서 격자 {st}mm → 성분 {n}")
