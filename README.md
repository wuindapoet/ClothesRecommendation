# AI002 Project: SmartFit – Smart Outfit Advisor Website

SmartFit is a context-aware outfit recommendation system that suggests suitable clothing based on **user attributes**, **occasion**, and **real-world weather conditions** derived from the user's location.
The system integrates a recommendation model with live weather data to provide practical and personalized outfit suggestions.

---

## 1. Features

- Outfit recommendation based on:
  - Gender
  - Occasion (e.g., Casual, Formal)
  - Location-based weather
- Real-time weather data using Open-Meteo API
- Context-aware recommendation model
- Web-based user interface with map-based location input

---

## 2. System Overview

The system follows a context-aware retrieval pipeline:

1. User selects gender, occasion, and location
2. Weather data is fetched using geographic coordinates
3. Weather is transformed into semantic features
4. A recommendation model ranks suitable outfits
5. Top outfit recommendations are returned to the user

---

## 3. Weather Feature Engineering

Instead of using raw numerical weather values, SmartFit converts weather data into meaningful categorical features:

### Temperature Level

| Average Temperature | Category |
|---------------------|----------|
| ≥ 28°C              | hot      |
| 20–27°C             | mild     |
| < 20°C              | cold     |

### Rain Level

| Average Precipitation | Category |
|-----------------------|----------|
| ≥ 5 mm                | rainy    |
| < 5 mm                | dry      |

Weather data is averaged over the next 3 days to reflect near-future conditions.

---
## 4. Project Structure
├── app.py # Flask application entry point

├── fetch_weather.py # Weather data fetching and processing

├── build_model.py # Recommendation model definition

├── train.py # Model training script

├── static/ # Static assets (CSS, images)

├── templates/ # HTML templates

├── data/ # Dataset files

└── README.md

---

