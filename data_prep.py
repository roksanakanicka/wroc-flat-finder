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

# FUNKCJE KATEGORII

def price_category(price):
    """Kategorie cenowe - oparte na percentylach"""
    cats = []
    if price < 490000:
        cats.extend(["tanie", "okazja", "przystępne"])
    elif price < 575000:
        cats.append("tanie")
    elif price < 840000:
        pass
    elif price < 1060000:
        cats.extend(["drogie", "luksusowe", "premium"])
    else:
        cats.extend(["bardzo drogie", "luksusowe", "premium", "ekskluzywne"])
    return cats

def size_category(m2):
    """Kategorie metrażu - więcej szczegółów"""
    cats = []
    if m2 < 25:
        cats.append("bardzo małe")
        cats.append("kawalerka")
    elif m2 < 40:
        cats.append("małe")
    elif m2 < 55:
        cats.append("średnie")
    elif m2 < 70:
        cats.append("duże")
    elif m2 < 90:
        cats.append("bardzo duże")
    else:
        cats.extend(["ogromne", "przestronne", "wielkie"])
    return cats

def rooms_category(rooms):
    """Kategoria liczby pokoi"""
    if pd.isna(rooms):
        return []
    r = int(rooms)
    cats = []
    if r == 1:
        cats.append("kawalerka")
    elif r == 2:
        cats.append("dwupokojowe")
    elif r == 3:
        cats.append("trzypokojowe")
    elif r >= 4:
        cats.append("czteropokojowe")
        cats.append("rodzinne")
    return cats

def floor_category(floor, floor_count):
    """Kategoria piętra"""
    cats = []
    if pd.isna(floor):
        return cats
    
    f = int(floor)
    if f == 0:
        cats.append("parter")
    elif f == 1:
        cats.append("pierwsze piętro")
        cats.append("niskie piętro")
    elif f <= 3:
        cats.append("niskie piętro")
    elif f > 6:
        cats.append("wysokie piętro")
    
    # ostatnie piętro
    if not pd.isna(floor_count) and f == int(floor_count):
        cats.append("ostatnie piętro")
    
    return cats

def building_height_category(floor_count):
    """Kategoria wysokości budynku"""
    if pd.isna(floor_count):
        return []
    fc = int(floor_count)
    if fc <= 2:
        return ["niski budynek"]
    elif fc <= 5:
        return ["średni budynek"]
    elif fc <= 10:
        return ["wysoki budynek"]
    else:
        return ["wieżowiec"]

def center_category(dist):
    """Odległość od centrum z podkreślnikami"""
    if pd.isna(dist):
        return []
    d = float(dist)
    if d < 1:
        return ["ścisłe centrum", "centrum"]
    elif d < 2:
        return ["blisko_centrum"]
    elif d < 4:
        return ["niedaleko centrum"]
    elif d < 6:
        return ["daleko od centrum"]
    else:
        return ["bardzo daleko od centrum", "peryferie"]

def year_category(year):
    """Rok budowy - bardziej szczegółowo"""
    if pd.isna(year):
        return []
    y = int(year)
    cats = []
    if y >= 2020:
        cats.extend(["nowe", "nowoczesne", "świeżo wybudowane"])
    elif y >= 2010:
        cats.extend(["nowe", "współczesne"])
    elif y >= 2000:
        cats.append("współczesne")
    elif y >= 1990:
        cats.append("z lat 90")
    elif y >= 1980:
        cats.extend(["stare", "PRL"])
    elif y >= 1960:
        cats.extend(["stare", "PRL", "blok z PRL"])
    else:
        cats.extend(["bardzo stare", "przedwojenne"])
    return cats

def poi_distance_category(dist, poi_name):
    """Odległość do punktu"""
    if pd.isna(dist):
        return []
    d = float(dist)
    if d < 0.2:
        return [f"bardzo_blisko_{poi_name}"]
    elif d < 0.5:
        return [f"blisko_{poi_name}"]
    else:
        return []

def ownership_category(ownership):
    """Typ własności"""
    if pd.isna(ownership):
        return []
    if ownership == "condominium":
        return ["własnościowe"]
    elif ownership == "cooperative":
        return ["spółdzielcze"]
    else:
        return []

def condition_category(condition):
    """Stan mieszkania"""
    if pd.isna(condition):
        return []
    if condition == "premium":
        return ["premium", "luksusowy stan", "wykończone"]
    elif condition == "low":
        return ["niski stan", "do remontu", "do odnowienia"]
    else:
        return []

def building_material_category(material):
    """Materiał budynku"""
    if pd.isna(material):
        return []
    if material == "brick":
        return ["cegła", "ceglany"]
    elif material == "concreteSlab":
        return ["wielka płyta", "betonowy"]
    else:
        return []

def building_type_category(building_type):
    """Typ budynku"""
    if pd.isna(building_type):
        return []
    if building_type == "blockOfFlats":
        return ["blok", "blok mieszkalny"]
    elif building_type == "apartmentBuilding":
        return ["apartamentowiec", "budynek mieszkalny"]
    elif building_type == "tenement":
        return ["kamienica"]
    else:
        return []

