import pandas as pd
import glob
import os
import sqlite3
from lemmatization import lemmatize_text

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
    cats = []
    if price < 490000:
        cats.extend(["tanie", "okazja", "przystępne"])
    elif price < 600000:
        cats.append("tanie")
    elif price < 1000000:
        pass
    else:
        cats.extend(["luksusowe", "premium", "ekskluzywne"])
    return cats

def size_category(m2):
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
    if pd.isna(ownership):
        return []
    if ownership == "condominium":
        return ["własnościowe"]
    elif ownership == "cooperative":
        return ["spółdzielcze"]
    else:
        return []

def condition_category(condition):
    if pd.isna(condition):
        return []
    if condition == "premium":
        return ["premium", "luksusowy stan", "wykończone"]
    elif condition == "low":
        return ["niski stan", "do remontu", "do odnowienia"]
    else:
        return []

def building_material_category(material):
    if pd.isna(material):
        return []
    if material == "brick":
        return ["cegła", "ceglany"]
    elif material == "concreteSlab":
        return ["wielka płyta", "betonowy"]
    else:
        return []

def building_type_category(building_type):
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


def make_document(row):
    parts = []
    
    parts += size_category(row["squareMeters"])
    parts += price_category(row["price"])
    parts += rooms_category(row.get("rooms"))
    parts += floor_category(row.get("floor"), row.get("floorCount"))
    parts += building_height_category(row.get("floorCount"))
    parts += building_type_category(row.get("type"))
    parts += center_category(row.get("centreDistance"))
    parts += year_category(row.get("buildYear"))
    parts += ownership_category(row.get("ownership"))
    parts += condition_category(row.get("condition"))
    parts += building_material_category(row.get("buildingMaterial"))
    
    # cechy bool
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
    
    # odległości
    parts += poi_distance_category(row.get("schoolDistance"), "szkoła")
    parts += poi_distance_category(row.get("clinicDistance"), "klinika")
    parts += poi_distance_category(row.get("kindergartenDistance"), "przedszkole")
    parts += poi_distance_category(row.get("pharmacyDistance"), "apteka")
    parts += poi_distance_category(row.get("restaurantDistance"), "restauracja")
    parts += poi_distance_category(row.get("collegeDistance"), "uczelnia")
    parts += poi_distance_category(row.get("postOfficeDistance"), "poczta")
    
    # dzielnica
    if row.get("district_name") is not None and row.get("district_name") != '':
        district_full = row["district_name"].lower()
        # dzielenie po '-' i dodanie każdej części osobno
        # dla kilku dzielnic w apartments.db np ' Pilczyce - Kozanów - Popowice Płn.'
        district_parts = [part.strip() for part in district_full.split(' - ')]
        parts.extend(district_parts)
    
    doc = " ".join(parts)
    return lemmatize_text(doc)

apartments_sale['document'] = apartments_sale.apply(make_document, axis=1)
apartments_sale['district_name'] = None

connection = sqlite3.connect('apartments_sale.db')
apartments_sale.to_sql('apartments', connection, if_exists='replace', index=False)


# ========== DODAWANIE DZIELNIC Z SHAPEFILE ==========

try:
    import geopandas as gpd
    from shapely.geometry import Point
    
    SHAPEFILE_PATH = 'location/GraniceOsiedli.shp'
    
    districts = gpd.read_file(SHAPEFILE_PATH, encoding='utf-8')
    name_column = 'NAZWAOSIED'
    
    # konwertuj do WGS84
    if districts.crs != 'EPSG:4326':
        districts = districts.to_crs('EPSG:4326')
        
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, latitude, longitude 
        FROM apartments 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    apartments = cursor.fetchall()
    
    matched = 0
    not_matched = 0
    
    try:
        from tqdm import tqdm
        iterator = tqdm(apartments, desc="dopasowywanie dzielnic")
    except ImportError:
        iterator = apartments
    
    for apt_id, lat, lon in iterator:
        point = Point(lon, lat)
        containing_district = districts[districts.contains(point)]
        
        if not containing_district.empty:
            district_name = containing_district.iloc[0][name_column]
            cursor.execute(
                "UPDATE apartments SET district_name = ? WHERE id = ?",
                (district_name, apt_id)
            )
            matched += 1
        else:
            distances = districts.geometry.distance(point)
            nearest_idx = distances.idxmin()
            district_name = districts.loc[nearest_idx, name_column]
            cursor.execute(
                "UPDATE apartments SET district_name = ? WHERE id = ?",
                (district_name, apt_id)
            )
            not_matched += 1
    
    connection.commit()
    
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM apartments")
    rows = cursor.fetchall()
    
    for row in rows:
        row_dict = dict(row)
        new_doc = make_document(row_dict)
        cursor.execute("UPDATE apartments SET document = ? WHERE id = ?", 
                      (new_doc, row_dict['id']))
    
    connection.commit()
    
    print(f"dzielnice: dopasowano dokladnie {matched}, najblizsze {not_matched}")

    cursor.execute("""
        SELECT district_name, COUNT(*) as count 
        FROM apartments 
        WHERE district_name IS NOT NULL
        GROUP BY district_name 
        ORDER BY count DESC 
        LIMIT 10
    """)
    
    print("\ntop 10 dzielnic:")
    for district, count in cursor.fetchall():
        print(f"  {district}: {count} mieszkań")
    
except ImportError:
    print("brak geopandas - pomijam dzielnice")
except FileNotFoundError:
    print(f"brak {SHAPEFILE_PATH} - pomijam dzielnice")
except Exception as e:
    print(f"blad przy dzielnicach: {e}")

connection.close()