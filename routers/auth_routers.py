from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from db.database import db_connect, db_close
import sqlite3

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn, cur = db_connect()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        db_close(conn, cur)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Валидация
        if not all(c.isalnum() or c in '._-' for c in username):
            flash('Логин может содержать только латинские буквы, цифры и символы ._-', 'error')
            return render_template('register.html')
        
        conn, cur = db_connect()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            flash('Пользователь с таким логином уже существует', 'error')
            db_close(conn, cur)
            return render_template('register.html')
        
        password_hash = generate_password_hash(password)
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                (username, password_hash, False)
            )
            db_close(conn, cur)
            flash('Регистрация успешна! Теперь войдите.', 'success')
            return redirect(url_for('auth.login'))
        except sqlite3.Error:
            flash('Ошибка базы данных', 'error')
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))