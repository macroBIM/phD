# 제3장 Cover-Attractive Field 이론 정식화

## 3.1 포텐셜 함수 정의

Cover-Attractive Field(이하 CAF)의 인력항은 **피복선까지의 방향성 광선거리**로 정의한다.
아래 정의는 구현(`macroBIM/macroBIM`, `physics.js:155` `getGravityTarget`)과 1:1로 대응한다.

### 기호

| 기호 | 뜻 |
|---|---|
| $\Omega \subset \mathbb{R}^2$ | 단면 영역 |
| $w$, $\mathbf{n}_w$, $c_w$ | 콘크리트 벽 선분, 그 안쪽 법선, 그 벽의 피복두께 |
| $\phi$, $S$ | 현재 철근 지름, 기배근 스택(`wallStack`) |
| $\mathbf{x}$, $\mathbf{n}$ | 철근 노드 위치, 그 세그먼트의 법선 방향 |

**상태는 위치만이 아니라 위치와 방향의 쌍** $(\mathbf{x}, \mathbf{n}) \in \Omega \times S^1$ 이다.
이것이 뒤의 모든 정의를 지배한다.

### 정의 3.1 (피복선 $\Gamma_{\text{cover}}$)

각 벽 $w$ 를 $\mathbf{n}_w$ 방향으로 $c_w + \phi/2$ 만큼 평행이동한 뒤, 이웃한 이동선끼리의 직선
교점으로 양 끝을 다시 잡은 선분들의 집합을 $\Gamma_{\text{cover}}(\phi)$ 라 한다. 각 조각은
**원본 벽의 법선 $\mathbf{n}_w$ 를 그대로 물려받는다**.
(`buildCoverWalls:128` → `trimShiftedLoop:75`. 코너를 교점으로 다시 잡는 이 처리가 2.3절의
offset self-intersection 을 대신한다.)

### 정의 3.2 (허용 경계 $A(\mathbf{n})$)

$$A(\mathbf{n}) = \{\, \gamma \in \Gamma_{\text{cover}} \;:\; \mathbf{n}_\gamma \cdot \mathbf{n} \le \alpha_{\text{th}} \,\},
\qquad \alpha_{\text{th}} = -0.6$$

**$A$ 는 $\mathbf{x}$ 에 의존하지 않고 $\mathbf{n}$ 에만 의존한다**(`physics.js:165`).
세그먼트 방향이 이완 중 고정이면 $A$ 는 상수집합이다.

### 정의 3.3 (광선거리 $\tau$ 와 진행방향 $\mathbf{d}$)

$$\tau^{+}(\mathbf{x},\mathbf{n}) = \inf\{\, t>0 : \mathbf{x} + t\,\mathbf{n} \in \textstyle\bigcup A(\mathbf{n}) \,\}$$

$\tau^{+}$ 가 유한하면 $\mathbf{d} = \mathbf{n}$, 아니면 $\mathbf{d} = -\mathbf{n}$ 으로 두고 같은 식을
후방에 적용한다(`physics.js:204` 의 후방 폴백). 이때의 값을 $\tau(\mathbf{x},\mathbf{n})$,
광선이 처음 만나는 조각을 $\gamma^{*}(\mathbf{x},\mathbf{n})$ 라 한다.

$$\Gamma_{\text{eff}}(\mathbf{x},\mathbf{n}) := \gamma^{*}(\mathbf{x},\mathbf{n}) \in A(\mathbf{n})$$

### 정의 3.4 (목표점 $T$ 와 인력 포텐셜)

교점 $\mathbf{p} = \mathbf{x} + \tau\,\mathbf{d}$ 에서의 적층 두께를 $s = \text{stackAt}(\gamma^{*},\mathbf{p})$,
$\cos = \mathbf{d}\cdot\mathbf{n}_{\gamma^{*}}$ 라 할 때

$$T(\mathbf{x},\mathbf{n}) = \mathbf{x} + \Big(\tau - \frac{s}{\cos}\Big)\mathbf{d}
\qquad (|\cos| \le 0.2 \text{ 이면 } T = \mathbf{p} + s\,\mathbf{n}_{\gamma^{*}})$$

$$U_{\text{attr}}(\mathbf{x},\mathbf{n}) = \tfrac{1}{2} k \lVert \mathbf{x} - T \rVert^{2}
 = \tfrac{1}{2} k \Big(\tau - \frac{s}{\cos}\Big)^{2}$$

### 주의 — 최근접거리가 아니다

