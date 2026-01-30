import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"

from flask import Flask, render_template, request, jsonify
import sys
import csv
from datetime import datetime
import fetch_weather
from model.build_model import RecommendationEngine
from search_links import build_buy_links
sys.stdout.reconfigure(line_buffering=True)

app = Flask(__name__)

recommendation_engine = RecommendationEngine()
recommendation_engine.load_model_and_index()

@app.route("/")
def home():
    return render_template("home.html", title="Home", active_page="home")

@app.route("/advisor")
def advisor():
    return render_template("advisor.html", title="Advisor", active_page="advisor")

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "GET":
        return render_template("feedback.html", title="Feedback", active_page="feedback")

    # POST
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    rating = data.get("rating")
    feedback_text = data.get("feedback")

    if not rating or not feedback_text:
        return jsonify({"error": "Missing rating or feedback"}), 400

    file_path = "feedback.csv"
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "rating", "feedback"])

        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            rating,
            feedback_text
        ])

    return jsonify({"message": "Feedback saved"})

@app.route('/process-location', methods=['POST'])
def process_location():
    try:
        data = request.get_json()
        result = process_data(data)

        return jsonify({
            'message': 'Location processed successfully!',
            'data': {'result': result}
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/recommend', methods=['POST'])
def recommend():
    """Get product recommendations"""
    try:
        data = request.get_json()

        # Extract user preferences
        user_inputs = {
            'gender': data.get('gender', 'Men'),
            'articleType': data.get('articleType', 'Tshirts'),
            'season': data.get('season', 'Summer'),
            'usage': data.get('usage', 'Casual')
        }

        # Get recommendations using the class
        recommendations = recommendation_engine.predict(user_inputs)

        for it in recommendations:
            it["buy_links"] = build_buy_links(it)

        return jsonify({
            'recommendations': recommendations,
            'query': user_inputs
        }), 200

    except Exception as e:
        print(f"Error in recommendation: {str(e)}")
        return jsonify({'error': f'Recommendation error: {str(e)}'}), 500


from datetime import datetime, date, timedelta

def process_data(data: dict):
    # AGE
    age = data.get("age")
    if age is None or not (15 <= age <= 50):
        raise ValueError("Age must be between 15 and 50")

    # k
    k = data.get("k")
    if k is None or not (1 <= k <= 10):
        raise ValueError("Number of items (k) must be between 1 and 10")

    # DATE 
    date_str = data.get("date")
    if not date_str:
        raise ValueError("Target date is required")

    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = date.today()

    if not (today <= target_date <= today + timedelta(days=15)):
        raise ValueError("Target date must be within 15 days from today")

    # LOCATION
    location = data.get("location")
    if not location:
        raise ValueError("Location is required")

    lat = location.get("lat")
    lng = location.get("lng")

    if not fetch_weather.is_on_land(lat, lng):
        raise ValueError("Selected location must be on land")

    # WEATHER & RECOMMEND
    weather_data = fetch_weather.fetch_weather_data(lat, lng)
    season = fetch_weather.categorize_season(weather_data)

    user_inputs = {
        'gender': data['gender'],
        'articleType': 'Tshirts',
        'season': season,
        'usage': data['occasion'].capitalize()
    }

    recommendations = recommendation_engine.predict(user_inputs, k=k)
    for it in recommendations:
        it["buy_links"] = build_buy_links(it)

    return recommendations

if __name__ == '__main__':
    app.run(debug=False, host='localhost', port=5000)