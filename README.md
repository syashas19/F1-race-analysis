# F1 Race Analysis

A small data analysis project that downloads real Formula 1 race results and answers three questions:

1. **How much does qualifying decide the race?** Win rate for each starting position.
2. **Who are the best racers?** Average places gained from grid to finish.
3. **Who dominated when?** Constructor points season by season.

Data comes from the free [Jolpica-F1 API](https://api.jolpi.ca/ergast/f1) (the successor to Ergast). It is downloaded on first run and cached in `data/`.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python f1_analysis.py            # defaults to 2018-2025
python f1_analysis.py --start 2010 --end 2025 --refresh
```

Charts are saved to `charts/` and summary tables print in the terminal.

## Tech
Python, pandas, matplotlib, requests.

## Notes
- Places gained only counts races a driver finished (including lapped finishes) and drivers with at least 30 races, and ignores pit-lane starts.
- Constructors that were renamed (for example Alfa Romeo to Sauber) appear under the name used in each season.

## Ideas to extend
- Add football data (e.g. Premier League results) and compare home advantage with pole advantage.
- Add a Jupyter notebook with your own conclusions.
- Break the analysis down by circuit.

Developed by S YASHAS
