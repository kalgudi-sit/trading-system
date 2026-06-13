# Trading System Architecture: Binance Futures (BTC/ETH) V2

**Status:** Foundation Design  
**Target:** Production-Grade Resilience  
**Scope:** Binance Futures (BTCUSDT, ETHUSDT, and similar)  
**Risk Model:** Hard cap at 0.7% notional loss per trade  

---

## Core Philosophy

**Signal generation and execution must NEVER be the same thing.**

This system enforces separation of concerns through 6 mandatory checkpoints:
1. **Signal Detection** (generate all opportunities)
2. **Signal Validation** (reject false breakouts)
3. **Breakout Strength** (quantify conviction)
4. **Risk Calculation** (protect capital)
5. **Dynamic Parameters** (assign TP/SL based on strength)
6. **Execution & Management** (open trade only after all checkpoints pass)

No trade executes until ALL checkpoints are satisfied.

---

## System Architecture: 6 Core Services

### Service 1: Signal Generator
**Purpose:** Identify ALL potential breakout opportunities  
**Responsibility:** Generate signals without filtering  
**Do NOT:** Validate, filter, or judge signals here  

#### Input
- OHLCV candles (1m, 5m, 15m, 1h, 4h timeframes)
- Previous candle states
- Trading pair (BTCUSDT, ETHUSDT, etc.)

#### Output
```json
{
  "signal_id": "sig_20250613_104530_BTCUSDT_1h",
  "timestamp": "2025-06-13T10:45:30Z",
  "pair": "BTCUSDT",
  "timeframe": "1h",
  "signal_type": "breakout_structure",
  "direction": "LONG",
  "breakout_price": 43520.50,
  "signal_confidence": 0.0,
  "notes": "Bullish break above swing high at 43450. No validation yet."
}
```

#### Signal Types (Must detect ALL)
1. **Structure Break** — Price breaks above swing high / below swing low
2. **EMA Crossover** — Fast EMA crosses above/below slow EMA
3. **Volatility Expansion** — ATR increases by >20% vs 20-candle average
4. **Momentum Divergence** — Price makes new high/low but RSI doesn't
5. **Trend Continuation** — Pullback to moving average, breaks continuation
6. **Volume Spike Initialization** — Volume >150% of 20-candle average (weak signal alone)

#### Guardrails
- ⚠️ Generate signals on MULTIPLE timeframes independently (1h, 4h, daily)
- ⚠️ Do NOT cascade timeframes (1h should not depend on 4h already having a signal)
- ⚠️ Mark signal timestamp (exact candle close time)
- ⚠️ Do NOT store historical signals; only current open opportunities
- ⚠️ Reset signal state on new candle close

---

### Service 2: Signal Validator (Volume-Based)
**Purpose:** Filter out false breakouts using volume conviction  
**Responsibility:** Reject signals that lack market participation  
**Output:** Validated vs rejected signals  

#### Input
- Signal from Service 1
- Current candle OHLCV
- Previous 20 candles (for averages)

#### Validation Logic

**Step A: Volume Expansion Check**
```
CurrentVolume / Avg(Volume_20candles) >= 1.5
```
- Breakouts WITHOUT volume are fake
- Minimum multiplier: 1.5x average volume
- **Fail Criterion:** Volume surge < 1.5x → REJECT signal

**Step B: Structure Confirmation**
```
For LONG breakout:
  - Close > SwingHigh
  - Close > Close[1] (higher high)
  - Range(current) > Range(average_20)
  
For SHORT breakout:
  - Close < SwingLow
  - Close < Close[1] (lower low)
  - Range(current) > Range(average_20)
```
- **Fail Criterion:** Structure not confirmed → REJECT signal

**Step C: Consecutive Candle Strength**
```
Count candles in breakout direction in last 3 candles.
Must have >= 2 candles in breakout direction.
```
- Single candle spikes are traps
- Multiple candles = real participation
- **Fail Criterion:** Only 1 candle in direction → REJECT signal

**Step D: Volatility Coherence**
```
Current ATR / Avg(ATR_20) >= 1.2
```
- Price move must be accompanied by volatility expansion
- Breakouts in low-volatility environments are unreliable
- **Fail Criterion:** ATR expansion < 1.2x → REJECT signal