# SŁOWNIK LEMATYZACJI
LEMMAS = {
    'tani': 'tani', 'tania': 'tani', 'tanie': 'tani', 'taniego': 'tani', 'taniej': 'tani',
    'okazja': 'okazja', 'okazji': 'okazja', 'okazję': 'okazja',
    'przystępne': 'przystępny', 'przystępny': 'przystępny', 'przystępna': 'przystępny',
    'drogi': 'drogi', 'droga': 'drogi', 'drogie': 'drogi', 'drogich': 'drogi', 'drogiego': 'drogi',
    'mały': 'mały', 'mała': 'mały', 'małe': 'mały', 'małych': 'mały', 'małego': 'mały',
    'średni': 'średni', 'średnia': 'średni', 'średnie': 'średni', 'średnich': 'średni',
    'duży': 'duży', 'duża': 'duży', 'duże': 'duży', 'dużych': 'duży', 'dużego': 'duży',
    'bardzo': 'bardzo',
    'nowy': 'nowy', 'nowa': 'nowy', 'nowe': 'nowy', 'nowych': 'nowy', 'nowego': 'nowy',
    'stary': 'stary', 'stara': 'stary', 'stare': 'stary', 'starych': 'stary', 'starego': 'stary',
    'współczesny': 'współczesny', 'współczesne': 'współczesny', 'współczesna': 'współczesny',
    'luksusowy': 'luksusowy', 'luksusowe': 'luksusowy', 'luksusowa': 'luksusowy',
    'ekskluzywne': 'ekskluzywny', 'ekskluzywny': 'ekskluzywny', 'ekskluzywna': 'ekskluzywny',
    'blisko': 'blisko', 'daleko': 'daleko', 'niedaleko': 'niedaleko',
    'blisko_centrum': 'blisko_centrum',
    'blisko_szkoła': 'blisko_szkoła',
    'blisko_klinika': 'blisko_klinika',
    'blisko_przedszkole': 'blisko_przedszkole',
    'blisko_apteka': 'blisko_apteka',
    'blisko_restauracja': 'blisko_restauracja',
    'blisko_uczelnia': 'blisko_uczelnia',
    'blisko_poczta': 'blisko_poczta',
    'bardzo_blisko_szkoła': 'bardzo_blisko_szkoła',
    'bardzo_blisko_klinika': 'bardzo_blisko_klinika',
    'bardzo_blisko_przedszkole': 'bardzo_blisko_przedszkole',
    'bardzo_blisko_apteka': 'bardzo_blisko_apteka',
    'bardzo_blisko_restauracja': 'bardzo_blisko_restauracja',
    'bardzo_blisko_uczelnia': 'bardzo_blisko_uczelnia',
    'bardzo_blisko_poczta': 'bardzo_blisko_poczta',
    'centrum': 'centrum', 'centrach': 'centrum', 'centru': 'centrum',
    'balkon': 'balkon', 'balkonu': 'balkon', 'balkony': 'balkon', 'balkonem': 'balkon',
    'winda': 'winda', 'windy': 'winda', 'windę': 'winda', 'windą': 'winda',
    'parking': 'parking', 'parkingu': 'parking', 'parkingi': 'parking', 'parkingiem': 'parking',
    'ochrona': 'ochrona', 'ochrony': 'ochrona', 'ochronę': 'ochrona', 'ochroną': 'ochrona',
    'piwnica': 'piwnica', 'piwnicy': 'piwnica', 'piwnicę': 'piwnica',
    'cena': 'cena', 'ceny': 'cena', 'cenę': 'cena',
    'od': 'od', 'z': 'z', 'do': 'do',
    'pokoje': 'pokój', 'pokój': 'pokój', 'pokoi': 'pokój',
    'kawalerka': 'kawalerka', 'kawalerki': 'kawalerka',
    'dwupokojowe': 'dwupokojowy', 'dwupokojowy': 'dwupokojowy',
    'trzypokojowe': 'trzypokojowy', 'trzypokojowy': 'trzypokojowy',
    'czteropokojowe': 'czteropokojowy', 'czteropokojowy': 'czteropokojowy',
    'rodzinne': 'rodzinny', 'rodzinny': 'rodzinny',
    'parter': 'parter', 'parterze': 'parter',
    'piętro': 'piętro', 'piętra': 'piętro', 'piętrze': 'piętro',
    'niskie': 'niski', 'niski': 'niski', 'niskiego': 'niski',
    'wysokie': 'wysoki', 'wysoki': 'wysoki', 'wysokiego': 'wysoki',
    'ostatnie': 'ostatni', 'ostatni': 'ostatni',
    'pierwsze': 'pierwszy', 'pierwszy': 'pierwszy',
    'budynek': 'budynek', 'budynku': 'budynek',
    'wieżowiec': 'wieżowiec', 'wieżowca': 'wieżowiec',
    'ścisłe': 'ścisły', 'ścisły': 'ścisły',
    'nowoczesne': 'nowoczesny', 'nowoczesny': 'nowoczesny',
    'świeżo': 'świeżo', 'wybudowane': 'wybudowany', 'wybudowany': 'wybudowany',
    'lat': 'rok', '90': '90',
    'PRL': 'prl', 'prl': 'prl',
    'blok': 'blok', 'bloku': 'blok',
    'przedwojenne': 'przedwojenny', 'przedwojenny': 'przedwojenny',
    'ogromne': 'ogromny', 'ogromny': 'ogromny',
    'przestronne': 'przestronny', 'przestronny': 'przestronny',
    'wielkie': 'wielki', 'wielki': 'wielki',
    'peryferie': 'peryferie', 'peryferiach': 'peryferie',
    'szkoła': 'szkoła', 'szkoły': 'szkoła', 'szkole': 'szkoła',
    'klinika': 'klinika', 'kliniki': 'klinika', 'klinice': 'klinika',
    'przedszkole': 'przedszkole', 'przedszkola': 'przedszkole',
    'apteka': 'apteka', 'apteki': 'apteka', 'aptece': 'apteka',
    'restauracja': 'restauracja', 'restauracji': 'restauracja',
    'uczelnia': 'uczelnia', 'uczelni': 'uczelnia',
    'poczta': 'poczta', 'poczty': 'poczta',
    'własnościowe': 'własnościowy', 'własnościowy': 'własnościowy',
    'spółdzielcze': 'spółdzielczy', 'spółdzielczy': 'spółdzielczy',
    'premium': 'premium',
    'stan': 'stan', 'stanu': 'stan',
    'remontu': 'remont', 'remont': 'remont',
    'odnowienia': 'odnowienie', 'odnowienie': 'odnowienie',
    'wykończone': 'wykończony', 'wykończony': 'wykończony',
    'cegła': 'cegła', 'cegły': 'cegła',
    'ceglany': 'ceglany', 'ceglana': 'ceglany', 'ceglane': 'ceglany',
    'wielka': 'wielki', 'płyta': 'płyta',
    'betonowy': 'betonowy', 'betonowa': 'betonowy', 'betonowe': 'betonowy',
    'mieszkalny': 'mieszkalny', 'mieszkalna': 'mieszkalny', 'mieszkalne': 'mieszkalny',
    'apartamentowiec': 'apartamentowiec', 'apartamentowca': 'apartamentowiec',
    'kamienica': 'kamienica', 'kamienicy': 'kamienica',
}

