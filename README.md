<div align="center">

# 🚜 TractoNow

### Smart Agri Equipment Sharing Platform

*Connecting farmers with equipment owners across rural Telangana & Andhra Pradesh*

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat-square&logo=mongodb)
![ML](https://img.shields.io/badge/ML-RandomForest-F7931E?style=flat-square)
![PWA](https://img.shields.io/badge/PWA-Ready-5A0FC8?style=flat-square)
![Languages](https://img.shields.io/badge/Languages-EN%20%7C%20TE%20%7C%20HI-green?style=flat-square)

</div>

---

## 👥 Development Team

| Name | Role |
|------|------|
| **M. Vijay** | Backend Developer — Flask, MongoDB, ML Models |
| **T. Yukthesh** | Frontend Developer — HTML, CSS, JavaScript, UI/UX |
| **P. Sravan** | AI/ML Developer — Scikit-learn, Demand Prediction |
| **A. Srinivas** | Full Stack Developer — API Design, GPS Tracking, PWA |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Crop Demand** | ML-based seasonal demand prediction (85% accuracy) |
| 📍 **Live GPS Tracking** | Real-time equipment location with OSRM road routing |
| 👥 **Group Booking** | Share one tractor with 2–5 farmers, auto cost splitting |
| 🌦️ **Weather Forecast** | 5-day forecast based on farmer's registered district |
| 🗣️ **Multilingual** | Telugu, Hindi, English voice input and UI |
| 💳 **Payments** | UPI, Card, Net Banking (demo) |
| 🔔 **Seasonal Alerts** | Month-based crop season notifications |
| ⏰ **10-min Cancel Window** | Farmer can cancel within 10 min of owner acceptance |
| 📱 **PWA** | Install as app on Android/iOS |
| 🗺️ **Turn-by-Turn Directions** | Road-based routing with navigation steps |

---

## 🏗️ Tech Stack

```
Backend          Flask 3.0 + PyMongo + PyJWT + bcrypt
Database         MongoDB (Atlas for production)
ML               Scikit-learn RandomForestClassifier
Maps/Routing     Leaflet.js + OpenStreetMap + OSRM (free, no API key)
Weather          OpenWeatherMap API (free tier)
Frontend         Jinja2 + Vanilla JS + CSS3
PWA              Service Worker + Web App Manifest
Hosting          Render.com (backend) + MongoDB Atlas (database)
```

---

## 📁 Project Structure

```
tractonow/
├── backend/
│   ├── app.py                 ← Flask app factory
│   ├── config.py              ← Configuration
│   ├── requirements.txt       ← Python dependencies
│   ├── .env.example           ← Environment variables template
│   ├── api/
│   │   └── api.py             ← API docs endpoint
│   ├── database/
│   │   ├── db.py              ← MongoDB connection + indexes
│   │   └── seed.py            ← Sample data (safe, never wipes)
│   ├── models/
│   │   ├── train_model.py     ← ML model training
│   │   ├── predict.py         ← Demand prediction inference
│   │   └── preprocess.py      ← Feature engineering
│   ├── routes/                ← 13 API blueprints
│   │   ├── auth_routes.py     ← Register, Login, Forgot Password
│   │   ├── equipment_routes.py
│   │   ├── booking_routes.py
│   │   ├── group_routes.py
│   │   ├── tracking_routes.py ← Real GPS + OSRM routing
│   │   ├── payment_routes.py
│   │   ├── weather_routes.py
│   │   ├── notification_routes.py
│   │   ├── ai_routes.py       ← AI crop demand
│   │   └── ml_routes.py
│   └── utils/
│       ├── auth.py
│       ├── pricing.py
│       ├── weather.py
│       └── translator.py
└── frontend/
    ├── templates/             ← 15 Jinja2 HTML pages
    │   ├── base.html          ← Navbar, background video, translator
    │   ├── index.html
    │   ├── login.html         ← Forgot password
    │   ├── register.html
    │   ├── dashboard_farmer.html
    │   ├── dashboard_owner.html
    │   ├── booking.html
    │   ├── group_booking.html
    │   ├── tracking.html      ← Live map + directions
    │   ├── payment.html
    │   ├── notifications.html
    │   ├── profile.html
    │   ├── rating.html
    │   ├── about.html
    │   └── offline.html
    └── static/
        ├── css/style.css
        ├── js/
        │   ├── main.js
        │   ├── booking.js
        │   ├── tracking.js
        │   ├── group.js
        │   ├── rating.js
        │   └── pwa.js
        ├── images/
        │   ├── fields.jpg     ← Login page background (add manually)
        │   ├── machines.jpg   ← About page background (add manually)
        │   └── equipment/     ← Uploaded equipment photos
        └── videos/
            └── farming.mp4   ← Background video (add manually)
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11+
- MongoDB (local) or MongoDB Atlas account (free)
- Git

### Step 1 — Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/tractonow.git
cd tractonow
```

### Step 2 — Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4 — Configure environment variables
```bash
cd backend
cp .env.example .env
# Edit .env with your MongoDB URI and API keys
```

`.env` file:
```env
MONGO_URI=mongodb://localhost:27017/tractonow
JWT_SECRET=your_very_long_random_secret_key_here
JWT_EXPIRY=604800
OPENWEATHER_API_KEY=your_key_from_openweathermap.org
FLASK_DEBUG=True
PORT=5000
```

### Step 5 — Train ML model & seed database
```bash
cd backend
python models/train_model.py     # train demand prediction model (once)
python database/seed.py          # insert sample data (safe, run anytime)
```

### Step 6 — Add media files
Place these files manually (too large for git):
```
frontend/static/videos/farming.mp4   ← background video
frontend/static/images/fields.jpg    ← login page background
frontend/static/images/machines.jpg  ← about page background
```

### Step 7 — Run the app
```bash
cd backend
python app.py
```

Open → **http://localhost:5000**

### Demo credentials
| Role | Email | Password |
|------|-------|----------|
| Farmer | ramu@farm.com | ramu123 |
| Farmer | lakshmi@farm.com | lakshmi123 |
| Owner | suresh@owner.com | suresh123 |
| Owner | venkat@owner.com | venkat123 |

---

## ☁️ Hosting on Render.com (Free)

Render.com is the easiest free hosting option for Python Flask apps.

### Step 1 — Set up MongoDB Atlas (free cloud database)

1. Go to [mongodb.com/atlas](https://mongodb.com/atlas) → **Sign Up Free**
2. Create a free **M0 cluster** (512MB, always free)
3. Create a database user: `Database Access` → Add User → username + password
4. Whitelist all IPs: `Network Access` → Add IP → `0.0.0.0/0`
5. Get connection string: `Clusters` → Connect → Connect your application → Copy URI
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/tractonow
   ```

### Step 2 — Push code to GitHub

```bash
cd tractonow

# Initialize git (if not done)
git init
git add .
git commit -m "Initial commit — TractoNow v2.0"

# Create repo on github.com then:
git remote add origin https://github.com/YOUR_USERNAME/tractonow.git
git push -u origin main
```

> **⚠️ Important:** Never commit `.env` — it's in `.gitignore`. Set env vars in Render dashboard instead.

### Step 3 — Deploy on Render.com

1. Go to [render.com](https://render.com) → **Sign Up** (free)
2. Click **New +** → **Web Service**
3. Connect your GitHub account → Select `tractonow` repository
4. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `tractonow` |
| **Region** | Singapore (closest to India) |
| **Branch** | `main` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r backend/requirements.txt && cd backend && python models/train_model.py && python database/seed.py` |
| **Start Command** | `gunicorn --chdir backend 'app:create_app()' --workers 2 --timeout 120 --bind 0.0.0.0:$PORT` |
| **Plan** | Free |

5. Add **Environment Variables** (click "Add Environment Variable"):

| Key | Value |
|-----|-------|
| `MONGO_URI` | `mongodb+srv://user:pass@cluster.mongodb.net/tractonow` |
| `JWT_SECRET` | Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_EXPIRY` | `604800` |
| `OPENWEATHER_API_KEY` | Your key from openweathermap.org |
| `FLASK_ENV` | `production` |
| `FLASK_DEBUG` | `False` |

6. Click **Create Web Service**
7. Wait ~3 minutes for first deploy
8. Your app is live at: `https://tractonow.onrender.com`

> **Free tier note:** Render free tier spins down after 15 minutes of inactivity. First load after sleep takes ~30 seconds. Upgrade to Starter ($7/month) for always-on.

---

## 🌐 Alternative Hosting Options

### Railway.app (Recommended — $5 free credits/month)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```
Set environment variables in Railway dashboard.

### PythonAnywhere (Free, India-friendly)
1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload project files via Files tab
3. Create a Web App → Flask → Python 3.11
4. Set working directory to `/home/username/tractonow/backend`
5. Configure WSGI file to import `create_app`

### VPS (DigitalOcean / Linode ~$6/month)
```bash
# On your VPS:
git clone https://github.com/YOUR/tractonow.git
cd tractonow/backend
pip install -r requirements.txt gunicorn
python models/train_model.py
python database/seed.py

# Run with gunicorn + nginx
gunicorn 'app:create_app()' --workers 4 --bind unix:/tmp/tractonow.sock &
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/check-phone` | Forgot password step 1 |
| POST | `/api/auth/reset-password` | Forgot password step 2 |
| GET | `/api/equipment/` | List equipment (with filters) |
| POST | `/api/equipment/` | Add equipment (owner) |
| POST | `/api/bookings/` | Create booking |
| GET | `/api/bookings/my` | My bookings |
| PUT | `/api/bookings/<id>/cancel` | Cancel booking |
| GET | `/api/groups/open` | Browse open groups |
| POST | `/api/groups/` | Create group |
| POST | `/api/groups/<id>/join` | Join group via link |
| POST | `/api/tracking/update` | Push real GPS (owner) |
| GET | `/api/tracking/<id>` | Get location + road route |
| GET | `/api/weather/forecast` | 5-day weather by district |
| GET | `/api/ai/crop-demand` | AI seasonal demand |
| POST | `/api/payment/pay` | Pay for booking |
| GET | `/api/health` | Health check |

---

## 🔧 Troubleshooting

**App won't start**
```bash
# Check Python version
python --version   # needs 3.11+

# Check MongoDB is running (local)
mongosh

# Check all dependencies installed
pip install -r backend/requirements.txt
```

**"Must register again after every restart"**
- Make sure `.env` has a fixed `JWT_SECRET` (not random)
- Set `JWT_EXPIRY=604800` (7 days)

**Equipment images showing as landscape bar**
- Images use `object-fit: contain` — they show actual ratio
- Portrait images will show as portrait ✓

**Map not loading**
- Leaflet loads from CDN — needs internet connection
- OSRM routing is free and needs no API key

**Weather not working**
- Get free API key from [openweathermap.org](https://openweathermap.org)
- Add to `.env` as `OPENWEATHER_API_KEY`

---

## 📄 License

MIT License — Free to use, modify, and distribute.

---

<div align="center">

Made with ❤️ for rural India 🇮🇳

**TractoNow v2.0** &nbsp;|&nbsp; 2024

</div>