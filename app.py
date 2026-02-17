from flask import Flask
import os
from db.database import init_db

from routers.auth_routers import auth_bp
from routers.main_routers import main_bp
from routers.admin_routers import admin_bp

app = Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
