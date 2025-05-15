from flask import Flask, render_template, request
import subprocess, sys, os, requests

app = Flask(__name__)

OPENWEATHER_API_KEY = '6b37fb1394549fc4eba81dbdd4f19fa2'

# Known accident zones (latitude, longitude)
accident_zones = [(13.0827, 80.2707), (12.9716, 77.5946)]

def is_in_accident_zone(lat, lon):
    for zone in accident_zones:
        dist = ((lat - zone[0]) ** 2 + (lon - zone[1]) ** 2) ** 0.5
        if dist < 0.02:
            return True
    return False

def get_weather(lat, lon):
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}'
    response = requests.get(url)
    data = response.json()
    return data['weather'][0]['main'] if 'weather' in data else "Clear"

def get_coords(place):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={place}"
    resp = requests.get(url, headers={"User-Agent": "Flask-App"}).json()
    if resp:
        return float(resp[0]['lat']), float(resp[0]['lon'])
    return None, None

def get_accident_risk(speed, in_hotspot, weather):
    if weather in ["Rain", "Thunderstorm", "Snow"]:
        return "High" if speed > 30 else "Medium"
    if in_hotspot and speed > 40:
        return "High"
    elif speed > 60:
        return "Medium"
    return "Low"

def voice_alert(message):
    python_exe = sys.executable
    speak_path = os.path.join(os.getcwd(), 'speak.py')
    subprocess.Popen([python_exe, speak_path, message])

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/map', methods=['POST'])
def map_route():
    start = request.form['start']
    end = request.form['end']
    speed = float(request.form['speed'])

    lat, lon = get_coords(start)
    if lat is None:
        return "Invalid start location"

    in_zone = is_in_accident_zone(lat, lon)
    weather = get_weather(lat, lon)
    risk = get_accident_risk(speed, in_zone, weather)

    if risk == "High":
        voice_alert("High risk of accident. Please slow down.")
    elif risk == "Medium":
        voice_alert("Moderate risk. Drive carefully.")

    return render_template("map.html", start=start, end=end, risk=risk, weather=weather)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
