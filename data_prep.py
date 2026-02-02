import pandas as pd
import glob
import os
import sqlite3

# ładowanie danych z CSV
csv_folder = 'data/'
sale_files = glob.glob(os.path.join(csv_folder, 'apartments_pl_*.csv'))
dfs = [pd.read_csv(f) for f in sale_files]
apartments_sale = pd.concat(dfs, ignore_index=True)

# tylko Wrocław
apartments_sale = apartments_sale[apartments_sale['city'] == 'wroclaw']

# uzupełnienie braków w kolumnach boolean
boolean_cols = ['hasParkingSpace', 'hasBalcony', 'hasElevator', 'hasSecurity', 'hasStorageRoom']
for col in boolean_cols:
    if col in apartments_sale.columns:
        apartments_sale[col] = apartments_sale[col].fillna('no')

# usunięcie duplikatów
apartments_sale = apartments_sale.drop_duplicates()

# funkcje kategorii dla dokumentów tekstowych
def price_category(price):
    if price < 400000:
        return ["tanie"]
    elif price < 700000:
        return ["średnia cena"]
    elif price < 1000000:
        return ["drogie"]
    else:
        return ["luksusowe"]

def size_category(m2):
    if m2 < 35:
        return ["małe"]
    elif m2 < 60:
        return ["średnie"]
    elif m2 < 90:
        return ["duże"]
    else:
        return ["bardzo duże"]
    
def center_category(dist):
    if pd.isna(dist):
        return []
    if float(dist) < 4:
        return ["blisko centrum"]
    else:
        return ["daleko od centrum"]

def year_category(year):
    if pd.isna(year):
        return []
    year = int(year)
    if year >= 2015:
        return ["nowe"]
    elif year >= 2000:
        return ["współczesne"]
    else:
        return ["stare"]

# słownik lematyzacji
LEMMAS = {
    'tani': 'tani', 'tania': 'tani', 'tanie': 'tani', 'taniego': 'tani', 'taniej': 'tani',
    'drogi': 'drogi', 'droga': 'drogi', 'drogie': 'drogi', 'drogich': 'drogi', 'drogiego': 'drogi',
    'mały': 'mały', 'mała': 'mały', 'małe': 'mały', 'małych': 'mały', 'małego': 'mały',
    'średni': 'średni', 'średnia': 'średni', 'średnie': 'średni', 'średnich': 'średni',
    'duży': 'duży', 'duża': 'duży', 'duże': 'duży', 'dużych': 'duży', 'dużego': 'duży',
    'bardzo': 'bardzo',
    'nowy': 'nowy', 'nowa': 'nowy', 'nowe': 'nowy', 'nowych': 'nowy', 'nowego': 'nowy',
    'stary': 'stary', 'stara': 'stary', 'stare': 'stary', 'starych': 'stary', 'starego': 'stary',
    'współczesny': 'współczesny', 'współczesne': 'współczesny', 'współczesna': 'współczesny',
    'luksusowy': 'luksusowy', 'luksusowe': 'luksusowy', 'luksusowa': 'luksusowy',
    'blisko': 'blisko', 'daleko': 'daleko',
    'centrum': 'centrum', 'centrach': 'centrum', 'centru': 'centrum',
    'balkon': 'balkon', 'balkonu': 'balkon', 'balkony': 'balkon', 'balkonem': 'balkon',
    'winda': 'winda', 'windy': 'winda', 'windę': 'winda', 'windą': 'winda',
    'parking': 'parking', 'parkingu': 'parking', 'parkingi': 'parking', 'parkingiem': 'parking',
    'ochrona': 'ochrona', 'ochrony': 'ochrona', 'ochronę': 'ochrona', 'ochroną': 'ochrona',
    'komórka': 'komórka', 'komórki': 'komórka', 'komórkę': 'komórka', 'komórką': 'komórka',
    'cena': 'cena', 'ceny': 'cena', 'cenę': 'cena',
    'od': 'od', 'z': 'z', 'do': 'do',
}

def lemmatize_text(text):
    """Lematyzacja tekstu przez słownik"""
    words = text.lower().split()
    return ' '.join([LEMMAS.get(w, w) for w in words])

def make_document(row):
    """Tworzy tekstowy dokument dla mieszkania"""
    parts = []
    parts += size_category(row["squareMeters"])
    parts += price_category(row["price"])
    parts += center_category(row.get("centreDistance"))
    parts += year_category(row.get("buildYear"))
    
    if row.get("hasBalcony") == "yes":
        parts.append("balkon")
    if row.get("hasElevator") == "yes":
        parts.append("winda")
    if row.get("hasParkingSpace") == "yes":
        parts.append("parking")
    if row.get("hasSecurity") == "yes":
        parts.append("ochrona")
    if row.get("hasStorageRoom") == "yes":
        parts.append("komórka")
    
    doc = " ".join(parts)
    return lemmatize_text(doc)

# dodanie kolumny document
apartments_sale['document'] = apartments_sale.apply(make_document, axis=1)

# zapis do SQLite
connection = sqlite3.connect('apartments_sale.db')
apartments_sale.to_sql('apartments', connection, if_exists='replace', index=False)
connection.close()

print(f"Liczba mieszkań w bazie danych: {len(apartments_sale)}")