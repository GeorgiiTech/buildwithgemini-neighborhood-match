# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Firestore database module for customer intake profiles and indexed neighborhood statistics."""

import datetime
import logging
import os
from typing import Any

from google.cloud import firestore

logger = logging.getLogger(__name__)

# Firestore requires the string project ID, not the numeric project number
_env_proj = os.environ.get("PROJECT_ID") or os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT", "")
if not _env_proj or _env_proj.isdigit():
    PROJECT_ID = "qwiklabs-gcp-04-ea3abe4d2d3b"
else:
    PROJECT_ID = _env_proj

_db = None


def get_firestore_client() -> firestore.Client:
    """Returns a singleton Cloud Firestore native client."""
    global _db
    if _db is None:
        try:
            _db = firestore.Client(project=PROJECT_ID)
        except Exception as e:
            logger.warning(f"Could not initialize Firestore client for project {PROJECT_ID}: {e}")
            _db = None
    return _db


# Curated neighborhood statistics with indexed scores (0-100)
SEED_NEIGHBORHOODS = [
    {
        "id": "austin_round_rock",
        "neighborhood": "Round Rock",
        "city": "Austin",
        "walkability_score": 42,
        "safety_score": 95,
        "crime_index": "Very Low (A)",
        "school_score": 94,
        "remote_work_score": 95,
        "car_parking_score": 98,
        "median_rent_2br": 1950,
        "median_home_price": 460000,
        "pros": [
            "Top-tier public schools (Round Rock ISD)",
            "Extremely safe family-oriented community",
            "Spacious homes with 2+ car garages and dedicated parking",
            "Ubiquitous gigabit fiber internet",
        ],
        "cons": [
            "Low walkability; car required for almost all errands",
            "Suburban pace with limited nightlife",
        ],
        "tags": ["low-crime", "top-schools", "remote-friendly", "car-friendly", "suburban"],
    },
    {
        "id": "austin_cedar_park",
        "neighborhood": "Cedar Park",
        "city": "Austin",
        "walkability_score": 48,
        "safety_score": 92,
        "crime_index": "Very Low (A-)",
        "school_score": 91,
        "remote_work_score": 92,
        "car_parking_score": 95,
        "median_rent_2br": 1850,
        "median_home_price": 480000,
        "pros": [
            "Great parks, recreation centers, and Leander ISD schools",
            "Quiet residential streets ideal for work-from-home",
            "Affordable 2-3BR rental and single-family options",
        ],
        "cons": [
            "Commuter traffic into Downtown Austin during peak hours",
            "Car dependency for grocery and retail trips",
        ],
        "tags": ["low-crime", "top-schools", "remote-friendly", "car-friendly", "family-parks"],
    },
    {
        "id": "austin_mueller",
        "neighborhood": "Mueller",
        "city": "Austin",
        "walkability_score": 86,
        "safety_score": 84,
        "crime_index": "Low (B+)",
        "school_score": 82,
        "remote_work_score": 90,
        "car_parking_score": 75,
        "median_rent_2br": 2600,
        "median_home_price": 680000,
        "pros": [
            "Highly walkable modern community with lake, trails, and farmer's market",
            "Great local coffee shops and coworking friendly spaces",
            "Close proximity to downtown with community parks",
        ],
        "cons": [
            "Higher price per square foot",
            "Moderate street parking restrictions",
        ],
        "tags": ["walkable", "modern", "remote-friendly", "parks", "eco-friendly"],
    },
    {
        "id": "austin_downtown",
        "neighborhood": "Downtown",
        "city": "Austin",
        "walkability_score": 94,
        "safety_score": 68,
        "crime_index": "Moderate (C+)",
        "school_score": 60,
        "remote_work_score": 82,
        "car_parking_score": 38,
        "median_rent_2br": 3200,
        "median_home_price": 790000,
        "pros": [
            "World-class walkability and vibrant dining/music scene",
            "Lady Bird Lake hike-and-bike trail right outside",
            "Public transit and micro-mobility accessibility",
        ],
        "cons": [
            "High urban property crime and street noise",
            "Limited public school options for growing children",
            "Expensive paid garage parking; not car-convenient",
        ],
        "tags": ["walkable", "nightlife", "urban", "dining", "transit-friendly"],
    },
    {
        "id": "austin_south_lamar",
        "neighborhood": "South Lamar",
        "city": "Austin",
        "walkability_score": 78,
        "safety_score": 76,
        "crime_index": "Moderate-Low (B)",
        "school_score": 75,
        "remote_work_score": 88,
        "car_parking_score": 68,
        "median_rent_2br": 2300,
        "median_home_price": 610000,
        "pros": [
            "Iconic Austin food culture, boutique coffee shops, and live music",
            "Balanced walkability to restaurants and shopping",
            "Short drive to downtown and greenbelt",
        ],
        "cons": [
            "Traffic on Lamar Blvd",
            "Older school facilities compared to northern suburbs",
        ],
        "tags": ["walkable", "foodie", "culture", "urban-suburban"],
    },
    {
        "id": "raleigh_cary",
        "neighborhood": "Cary",
        "city": "Raleigh",
        "walkability_score": 52,
        "safety_score": 98,
        "crime_index": "Very Low (A+)",
        "school_score": 96,
        "remote_work_score": 97,
        "car_parking_score": 96,
        "median_rent_2br": 1800,
        "median_home_price": 520000,
        "pros": [
            "Ranked among the safest cities in the United States",
            "Nationally top-ranked public schools and greenway systems",
            "High concentration of tech remote workers and Google Fiber",
        ],
        "cons": ["Requires personal car for daily mobility"],
        "tags": ["low-crime", "top-schools", "remote-friendly", "car-friendly", "tech-hub"],
    },
    {
        "id": "seattle_bellevue",
        "neighborhood": "Bellevue",
        "city": "Seattle",
        "walkability_score": 70,
        "safety_score": 92,
        "crime_index": "Low (A)",
        "school_score": 96,
        "remote_work_score": 96,
        "car_parking_score": 82,
        "median_rent_2br": 2900,
        "median_home_price": 1250000,
        "pros": [
            "Exceptional public school system and very safe public parks",
            "Thriving tech economy and high-speed infrastructure",
            "Clean and balanced urban-suburban community",
        ],
        "cons": ["High cost of living and expensive real estate"],
        "tags": ["low-crime", "top-schools", "remote-friendly", "safe", "high-income"],
    },
]