$U_{\text{attr}}$ 를 $\tfrac12 k\, d(\mathbf{x},\Gamma_{\text{eff}})^2$ 로 적으면 $d$ 가 최근접거리
(수선의 발)로 읽힌다. 그러나 위 정의의 $d$ 는 **$\mathbf{n}$ 방향 광선거리**이며 둘은 다른 함수다.
최근접 투영은 medial axis 에서만 불연속이지만, 광선 투사는 거기에 더해

1. $A(\mathbf{n})$ 이 바뀌는 방향 임계,
2. 광선이 조각의 끝점을 스치는 위치,
3. 전방↔후방 폴백이 전환되는 면

에서도 불연속이다. 4.3의 채터링은 이 불연속의 발현으로 본다.
본 논문은 **구현을 따라 광선 투사로 정식화**하며, 최근접 투영판은 3.3절의 퇴화 사례로만 다룬다.

## 3.2 H1 — well-definedness (방향정합성 조건)

**H1.** 정의 3.1–3.4 의 $\Gamma_{\text{eff}}(\mathbf{x},\mathbf{n})$ 이 잘 정의된다. 즉 아래 세 조건이
성립하는 영역에서 $\gamma^{*}$ 와 $T$ 가 존재하고 유일하다.

| 조건 | 내용 | 실패하면 |
|---|---|---|
| (W1) 비공집합 | $A(\mathbf{n}) \ne \emptyset$ | 유인할 경계가 없음 |
| (W2) 도달 | $\tau^{+}$ 또는 후방 $\tau^{-}$ 가 유한 | 4.2의 도달가능성 실패 |
| (W3) 유일 | 최근접 교점이 하나 | 동률에서 target 이 진동(4.3) |

**$\alpha_{\text{th}}$ 의 역할.** 임계를 낮추면(더 엄격하면) (W1)이 깨지기 쉽고, 높이면(느슨하면)
비스듬한 벽까지 후보에 들어와 (W3)의 동률과 오귀속이 늘어난다. 현재 구현값
$\alpha_{\text{th}} = -0.6$ 은 $\theta \ge \arccos(-0.6) \approx 126.87^\circ$,
즉 정반대에서 $\pm 53.13^\circ$ 이내를 허용한다.

**검증 절차.** $\theta$ 를 $0^\circ$–$90^\circ$ 로 스윕하며 세 사례연구에서 측정한다.

| 지표 | 정의 | 대응 조건 |
|---|---|---|
| $f_1(\alpha)$ | 수렴 실패율 | (W1), (W2) |
| $f_2(\alpha)$ | 오귀속률 | (W3) |

비볼록 단면(I빔)과 곡선 경계(중공교각)에서 민감도가 가장 클 것으로 예상한다.

> 다음 작업: $\alpha$ 스윕 실증 검증.

## 3.3 H3 — 기존 APF는 CAF의 특수 사례

**H3.** $A(\mathbf{n})$ 이 방향과 무관한 한 점 $\mathbf{x}_0$ 로 퇴화하면 CAF 의 인력항은 고전 APF 의
인력항으로 환원된다. 이때 $\tau\,\mathbf{d} = \mathbf{x}_0 - \mathbf{x}$, $s=0$ 이므로

$$U_{\text{attr}} = \tfrac12 k \lVert \mathbf{x} - \mathbf{x}_0 \rVert^{2}$$

가 되어 목표가 상수점인 표준형과 같아진다. **광선거리로 정식화해도 이 환원은 그대로
성립한다** — 목표가 0차원이면 광선거리와 최근접거리가 일치하기 때문이며, 이것이 3.1절 주의에서
"최근접 투영판은 퇴화 사례"라고 한 이유다.

**함정.** "점은 길이 0 인 곡선"이라는 정의상 자명함에 그치면 기여가 되지 않는다. 이 일반화가
**실제로 여는 새로운 문제 클래스**를 정리로 명시해야 한다. 광선 정식화에서 그 목록은 분명하다.

1. 목표가 1차원이므로 **어느 조각에 붙을지**를 정해야 한다 → 방향정합성(3.2)과 다중경계 할당(5.1).
2. 목표가 상태의존이므로 $\partial T/\partial \mathbf{x} \ne 0$ 이다 → 4.1의 동결 가정과 그 오차.
3. 목표 선택이 불연속일 수 있다 → 4.3의 채터링. 상수점 APF 에는 이 현상 자체가 없다.

즉 H3 는 "APF 를 포함한다"가 아니라 **"APF 에는 존재하지 않던 세 문제가 여기서 비로소 생긴다"**
는 진술로 세운다.
