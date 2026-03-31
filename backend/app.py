import os, sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_cors import CORS
from config import Config

from api.api                    import api_bp
from routes.auth_routes         import auth_bp
from routes.user_routes         import user_bp
from routes.equipment_routes    import equipment_bp
from routes.booking_routes      import booking_bp
from routes.group_routes        import group_bp
from routes.rating_routes       import rating_bp
from routes.tracking_routes     import tracking_bp
from routes.ml_routes           import ml_bp
from routes.weather_routes      import weather_bp
from routes.notification_routes import notification_bp
from routes.payment_routes      import payment_bp
from routes.ai_routes           import ai_bp

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__),"../frontend/templates"),
        static_folder=os.path.join(os.path.dirname(__file__),"../frontend/static")
    )
    CORS(app, resources={r"/api/*":{"origins":"*"}})

    app.register_blueprint(api_bp,           url_prefix="/api")
    app.register_blueprint(auth_bp,          url_prefix="/api/auth")
    app.register_blueprint(user_bp,          url_prefix="/api/users")
    app.register_blueprint(equipment_bp,     url_prefix="/api/equipment")
    app.register_blueprint(booking_bp,       url_prefix="/api/bookings")
    app.register_blueprint(group_bp,         url_prefix="/api/groups")
    app.register_blueprint(rating_bp,        url_prefix="/api/ratings")
    app.register_blueprint(tracking_bp,      url_prefix="/api/tracking")
    app.register_blueprint(ml_bp,            url_prefix="/api/ml")
    app.register_blueprint(weather_bp,       url_prefix="/api/weather")
    app.register_blueprint(notification_bp,  url_prefix="/api/notifications")
    app.register_blueprint(payment_bp,       url_prefix="/api/payment")
    app.register_blueprint(ai_bp,            url_prefix="/api/ai")

    frontend_root = os.path.join(os.path.dirname(__file__),"../frontend")

    @app.route("/manifest.json")
    def manifest(): return send_from_directory(frontend_root,"manifest.json")

    @app.route("/service-worker.js")
    def sw(): return send_from_directory(
        os.path.join(frontend_root,"static"),"service-worker.js",
        mimetype="application/javascript")

    pages = {
        "/":"index.html","/login":"login.html","/register":"register.html",
        "/booking":"booking.html","/group-booking":"group_booking.html",
        "/tracking":"tracking.html","/rating":"rating.html",
        "/dashboard/farmer":"dashboard_farmer.html",
        "/dashboard/owner":"dashboard_owner.html",
        "/offline":"offline.html","/payment":"payment.html",
        "/notifications":"notifications.html","/profile":"profile.html",
        "/about":"about.html",
    }
    for path, tmpl in pages.items():
        app.add_url_rule(path, endpoint=path, view_func=lambda t=tmpl: render_template(t))

    @app.route("/api/health")
    def health(): return jsonify({"status":"ok","version":"2.0.0","app":"TractoNow"})

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"): return jsonify({"success":False,"message":"Not found"}),404
        return render_template("index.html"),404

    @app.errorhandler(500)
    def err(e):
        if request.path.startswith("/api/"): return jsonify({"success":False,"message":"Server error"}),500
        return render_template("index.html"),500

    return app

if __name__ == "__main__":
    app = create_app()
    print("\n🚜 TractoNow v2.0 → http://localhost:5000\n")
    app.run(debug=Config.DEBUG, port=Config.PORT)
