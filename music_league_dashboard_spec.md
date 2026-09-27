# Music League Dashboard — Build Specification

## Project Goal
Build a mobile-friendly, shareable Music League analytics dashboard that can be hosted for free and shared via Facebook Messenger.

The dashboard should ingest exported Music League data, enrich song submissions with external music metadata, calculate player/song/social metrics, and present the results in a playful, highly shareable interface.

The visual direction should combine:
- modern music analytics
- sports-style leaderboards
- FIFA/FUT-inspired collectible player cards
- mobile-first layouts suitable for opening from Messenger

The first deployment target is **Streamlit Community Cloud**.

---

# 1. Recommended Tech Stack

Use:
- Python 3.11+
- Streamlit
- pandas or polars
- DuckDB or Parquet for processed data
- Plotly for charts
- requests/httpx for API calls
- python-dotenv for local secrets

External enrichment sources:
- Spotify Web API where available
- MusicBrainz for canonical release/artist metadata
- Last.fm for genre/tag enrichment

Design the enrichment layer so Spotify-specific fields can be replaced later if an API field disappears.

---

# 2. Repository Structure

Create the project with this structure:

```text
music-league-dashboard/
│
├── app.py
├── pages/
│   ├── 1_Players.py
│   ├── 2_Songs_and_Records.py
│   ├── 3_Relationships.py
│   └── 4_Taste.py
│
├── src/
│   ├── config.py
│   ├── ingest.py
│   ├── clean.py
│   ├── enrich.py
│   ├── spotify_client.py
│   ├── musicbrainz_client.py
│   ├── lastfm_client.py
│   ├── metrics.py
│   ├── player_cards.py
│   ├── narrative.py
│   └── utils.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── cache/
│
├── assets/
│   ├── players/
│   ├── logos/
│   └── card_backgrounds/
│
├── tests/
│   ├── test_ingest.py
│   ├── test_metrics.py
│   └── test_player_cards.py
│
├── .streamlit/
│   └── config.toml
│
├── .env.example
├── requirements.txt
├── README.md
└── player_assets.json
```

---

# 3. Observed Music League Export Schema and Core Data Model

The supplied Music League export is already split into four CSV files. Build the parser against these exact schemas, while keeping column-mapping code isolated so future export changes are easy to handle.

## Raw files observed

### `competitors.csv`
- `ID` — stable competitor/player ID
- `Name` — Music League display name

### `rounds.csv`
- `ID` — stable round ID
- `Created` — UTC timestamp for round creation
- `Name`
- `Description`
- `Playlist URL` — Spotify playlist URL

### `submissions.csv`
- `Spotify URI` — exact Spotify track URI, e.g. `spotify:track:<track_id>`
- `Title`
- `Album`
- `Artist(s)` — display string; can contain multiple artists
- `Submitter ID` — joins to `competitors.ID`
- `Created` — UTC submission timestamp
- `Comment` — optional submitter note; may be blank/whitespace
- `Round ID` — joins to `rounds.ID`
- `Visible To Voters` — observed as `Yes`; normalize to boolean

### `votes.csv`
- `Spotify URI`
- `Voter ID` — joins to `competitors.ID`
- `Created` — UTC vote timestamp
- `Points Assigned` — signed integer; observed values include negative points, zero, and positive points
- `Comment` — optional voter comment
- `Round ID`

Important observed behavior:
- votes can be negative (observed down to at least `-4`)
- explicit zero-point vote rows can exist
- missing vote rows represent no explicit vote allocation and should be treated as zero only when constructing dense relationship/voting matrices
- there are no self-votes in the supplied data
- the export contains no standings table; scores and ranks must be derived
- each round currently has one submission per participating player
- not every competitor participates in every round
- `Spotify URI` means Spotify enrichment can normally use the exact track ID directly; fuzzy title/artist search should be a fallback only

## Normalized tables

