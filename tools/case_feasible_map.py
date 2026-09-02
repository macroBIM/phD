#!/usr/bin/env python3
"""
case_feasible_map.py — "손으로 그리면 되는 쉬운 문제인가"를 재본다.

도면에는 덕트 간격만 적힌다. 그 사이로 철근이 지나갈 수 있는지는 철근
지름과 피복에 함께 달려 있고, 그 경계는 도면을 봐서는 알 수 없다.
간격 x 지름 평면에서 가능/불가능 경계를 그린다.
"""
import sys, math; sys.path.insert(0, ".")
from admissible import Section, corridor
import case_boxgirder as C

KS = {"D13":12.7,"D16":15.9,"D19":19.1,"D22":22.2,"D25":25.4,"D29":28.6,"D32":31.8,"D35":34.9,"D41":41.3}
GAPS = [140, 160, 180, 200, 220, 240, 260, 280, 300]     # 덕트 중심 간 거리(도면에 적히는 값)

print("가로 = 덕트 중심간 거리(mm, 도면값) / 세로 = 철근 지름")
print("○ 통과 가능, ✕ 통과 불가, 숫자는 여유(mm)\n")
hdr = "        " + "".join(f"{g:>7}" for g in GAPS)
print(hdr); print("        " + "".join(f"{'(' + str(round(C.gap_between(Section(C.OUTER,[C.VOID],C.ducts(g),C.COVER),0,1))) + ')':>7}" for g in GAPS))
rows = {}
for name, phi in KS.items():
    line, vals = f"{name:>7} ", []
    for g in GAPS:
        sec = Section(C.OUTER, [C.VOID], C.ducts(g), C.COVER)
        cl, _ = corridor(sec, 0, 1, phi)
        vals.append(cl)
        line += f"{('○' if cl >= 0 else '✕'):>7}"
    rows[name] = vals
    print(line)
print("\n여유(mm) 상세")
print(hdr)
for name, vals in rows.items():
    print(f"{name:>7} " + "".join(f"{v:>7.0f}" for v in vals))

print("\n── 같은 도면에서 지름만 바꾸면 뒤집히는 구간 ──")
for gi, g in enumerate(GAPS):
    ok = [n for n in KS if rows[n][gi] >= 0]
    ng = [n for n in KS if rows[n][gi] < 0]
    if ok and ng:
        print(f"  덕트 간격 {g}mm : 가능 {','.join(ok)}  /  불가 {','.join(ng)}")
