"""Sample curriculum: algorithmic trading foundations.

Every lesson body carries `content_status = "sample"`: clearly-labeled example
material written for this app, not syllabus or vendor content. Nothing here
claims a strategy is profitable or that code compiles in a live venue.
"""

COURSE = {
    "title": "Algorithmic Trading Foundations",
    "slug": "algo-trading-foundations",
    "description": (
        "A structured path from market mechanics to a tested, journal-tracked "
        "research process. Education and research only: this platform never "
        "places orders and holds no credentials."
    ),
}

# Each lesson: slug, title, summary, difficulty, minutes, topics, body.
# Bodies use markdown the frontend renders. Callouts start with "> " lines.

MODULES = [
    {
        "number": 0,
        "slug": "orientation",
        "title": "Orientation",
        "summary": "What this platform is, how to study with it, and the journal habit.",
        "lessons": [
            {
                "slug": "what-this-platform-is",
                "title": "What this platform is (and is not)",
                "summary": "Scope, boundaries, and the education-and-research-only contract.",
                "difficulty": "beginner",
                "minutes": 6,
                "topics": ["scope", "safety"],
                "body": """## What you are using

This is a **study platform**. It gives you lessons, notes, flashcards, quizzes,
coding labs, and a project workspace so you can learn algorithmic trading as a
research discipline.

## What it deliberately does not do

- It does **not** connect to a broker.
- It does **not** hold API keys, tokens, or account credentials.
- It does **not** place, route, or simulate-live orders.
- It does **not** promise returns, and it will not tell you a strategy is profitable.

> **Sample content notice.** Every lesson in this course is labeled `sample`.
> It was written for this app as example teaching material. Treat it as a
> starting point to verify, not as authority.

## The mental model to adopt

Treat trading research the way a lab treats an experiment: write the hypothesis
*before* you look at the result, define what would prove you wrong, and record
what actually happened. Most retail losses in quant trading come from
undisciplined evaluation, not from a lack of indicators.

## Suggested pace

Roughly one lesson a day. Use the flashcards the same day you read, and take a
quiz before moving on. The spaced-repetition queue is designed to resurface
exactly what you got wrong.
""",
            },
            {
                "slug": "how-to-study-with-this-app",
                "title": "How to study with this app",
                "summary": "Lesson flow, notes, flashcards, quizzes, and the review queue.",
                "difficulty": "beginner",
                "minutes": 5,
                "topics": ["workflow"],
                "body": """## The loop

1. **Read** a lesson and mark it complete when you can summarize it aloud.
2. **Note** anything you want to keep in your own words.
3. **Quiz** on the lesson — the questions are drawn from its topics.
4. **Review** the spaced-repetition queue daily; it is fed by what you miss.

## Notes

Notes are yours. Each note has a `kind` so you can separate research from
mistakes. The **mistake** kind is the most valuable one you will keep: write
down what you believed, what was actually true, and how you would have caught
the difference earlier.

## Flashcards

Cards are created two ways: by you, and automatically when you miss a quiz
question. Missed-question cards land in a deck called **From missed
questions** and are due the next day.

## The review queue

Scheduling is SM-2 style. When you grade a card:

- **again** — you forgot; it returns in about 15 minutes and eases down.
- **difficult** — remembered with effort; a short interval.
- **good** — normal recall; interval grows by the card's ease factor.
- **easy** — instant recall; the interval jumps and ease rises.

Grading honestly matters more than grading generously. An "easy" you did not
actually find easy trains the scheduler to hide the card from you.
""",
            },
            {
                "slug": "the-journal-habit",
                "title": "The trader's journal habit",
                "summary": "Why the record is the product, and what to write in it.",
                "difficulty": "beginner",
                "minutes": 6,
                "topics": ["journaling", "process"],
                "body": """## The record is the product

A strategy is not the product of research. The **record** is: the hypothesis,
the parameters, the test window, the costs you assumed, and the result. Without
the record you cannot distinguish a good process with a bad outcome from a bad
process with a lucky outcome.

## What every entry needs

- **Date and intent.** What you were about to test or observe.
- **Hypothesis.** One sentence, falsifiable.
- **Preconditions.** Data range, universe, timeframe, cost assumptions.
- **Result.** What happened, including the unflattering parts.
- **Verdict.** Keep, change, or discard — and *why*.

## Why verdicts matter

Over months, your journal becomes a dataset about **you**: which hypotheses
tended to be right, which market regimes you read poorly, which rules you keep
ignoring. That is more useful than any single backtest.

> This platform stores your journal notes privately and exports them. Nothing
> you write is shared, scored, or used to make a claim about performance.
""",
            },
        ],
    },
    {
        "number": 1,
        "slug": "market-microstructure",
        "title": "Market microstructure",
        "summary": "What happens when an order meets a book, and what it costs you.",
        "lessons": [
            {
                "slug": "orders-and-the-book",
                "title": "Orders and the book",
                "summary": "The limit order book, matching, and why queues matter.",
                "difficulty": "beginner",
                "minutes": 9,
                "topics": ["microstructure", "order-book", "liquidity"],
                "body": """## Two kinds of intent

A **market order** says "fill me now, at whatever is available." A **limit
order** says "fill me only at my price or better." Market orders take
liquidity; limit orders provide it. That distinction drives exchange fees and
is the closest thing to a physical law in trading.

## The book

The **order book** is the set of resting limit orders. The best bid is the
highest buy; the best ask is the lowest sell. The difference is the **spread**.

```
ASK  102.40 x 500   <- sellers willing to wait
ASK  102.30 x 200
---- 102.25 / 102.28  <- spread: 0.03
BID  102.25 x 300
BID  102.20 x 800   <- buyers willing to wait
```

When your market buy arrives, it consumes the ask levels top-down. If you want
more size than the top level offers, you walk into deeper levels and your
average price worsens. That movement caused purely by your own order is
**market impact**.

## Why queues matter

If you place a limit buy at 102.25, your place in the queue is order-dependent.
Orders ahead of you fill first. A limit order that was never filled is not a
"saved" trade — it is often a trade that would have lost, and your strategy's
real results depend on those unfilled orders too.

> **Sample content.** Illustrative book only. Real books are fragmented across
> venues and change in microseconds.
""",
            },
            {
                "slug": "spread-liquidity-and-impact",
                "title": "Spread, liquidity, and impact",
                "summary": "Measuring the cost of entering and exiting.",
                "difficulty": "beginner",
                "minutes": 8,
                "topics": ["spread", "liquidity", "impact", "costs"],
                "body": """## The spread is a toll

To buy at the ask and sell at the bid is to pay the spread once. If a signal
earns 0.4% per trade and the spread is 0.3%, your edge is nearly gone before
any fee.

## Depth is not free depth

Published depth sums all resting orders. It overstates what you can actually
take: much of it cancels the moment price starts moving. A better question than
"How much depth is there?" is "How much depth survives a 0.1% move?"

## Estimating your own cost

A practical per-trade cost model:

```
cost ≈ half_spread + fees + impact(size, adv) + slippage
```

Where `adv` is average daily volume. A common crude impact estimate is
proportional to `size / sqrt(adv)` — doubling your size does not double the
cost, but it does more than linearly worsen it once you matter to the book.

## The uncomfortable consequence

Short-horizon strategies have the least room for cost. A signal that fires
dozens of times a day must clear the spread every time. This is why cost
modeling is not a finishing touch — it frequently decides whether an idea
survives at all.

> **Sample content.** The `1/sqrt(adv)` form is an order-of-magnitude teaching
> approximation, not a calibrated model for any venue.
""",
            },
            {
                "slug": "order-types-and-their-failure-modes",
                "title": "Order types and their failure modes",
                "summary": "Market, limit, stop, stop-limit, and post-only — and how each betrays you.",
                "difficulty": "intermediate",
                "minutes": 10,
                "topics": ["order-types", "execution", "risk"],
                "body": """## Market

Guarantees urgency, not price. In a fast market the print you saw is not the
price you get.

## Limit

Guarantees price, not execution. The failure mode is **adverse selection**: you
tend to get filled when the market is moving against you, because that is when
someone is happy to take the other side.

## Stop

A stop becomes a market order once triggered. In a gap it triggers far from
where you expected — the classic "stop at 100 filled at 92" story. Stops
protect against ordinary drift, not against discontinuity.

## Stop-limit

Adds a limit after the stop. This caps the price but can leave you **completely
unhedged** if the limit is never reached. It converts a certain bad fill into a
possible much worse position.

## Post-only

Guarantees your order is posted rather than taking liquidity, so you pay the
maker side. It is the standard choice for patient entries — at the cost of
uncertain fills.

## The rule worth keeping

> Every order type trades one of {price certainty, execution certainty,
> urgency} for another. Name the trade you are making *before* you place it.

## Design implication for your bot

Your strategy must specify, for every order it sends, which failure mode it is
accepting. A backtest that assumes "we exit at the close" is silently assuming
infinite liquidity at a price that will not exist.
""",
            },
            {
                "slug": "slippage-fees-and-the-cost-of-getting-in",
                "title": "Slippage, fees, and the cost of getting in",
                "summary": "Building a realistic cost model before you trust any backtest.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["slippage", "fees", "costs", "backtesting"],
                "body": """## Slippage has three sources

1. **Spread** — you crossed it.
2. **Impact** — your size moved the book.
3. **Timing** — the price moved between your signal and your fill.

Backtests usually model only #1, if that. #3 is the one that quietly inflates
results, because the signal you computed at the close is rarely the price you
can transact at the close.

## Fees are not optional

Per-side fees compound with turnover. A strategy trading 20 times a week pays
roughly 1,000 fee events a year. A fee model that is off by a tenth of a basis
point can turn a profitable hypothesis into a losing one.

## A minimal honest model

```python
def net_return(gross, fill_price, exit_price, side, fee_bps, slip_bps):
    slip = fill_price * (slip_bps / 10_000) * side
    fill = fill_price + slip
    fees = (fill + exit_price) * (fee_bps / 10_000)
    return (exit_price - fill) * side - fees
```

## Sensitivity beats precision

You do not know your exact cost. So do not pick one number — sweep it. Run the
same backtest at 1x, 2x, and 3x your estimated cost. If the idea dies at 2x, it
is a fragile idea and you should know that now.

> **Sample content.** The function above is illustrative and ignores rounding,
> partial fills, and venue specifics.
""",
            },
        ],
    },
    {
        "number": 2,
        "slug": "data",
        "title": "Data",
        "summary": "Candles, timeframes, adjustments, and the biases hidden in your dataset.",
        "lessons": [
            {
                "slug": "ohlcv-and-what-candles-hide",
                "title": "OHLCV candles and what they hide",
                "summary": "What four prices and a volume number cannot tell you.",
                "difficulty": "beginner",
                "minutes": 8,
                "topics": ["data", "ohlcv", "candles"],
                "body": """## The compression

A candle reduces an interval to five numbers: open, high, low, close, volume.
That is an enormous loss. Within the bar, price may have trended, whipsawed,
or simply sat — and the bar looks identical.

## The high is a path-free abstraction

A bar's high tells you price reached a level. It does not tell you **when**, or
whether the open was before or after. This matters for indicators built on
bar-to-bar comparisons: two datasets with identical OHLCV can require
completely different orders to produce.

> This is the root of a whole family of strategy bugs: an indicator that "looked
> great" on close-to-close data can be impossible to trade, because the fills it
> assumes were never reachable in the sequence price actually moved.

## Volume is not one thing

Total volume does not distinguish aggressive buys from aggressive sells, nor
repeat quotes from real trades. It is a coarse activity meter, not direction.

## What to demand from a data vendor

- Intraday data if your horizon is intraday — daily bars cannot validate an
  intraday idea.
- Explicit timestamps and timezone.
- A stated aggregation rule (how the bar was built).
- Trade flags or aggressor side if you intend to model microstructure.

> **Sample content.** Written as general education; no vendor is endorsed.
""",
            },
            {
                "slug": "timeframes-and-resampling-traps",
                "title": "Timeframes and resampling traps",
                "summary": "Why testing on many timeframes manufactures false confidence.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["timeframes", "resampling", "overfitting", "data"],
                "body": """## Aggregation is lossy in one direction

Resampling 1-minute bars into 5-minute bars is well defined. Going the other
way is not: you cannot recover the path inside a 5-minute bar. Strategies that
require intrabar sequence must be built on intrabar data.

## The many-timeframe trap

If you test one idea on 1m, 5m, 15m, 1h, and 1d, and report the best, you have
run five experiments and shown one. The others are still evidence — and they
usually disagree. Disagreement across timeframes is a signal about the idea's
fragility, not a nuisance to filter away.

## Alignment between signal and execution

A common error: compute the signal on the daily close, then assume you can
trade at that close. If the signal is only known after the close, the earliest
honest fill is the next bar's open. That single change frequently removes the
entire edge.

## Calendar effects are data artifacts

Day-of-week and time-of-day effects often reflect **when institutions
transact**, which changes with venue rules and holidays. Any calendar-based
pattern should be re-derived from your own data each year rather than assumed.

## Checklist before trusting a timeframe result

- Was the signal available *before* the bar you traded?
- Did you resample in a way that preserves your signal's logic?
- Does the result survive on an adjacent timeframe?

> **Sample content.** General education only.
""",
            },
            {
                "slug": "corporate-actions-and-adjusted-data",
                "title": "Corporate actions, splits, and adjusted data",
                "summary": "Why unadjusted data breaks indicators and adjusted data breaks prices.",
                "difficulty": "intermediate",
                "minutes": 8,
                "topics": ["data", "splits", "corporate-actions"],
                "body": """## Splits change the tape, not the value

A 2-for-1 split halves every historical price and doubles the share count.
Economically nothing changed — but an unadjusted price series will show a
50% "crash" that never happened, and any price-threshold rule will fire
spuriously.

## The adjustment dilemma

Vendors typically offer:

- **Back-adjusted** prices: historical prices scaled so returns are continuous,
  but the *stated* prices no longer match what traded at the time.
- **Forward-adjusted**: current prices are real, history is scaled the other way.
- **Unadjusted**: historically accurate, discontinuous at each event.

There is no free choice. Back-adjusted data is right for return math and wrong
for anything comparing to a historical price level (a 52-week high, a round
number, a stop level).

## Dividends are not splits

A dividend genuinely removes cash from the company, so total-return series and
price-return series diverge over time. Whether you should include dividends
depends on whether your strategy could actually have received them.

## Practical rule

> Store the adjustment factor alongside the series and be explicit in your
> report about which convention you used. "We used back-adjusted closes" is a
> sentence a reviewer must be able to read.

> **Sample content.** General education; corporate-action handling varies by
> vendor and asset class.
""",
            },
            {
                "slug": "survivorship-bias",
                "title": "Survivorship bias in symbol lists",
                "summary": "Why today's index members rewrite history in your favor.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["survivorship", "bias", "data", "backtesting"],
                "body": """## The error

You backtest "the S&P 500" using the *current* 500 members. But the index in
2005 contained companies that later went bankrupt, were acquired, or were
removed. Those names are missing from your dataset, and they are precisely the
names that performed worst.

The measured return is therefore biased **upward**, often substantially, and
the bias grows with the length of your test.

## It hides in more places than indices

- "All US-listed stocks today" excludes delisted names.
- "Cryptos that exist now" excludes the many that went to zero.
- Sector screens inherit the current sector classification of survivors.

## Fixes, in order of quality

1. **Point-in-time data.** Membership as it was on each date. Best, and often
   paid.
2. **Include delisted symbols.** Any survivor-free universe beats a survivor one.
3. **Bias estimate.** Run on survivors, then run again on a sample of removed
   names and report the difference.

## A cheap self-audit

If your strategy selects the top decile of a universe, ask: how many symbols in
that universe were later delisted? If the answer is zero, your universe is
almost certainly survivor-filtered.

> **Sample content.** General education; specific data products are not
> endorsed here.
""",
            },
        ],
    },
    {
        "number": 3,
        "slug": "signals",
        "title": "Indicators and signal design",
        "summary": "What indicators actually compute, and how to write a falsifiable hypothesis.",
        "lessons": [
            {
                "slug": "moving-averages-what-they-smooth-away",
                "title": "Moving averages: what they smooth away",
                "summary": "SMA vs EMA, lag, and why crossovers are a lagging story.",
                "difficulty": "beginner",
                "minutes": 8,
                "topics": ["indicators", "moving-average", "signal"],
                "body": """## The computation

An **SMA** over `n` bars is the mean of the last `n` closes. An **EMA** weights
recent bars more, so it responds faster and is noisier. Both are low-pass
filters: they remove high-frequency movement and leave the trend.

## Lag is structural

A moving average cannot lead. Its lag is roughly `(n+1)/2` bars for an SMA. A
20-bar SMA is therefore about 10 bars behind the price action it describes. You
are not detecting a turn; you are detecting that the average of the past has
finally shifted.

## The crossover story

A golden cross (short MA above long MA) means: recent prices have risen enough
to pull the short average above the long one. That is a *lagged summary*, not
information about the future. It is profitable in persistent trends and
expensive in chop.

## What to measure before you believe one

- How many whipsaws per unit time at your chosen lengths?
- Does the result survive a modest change in `n` (say ±20%)?
- What fraction of the profit comes from one or two trades?

> **Sample content.** General education. Moving averages are widely studied;
> treat any specific parameter choice as a hypothesis, not a finding.
""",
            },
            {
                "slug": "momentum-and-mean-reversion",
                "title": "Momentum, RSI, and mean reversion",
                "summary": "Oscillators, what they measure, and the regimes they need.",
                "difficulty": "intermediate",
                "minutes": 10,
                "topics": ["momentum", "rsi", "mean-reversion", "indicators"],
                "body": """## Two opposed worldviews

**Momentum** assumes a move continues: buy strength, sell weakness.
**Mean reversion** assumes an excursion is excessive: buy weakness, sell
strength. They are not both right at the same horizon — which is why an
oscillator that works on 5-minute bars can fail on daily ones.

## What RSI actually is

RSI compares average gains to average losses over `n` bars and rescales to
0–100:

```
RSI = 100 - 100 / (1 + RS),  RS = avg_gain / avg_loss
```

It measures the **balance of recent movement**, not overbought/oversold truth.
An RSI of 70 in a strong trend is not a sell signal; it is a description of a
strong trend.

## Regime dependence

Mean reversion needs a range. Trend following needs, unsurprisingly, a trend.
The hard research question is not "what is the best indicator" but "what
measurable condition separates the two regimes, and is that condition knowable
in time to act?"

## A falsifiable formulation

> "When the 20-bar ATR is below its 100-bar median **and** price is inside its
> 20-bar range, a RSI(14) cross below 30 followed by a close back above 30
> precedes a 3-bar gain net of costs at least 55% of the time."

That statement can be checked and refuted. "RSI works in ranges" cannot.

> **Sample content.** General education only; thresholds are illustrative.
""",
            },
            {
                "slug": "volatility-atr-and-regime",
                "title": "Volatility: ATR, bands, and regime",
                "summary": "Measuring volatility and why it is more predictable than direction.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["volatility", "atr", "regime", "risk"],
                "body": """## Direction is hard; volatility is easier

Volatility clusters: high-volatility periods tend to follow high-volatility
periods. This is one of the most robust empirical facts in finance, and it is
why position sizing based on volatility is more defensible than sizing based on
a directional forecast.

## True range

Average True Range widens the bar definition to include gaps:

```
TR = max(high - low, |high - prev_close|, |low - prev_close|)
ATR = smoothed mean of TR
```

Without the gap terms, an overnight jump would be recorded as a quiet bar.

## ATR as a unit of risk

Expressing stops and targets in ATR multiples makes rules portable across
symbols and regimes. A 2-ATR stop means "exit when the market moves two
typical bars against me," which adapts automatically when conditions change.

## Bands

Bollinger-style bands are a mean plus a volatility multiple. A price touching
the upper band says the move is large *relative to recent volatility* — it says
nothing about whether it will continue. Bands define a question, not an answer.

## Regime flags worth tracking

- ATR percentile over a long window (calm vs stressed).
- Short-horizon volatility relative to long (rising vs falling).
- Correlation between assets (diversified vs correlated).

> **Sample content.** General education; no calibration is implied.
""",
            },
            {
                "slug": "writing-a-falsifiable-hypothesis",
                "title": "Writing a falsifiable hypothesis",
                "summary": "The single skill that separates research from chart reading.",
                "difficulty": "beginner",
                "minutes": 7,
                "topics": ["hypothesis", "process", "research"],
                "body": """## Why this comes before any code

If you cannot state what would prove your idea wrong, you cannot design a test.
You will instead find a test that agrees with you — which is exactly what most
failed research does.

## The template

> **When** [measurable market condition], **then** [specific action] **because**
> [mechanism], **and this fails if** [observable outcome].

Example:

> When the 5-day realized volatility is in its lowest quartile over the last
> year, then go long at the close and exit after 5 sessions, because compressed
> volatility precedes directional moves in this instrument. This fails if the
> net-of-cost hit rate is below 52% or if the result depends on any single year.

## The three failure modes it prevents

1. **Post-hoc fitting** — you must commit before seeing the answer.
2. **Vagueness** — "works in ranging markets" cannot be tested.
3. **Unfalsifiable rescue** — "it just needs the right regime" is disallowed
   because you pre-declared the regime.

## Score yourself

Before running anything, write:

- The metric you will judge it by.
- The minimum value that counts as success.
- The one result that would make you discard it.

If you cannot fill those three in, the idea is not ready to be tested.

> **Sample content.** A process habit, not financial advice.
""",
            },
        ],
    },
    {
        "number": 4,
        "slug": "backtesting",
        "title": "Backtesting without fooling yourself",
        "summary": "Bias, validation, costs, and honest reporting.",
        "lessons": [
            {
                "slug": "why-most-backtests-lie",
                "title": "Why most backtests lie",
                "summary": "The catalog of ways a test flatters an idea.",
                "difficulty": "beginner",
                "minutes": 10,
                "topics": ["backtesting", "bias"],
                "body": """## They lie by construction

A backtest is a simulation with assumptions. Each assumption is a place the
result can be flattered without anyone meaning to.

## The standard culprits

- **Lookahead bias** — using information that was not yet known.
- **Survivorship bias** — testing only on names that endured.
- **Selection bias** — trying many ideas and reporting the winner.
- **Transaction-cost omission** — assuming free, infinite fills.
- **Data snooping** — the dataset has been mined by many people before you.
- **Parameter tuning** — optimizing until the curve is beautiful.

## The sneakiest one: subtle lookahead

It is rarely `shift(-1)`. More often it is:

- Computing a "daily" feature from the whole day, then trading that day's close.
- Using a company's fundamentals filed *after* the period they describe.
- Normalizing with a mean that includes future bars.

Each of these inflates results and none looks wrong at a glance.

## The meta-lesson

> The question is not "is this backtest good?" It is "what would have had to be
> true for this backtest to be good *by accident*?" Then check those things.

## A discipline that helps

Have someone else — or a future you — try to break the result. Publish the
assumptions next to the number. An unexplained return figure is not evidence.

> **Sample content.** General education about evaluation, not about any
> particular instrument.
""",
            },
            {
                "slug": "train-validate-test",
                "title": "Train, validate, test — and walk-forward",
                "summary": "Splitting data so your result means something out of sample.",
                "difficulty": "intermediate",
                "minutes": 10,
                "topics": ["validation", "walk-forward", "overfitting"],
                "body": """## The three sets

- **Train** — you fit parameters here.
- **Validate** — you choose between candidate designs here.
- **Test** — you look exactly once, at the very end.

Touching the test set more than once turns it into a validation set, and your
"out of sample" result stops being out of sample.

## Why a single split is weak for time series

Markets change. A split at one arbitrary date may put a crisis entirely in
train or entirely in test. **Walk-forward** evaluation rolls the window:

```
train [====] validate []
train   [====] validate []
train     [====] validate []
```

You refit on each training window and score on the immediately following
window, then concatenate the out-of-sample results. The final equity curve is
made only of periods the model had not seen.

## Purging and embargo

If your features look back `k` bars and your labels look forward `m` bars,
adjacent train and test rows leak into each other. Purge overlapping rows and
add an embargo gap of at least `m` bars.

## What to report

Number of folds, window lengths, the leakage controls you applied, and the
distribution of fold results — not just the mean. A strategy that earns 40% in
one fold and loses in all others is not a strategy.

> **Sample content.** General methodology education.
""",
            },
            {
                "slug": "overfitting-and-degrees-of-freedom",
                "title": "Overfitting and degrees of freedom",
                "summary": "Counting the choices you made, and paying for each one.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["overfitting", "statistics", "validation"],
                "body": """## Every choice is a degree of freedom

Each parameter you tune, each filter you add, each regime you exclude is one
opportunity for the data to cooperate by accident. Twenty tuned parameters on
ten years of daily data is a system with more freedom than data.

## The uncomfortable math

A useful heuristic: the rarer the event your strategy trades, the more data you
need to say anything. If a signal fires 12 times in a decade, ten wins out of
twelve is not evidence — it is a coin flip you would not blink at.

## Ways it manifests

- Equity curves that are suspiciously smooth.
- Great results that collapse on a one-bar change in timing.
- Rules with no economic story ("only on Tuesdays after down weeks").
- Performance concentrated in one instrument or one year.

## Defenses that actually work

1. **Fewer parameters.** Prefer rules with a mechanism over rules with a fit.
2. **Nested validation** if you must tune heavily.
3. **Penalize complexity** — compare models at equal complexity before adding.
4. **Pre-registration.** Write the hypothesis and metric first; the app's
   journal exists for exactly this.

## The test that catches you

Re-run with parameters perturbed ±20%. If performance collapses, you fitted
noise. Robust ideas have broad plateaus, not sharp peaks.

> **Sample content.** General statistics education applied to research
> discipline.
""",
            },
            {
                "slug": "reporting-a-backtest-honestly",
                "title": "Reporting a backtest honestly",
                "summary": "The numbers to publish and the ones that are usually missing.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["reporting", "backtesting", "metrics"],
                "body": """## Return is the least informative number

A high return tells you almost nothing without exposure and risk. Two strategies
up 40% — one at 5% volatility, one at 40% — are not comparable.

## The minimum report

- **CAGR** and **volatility**, so the two can be compared.
- **Sharpe** (or Sortino), with the risk-free assumption stated.
- **Maximum drawdown** and its **duration**.
- **Turnover**, because costs scale with it.
- **Trade count** and **hit rate** together — either alone is misleading.
- **Exposure**: how much of the time were you in the market?

## The disclosures that build trust

- The cost model, including spread and slippage assumptions.
- The universe and how delisted names were handled.
- The exact out-of-sample protocol.
- The number of ideas tried before this one was reported.

## The sentence that separates reports

> A report that says "we tested 40 hypotheses and this is the best" is more
> credible than one that says "we tested one hypothesis and it worked."

Reporting your failures is not weakness; it is the evidence that your selection
process is real.

> **Sample content.** General education; no performance figures are presented
> here or anywhere in this app.
""",
            },
        ],
    },
    {
        "number": 5,
        "slug": "risk",
        "title": "Risk management",
        "summary": "Sizing, correlation, drawdown, and the arithmetic of ruin.",
        "lessons": [
            {
                "slug": "position-sizing-and-risk-of-ruin",
                "title": "Position sizing and risk of ruin",
                "summary": "Why sizing decisions dominate strategy quality.",
                "difficulty": "beginner",
                "minutes": 10,
                "topics": ["sizing", "risk-of-ruin", "risk"],
                "body": """## The insight that changes everything

Two traders can run the identical strategy. One sizes at 2% of equity per
trade, the other at 20%. Over a decade their outcomes are unrecognizable,
because the second will hit sequences of losses that the first survives.

Sizing is not a detail of implementation. It is often the dominant variable.

## Risk of ruin, roughly

For a trade with win probability `p` and payoff ratio `b`, betting fraction
`f` of equity, the classic approximation is:

```
risk_of_ruin ≈ ((1 - p·b) / (p·b))^((1-f)/f)
```

The exact form matters less than its shape: ruin falls *exponentially* as `f`
shrinks. Halving your bet size does not halve your chance of ruin — it can cut
it by an order of magnitude.

## Fixed fractional sizing

Risk a fixed percentage of current equity per trade, sizing the position from
the stop distance:

```
units = (equity * risk_per_trade) / |entry - stop|
```

This scales down automatically in a drawdown, which is the behavior you want.

## A conservative starting point

Many educators suggest 1–2% of equity at risk per trade. This is a heuristic,
not a law — but it is a defensible place to begin before you have evidence
about your own drawdown behavior.

> **Sample content.** Educational only; this is not personalized financial
> advice and no outcome is promised.
""",
            },
            {
                "slug": "correlation-and-concentration",
                "title": "Correlation and concentration",
                "summary": "Why ten positions can secretly be one position.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["correlation", "diversification", "risk"],
                "body": """## The illusion of diversification

You hold twelve uncorrelated-looking tech names. In a sector shock their
correlations converge toward one, and your portfolio behaves like a single
leveraged bet on that sector. Diversification you can only count on in calm
markets is not diversification.

## Measure it under stress

Average correlation overstates risk; **correlation in drawdowns** is what
hurts. Compare a portfolio's worst-day correlation to its long-run average. A
large gap is a warning about tail behavior.

## Concentration has more faces than position count

- **Sector** — twelve names, one industry.
- **Factor** — all exposed to the same momentum or value factor.
- **Signal** — several strategies all mean-reverting on the same input.
- **Liquidity** — all positions exit through the same thin book.

## Practical controls

- Cap total exposure per sector and per factor, not just per name.
- Monitor portfolio-level metrics: beta to the market, net exposure, and the
  effective number of independent bets.
- Pre-commit a rule for what you do when correlations spike; deciding in the
  moment is how the rule gets abandoned.

> **Sample content.** General education about portfolio construction.
""",
            },
            {
                "slug": "drawdown-math-and-psychology",
                "title": "Drawdown: math and psychology",
                "summary": "Asymmetry, recovery arithmetic, and the point where discipline breaks.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["drawdown", "risk", "psychology"],
                "body": """## The asymmetry that catches people

Losses need disproportionately large gains to recover:

| Drawdown | Required gain |
|----------|---------------|
| 10%      | 11%           |
| 20%      | 25%           |
| 33%      | 50%           |
| 50%      | 100%          |
| 75%      | 300%          |

A 50% loss is not "half as bad as" a 25% loss. It is a different problem
entirely. This asymmetry is the strongest argument for cutting exposure early
rather than waiting for recovery.

## The human part

Drawdowns do not just cost money; they cost conviction. The typical failure
sequence:

1. Confident sizing in calm markets.
2. A loss arrives; you add size to "get it back."
3. A second loss arrives at larger size.
4. You abandon the strategy at its statistically most attractive moment.

The rule that breaks first is the sizing rule, which is why it should be
automated rather than decided under stress.

## Circuit breakers worth pre-committing

- A daily loss limit that flattens you until the next session.
- A drawdown threshold that halves size.
- A maximum consecutive-loss count that triggers a review, not revenge.

> **Sample content.** Educational; the table is arithmetic, not advice.
""",
            },
            {
                "slug": "leverage-what-amplifies-both-ways",
                "title": "Leverage: what amplifies both ways",
                "summary": "Buying power, margin, and the discontinuity of forced exits.",
                "difficulty": "intermediate",
                "minutes": 8,
                "topics": ["leverage", "margin", "risk"],
                "body": """## What leverage actually does

Leverage does not improve a strategy's quality; it scales both its returns and
its risks, and it adds a new failure mode: **forced liquidation**. A strategy
that would have survived a 20% adverse move with 1x can be destroyed by the
same move at 5x, because the margin call happens before the recovery.

## The discontinuity

Without leverage, a drawdown reduces your capital. With leverage, a drawdown
can end your participation entirely. That is the qualitative difference: the
possibility of an absorbing state.

## Sizing under leverage

Volatility-scaled position sizing becomes essential:

```
position = target_risk / realized_volatility
```

This reduces exposure automatically in stressed regimes — exactly the behavior
margin models do not provide for you.

## Questions to ask before using any leverage

- What exact price triggers a forced exit, and how far is it from here?
- Does my sizing rule reduce exposure *before* that level is approached?
- Can the instrument gap through my margin buffer?

> **Sample content.** Educational only. Leverage magnifies losses as reliably
> as gains, and this app makes no recommendation about its use.
""",
            },
        ],
    },
    {
        "number": 6,
        "slug": "pine",
        "title": "Pine Script fundamentals",
        "summary": "Declarations, series semantics, repainting, and debugging.",
        "lessons": [
            {
                "slug": "pine-structure-and-series",
                "title": "Pine structure and the series type",
                "summary": "How Pine evaluates bar by bar, and what 'series' really means.",
                "difficulty": "beginner",
                "minutes": 10,
                "topics": ["pine", "series", "syntax"],
                "body": """## Scripts are re-executed per bar

A Pine script runs once for every bar on the chart. Variables declared at the
global scope are recomputed each bar; `var` persists a value across bars until
reassigned. That single fact explains most beginner confusion.

## The series type

A `series` value is one that can change bar to bar. `close` is a series.
`input.int(14)` is a *simple* value — constant across the chart. Operations that
mix them inherit the series-ness, which is why you cannot use a series where a
constant is required (such as an array size).

## Plotting is the output

```pine
//@version=6
indicator("My first indicator", overlay=true)

len = input.int(20, "Length", minval=1)
ma  = ta.sma(close, len)

plot(ma, "SMA", color=color.blue)
plot(ta.crossover(ma, close) ? close : na, style=plot.style_circles,
     color=color.green, linewidth=2)
```

## Common early mistakes

- Forgetting `//@version=6` and getting v4 semantics.
- Comparing a series to a constant with `=` instead of `==`.
- Expecting `plotshape` to accept a boolean where a series is needed.
- Not handling `na`, which propagates silently through arithmetic.

## Repainting: the topic to internalize early

A repainting indicator shows different values for historical bars than it did
in real time. It is not always a bug, but it always invalidates a backtest that
assumes stability. That is covered in depth in the next lesson.

> **Sample content.** Pine is a TradingView language; this app does not compile
> it. Labs use static checks only.
""",
            },
            {
                "slug": "strategy-vs-indicator",
                "title": "`strategy` vs `indicator`, and misleading overlays",
                "summary": "Backtest declarations, overlays, and the settings that flatter results.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["pine", "strategy", "backtesting"],
                "body": """## The declaration changes everything

`indicator(...)` draws. `strategy(...)` records simulated orders and produces a
backtest report. The strategy declaration also introduces settings that
materially change reported performance:

```pine
strategy("Example", overlay=true,
     initial_capital=100000,
     commission_type=strategy.commission.percent,
     commission_value=0.05,
     slippage=1,
     pyramiding=0)
```

## Settings that flatter

- **Fill on next bar's close** — often the most generous available assumption.
- **Zero commission and slippage** — removes the real cost entirely.
- **Pyramiding** — adds position on every signal, which inflates results in
  trends and blow-ups in chop.

A backtest produced with default settings is closer to an upper bound than an
estimate.

## Overlays can mislead visually

An overlay indicator on a log-scaled chart makes long-run moves look smaller
than they were in percentage terms. Percentage-based rules computed on linear
prices behave differently than they appear.

## Static checks you can run yourself

In the labs here, Pine exercises are graded by static checks — pattern and
structure checks, not compilation:

- Does the script declare a version?
- Are commission and slippage explicitly set?
- Does the exit rule reference the entry bar rather than the current bar?

> **Sample content.** Pine compilation happens inside TradingView only. This
> platform makes no claim that any snippet compiles or is profitable.
""",
            },
            {
                "slug": "repainting-and-lookahead",
                "title": "Repainting and lookahead bias",
                "summary": "The two failure modes that invalidate a Pine backtest.",
                "difficulty": "advanced",
                "minutes": 11,
                "topics": ["pine", "repainting", "lookahead", "backtesting"],
                "body": """## Lookahead

Any construct that reads a future value makes history unrealistically easy:

```pine
// BROKEN: peeks at the bar's high
futureHigh = high[0]      // on the *current* forming bar this is not final
```

On the real-time bar, `high` is still forming. On history it is final. Any rule
that uses it will look perfect historically and fail live.

## Repainting

A repainting script revises its past output. Typical causes:

- `request.security()` without a fixed lookahead, so the callee's close is read
  at the caller's current bar.
- Drawing on `timeframe.isrealtime` conditions.
- Using `barstate.isconfirmed` inconsistently between live and historical bars.
- Daily-aggregate values read intraday, which cannot be known yet.

## The test that exposes it

Load the chart, note the last three signals, then wait for those bars to age
into history. If the values or signals change, the script repaints and any
backtest built on it is optimistic.

## Writing it safely

- Use `request.security(..., lookahead=barmerge.lookahead_on)` with an
  explicitly shifted series, or the correct combination for your intent.
- Confirm signals only on `barstate.isconfirmed`.
- Prefer `close` of the **previous** completed bar over the forming bar.
- Never let a historical-only variable influence a live decision.

> **Sample content.** Educational. This app cannot execute Pine, so labs grade
> these rules statically rather than by compilation.
""",
            },
            {
                "slug": "debugging-pine",
                "title": "Debugging Pine",
                "summary": "Labels, `plotchar`, and isolating a broken condition.",
                "difficulty": "advanced",
                "minutes": 8,
                "topics": ["pine", "debugging"],
                "body": """## Print debugging does not exist

Pine has no console. Your instrumentation is visual: plot values and mark bars.

## The three tools

1. **`plot` the intermediate** — if you expect a condition, plot it. An all-`na`
   line means the condition never fired or the series is wrong.
2. **`plotchar` at the exact bar** — mark where a condition is true:

```pine
plotchar(condition, title="trigger", char="↑", location=location.belowbar,
     color=color.green)
```

3. **`plotshape` for narrative** — good for showing state changes, not values.

## A triage order that works

1. Is the input data what you think? Plot the raw input first.
2. Is the intermediate correct? Plot each step of the chain separately.
3. Is the comparison right? Series-to-series comparisons with `==` on floats
   silently fail.
4. Is `na` propagating? Wrap in `nz()` only *after* you know why it is `na`.

## The classic bug

```pine
longCondition = ta.crossover(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
```

This looks correct and is — but if `fast` and `slow` repaint, the entry will
relocate in history. Debugging the logic when the real fault is in the data
timing wastes hours; check timing first.

> **Sample content.** Educational; Pine is not executed in this platform.
""",
            },
        ],
    },
    {
        "number": 7,
        "slug": "python",
        "title": "Python research tooling",
        "summary": "Reproducible research, feature frames, and evaluation harnesses.",
        "lessons": [
            {
                "slug": "the-research-stack",
                "title": "The research stack",
                "summary": "pandas, numpy, and the reproducibility habits that keep results honest.",
                "difficulty": "beginner",
                "minutes": 9,
                "topics": ["python", "pandas", "reproducibility"],
                "body": """## The core libraries

- **numpy** — arrays and linear algebra; the numeric foundation.
- **pandas** — labeled, time-indexed tables; the data-work language.
- Optional later: **statsmodels** for regressions, **scikit-learn** for ML,
  **matplotlib** for plots.

## Reproducibility is a feature, not overhead

A result you cannot re-derive is not a result. Minimum habits:

- Pin dependency versions.
- Seed every random source.
- Make the run idempotent: same input, same output.
- Store the parameters next to the result.

```python
import numpy as np
rng = np.random.default_rng(42)   # seeded, not np.random.seed
```

## A tidy research layout

```
research/
  data/        # raw, immutable, never edited
  src/         # load, features, backtest
  notebooks/   # exploration only; logic lives in src/
  results/     # dated outputs + parameter snapshots
```

Put logic in modules, not notebooks. Notebooks execute cells out of order and
quietly become unreproducible.

## Load once, verify always

Every loader should assert something: row counts, monotonic timestamps, no
duplicate index entries, and a sanity range on prices. Silent data errors are
the most expensive bugs in this field.

> **Sample content.** Educational; no specific vendor data is endorsed.
""",
            },
            {
                "slug": "building-a-feature-frame",
                "title": "Building a feature frame",
                "summary": "Lagging correctly and avoiding leakage in feature construction.",
                "difficulty": "intermediate",
                "minutes": 10,
                "topics": ["python", "features", "leakage"],
                "body": """## The rule

A feature available at time `t` may only use information known at `t`. Anything
computed with future rows is leakage, and leakage produces spectacular
backtests that vanish live.

## Rolling windows are the danger zone

```python
# LEAKAGE: includes the current and future rows
df["vol"] = df["ret"].rolling(20).std()

# CORRECT: shift so only past rows are used
df["vol"] = df["ret"].rolling(20).std().shift(1)
```

The `shift(1)` is the whole lesson. Whether it belongs depends on when the
signal is evaluated relative to the bar's close — decide it explicitly and
write down which convention you chose.

## Cross-sectional features

Ranking across symbols introduces a second leak: computing a cross-sectional
mean over all symbols on a date can include a symbol's own future. Compute ranks
as of the decision time only.

## A useful invariant

> For every feature, write one line stating when it first becomes knowable.

If you cannot write that line, the feature is not ready.

## Sanity checks worth automating

- Correlation of the feature with next-bar return computed correctly vs
  naively; a large gap suggests leakage.
- A "cheat" feature that uses the label directly; it should score ~perfectly,
  proving your harness detects signal.

> **Sample content.** Educational; snippets are illustrative.
""",
            },
            {
                "slug": "vectorized-vs-event-driven",
                "title": "Vectorized vs event-driven evaluation",
                "summary": "Fast approximations, careful simulations, and when each is honest.",
                "difficulty": "advanced",
                "minutes": 11,
                "topics": ["python", "backtesting", "performance"],
                "body": """## Vectorized

Compute the whole signal matrix at once, then form returns:

```python
signal = (fast > slow).astype(int).shift(1)
returns = (signal * df["ret"]).sum(axis=1)
```

Fast and elegant. The `shift(1)` enforces "trade after the signal is known."
Its weakness: it cannot express position-dependent logic, partial fills, or
path-dependent risk.

## Event-driven

Iterate bars, maintain portfolio state, and apply rules as events arrive.
Slower, more code — and able to model the things vectorized cannot: stops
intrabar, size changes, costs that depend on state, and margin.

## Which is honest?

- **Vectorized** for screening many hypotheses quickly. Label its results
  "approximate."
- **Event-driven** for anything you intend to trade, and for the final numbers
  you report.

The failure mode is quoting vectorized results as if they were
event-driven ones.

## A middle path

Screen hundreds of ideas vectorized; promote survivors to an event-driven
harness with a cost model. Then, and only then, do a walk-forward test.

## Common event-driven bugs

- Filling at the signal bar's close when the signal used that close.
- Ignoring unfilled orders.
- Recomputing position size from future equity.
- Not advancing the clock consistently.

> **Sample content.** Educational; the labs here run Python in your browser via
> Pyodide, isolated with no network or filesystem access.
""",
            },
            {
                "slug": "writing-a-small-harness",
                "title": "Writing a small strategy harness",
                "summary": "The minimal pieces every evaluation loop needs.",
                "difficulty": "advanced",
                "minutes": 10,
                "topics": ["python", "harness", "backtesting"],
                "body": """## Four responsibilities

A harness needs to (1) load data, (2) compute signals, (3) simulate fills with
costs, and (4) report metrics. Keep them separate so each can be tested alone.

## A minimal shape

```python
def backtest(df, signal, cost_bps=5):
    # signal: +1 long, -1 short, 0 flat, already lagged
    pos = signal.shift(1)              # trade the bar after the signal
    ret = pos * df["ret"]
    turn = pos.diff().abs()
    costs = turn * (cost_bps / 10_000)
    pnl = (ret - costs).dropna()
    return {
        "cagr": (1 + pnl).prod() ** (252 / len(pnl)) - 1,
        "vol":  pnl.std() * (252 ** 0.5),
        "sharpe": _sharpe(pnl),
        "max_dd": _max_drawdown(pnl),
        "turnover": turn.mean(),
    }
```

## What the shape enforces

- The `shift(1)` is inside the harness, so no caller can forget it.
- Costs are applied from turnover, so a high-frequency idea pays for itself.
- Metrics are returned as a dict so runs can be compared in a table.

## Reporting rule

Always report **turnover alongside return**. A high Sharpe at extreme turnover
is usually a cost model error, not an edge.

> **Sample content.** Educational and simplified; real harnesses need care with
> intrabar fills, partial execution, and multi-asset accounting.
""",
            },
        ],
    },
    {
        "number": 8,
        "slug": "deployment",
        "title": "Deployment discipline",
        "summary": "Paper trading, monitoring, kill switches, and the ethics of automation.",
        "lessons": [
            {
                "slug": "paper-vs-live",
                "title": "Paper trading vs live: the gap",
                "summary": "What simulation cannot capture and how to stage the transition.",
                "difficulty": "beginner",
                "minutes": 9,
                "topics": ["deployment", "paper-trading", "process"],
                "body": """## The gap is real, and it is not just costs

Paper results overstate live results for reasons beyond slippage:

- **Data availability** — in live trading you get the bar after it closes, not
  at its close.
- **Rejects and partial fills** — a simulator rarely says no.
- **Operational failure** — feeds drop, processes restart, clocks drift.
- **Behavioral drift** — you intervene, and intervention is usually untimed.

## A staged path

1. **Backtest** with costs and walk-forward.
2. **Paper trade** on a live feed for a meaningful window — long enough to see
   both calm and stressed days.
3. **Tiny size** where a full loss is acceptable and the point is operational
   learning, not return.
4. **Scale slowly**, and only after the operational log is boring.

## What to compare

Do not compare returns at first. Compare **decisions**: did the live system
take the same trades the simulator predicted for the same data? Divergence in
decisions is the thing to fix before diverging returns.

## The honest framing

> Paper trading is not a weaker version of live trading. It is a different
> experiment whose purpose is to validate your *plumbing*.

> **Sample content.** Educational; this platform does not connect to any broker
> and cannot paper-trade a live feed.
""",
            },
            {
                "slug": "monitoring-and-kill-switches",
                "title": "Monitoring, alerting, and kill switches",
                "summary": "Designing for the day something goes wrong.",
                "difficulty": "intermediate",
                "minutes": 10,
                "topics": ["deployment", "monitoring", "risk", "ops"],
                "body": """## Assume a component will fail

Every live system eventually: loses its data feed, submits a duplicate order,
misreads a position, or hangs. Designing as if this will not happen is the most
expensive assumption in the stack.

## What to monitor

- **Heartbeat** — has the process run recently?
- **Data sanity** — is the feed stale, are prices within a plausible band?
- **Position reconciliation** — does my model of my position match the broker?
- **Risk limits** — daily loss, max position, max orders per minute.

## The kill switch

A kill switch must be:

- **Fast** — faster than the strategy's worst-case loss accumulation.
- **Independent** — running outside the process it kills.
- **Tested** — exercised on a schedule, not only in an incident.

An untested kill switch is a hope.

## Alerting that gets read

Alert on **state**, not on noise. "Feed stale for 90 seconds" is actionable;
"price moved 0.3%" at 3am is how alert fatigue begins and real incidents get
missed.

## Log as evidence

Log every order intent, every fill, every rejection, and every manual override.
When something goes wrong — and it will — the log is the difference between a
post-mortem and a guess.

> **Sample content.** Educational; no deployment or broker integration exists
> in this platform.
""",
            },
            {
                "slug": "journaling-and-postmortems",
                "title": "Journaling, review, and post-mortems",
                "summary": "Turning incidents and trades into durable process improvement.",
                "difficulty": "beginner",
                "minutes": 8,
                "topics": ["journaling", "review", "process"],
                "body": """## Review on a schedule

Daily: what did the system do, and did it match intent? Weekly: which rules
held, which were bent? Monthly: is the process producing the records it should?

## The post-mortem format

When something breaks, write:

1. **What happened**, in timeline form, with times.
2. **What should have happened.**
3. **The gap** — the single mechanism that produced the difference.
4. **Detection** — how long it took to notice, and why.
5. **Fix** — a change to the system, not to a person.

## Blameless is practical, not sentimental

If a post-mortem ends with "operator error," nothing has been learned. The
useful question is which property of the system made that error possible, cheap
to make, or slow to detect.

## The journal pays compounding interest

Your mistake log is the only dataset that describes **your** failure modes. Over
a year it becomes more predictive of your results than any market model.

> **Sample content.** Educational; this app provides notes and reports for your
> own records, and exports them as JSON or Markdown.
""",
            },
            {
                "slug": "ethics-and-what-not-to-automate",
                "title": "Ethics, regulation, and what not to automate",
                "summary": "Manipulation, access boundaries, and responsibilities.",
                "difficulty": "intermediate",
                "minutes": 9,
                "topics": ["ethics", "compliance", "safety"],
                "body": """## Lines that are not blurry

Certain behaviors are illegal in most markets regardless of intent or
sophistication:

- **Spoofing / layering** — placing orders you intend to cancel to create a
  false impression of depth.
- **Wash trading** — trading with yourself to manufacture volume.
- **Marking the close** — trading to move a benchmark you are valued against.

Automation does not change their status. "The bot did it" is not a defense.

## Access boundaries

Never share credentials, and never let a study tool hold them. A system that
only reads market data cannot place an order — that property is worth
preserving deliberately.

## Market impact on others

If your strategy's edge depends on moving prices that other participants see,
you are externalizing cost. Understand where your fills come from.

## Responsible disclosure

If you find a genuine exchange or vendor vulnerability, report it through
proper channels rather than trading on it.

## The durable principle

> Automate analysis freely. Automate execution only where you would be
> comfortable explaining the mechanism, in writing, to a regulator and to the
> person on the other side of your fill.

> **Sample content.** General education; not legal advice. Rules vary by venue
> and jurisdiction.
""",
            },
        ],
    },
]
