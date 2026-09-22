# ruff: noqa
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

from typing import Any
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from .a2ui_utils import a2ui_callback
from .firestore_db import (
    get_customer_profile,
    get_relocation_statistics,
    query_neighborhood_rankings,
    save_customer_profile,
    seed_neighborhood_database,
)


MODEL = "gemini-3.6-flash"


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to persist conversation turns and extracted user facts to Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except (ValueError, AttributeError):
        # Gracefully pass if memory service is not attached in local test harnesses
        pass
    return None


async def remember_user_personal_facts(
    user_id: str = "default_user",
    personal_facts: str = "",
) -> dict[str, Any]:
    """Saves personal customer facts (e.g. marital status, having a spouse/partner,
    children/family details, car/SUV ownership, remote job status) into Vertex AI Memory Bank
    specifically indexed by the customer's user_id.

    Args:
        user_id: Customer's unique identifier.
        personal_facts: Description of personal facts (e.g. 'User is married, has an 8-year-old son, owns an SUV needing parking, works remotely').

    Returns:
        Confirmation dictionary indicating the facts have been remembered in Vertex AI Memory Bank.
    """
    if not personal_facts or not user_id:
        return {"status": "skipped", "message": "user_id and personal_facts required"}

    from google.adk.memory.base_memory_service import MemoryEntry
    from .app_utils.services import get_memory_service

    svc = get_memory_service()
    entry = MemoryEntry(
        author="user",
        content=types.Content(parts=[types.Part(text=personal_facts)]),
    )
    try:
        await svc.add_memory(
            app_name="neighborhood_match",
            user_id=user_id,
            memories=[entry],
        )
        return {
            "status": "success",
            "message": f"Personal facts successfully persisted in Vertex AI Memory Bank for user '{user_id}'.",
            "remembered_facts": personal_facts,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def search_user_memory(
    user_id: str = "default_user",
    query: str = "marital status family children car vehicle remote job",
) -> dict[str, Any]:
    """Retrieves remembered personal facts (marital status, car/SUV, family/kids, remote work)
    from Vertex AI Memory Bank for this specific customer.

    Args:
        user_id: Customer's unique identifier.
        query: Search query for personal memory retrieval.

    Returns:
        List of remembered personal facts from Vertex AI Memory Bank.
    """
    if not user_id:
        return {"memories": []}

    from .app_utils.services import get_memory_service

    svc = get_memory_service()
    try:
        resp = await svc.search_memory(
            app_name="neighborhood_match",
            user_id=user_id,
            query=query,
        )
        memories = [
            m.content.parts[0].text
            for m in resp.memories
            if m.content and m.content.parts and m.content.parts[0].text
        ]
        return {
            "user_id": user_id,
            "found_count": len(memories),
            "memories": memories,
        }
    except Exception as e:
        return {"user_id": user_id, "found_count": 0, "memories": []}


def get_or_check_customer_profile(user_id: str = "default_user") -> dict[str, Any]:
    """Checks if the customer already has a profile in the Firestore database.
    If first-time visitor, returns guidance to collect their current living location,
    relocation goals, family/school needs, car/parking, remote work, and walkability/safety priorities.

    Args:
        user_id: Customer's unique identifier.

    Returns:
        Customer profile dict or status indicating first-time visitor.
    """
    profile = get_customer_profile(user_id)
    if not profile:
        return {
            "status": "new_customer",
            "message": "First-time customer detected. Conduct an intake interview: ask where they currently live, destination city, rent vs buy, budget, family/school needs, car/parking needs, remote work setup, and priorities for safety vs walkability.",
            "profile": None,
        }
    return {
        "status": "returning_customer",
        "message": f"Returning customer recognized (iteration #{profile.get('iteration_count', 1)}). Currently living in: {profile.get('current_location', 'Unknown')}, target: {profile.get('target_city', 'Austin')}.",
        "profile": profile,
    }


def save_customer_intake_profile(
    user_id: str = "default_user",
    current_location: str = "",
    target_city: str = "Austin, TX",
    housing_type: str = "rent",
    target_price: float = 2400.0,
    reason_for_leaving: str = "",
    crime_level_answer: str = "",
    crime_safety_priority: int = 8,
    walkability_priority: int = 5,
    school_priority: int = 8,
    max_budget: float = 2400.0,
    family_details: str = "",
    has_car: bool = True,
    remote_work: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Persists customer intake data, housing price, crime answers, and reasons for leaving
    into Cloud Firestore (both in customer_profiles and indexed in relocation_statistics).

    Args:
        user_id: Unique customer ID.
        current_location: Where the customer is currently living (e.g. 'Brooklyn, NY').
        target_city: Desired relocation city (e.g. 'Austin, TX').
        housing_type: 'rent' or 'buy'.
        target_price: Desired price of apartment or house (monthly rent or home purchase budget).
        reason_for_leaving: Why they want to leave their current place (e.g. 'high rent, cramped space, safety concerns, seeking better schools').
        crime_level_answer: Customer's specific answer or requirements about crime level and safety.
        crime_safety_priority: 1 to 10 scale of importance for low crime and high neighborhood safety.
        walkability_priority: 1 to 10 scale of importance for walkable shops/cafes/errands.
        school_priority: 1 to 10 scale of importance for top-rated public or private schools.
        max_budget: Optional budget parameter (alias for target_price).
        family_details: Description of family/children/pets.
        has_car: Vehicle ownership and parking requirements.
        remote_work: Remote work status.

    Returns:
        Dictionary confirmation of saved profile in Firestore.
    """
    resolved_price = target_price or max_budget
    saved = save_customer_profile(
        user_id=user_id,
        current_location=current_location,
        target_city=target_city,
        housing_type=housing_type,
        target_price=resolved_price,
        max_budget=resolved_price,
        reason_for_leaving=reason_for_leaving,
        crime_level_answer=crime_level_answer,
        crime_safety_priority=crime_safety_priority,
        walkability_priority=walkability_priority,
        school_priority=school_priority,
        family_details=family_details,
        has_car=has_car,
        remote_work=remote_work,
        **kwargs,
    )
    return {"status": "saved", "profile": saved}


def get_customer_relocation_statistics(
    origin_city: str = "",
    target_city: str = "Austin",
) -> dict[str, Any]:
    """Retrieves aggregated statistics and trends from Firestore on why people leave,
    housing prices (rent/buy), and crime level preferences from past customer inquiries.

    Args:
        origin_city: Optional filter by origin city (e.g. 'Brooklyn', 'New York', 'San Francisco').
        target_city: Target relocation city (defaults to 'Austin').

    Returns:
        Summary of statistics: common reasons for leaving, average prices for renting/buying,
        crime/safety scores, and community trends to answer customer questions.
    """
    return get_relocation_statistics(origin_city=origin_city, target_city=target_city)


def rank_neighborhoods_by_preference(
    city: str = "Austin",
    user_id: str = "default_user",
    walk_weight: int | None = None,
    safety_weight: int | None = None,
    school_weight: int | None = None,
    remote_weight: int | None = None,
    car_weight: int | None = None,
) -> list[dict[str, Any]]:
    """Queries indexed neighborhood statistics in Firestore (walkability, crime/safety,
    school quality, remote work, car friendliness, budget) and calculates a weighted match score
    customized to the customer's profile.

    Args:
        city: Target city to rank neighborhoods for (e.g. 'Austin', 'Raleigh', 'Seattle').
        user_id: Customer ID used to retrieve preferences from Firestore.
        walk_weight: Optional 1-10 priority override for walkability.
        safety_weight: Optional 1-10 priority override for crime and safety.
        school_weight: Optional 1-10 priority override for school ratings.
        remote_weight: Optional 1-10 priority override for remote work viability.
        car_weight: Optional 1-10 priority override for parking/vehicle convenience.

    Returns:
        Ranked list of neighborhoods with composite match score and indexed metrics.
    """
    return query_neighborhood_rankings(
        city=city,
        user_id=user_id,
        walk_weight=walk_weight,
        safety_weight=safety_weight,
        school_weight=school_weight,
        remote_weight=remote_weight,
        car_weight=car_weight,
    )


def lookup_neighborhood_stats(neighborhood: str, city: str) -> dict[str, Any]:
    """Retrieves objective statistics for a neighborhood including safety/crime,
    school quality, remote work viability, and median housing costs.

    Args:
        neighborhood: Name of the neighborhood or district.
        city: Name of the city (e.g. 'Austin', 'San Francisco', 'Raleigh').

    Returns:
        A dictionary containing crime index, school ratings, remote work score,
        median rent, median purchase price, parking/car friendliness, and pros/cons.
    """
    key = f"{neighborhood.lower().strip()}_{city.lower().strip()}"

    # Curated knowledge base of representative neighborhood profiles
    neighborhoods_db = {
        "round rock_austin": {
            "neighborhood": "Round Rock",
            "city": "Austin Metro",
            "crime_rating": "A (Very Low Crime / Safe)",
            "school_rating": "9/10 (Exemplary public school district)",
            "remote_work_score": "9.5/10 (High-speed fiber ubiquitous, quiet suburban setting)",
            "car_friendliness": "Excellent (2+ car garages, ample parking, easy highway access)",
            "median_rent_2br": "$1,950/mo",
            "median_home_price": "$460,000",
            "pros": [
                "Top-tier public schools for kids",
                "Extremely safe family-oriented community",
                "Spacious homes and rental units with dedicated parking",
            ],
            "cons": [
                "Requires a car for most daily errands",
                "Suburban lifestyle with limited late-night nightlife",
            ],
        },
        "cedar park_austin": {
            "neighborhood": "Cedar Park",
            "city": "Austin Metro",
            "crime_rating": "A- (Very Low Crime)",
            "school_rating": "9/10 (Leander ISD - Top rated)",
            "remote_work_score": "9.2/10 (Fast fiber, peaceful residential streets)",
            "car_friendliness": "Excellent (Spacious parking, wide roads)",
            "median_rent_2br": "$1,850/mo",
            "median_home_price": "$480,000",
            "pros": [
                "Great parks, sports complexes, and family amenities",
                "High safety score and excellent schools",
            ],
            "cons": ["Traffic during peak commuter hours into central downtown"],
        },
        "downtown_austin": {
            "neighborhood": "Downtown",
            "city": "Austin",
            "crime_rating": "C+ (Moderate urban property crime)",
            "school_rating": "6/10 (Fewer public school options, mostly private)",
            "remote_work_score": "8.0/10 (High-speed fiber, but urban street noise)",
            "car_friendliness": "Fair (Expensive paid garage parking, congested streets)",
            "median_rent_2br": "$3,200/mo",
            "median_home_price": "$780,000",
            "pros": [
                "Vibrant nightlife, walkable dining, and live entertainment"
            ],
            "cons": [
                "High housing costs",
                "Not ideal for families with young children seeking top public schools",
                "Street parking is scarce and costly",
            ],
        },
        "cary_raleigh": {
            "neighborhood": "Cary",
            "city": "Raleigh-Durham",
            "crime_rating": "A+ (One of the safest towns in the nation)",
            "school_rating": "9.5/10 (Wake County top magnet & base schools)",
            "remote_work_score": "9.8/10 (Google Fiber, quiet green neighborhoods)",
            "car_friendliness": "Excellent (Easy parking everywhere)",
            "median_rent_2br": "$1,800/mo",
            "median_home_price": "$520,000",
            "pros": [
                "Exceptional safety and school ratings",
                "Large greenway trail system and family parks",
            ],
            "cons": ["Higher purchase price relative to rural NC"],
        },
        "bellevue_seattle": {
            "neighborhood": "Bellevue",
            "city": "Seattle Metro",
            "crime_rating": "A (Low crime)",
            "school_rating": "9.5/10 (Nationally ranked public schools)",
            "remote_work_score": "9.5/10 (High speed tech infrastructure)",
            "car_friendliness": "Good (Dedicated parking available in most residential communities)",
            "median_rent_2br": "$2,900/mo",
            "median_home_price": "$1,250,000",
            "pros": [
                "World-class schools and safe parks",
                "Clean and modern urban-suburban mix",
            ],
            "cons": ["High cost of living and expensive real estate"],
        },
    }

    # Match or generate tailored profile for queried area
    for k, data in neighborhoods_db.items():
        if k in key or key in k:
            return data

    return {
        "neighborhood": neighborhood.title(),
        "city": city.title(),
        "crime_rating": "B+ (Moderate-to-low crime)",
        "school_rating": "8/10 (Above state average schools)",
        "remote_work_score": "8.8/10 (Standard gigabit broadband available)",
        "car_friendliness": "Good (Dedicated street or off-street parking available)",
        "median_rent_2br": "$2,100/mo",
        "median_home_price": "$430,000",
        "pros": [
            "Good residential community balance",
            "Reasonable accessibility to essential services and recreation",
        ],
        "cons": [
            "Moderate traffic during peak hours; check specific street ratings for school zoning"
        ],
    }


def search_housing_listings(
    location: str, property_type: str = "rent", max_budget: int = 3500, min_bedrooms: int = 2
) -> list[dict[str, Any]]:
    """Searches available housing listings matching criteria.

    Args:
        location: City or neighborhood to search in.
        property_type: 'rent' (apartment/townhouse) or 'buy' (single family house/condo).
        max_budget: Maximum monthly rent or total purchase budget in USD.
        min_bedrooms: Minimum number of bedrooms needed.

    Returns:
        List of matching property listings with price, specs, and parking info.
    """
    listings = [
        {
            "id": "LST-101",
            "title": "Sunlit 2BR Garden Apartment with Reserved Parking",
            "neighborhood": "Round Rock",
            "city": "Austin",
            "type": "rent",
            "price_monthly": 1850,
            "bedrooms": 2,
            "bathrooms": 2,
            "parking": "2 reserved covered parking spots included",
            "highlights": "Quiet corner unit, high-speed fiber ready, zoned for top elementary school.",
        },
        {
            "id": "LST-102",
            "title": "Spacious 3BR Townhome with 2-Car Garage",
            "neighborhood": "Cedar Park",
            "city": "Austin",
            "type": "rent",
            "price_monthly": 2250,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "parking": "Attached 2-car garage + driveway",
            "highlights": "Dedicated home office space, fenced yard, walk to neighborhood park.",
        },
        {
            "id": "LST-103",
            "title": "Modern 2BR High-Rise Residence",
            "neighborhood": "Downtown",
            "city": "Austin",
            "type": "rent",
            "price_monthly": 3100,
            "bedrooms": 2,
            "bathrooms": 2,
            "parking": "1 valet garage space ($200/mo optional)",
            "highlights": "Rooftop pool, skyline views, steps from dining.",
        },
        {
            "id": "LST-104",
            "title": "Charming 3BR Craftsman Home in Family Cul-de-Sac",
            "neighborhood": "Cary",
            "city": "Raleigh",
            "type": "rent",
            "price_monthly": 2100,
            "bedrooms": 3,
            "bathrooms": 2,
            "parking": "2-car garage + private driveway",
            "highlights": "Quiet street, 5-minute walk to elementary school, Google Fiber connected.",
        },
    ]

    filtered = []
    for item in listings:
        if item["bedrooms"] >= min_bedrooms:
            if property_type.lower() in item["type"].lower() and item["price_monthly"] <= max_budget:
                filtered.append(item)

    if not filtered:
        # Fallback simulated listing matching the exact requested params
        filtered.append({
            "id": "LST-CUSTOM",
            "title": f"Comfortable {min_bedrooms}BR Home with Parking",
            "neighborhood": location.title(),
            "city": location.title(),
            "type": property_type.lower(),
            "price_monthly": min(max_budget, 2400) if property_type == "rent" else max_budget,
            "bedrooms": min_bedrooms,
            "bathrooms": 2,
            "parking": "Dedicated driveway / 2-car garage included",
            "highlights": "Family-friendly residential area with quiet work-from-home setting.",
        })

    return filtered


def calculate_monthly_budget(
    property_type: str,
    price: int,
    down_payment: int = 0,
    interest_rate_pct: float = 6.5,
) -> dict[str, Any]:
    """Calculates estimated total monthly housing expense including utilities, taxes, or HOA.

    Args:
        property_type: 'rent' or 'buy'.
        price: Monthly rent amount or total purchase price.
        down_payment: Down payment amount in USD (if buying).
        interest_rate_pct: Annual mortgage interest rate percentage.

    Returns:
        Estimated monthly total cost breakdown.
    """
    if property_type.lower() == "rent":
        est_utilities = 220
        est_renters_insurance = 25
        est_parking = 0  # assuming included in suburban listings
        total = price + est_utilities + est_renters_insurance + est_parking
        return {
            "property_type": "rent",
            "base_rent": price,
            "utilities": est_utilities,
            "insurance": est_renters_insurance,
            "parking": est_parking,
            "estimated_total_monthly": total,
        }
    else:
        loan_amount = max(0, price - down_payment)
        monthly_rate = (interest_rate_pct / 100) / 12
        months = 360
        if monthly_rate > 0 and loan_amount > 0:
            principal_interest = (
                loan_amount * (monthly_rate * (1 + monthly_rate) ** months)
            ) / ((1 + monthly_rate) ** months - 1)
        else:
            principal_interest = loan_amount / months if loan_amount else 0

        property_tax = (price * 0.018) / 12  # approx 1.8% annual
        homeowners_insurance = 150
        est_hoa = 60
        est_utilities = 280
        total = round(principal_interest + property_tax + homeowners_insurance + est_hoa + est_utilities)
        return {
            "property_type": "buy",
            "purchase_price": price,
            "down_payment": down_payment,
            "monthly_principal_and_interest": round(principal_interest),
            "monthly_property_tax": round(property_tax),
            "monthly_insurance_and_hoa": round(homeowners_insurance + est_hoa),
            "monthly_utilities": est_utilities,
            "estimated_total_monthly": total,
        }


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

INSTRUCTION = schema_manager.generate_system_prompt(
    role_description=(
        "You are an expert Relocation and Neighborhood Concierge assistant. "
        "Your mission is to help customers figure out the ideal place to move and live "
        "(renting an apartment or buying a house) based on their specific lifestyle, family, "
        "and financial needs. You have two dedicated persistence layers: Vertex AI Memory Bank and Google Cloud Firestore.\n\n"
        "1. Identify Customer & Memory Check:\n"
        "   - Notice if the customer's message starts with a [User: <id>] tag (or default to 'default_user' if absent).\n"
        "   - Call search_user_memory(user_id) to retrieve remembered personal facts (marital status, kids, car, remote job) and get_or_check_customer_profile(user_id) to check Firestore.\n\n"
        "2. Strict Data Separation Architecture:\n"
        "   - [MEMORY BANK BY USER ID]: Remember personal identity attributes (e.g., married or single, children/family, car/SUV ownership, remote work). Always call remember_user_personal_facts(user_id, personal_facts) when learning or updating these.\n"
        "   - [FIRESTORE DATABASE]: Record transactional and community criteria: where they are living now, why they want to leave their current city, what price of apartment or house they are targeting, and their answer about acceptable crime level / safety priorities. Always call save_customer_intake_profile(...) with these fields so they are indexed in Firestore for statistics and future answers.\n\n"
        "3. Answering Questions with Relocation Statistics:\n"
        "   - If a customer asks what other people are doing, why other movers leave their current city (e.g. New York, San Francisco, Chicago), typical apartment/home prices, or crime sentiments, call get_customer_relocation_statistics(origin_city, target_city) to share authentic aggregated community statistics.\n\n"
        "4. Recommendations & Beautiful Presentation:\n"
        "   - Call rank_neighborhoods_by_preference to query indexed neighborhood metrics (walkability, crime/safety, schools, remote work, car friendliness, budget) and score top matches.\n"
        "   - For deeper details, use lookup_neighborhood_stats, search_housing_listings, or calculate_monthly_budget.\n"
        "   - Present answers with clean markdown headings (###), bullet points, and neat formatting. Highlight the #1 recommendation with an A2UI Card."
    ),
    workflow_description=(
        "1. Check customer ID from [User: <id>]. Check search_user_memory and get_or_check_customer_profile.\n"
        "2. If first-time visitor, warmly greet them and gather any missing information: where they live now, why they want to leave, target city, apartment/home price budget, crime level expectations, and personal status (marital status, kids, car, remote job).\n"
        "3. Route personal status (married, kids, car, remote job) to remember_user_personal_facts(user_id, personal_facts) for Memory Bank.\n"
        "4. Route location, reason for leaving, apartment/house price, and crime level answers to save_customer_intake_profile(...) for Firestore.\n"
        "5. If asked about community trends or other movers, call get_customer_relocation_statistics.\n"
        "6. Rank neighborhoods with rank_neighborhoods_by_preference and return formatted guidance alongside an A2UI card."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[
        PreloadMemoryTool(),
        get_or_check_customer_profile,
        remember_user_personal_facts,
        search_user_memory,
        save_customer_intake_profile,
        get_customer_relocation_statistics,
        rank_neighborhoods_by_preference,
        lookup_neighborhood_stats,
        search_housing_listings,
        calculate_monthly_budget,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
