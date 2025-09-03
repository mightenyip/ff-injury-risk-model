# NFL RB/WR Injury Risk Model

A comprehensive pipeline for scraping NFL data from Pro Football Reference and building injury risk prediction models for running backs and wide receivers.

## Overview

This project implements a complete data pipeline for NFL injury risk modeling:

1. **Data Discovery**: Scrape player lists from PFR
2. **Data Collection**: Download weekly game logs for each player
3. **Data Processing**: Join weekly data with team schedules
4. **Feature Engineering**: Aggregate weekly data into season-level features
5. **Model Training**: Train injury risk prediction models
6. **Player Scoring**: Predict injury risk for individual players

## Project Structure

```
ff-injury-risk-model/
├── scripts/                          # Data processing scripts
│   ├── discover_rbs_from_pfr.py     # Discover RB players for a season
│   ├── scrape_pfr_weeklies.py       # Download weekly game logs
│   ├── scrape_team_schedule.py      # Get team schedules
│   ├── join_weekly_with_schedule.py # Join weekly data with schedules
│   ├── bulk_join_weekly.py          # Bulk process all weekly data
│   ├── build_rb_seasons.py          # Create season-level features
│   └── score_player.py              # Score individual players
├── src/
│   └── models/
│       └── rb_model.py              # RB injury risk model training
├── data/                            # Data directories
│   ├── weekly_raw/                  # Raw weekly game logs
│   ├── weekly_joined/               # Weekly data joined with schedules
│   └── schedules/                   # Team schedule files
├── injury_model.py                  # Original injury risk model
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ff-injury-risk-model
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Discover RBs for a Season

Scrape the PFR rushing leaderboard to get every RB's player ID and profile URL:

```bash
python scripts/discover_rbs_from_pfr.py --season 2024 --out data/rb_2024_players.csv
```

**Output**: `data/rb_2024_players.csv` with columns:
- `player`: Player name
- `player_id`: PFR player ID
- `pfr_url`: Player profile URL

### 2. Download Weekly Logs

For each player ID, pull the Receiving & Rushing weekly table from their Game Log page:

```bash
python scripts/scrape_pfr_weeklies.py --season 2024 \
  --players_csv data/rb_2024_players.csv \
  --out_dir data/weekly_raw --pause 1.5
```

**Output**: Individual CSV files like `data/weekly_raw/2024/JacoJo01.csv`

**Columns include**: Week, Age, team, opp, targets, receptions, rush_att, rec_yds, rec_td, rush_yds, rush_td, etc.

**Note**: The script is polite (custom User-Agent + pause between requests). Keep usage moderate and respect PFR's terms.

### 3. Get Team Schedules

To detect missed weeks, you need each team's Schedule & Results table:

```bash
python scripts/scrape_team_schedule.py --team GNB --season 2024 --out data/schedules/gnb_2024.csv
```

Repeat for each team that appears in your weekly CSVs. You can scan the `team` column to see which teams you need.

### 4. Join Weekly Logs with Schedule

Merge a player's weekly data with the team's week list, filling in DNP weeks:

```bash
python scripts/join_weekly_with_schedule.py \
  --weekly_csv data/weekly_raw/2024/JacoJo01.csv \
  --schedule_csv data/schedules/gnb_2024.csv \
  --out data/weekly_joined/2024/JacoJo01_joined.csv
```

**What this does**:
- Adds `played = 1/0` column
- Sets targets, receptions, rush_att to 0 on DNPs
- Creates a complete 1..18 week matrix

**Bulk Processing**: Use the bulk script to process all players at once:

```bash
python scripts/bulk_join_weekly.py --season 2024
```

This will create `data/weekly_joined/2024/all_joined.csv` with all players combined.

### 5. Create Season-Level Features

Aggregate weekly joined data into season-level features for modeling:

```bash
python scripts/build_rb_seasons.py \
  --in_weekly data/weekly_joined/2024/all_joined.csv \
  --out_seasons data/rb_seasons.csv
```

**Output columns**:
- `age`: Player age
- `touches_per_game`: Average touches per game
- `yards_per_touch`: Average yards per touch
- `multiweek_absences`: Whether player had multi-week absences
- `max_consecutive_missed`: Maximum consecutive games missed

### 6. Train the Model

Train and save an injury risk model:

```bash
python -m src.models.rb_model --in data/rb_seasons.csv --out data/rb_model.pkl
```

### 7. Score Individual Players

Predict injury risk for a specific player:

```bash
python scripts/score_player.py --type rb --model data/rb_model.pkl \
  --player '{"age":27,"touches_prev":337,"career_touches_prior":1839,"prior_multiweek_prev":0}'
```

## Data Flow

```
PFR Scraping → Weekly Logs → Schedule Joining → Feature Engineering → Model Training → Player Scoring
     ↓              ↓              ↓              ↓              ↓              ↓
Player List    Game Data     Complete Data   Season Stats   Trained Model   Risk Scores
```

## Features

- **Comprehensive Data Pipeline**: From raw scraping to trained models
- **Respectful Scraping**: Polite requests with configurable delays
- **Robust Error Handling**: Graceful handling of missing data and API failures
- **Flexible Configuration**: Command-line arguments for all parameters
- **Bulk Processing**: Automated processing of multiple players/seasons
- **Model Persistence**: Save and load trained models

## Dependencies

- `numpy`: Numerical computing
- `pandas`: Data manipulation
- `matplotlib`: Plotting
- `seaborn`: Enhanced plotting
- `scikit-learn`: Machine learning
- `scipy`: Scientific computing
- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `lxml`: XML/HTML parser

## Notes

- **Rate Limiting**: Always use the `--pause` parameter to respect PFR's servers
- **Data Quality**: The pipeline handles missing data and edge cases gracefully
- **Scalability**: Designed to process multiple seasons and players efficiently
- **Extensibility**: Easy to add new features or modify the modeling approach

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational and research purposes. Please respect Pro Football Reference's terms of service when scraping data.
