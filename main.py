
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
    """Handle location data from frontend"""
    option_num = 2
    try:
        # Get JSON data from request
        data = request.get_json()
        print(data)

        # Example: Do something with the data
        result = process_data(data)

        # Return success response
        return jsonify({
            'message': 'Location processed successfully!',
            'data': {
                'result': result
            }
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
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


def process_data(data: dict):
    location = data['location']
    weather_data = fetch_weather.fetch_weather_data(location['lat'], location['lng'])
    season = fetch_weather.categorize_season(weather_data)

    user_inputs = {
        'gender': data['gender'],
        'articleType': 'Tshirts',
        'season': season,
        'usage': data['occasion'].capitalize()
    }

    k = data.get("k", 5)

    recommendations = recommendation_engine.predict(user_inputs, k=k)
    for it in recommendations:
        it["buy_links"] = build_buy_links(it)
    return recommendations

if __name__ == '__main__':
    app.run(debug=False, host='localhost', port=5000)