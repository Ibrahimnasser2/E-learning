"""
Clear all application data and re-seed Maha admin.
Usage (from api/):
  python clear_database.py
"""
from database import SessionLocal, create_tables, clear_application_data, ADMIN_EMAIL, ADMIN_USERNAME


def main():
    create_tables()
    db = SessionLocal()
    try:
        admin = clear_application_data(db, keep_admin=True)
        print("---")
        print(f"Admin email:    {ADMIN_EMAIL}")
        print(f"Admin username: {ADMIN_USERNAME}")
        print(f"Admin id:       {admin.id if admin else 'n/a'}")
        print("Database cleared. Maha account is ready.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
