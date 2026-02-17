import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

def db_connect():
    # SQLite подключение
    dir_path = Path(__file__).parent
    db_path = dir_path / "database.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    return conn, cur

def db_close(conn, cur):
    conn.commit()
    cur.close()
    conn.close()

def init_db():
    """Инициализация базы данных с тестовыми данными"""
    conn, cur = db_connect()
    
    # Создание таблицы пользователей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Создание таблицы книг
    cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            pages INTEGER NOT NULL,
            publisher TEXT NOT NULL,
            cover_image TEXT DEFAULT 'default_cover.jpg'
        )
    ''')
    
    # Создание администратора
    admin_password = generate_password_hash('admin123')
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            ('admin', admin_password, True)
        )
    except sqlite3.IntegrityError:
        pass  # Админ уже существует
    
    # Добавление тестовых книг (минимум 100)
    books_count = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if books_count == 0:
        sample_books = [
            ('Автостопом по галактике', 'Дуглас Адамс', 416, 'АСТ', 'Hitchhiker.jpg'),
            ('451 градус по Фаренгейту', 'Рэй Брэдбери', 256, 'Эксмо', 'Fahrenheit_451.jpg'),
            ('Дюна', 'Фрэнк Герберт', 896, 'АСТ', 'Dune.jpg'),
            ('1984', 'Джордж Оруэлл', 352, 'АСТ', '1984.jpg'),
            ('Долгая прогулка', 'Стивен Кинг (как Ричард Бахман)', 384, 'АСТ', 'Long_Walk.jpg'),
            ('Пикник на обочине', 'Аркадий и Борис Стругацкие', 224, 'АСТ', 'Roadside_Picnic.jpg'),
            ('Метро 2033', 'Дмитрий Глуховский', 544, 'АСТ', 'Metro_2033.jpg'),
            ('Метро 2034', 'Дмитрий Глуховский', 448, 'АСТ', 'Metro_2034.jpg'),
            ('Метро 2035', 'Дмитрий Глуховский', 384, 'АСТ', 'Metro_2035.jpg'),
            ('Кладбище домашних животных', 'Стивен Кинг', 480, 'АСТ', 'Pet_Sematary.jpg'),
            ('Противостояние', 'Стивен Кинг', 1248, 'АСТ', 'The_Stand.jpg'),
            ('Сияние', 'Стивен Кинг', 416, 'АСТ', 'The_Shining.jpg'),
            ('Метро 2033: Путевые знаки', 'Владимир Березин', 352, 'АСТ', 'Putevye_znaki.jpg'),
            ('Темная Башня: Стрелок', 'Стивен Кинг', 320, 'АСТ', 'Dark_Tower_Gunslinger.jpg'),
            ('Собачье сердце', 'Михаил Булгаков', 192, 'Фолио', 'dog_heart.jpg'),
            ('Бесы', 'Федор Достоевский', 768, 'Эксмо', 'demons.jpg'),
            ('Гроза', 'Александр Островский', 128, 'Эксмо', 'thunderstorm.jpg'),
            ('Тихий Дон', 'Михаил Шолохов', 1504, 'Эксмо', 'quiet_don.jpg'),
            ('Поднятая целина', 'Михаил Шолохов', 672, 'Азбука', 'virgin_soil.jpg'),
            ('Доктор Живаго', 'Борис Пастернак', 592, 'Фолио', 'doctor_zhivago.jpg'),
            ('Белая гвардия', 'Михаил Булгаков', 352, 'АСТ', 'white_guard.jpg'),
            ('Двенадцать стульев', 'Ильф и Петров', 416, 'Эксмо', 'twelve_chairs.jpg'),
            ('Золотой теленок', 'Ильф и Петров', 384, 'Азбука', 'golden_calf.jpg'),
            ('Как закалялась сталь', 'Николай Островский', 416, 'Фолио', 'how_steel_tempered.jpg'),
        ]
        # Добавим еще книг чтобы было больше 100
        label = ['A', 'B', 'C', 'D', 'E', 'F']
        for i in range(1, 101):
            sample_books.append(
                (f'Книга пример {i}', f'Автор {label[i%5]}', 200 + i * 10, f'Издательство {label[i%5]}', 'default_cover.jpg')
            )
        
        cur.executemany(
            "INSERT INTO books (title, author, pages, publisher, cover_image) VALUES (?, ?, ?, ?, ?)",
            sample_books
        )
    
    db_close(conn, cur)