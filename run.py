from werkzeug.security import generate_password_hash
import click

from app import create_app, db
from app.models import User
import os

app = create_app()

@app.cli.command("init-db")
def init_db():
    """CLI Command: flask init-db[cite: 2]"""
    # Create required directories for the pipeline[cite: 1, 2]
    folders = ['data/master', 'data/temp', 'data/verified', 'data/review', 'logs']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")

    db.create_all()
    print("Initialized the local SQLite database (uc_audit.db).")

@app.cli.command("create-user")
@click.argument('username')
@click.argument('password')
@click.option('--role', default='consultant', help='Role: consultant or admin')
def create_user(username, password, role):
    """CLI Command: flask create-user <username> <password> [--role admin]"""
    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists.")
        return
    
    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    print(f"User '{username}' created successfully with role '{role}'.")

if __name__ == "__main__":
    app.run(debug=True)