from app import create_app, socketio, db

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Clear existing data and create new tables."""
    from app.auth import create_default_admin
    with app.app_context():
        db.create_all()
        create_default_admin()
        print("Initialized the database.")

if __name__ == '__main__':
    # Use SocketIO run instead of app.run for WebSocket support
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
