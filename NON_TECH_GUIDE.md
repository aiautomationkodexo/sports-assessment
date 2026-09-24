# How This Tool Works — A Guide for Everyone

*No technical background needed. Every term is explained before it's used, and every number in this guide is a real one taken from the working tool.*

---

## The one-sentence version

**The tool compares two opinions about tonight's baseball games — what the season records say, and what the betting prices say — and highlights the games where those two opinions disagree.**

Everything else in this guide explains how it gets there.

---

## Part 1: The idea, before any numbers

There are two completely separate ways to guess who'll win a baseball game.

**The first is the season record.** If a team has won 84 games and lost 74, they're clearly decent. If their opponent has won 57 and lost 101, they're clearly not. Counting wins is simple and factual.

**The second is the betting price.** Bookmakers set prices based on who they think will win. Their prices reflect everything they know — injuries, who's pitching tonight, recent form, money coming in from bettors.

Usually these two agree. Good teams have good records *and* get favorable prices. Nothing surprising.

**But sometimes they point in opposite directions.** The team with the far better season is priced as the *less* likely winner. That's strange, and that's what the tool hunts for.

When it finds one, it marks the game **⚠ Favorite Undervalued** — meaning "the team that should be the favorite is being treated as the underdog."

---

## Part 2: Understanding betting prices

This is the only genuinely unfamiliar concept. Once it clicks, the rest is easy.

### What the numbers mean

American betting prices look like this:

> Colorado Rockies **−125**
> Arizona Diamondbacks **+105**

The sign matters more than the number:

| | Meaning | How to read it |
|---|---|---|
| **Minus (−)** | This team is the **favorite** | **−125** = risk $125 to win $100 |
| **Plus (+)** | This team is the **underdog** | **+105** = risk $100 to win $105 |

The logic: you must risk *more* to back a likely winner, and you're rewarded *more* for backing an unlikely one. That's it.

### The hidden second meaning

Here's the key insight the whole tool rests on.

**A betting price is a prediction in disguise.** Bookmakers don't pick numbers randomly — they price games according to how likely each outcome is. So you can work *backwards* from the price to uncover what the bookmaker actually believes.

The arithmetic:

> **For a minus price (favorite):** drop the sign, then divide by itself-plus-100
> **−125** → 125 ÷ (125 + 100) → 125 ÷ 225 → **55.6%**
>
> **For a plus price (underdog):** divide 100 by itself-plus-100
> **+105** → 100 ÷ (105 + 100) → 100 ÷ 205 → **48.8%**

So "Colorado −125" really means: *"I think Colorado wins about 56 times out of 100."*

That extracted percentage has a name: **implied probability**. "Implied" because nobody states it openly — it's buried inside the price, and you have to do the division to reveal it.

**This conversion is what makes the whole comparison possible.** You can't compare a win-loss record to a betting price directly — they're different kinds of thing. But once both are percentages, comparing them is trivial.

---

## Part 3: Working through a real flagged game

Here is an actual game the tool flagged, with every step shown.

### The two teams

| | Arizona Diamondbacks | Colorado Rockies |
|---|---|---|
| **Record** | 84 wins, 74 losses | 57 wins, 101 losses |

### Step 1 — Who's better on paper?

Divide wins by total games played:

> **Arizona:** 84 ÷ (84 + 74) = 84 ÷ 158 = **53.2%**
> **Colorado:** 57 ÷ (57 + 101) = 57 ÷ 158 = **36.1%**

**Arizona is better**, and it isn't close. They've won 27 more games. Colorado is one of the weakest teams in the league.

### Step 2 — Who does the market favor?

The prices for this game were **Arizona +105** and **Colorado −125**. Converting both:

> **Arizona +105** → 100 ÷ 205 = **48.8%**
> **Colorado −125** → 125 ÷ 225 = **55.6%**

**The market favors Colorado.** It gives Arizona *less* than a coin flip.

### Step 3 — Do the two opinions agree?