SAMPLE_RELOCATION_STATS = [
    {
        "id": "stat_ny_austin_1",
        "user_id": "anon_ny_101",
        "origin_city": "Brooklyn, NY",
        "target_city": "Austin, TX",
        "reason_for_leaving": "High rent, cramped apartment, steep city taxes, wanting yard and top-tier public schools for children.",
        "housing_type": "rent",
        "target_price": 2400,
        "crime_level_answer": "Top priority - must have safe neighborhood with very low violent crime (10/10)",
        "crime_safety_priority": 10,
        "walkability_priority": 4,
        "school_priority": 10,
        "created_at": "2026-09-15T10:00:00Z",
    },
    {
        "id": "stat_sf_austin_1",
        "user_id": "anon_sf_202",
        "origin_city": "San Francisco, CA",
        "target_city": "Austin, TX",
        "reason_for_leaving": "Excessive cost of living, property crime concerns, remote job freedom allows moving somewhere with more affordable homeownership.",
        "housing_type": "buy",
        "target_price": 520000,
        "crime_level_answer": "Very concerned about car break-ins and property crime; want peaceful suburban safety (9/10)",
        "crime_safety_priority": 9,
        "walkability_priority": 6,
        "school_priority": 8,
        "created_at": "2026-09-18T14:30:00Z",
    },
    {
        "id": "stat_chi_austin_1",
        "user_id": "anon_chi_303",
        "origin_city": "Chicago, IL",
        "target_city": "Austin, TX",
        "reason_for_leaving": "Harsh winters, wanting year-round outdoor lifestyle for growing family, high property taxes.",
        "housing_type": "rent",
        "target_price": 2100,
        "crime_level_answer": "High priority on low crime, safe parks and quiet residential cul-de-sacs (9/10)",
        "crime_safety_priority": 9,
        "walkability_priority": 5,
        "school_priority": 9,
        "created_at": "2026-09-20T09:15:00Z",
    },
    {
        "id": "stat_sea_austin_1",
        "user_id": "anon_sea_404",
        "origin_city": "Seattle, WA",
        "target_city": "Austin, TX",
        "reason_for_leaving": "Cloudy weather, looking for booming tech community with 0% state income tax and spacious homes.",
        "housing_type": "buy",
        "target_price": 490000,
        "crime_level_answer": "Moderate-to-high safety expectations, family-friendly atmosphere (8/10)",
        "crime_safety_priority": 8,
        "walkability_priority": 7,
        "school_priority": 8,
        "created_at": "2026-09-21T16:00:00Z",
    },
]


def seed_neighborhood_database() -> int:
    """Populates the neighborhood_stats and relocation_statistics collections in Firestore."""
    client = get_firestore_client()
    if client is None:
        logger.warning("Firestore client unavailable for seeding.")
        return 0

    count = 0
    col_ref = client.collection("neighborhood_stats")
    for doc_data in SEED_NEIGHBORHOODS:
        doc_id = doc_data["id"]
        doc_ref = col_ref.document(doc_id)
        doc_ref.set(doc_data, merge=True)
        count += 1

    stats_col = client.collection("relocation_statistics")
    for stat in SAMPLE_RELOCATION_STATS:
        stats_col.document(stat["id"]).set(stat, merge=True)
        count += 1

    return count


