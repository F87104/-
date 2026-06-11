# Sai Method Automation Spec v0.2

Source: user-provided transcripts of Sai "FX完全攻略！プロトレーダーの全戦略を大公開" and "FXトレード手法完全攻略".

Purpose: convert the discretionary Sai method into rules that can be tested in Forex Tester, TradingView, Python, or a semi-automated AI review workflow.

This is not investment advice. It is a technical rule specification for backtesting and automation.

## Core Idea

Sai method is a trend-following, price-action method built around:

- One-hour chart as the primary decision chart.
- "Short-mid alignment" as the definition of trend-following.
- Avoiding vague, emotional, or "looks like it will move" trades.
- Trading only when trend, momentum, and a defined setup align.
- Separating setup from trigger.
- Avoiding first breakouts in many cases, especially range breakouts.
- Taking the middle of the move, not the exact top or bottom.
- Letting profits run while the trend structure remains intact.
- Seeking low-volatility entry areas that can lead to one-directional moves.

## Default Timeframe

- Primary timeframe: 1H.
- Avoid applying the main setup directly to 5M or 15M because precision drops.
- Daily/weekly/monthly can be checked as background, but the operational rules are based on 1H.
- Chart view should show roughly 4 to 5 months of 1H history for context.

## Short-Mid Alignment

Sai defines trend-following as alignment between the medium-term direction and the short-term direction.

Medium-term direction:

- Use roughly the prior 1 month of 1H price action.
- For bullish bias, the medium-term path should be rising or have clearly bottomed and turned upward.
- For bearish bias, the medium-term path should be falling or have clearly topped and turned downward.

Short-term direction:

- Use the latest several hours to roughly 1 week of 1H price action.
- The latest few hours are especially important.
- If short-term price is temporarily moving against the medium-term direction, do not enter.

Bullish short-mid alignment:

- Medium-term direction is up.
- Short-term direction is also up.
- Only long setups are considered.

Bearish short-mid alignment:

- Medium-term direction is down.
- Short-term direction is also down.
- Only short setups are considered.

If medium-term and short-term direction disagree, classify as no-trade.

## Key Definitions

### Setup And Trigger

Setup means the market condition where trading is allowed.

Trigger means the exact entry event inside that allowed condition.

Setup examples:

- Range has ended and trend direction is emerging.
- Short-mid alignment exists.
- Trend and momentum are present.
- Price is near an important support/resistance level.
- Price is in a valid stagnation/V-shape/second-breakout context.

Trigger examples:

- Break above a valid stagnation zone.
- Break below a valid stagnation zone.
- Break of the second range breakout level.
- V-shape completion plus a small continuation break.

If the setup is absent, do not look for triggers.

### Trend

Bullish trend:

- Price is forming higher highs and higher lows.
- Recent swing highs are being exceeded.
- Recent swing lows are not being broken.

Bearish trend:

- Price is forming lower lows and lower highs.
- Recent swing lows are being broken.
- Recent swing highs are not being reclaimed.

If swing structure is unclear, classify as no-trade.

### Momentum

Momentum means price is moving with visible force in one direction.

Bullish momentum examples:

- Consecutive bullish candles.
- Large-bodied candles.
- Few upper/lower wicks against the direction.
- Price advances quickly toward a key resistance.

Bearish momentum examples:

- Consecutive bearish candles.
- Large-bodied candles.
- Few counter-direction wicks.
- Price declines quickly toward a key support.

No momentum:

- Sideways drift.
- Alternating small candles.
- Many wicks.
- No clear direction after a prior trend move.

### Stagnation

Stagnation is a pause at roughly the same price zone.

Default definition:

- 1H chart.
- 7 to 8 candles or more.
- Price remains in a relatively narrow zone.
- The zone is near a meaningful support/resistance area, or appears after a strong trend/momentum move.

The exact width should be volatility-adjusted, not fixed in pips.

Suggested measurable version:

- stagnation_bars >= 7
- zone_height <= 0.8 * ATR(14) to 1.5 * ATR(14), depending on instrument volatility
- candles overlap the same zone by at least 60%

Reset rule:

- If price leaves the stagnation zone and then returns, reset the stagnation count to 0.
- This leave-and-return behavior can show momentum, but it is not an immediate entry signal.
- Wait for a fresh stagnation count or a separate valid trigger.