#### Output
```json
{
  "signal_id": "sig_20250613_104530_BTCUSDT_1h",
  "validation_result": "VALID",
  "validation_confidence": 0.78,
  "checks": {
    "volume_expansion": {
      "pass": true,
      "current_volume": 45000,
      "avg_volume_20": 28000,
      "ratio": 1.607
    },
    "structure_confirmation": {
      "pass": true,
      "high_closed_above_swing": true,
      "range_expanded": true
    },
    "consecutive_strength": {
      "pass": true,
      "bullish_candles_in_last_3": 3
    },
    "volatility_coherence": {
      "pass": true,
      "atr_current": 185.5,
      "atr_avg_20": 142.0,
      "ratio": 1.308
    }
  },
  "rejection_reason": null
}
```

#### Guardrails
- ⚠️ ALL 4 checks must PASS for validation to proceed
- ⚠️ If ANY check fails → REJECT signal (no partial credit)
- ⚠️ Validation confidence = average of all check pass/fail
- ⚠️ Store validation timestamp for audit trail
- ⚠️ Log all REJECTED signals for analysis

---

### Service 3: Breakout Strength Scorer
**Purpose:** Quantify the conviction/power of the breakout  
**Responsibility:** Score 0-100 and assign grade  
**Output:** Strength score determines T/P and S/L ratios  

#### Input
- Validated signal from Service 2
- Historical structure (swing highs/lows over 5/10/20 candle periods)
- Volume profile
- Market regime (uptrend/downtrend/range)

#### Scoring Framework (0-100 Scale)

**Factor 1: Structure Significance (Weight: 40%)**
```
Local Swing Break (5 candles):     20 points
Weekly Swing Break (20 candles):   40 points
Monthly Swing Break (60 candles):  60 points
Resistance/Support Break (Daily):  50 points

Score = (points / 60) × 40
```

**Factor 2: Volume Conviction (Weight: 25%)**
```
Volume Ratio = CurrentVolume / Avg(Volume_20)

1.5x - 2.0x:   15 points (weak)
2.0x - 3.0x:   25 points (moderate)
3.0x - 5.0x:   35 points (strong)
>5.0x:         45 points (exceptional)

Score = (points / 45) × 25
```

**Factor 3: Momentum Strength (Weight: 20%)**
```
Price Distance from Entry to Breakout:
  - 0.5% move:    10 points (weak)
  - 0.5% - 1.0%:  15 points (moderate)
  - 1.0% - 2.0%:  20 points (strong)
  - >2.0%:        25 points (exceptional)

RSI Divergence Check:
  - No divergence: +5 points
  - Bullish divergence exists: +5 points
  
Score = ((move_points + divergence) / 30) × 20
```

**Factor 4: Candle Geometry (Weight: 15%)**
```
Body Size vs ATR:
  - Body / ATR < 0.3:      5 points (small)
  - Body / ATR 0.3 - 0.6:  10 points (medium)
  - Body / ATR 0.6 - 0.9:  15 points (strong)
  - Body / ATR > 0.9:      20 points (exceptional)

Wick Size (smaller is better):
  - Wick > 2x body:        -5 points (rejection)
  - Wick = body:           0 points
  - Wick < 0.5x body:      +3 points

Score = ((body_points + wick_adjustment) / 20) × 15
```

#### Strength Grade Assignment
```
0-25:    WEAK
26-50:   MODERATE
51-75:   STRONG
76-100:  EXCEPTIONAL
```

#### Output
```json
{
  "signal_id": "sig_20250613_104530_BTCUSDT_1h",
  "breakout_score": 72,
  "grade": "STRONG",
  "score_breakdown": {
    "structure_significance": {
      "weight": 0.40,
      "points": 40,
      "raw_score": 26.67
    },
    "volume_conviction": {
      "weight": 0.25,
      "points": 35,
      "raw_score": 19.44
    },
    "momentum_strength": {
      "weight": 0.20,
      "points": 22,
      "raw_score": 14.67
    },
    "candle_geometry": {
      "weight": 0.15,
      "points": 18,
      "raw_score": 13.50
    }
  }
}
```

#### Guardrails
- ⚠️ Score must be deterministic and reproducible
- ⚠️ Each factor must be clearly documented and auditable
- ⚠️ Grade assignment is final; no rounding bias
- ⚠️ WEAK signals should be rejected before Risk Engine (optional filter at scale)
- ⚠️ EXCEPTIONAL signals get priority attention in risk management