def lemmatize_text(text):
    """Lematyzacja tekstu przez słownik"""
    words = text.lower().split()
    return ' '.join([LEMMAS.get(w, w) for w in words])

def make_document(row):
    """Tworzy szczegółowy tekstowy dokument dla mieszkania"""
    parts = []
    
    # metraż
    parts += size_category(row["squareMeters"])
    # cena
    parts += price_category(row["price"])
    # liczba pokoi
    parts += rooms_category(row.get("rooms"))
    # piętro
    parts += floor_category(row.get("floor"), row.get("floorCount"))
    # wysokość budynku
    parts += building_height_category(row.get("floorCount"))
    # typ budynku
    parts += building_type_category(row.get("type"))
    # odległość od centrum
    parts += center_category(row.get("centreDistance"))
    # rok budowy
    parts += year_category(row.get("buildYear"))
    # własność
    parts += ownership_category(row.get("ownership"))
    # stan
    parts += condition_category(row.get("condition"))
    # materiał
    parts += building_material_category(row.get("buildingMaterial"))
    
    # wszystkie cechy bool
    if row.get("hasBalcony") == "yes":
        parts.append("balkon")
    if row.get("hasElevator") == "yes":
        parts.append("winda")
    if row.get("hasParkingSpace") == "yes":
        parts.append("parking")
    if row.get("hasSecurity") == "yes":
        parts.append("ochrona")
    if row.get("hasStorageRoom") == "yes":
        parts.append("piwnica")
    
    # odległości do punktu (tylko jak blisko)
    parts += poi_distance_category(row.get("schoolDistance"), "szkoła")
    parts += poi_distance_category(row.get("clinicDistance"), "klinika")
    parts += poi_distance_category(row.get("kindergartenDistance"), "przedszkole")
    parts += poi_distance_category(row.get("pharmacyDistance"), "apteka")
    parts += poi_distance_category(row.get("restaurantDistance"), "restauracja")
    parts += poi_distance_category(row.get("collegeDistance"), "uczelnia")
    parts += poi_distance_category(row.get("postOfficeDistance"), "poczta")
    
    doc = " ".join(parts)
    return lemmatize_text(doc)

# dodanie kolumny document
apartments_sale['document'] = apartments_sale.apply(make_document, axis=1)

# zapis do SQLite
connection = sqlite3.connect('apartments_sale.db')
apartments_sale.to_sql('apartments', connection, if_exists='replace', index=False)
connection.close()
