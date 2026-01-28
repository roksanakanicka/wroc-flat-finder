from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# funkcja do pobierania danych z bazy z filtrami
def get_filtered_apartments(city=None, min_rooms=None, min_square=None, max_square=None,
                            min_price=None, max_price=None,
                            kindergarten=None, school=None, balcony=None, elevator=None,
                            min_floor=None, max_floor_count=None):
    connection = sqlite3.connect('apartments_sale.db')
    cursor = connection.cursor()

    query = 'SELECT * FROM apartments WHERE 1=1'
    params = []

    if city:
        query += ' AND city LIKE ?'
        params.append(f'%{city}%')
    if min_rooms:
        query += ' AND rooms >= ?'
        params.append(min_rooms)
    if min_square:
        query += ' AND squareMeters >= ?'
        params.append(min_square)
    if max_square:
        query += ' AND squareMeters <= ?'
        params.append(max_square)
    if min_price:
        query += ' AND price >= ?'
        params.append(min_price)
    if max_price:
        query += ' AND price <= ?'
        params.append(max_price)

    if kindergarten == 'yes':
        query += ' AND kindergartenDistance <= 1'
    if school == 'yes':
        query += ' AND schoolDistance <= 1'
    if balcony == 'yes':
        query += ' AND hasBalcony = "yes"'
    if elevator == 'yes':
        query += ' AND hasElevator = "yes"'
    if min_floor:
        query += ' AND floor >= ?'
        params.append(min_floor)
    if max_floor_count:
        query += ' AND floorCount <= ?'
        params.append(max_floor_count)
    
    query += ' LIMIT 50' # wynik ograniczony do 50 rekordów

    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    return results

# Strona główna
@app.route('/', methods=['GET', 'POST'])
def index():
    # pobiera wartości nawet jeśli puste
    filters = {
        'city': request.form.get('city', ''),
        'min_rooms': request.form.get('min_rooms', ''),
        'min_square': request.form.get('min_square', ''),
        'max_square': request.form.get('max_square', ''),
        'min_price': request.form.get('min_price', ''),
        'max_price': request.form.get('max_price', ''),
        'kindergarten': request.form.get('kindergarten', ''),
        'school': request.form.get('school', ''),
        'balcony': request.form.get('balcony', ''),
        'elevator': request.form.get('elevator', ''),
        'min_floor': request.form.get('min_floor', ''),
        'max_floor_count': request.form.get('max_floor_count', '')
    }

    # konwersja na int/float
    for key in ['min_rooms', 'min_square', 'max_square', 'min_price', 'max_price', 'min_floor', 'max_floor_count']:
        if filters[key]:
            filters[key] = float(filters[key]) if 'square' in key else int(filters[key])
        else:
            filters[key] = None
    
    print(filters['balcony'], filters['elevator'])


    results = get_filtered_apartments(**filters) if request.method == 'POST' else []

    return render_template('index.html', results=results, filters=filters)



if __name__ == '__main__':
    app.run(debug=True)