---

### Service 4: Risk Engine
**Purpose:** Calculate position size, stop loss distance, capital allocation  
**Responsibility:** Enforce hard capital constraints  
**Output:** Safe position size and stop loss placement  

#### Hard Constraints
```
Max Notional Loss per Trade: 0.7% of account
Risk/Reward Minimum: 1:1.0 (will be adjusted by breakout grade in Service 5)
Max Position Size: Limited by account size and stop distance
```

#### Input
- Account equity (USDT)
- Breakout grade from Service 3
- Entry price
- Proposed stop loss price (calculated based on structure)

#### Position Sizing Logic

**Step 1: Calculate Stop Distance**
```
For LONG:
  StopDistance = Entry - StopLoss (in absolute price)
  StopDistancePct = (Entry - StopLoss) / Entry × 100

For SHORT:
  StopDistance = StopLoss - Entry (in absolute price)
  StopDistancePct = (StopLoss - Entry) / Entry × 100
```

**Step 2: Calculate Maximum Position Size**
```
MaxNotionalRisk = AccountEquity × 0.007  (0.7% hard cap)

PositionSize = MaxNotionalRisk / (StopDistancePct / 100)

Example:
  Account: $10,000
  Entry: $43,500
  StopLoss: $43,200
  StopDistancePct = (300/43500) × 100 = 0.69%
  
  MaxNotionalRisk = $10,000 × 0.007 = $70
  PositionSize = $70 / 0.0069 = $10,144.93 USDT
  
  At $43,500/BTC, this = ~0.233 BTC
```

**Step 3: Apply Breakout Grade Modifier**
```
WEAK:        Position Size × 0.6  (extra conservative)
MODERATE:    Position Size × 0.8
STRONG:      Position Size × 1.0  (full size)
EXCEPTIONAL: Position Size × 1.0  (full size)
```

**Step 4: Enforce Leverage Limits**
```
Maximum Leverage: 5x (Binance default)
EffectiveLeverage = PositionSize / AccountEquity

If EffectiveLeverage > 5x:
  Reduce PositionSize to meet 5x limit
```

#### Output
```json
{
  "signal_id": "sig_20250613_104530_BTCUSDT_1h",
  "risk_engine_result": "APPROVED",
  "parameters": {
    "account_equity": 10000,
    "max_notional_loss_0_7_pct": 70,
    "entry_price": 43500,
    "stop_loss_price": 43200,
    "stop_distance_pct": 0.69,
    "base_position_size_usdt": 10144.93,
    "grade_modifier": 1.0,
    "adjusted_position_size_usdt": 10144.93,
    "adjusted_position_size_btc": 0.233,
    "effective_leverage": 1.014,
    "leverage_check": "PASS"
  },
  "risk_approval": {
    "notional_risk_amount": 70,
    "notional_risk_pct": 0.7,
    "acceptable": true
  }
}
```

#### Guardrails
- ⚠️ Hard stop at 0.7% account risk; NO exceptions
- ⚠️ Stop loss MUST be placed below/above structure (not arbitrary)
- ⚠️ Position size = Risk / StopDistance (always this formula)
- ⚠️ Leverage never exceeds 5x without explicit override
- ⚠️ Reject trade if stop loss distance > 3% (too risky setup)
- ⚠️ Log all rejected trades with reason for audit

---

### Service 5: Dynamic Parameters Engine
**Purpose:** Calculate take profit levels based on breakout strength  
**Responsibility:** Assign R:R ratios dynamically  
**Output:** Target exit prices  

#### Input
- Breakout grade from Service 3
- Entry price
- Stop loss price (from Service 4)
- Breakout direction (LONG/SHORT)

#### R:R Ratio Mapping (Core Strategy Decision)
```
WEAK breakout:
  RR Ratio = 1.0
  Risk = StopDistance
  Target = Entry + (StopDistance × 1.0)

MODERATE breakout:
  RR Ratio = 1.5
  Risk = StopDistance
  Target = Entry + (StopDistance × 1.5)

STRONG breakout:
  RR Ratio = 2.0
  Risk = StopDistance
  Target = Entry + (StopDistance × 2.0)

EXCEPTIONAL breakout:
  RR Ratio = 2.5 to 3.0
  Risk = StopDistance
  Target = Entry + (StopDistance × 2.5 to 3.0)
```