Wide/irregular stagnation:

- If the zone is wider than normal, do not enter inside the zone.
- Wait for the upper/lower boundary or a smaller internal zone to break.
- If the zone drifts slightly against the intended direction, wait until price reverses and breaks the relevant boundary.

## No-Trade Filters

Do not enter when any of these are true:

1. Range Market
   - Price has moved sideways in the same broad zone for about 1 month or more.
   - Upper and lower range boundaries have been touched or rejected at least twice where possible.
   - No clear trend has emerged.

2. No Momentum
   - The prior trend has stalled.
   - Price is sideways after a trend move.
   - Direction is unclear.
   - This state can become a range later.

3. Too Far From Key Level
   - Price is far from important resistance/support.
   - Even if short-term candles look trendy, the move is still inside a larger range or triangle.
   - Wait until price approaches the key level and shows valid behavior there.

4. First Breakout Of A Range
   - For range breakouts, the first break is often ignored.
   - Prefer second breakout after price returns into the range or retests and breaks again.

5. Weak Single Reason
   - Do not trade only because of a golden cross, RSI, double bottom, neckline break, or "looks strong".
   - These can be supporting factors, not the whole reason.

6. Directionless Pause After Trend
   - After a trend leg ends, price can pause without becoming a full range yet.
   - This is setup-outside territory.
   - Wait until direction and momentum return.

7. After Crash / Violent Move
   - After a sharp crash or violent spike, volatility and randomness are high.
   - Ordinary setups may stop working temporarily.
   - Avoid trading until volatility calms and directional structure returns.

8. Plain Breakout
   - A simple high break or resistance break in a normal trend is not enough.
   - Add a plus-alpha factor: stagnation, V-shape, failed first breakout, second breakout, or clear key-level behavior.

9. Strong Higher-Timeframe Bias Against The Trade
   - In a strong multi-month uptrend, avoid casual shorts.
   - In a strong multi-month downtrend, avoid casual longs.
   - Counter-trend trades require much stronger evidence and are generally not the main Sai approach.

10. Thin/Seasonal Market
    - Avoid mid-December through early January unless the setup is unusually clear.
    - Market participation can be thin and random moves are more common.

11. Instrument Mismatch
    - Avoid assuming every instrument fits the method.
    - The transcript specifically warns that USDJPY tends to be less compatible because of frequent ranges and smaller volatility.

## Entry Setup A: Simple High/Low Stagnation

Use when a trend and momentum are already clear.

Bullish setup:

- 1H bullish trend exists.
- Bullish momentum exists.
- Price pauses at a high zone for 7 to 8 candles or more.
- Stagnation remains relatively tight.
- Enter long when stagnation breaks upward or when continuation is confirmed.

Bearish setup:

- 1H bearish trend exists.
- Bearish momentum exists.
- Price pauses at a low zone for 7 to 8 candles or more.
- Stagnation remains relatively tight.
- Enter short when stagnation breaks downward or continuation is confirmed.

Rationale:

- No pullback entry may appear.
- Stagnation can act as the "pause before continuation".

## Entry Setup B: Stagnation Near Resistance/Support

Bullish setup:

- Medium-term trend is bullish.
- Short-term momentum is bullish.
- Price approaches an important resistance.
- Price stagnates just before, on, or slightly around that resistance.
- Enter long if stagnation holds and continuation/break is likely.

Bearish setup:

- Medium-term trend is bearish.
- Short-term momentum is bearish.
- Price approaches an important support.
- Price stagnates just before, on, or slightly around that support.
- Enter short if stagnation holds and continuation/break is likely.

Avoid:

- Stagnation far away from the key level.
- Stagnation immediately after a pullback with weak momentum.

## Entry Setup C: Stagnation After Breakout

Bullish setup:

- Price clearly breaks an important resistance.
- After breakout, price pauses/stagnates above or around the broken level.
- Enter long from the post-breakout stagnation if momentum remains bullish.

Bearish setup:

- Price clearly breaks an important support.
- After breakout, price pauses/stagnates below or around the broken level.
- Enter short from the post-breakout stagnation if momentum remains bearish.

Risk:

- This can fail quickly after entry.
- If price reverses after entry and the setup premise breaks, cut immediately.

