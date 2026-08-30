# 제4장 수렴성 및 안정성

**H2'.** 장애물이 존재할 때의 수렴성을 세 단계로 나누어 다룬다 — (a) 수치안정성,
(b) 기하학적 도달가능성, (c) 군집 장애물 채터링. 폐기된 H7 은 H1 과 H2' 로 흡수되었다.

## 4.1 H2'-a — 수치안정성 (파라미터 안정조건 유도)

### 가정 (A1) — 목표 동결

3.4절의 목표 $T(\mathbf{x},\mathbf{n})$ 은 상태에 의존하므로 인력항의 정확한 기울기는

$$\nabla U_{\text{attr}} = k\,\Big(I - \frac{\partial T}{\partial \mathbf{x}}\Big)^{\!\top} (\mathbf{x} - T)$$

이다. 구현은 매 스텝 $T$ 를 상수로 두고 $k(\mathbf{x}-T)$ 만 쓴다. 즉
**$\partial T/\partial \mathbf{x} = 0$ 을 가정**한다. 이 절의 안정조건은 모두 이 가정 위에 있고,
가정이 깨지는 곳이 4.3이다. 그 오차를 먼저 정량화해 둔다.

### 명제 4.1 (평면 벽에서의 정확한 기울기)

$\gamma^{*}$ 가 평면(직선) 조각이고 $\mathbf{n}$ 이 고정일 때, 적층이 없으면
$U_{\text{attr}} = \tfrac12 k\tau^{2}$ 이고 $\nabla \tau = -\mathbf{n}_{\gamma}/(\mathbf{d}\cdot\mathbf{n}_{\gamma})$ 이므로

$$\mathbf{F} = -\nabla U_{\text{attr}}
 = \frac{k\,\tau}{\mathbf{d}\cdot\mathbf{n}_{\gamma}}\;\mathbf{n}_{\gamma},
\qquad \lVert \mathbf{F} \rVert = \frac{k\,\tau}{|\cos\theta|}$$

여기서 $\theta$ 는 광선과 벽 법선 사이의 입사각이다. 반면 구현이 가하는 힘은
$\mathbf{F}_{\text{code}} = k\,\tau\,\mathbf{d}$ 이다. 둘의 관계는

| 비교 | 결과 |
|---|---|
| 방향 | 정확한 힘은 **벽 법선** $\mathbf{n}_{\gamma}$, 구현은 **광선** $\mathbf{d}$ — 정확히 $\theta$ 만큼 어긋난다 |
| 크기 | $\lVert\mathbf{F}\rVert / \lVert\mathbf{F}_{\text{code}}\rVert = 1/\cos\theta$ — 구현이 그만큼 작다 |
| 일치 | $\theta = 0$ (수직 입사)일 때만 |

수치 확인(수치미분 대 닫힌형, 오차 $10^{-3}$ 이내):

| $\theta$ | $\lvert\cos\theta\rvert$ | 크기비 | 방향차 |
|---|---|---|---|
| $0^\circ$ | 1.000 | 1.000 | $0^\circ$ |
| $20^\circ$ | 0.940 | 1.064 | $20^\circ$ |
| $40^\circ$ | 0.766 | 1.305 | $40^\circ$ |
| $53.13^\circ$ | 0.600 | 1.667 | $53.13^\circ$ |

마지막 줄이 3.2절 $\alpha_{\text{th}} = -0.6$ 이 허용하는 한계다. 즉 **허용 한계에서 구현의 힘은
방향이 $53^\circ$ 어긋나고 크기가 1.67배 작다.** $|\cos|$ 이 같은 양으로 3.4절의 적층 후퇴
($s/\cos$)와 구현의 폴백 임계 $|\cos| > 0.2$(`physics.js:213`)에도 나타난다 — 임계 0.2 에서는
5배다. 세 곳에 같은 $1/\cos$ 이 걸리므로, $\alpha_{\text{th}}$ 는 방향정합성(3.2)만의 문제가
아니라 **동결 가정의 오차 한계를 정하는 값**이기도 하다.

