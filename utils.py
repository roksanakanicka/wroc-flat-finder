import math
import sqlite3
import io
import base64
import folium
from folium.plugins import MarkerCluster
import matplotlib
from collections import Counter
from functools import lru_cache
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from lemmatization import lemmatize_text

# ========== BAZA DANYCH I LOGIKA ==========

def get_db_connection():
    conn = sqlite3.connect('apartments_sale.db')
    conn.row_factory = sqlite3.Row
    return conn

@lru_cache(maxsize=1)
def load_documents_cached():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, document FROM apartments')
    rows = cursor.fetchall()
    conn.close()
    
    ids = [row['id'] for row in rows]
    documents = [row['document'] for row in rows]
    return ids, documents

def analyze_districts():
    """statystyki ogólne rynku z bazy danych"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT price, squareMeters FROM apartments')
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {'avg_price': 0, 'avg_sqm': 0, 'avg_price_per_sqm': 0, 'total_count': 0}

    prices = [row['price'] for row in rows]
    sqms = [row['squareMeters'] for row in rows]
    
    total_price = sum(prices)
    total_sqm = sum(sqms)
    
    return {
        'avg_price': total_price / len(prices),
        'avg_sqm': total_sqm / len(sqms),
        'avg_price_per_sqm': total_price / total_sqm if total_sqm > 0 else 0,
        'total_count': len(prices)
    }

def get_filtered_apartments(min_rooms=None, min_square=None, max_square=None,
                            min_price=None, max_price=None, min_build_year=None, 
                            max_centre_distance=None, balcony=None, elevator=None, 
                            parking=None, min_floor=None, max_floor_count=None, 
                            district=None, sort_by=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM apartments WHERE 1=1'
    params = []
    
    if min_rooms is not None:
        query += ' AND rooms >= ?'
        params.append(min_rooms)
    if min_square is not None:
        query += ' AND squareMeters >= ?'
        params.append(min_square)
    if max_square is not None:
        query += ' AND squareMeters <= ?'
        params.append(max_square)
    if min_price is not None:
        query += ' AND price >= ?'
        params.append(min_price)
    if max_price is not None:
        query += ' AND price <= ?'
        params.append(max_price)
    if min_floor is not None:
        query += ' AND floor >= ?'
        params.append(min_floor)
    if max_floor_count is not None:
        query += ' AND floorCount <= ?'
        params.append(max_floor_count)
        
    if min_build_year is not None:
        query += ' AND buildYear >= ?'
        params.append(min_build_year)
    if max_centre_distance is not None:
        query += ' AND centreDistance <= ?'
        params.append(max_centre_distance)
    
    if balcony == 'yes':
        query += ' AND hasBalcony = "yes"'
    if elevator == 'yes':
        query += ' AND hasElevator = "yes"'
    if parking == 'yes':
        query += ' AND hasParkingSpace = "yes"'
    
    if district is not None and district != '':
        query += ' AND district_name = ?'
        params.append(district)
    
    valid_sort = ['rooms', 'squareMeters', 'floor', 'floorCount', 'price']
    
    if sort_by in valid_sort:
        query += f' ORDER BY {sort_by} ASC'
    
    query += ' LIMIT 50'
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]

# ========== TF-IDF I PODOBIEŃSTWA ==========

def preprocess_query(query):
    """Lematyzuje, potem łączy 'blisko/bardzo blisko/obok' z następnym słowem"""
    # lematyzacja
    lemmatized = lemmatize_text(query)
    
    # sklejanie
    words = lemmatized.split()
    result = []
    i = 0
    
    while i < len(words):
        # bardzo blisko X
        if i < len(words) - 2 and words[i] == "bardzo" and words[i+1] == "blisko":
            result.append(f"bardzo_blisko_{words[i+2]}")
            i += 3
        # blisko X
        elif i < len(words) - 1 and words[i] == "blisko":
            result.append(f"blisko_{words[i+1]}")
            i += 2
        # obok X
        elif i < len(words) - 1 and words[i] == "obok":
            result.append(f"blisko_{words[i+1]}")
            i += 2
        else:
            result.append(words[i])
            i += 1
    
    return " ".join(result)

def compute_tfidf(documents):
    N = len(documents)
    tokenized_docs = [doc.split() for doc in documents]
    
    df_counts = Counter()
    for tokens in tokenized_docs:
        for token in set(tokens):
            df_counts[token] += 1
    
    tfidf_docs = []
    for tokens in tokenized_docs:
        tf_counts = Counter(tokens)
        max_tf = max(tf_counts.values()) if tf_counts else 1
        
        tfidf = {
            token: (tf / max_tf) * math.log10(N / df_counts[token]) 
            for token, tf in tf_counts.items()
        }
        tfidf_docs.append(tfidf)
    
    return tfidf_docs, tokenized_docs, df_counts, N

def search_tfidf(query, documents, tfidf_docs, top_n=25):
    query = preprocess_query(query)
    query_tokens = lemmatize_text(query).split()
    scores = []
    
    for idx, doc_tfidf in enumerate(tfidf_docs):
        score = sum(doc_tfidf.get(token, 0) for token in query_tokens)
        if score > 0:
            scores.append((idx, score))
    
    scores.sort(key=lambda x: x[1], reverse=True)
    return [i for i, _ in scores[:top_n]]

def cosine_similarity(vec1, vec2):
    all_tokens = set(vec1.keys()) | set(vec2.keys())
    dot_product = sum(vec1.get(t, 0) * vec2.get(t, 0) for t in all_tokens)
    mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
    if mag1 == 0 or mag2 == 0: 
        return 0
    return dot_product / (mag1 * mag2)

def jaccard_similarity(vec1, vec2):
    all_tokens = set(vec1.keys()) | set(vec2.keys())
    
    numerator = sum(vec1.get(t, 0) * vec2.get(t, 0) for t in all_tokens)
    sum_sq1 = sum(v**2 for v in vec1.values())
    sum_sq2 = sum(v**2 for v in vec2.values())
    
    denominator = sum_sq1 + sum_sq2 - numerator
    return numerator / denominator if denominator > 0 else 0

def dice_similarity(vec1, vec2):
    all_tokens = set(vec1.keys()) | set(vec2.keys())
    
    numerator = 2 * sum(vec1.get(t, 0) * vec2.get(t, 0) for t in all_tokens)
    sum_sq1 = sum(v**2 for v in vec1.values())
    sum_sq2 = sum(v**2 for v in vec2.values())
    
    denominator = sum_sq1 * sum_sq2
    return numerator / denominator if denominator > 0 else 0

def calculate_similarity_for_doc(query, doc_tfidf, doc_tokens_set, df_counts, N):
    # obliczenie tf-idf dla query takie samo jak dla dokumentów
    processed_query = preprocess_query(query) 
    query_tokens = lemmatize_text(processed_query).split()
    
    tf_counts = Counter(query_tokens)
    max_tf = max(tf_counts.values()) if tf_counts else 1
    
    query_tfidf = {
        token: (tf / max_tf) * math.log10(N / df_counts.get(token, N))
        for token, tf in tf_counts.items()
    }
    
    return {
        'cosine': cosine_similarity(query_tfidf, doc_tfidf),
        'jaccard': jaccard_similarity(query_tfidf, doc_tfidf),
        'dice': dice_similarity(query_tfidf, doc_tfidf)
    }

# ========== WIZUALIZACJE ==========

def create_charts(results):
    charts = {}
    if not results:
        return charts
    
    prices = [r['price'] for r in results if r.get('price') is not None]
    if not prices:
        return charts

    # histogram cen
    plt.figure(figsize=(10, 6))
    prices = [r['price'] for r in results]
    plt.hist(prices, bins=15, color='steelblue', edgecolor='black')
    plt.xlabel('Cena (zł)')
    plt.ylabel('Liczba ofert')
    ax = plt.gca()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', ' ')))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    charts['price_hist'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    # scatter plot
    plt.figure(figsize=(10, 6))
    squares = [r['squareMeters'] for r in results]
    plt.scatter(squares, prices, alpha=0.6, color='coral', s=50)
    plt.xlabel('Metraż (m²)')
    plt.ylabel('Cena (zł)')
    plt.grid(alpha=0.3)
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', ' ')))
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    charts['scatter'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    # bar chart pokoi
    plt.figure(figsize=(10, 6))
    rooms_count = Counter([r['rooms'] for r in results])
    rooms_sorted = sorted(rooms_count.items())
    
    plt.bar([str(int(r)) for r, _ in rooms_sorted], 
            [c for _, c in rooms_sorted], 
            color='lightgreen', edgecolor='black', width=0.6)
    plt.xlabel('Liczba pokoi')
    plt.ylabel('Liczba ofert')
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    charts['rooms_bar'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return charts

def create_map(results):
    # mapa Folium
    if not results:
        return None
    
    locs = [(r['latitude'], r['longitude'], r['price'], r['rooms'], i+1) 
            for i, r in enumerate(results) 
            if r.get('latitude') is not None and r.get('longitude') is not None 
            and r.get('price') is not None and r.get('rooms') is not None]
    
    if not locs:
        return None

    lat_avg = sum([x[0] for x in locs]) / len(locs)
    lon_avg = sum([x[1] for x in locs]) / len(locs)
    
    m = folium.Map(location=[lat_avg, lon_avg], zoom_start=12)
    
    # grupowanie z MarkerCluster
    marker_cluster = MarkerCluster().add_to(m)
    
    for lat, lon, price, rooms, num in locs:
        popup_text = f"Nr: {num}<br>Cena: {int(price):,} zł<br>Pokoje: {int(rooms)}".replace(',', ' ')
        popup = folium.Popup(popup_text, max_width=300, min_width=150)
        folium.Marker([lat, lon], popup=popup).add_to(marker_cluster)
    
    return m._repr_html_()

def get_all_districts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT district_name 
        FROM apartments 
        WHERE district_name IS NOT NULL 
        ORDER BY district_name
    """)
    districts = [row['district_name'] for row in cursor.fetchall()]
    conn.close()
    return districts