### players
- `player_id` <- `competitors.ID`
- `player_name` <- `competitors.Name`
- `image_path`
- `active_flag` — derive from whether the player appears in any round/submission/vote

### rounds
- `round_id` <- `rounds.ID`
- `round_name` <- `rounds.Name`
- `round_description` <- `rounds.Description`
- `round_created_at` <- parsed UTC `rounds.Created`
- `playlist_url` <- `rounds.Playlist URL`
- `round_number` — derive from chronological `round_created_at` when no explicit ordering field exists
- `participant_count` — distinct submitters in the round

Do not treat `round_created_at` as the date the round was played/closed; it is only the timestamp supplied by the export.

### submissions
One row per player submission per round.

Use a deterministic composite `submission_id`, for example a hash of `round_id + Spotify URI`. Do not use Spotify URI alone because the same track may be submitted again in a later round.

- `submission_id`
- `round_id`
- `player_id` <- `Submitter ID`
- `spotify_uri`
- `spotify_track_id` — parse from `spotify:track:<id>`
- `track_name` <- `Title`
- `artist_display` <- `Artist(s)`
- `album_name` <- `Album`
- `submitted_at` <- parsed UTC `Created`
- `submission_comment` <- trimmed `Comment`; blank/whitespace becomes null
- `visible_to_voters` <- normalized boolean
- `total_points` — derive as the signed sum of all vote rows for the submission
- `round_rank` — derive within each round from `total_points`

Use a documented tie policy for ranks. Default to competition ranking (`1, 2, 2, 4`) and expose ties clearly in the UI.

### votes
One row per explicit vote allocation.

- `round_id`
- `submission_id` — join on `round_id + Spotify URI`
- `voter_player_id` <- `Voter ID`
- `submitted_by_player_id` — join from submissions
- `voted_at` <- parsed UTC `Created`
- `points` <- signed integer `Points Assigned`
- `vote_comment` <- trimmed `Comment`; blank/whitespace becomes null

A row with `points == 0` is still an explicit interaction and counts as engagement. A missing row is a non-vote, not an explicit zero vote.

### comments
Normalize both comment sources into one table with a type field.

- `comment_id` — deterministic hash
- `round_id`
- `submission_id`
- `commenter_player_id`
- `comment_type` — `submission_note` or `vote_comment`
- `comment_text`
- `comment_word_count`
- `comment_char_count`
- `created_at`

For social/player writing metrics, include both comment types unless a metric below explicitly says otherwise. For song discussion metrics, use voter comments only so a submitter's own note does not make their song look more discussed.

### round_participation
Materialize a helper table to make denominators unambiguous.

- `round_id`
- `player_id`
- `submitted_flag`
- `voted_flag`
- `participant_flag`

Default `participant_flag` to having submitted a song in the round. In the supplied extracts, submitter and voter participation align, but keep the flags separate for robustness.

### vote_opportunities
Create a dense helper table with one row for every eligible voter/submission pair in a round, excluding self-votes. Left join explicit votes and set missing `points_effective = 0`. Keep an `explicit_vote_flag` so missing rows remain distinguishable from explicit zero-point rows. This table should power relationship normalization and voting-similarity calculations.

### track_enrichment
Use the parsed Spotify track ID as the primary external lookup key whenever possible.

- `spotify_track_id`
- `spotify_uri`
- `spotify_artist_id`
- `popularity_score`
- `popularity_source`
- `popularity_retrieved_at`
- `duration_ms`
- `release_date`
- `release_year`
- `decade`
- `explicit`
- `genres`
- `lastfm_tags`
- `musicbrainz_recording_id`

Enrichment should be keyed at track level and reused across submissions of the same track. Cache all API responses.

---

# 3A. Ingestion and Validation Rules Learned from the Real Extracts

Implement these checks in `src/ingest.py` / `src/clean.py` and cover them with tests:

1. Parse all `Created` fields as timezone-aware UTC timestamps.
2. Trim comment strings and normalize blank/whitespace-only values to null.
3. Parse Spotify IDs directly from URIs beginning `spotify:track:`.
4. Validate uniqueness of `round_id + spotify_uri` in submissions.
5. Validate uniqueness of `round_id + spotify_uri + voter_id` in votes.
6. Validate all `Submitter ID` and `Voter ID` values exist in competitors.
7. Validate all submission/vote `Round ID` values exist in rounds.
8. Validate no explicit self-vote rows; fail loudly if found unless a future export format documents them.
9. Do not assume every competitor appears in every round.
10. Do not assume every eligible voter has an explicit vote row for every song.
11. Do not assume point allocations are non-negative.
12. Derive submission totals and standings from the signed vote values, not from any external leaderboard table.
13. Keep `Visible To Voters` as a boolean field even though all supplied rows currently say `Yes`.
14. Generate a small validation report after ingestion with player count, round count, submissions per round, voters per round, point-value distribution, orphan-key checks, duplicate-key checks, and self-vote checks.

The currently supplied sample contains 15 competitors, 2 rounds, 27 submissions and 212 explicit vote rows. Treat those counts as sample diagnostics, not permanent assertions in production code.

---

# 4. Dashboard Information Architecture

Create five primary experiences.

## Home / League HQ
Purpose: immediately entertaining summary.

Show:
- overall league standings
- top 3 highlighted prominently
- award cards
- Spotify popularity vs Music League performance scatter
- 3–5 generated “league lore” facts
- quick links to Players, Records, Relationships, and Taste

Mobile layout should be a single vertical feed.

## Players
Purpose: FIFA-style player cards and detailed player profiles.

Show:
- grid/gallery of player cards
- selectable player profile
- player card hero
- wins, podiums, average points, overall rank
- award badges
- best/worst submissions
- taste profile
- comment/social profile
- biggest fan / nemesis

## Songs & Records
Purpose: song-level leaderboards and league records.

Include full leaderboards for:
- Most Engaged
- Marmite
- Biggest Hit
- Biggest Flop
- Crowd Pleaser
- Cult Classic
- Consensus Pick
- Most Discussed Song
- Basic
- Underground
- Hidden Gem
- Mainstream Flop
- Longest Song
- Shortest Song

## Relationships
Purpose: social/voting dynamics.

Include:
- Biggest Fan
- Nemesis
- Kingmaker / Queenmaker
- Voting Soulmates
- voter-to-submitter matrix
- optional network visualization

## Taste
Purpose: musical profile of the league.

Include:
- Spotify popularity vs league points scatter
- release-year / decade breakdown
- genre/tag breakdown
- player taste comparison
- Old Soul
- New Music Addict
- Musical Time Traveller
- Trend Chaser
- Repeat Offender
- Explorer
- Decade Specialist
- Genre Loyalist
- Pop Idol
- Hipster

---

# 5. Confirmed Metrics and Definitions

## General Performance

### Overall Standings
The supplied export has no standings table. Derive standings from votes:

```text
submission_total_points = sum(signed Points Assigned)
player_total_points = sum(submission_total_points across that player's submissions)
```

Use signed points, including negative values. Rank players by `player_total_points` and show ties explicitly.

### Average Points per Submission
```text
average_points = total_points / number_of_submissions
```

### Wins
Count round finishes where `round_rank == 1`.

### Podiums
Count round finishes where `round_rank <= 3`.

---

# 6. Voting Behaviour Metrics

## Most Generous
Highest average signed points across a player's **explicit vote rows**. Include positive, zero, and negative allocations. Missing/non-vote opportunities are excluded from this average.

This captures how generous the player is when they choose to interact with a song. Also display their positive-vote rate and negative-vote rate for context.

## Harshest Critic
Lowest average signed points across a player's explicit vote rows, again including negative and zero values.

## Biggest Fan
For each recipient player, identify the voter with the highest normalized support across eligible opportunities. Use the dense `vote_opportunities` table so skipped songs count as zero and missed rounds do not create false differences.

