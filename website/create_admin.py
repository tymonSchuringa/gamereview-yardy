from website import db
from website.models import User
from werkzeug.security import generate_password_hash

admin = User(
    username="admin",
    email="admin@example.com",
    password_hash=generate_password_hash("admin123"),
    is_admin=True
)

db.session.add(admin)
db.session.commit()
print("Admin user aangemaakt!")