#### Multi-Level Take Profit Strategy (Optional but Recommended)
```
For STRONG and EXCEPTIONAL breakouts, implement scaling:

Level 1 (Partial TP): 0.5R
  - Close 50% of position
  - Move stop to breakeven
  - Let 50% run to target

Level 2 (Full TP): 2.0R
  - Close remaining position
  
Example (STRONG breakout, LONG):
  Entry: $43,500
  Stop: $43,200 (Risk = $300)
  
  Level 1: $43,500 + ($300 × 0.5) = $43,650  → Close 50%
  Level 2: $43,500 + ($300 × 2.0) = $44,100  → Close 50%
```

#### Calculation Example
```
Entry: $43,500
Stop: $43,200
StopDistance: $300

STRONG breakout (RR = 2.0):
  TakeProfit = $43,500 + ($300 × 2.0) = $44,100
  Risk/Reward = 2.0
```

#### Output
```json
{
  "signal_id": "sig_20250613_104530_BTCUSDT_1h",
  "dynamic_parameters": {
    "entry_price": 43500,
    "stop_loss_price": 43200,
    "stop_distance": 300,
    "breakout_grade": "STRONG",
    "rr_ratio": 2.0,
    "take_profit_single_level": 44100,
    "take_profit_scaled": [
      {
        "level": 1,
        "price": 43650,
        "rr": 0.5,
        "action": "CLOSE 50%"
      },
      {
        "level": 2,
        "price": 44100,
        "rr": 2.0,
        "action": "CLOSE 50%"
      }
    ]
  }
}
```

#### Guardrails
- ⚠️ RR ratio MUST scale with breakout grade
- ⚠️ Minimum RR = 1.0 (never enter below 1:1)
- ⚠️ WEAK breakouts should consider skipping (low edge)
- ⚠️ Take profit placement must be at round numbers where possible (psychological levels)
- ⚠️ For EXCEPTIONAL breakouts, allow trailing stop after 1.0R
- ⚠️ Multi-level TP improves capital efficiency and risk management

---

### Service 6: Execution Engine & Trade Manager
**Purpose:** Open positions only after ALL checkpoints pass  
**Responsibility:** Execute trades and manage open positions  
**Output:** Trade logs, live position tracking  

#### Pre-Execution Checklist
```
BEFORE executing ANY trade, verify:

☑ Signal detected (Service 1) ✓
☑ Signal validated (Service 2) ✓
☑ Breakout strength scored (Service 3) ✓
☑ Risk engine approved (Service 4) ✓
☑ Dynamic parameters calculated (Service 5) ✓
☑ No other position open on this pair (avoid overlap)
☑ Account margin sufficient for position size
☑ Order placement will NOT exceed max daily risk
```

#### Trade Execution
```json
{
  "trade_id": "trade_20250613_104530_BTCUSDT_1h_001",
  "timestamp": "2025-06-13T10:45:30Z",
  "pair": "BTCUSDT",
  "timeframe": "1h",
  "direction": "LONG",
  "entry_price": 43500,
  "position_size_usdt": 10144.93,
  "position_size_contracts": 0.233,
  "stop_loss": 43200,
  "take_profit_primary": 44100,
  "take_profit_scaled": [43650, 44100],
  "rr_ratio": 2.0,
  "notional_risk": 70,
  "notional_risk_pct": 0.7,
  "breakout_grade": "STRONG",
  "status": "OPEN"
}
```

#### Trade Management Rules (Active Management)

**Rule 1: Move Stop to Breakeven**
```
When position reaches +0.5R:
  - Move stop loss to entry price
  - Lock in no loss
  - Continue to target
```

**Rule 2: Partial Take Profit**
```
At Level 1 (0.5R):
  - Close 50% of position
  - Move stop to breakeven on remaining 50%
  - Let remaining 50% run to full target
```

**Rule 3: Trailing Stop (EXCEPTIONAL only)**
```
If breakout grade = EXCEPTIONAL AND position > +1.5R:
  - Trail stop at 0.5R distance from current price
  - Allows capturing larger moves
  - Max trail = 0.5R below current price
```

**Rule 4: Exit Conditions**
```
IMMEDIATE EXIT if:
  - Close crosses stop loss
  - Close reaches take profit target
  - 4 consecutive candles against position (reversal signal)
  - Breakout grade confirmed as INVALID (reversal structure)
```

