from flask import Flask, render_template, request
from wikipedia_parser import get_city_description

from utils import (
    compute_tfidf, search_tfidf, get_db_connection, analyze_districts,
    load_documents_cached, get_filtered_apartments, create_charts,
    create_map, calculate_similarities
)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    doc_ids, documents = load_documents_cached()
    tfidf_docs, tokenized_docs = compute_tfidf(documents)
    
    filters = {
        'min_rooms': request.form.get('min_rooms', type=int),
        'min_square': request.form.get('min_square', type=float),
        'max_square': request.form.get('max_square', type=float),
        'min_price': request.form.get('min_price', type=float),
        'max_price': request.form.get('max_price', type=float),
        'min_build_year': request.form.get('min_build_year', type=int),
        'max_centre_distance': request.form.get('max_centre_distance', type=float),
        'min_floor': request.form.get('min_floor', type=int),
        'max_floor_count': request.form.get('max_floor_count', type=int),
        'balcony': request.form.get('balcony'),
        'elevator': request.form.get('elevator'),
        'parking': request.form.get('parking')
    }
    
    sort_by = request.form.get('sort_by')
    search_query = request.form.get('search', '').strip()
    
    results = []
    map_html = None
    charts = {}
    similarities = []
    
    if request.method == 'POST':
        if search_query:
            # wyszukiwanie TF-IDF
            top_indices = search_tfidf(search_query, documents, tfidf_docs, top_n=50)
            
            if top_indices:
                filtered_ids = [doc_ids[i] for i in top_indices]
                placeholders = ','.join(['?'] * len(filtered_ids))
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM apartments WHERE id IN ({placeholders})', filtered_ids)
                rows = cursor.fetchall()
                conn.close()
                
                id_to_row = {row['id']: dict(row) for row in rows}
                results = [id_to_row[_id] for _id in filtered_ids if _id in id_to_row]
                
                top_10_indices = top_indices[:10]
                similarities = calculate_similarities(search_query, 
                                                   [tfidf_docs[i] for i in top_10_indices])
            else:
                results = []
        else:
            # zwykłe filtrowanie SQL
            results = get_filtered_apartments(**filters, sort_by=sort_by)
        
        if results:
            map_html = create_map(results)
            charts = create_charts(results)
    
    district_stats = analyze_districts()
    
    wiki_data = None
    if request.form.get('show_wiki'):
        wiki_data = get_city_description()
    
    return render_template('index.html',
                          results=results,
                          filters=filters,
                          sort_by=sort_by,
                          map_html=map_html,
                          charts=charts,
                          similarities=similarities,
                          wiki_data=wiki_data,
                          district_stats=district_stats,
                          enumerate=enumerate)

if __name__ == '__main__':
    app.run(debug=True)