Suggested primary metric:
```text
fan_score = sum(points_effective_given_to_player) / eligible_opportunities
```

Also display raw cumulative signed points. Show this primarily on player profiles.

## Nemesis
For each recipient player, identify the voter with the lowest normalized support across eligible opportunities. Use the same denominator as Biggest Fan:

```text
nemesis_score = sum(points_effective_given_to_player) / eligible_opportunities
```

Lowest score becomes the nemesis, subject to a configurable minimum opportunity threshold. Negative votes naturally reduce the score.

## Kingmaker / Queenmaker
Count how often a voter **positively backed** the eventual round winner (`points > 0`). A zero or negative allocation to the winner does not count as backing them.

Suggested display metrics:
- number of winning songs they positively backed
- % of eligible rounds where they positively backed the winner

Use “Kingmaker / Queenmaker” as the award label.

## Voting Soulmates
Compute pairwise similarity between two voters across shared eligible voting opportunities.

Preferred implementation:
- build vectors from the dense `vote_opportunities` table
- missing eligible vote rows become effective zeroes
- preserve explicit-zero vs missing flags for diagnostics, but compare on `points_effective`
- exclude each voter's own ineligible submission
- use cosine similarity or Pearson correlation
- require a configurable minimum number of shared eligible submissions

Show the most similar pair.

---

# 7. Song-Level Awards

## Most Engaged
The user-defined concept is “the song most people voted on”, so count **any explicit vote row**, whether negative, zero, or positive.

For each submission:
```text
eligible_voters = number of round participants excluding the submitter
explicit_voters = distinct eligible voters with a row in votes.csv
engagement_rate = explicit_voters / eligible_voters
```

Use engagement rate for ranking so rounds with different participant counts remain comparable. Also display the raw count, e.g. `9 / 12 voters`.

Do not count missing vote rows as engagement. Explicit `0` vote rows do count.

## Marmite
Because the export supports downvotes, use the full spread of explicit vote values:

```text
marmite_spread = max(points) - min(points)
```

Include negative, zero, and positive explicit votes. Do not insert zeroes for people who did not vote.

Tie-breaker:
- higher standard deviation across all explicit vote values
- then higher engagement rate

## Biggest Hit
Highest total Music League points for a single submission.

## Biggest Flop
Lowest total Music League points for a single submission.

For ties, prefer:
1. lower engagement
2. lower average signed vote among explicit voters

## Crowd Pleaser
A song that combines broad engagement and strong overall score.

Normalize both measures to 0–1 and calculate:
```text
crowd_pleaser_score = 0.5 * engagement_percentile + 0.5 * points_percentile
```

## Cult Classic
Low engagement but high enthusiasm among the people who voted for it.

Suggested score:
```text
cult_classic_score = avg_explicit_vote_percentile * (1 - engagement_rate)
```

Require a positive average assigned score and a minimum number of explicit voters, e.g. at least 2 or 3.

## Consensus Pick
High agreement among explicit voters.

Primary metric:
- lowest standard deviation of all explicit vote values, including negative and zero

Require a minimum engagement threshold so a song with one voter cannot win.

## Most Discussed Song
Rank by total word count in **voter comments** (`votes.Comment`) associated with the submission. Do not include the submitter's own `submissions.Comment` note in this award.

Also display:
- number of voter comments
- number of distinct voter-commenters

## Longest Song / Shortest Song
Use enriched track duration.

---

# 8. Spotify / Popularity Metrics

Store popularity as a timestamped snapshot.

Do not hard-code business logic directly to Spotify field names. Use:
- popularity_score
- popularity_source
- popularity_retrieved_at

## Pop Idol
Player with highest average popularity score across submissions.

Require a minimum number of submissions.

## The Hipster
Player with lowest average popularity score across submissions.

Require the same minimum number of submissions.