**Rule 5: Time-Based Exit (Optional)**
```
If position is:
  - WEAK breakout: Exit if no movement to 1.0R after 3x candle periods
  - MODERATE: Exit if no movement to 1.5R after 5x candle periods
  - STRONG: No time limit (trend may take time)
  - EXCEPTIONAL: No time limit
```

#### Trade Log Output
```json
{
  "trade_id": "trade_20250613_104530_BTCUSDT_1h_001",
  "entry_time": "2025-06-13T10:45:30Z",
  "exit_time": "2025-06-13T11:23:15Z",
  "exit_reason": "TAKE_PROFIT_LEVEL_2",
  "direction": "LONG",
  "entry_price": 43500,
  "exit_price": 44100,
  "pnl": 600,
  "pnl_pct": 0.6,
  "notional_risk": 70,
  "rr_achieved": 2.0,
  "breakout_grade": "STRONG",
  "status": "CLOSED"
}
```

#### Guardrails
- ⚠️ NO trade executes without all 6 service checkpoints passing
- ⚠️ Position size is FIXED at entry; no averaging up/down
- ⚠️ Stop loss is SACRED; moving it wider is forbidden
- ⚠️ Take profit levels are NOT targets to avoid; they are mandatory exit points
- ⚠️ All trade decisions logged with timestamp and reason code
- ⚠️ Daily risk tracking: cumulative losses must not exceed account daily max

---

## System Workflow: Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ INCOMING CANDLE CLOSE (1h, 4h, or daily)                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ SERVICE 1: SIGNAL GENERATOR                                     │
│ Generate all potential breakout signals (no filtering)          │
│ Output: 0 to 10 signals                                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ FOR EACH SIGNAL:                                                 │
│                                                                  │
│ SERVICE 2: SIGNAL VALIDATOR                                     │
│ ├─ Check volume expansion (>1.5x)                               │
│ ├─ Check structure confirmation                                 │
│ ├─ Check consecutive candle strength (≥2 in direction)          │
│ └─ Check volatility coherence (ATR >1.2x)                       │
│                                                                  │
│ IF ANY CHECK FAILS → REJECT & CONTINUE                          │
│ IF ALL PASS → Continue to Service 3                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ SERVICE 3: BREAKOUT STRENGTH SCORER                             │
│ Score 0-100 based on:                                           │
│ ├─ Structure significance (40%)                                 │
│ ├─ Volume conviction (25%)                                      │
│ ├─ Momentum strength (20%)                                      │
│ └─ Candle geometry (15%)                                        │
│                                                                  │
│ Assign grade: WEAK / MODERATE / STRONG / EXCEPTIONAL            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ SERVICE 4: RISK ENGINE                                          │
│ ├─ Calculate stop loss distance                                 │
│ ├─ Calculate position size (risk / stop distance)               │
│ ├─ Apply grade modifier                                         │
│ ├─ Verify 0.7% hard cap                                         │
│ └─ Verify leverage limit (5x max)                               │
│                                                                  │
│ IF RISK CHECK FAILS → REJECT & CONTINUE                         │
│ IF APPROVED → Continue to Service 5                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ SERVICE 5: DYNAMIC PARAMETERS ENGINE                            │
│ ├─ Map breakout grade to R:R ratio                              │
│ ├─ Calculate take profit price                                  │
│ ├─ (Optional) Calculate multi-level TP                          │
│ └─ Finalize all trade parameters                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ SERVICE 6: EXECUTION ENGINE                                     │
│ ├─ Final pre-execution checklist                                │
│ ├─ Place ENTRY order at breakout price                          │
│ ├─ Place STOP LOSS order                                        │
│ ├─ Place TAKE PROFIT order(s)                                   │
│ └─ Log trade to trade journal                                   │
│                                                                  │
│ TRADE NOW ACTIVE & MANAGED                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ LIVE TRADE MANAGEMENT (Service 6 continuous)                    │
│ ├─ Monitor position P&L                                         │
│ ├─ Execute scaling rules (move SL to BE, partial TP)            │
│ ├─ Monitor exit conditions                                      │
│ ├─ Close at TP / SL / exit signal                               │
│ └─ Log closure to trade journal                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Checkpoint Decision Matrix

