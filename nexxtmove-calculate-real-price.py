import pandas as pd
import datetime as dt
import os

# Zet pad naar Excel-bestand (Windows-stijl)
file_path = os.path.join(os.getcwd(), "export_charges_kwartaal2.xlsx")
df = pd.read_excel(file_path)

# Functie om uren op te splitsen in dag/nacht (met weekendlogica)
def split_day_night(start: dt.datetime, end: dt.datetime):
    cur = start
    day = night = dt.timedelta()
    while cur < end:
        nxt = min(end, cur + dt.timedelta(minutes=1))  # per minuut nauwkeurigheid
        is_weekend = (
            cur.weekday() == 5 or cur.weekday() == 6 or  # zaterdag of zondag
            (cur.weekday() == 4 and cur.hour >= 22) or   # vrijdag vanaf 22u
            (cur.weekday() == 0 and cur.hour < 7)        # maandag tot 7u
        )
        if not is_weekend and 7 <= cur.hour < 22:
            day += nxt - cur
        else:
            night += nxt - cur
        cur = nxt
    return round(day.total_seconds()/3600, 2), round(night.total_seconds()/3600, 2)

# Parse kolommen naar datetime
df['Sessie gestart'] = pd.to_datetime(df['Sessie gestart'])
df['Sessie beëindigd'] = pd.to_datetime(df['Sessie beëindigd'])

# Bereken dag/nacht uren per rij
res = df.apply(lambda row: split_day_night(row['Sessie gestart'], row['Sessie beëindigd']), axis=1)
df[['Daguren', 'Nachturen']] = pd.DataFrame(res.tolist(), index=df.index)

# Verbruik opsplitsen volgens verhouding dag/nacht
verbruik = df['Verbruik'].astype(float)
totaal_uren = df['Daguren'] + df['Nachturen']
df['Verbruik_dag'] = (df['Daguren'] / totaal_uren) * verbruik
df['Verbruik_nacht'] = (df['Nachturen'] / totaal_uren) * verbruik

# Tarieven
prijs_dag = 39.89  # cent per kWh
prijs_nacht = 39.22  # cent per kWh

#Kwartaal 1: 0,4081 / 0,4014
#Kwartaal 2: 0,3989 / 0,3922

#Kwartaal 1 #energie 0,1064 / 0,0997
#Kwartaal 2 #energie 0,0972 / 0,0905
#Vaste kosten jaar (0,3017): 
#netkosten 0,0472
#heffingen 0,2042
#heffingen 0,0503
#Totaal 0,4081
#
#
#

# Bereken kost
# Opm: je kan ook /100 doen om naar euro te gaan, afhankelijk van je input

df['Kost_dag_cent'] = df['Verbruik_dag'] * prijs_dag
df['Kost_nacht_cent'] = df['Verbruik_nacht'] * prijs_nacht

df['Totale_kost_cent'] = df['Kost_dag_cent'] + df['Kost_nacht_cent']

# Opslaan naar nieuw Excel-bestand
output_path = os.path.join(os.getcwd(), "verrijkte_sessies_kwartaal2.xlsx")
df.to_excel(output_path, index=False)

# Resultaat tonen
print(df[['Sessie gestart', 'Sessie beëindigd', 'Daguren', 'Nachturen', 'Verbruik_dag', 'Verbruik_nacht', 'Totale_kost_cent']])
print(f"Bestand opgeslagen als: {output_path}")

