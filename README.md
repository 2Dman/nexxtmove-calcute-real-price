# EV Charging Sessions — Day/Night Split and Cost Calculation

This guide explains what the Python script below does, how to use it, and which assumptions are made during the calculation.

## Purpose
The script reads an Excel export of charging sessions and splits the duration of each session into **day hours** and **night hours**, with **weekend logic**. Based on this, it proportionally allocates the consumption (kWh) to day/night and calculates the **cost in euro cents** using separate day and night tariff prices. The result is saved to a new Excel file `enriched_sessions.xlsx`.

## Input
An Excel file `export_charges_kwartaal1.xlsx` in the current working directory with at least these columns:
- `Sessie gestart` (datetime)
- `Sessie beëindigd` (datetime)
- `Verbruik` (kWh, numeric)

## Output
A new Excel file `enriched_sessions.xlsx` with additional columns:
- `Daguren` — number of hours during the day (decimal, rounded to 0.01 hours)
- `Nachturen` — number of hours during the night/weekend (decimal, rounded to 0.01 hours)
- `Verbruik_dag` — portion of `Verbruik` assigned to day hours
- `Verbruik_nacht` — portion of `Verbruik` assigned to night hours
- `Kost_dag_cent` — cost (in **cents**) for the day portion
- `Kost_nacht_cent` — cost (in **cents**) for the night portion
- `Totale_kost_cent` — sum of day + night (in **cents**)

Additionally, a subset of these columns is printed in the console.

## Day/Night and weekend logic
The function `split_day_night(start, end)` iterates minute-by-minute through the interval and adds duration to two “buckets”:
- **Day** when it’s **not weekend** and the hour is within **[07:00, 22:00)**.
- **Night** in all other cases (night + weekend).

Weekend definition in the code:
- Saturday and Sunday are always **night**.
- **Friday from 22:00** counts as **night/weekend**.
- **Monday until 07:00** counts as **night/weekend**.

The function rounds total day and night durations to **2 decimal hours** (e.g., 1.75 h).

## Calculations
1. **Hour allocation**
   ```python
   day_hours, night_hours = split_day_night(start, end)
   ```
2. **Proportional consumption allocation**
   ```python
   total_hours = Daguren + Nachturen
   Verbruik_dag   = (Daguren   / total_hours) * Verbruik
   Verbruik_nacht = (Nachturen / total_hours) * Verbruik
   ```
   > Note: if `total_hours` is 0 (e.g., identical start and end time), you should guard against division by zero.
3. **Tariff prices (in cents/kWh)**
   ```python
   prijs_dag   = 40.81  # cents per kWh
   prijs_nacht = 40.14  # cents per kWh
   ```
4. **Cost calculation (in cents)**
   ```python
   Kost_dag_cent    = Verbruik_dag   * prijs_dag
   Kost_nacht_cent  = Verbruik_nacht * prijs_nacht
   Totale_kost_cent = Kost_dag_cent + Kost_nacht_cent
   ```
   > If needed, divide by 100 to convert to **euros**.

## Full script (as provided)
```python
import pandas as pd
import datetime as dt
import os

# Set path to Excel file (Windows-style)
file_path = os.path.join(os.getcwd(), "export_charges_kwartaal1.xlsx")
df = pd.read_excel(file_path)

# Function to split hours into day/night (with weekend logic)
def split_day_night(start: dt.datetime, end: dt.datetime):
    cur = start
    day = night = dt.timedelta()
    while cur < end:
        nxt = min(end, cur + dt.timedelta(minutes=1))  # per-minute accuracy
        is_weekend = (
            cur.weekday() == 5 or cur.weekday() == 6 or  # Saturday or Sunday
            (cur.weekday() == 4 and cur.hour >= 22) or   # Friday from 22:00
            (cur.weekday() == 0 and cur.hour < 7)        # Monday until 07:00
        )
        if not is_weekend and 7 <= cur.hour < 22:
            day += nxt - cur
        else:
            night += nxt - cur
        cur = nxt
    return round(day.total_seconds()/3600, 2), round(night.total_seconds()/3600, 2)

# Parse columns to datetime
df['Sessie gestart'] = pd.to_datetime(df['Sessie gestart'])
df['Sessie beëindigd'] = pd.to_datetime(df['Sessie beëindigd'])

# Calculate day/night hours per row
res = df.apply(lambda row: split_day_night(row['Sessie gestart'], row['Sessie beëindigd']), axis=1)
df[['Daguren', 'Nachturen']] = pd.DataFrame(res.tolist(), index=df.index)

# Split consumption according to day/night ratio
consumption = df['Verbruik'].astype(float)
total_hours = df['Daguren'] + df['Nachturen']
df['Verbruik_dag'] = (df['Daguren'] / total_hours) * consumption
df['Verbruik_nacht'] = (df['Nachturen'] / total_hours) * consumption

# Tariffs
prijs_dag = 40.81  # cents per kWh
prijs_nacht = 40.14  # cents per kWh

# Calculate cost
# Note: divide by 100 to get euros if needed

df['Kost_dag_cent'] = df['Verbruik_dag'] * prijs_dag
df['Kost_nacht_cent'] = df['Verbruik_nacht'] * prijs_nacht

df['Totale_kost_cent'] = df['Kost_dag_cent'] + df['Kost_nacht_cent']

# Save to new Excel file
output_path = os.path.join(os.getcwd(), "enriched_sessions.xlsx")
df.to_excel(output_path, index=False)

# Show result
print(df[['Sessie gestart', 'Sessie beëindigd', 'Daguren', 'Nachturen', 'Verbruik_dag', 'Verbruik_nacht', 'Totale_kost_cent']])
print(f"File saved as: {output_path}")
```

## Requirements
- Python 3.9+
- Packages: `pandas`, `openpyxl` (for Excel I/O)
  ```bash
  pip install pandas openpyxl
  ```

## Usage
Place `export_charges_kwartaal1.xlsx` in the same folder as the script and run it. After completion, you’ll find **enriched_sessions.xlsx** with the calculated columns.

## Practical tips
- **Performance:** minute-by-minute iteration is accurate but may be slow for very long sessions or large datasets. Consider an interval-based approach (splitting by time blocks) for optimization.
- **Robustness:** add a check to handle `total_hours == 0`.
- **Currency:** divide by 100 to get euros and format to 2 decimal places if desired.
- **Tariffs:** adjust `prijs_dag` and `prijs_nacht` if rates change.
