import pytest
from app.firestore_db import (
    get_customer_profile,
    save_customer_profile,
    query_neighborhood_rankings,
    seed_neighborhood_database,
)
from app.agent import (
    get_or_check_customer_profile,
    save_customer_intake_profile,
    rank_neighborhoods_by_preference,
)


def test_firestore_profile_and_ranking():
    user_id = "test_unit_user_42"
    # 1. New profile check
    res = get_or_check_customer_profile(user_id)
    assert "status" in res

    # 2. Save intake profile
    saved = save_customer_intake_profile(
        user_id=user_id,
        current_location="Brooklyn, NY",
        target_city="Austin",
        housing_type="buy",
        max_budget=500000,
        family_details="Family with 8yo boy needing top elementary school",
        has_car=True,
        remote_work=True,
        walkability_priority=3,
        crime_safety_priority=10,
        school_priority=10,
    )
    assert saved["status"] == "saved"
    assert saved["profile"]["current_location"] == "Brooklyn, NY"
    assert saved["profile"]["school_priority"] == 10

    # 3. Check profile now returning
    ret = get_or_check_customer_profile(user_id)
    assert ret["status"] == "returning_customer"
    assert ret["profile"]["target_city"] == "Austin"

    # 4. Rank neighborhoods
    rankings = rank_neighborhoods_by_preference(city="Austin", user_id=user_id)
    assert len(rankings) > 0
    # Top result should favor safety and schools over walkability for this profile
    top = rankings[0]
    assert "match_score" in top
    assert top["neighborhood"] in ["Round Rock", "Cedar Park"]
    assert top["match_score"] >= rankings[-1]["match_score"]
