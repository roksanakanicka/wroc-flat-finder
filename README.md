# Wyszukiwarka Mieszkań Wrocław

Wyszukiwarka mieszkań wykorzystująca TF-IDF i miary podobieństwa do wyszukiwania ofert na podstawie zapytań w języku naturalnym.

## Dane
**Zbiór danych mieszkań:** https://www.kaggle.com/datasets/krzysztofjamroz/apartment-prices-in-poland

Użyto danych mieszkan na sprzedaż znajdujących się we Wrocławiu.

**Granice osiedli Wrocławia po współrzędnych:** https://geoportal.wroclaw.pl/zasoby/

**Parsowanie informacji o mieście:** https://pl.wikipedia.org/wiki/Wroc%C5%82aw

## Technologie

- **Flask** - framework aplikacji webowej
- **SQLite** - baza danych z >10k rekordów mieszkań
- **Beautiful Soup** - parsowanie HTML z Wikipedii
- **Folium** - interaktywna mapa z MarkerCluster
- **Matplotlib** - wizualizacje danych
- **GeoPandas** - spatial join dzielnic Wrocławia

## Funkcjonalności

### Wyszukiwanie tekstowe
Zapytania w naturalnym języku typu "tanie mieszkanie blisko szkoły z balkonem" są przetwarzane przez:
- **Lematyzację** - słownik 200+ form wyrazów do analizy morfologicznej
- **TF-IDF** - wagi termów z normalizacją TF przez max i IDF = log₁₀(N/df)
- **Preprocessing** - sklejanie fraz "blisko X", "bardzo blisko X"

### Miary podobieństwa
Każdy wynik wyszukany przez lupkę zawiera 3 miary podobieństwa do query:
- **Cosine**
- **Jaccard**
- **Dice**

Możliwość sortowania wyników według wybranej miary.

### Filtry i kategoryzacja
13 filtrów SQL: pokoje, metraż, cena, rok budowy, piętro, dzielnica, balkon, winda, parking, odległość od centrum.

Automatyczna kategoryzacja mieszkań na podstawie:
- ceny (tanie/luksusowe/premium)
- wielkości (małe/średnie/duże/ogromne)
- lokalizacji (centrum/blisko centrum/peryferie)
- wieku (nowe/współczesne/PRL/przedwojenne)
- odległości do POI (szkoła, klinika, przedszkole, apteka, uczelnia, restauracja, poczta)

### Wizualizacje
- Histogram cen
- Scatter plot cena vs metraż
- Bar chart liczby pokoi
- Mapa Folium z klastrowaniem markerów

### Dane o mieście
Parsowanie Wikipedii (5 reguł Beautiful Soup + regex) dla populacji, powierzchni i opisu Wrocławia.

### Spatial join dzielnic
GeoPandas łączy każde mieszkanie z dzielnicą na podstawie shapefiles GraniceOsiedli.shp - spatial containment lub nearest neighbor.

## Struktura danych

**27+ unikalnych cech** w bazie: rooms, squareMeters, price, floor, floorCount, buildYear, latitude, longitude, centreDistance, hasBalcony, hasElevator, hasParkingSpace, hasSecurity, hasStorageRoom, ownership, condition, buildingMaterial, type, schoolDistance, clinicDistance, kindergartenDistance, pharmacyDistance, restaurantDistance, collegeDistance, postOfficeDistance, district_name, document.

## Instalacja

```bash
pip install -r requirements.txt
```

## Uruchomienie

1. Przygotowanie bazy danych:
```bash
python data_prep.py
```

2. Uruchomienie aplikacji:
```bash
python app.py
```

3. Otwórz http://localhost:5000


## Architektura

```
├── data/                           # folder z plikami CSV
│   └── apartments_pl_*.csv         # dane mieszkań z Kaggle
│
├── location/                       # shapefiles dzielnic Wrocławia
│   ├── GraniceOsiedli.shp     
│   ├── GraniceOsiedli.dbf          
│   ├── GraniceOsiedli.shx          
│   └── GraniceOsiedli.prj          
│
├── templates/
│   └── index.html                  # interfejs użytkownika
│
├── lemmatization.py                # słownik lematyzacji
├── utils.py                        # TF-IDF, miary podobieństwa, wykresy, mapy
├── wikipedia_parser.py             # parsowanie HTML z Wikipedii
├── data_prep.py                    # przygotowanie bazy, spatial join dzielnic
├── app.py                          # Flask routing, logika wyszukiwania
│
├── apartments_sale.db              # baza SQLite (generowana przez data_prep.py)
└── requirements.txt                # zależności Python