## Entry Setup D: Wide Stagnation

Use when stagnation exists, but the range is wider and less clean.

Bullish setup:

- Price is near important resistance.
- Stagnation is visible, but candles fluctuate more widely.
- Do not enter inside the wide fluctuation.
- Wait for a smaller internal zone or the resistance/stagnation zone to break upward.

Bearish setup:

- Price is near important support.
- Stagnation is visible, but candles fluctuate more widely.
- Do not enter inside the wide fluctuation.
- Wait for a smaller internal zone or support/stagnation zone to break downward.

Important:

- Wide stagnation is valid mainly near a key level.
- Do not use it in the middle of a range or where momentum is absent.
- Do not treat every broad sideways area as a setup.

## Entry Setup E: V-Shape / Sudden Reversal

Bullish V-shape:

- Price drops sharply.
- Price rebounds sharply with similar force.
- Price returns close to the original breakdown/start zone.
- The move suggests a possible trend transition or strong continuation.

Entry approaches:

- Conservative: wait until price returns to the pre-drop area and stabilizes/breaks.
- Aggressive: if about 80% of the drop has recovered and price stagnates near resistance in a strong broader uptrend, early entry may be allowed.

Bearish inverse V-shape:

- Price rises sharply.
- Price falls sharply with similar force.
- Price returns close to the original rally/start zone.
- Use symmetric logic for shorts.

Notes:

- V-shape is more difficult than stagnation.
- It is strongest when combined with stagnation, key level behavior, or a broader trend transition.
- A partial recovery is not enough unless other strong evidence exists.

### V-Shape Quality Checklist

When unsure whether a V-shape is valid, check:

- Did it occur during or after a meaningful trend/momentum context?
- Is it a sharp recovery, not a slow drift back?
- Did it trap or fake out participants who chased the prior direction?
- Did price recover close to the original breakdown/start area?
- Is there a follow-up trigger such as stagnation or a small continuation break?

Do not treat every bounce as a V-shape.

## Entry Setup E2: Sudden Reversal Plus V-Shape

Bullish version:

- A sharp downward move occurs.
- Price rapidly recovers.
- This sudden reversal is the setup.
- A smaller V-shape, stagnation, or continuation break becomes the trigger.
- Do not enter too early while downward momentum still dominates.

Bearish version:

- A sharp upward move occurs.
- Price rapidly falls back.
- This sudden reversal is the setup.
- A smaller inverse V-shape, stagnation, or continuation break becomes the trigger.

## Entry Setup E3: Sudden Reversal Plus Stagnation

Bullish version:

- Price sharply breaks downward from a prior area or range.
- Price quickly returns back into or above that area.
- Price then forms high stagnation, ideally near a resistance/key level.
- Enter on break of the stagnation zone.

Bearish version:

- Price sharply breaks upward from a prior area or range.
- Price quickly returns back into or below that area.
- Price then forms low stagnation, ideally near a support/key level.
- Enter on break of the stagnation zone.

The sudden reversal is the setup; stagnation is the trigger.

## Entry Setup E4: V-Shape Plus High/Low Stagnation

Bullish:

- V-shape recovery appears in a bullish short-mid alignment.
- Price forms high stagnation after the V-shape.
- Enter when the high stagnation breaks upward.

Bearish:

- Inverse V-shape appears in a bearish short-mid alignment.
- Price forms low stagnation after the inverse V-shape.
- Enter when the low stagnation breaks downward.

## Entry Setup F: Range Breakout, Second Breakout

Bullish setup:

- A range exists for about 1 month or more.
- Price breaks above the range once.
- First breakout is not entered.
- Price returns into the range or fails to extend.
- Price then breaks the prior breakout high again.
- Enter on this second breakout.

Bearish setup:

- A range exists for about 1 month or more.
- Price breaks below the range once.
- First breakout is not entered.
- Price returns into the range or fails to extend.
- Price then breaks the prior breakout low again.
- Enter on this second breakout.

Not valid:

- Simple higher-high continuation inside an existing trend is not the same as "second breakout".
- The prior structure must be a range, not merely a small trend step.

If second breakout fails:

- Cut the loss immediately.
- A third or fourth breakout attempt can still be valid.
- If repeated attempts fail and price keeps rejecting the same area, reclassify as a range and switch to wait mode.

