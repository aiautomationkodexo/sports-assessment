"""Tunable constants. Kept in one place so a reviewer can find every knob."""

ESPN_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
)

# Upstream requests must fail fast rather than hang a page load.
HTTP_TIMEOUT_SECONDS = 5.0

LEAGUE = "MLB"

# --- Mock odds tuning -------------------------------------------------------
# Bookmaker margin ("overround"). Both sides' implied probabilities are scaled
# to sum to this instead of 1.0.
VIG = 1.045

# Home-field advantage added to the log5 base probability.
HOME_FIELD_BUMP = 0.04

# Standard deviation of the gaussian "market noise". This is the dial that
# controls how often the market disagrees with the records -- i.e. how many
# games get flagged. Tuned in M3; see README.
NOISE_SD = 0.08

# Probabilities are clamped here so mock odds never reach absurd extremes.
PROB_FLOOR = 0.25
PROB_CEILING = 0.75