| | Says the better team is… |
|---|---|
| The records | **Arizona** (53.2% vs 36.1%) |
| The betting prices | **Colorado** (55.6% vs 48.8%) |

**They point at different teams.** The far better team is priced as the underdog.

### ⚠ Flagged

The tool highlights this row and explains itself in plain English:

> *"ARI has the better record (84-74) but the market gives them 49% vs COL's 56%."*

---

## Part 4: A game that does *not* get flagged

To see the contrast, here's a game from the same evening that stayed unmarked.

| | Milwaukee Brewers | Philadelphia Phillies |
|---|---|---|
| **Record** | 99-59 → **62.7%** | 87-71 → **55.1%** |
| **Price** | −145 | +120 |
| **Implied chance** | **59.2%** | 45.5% |

- The records say **Milwaukee** is better.
- The prices say **Milwaukee** is more likely to win.

**Both point at the same team.** They agree, so there's nothing unusual here. **No flag.**

---

## Part 5: The surprising part — size doesn't matter

This is the bit that confuses most people, so it's worth pausing on.

On one evening's games, here's what happened:

| Game | Better team | Market favors | Agree? | Flagged |
|---|---|---|---|---|
| LAA @ SEA | Seattle | Seattle (**73.3%**) | Yes | — |
| MIL @ PHI | Milwaukee | Milwaukee (59.2%) | Yes | — |
| CIN @ ATL | Atlanta | Atlanta (65.5%) | Yes | — |
| **ARI @ COL** | **Arizona** | **Colorado (55.6%)** | **No** | **⚠ FLAG** |

Look at **LAA @ SEA**: the market is *enormously* confident, giving Seattle a 73.3% chance. That's a lopsided, dramatic price. **No flag** — because the better team is the favorite. They agree.

Now look at **ARI @ COL**: the prices are almost even, 55.6% versus 48.8%. A much *smaller* gap. **Flagged** — because the two opinions point at different teams.

> **The tool doesn't care how big the gap is. It cares whether the two sources disagree.**

A huge gap where everyone agrees is boring. A tiny gap where they disagree is interesting.

---

## Part 6: The number that looks like a mistake

Add the two implied percentages from the flagged game:

> Arizona 48.8% + Colorado 55.6% = **104.3%**

More than 100%. Two teams, one game, and their chances sum to over certainty. That can't be right — except it is.

**That extra 4.3% is the bookmaker's profit margin.** The industry calls it the *vig* (short for "vigorish") or the *juice*. Bookmakers shade both prices slightly in their own favor so they earn a small cut regardless of who wins. Every real sportsbook does this. It's how they stay in business.

### Why the tool ignores it

You might expect the tool to strip this margin out before comparing. It deliberately doesn't, and the reason is elegant:

**The margin inflates both teams' numbers by roughly the same amount.** If you carefully removed it:

> 48.8% and 55.6% → become about 46.8% and 53.2%

Arizona is *still* the lower number. Both values shifted, but **which one is larger never changed** — and "which one is larger" is the only question the tool asks.

So removing the margin would mean extra work that cannot possibly change a single answer. Leaving it in has a bonus: the percentages shown on screen are the real ones a sportsbook would actually post, not adjusted figures that exist nowhere in the real world.

---

## Part 7: When the question doesn't make sense

Sometimes "do the two opinions disagree?" is simply the wrong question. The tool handles four such cases deliberately.

| Situation | What the tool shows | Why |
|---|---|---|
| **Both teams have identical records** | no flag | There is no "better team," so nobody can be undervalued. The question is meaningless. |
| **Both teams have identical prices** | no flag | The market hasn't favored anyone, so it can't be disagreeing with anyone. |
| **A record or the prices are missing** | **"N/A"** | We *could not check*. |
| **A team has played zero games** | **"N/A"** | You cannot compute a win rate from zero games — it would mean dividing by zero. |

### Why "N/A" matters so much