## Basic
Single submission with the highest popularity score.

## Underground
Single submission with the lowest popularity score.

## Mainstream vs League
Create a scatter plot:
- X axis = popularity score
- Y axis = Music League points
- one point per submission
- hover: track, artist, submitter, round, popularity, points

Calculate correlation between popularity and league points.

Display a neutral interpretation based on thresholds, for example:
- absolute correlation < 0.2 → little relationship
- 0.2–0.4 → weak relationship
- 0.4–0.6 → moderate relationship
- >0.6 → strong relationship

Do not hard-code a joke about the league’s taste; generate text from the data.

## Hidden Gem
Low popularity but unusually strong Music League performance.

Suggested score:
```text
hidden_gem_score = points_percentile - popularity_percentile
```

Highest score wins.

## Mainstream Flop
High popularity but unusually weak Music League performance.

Suggested score:
```text
mainstream_flop_score = popularity_percentile - points_percentile
```

Highest score wins.

---

# 9. Era and Submission-Habit Metrics

## Old Soul
Player with oldest average release year.

## New Music Addict
Player with newest average release year.

## Musical Time Traveller
Player with widest spread of release years.

Suggested metric:
```text
release_year_range = max_release_year - min_release_year
```

Optionally use standard deviation as a tie-breaker.

## Trend Chaser
Player most likely to submit recently released tracks.

Suggested metric:
```text
track_age_at_submission = submission_year - release_year
```

Lowest average track age wins.

## Repeat Offender
Player with highest artist repetition.

Suggested metric:
```text
repeat_rate = 1 - unique_artists / total_submissions
```

## Explorer
Player with highest artist diversity.

Suggested metric:
```text
artist_diversity = unique_artists / total_submissions
```

## Decade Specialist
Player whose submissions are most concentrated in one decade.

Suggested metric:
```text
max_decade_share = max(submissions_in_decade / total_submissions)
```

## Genre Loyalist
Player whose submissions are most concentrated in one genre/tag family.

Use normalized genre/tag labels before calculating.

---

# 10. Comments / Social Metrics

## Most Vocal
Player with highest total authored comment word count across both:
- `submissions.Comment` (their own submission notes)
- `votes.Comment` (comments they leave while voting)

Trim whitespace-only comments before counting.

## The Mute
Player with lowest total authored comment word count across both comment sources. Display zero-comment players distinctly.

## Essayist
Highest average authored comment length by words across both comment sources.

Use a configurable minimum number of nonblank comments. The supplied extract is still small, so default to `min_comments = 3` initially rather than hard-coding 5.

## Drive-By Critic
Lowest average authored comment length among regular commenters. Use the same configurable minimum-comment threshold.

## Conversation Starter
Player whose **vote comments** cover the widest number of distinct other submissions. Submission notes should not count here.

Primary metric:
```text
distinct_other_submissions_with_vote_comment
```

---

# 11. FIFA-Inspired Player Cards

Create a player-card component inspired by football/FUT cards but not copied exactly.

Each player gets:
- player image
- player name
- overall rating
- primary archetype/title
- 6 attribute ratings
- optional award badges

## Card Attributes
Use these six attributes:

### PFM — Performance
Derived from:
- average points percentile
- wins percentile
- podiums percentile
- overall standings percentile

Suggested weighting:
```text
PFM = 40% avg points
    + 25% wins
    + 20% podiums
    + 15% overall standing
```

### TST — Taste
Derived from:
- artist diversity
- genre diversity
- hidden-gem tendency
- release-year breadth

### VOC — Vocal
Derived from:
- total comment words
- comment count
- distinct submissions commented on

### VOT — Voting
Derived from:
- voting participation
- kingmaker rate
- consistency of using available votes where measurable

Do not interpret “high” as morally better; it is just an activity/profile rating.

### DVG — Divisiveness
Derived from how polarising the player’s submitted tracks tend to be.

Use average normalized Marmite score across their submissions.

