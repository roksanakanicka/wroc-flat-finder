from flask import Flask, render_template, request

from utils import (
    compute_tfidf, search_tfidf, get_db_connection, analyze_districts,
    load_documents_cached, get_filtered_apartments, create_charts,
    create_map, calculate_similarity_for_doc, get_all_districts
)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():    
    doc_ids, documents = load_documents_cached()
    tfidf_docs, tokenized_docs, df_counts, N = compute_tfidf(documents)
    
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
        'parking': request.form.get('parking'),
        'district': request.form.get('district')
    }

    sort_by = request.form.get('sort_by')
    search_query = request.form.get('search', '').strip()
    
    results = []
    map_html = None
    charts = {}
    
    if request.method == 'POST':
        if search_query:
            top_indices = search_tfidf(search_query, documents, tfidf_docs, top_n=20)
            
            if top_indices:
                filtered_ids = [doc_ids[i] for i in top_indices]
                placeholders = ','.join(['?'] * len(filtered_ids))
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM apartments WHERE id IN ({placeholders})', filtered_ids)
                rows = cursor.fetchall()
                conn.close()
                
                id_to_row = {row['id']: dict(row) for row in rows}
                results = []
                
                # obliczenie miary dla każdego wyniku
                for idx, _id in enumerate(filtered_ids):
                    if _id in id_to_row:
                        result = id_to_row[_id]
                        orig_idx = top_indices[idx]
                        doc_tokens_set = set(tokenized_docs[orig_idx])
                        sims = calculate_similarity_for_doc(search_query, tfidf_docs[orig_idx], 
                                                           doc_tokens_set, df_counts, N)
                        result['cosine_sim'] = sims['cosine']
                        result['jaccard_sim'] = sims['jaccard']
                        result['dice_sim'] = sims['dice']
                        results.append(result)
                
                # Sortowanie po miarach podobieństwa
                similarity_sort = request.form.get('similarity_sort')
                if similarity_sort == 'cosine':
                    results.sort(key=lambda x: x.get('cosine_sim', 0), reverse=True)
                elif similarity_sort == 'jaccard':
                    results.sort(key=lambda x: x.get('jaccard_sim', 0), reverse=True)
                elif similarity_sort == 'dice':
                    results.sort(key=lambda x: x.get('dice_sim', 0), reverse=True)
            else:
                results = []
        else:
            results = get_filtered_apartments(**filters, sort_by=sort_by)
        
        if results:
            map_html = create_map(results)
            charts = create_charts(results)
    
    district_stats = analyze_districts()
    
    from wikipedia_parser import get_city_description
    city_stats = get_city_description()
    
    similarity_sort = request.form.get('similarity_sort')
    
    try:
        all_districts = get_all_districts()
    except Exception as e:
        all_districts = []
    
    return render_template('index.html',
                       results=results,
                       filters=filters,
                       sort_by=sort_by,
                       similarity_sort=similarity_sort,
                       map_html=map_html,
                       charts=charts,
                       city_stats=city_stats,
                       district_stats=district_stats,
                       search_query=search_query,
                       enumerate=enumerate,
                       all_districts=all_districts)


if __name__ == '__main__':
    app.run(debug=True)