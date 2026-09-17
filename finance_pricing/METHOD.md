# Mathematical specification — version 0.1

## Contract and model

The contract pays (w1 S1(T) + w2 S2(T) - K)+ at maturity T. Prices and K are
expressed in the same monetary unit. The implementation assumes a risk-neutral,
constant-parameter Black–Scholes model without dividends, nonnegative basket
weights summing to one, positive initial spots/strike/maturity, and correlation
rho in [0,1]. Volatilities are nonnegative. Inputs are exact rational values.
The two standard normal variables Z1,Z2 are independent:

S1(T) = S1 exp((r - sigma1²/2)T + sigma1 sqrt(T) Z1)
S2(T) = S2 exp((r - sigma2²/2)T + sigma2 sqrt(T)(rho Z1 + sqrt(1-rho²) Z2)).

The price is exp(-rT) times the expected payoff. Model specification is part of
the certificate. Negative correlations, dividends, early exercise, barriers,
path dependence, transaction costs and live calibration are not implemented.

## Conditional dimension reduction

Fix Z1=z. Set

A = w1 S1 exp((r-sigma1²/2)T + sigma1 sqrt(T) z),
B = w2 S2 exp((r-sigma2²/2)T + sigma2 sqrt(T) rho z),
b = sigma2 sqrt(T) sqrt(1-rho²), H=K-A.

For H>0 and b>0,

C(z) = exp(-rT) [B exp(b²/2) Phi(d1) - H Phi(d2)],
d2 = log(B/H)/b, d1=d2+b.

For H<=0 the bracket equals B exp(b²/2)-H. Deterministic cases b=0 or w2=0
are handled separately. C(z) is the conditional discounted expectation, and
V = integral C(z) phi(z) dz over the real line.

Because weights, volatilities and rho are nonnegative, the payoff for each
fixed Z2 is nondecreasing in z. Hence C(z) is nondecreasing. On [a,b], its
integral against normal density lies between C(a)[Phi(b)-Phi(a)] and
C(b)[Phi(b)-Phi(a)]. Rigorous endpoint balls and positivity give the implemented
lower/upper bounds. This monotonicity is why the current implementation rejects
negative correlations; rejecting them is a scope restriction, not a claim that
negative correlations are unpriceable.

## Infinite-tail bound

The payoff is nonnegative and is bounded above by w1 S1(T)+w2 S2(T).
Exponential tilting of the remaining standard normal variable gives

0 <= E[discounted payoff * 1{|Z1|>L}]
  <= sum_i wi Si [Phi(-L-mi) + Phi(mi-L)],

where m1=sigma1 sqrt(T), m2=sigma2 sqrt(T) rho. This formula accounts for both
tails and for the unbounded lognormal asset values. Multiplying a maximum payoff
by a Gaussian tail probability would not be valid: the payoff is unbounded.

The interior lower bound remains a full-price lower bound; the tail upper bound
is added to the interior upper bound. The midpoint is within the claimed absolute
tolerance only when half the total interval width is no larger than that tolerance.

## Numerical guarantees and trust boundary

FLINT/Arb evaluates exp, log, sqrt and Phi via erfc at 128-bit precision. Ball
endpoints are converted exactly to rationals using their binary mantissa/exponent.
Block contributions are rounded outwards to the dyadic grid 2^-64 by integer
arithmetic. Summation of these rational bounds is exact. Decimal summary fields
are displays only; the rational certificate is authoritative.

The verifier checks a complete nonoverlapping binary partition of [-L,L],
recomputes each block and both tails, and compares the claimed bounds and status.
It shares the pricing formulas and FLINT dependency with the generator; this is
reproducible replay, not an independently implemented proof assistant. No claim is
made about robustness against arbitrary malicious resource-exhaustion payloads.

The calculation assumes the stated stochastic model and input parameters. It
bounds numerical error, not model misspecification, calibration uncertainty,
market liquidity or future realized profit/loss. A quote outside the interval is
inconsistent with this fixed model calculation; it is not evidence of an arbitrage
or a recommendation to trade. A quote inside is compatible, not proven fair.

## Prior work and research positioning

Conditional smoothing for basket pricing is established, including Bayer,
Siebenmorgen and Tempone, *Smoothing the payoff for efficient computation of
Basket option prices*, 2016/2017: https://arxiv.org/abs/1607.05572

Adaptive integration for basket options is also established: De Luigi, Lelong
and Maire, 2012: https://arxiv.org/abs/1210.7783

QMCPy's 2026 demonstrations include option pricing with accuracy targets:
https://qmcsoftware.github.io/QMCSoftware/demos/talk_paper_demos/JOSS2026/joss2026/

Arb/FLINT supplies the rigorous arithmetic, rather than being a claimed invention
of this project: https://flintlib.org/doc/arb.html

The present prototype assembles a bounded financial use case, explicit tail
accounting, success/failure status and replayable output. It does not establish
scientific novelty or superiority over existing numerical libraries. Its purpose
is to make a candidate valuation-control tool concrete and measurable.