### RNG — Range
Derived from:
- artist diversity
- decade breadth
- genre breadth
- release-year range

## Overall Rating
Calculate a weighted composite:
```text
OVR = 35% PFM
    + 20% TST
    + 15% VOC
    + 10% VOT
    + 10% DVG
    + 10% RNG
```

Normalize card stats to an intuitive range such as 40–99.

Use percentile-based scaling to avoid extreme raw-data distortion.

Suggested mapping:
```text
rating = round(40 + percentile * 59)
```

## Primary Archetype / Title
Assign one primary title based on strongest/most distinctive metric.

Possible titles:
- Pop Idol
- The Hipster
- Most Vocal
- Explorer
- Repeat Offender
- Kingmaker / Queenmaker
- Old Soul
- New Music Addict
- Decade Specialist
- Genre Loyalist
- Musical Time Traveller
- Trend Chaser

Award multiple badges but select only one primary title for the card face.

## Card Visual States
Create visual variants:
- Base card
- Top-performer card
- Pop Idol special
- Hipster special
- Most Vocal special
- Kingmaker / Queenmaker special
- Explorer special

Use original styling. Avoid trademarked logos or exact FIFA card replicas.

## Player Images
Read player image mappings from `player_assets.json`.

Example:
```json
{
  "Alex": "assets/players/alex.png",
  "Sam": "assets/players/sam.jpg"
}
```

Use a generic silhouette if no image exists.

Cards must work in a responsive grid and collapse to one or two columns on mobile.

---

# 12. Player Profile Layout

When a player is selected, show:

## Hero
- large player card
- rank
- total points
- average points
- wins
- podiums

## Awards
Badge chips for all awards/titles earned.

## Submission Highlights
- biggest hit
- biggest flop
- most engaged submission
- most marmite submission
- most mainstream submission
- most underground submission

## Taste Profile
- average popularity
- release year distribution
- decade breakdown
- genre/tag breakdown
- most repeated artists

## Social Profile
- total comments
- total words
- average comment length
- biggest fan
- nemesis
- kingmaker rate where relevant

## History
Sortable table of all submissions with:
- round
- track
- artist
- points
- rank
- engagement
- popularity

---

# 13. Home Page Award Cards

Show a compact rotating/featured set of awards:

- Biggest Hit
- Biggest Flop
- Most Engaged
- Marmite
- Pop Idol
- The Hipster
- Most Vocal
- Kingmaker / Queenmaker

Each card should show:
- award name
- winner / track
- short metric value
- optional player/album image
- click path to full leaderboard/profile

---

# 14. League Lore Generator

Generate short facts from the data.

Examples of templates:
- `{A} has given {B} {x} points, while {B} has given {A} {y}.`
- `{A}'s average submitted track is {n} years older than {B}'s.`
- `{A} has commented on {pct}% of all eligible submissions.`
- `{track} scored highly despite a Spotify popularity of only {score}.`
- `{A} has submitted {artist} {n} times.`

Rules:
- facts must be directly calculated from data
- avoid negative/personal insults
- surface statistically interesting differences
- prefer facts with a large relative gap or unusual percentile

---

# 15. Mobile / Messenger Requirements

The dashboard will primarily be opened from a Facebook Messenger link.

Requirements:
- mobile-first layout
- one-column layout at narrow widths
- large tap targets
- no hover-only interactions
- readable charts on phone screens
- avoid giant tables on the landing page
- use expandable sections for detail
- optimize images before deployment
- cache processed datasets

Page should load useful content quickly even if enrichment APIs are unavailable.

API calls should happen during preprocessing, not on every page load.

---

# 16. Data Pipeline

Implement two modes.

## Preprocessing / Refresh Mode
A command such as:

```bash
python -m src.ingest
python -m src.enrich
python -m src.metrics
```

or a single script:

```bash
python refresh_data.py
```

