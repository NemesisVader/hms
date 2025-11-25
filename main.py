import sys
from backend.app import app
from backend.seed import seed_admin, seed_all

if __name__ == "__main__":
    # If user passed "seed" argument
    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        with app.app_context():
            seed_all()  # Seed everything: admin, departments, sample data
        sys.exit(0)
    
    # If user passed "seed-admin" argument (admin only)
    if len(sys.argv) > 1 and sys.argv[1] == "seed-admin":
        with app.app_context():
            seed_admin()  # Seed admin only
        sys.exit(0)

    # Normal application run
    app.run(debug=True)