## Exit Rules

### Exit Principle

If the position is profitable and price continues in the profit direction, avoid premature exit.

Do not exit only because:

- Price has moved a lot.
- It "feels" overextended.
- Unrealized profit has become emotionally large.
- A small pullback appears.
- The current profit/loss amount feels large or painful.

Exit decisions should be based on chart structure, not current yen/dollar profit.

For a trend-following long position, selling while price is still rising is effectively acting against the trend. For a trend-following short, buying back while price is still falling is the same issue. The method tries to keep the exit logic aligned with the entry logic.

### Exit Rule 1: Watch One Swing

For long positions:

- After entry, let price form at least one pullback/swing.
- Continue holding while the latest pullback low is not broken.
- Exit if price breaks the latest meaningful pullback low after a profitable advance.

For short positions:

- Let price form at least one bounce/swing.
- Continue holding while the latest bounce high is not broken.
- Exit if price breaks above the latest meaningful bounce high after a profitable decline.

### Exit Rule 2: Bonus Time

Bonus time is the period after a valid trend-following entry where the trade is expected to move in the profit direction.

Default:

- About 2 to 3 weeks after entry.
- Only applies when the trade is already in profit.
- Only applies to a valid trend-following setup with edge.

During bonus time:

- A straight-line counter-move can be treated as temporary adjustment if no clear swing break has formed.
- Hold unless the original setup is invalidated or a meaningful swing level breaks.

After bonus time:

- If price makes a sharp counter-move, exit is more acceptable.
- The original edge decays with time.

### Exit Rule 3: Consolidation Neckline Break

For a profitable long:

- If price consolidates for 2 days or more.
- Draw the local consolidation support/neckline.
- Exit if price breaks below that neckline.

For a profitable short:

- If price consolidates for 2 days or more.
- Draw the local consolidation resistance/neckline.
- Exit if price breaks above that neckline.

Rationale:

- After consolidation, price tends to continue in the breakout direction.
- A break against the position can signal trend pause or reversal.

## Stop Loss Rules

The transcript emphasizes immediate loss cutting when the setup premise fails.

Suggested measurable stops:

- Initial stop beyond the opposite side of the stagnation zone.
- Or beyond the most recent swing low/high.
- Or fixed risk boundary based on ATR.

For long:

- Stop below stagnation zone low, recent swing low, or key broken resistance.

For short:

- Stop above stagnation zone high, recent swing high, or key broken support.

If entry immediately moves against the setup and invalidates momentum, cut quickly.

## Risk Management

Risk should be based on personal financial context, not only account percentage.

Conservative default for automation:

- Risk per trade: 1% to 3% of account.
- Max daily loss: 3% to 5%.
- Max monthly loss: user-defined amount that can be financially recovered without emotional damage.

If using a high-risk small account approach:

- Define a fixed monthly loss budget.
- Stop trading for the month when the budget is hit.
- Do not increase risk after a loss to recover.

## Instrument And Season Filters

Instrument preference from the transcripts:

- Better candidates: XAUUSD, EURJPY, GBPJPY, EURUSD, other instruments with trend and volatility.
- Caution: USDJPY, because the method was described as less compatible due to more ranges and smaller volatility.

Seasonal filter:

- Avoid most trades from around mid-December through early January.
- Resume when normal participation, direction, and clean structure return.

Directional bias filter:

- If a multi-month higher-timeframe trend is strongly bullish, prioritize longs and avoid casual shorts.
- If a multi-month higher-timeframe trend is strongly bearish, prioritize shorts and avoid casual longs.
- Counter-trend trades are not forbidden, but they should require a major structural break, not just a short-term neckline break.

## Method Evolution Principles

The method is not meant to be copied mechanically forever. The stable principles are:

1. Enter when volatility is small.
   - This helps keep stop distance and loss size small.
   - Stagnation is useful because volatility has contracted.

2. Enter where price can move one directionally.
   - Breakout, stagnation break, V-shape continuation, and second breakout are useful because they can become one-directional moves.
   - If the trade moves against the setup, cut quickly.
   - If it moves in the profit direction, let the move develop.

These two principles should guide parameter tuning and future variations.

## Suggested Parameters For Backtesting

