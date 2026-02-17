from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from db.database import db_connect, db_close

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Получаем параметры из GET запроса
    page = request.args.get('page', 1, type=int)
    sort_field = request.args.get('sort_field', 'title')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Фильтры из GET параметров
    filters = {
        'title': request.args.get('title', ''),
        'author': request.args.get('author', ''),
        'publisher': request.args.get('publisher', ''),
        'pages_min': request.args.get('pages_min', ''),
        'pages_max': request.args.get('pages_max', '')
    }
    
    per_page = 21
    
    # Получаем уникальных авторов и издателей из БД
    conn, cur = db_connect()
    
    # Уникальные авторы
    cur.execute("SELECT DISTINCT author FROM books ORDER BY author")
    authors = [row['author'] for row in cur.fetchall()]
    
    # Уникальные издательства
    cur.execute("SELECT DISTINCT publisher FROM books ORDER BY publisher")
    publishers = [row['publisher'] for row in cur.fetchall()]
    
    # Построение SQL запроса для книг
    where_conditions = []
    query_params = []
    
    if filters['title']:
        where_conditions.append("title LIKE ?")
        query_params.append(f"%{filters['title']}%")
    
    if filters['author']:
        where_conditions.append("author = ?")  # Точное совпадение для выпадающего списка
        query_params.append(filters['author'])
    
    if filters['publisher']:
        where_conditions.append("publisher = ?")  # Точное совпадение для выпадающего списка
        query_params.append(filters['publisher'])
    
    if filters['pages_min']:
        where_conditions.append("pages >= ?")
        query_params.append(int(filters['pages_min']))
    
    if filters['pages_max']:
        where_conditions.append("pages <= ?")
        query_params.append(int(filters['pages_max']))
    
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    # Подсчет общего количества
    count_query = f"SELECT COUNT(*) as total FROM books {where_clause}"
    cur.execute(count_query, query_params)
    total_count = cur.fetchone()['total']
    
    # Получение книг с пагинацией
    offset = (page - 1) * per_page
    order_clause = f"ORDER BY {sort_field} {sort_order.upper()}"
    
    books_query = f"""
        SELECT * FROM books 
        {where_clause} 
        {order_clause} 
        LIMIT ? OFFSET ?
    """
    
    query_params.extend([per_page, offset])
    cur.execute(books_query, query_params)
    books = cur.fetchall()
    
    db_close(conn, cur)
    
    has_next = (page * per_page) < total_count
    
    return render_template('index.html', 
                         books=books,
                         current_page=page,
                         total_count=total_count,
                         has_next=has_next,
                         sort_field=sort_field,
                         sort_order=sort_order,
                         filters=filters,
                         authors=authors,
                         publishers=publishers)