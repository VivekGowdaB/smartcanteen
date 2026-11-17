"""Application WSGI entrypoint."""
import os
import sys
from app import create_app
from app.extensions import db

env_name = os.environ.get("FLASK_ENV", "development")
app = create_app(env_name)

# Ensure database tables exist upon startup
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")

    print("\n" + "=" * 60)
    print("  Smart Canteen Ordering System is Running!")
    print(f"  --> Open in Browser: http://localhost:{port} (or http://127.0.0.1:{port})")
    print("=" * 60)
    print("  Demo Login Accounts:")
    print("    Admin:   admin     / Admin@123")
    print("    Staff:   staff     / Staff@123")
    print("    Student: student1  / Student@123  (Wallet: Rs 500)")
    print("    Student: student2  / Student@123  (Wallet: Rs 350)")
    print("=" * 60 + "\n", flush=True)

    try:
        app.run(host=host, port=port, debug=False, use_reloader=False)
    except OSError as e:
        print(f"[!] Port {port} encountered: {e}")
        fallback_port = 5050
        print(f"[*] Retrying on fallback port: http://localhost:{fallback_port}", flush=True)
        app.run(host=host, port=fallback_port, debug=False, use_reloader=False)