The third row deserves special attention, because it's a genuine design decision rather than an obvious one.

A careless version of this tool would show "no flag" when data is missing. That would quietly tell you *"this game is fine"* — when the truth is **nobody ever looked at it.**

Those are completely different statements, and blurring them is how a tool starts lying to the people who trust it. So the tool shows a distinct grey **"N/A"** badge instead. A gap in the data can never masquerade as a clean result.

This distinction is important enough that there's an automated check whose entire purpose is to make sure a future change never accidentally merges the two.

---

## Part 8: What's real and what's invented

Complete honesty about this, because it's the question every reviewer asks first.

| What you see on screen | Where it comes from | Real? |
|---|---|---|
| The games and which teams are playing | ESPN | ✅ **Real** |
| Team win-loss records (84-74, etc.) | ESPN | ✅ **Real** |
| Start times | ESPN | ✅ **Real** |
| **The betting prices (+105, −125)** | **Generated by this tool** | ⚠️ **Invented** |
| The implied percentages | Calculated from the invented prices | ⚠️ Based on invented data |
| The ⚠ flag itself | Real records + invented prices | The *logic* is real |

So a flagged row is **half real and half invented**: real teams with real records, but made-up prices.

### Why the prices are invented

**Real betting odds cost money.** Providers require paid accounts. The assignment explicitly permitted using made-up odds, since the point is to demonstrate that the *comparison logic* works correctly.

**There's also a practical reason specific to this data source.** ESPN's own response does sometimes include real betting odds from DraftKings — but only for games happening *today*. Checked across four other dates, every single one returned nothing. A version using ESPN's real odds would work for exactly one day and show blank columns for every other date, making the date picker useless.

The invented prices keep the tool working for any date you choose. And the tool is deliberately built so that a paid odds service could be connected later **without changing how the flag works at all.**

### How the invented prices are made

They're not random — random prices would look obviously fake and would never produce meaningful flags. Instead, for each game the tool:

1. **Starts from the two records.** A much better team starts out much more likely to win.
2. **Adds a small home-field boost.** Home teams do genuinely win slightly more often.
3. **Adds a random wobble.** This is the crucial ingredient. Real markets don't perfectly track season records — they know about tonight's pitcher, injuries, and so on. The wobble simulates that. **Without it, the prices would always agree with the records and nothing would ever be flagged**, making the tool pointless.
4. **Adds the bookmaker's margin**, so the numbers behave like a real sportsbook's.
5. **Converts the result into a price** like −125.

The wobble is calculated from the date and the game's ID rather than being truly random. This means **the same game on the same date always produces exactly the same price.** Reload the page as many times as you like — nothing shifts. Useful for demonstrations, and it means the tool can be tested reliably.

The result is prices that mostly agree with the records (as a real market would) but occasionally don't — which is exactly the situation the tool exists to catch. On a typical evening, around 2 to 4 games out of a dozen get flagged.

---

## Part 9: How a page load actually works

Six steps, from clicking a date to seeing highlighted rows:

```
1. FETCH      Ask ESPN for the games on the chosen date
                 → gets teams, records, start times (real)

2. TIDY UP    Convert ESPN's messy response into a clean list
                 → if one game is malformed, skip just that one

3. PRICE      Invent a betting price for each game
                 → labeled "mock" so nobody mistakes it for real

4. CONVERT    Turn every price into an implied percentage
                 → −125 becomes 55.6%

5. COMPARE    For each game, ask: does the better team have
              the lower implied chance?
                 → yes = flag, no = leave alone

6. DISPLAY    Draw the table, highlight flagged rows in amber
```

**Step 5 is the entire product.** Steps 1 through 4 exist only to make step 5 possible, and step 6 exists to show you the result.

### Why it's built in separate stages

Each stage does one job and hands a clean result to the next. This matters for a reason that isn't obvious:

