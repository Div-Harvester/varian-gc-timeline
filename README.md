# Varian GC Data & Weather Conditions

Interactive Dash app for viewing gas chromatograph contaminant data alongside NOAA weather for Beverly, MA.

## Files needed
- `gc_timeline_app.py`
- `beverly_weather.csv` (included)
- `VarianGCData_Thru_102126_1615.xlsx` (add this file to the repo root)

## Local run
```bash
pip install -r requirements.txt
python gc_timeline_app.py
```
Open http://127.0.0.1:8050

## Deploy to Render
1. Connect this GitHub repo to Render.
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python gc_timeline_app.py`
4. Upload the Excel file to the repo if not already present.