These are starting values only.

- timeframe: 1H
- trend_lookback_bars: 80 to 240
- medium_trend_lookback_bars: about 480 to 720, roughly 1 month on 1H excluding weekends/market gaps
- short_trend_lookback_bars: 6 to 120, with latest several hours weighted heavily
- stagnation_min_bars: 7
- stagnation_max_atr_multiple: 1.0
- wide_stagnation_max_atr_multiple: 2.5
- momentum_lookback_bars: 6 to 24
- key_level_lookback_bars: 120 to 720
- range_min_days: 20
- range_min_touches_each_side: 2
- bonus_time_min_days: 14
- bonus_time_max_days: 21
- consolidation_exit_min_days: 2
- avoid_dates: around Dec 15 to Jan 10 by default
- excluded_or_low_priority_symbols: USDJPY until separate testing proves edge

## Automation Pseudocode

```text
for each new 1H candle:
    update swings
    update key support/resistance levels
    classify market_state:
        medium_direction = bullish / bearish / none
        short_direction = bullish / bearish / none
        short_mid_alignment = true / false
        trend_direction = bullish / bearish / none
        momentum_state = strong / weak / none
        range_state = true / false

    if no open position:
        if date is seasonal_avoid_period:
            skip
        if symbol is low_priority and not explicitly testing it:
            skip
        if not short_mid_alignment:
            skip
        if range_state and not second_breakout_setup:
            skip
        if momentum_state is weak:
            skip
        if price far from key level and setup requires key level:
            skip

        if bullish trend and bullish momentum:
            if simple_high_stagnation:
                enter long
            if resistance_near_stagnation:
                enter long
            if post_resistance_break_stagnation:
                enter long
            if sudden_reversal_plus_stagnation:
                enter long
            if bullish_v_shape_with_confirmation:
                enter long
            if bullish_v_shape_plus_high_stagnation:
                enter long
            if bullish_second_breakout_after_range:
                enter long

        if bearish trend and bearish momentum:
            mirror the above for shorts

    if open long:
        if price invalidates setup or hits stop:
            exit
        else if profitable:
            if latest_meaningful_pullback_low_breaks:
                exit
            else if days_since_entry > 21 and sharp_counter_move:
                exit
            else if consolidation_2_days_or_more and neckline_break_down:
                exit

    if open short:
        mirror long exit rules
```

## AI-Assisted Workflow

Full automation should be built in layers:

1. Rule-based scanner
   - Detect trend, momentum, key levels, stagnation, V-shape, range breakout.

2. AI visual reviewer
   - Review screenshots only for ambiguous setups.
   - Output: valid / invalid / unclear, with reasons.

3. Backtester
   - Run every candidate signal mechanically.
   - Track win rate, profit factor, max drawdown, average R, hold time.

4. Human review loop
   - Review false positives and false negatives.
   - Adjust definitions and thresholds.

## Forex Tester Implementation Notes

Best path:

- Start with a semi-automated indicator/scanner that marks candidate setups.
- Do not immediately make a full auto-trading EA.
- First verify whether the scanner finds the same setups that a human would identify.
- After validation, convert selected setups into an EA/strategy.

Minimum scanner outputs:

- Trend direction.
- Momentum state.
- Nearby key level.
- Stagnation zone.
- Setup type.
- Entry trigger candle.
- Suggested stop.
- Suggested exit monitoring level.

## Open Questions To Resolve During Testing

- How exactly should "important resistance/support" be ranked?
- What ATR multiple best defines tight stagnation per instrument?
- How many touches are required for a key level?
- What constitutes a "sharp counter-move" after bonus time?
- Should entries be made at candle close or intra-candle break?
- Which instruments match the method best: gold, USDJPY, GBPJPY, major FX pairs?
- What is the expected average holding period by setup type?

## Recommended First Backtest Scope

Start narrow:

- Instrument: XAUUSD first, then EURJPY and GBPJPY. Treat USDJPY as low priority until tested separately.
- Timeframe: 1H.
- Period: 2 to 5 years.
- Setups: short-mid alignment, simple stagnation, resistance/support stagnation, wide/irregular stagnation, second range breakout.
- Exits: one-swing break and consolidation neckline break.

Add V-shape only after the stagnation setups are measurable and stable.
