from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from db.database import db_connect, db_close
from werkzeug.utils import secure_filename
import os
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# Настройки для загрузки файлов
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 
                              os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'pic'))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Создаем папку если её нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    result = '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    print(f"Allowed file check: {filename} -> {result}")  # Отладка
    return result

def generate_unique_filename(filename):
    """Генерирует уникальное имя файла с timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    # Получаем расширение из оригинального имени
    original_ext = os.path.splitext(filename)[1].lower()
    
    # Проверяем что расширение допустимое, иначе используем .jpg
    if not original_ext or original_ext[1:] not in ALLOWED_EXTENSIONS:
        original_ext = '.jpg'
    
    # Генерируем случайное имя + timestamp
    import uuid
    random_name = str(uuid.uuid4())[:8]  # первые 8 символов UUID
    print(f"book_{random_name}_{timestamp}{original_ext}")
    return f"book_{random_name}_{timestamp}{original_ext}"

@admin_bp.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if not session.get('is_admin'):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        pages = request.form.get('pages', '').strip()
        publisher = request.form.get('publisher', '').strip()
        
        # Значение по умолчанию для обложки
        cover_image = 'default_cover.jpg'
        
        # Подключаемся к БД для проверки дубликатов
        conn, cur = db_connect()
        
        try:
            # Проверяем нет ли такой книги уже
            cur.execute(
                "SELECT id FROM books WHERE title = ? AND author = ? AND publisher = ?",
                (title, author, publisher)
            )
            existing_book = cur.fetchone()
            
            if existing_book:
                flash('Такая книга уже существует в библиотеке!', 'error')
                db_close(conn, cur)
                return render_template('add_book.html')
            
            # Обработка загруженного файла
            if 'cover_image' in request.files:
                file = request.files['cover_image']
                print(f"File received: {file}")  # Отладка
                print(f"File filename: {file.filename}")  # Отладка
                print(f"File content type: {file.content_type}")  # Отладка
                
                # Проверяем что файл действительно загружен и имеет допустимое расширение
                if file and file.filename and file.filename != '':
                    print(f"File is not empty, checking extension...")  # Отладка
                    
                    if allowed_file(file.filename):
                        print(f"File extension is allowed")  # Отладка
                        
                        filename = generate_unique_filename(file.filename)
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        
                        print(f"Attempting to save to: {file_path}")  # Отладка
                        print(f"Upload folder: {UPLOAD_FOLDER}")  # Отладка
                        print(f"Full path exists: {os.path.exists(file_path)}")  # Отладка
                        
                        # Сохраняем файл
                        try:
                            file.save(file_path)
                            print(f"File save attempted, checking if exists...")  # Отладка
                            
                            # Проверяем что файл действительно сохранился
                            if os.path.exists(file_path):
                                file_size = os.path.getsize(file_path)
                                print(f"File successfully saved! Size: {file_size} bytes")  # Отладка
                                cover_image = filename
                                flash('Обложка успешно загружена!', 'success')
                            else:
                                print("ERROR: File was not saved!")  # Отладка
                                flash('Ошибка: файл не был сохранен на сервере', 'error')
                                
                        except Exception as e:
                            print(f"ERROR during file save: {e}")  # Отладка
                            flash(f'Ошибка при сохранении файла: {str(e)}', 'error')
                            
                    else:
                        print(f"File extension not allowed: {file.filename}")  # Отладка
                        flash('Недопустимый формат файла. Используйте JPG, PNG или GIF.', 'error')
                else:
                    print("File is empty or no filename")  # Отладка
            
            # Валидация обязательных полей
            if not all([title, author, pages, publisher]):
                flash('Все обязательные поля должны быть заполнены', 'error')
                db_close(conn, cur)
                return render_template('add_book.html')
            
            # Валидация числовых полей
            try:
                pages_int = int(pages)
                if pages_int <= 0:
                    raise ValueError("Pages must be positive")
            except (ValueError, TypeError):
                flash('Количество страниц должно быть положительным числом', 'error')
                db_close(conn, cur)
                return render_template('add_book.html')
            
            # Добавляем книгу в БД
            cur.execute(
                "INSERT INTO books (title, author, pages, publisher, cover_image) VALUES (?, ?, ?, ?, ?)",
                (title, author, pages_int, publisher, cover_image)
            )
            
            db_close(conn, cur)
            flash('Книга успешно добавлена!', 'success')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            db_close(conn, cur)
            flash(f'Ошибка базы данных: {str(e)}', 'error')
    
    return render_template('add_book.html')

@admin_bp.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if not session.get('is_admin'):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
    
    conn, cur = db_connect()
    
    try:
        # Получаем текущую книгу
        cur.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        book = cur.fetchone()
        
        if not book:
            flash('Книга не найдена', 'error')
            db_close(conn, cur)
            return redirect(url_for('main.index'))
        
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            author = request.form.get('author', '').strip()
            pages = request.form.get('pages', '').strip()
            publisher = request.form.get('publisher', '').strip()
            
            # По умолчанию оставляем текущую обложку
            cover_image = book['cover_image']
            
            # Проверяем нет ли дубликата (исключая текущую книгу)
            cur.execute(
                "SELECT id FROM books WHERE title = ? AND author = ? AND publisher = ? AND id != ?",
                (title, author, publisher, book_id)
            )
            existing_book = cur.fetchone()
            
            if existing_book:
                flash('Такая книга уже существует в библиотеке!', 'error')
                return render_template('edit_book.html', book=book)
            
            # Обработка новой загруженной обложки
            if 'cover_image' in request.files:
                file = request.files['cover_image']
                # Проверяем что файл действительно загружен
                if file and file.filename and file.filename != '':
                    if allowed_file(file.filename):
                        filename = generate_unique_filename(file.filename)
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        
                        # Сохраняем новый файл
                        file.save(file_path)
                        cover_image = filename
                        flash('Новая обложка успешно загружена!', 'success')
                    else:
                        flash('Недопустимый формат файла. Используйте JPG, PNG или GIF.', 'error')
                        return render_template('edit_book.html', book=book)
            
            # Валидация обязательных полей
            if not all([title, author, pages, publisher]):
                flash('Все обязательные поля должны быть заполнены', 'error')
                return render_template('edit_book.html', book=book)
            
            # Валидация числовых полей
            try:
                pages_int = int(pages)
                if pages_int <= 0:
                    raise ValueError("Pages must be positive")
            except (ValueError, TypeError):
                flash('Количество страниц должно быть положительным числом', 'error')
                return render_template('edit_book.html', book=book)
            
            # Обновляем книгу в БД
            cur.execute(
                "UPDATE books SET title = ?, author = ?, pages = ?, publisher = ?, cover_image = ? WHERE id = ?",
                (title, author, pages_int, publisher, cover_image, book_id)
            )
            
            db_close(conn, cur)
            flash('Книга успешно обновлена!', 'success')
            return redirect(url_for('main.index'))
        
        # GET запрос - показываем форму с текущими данными
        return render_template('edit_book.html', book=book)
        
    except Exception as e:
        db_close(conn, cur)
        flash(f'Ошибка: {str(e)}', 'error')
        return redirect(url_for('main.index'))

# ДОБАВЛЯЕМ УДАЛЕНИЕ КНИГИ
@admin_bp.route('/admin/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if not session.get('is_admin'):
        flash('Доступ запрещен', 'error')
        return redirect(url_for('main.index'))
    
    conn, cur = db_connect()
    
    # Проверяем существование книги
    cur.execute("SELECT id FROM books WHERE id = ?", (book_id,))
    if not cur.fetchone():
        flash('Книга не найдена', 'error')
        db_close(conn, cur)
        return redirect(url_for('main.index'))
    
    try:
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
        db_close(conn, cur)
        flash('Книга успешно удалена!', 'success')
    except Exception as e:
        db_close(conn, cur)
        flash(f'Ошибка базы данных: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))