from app import app
from models import db, User

with app.app_context():
    db.create_all()
    def ensure(u, p, r):
        if not User.query.filter_by(username=u).first():
            user = User(username=u, role=r)
            user.set_password(p)
            db.session.add(user)
            print(f"created: {u}/{p} ({r})")
    ensure("admin", "admin123", "admin")
    ensure("user1", "user123", "user")
    ensure("user2", "user123", "user")
    db.session.commit()
    print("done.")