> 작성 예정: 곡선 조각($\gamma^{*}$ 가 이산화된 원호)에서의 대응 명제. 위 유도는 평면 조각에
> 한정된다.

### 이산시간 동역학

현재 구현값은 `macroBIM/macroBIM` 의 `domain.js:8` 에 있다.

```js
PHYSICS: { GRAVITY_K: 0.08, DAMPING: 0.80, CONVERGE: 0.2, NODE_POS: [0.4, 0.6] }
```

target 이 국소적으로 고정되어 있다고 가정하고 선형화하면, 이산시간 동역학은 다음과 같다.

$$v_{n+1} = D\,(v_n + K\,e_n), \qquad e_{n+1} = e_n - v_{n+1}$$

여기서 $K=$ `GRAVITY_K`, $D=$ `DAMPING` 이다. 상태 $(e_n, v_n)$ 에 대한 천이행렬은

$$A = \begin{bmatrix} 1 - DK & -D \\ DK & D \end{bmatrix},
\qquad \det A = D, \qquad \operatorname{tr} A = 1 + D(1-K)$$

안정조건은 고유값이 단위원 안에 있는 것이다.

$$|\lambda_{1,2}| < 1$$

**Jury 안정성 판정**으로 $K$ 와 $D$ 에 대한 닫힌형 부등식을 유도한다.

> **미완료 — 다음 작업 2순위.** 지금까지 계획만 있었고 실제 유도는 하지 않았다.
> 유도 후 현재값 $K=0.08$, $D=0.80$ 이 그 부등식을 만족하는지 검증해야 한다.

**`CONVERGE`(=0.2) 의 정당화.**

- **하한**: `CONVERGE` < 시공허용오차(KS/BS 기준) 라는 부등식으로 정당화한다.
- **상한**: 반복횟수–정확도 trade-off 곡선의 knee point 로 결정한다.

## 4.2 H2'-b — 기하학적 도달가능성 (장애물 배치 실패모드)

검증해야 할 실패모드는 일곱 가지다.

| # | 실패모드 | 발생 조건 / 대상 단면 |
|---|---|---|
| 1 | Obstacle-in-path | 세그먼트와 attractor 사이를 장애물이 직접 가로막음 (기본 케이스, 3단면 공통) |
| 2 | GNRON (Goal Non-Reachable with Obstacles Nearby) | 덕트가 피복선에 바짝 붙은 경우 |
| 3 | 대칭 트랩 (symmetric saddle point) | 대칭 단면의 중심선 위 (박스거더, I빔) |
| 4 | 좁은 통로 (narrow corridor) | 인접 덕트 사이 간격이 좁음 (중공교각) |
| 5 | 오목 포켓 (concave trap) | I빔 web reflex corner — **이미 확인됨** |
| 6 | 장애물 밀집 (high-density cluster) | Monte Carlo / Sobol sequence 로 통계 검증 |
| 7 | 반발영역 중첩 | 초기위치가 여러 반발영역이 겹치는 구간에 있는 경우 |

모드 6 의 표본수는 조건당 약 400회로 둔다 — 95% 신뢰수준, 오차 5% 기준의 표본크기 공식에서
산출한 값이며 임의로 정한 수가 아니다.

## 4.3 H2'-c — 군집 장애물 채터링 문제와 해법 (그룹 무게중심 반발장)

세 단계 중 **가장 중요한 신규 기여**다.

**발견 경위.** PSC I빔 실제 단면(덕트 3개, 2단 배치 포함)을 검토하다 발견했다. 2단으로 인접한
덕트 사이에 철근이 들어가면, 매 스텝마다 target 이 위 덕트 ↔ 아래 덕트로 스위칭되며 힘의 방향이
계속 뒤집힌다 — **채터링(chattering)**.

**진동(oscillation)과 다르다.** 진동은 하나의 target 주변을 왔다갔다 하는 것이고, 채터링은
**target 선택 로직 자체의 불연속적 전환**이 원인이다. 3.1절이 나열한 광선 투사의 불연속 세
가지 중 두 번째(광선이 조각의 끝점을 스치는 위치)에 해당한다 — 2단 덕트 사이에서는 위·아래
덕트의 피복선 조각이 광선의 양쪽에 놓여, 미세한 변위가 $\gamma^{*}$ 를 통째로 바꾼다.
따라서 4.1의 가정 (A1)이 여기서 무효화된다. $\partial T/\partial \mathbf{x}$ 가 큰 것이 아니라
**존재하지 않는다**(불연속)는 점이 본질이다.