def get_customer_profile(user_id: str) -> dict[str, Any] | None:
    """Fetches customer profile from Firestore collection customer_profiles."""
    client = get_firestore_client()
    if client is None or not user_id:
        return None

    try:
        doc_ref = client.collection("customer_profiles").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        logger.error(f"Error fetching profile for {user_id}: {e}")
    return None


def save_customer_profile(
    user_id: str,
    current_location: str = "",
    target_city: str = "",
    housing_type: str = "rent",
    target_price: float | int = 0,
    reason_for_leaving: str = "",
    crime_level_answer: str = "",
    crime_safety_priority: int = 8,
    walkability_priority: int = 5,
    school_priority: int = 8,
    max_budget: float | int = 0,
    **kwargs,
) -> dict[str, Any]:
    """Saves or updates customer intake preferences in Firestore customer_profiles
    and records an event in relocation_statistics for community indexing.
    """
    client = get_firestore_client()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    existing = get_customer_profile(user_id) or {}
    iteration_count = existing.get("iteration_count", 0) + 1

    # Resolve price
    resolved_price = target_price or max_budget or existing.get("target_price", 0) or existing.get("max_budget", 0)

    profile_data = {
        "user_id": user_id,
        "current_location": current_location or existing.get("current_location", ""),
        "target_city": target_city or existing.get("target_city", "Austin, TX"),
        "housing_type": housing_type or existing.get("housing_type", "rent"),
        "target_price": resolved_price,
        "max_budget": resolved_price,
        "reason_for_leaving": reason_for_leaving or existing.get("reason_for_leaving", ""),
        "crime_level_answer": crime_level_answer or existing.get("crime_level_answer", ""),
        "crime_safety_priority": crime_safety_priority or existing.get("crime_safety_priority", 8),
        "walkability_priority": walkability_priority or existing.get("walkability_priority", 5),
        "school_priority": school_priority or existing.get("school_priority", 8),
        "iteration_count": iteration_count,
        "updated_at": now_iso,
    }
    if "created_at" not in existing:
        profile_data["created_at"] = now_iso

    if client:
        try:
            # 1. Update customer profile document
            client.collection("customer_profiles").document(user_id).set(profile_data, merge=True)

            # 2. Add to relocation_statistics for indexing across customers
            stat_id = f"stat_{user_id}_{iteration_count}"
            client.collection("relocation_statistics").document(stat_id).set({
                "id": stat_id,
                "user_id": user_id,
                "origin_city": profile_data["current_location"],
                "target_city": profile_data["target_city"],
                "housing_type": profile_data["housing_type"],
                "target_price": profile_data["target_price"],
                "reason_for_leaving": profile_data["reason_for_leaving"],
                "crime_level_answer": profile_data["crime_level_answer"],
                "crime_safety_priority": profile_data["crime_safety_priority"],
                "walkability_priority": profile_data["walkability_priority"],
                "school_priority": profile_data["school_priority"],
                "created_at": now_iso,
            }, merge=True)
        except Exception as e:
            logger.error(f"Error saving profile for {user_id}: {e}")

    return profile_data


