from flask import Flask, render_template, jsonify
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

API_KEY = "3731e5395f8a4660bf662e904a63a35a"

@app.route("/")
def home():
    return render_template("index.html")

# ---------------------------------------------------------
# CIRCUIT DATABASE (stable, no scraping)
# ---------------------------------------------------------
CIRCUIT_DATA = {
    "monza": {
        "track_length": "5.793 km",
        "laps": "53",
        "race_distance": "306.72 km",
        "circuit_map": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Monza_track_map.svg/800px-Monza_track_map.svg.png"
    },
    "silverstone": {
        "track_length": "5.891 km",
        "laps": "52",
        "race_distance": "306.198 km",
        "circuit_map": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Silverstone_Circuit_2020.svg/800px-Silverstone_Circuit_2020.svg.png"
    },
    "spa": {
        "track_length": "7.004 km",
        "laps": "44",
        "race_distance": "308.052 km",
        "circuit_map": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Circuit_Spa.svg/800px-Circuit_Spa.svg.png"
    },
    "suzuka": {
        "track_length": "5.807 km",
        "laps": "53",
        "race_distance": "307.471 km",
        "circuit_map": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Suzuka_circuit_map--2019.svg/800px-Suzuka_circuit_map--2019.svg.png"
    },
    "bahrain": {
        "track_length": "5.412 km",
        "laps": "57",
        "race_distance": "308.238 km",
        "circuit_map": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Bahrain_International_Circuit--Grand_Prix_Layout.svg/800px-Bahrain_International_Circuit--Grand_Prix_Layout.svg.png"
    }
}

# ---------------------------------------------------------
# F1 ROUTE
# ---------------------------------------------------------
@app.route("/f1")
def f1():
    try:
        import requests
        from datetime import datetime

        # -----------------------------
        # GET NEXT RACE FROM ERGAST
        # -----------------------------
        raw_race = requests.get("https://api.jolpi.ca/ergast/f1/current/next").json()
        race_info = raw_race["MRData"]["RaceTable"]["Races"][0]

        # -----------------------------
        # FORMAT RACE DATE (dd/mm/yyyy)
        # -----------------------------
        race_date_raw = race_info["date"]
        race_date = datetime.strptime(race_date_raw, "%Y-%m-%d").strftime("%d/%m/%Y")

        # Clean race time (hh:mm)
        raw_race_time = race_info.get("time", "TBA")
        race_time = raw_race_time.replace("Z", "")[:5]  # removes Z and seconds

        race_name = race_info["raceName"]
        circuit_name = race_info["Circuit"]["circuitName"]
        locality = race_info["Circuit"]["Location"]["locality"]
        country = race_info["Circuit"]["Location"]["country"]
        circuit_id = race_info["Circuit"]["circuitId"]

        # -----------------------------
        # SESSION TIMES (dd/mm/yyyy hh:mm)
        # -----------------------------
        def format_session(session):
            if session in race_info:
                raw_date = race_info[session]["date"]
                raw_time = race_info[session]["time"]

                # Convert date
                nice_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d/%m/%Y")

                # Convert time (remove Z + seconds)
                clean_time = raw_time.replace("Z", "")[:5]

                return nice_date + " " + clean_time

            return "TBA"

        fp1 = format_session("FirstPractice")
        fp2 = format_session("SecondPractice")
        fp3 = format_session("ThirdPractice")
        qualifying = format_session("Qualifying")
        sprint = format_session("Sprint") if "Sprint" in race_info else None

        race_session = race_date + " " + race_time

        # -----------------------------
        # CIRCUIT INFO FROM DATABASE
        # -----------------------------
        circuit_data = CIRCUIT_DATA.get(circuit_id, {})

        track_length = circuit_data.get("track_length", "Unknown")
        laps = circuit_data.get("laps", "Unknown")
        race_distance = circuit_data.get("race_distance", "Unknown")

        # -----------------------------
        # DRIVER STANDINGS
        # -----------------------------
        raw_standings = requests.get("https://api.jolpi.ca/ergast/f1/current/driverStandings").json()
        top3 = raw_standings["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"][:3]

        top3_names = [
            f"{driver['Driver']['givenName']} {driver['Driver']['familyName']}"
            for driver in top3
        ]

        top3_teams = [
            driver["Constructors"][0]["name"]
            for driver in top3
        ]

        # -----------------------------
        # RETURN FULL DATA PACKAGE
        # -----------------------------
        return {
            "race_name": race_name,
            "race_date": race_date,
            "race_time": race_time,

            "circuit_name": circuit_name,
            "locality": locality,
            "country": country,

            "fp1": fp1,
            "fp2": fp2,
            "fp3": fp3,
            "qualifying": qualifying,
            "sprint": sprint,
            "race": race_session,

            "track_length": track_length,
            "laps": laps,
            "race_distance": race_distance,

            "top3": top3_names,
            "top3Teams": top3_teams
        }

    except Exception as e:
        print("F1 ERROR:", e)

