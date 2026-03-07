from app import create_app
from app.auth import create_default_admin
from app.models import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        create_default_admin()
    app.run(debug=True, host='0.0.0.0', port=5000)