def get_relocation_statistics(
    origin_city: str = "",
    target_city: str = "Austin",
) -> dict[str, Any]:
    """Retrieves aggregated statistics and trends from Firestore on why people leave,
    housing prices (rent/buy), and crime level preferences from past customer inquiries.

    Args:
        origin_city: Filter by customer origin (e.g., 'Brooklyn', 'New York', 'San Francisco').
        target_city: Target relocation destination (defaults to 'Austin').

    Returns:
        Aggregated statistics including common origin cities, top reasons for leaving,
        average target prices for renting and buying, and crime/safety priorities.
    """
    client = get_firestore_client()
    stats = []

    if client:
        try:
            for doc in client.collection("relocation_statistics").stream():
                stats.append(doc.to_dict())
        except Exception as e:
            logger.warning(f"Error streaming relocation statistics: {e}")

    if not stats:
        stats = list(SAMPLE_RELOCATION_STATS)

    # Filter by origin / target if specified
    filtered = []
    for s in stats:
        match_orig = not origin_city or origin_city.lower() in s.get("origin_city", "").lower()
        match_target = not target_city or target_city.lower() in s.get("target_city", "").lower()
        if match_orig and match_target:
            filtered.append(s)

    if not filtered:
        filtered = stats

    rent_prices = [s["target_price"] for s in filtered if s.get("housing_type") == "rent" and s.get("target_price")]
    buy_prices = [s["target_price"] for s in filtered if s.get("housing_type") == "buy" and s.get("target_price")]
    safety_scores = [s["crime_safety_priority"] for s in filtered if s.get("crime_safety_priority")]

    avg_rent = round(sum(rent_prices) / len(rent_prices)) if rent_prices else 2200
    avg_buy = round(sum(buy_prices) / len(buy_prices)) if buy_prices else 505000
    avg_safety = round(sum(safety_scores) / len(safety_scores), 1) if safety_scores else 9.2

    origins = {}
    for s in filtered:
        orig = s.get("origin_city", "Unknown")
        if orig:
            origins[orig] = origins.get(orig, 0) + 1

    reasons = [s["reason_for_leaving"] for s in filtered if s.get("reason_for_leaving")]
    crime_concerns = [s["crime_level_answer"] for s in filtered if s.get("crime_level_answer")]

    return {
        "total_inquiries_analyzed": len(filtered),
        "target_city": target_city,
        "top_origin_cities": sorted(origins.items(), key=lambda x: x[1], reverse=True),
        "average_target_monthly_rent": f"${avg_rent:,}/mo",
        "average_target_home_purchase_price": f"${avg_buy:,}",
        "average_crime_safety_importance": f"{avg_safety} / 10",
        "key_reasons_people_are_leaving": reasons[:5],
        "common_crime_and_safety_sentiments": crime_concerns[:5],
        "insights_summary": (
            f"Based on {len(filtered)} mover inquiries, the top reasons people leave places like "
            f"{', '.join(list(origins.keys())[:3])} for {target_city} are high housing costs, "
            f"cramped living conditions, and safety concerns. Customers prioritize low crime and school quality "
            f"very highly (average safety priority: {avg_safety}/10), with average budgets of "
            f"${avg_rent:,}/mo for rentals and ${avg_buy:,} for home purchases."
        ),
    }


def query_neighborhood_rankings(
    city: str = "Austin",
    user_id: str = "",
    walk_weight: int | None = None,
    safety_weight: int | None = None,
    school_weight: int | None = None,
    remote_weight: int | None = None,
    car_weight: int | None = None,
) -> list[dict[str, Any]]:
    """Calculates weighted match scores and ranks neighborhoods in the target city.

    Weights are drawn from the customer's stored profile if available.
    """
    profile = get_customer_profile(user_id) if user_id else {}
    w_walk = walk_weight if walk_weight is not None else (profile.get("walkability_priority") if profile else 5)
    w_safe = safety_weight if safety_weight is not None else (profile.get("crime_safety_priority") if profile else 8)
    w_school = school_weight if school_weight is not None else (profile.get("school_priority") if profile else 8)
    w_remote = remote_weight if remote_weight is not None else (9 if profile.get("remote_work", True) else 5)
    w_car = car_weight if car_weight is not None else (8 if profile.get("has_car", True) else 3)

    neighborhoods = []
    client = get_firestore_client()
    if client:
        try:
            col_ref = client.collection("neighborhood_stats")
            for doc in col_ref.stream():
                data = doc.to_dict()
                if not city or city.lower() in data.get("city", "").lower():
                    neighborhoods.append(data)
        except Exception as e:
            logger.warning(f"Error streaming from Firestore: {e}")

    if not neighborhoods:
        for n in SEED_NEIGHBORHOODS:
            if not city or city.lower() in n["city"].lower():
                neighborhoods.append(n)

    if not neighborhoods:
        neighborhoods = list(SEED_NEIGHBORHOODS)

    total_weight = max(1, w_walk + w_safe + w_school + w_remote + w_car)

    scored: list[dict[str, Any]] = []
    for n in neighborhoods:
        walk = n.get("walkability_score", 50)
        safe = n.get("safety_score", 50)
        school = n.get("school_score", 50)
        remote = n.get("remote_work_score", 50)
        car = n.get("car_parking_score", 50)

        composite_score = round(
            (walk * w_walk + safe * w_safe + school * w_school + remote * w_remote + car * w_car)
            / total_weight,
            1,
        )

        entry = dict(n)
        entry["match_score"] = composite_score
        entry["weight_breakdown"] = {
            "walkability": f"{walk}/100 (wt: {w_walk})",
            "safety": f"{safe}/100 (wt: {w_safe})",
            "schools": f"{school}/100 (wt: {w_school})",
            "remote_work": f"{remote}/100 (wt: {w_remote})",
            "car_friendliness": f"{car}/100 (wt: {w_car})",
        }
        scored.append(entry)

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored
