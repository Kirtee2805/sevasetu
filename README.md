 # SevaSetu — Smart PHC Management System
**Team AstraSync | GEC Rajkot, Gujarat**

> Predicting medicine stock-outs at rural PHCs before they happen —
> so no patient arrives to find an empty shelf.

## Problem
India's Primary Health Centers face recurring medicine stock-outs,
undetected data fraud, and zero early warning systems. District
officers have no real-time visibility until the crisis has already hit.

## Our Solution
SevaSetu uses AI to:
- Detect suspicious stock reports automatically (Anomaly Detection)
- Predict which PHC will run out of which medicine in 7 days (XGBoost)
- Detect disease outbreaks from consumption pattern clusters
- Score each district's healthcare trust level
- Recommend smart redistribution before stock-out happens

## Data Sources
- HMIS (Health Management Information System) — Government of India
- Kaggle India Primary Health Care Dataset
- Synthetic daily data derived from real monthly HMIS aggregates

## Tech Stack
Python | XGBoost | Scikit-learn | Streamlit | FastAPI | SQLite | Gemini API

## Team
- Kirtee Pitroda — ML Lead & Team Leader
- Jiya Maru — Research & Design
- Shivkumar — Dashboard & AI Integration
- Aryan Mori — Backend & Database

## Competition
- Dewang Mehta IT Award 2026 — GTU Gujarat
- Build with AI — Hack2skill x Google 2026

## Run Locally
pip install -r requirements.txt
python models/data_pipeline.py
streamlit run dashboard/app.py