This should:
1. read the latest Music League export from `data/raw/`
2. normalize tables
3. match/enrich tracks
4. cache API responses
5. calculate metrics
6. write processed Parquet files

## Dashboard Runtime
Streamlit should read only processed files.

Do not call external APIs for normal user interactions.

---

# 17. API Matching Strategy

For track matching:

1. normalize track name and artist
2. query external source
3. compare returned track/artist strings
4. store match confidence
5. flag ambiguous matches for manual review

Create a manual overrides file such as:

```text
data/manual_track_matches.csv
```

Columns:
- submission_id
- external_track_id
- source
- notes

Always prefer manual overrides over automatic matching.

---

# 18. Caching

Cache all external calls by a deterministic key such as normalized artist + track.

Suggested files/tables:
- spotify_cache.parquet
- musicbrainz_cache.parquet
- lastfm_cache.parquet

Never re-fetch already enriched tracks unless explicitly requested.

---

# 19. Configuration / Secrets

Local development uses `.env`.

Example `.env.example`:

```text
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
LASTFM_API_KEY=
```

For Streamlit Cloud, read credentials from `st.secrets`.

Never commit real API keys.

---

# 20. Testing Requirements

Write unit tests for at least:
- parsing Music League exports
- engagement calculations
- Marmite calculations
- average points
- wins / podiums
- Biggest Fan / Nemesis
- popularity-derived awards
- player-card stat normalization

Include fixtures with small synthetic leagues where expected winners are obvious.

---

# 21. Graceful Degradation

If Spotify popularity is missing:
- hide popularity-specific awards
- show a notice in the relevant section
- keep all Music League-native metrics working

If a player image is missing:
- show generic silhouette

If genre/tag enrichment is missing:
- hide genre awards only

The core app should never fail because one enrichment source is unavailable.

---

# 22. Deployment

Target: Streamlit Community Cloud.

Deployment flow:
1. push repository to GitHub
2. connect repo to Streamlit Community Cloud
3. select `app.py`
4. configure secrets
5. deploy
6. copy public Streamlit URL
7. share the URL in Facebook Messenger

Keep data volume small enough to live inside the repository or in generated Parquet files.

---

# 23. Build Order

Implement in this order.

## Phase 1 — Data Foundation
- parse export
- normalize players, rounds, submissions, votes, comments
- build core league leaderboard

## Phase 2 — Native Metrics
- performance
- engagement
- Marmite
- comments
- voting relationships

## Phase 3 — Basic Dashboard
- Home
- Records
- player selector

## Phase 4 — Player Cards
- image mapping
- six attributes
- OVR
- responsive card gallery
- detailed player profiles

## Phase 5 — Music Enrichment
- Spotify matching
- release year / duration
- popularity snapshot where available
- MusicBrainz / Last.fm enrichment

## Phase 6 — Enriched Metrics
- Pop Idol
- Hipster
- Basic
- Underground
- Hidden Gem
- Mainstream Flop
- era metrics
- genre metrics

## Phase 7 — Polish
- league lore
- special card designs
- mobile QA
- caching
- deployment

---

# 24. Definition of Done for V1

V1 is complete when:

- Music League export can be dropped into `data/raw/`
- one refresh command creates all processed datasets
- Home page shows overall leaderboard and featured awards
- Players page shows FIFA-inspired cards for every player
- selecting a player shows a detailed profile
- Songs & Records contains the agreed leaderboards
- Relationships contains Biggest Fan, Nemesis, Kingmaker/Queenmaker, and Voting Soulmates
- Taste contains popularity/release/genre analysis where data exists
- dashboard works well on a phone
- dashboard is deployed to a shareable Streamlit URL
- no API secrets are committed to GitHub

---

# 25. Important Implementation Principle

Prioritize explainable metrics over complex black-box scoring.

Every award should have a visible tooltip or caption explaining exactly how it is calculated.

The dashboard is intended to start conversations among friends, so make the interface playful while keeping calculations transparent and reproducible.