@app.route("/f1_standings")
def f1_standings():
    try:
        url = "https://f1connectapi.vercel.app/api/current/drivers-championship"
        response = requests.get(url, timeout=10)
        data = response.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

import requests
from flask import jsonify

API_KEY = "3731e5395f8a4660bf662e904a63a35a"

def get_next_match(team_id):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": API_KEY}

    try:
        res = requests.get(url, headers=headers).json()

        # Get the FIRST upcoming match
        match = res["matches"][0]

        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]

        # Extract date + time from UTC format
        date = match["utcDate"].split("T")[0]
        time = match["utcDate"].split("T")[1][:5]

        opponent = f"{home} vs {away}"

        return {
            "opponent": opponent,
            "date": date,
            "time": time
        }

    except Exception as e:
        print("FOOTBALL ERROR:", e)
        return {"opponent": "Unavailable", "date": "-", "time": "-"}


@app.route("/football")
def football():
    return jsonify({
        "newcastle": get_next_match(67),        # Newcastle United
        "man_city": get_next_match(65),         # Manchester City
        "middlesbrough": get_next_match(343)    # Middlesbrough
    })

@app.route("/live-scores")
def live_scores():
    try:
        url = "https://sportapi7.p.rapidapi.com/api/v1/football/fixtures"

        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": "sportapi7.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers)
        data = response.json()

        # Extract fixtures
        fixtures = data.get("data", [])

        # Teams you track
        teams = {
            "newcastle": "Newcastle United",
            "man_city": "Manchester City",
            "middlesbrough": "Middlesbrough"
        }

        results = {}

        for key, team_name in teams.items():
            match = next(
                (f for f in fixtures
                 if f.get("home_team_name") == team_name
                 or f.get("away_team_name") == team_name),
                None
            )

            if match:
                results[key] = {
                    "home": match["home_team_name"],
                    "away": match["away_team_name"],
                    "home_goals": match["home_score"],
                    "away_goals": match["away_score"],
                    "status": match["status"],
                    "minute": match.get("minute", "")
                }
            else:
                results[key] = None

        return results

    except Exception as e:
        print("FOOTBALL ERROR:", e)
        return {"error": True}

import requests
import xml.etree.ElementTree as ET

@app.route("/youtube")
def youtube():
    try:
        channels = {
            "coach_colin": "UCf5fZQnO2PpY3W8Y7Z2N0xQ",
            "candace_owens": "UCy1b1nig0G0D0QdS9lO8r2w",
            "patricia_delicious": "UCYtZJv1nQG5xX8t1xX2zJ7g"
        }

        latest_videos = {}

        for name, channel_id in channels.items():
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            raw = requests.get(url).text

            # Debug print so we can see what YouTube returned
            print(f"RAW YOUTUBE RESPONSE for {name}:\n", raw[:200])

            # If YouTube returned HTML instead of XML, skip it
            if raw.strip().startswith("<!DOCTYPE html") or raw.strip().startswith("<html"):
                print(f"HTML BLOCKED RESPONSE for {name}")
                latest_videos[name] = {
                    "title": "Feed blocked by YouTube",
                    "link": "",
                    "published": ""
                }
                continue

            # Parse XML safely
            root = ET.fromstring(raw)
            entry = root.find("{http://www.w3.org/2005/Atom}entry")

            if entry is None:
                print(f"NO ENTRY FOUND FOR: {name}")
                latest_videos[name] = {
                    "title": "No recent videos",
                    "link": "",
                    "published": ""
                }
                continue

            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            link = entry.find("{http://www.w3.org/2005/Atom}link").attrib["href"]
            published = entry.find("{http://www.w3.org/2005/Atom}published").text

            latest_videos[name] = {
                "title": title,
                "link": link,
                "published": published
            }

        return latest_videos

    except Exception as e:
        print("YOUTUBE ERROR:", e)
        return {"error": True}

