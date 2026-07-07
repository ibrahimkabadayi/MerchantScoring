# Moka Fit Score

AI-powered lead scoring engine for Moka United's sales team. Prioritizes the most conversion-likely merchant candidates using open data and generates personalized outreach content.

## Project Structure

```
backend/
├── main.py              # FastAPI entry point
├── config.py            # Environment variables & settings
├── database.py          # SQLite + SQLAlchemy setup
├── models.py            # ORM models (Merchant table)
├── api/
│   ├── schemas.py       # Pydantic request/response models
│   └── routes/
│       ├── merchants.py # Merchant CRUD & filtering endpoints
│       └── outreach.py  # Outreach message generation endpoint
├── data/
│   ├── collector.py     # Google Places API collector
│   ├── osm_collector.py # OpenStreetMap density data
│   └── mock_generator.py# Faker-based mock data
├── features/
│   ├── engineer.py      # Feature engineering pipeline
│   └── preprocessor.py  # Imputation & normalization
├── model/
│   ├── trainer.py       # XGBoost model training
│   ├── scorer.py        # Score prediction & breakdown
│   └── artifacts/       # Saved model files (.pkl)
└── outreach/
    └── generator.py     # Gemini LLM outreach messages
```

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Configure environment
# Edit .env in project root with your API keys

# 4. Run the API server
uvicorn main:app --reload

# 5. Open API docs
# http://localhost:8000/docs
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/merchants` | List merchants (filterable) |
| GET | `/api/merchants/top` | Top N by score |
| GET | `/api/merchants/stats` | Dashboard statistics |
| GET | `/api/merchants/{place_id}` | Single merchant detail |
| POST | `/api/outreach/generate` | Generate outreach message |

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **ML:** XGBoost, scikit-learn, pandas
- **LLM:** Google Gemini API
- **Frontend:** React + TypeScript + Tailwind CSS (coming soon)
