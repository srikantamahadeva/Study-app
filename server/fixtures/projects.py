"""Sample capstone projects A-J.

Each project is a research or tooling exercise. None asks you to connect a
broker, hold credentials, or place orders. All are labeled origin="sample".
"""

PROJECTS = [
    dict(
        key="A",
        title="Build a reproducible data pipeline",
        objectives=[
            "Load OHLCV data from a source you choose and store it immutably.",
            "Assert on row counts, monotonic timestamps and duplicates at load time.",
            "Produce a single command that rebuilds the dataset from scratch.",
        ],
        prerequisites=["Basic Python", "Comfort with pandas DataFrames"],
        steps=[
            {"title": "Define the storage layout", "detail": "Raw data is immutable and separate from anything derived."},
            {"title": "Write a loader with assertions", "detail": "Fail loudly on duplicate timestamps, non-monotonic indices, or implausible prices."},
            {"title": "Handle corporate actions", "detail": "State your adjustment convention explicitly and record it with the data."},
            {"title": "Make it idempotent", "detail": "Running twice produces identical output."},
        ],
        required_files=["load.py", "validate.py", "README.md"],
        example_inputs=[{"source": "vendor CSV", "symbols": ["AAA", "BBB"], "start": "2018-01-01"}],
        expected_outputs="A validated parquet dataset plus a validation report.",
        acceptance_tests=[
            "Loading the same source twice yields byte-identical output.",
            "A deliberately duplicated row causes the validator to raise.",
            "Timestamps are strictly increasing after load.",
            "The adjustment convention is written to a metadata file.",
        ],
        failure_scenarios=[
            "Vendor silently reorders rows.",
            "A symbol is missing for part of the requested range.",
            "A corporate action appears mid-range and breaks price continuity.",
        ],
        security_checks=[
            "No API credentials are stored in the repository or in notebooks.",
            "Data source credentials come from the environment only.",
        ],
        completion_criteria=[
            "One command rebuilds the dataset.",
            "All acceptance tests pass.",
            "README states the adjustment convention and its consequences.",
        ],
        final_assessment=(
            "Most research failures begin upstream of the strategy. This project "
            "proves your data layer fails loudly instead of quietly. It is "
            "education and research only; no trading is involved."
        ),
    ),
    dict(
        key="B",
        title="Test a hypothesis with walk-forward validation",
        objectives=[
            "Write a falsifiable hypothesis before computing anything.",
            "Implement walk-forward evaluation with purge and embargo.",
            "Report the distribution of fold results, not just the mean.",
        ],
        prerequisites=["Project A", "Familiarity with train/validate/test"],
        steps=[
            {"title": "Pre-register the hypothesis", "detail": "Record metric, minimum success value, and kill criterion in your journal first."},
            {"title": "Design the walk-forward loop", "detail": "Choose train and test window lengths and justify them."},
            {"title": "Implement purge and embargo", "detail": "Remove overlapping rows and add an embargo gap equal to your label horizon."},
            {"title": "Report honestly", "detail": "Publish fold-level results including the worst fold."},
        ],
        required_files=["hypothesis.md", "walkforward.py", "results/"],
        example_inputs=[{"train_days": 756, "test_days": 126, "embargo_days": 5}],
        expected_outputs="A table of per-fold metrics and an aggregated out-of-sample equity curve.",
        acceptance_tests=[
            "The hypothesis was written to disk before any result was computed.",
            "No training row overlaps a test row after purging.",
            "The embargo gap is at least the label horizon.",
            "All folds are reported, including negative ones.",
        ],
        failure_scenarios=[
            "One fold carries the entire result.",
            "Removing the embargo silently improves results.",
            "The result depends on a single calendar year.",
        ],
        security_checks=[
            "No credentials in the repository.",
            "The process runs fully offline on stored data.",
        ],
        completion_criteria=[
            "Out-of-sample results are computed only on held-forward windows.",
            "The kill criterion you pre-registered was actually evaluated.",
        ],
        final_assessment=(
            "The deliverable is not a return number. It is a demonstration that "
            "you can measure an idea without flattering it. Education and "
            "research only."
        ),
    ),
    dict(
        key="C",
        title="Build a cost-aware backtest harness",
        objectives=[
            "Implement event-driven simulation with explicit costs.",
            "Sweep costs at 1x, 2x and 3x and report sensitivity.",
            "Report turnover alongside every return figure.",
        ],
        prerequisites=["Project A", "Python comfort"],
        steps=[
            {"title": "Separate the four responsibilities", "detail": "Load, signal, simulate, report — as independently testable modules."},
            {"title": "Model costs explicitly", "detail": "Spread, per-side fees, and a slippage term."},
            {"title": "Add sensitivity sweeping", "detail": "Same idea at multiple cost levels, tabulated."},
            {"title": "Unit test the harness", "detail": "Hand-computed cases for a two-bar trade."},
        ],
        required_files=["harness.py", "costs.py", "test_harness.py"],
        example_inputs=[{"fee_bps": 2.0, "slippage_bps": 3.0, "sweep": [1, 2, 3]}],
        expected_outputs="A metrics table with return, volatility, Sharpe, max drawdown and turnover per cost level.",
        acceptance_tests=[
            "A flat position produces exactly zero cost.",
            "A one-bar round trip pays one entry and one exit cost.",
            "Doubling turnover doubles cost, all else equal.",
            "The 3x cost column is strictly worse than the 1x column.",
        ],
        failure_scenarios=[
            "Turnover is undercounted by ignoring the entry transition.",
            "Costs are applied to returns rather than to notional.",
            "A zero-cost assumption leaks back in.",
        ],
        security_checks=[
            "No live order routing or broker SDK is imported.",
            "No credentials of any kind are present.",
        ],
        completion_criteria=[
            "Costs are declared in one place and swept.",
            "Every reported return includes its turnover figure.",
        ],
        final_assessment=(
            "You cannot judge an idea until you know what it costs to trade. "
            "This project makes cost a first-class input. Education and research "
            "only."
        ),
    ),
    dict(
        key="D",
        title="Detect and eliminate lookahead bias",
        objectives=[
            "Construct a deliberately leaky feature and prove your harness catches it.",
            "Fix it with correct lagging and re-measure.",
            "Automate a leakage regression test.",
        ],
        prerequisites=["Project C"],
        steps=[
            {"title": "Build the cheat feature", "detail": "A feature that uses the label. It should score near-perfectly."},
            {"title": "Prove the harness detects it", "detail": "The cheat must show up as wildly better than a real feature."},
            {"title": "Fix with lagging", "detail": "Apply shift and re-run; performance should collapse toward realism."},
            {"title": "Add a regression test", "detail": "Fail the build if any future feature correlates suspiciously with the label."},
        ],
        required_files=["leaky.py", "fixed.py", "test_leakage.py"],
        example_inputs=[{"feature": "rolling_mean_of_future_close", "window": 5}],
        expected_outputs="A before/after comparison demonstrating the leak and its fix.",
        acceptance_tests=[
            "The leaky version scores dramatically higher than the fixed version.",
            "The fixed version's feature uses only past bars.",
            "A regression test fails when the leak is reintroduced.",
        ],
        failure_scenarios=[
            "Rolling windows include the current bar when they should not.",
            "Cross-sectional ranks are computed with a symbol's own future.",
            "A target is accidentally included in the feature matrix.",
        ],
        security_checks=["No credentials required."],
        completion_criteria=[
            "The harness demonstrably detects a known leak.",
            "The fixed feature states when it becomes knowable.",
        ],
        final_assessment=(
            "You have not understood lookahead until you have seen it inflate a "
            "result in your own harness. Education and research only."
        ),
    ),
    dict(
        key="E",
        title="Design a position-sizing and drawdown framework",
        objectives=[
            "Implement fixed-fractional sizing from stop distance.",
            "Compute risk of ruin across a grid of bet fractions.",
            "Add pre-committed circuit breakers.",
        ],
        prerequisites=["Project C", "Basic probability"],
        steps=[
            {"title": "Implement sizing", "detail": "risk_budget / stop_distance, with a zero-distance guard."},
            {"title": "Grid the risk of ruin", "detail": "Compute across bet fractions and win rates; visualize the surface."},
            {"title": "Add circuit breakers", "detail": "Daily loss limit, drawdown-based size reduction, and a consecutive-loss review trigger."},
            {"title": "Test the breakers", "detail": "Feed a synthetic losing streak and confirm the breakers fire."},
        ],
        required_files=["sizing.py", "ruin.py", "breakers.py", "test_breakers.py"],
        example_inputs=[{"risk_per_trade": 0.01, "win_rate": 0.52, "payoff_ratio": 1.6}],
        expected_outputs="A sizing module, a ruin surface, and breaker behaviour under a synthetic losing streak.",
        acceptance_tests=[
            "Sizing scales linearly with the risk budget.",
            "Risk of ruin falls monotonically as bet fraction falls.",
            "The daily loss breaker flattens the book for the session.",
            "The drawdown breaker halves size once the threshold is crossed.",
        ],
        failure_scenarios=[
            "A zero-distance stop causes a division by zero.",
            "The breaker fires after the loss, not before it.",
            "Sizing ignores a concurrent correlated position.",
        ],
        security_checks=["No broker connectivity.", "No credentials."],
        completion_criteria=[
            "Breakers are demonstrably automatic, not advisory.",
            "The ruin surface is reported with the assumptions stated.",
        ],
        final_assessment=(
            "Sizing and circuit breakers are what survive a bad week. This "
            "project builds them as code rather than as intentions. Education "
            "and research only."
        ),
    ),
    dict(
        key="F",
        title="Build a topic-mastery measurement report",
        objectives=[
            "Aggregate quiz attempts into per-topic accuracy.",
            "Compute an exponential moving average of mastery.",
            "Recommend revision targets from actual weak spots.",
        ],
        prerequisites=["Comfort with Python dictionaries and grouping"],
        steps=[
            {"title": "Define topics", "detail": "Tag questions by concept and list them explicitly."},
            {"title": "Aggregate attempts", "detail": "Per topic: attempts, correct, accuracy."},
            {"title": "Smooth with an EMA", "detail": "Recent answers weigh more than old ones."},
            {"title": "Produce recommendations", "detail": "Sort by mastery and surface the weakest topics with at least three attempts."},
        ],
        required_files=["mastery.py", "report.py", "test_mastery.py"],
        example_inputs=[{"ema_alpha": 0.3, "min_attempts": 3}],
        expected_outputs="A sorted topic table plus a short list of revision targets.",
        acceptance_tests=[
            "A topic with zero attempts is excluded from recommendations.",
            "Mastery is bounded between 0 and 100.",
            "A correct answer raises mastery and an incorrect one lowers it.",
            "Recommendations are sorted ascending by mastery.",
        ],
        failure_scenarios=[
            "Topics with one attempt dominate the weak list.",
            "Mastery drifts outside its bounds after many updates.",
            "A topic with no attempts is shown as 0% mastery.",
        ],
        security_checks=["No external data leaves the process."],
        completion_criteria=[
            "Every number is derived from recorded attempts.",
            "The report states its smoothing parameter.",
        ],
        final_assessment=(
            "This app computes exactly this over your quiz history. Rebuilding "
            "it teaches you what the numbers do and do not mean. Education only."
        ),
    ),
    dict(
        key="G",
        title="Implement an SM-2 spaced repetition scheduler",
        objectives=[
            "Implement the SM-2 state machine: new, learning, review, relearning.",
            "Handle lapses and ease bounds correctly.",
            "Reproduce the intervals in the app against a fixed sequence of grades.",
        ],
        prerequisites=["Basic Python"],
        steps=[
            {"title": "Model the state", "detail": "ease, interval, repetitions, lapses, state."},
            {"title": "Implement grading", "detail": "again / difficult / good / easy transitions with bounded ease."},
            {"title": "Handle lapses", "detail": "A lapse returns the card to relearning and increments lapses."},
            {"title": "Verify against a sequence", "detail": "Feed a known grade sequence and compare intervals."},
        ],
        required_files=["sm2.py", "test_sm2.py"],
        example_inputs=[{"grades": ["good", "good", "easy", "again", "good"]}],
        expected_outputs="A scheduler whose intervals match a fixed expected sequence.",
        acceptance_tests=[
            "Ease never falls below 1.3 or rises above 3.0.",
            "'again' resets repetitions and moves the card to relearning.",
            "Intervals are capped at 365 days.",
            "A brand-new card graded 'good' gets a one-day interval.",
        ],
        failure_scenarios=[
            "Ease drifts below 1.3 after repeated failures.",
            "Intervals grow unbounded and the card disappears forever.",
            "'again' does not reset repetitions.",
        ],
        security_checks=["No credentials; pure functions."],
        completion_criteria=[
            "All four grades produce the documented transitions.",
            "Ease bounds are enforced and tested.",
        ],
        final_assessment=(
            "Spaced repetition looks simple until you handle lapses and bounds. "
            "This project closes that gap. Education only."
        ),
    ),
    dict(
        key="H",
        title="Create a Pine Script static analyzer",
        objectives=[
            "Parse a Pine script for version declarations and risky constructs.",
            "Flag repaint-causing patterns and missing cost settings.",
            "Report findings with line numbers.",
        ],
        prerequisites=["Python regular expressions", "Basic Pine awareness"],
        steps=[
            {"title": "Define rules", "detail": "Version missing, strategy without commission, unguarded request.security."},
            {"title": "Implement checks", "detail": "Return findings with rule name, line, and severity."},
            {"title": "Add repaint detection", "detail": "Flag request.security without an explicit lookahead."},
            {"title": "Test against samples", "detail": "Use the lab exercises here as fixtures."},
        ],
        required_files=["analyzer.py", "test_analyzer.py", "samples/"],
        example_inputs=[{"file": "samples/repainting.pine"}],
        expected_outputs="A findings list with severity and line numbers.",
        acceptance_tests=[
            "A missing //@version is reported as an error.",
            "A strategy without commission settings is flagged.",
            "request.security without lookahead is flagged as repainting risk.",
            "Line numbers are accurate.",
        ],
        failure_scenarios=[
            "A commented-out directive is treated as live code.",
            "A string literal containing 'security' triggers a false positive.",
        ],
        security_checks=[
            "The analyzer never executes the script it reads.",
            "Input files are treated as untrusted text.",
        ],
        completion_criteria=[
            "All four rule families are implemented.",
            "False positives are documented.",
        ],
        final_assessment=(
            "Static analysis is the honest way to review Pine here, since this "
            "platform does not compile it. Education and research only."
        ),
    ),
    dict(
        key="I",
        title="Build an experiment journal with post-mortems",
        objectives=[
            "Store structured journal entries: hypothesis, preconditions, result, verdict.",
            "Derive statistics about your own decisions over time.",
            "Generate a post-mortem from a failed experiment.",
        ],
        prerequisites=["Project B"],
        steps=[
            {"title": "Define the schema", "detail": "Fixed fields so entries become a dataset rather than free text."},
            {"title": "Add verdict tracking", "detail": "keep / change / discard, plus a reason."},
            {"title": "Compute self-statistics", "detail": "How often each verdict preceded a positive out-of-sample result."},
            {"title": "Write a post-mortem", "detail": "Timeline, gap, detection, and a system fix."},
        ],
        required_files=["journal.py", "postmortem.py", "entries/"],
        example_inputs=[{"entry": "hypothesis + verdict + reason"}],
        expected_outputs="A journal plus a monthly summary of your decision quality.",
        acceptance_tests=[
            "Every entry has a hypothesis recorded before a result.",
            "Verdicts carry a non-empty reason.",
            "The summary reports outcomes by verdict type.",
            "A post-mortem names a system change, not a person.",
        ],
        failure_scenarios=[
            "Entries are added after results are known.",
            "Verdicts are never recorded, so no statistics accrue.",
            "Post-mortems end at 'operator error'.",
        ],
        security_checks=["Journal contents stay local and private."],
        completion_criteria=[
            "Entries are structured and exportable.",
            "The monthly summary is generated from recorded data only.",
        ],
        final_assessment=(
            "Your mistake log is the only dataset describing your own failure "
            "modes. This project makes it a first-class artifact. Education only."
        ),
    ),
    dict(
        key="J",
        title="Write an operations runbook and kill-switch design",
        objectives=[
            "Document monitoring checks with thresholds and owners.",
            "Design an independent, scheduled-tested kill switch.",
            "Run a tabletop incident and record the post-mortem.",
        ],
        prerequisites=["Project E"],
        steps=[
            {"title": "Enumerate failure modes", "detail": "Feed loss, duplicate order, position mismatch, clock drift, hung process."},
            {"title": "Specify monitoring", "detail": "For each check: what is measured, threshold, alert channel, and expected response."},
            {"title": "Design the kill switch", "detail": "Independent process, documented trigger conditions, and a test schedule."},
            {"title": "Run a tabletop exercise", "detail": "Inject a failure on paper and walk through detection and response."},
        ],
        required_files=["runbook.md", "killswitch.md", "postmortem.md"],
        example_inputs=[{"scenario": "data feed stale for 5 minutes during a volatile session"}],
        expected_outputs="A runbook, a kill-switch design, and one written post-mortem.",
        acceptance_tests=[
            "Every monitoring check names a threshold and a response.",
            "The kill switch runs outside the process it kills.",
            "The kill switch has a documented test schedule.",
            "The post-mortem names a system fix rather than a person.",
        ],
        failure_scenarios=[
            "The kill switch depends on the failing process.",
            "Alerts fire on noise and get muted.",
            "Nobody knows who responds at 3am.",
        ],
        security_checks=[
            "The runbook contains no credentials or secret values.",
            "Access boundaries are documented rather than shared.",
        ],
        completion_criteria=[
            "A tabletop exercise has been run and recorded.",
            "Every alert has a documented expected response.",
        ],
        final_assessment=(
            "Operational discipline, not signal quality, is what usually decides "
            "whether a system survives its first bad week. This project is "
            "entirely a documentation and design exercise: no broker, no "
            "credentials, no orders."
        ),
    ),
]
