from flask import Flask, request, jsonify, render_template
import sqlite3
import json
import requests
from datetime import datetime
import os
import requests
app = Flask(__name__)

# Datenbank initialisieren
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
            gps_latitude REAL,
            gps_longitude REAL,
            gps_accuracy REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()


def get_public_ip():
    try:
        # Einfacher Dienst, der nur die IP als Text zurückgibt
        response = requests.get('https://api.ipify.org', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"Fehler beim Abrufen der öffentlichen IP: {e}")
    return None

def get_ip_geolocation(ip):
    """Holt Standortinformationen zur IP-Adresse"""
    try:
        # Kostenlose IP-API (kein API-Key nötig)
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
    except Exception as e:
        print(f"Geolocation-Error: {e}")
    return {'city': '', 'region': '', 'country': '', 'latitude': 0.0, 'longitude': 0.0}

def parse_user_agent(user_agent):
    """Einfache Geräte- und Browser-Erkennung aus User-Agent"""
    ua = user_agent.lower()
    
    # Betriebssystem
    platform = 'Unknown'
    if 'windows' in ua:
        platform = 'Windows'
    elif 'macintosh' in ua or 'mac os' in ua:
        platform = 'macOS'
    elif 'linux' in ua:
        platform = 'Linux'
    elif 'android' in ua:
        platform = 'Android'
    elif 'iphone' in ua or 'ipad' in ua or 'ipod' in ua:
        platform = 'iOS'
    
    # Browser
    browser = 'Unknown'
    if 'edg' in ua:
        browser = 'Edge'
    elif 'opr' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'chrome' in ua and 'android' not in ua:
        browser = 'Chrome'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'firefox' in ua:
        browser = 'Firefox'
    
    # Gerätetyp
    device_type = 'Desktop'
    if 'mobile' in ua or 'android' in ua:
        device_type = 'Mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device_type = 'Tablet'
    
    return platform, browser, device_type

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/track', methods=['POST'])
@app.route('/track', methods=['POST'])
def track():
    try:
        # 1. Daten vom Frontend empfangen
        data = request.get_json()
        
        # 2. Öffentliche IP ermitteln (statt localhost)
        public_ip = get_public_ip()
        if public_ip:
            ip_address = public_ip
            print(f"🌍 Öffentliche IP erkannt: {ip_address}")
        else:
            # Fallback: REMOTE_ADDR (bei lokalen Tests oft 127.0.0.1)
            ip_address = request.remote_addr
            print(f"⚠️ Fallback auf REMOTE_ADDR: {ip_address}")
        
        # 3. IP-Geolocation (Standort zur IP)
        ip_geo = get_ip_geolocation(ip_address)
        
        # 4. User-Agent parsen (Gerät, Browser, OS)
        user_agent = request.headers.get('User-Agent', '')
        platform, browser, device_type = parse_user_agent(user_agent)
        
        # 5. GPS-Daten aus Frontend (wenn vorhanden)
        gps_lat = data.get('latitude', 0.0)
        gps_lon = data.get('longitude', 0.0)
        gps_accuracy = data.get('accuracy', 0.0)
        
        # 6. In Datenbank speichern
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO clicks (
                ip_address, user_agent, platform, browser, device_type,
                city, region, country, latitude, longitude,
                gps_latitude, gps_longitude, gps_accuracy, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ip_address, user_agent, platform, browser, device_type,
            ip_geo['city'], ip_geo['region'], ip_geo['country'],
            ip_geo['latitude'], ip_geo['longitude'],
            gps_lat, gps_lon, gps_accuracy,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        # 7. Erfolgsmeldung an Frontend senden
        return jsonify({
            'status': 'success',
            'message': 'Data stored',
            'ip': ip_address,
            'location': f"{ip_geo['city']}, {ip_geo['country']}"
        }), 200
        
    except Exception as e:
        print(f"❌ Fehler in track(): {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    try:
        data = request.get_json()
        ip = request.remote_addr
        
        # IP-Geolocation
        ip_geo = get_ip_geolocation(ip)
        
        # User-Agent parsen
        user_agent = request.headers.get('User-Agent', '')
        platform, browser, device_type = parse_user_agent(user_agent)
        
        public_ip = get_public_ip()
        if public_ip:
            ip_address = public_ip  # Verwende die öffentliche IP
        else:
            ip_address = request.remote_addr  # Fallback auf lokale IP



        # GPS-Daten aus Frontend
        gps_lat = data.get('latitude', 0.0)
        gps_lon = data.get('longitude', 0.0)
        gps_accuracy = data.get('accuracy', 0.0)
        
        # In Datenbank speichern
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO clicks (
                ip_address, user_agent, platform, browser, device_type,
                city, region, country, latitude, longitude,
                gps_latitude, gps_longitude, gps_accuracy, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ip, user_agent, platform, browser, device_type,
            ip_geo['city'], ip_geo['region'], ip_geo['country'],
            ip_geo['latitude'], ip_geo['longitude'],
            gps_lat, gps_lon, gps_accuracy,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Data stored'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/data')
def view_data():
    """Einfache Ansicht aller gespeicherten Daten"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM clicks ORDER BY id DESC LIMIT 100')
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)