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

if __name__ == "__main__":
    app.run(debug=True)