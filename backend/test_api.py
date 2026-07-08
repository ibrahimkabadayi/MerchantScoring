"""Quick API integration test."""
import requests

BASE = "http://127.0.0.1:8000"

# Test 1: Top merchants
print("=== Top 3 Merchants ===")
r = requests.get(f"{BASE}/api/merchants/top?limit=3")
data = r.json()
for m in data:
    print(f"  {m['name']:30s} Score:{m['moka_fit_score']:5.1f} Tier:{m['priority_tier']}")

# Test 2: Stats
print("\n=== Dashboard Stats ===")
r = requests.get(f"{BASE}/api/merchants/stats")
stats = r.json()
print(f"  Total: {stats['total_merchants']}")
print(f"  HIGH: {stats['high_count']} | MEDIUM: {stats['medium_count']} | LOW: {stats['low_count']}")
print(f"  Avg Score: {stats['avg_score']}")

# Test 3: Filter by tier + category
print("\n=== HIGH tier cafes ===")
r = requests.get(f"{BASE}/api/merchants", params={"tier": "HIGH", "category": "cafe", "limit": 3})
cafes = r.json()
for m in cafes["merchants"][:3]:
    print(f"  {m['name']:30s} {m['district']:12s} Score:{m['moka_fit_score']:5.1f}")

# Test 4: Outreach generation
print("\n=== Outreach Message ===")
place_id = data[0]["place_id"]
r = requests.post(f"{BASE}/api/outreach/generate", json={"place_id": place_id})
out = r.json()
print(f"  For: {out['merchant_name']}")
print(f"  Message:\n{out['message']}")
