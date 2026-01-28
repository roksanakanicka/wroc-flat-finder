import pandas as pd
import glob
import os
import sqlite3

csv_folder = 'data/'

sale_files = glob.glob(os.path.join(csv_folder, 'apartments_pl_*.csv'))

dfs = []
for f in sale_files:
    df = pd.read_csv(f)
    df['type'] = 'sale'
    dfs.append(df)

# łączymy w jeden df
apartments_sale = pd.concat(dfs, ignore_index=True)

apartments_sale = apartments_sale.dropna()

print(f"Liczba rekordów sprzedaży: {len(apartments_sale)}")
print(apartments_sale.head())
print("\nBraki w kolumnach:")
print(apartments_sale.isna().sum())

# tworzenie bazy SQLite i zapis tabeli
connection = sqlite3.connect('apartments_sale.db')
apartments_sale.to_sql('apartments', connection, if_exists='replace', index=False)
connection.close()

# wszystkie unikalne miasta
cities = apartments_sale['city'].unique()
print(cities)

# ile ich jest
print(f"Liczba unikalnych miast: {len(cities)}")
cities = sorted(apartments_sale['city'].unique())
print(cities)