| Checkpoint | Pass → | Fail → | Why |
|---|---|---|---|
| Signal Detection | Continue to Validation | Skip this signal | No signal = no opportunity |
| Volume/Structure Validation | Continue to Strength | Reject signal | Volume is proof of conviction |
| Breakout Strength Score | Continue to Risk | (Optional) Reject if WEAK | Low conviction = low edge |
| Risk Engine Approval | Continue to Parameters | Reject trade | Hard cap protects capital |
| Dynamic Parameters | Continue to Execution | Reject trade | Stop distance determines position size |
| Execution Checklist | EXECUTE | Reject trade | Final gate before real money |

---

## Key Design Principles (Non-Negotiable)

### 1. Separation of Concerns
- Signal Generation ≠ Signal Validation
- Validation ≠ Risk Management
- Risk Management ≠ Execution
- Each service has ONE job

### 2. Layered Filtering
- Service 1: Generate all signals (permissive)
- Service 2: Filter for volume conviction (strict)
- Service 3: Filter for strength (moderate)
- Service 4: Filter for capital safety (strict)
- Service 5: NOT a filter (deterministic calculation)
- Service 6: NOT a filter (execution only)

### 3. Deterministic & Auditable
- Every decision has explicit rules
- Every rule is testable
- Every trade decision is logged with reason code
- No magic, no black boxes

### 4. Capital Preservation First
- Hard cap at 0.7% per trade (NEVER exceeded)
- Position size derived from risk, not from conviction
- Strong breakout ≠ larger position (same risk, different RR)
- Weak breakout = pass or reduced size

### 5. Market Regime Awareness (Future Enhancement)
- When market is choppy (low conviction) → reduce position sizes or skip entirely
- When market is trending (high conviction) → normal position sizes
- When market is in transition → caution (may add later)

---

## Out-of-Scope for V1 (Future Enhancements)

- [ ] Market regime detection service
- [ ] Correlation analysis (BTC vs ETH moves)
- [ ] Time-of-day filters (Asian/European/US session bias)
- [ ] News/macro event awareness
- [ ] Advanced ML-based strength scoring
- [ ] Portfolio-level position sizing (multiple pairs simultaneously)
- [ ] Advanced hedging strategies

---

## Expected Deliverables (By Phase)

### Phase 1: Architecture & Framework ✓ (You are here)
- [x] System architecture defined
- [x] 6 services specified
- [x] Checkpoints and guardrails documented
- [x] Decision matrix created

### Phase 2: Signal Generation & Validation
- [ ] Signal Generator implemented (Python)
- [ ] Signal Validator implemented (Python)
- [ ] Backtester framework (walk-forward)
- [ ] First backtest run on 6 months data

### Phase 3: Scoring & Risk
- [ ] Breakout Strength Scorer
- [ ] Risk Engine
- [ ] Dynamic Parameters Engine
- [ ] Full system integration

### Phase 4: Execution & Management
- [ ] Trade Execution Service
- [ ] Trade Management Service
- [ ] Live order placement integration (Binance API)
- [ ] Trade journal logging

### Phase 5: Analytics & Optimization
- [ ] Strategy Analytics Service
- [ ] Per-grade performance reporting
- [ ] Parameter tuning framework
- [ ] A/B testing capability

---

## Audit Trail & Logging Requirements

Every trade must log:
```
trade_id, timestamp, pair, timeframe, signal_type, 
signal_confidence, validation_result, breakout_score, breakout_grade,
entry_price, stop_loss, take_profit, position_size, notional_risk,
rr_ratio, entry_time, exit_time, exit_reason, exit_price, 
pnl, pnl_pct, status
```

Every rejected signal must log:
```
signal_id, timestamp, pair, timeframe, signal_type,
rejection_checkpoint (1-6), rejection_reason, 
volume_ratio, structure_confirmation, atr_ratio, etc.
```

---

## Summary

This system is designed to:

✅ Generate many signals (permissive)  
✅ Validate only real opportunities (strict)  
✅ Quantify conviction (deterministic)  
✅ Protect capital (hard constraints)  
✅ Execute only high-conviction setups  
✅ Learn what actually works (analytics)  

**Core Promise:** No trade executes until ALL checkpoints pass. This is non-negotiable.

---

**Next Step:** Once you approve this framework, we move to Pine Script translation and Python backtester implementation.
