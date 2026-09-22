import pytest
from app.agent import (
    remember_user_personal_facts,
    search_user_memory,
    get_customer_relocation_statistics,
    save_customer_intake_profile,
    get_or_check_customer_profile,
)
from app.firestore_db import get_relocation_statistics


@pytest.mark.asyncio
async def test_memory_bank_tools():
    user_id = "test_memory_user_99"
    facts = "Customer is married, has a 7yo son, drives an electric SUV, works remotely full-time."
    
    # Test saving personal facts to Memory Bank
    save_res = await remember_user_personal_facts(user_id=user_id, personal_facts=facts)
    assert save_res["status"] == "success"
    assert "Vertex AI Memory Bank" in save_res["message"]

    # Test searching Memory Bank
    search_res = await search_user_memory(user_id=user_id, query="married son SUV")
    assert search_res["user_id"] == user_id
    assert search_res["found_count"] >= 1
    assert any("married" in m.lower() for m in search_res["memories"])


def test_relocation_statistics_tool():
    # Save a profile with relocation reasons, crime answers, and budget
    user_id = "stat_test_user_88"
    save_res = save_customer_intake_profile(
        user_id=user_id,
        current_location="Brooklyn, NY",
        target_city="Austin, TX",
        housing_type="rent",
        target_price=2350,
        reason_for_leaving="Seeking lower cost of living, top schools, and peaceful neighborhoods.",
        crime_level_answer="Low crime is essential, priority 10/10.",
        crime_safety_priority=10,
        walkability_priority=4,
        school_priority=10,
    )
    assert save_res["status"] == "saved"
    assert save_res["profile"]["target_price"] == 2350

    # Query relocation statistics
    stats = get_customer_relocation_statistics(target_city="Austin")
    assert "total_inquiries_analyzed" in stats
    assert stats["total_inquiries_analyzed"] >= 1
    assert "average_target_monthly_rent" in stats
    assert "average_crime_safety_importance" in stats
    assert "insights_summary" in stats