import requests
import xml.etree.ElementTree as ET

@app.route("/news")
def news():
    try:
        feeds = {
            "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
            "GB News": "https://www.gbnews.com/rss"
        }

        headlines = []

        for source, url in feeds.items():
            raw = requests.get(url).text

            # If feed returns HTML instead of XML, skip it
            if raw.strip().startswith("<!DOCTYPE html") or raw.strip().startswith("<html"):
                print(f"HTML BLOCKED RESPONSE for {source}")
                continue

            root = ET.fromstring(raw)

            # RSS items are under channel/item
            for item in root.findall("./channel/item")[:5]:  # Get top 5 from each source
                title = item.find("title").text if item.find("title") is not None else "No title"
                link = item.find("link").text if item.find("link") is not None else ""
                headlines.append({
                    "source": source,
                    "title": title,
                    "link": link
                })

        return {"headlines": headlines}

    except Exception as e:
        print("NEWS ERROR:", e)
        return {"error": True}

import json
import os

# Load all recipes
@app.route("/recipes")
def get_recipes():
    try:
        if not os.path.exists("recipes.json"):
            return {"recipes": []}

        with open("recipes.json", "r") as f:
            data = json.load(f)

        return data  # returns {"recipes": [...]}

    except Exception as e:
        print("RECIPE LOAD ERROR:", e)
        return {"recipes": []}

import json
import os
import uuid
from flask import request

# Add a new recipe
@app.route("/add_recipe", methods=["POST"])
def add_recipe():
    try:
        # Load existing recipes
        if os.path.exists("recipes.json"):
            with open("recipes.json", "r") as f:
                data = json.load(f)
        else:
            data = {"recipes": []}

        # Get recipe data from the request
        new_recipe = request.json

        # Assign a unique ID
        new_recipe["id"] = str(uuid.uuid4())

        # Add creation date
        new_recipe["created"] = "2026-08-12"  # You can automate this later

        # Add to list
        data["recipes"].append(new_recipe)

        # Save back to file
        with open("recipes.json", "w") as f:
            json.dump(data, f, indent=4)

        return {"success": True, "id": new_recipe["id"]}

    except Exception as e:
        print("RECIPE SAVE ERROR:", e)
        return {"success": False}

# Get a single recipe by ID
@app.route("/recipe/<id>")
def get_recipe(id):
    try:
        with open("recipes.json", "r") as f:
            data = json.load(f)

        for recipe in data["recipes"]:
            if recipe["id"] == id:
                return recipe

        return {"error": "Recipe not found"}

    except Exception as e:
        print("RECIPE VIEW ERROR:", e)
        return {"error": "Could not load recipe"}

# Edit an existing recipe
@app.route("/edit_recipe/<id>", methods=["POST"])
def edit_recipe(id):
    try:
        with open("recipes.json", "r") as f:
            data = json.load(f)

        updated = request.json

        for recipe in data["recipes"]:
            if recipe["id"] == id:
                recipe["title"] = updated.get("title", recipe["title"])
                recipe["ingredients"] = updated.get("ingredients", recipe["ingredients"])
                recipe["steps"] = updated.get("steps", recipe["steps"])
                recipe["notes"] = updated.get("notes", recipe["notes"])
                recipe["youtube"] = updated.get("youtube", recipe["youtube"])
                recipe["category"] = updated.get("category", recipe["category"])

                break

        with open("recipes.json", "w") as f:
            json.dump(data, f, indent=4)

        return {"success": True}

    except Exception as e:
        print("EDIT ERROR:", e)
        return {"success": False}

# Delete a recipe
@app.route("/delete_recipe/<id>", methods=["POST"])
def delete_recipe(id):
    try:
        with open("recipes.json", "r") as f:
            data = json.load(f)

        data["recipes"] = [r for r in data["recipes"] if r["id"] != id]

        with open("recipes.json", "w") as f:
            json.dump(data, f, indent=4)

        return {"success": True}

    except Exception as e:
        print("DELETE ERROR:", e)
        return {"success": False}

@app.route("/votd")
def votd():
    try:
        response = requests.get(
            "https://labs.bible.org/api/?passage=votd&type=json"
        )
        data = response.json()[0]

        verse = data["text"]
        reference = f"{data['bookname']} {data['chapter']}:{data['verse']}"

        return jsonify({
            "reference": reference,
            "text": verse
        })

    except Exception:
        return jsonify({
            "reference": "Verse unavailable",
            "text": "Could not reach daily verse source."
        })

@app.route("/gallery")
def gallery():
    folder = "static/gallery"
    photos = []

    for filename in os.listdir(folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            photos.append(filename)

    return jsonify({"photos": photos})

from flask import request

@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    file = request.files.get("photo")
    if not file:
        return jsonify({"success": False, "error": "No file uploaded"})

    save_path = f"static/gallery/{file.filename}"
    file.save(save_path)

    return jsonify({"success": True})

from flask import render_template

@app.route("/gallery_page")
def gallery_page():
    return render_template("gallery.html")

@app.post("/delete_photo")
def delete_photo():
    data = request.get_json()
    filename = data.get("filename")

    path = os.path.join("static/gallery", filename)

    if os.path.exists(path):
        os.remove(path)
        return {"success": True}
    else:
        return {"success": False}


import requests
import xml.etree.ElementTree as ET
from flask import jsonify
import re

def clean_html(text):
    # Remove HTML tags
    return re.sub(r"<.*?>", "", text).strip()

def extract_details(description):
    if not description:
        return None, None, None

    text = clean_html(description)

    # First sentence
    first_sentence = text.split(".")[0] + "."

    # Extract age
    age_patterns = [
        r"aged (\d+)",
        r"age (\d+)",
        r"was (\d+)",
        r"at (\d+)",
        r"(\d+)-year-old"
    ]

    age = None
    for pattern in age_patterns:
        match = re.search(pattern, text)
        if match:
            age = match.group(1)
            break

    # Extract profession (first capitalised phrase)
    profession = None
    prof_match = re.search(r"\b[Aa]n? ([A-Z][a-z]+(?: [A-Z][a-z]+)*)", text)
    if prof_match:
        profession = prof_match.group(1)

    return age, profession, first_sentence

def generate_summary(title, description):
    clean_title = title.replace("obituary", "").replace("Obituary", "").strip(" -–")
    name = clean_title.split(",")[0].strip()

    age, profession, first_sentence = extract_details(description)

    if first_sentence:
        summary = first_sentence
        if age:
            summary += f" (Age {age})"
        return summary

    if age or profession:
        parts = []
        if age:
            parts.append(f"aged {age}")
        if profession:
            parts.append(profession)
        details = ", ".join(parts)
        return f"{name}, {details}, has recently passed away."

    return f"{name} has recently passed away."

@app.route("/death_news")
def death_news():
    feeds = {
        "Guardian": "https://www.theguardian.com/tone/obituaries/rss",
        "Telegraph": "https://www.telegraph.co.uk/obituaries/rss.xml",
        "Independent": "https://www.independent.co.uk/news/obituaries/rss"
    }

    results = []

    for source, url in feeds.items():
        try:
            raw = requests.get(url).text

            if raw.strip().startswith("<html"):
                continue

            root = ET.fromstring(raw)

            for item in root.findall("./channel/item"):
                title = item.find("title").text
                link = item.find("link").text
                description = item.find("description").text

                summary = generate_summary(title, description)

                results.append({
                    "source": source,
                    "title": title,
                    "summary": summary,
                    "link": link
                })

        except Exception as e:
            print("DEATH NEWS ERROR:", e)
            continue

    return jsonify({"deaths": results[:5]})

@app.route('/stream')
def stream():
    url = "https://icecast.radiofrance.fr/fip-hifi.mp3"
    r = requests.get(url, stream=True)

    return Response(
        r.iter_content(chunk_size=4096),
        mimetype="audio/mpeg"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