**The comparison logic never touches ESPN's raw data.** By the time step 5 runs, it's working with tidy, verified numbers. This means the most important part of the tool can be checked thoroughly with simple made-up examples — no internet needed — and a change to ESPN's format can never break it.

It's also why swapping the invented prices for real ones later is straightforward: only step 3 would change. Steps 5 and 6 wouldn't know the difference.

---

## Part 10: When things go wrong

A tool that crashes or shows a blank page is worse than useless. Every failure produces a clear message instead:

| What goes wrong | What you see |
|---|---|
| ESPN is unreachable or down | *"Couldn't reach the sports data provider. Try again."* |
| You pick a date with no baseball | *"No games scheduled for this date."* |
| You enter an invalid date | *"Invalid date. Use YYYY-MM-DD."* |
| The data is still loading | *"Loading games…"* |
| **One single game has broken data** | **That one game is skipped — every other game still appears** |

That last row is a deliberate choice worth calling out. A single corrupted game does **not** take down the whole page. It's quietly dropped, the problem is recorded, and you still see the other fifteen games. One bad row never costs you the evening's slate.

---

## Part 11: What this tool is not

Being clear about the limits is as important as explaining the features.

**It is not betting advice.** A flag means *"this game looks unusual, someone should look closer."* It does not mean "place this bet." The tool has no opinion about what you should do.

**A flag doesn't mean the bookmaker is wrong.** When the market disagrees with the records, there are usually two possible explanations, and the tool cannot tell them apart:

1. **The market knows something the record can't see.** Maybe the better team's ace pitcher is resting tonight. Maybe their best hitter is injured. A season record is a summary of the past — it knows nothing about tonight's lineup.
2. **The price is genuinely mispriced**, and there's an opportunity.

Distinguishing these requires a human who knows baseball. The tool just narrows a dozen games down to the two or three worth that attention.

**Win percentage is a crude measure of quality.** This is the tool's biggest simplification. A season record ignores:

- **Who's pitching tonight** — in baseball this is enormous. The same team is a very different proposition with its best starter versus its fifth.
- **Injuries and rest** — a team missing three regulars still carries its full-season record.
- **Recent form** — a team that won 30 straight in April and has lost 20 straight since looks identical on paper to a steady one.
- **Strength of schedule** — 85 wins against weak opponents isn't the same as 85 against strong ones.

**And in this prototype, the prices are invented.** So today's flags demonstrate that the logic works correctly. They are not real market signals.

---

## Part 12: What would come next

Natural improvements, roughly in order of value:

1. **Real betting odds** from a paid provider — the single biggest upgrade, and the tool is already built to accept them without changing anything else.
2. **Smarter team ratings** — measures that account for *how* teams win, not just how often. A team that wins many close games and loses badly is usually weaker than its record suggests.
3. **More sports** — American football and college football would be natural additions. College football is particularly interesting because it has genuine official rankings, so there'd be no need to use win percentage as a stand-in.
4. **A track record** — save every flag and check afterwards how those games actually turned out. This is the one that would turn the tool from a highlighter into something with evidence behind it. Right now it can tell you a game is unusual; it can't yet tell you whether unusual games are worth acting on.

---

## Glossary

| Term | Plain meaning |
|---|---|
| **Moneyline** | A bet on who simply wins the game |
| **Favorite** | The team expected to win — shown with a minus price |
| **Underdog** | The team expected to lose — shown with a plus price |
| **Implied probability** | The win chance hidden inside a betting price |
| **Vig / juice** | The bookmaker's built-in profit margin |
| **Win percentage** | Wins divided by total games played |
| **Pick'em** | A game where both teams have the same price — the market has no opinion |
| **Mock data** | Made-up data used for demonstration |
| **API** | A way for one program to request data from another — here, how the tool asks ESPN for games |
| **Favorite Undervalued** | This tool's flag: the better team is priced as the underdog |

---

*Games and records are live from ESPN. Betting prices are invented for demonstration and labeled as such throughout. This is not betting advice.*