**이론적 배경.**

- Rimon & Koditschek (1992, IEEE T-RA), *Exact robot navigation using artificial potential
  functions* — navigation function 하에서 critical point 는 목표점(minimum) 하나와
  안장점(saddle point)들뿐이며, 안장점은 항상 작은 섭동으로 탈출 가능함이 보장된다.
- Kim & Khosla (1991) — 조화함수($\nabla^2 U = 0$) 포텐셜은 최댓값 원리에 의해 내부에 진짜
  local minimum 이 존재할 수 없다.

**채택된 해법: 그룹 무게중심 반발장(group-centroid repulsion field).**

1. 인접 장애물을 간격 임계값(예: 2×피복두께) 기준 connected-component 로 **자동 그룹핑**한다.
   사람이 수동으로 라벨링하지 않는다는 점이 핵심이다.
2. 그룹 무게중심은 그룹 내 장애물 중심들의 면적가중 평균이다.

$$\mathbf{c}_{\text{group}} = \frac{\sum_{i \in G} a_i\, \mathbf{x}_i}{\sum_{i \in G} a_i}$$

3. 척력은 **혼합(hybrid) 구조**로 둔다.

$$U_{\text{rep}} = \underbrace{U_{\text{rep,group}}}_{\text{원거리, 무게중심 기반}}
  \;+\; \underbrace{\sum_{i \in G} U_{\text{rep},i}}_{\text{근거리, 개별 피복조건}}$$

그룹장 하나만 쓰면 비대칭 클러스터에서 개별 피복을 위반할 위험이 있으므로 근거리 개별항과
반드시 결합해야 한다. 원거리 항이 여러 개의 경쟁하는 극값을 하나의 매끄러운 지형으로 합쳐
채터링을 **구조적으로 사전 방지**한다.

**기각된 대안.**

| 대안 | 기각 사유 |
|---|---|
| 수동 $\varphi$(편향방향) 라벨링 | 사람이 매번 판단해야 함 |
| Hessian 고유벡터 기반 자동 안장점 탈출 | 이론적으로 우아하나 사후 대응 — 그룹 반발장이 사전 방지로 더 근본적. 보조 안전장치로는 재고 가능 |
| 무작위 섭동 | 이론적 근거 약함, 최후 수단 |

**의도적으로 스코프 밖에 둔 것 — RAF(Rebar-Attractive Field).** 덕트 지지철근처럼 철근이
콘크리트 경계가 아니라 다른 철근·덕트에 인력되어야 하는, 역할 기반 인력/척력 이중성 개념이다.
longitudinal rebar 사례연구 이후로 미루고, 논문에는 확장 가능성(extensibility)으로만 명시하며
증명·구현은 하지 않는다.

> **다음 작업 1순위.** 그룹 무게중심 반발장을 `physics.js` 에 구현한다 — 자동 그룹핑
> (간격 임계값 기반 connected-component), 원거리(그룹)+근거리(개별) 혼합 포텐셜.
> 테스트는 7.3 의 슬래브–복부 접합부 단면(2단 덕트)으로 하고, 구현 전후의
> $|\mathbf{x}_n - \mathbf{x}_{n-1}|$ 시계열을 비교해 채터링 해소를 확인한다.

## 4.4 파라미터 결합 민감도 분석

- 대상: $\alpha_{\text{th}}$, `GRAVITY_K`, `DAMPING`, `CONVERGE`, 그룹핑 간격 임계값.
- 방법: 1인자 스윕 + 2인자 격자. 응답은 수렴 반복수, 수렴 실패율, 최종 간섭·피복 위반 건수.
- 4.1 의 Jury 부등식이 예측하는 안정영역과 실측 수렴영역이 일치하는지를 함께 확인한다.
