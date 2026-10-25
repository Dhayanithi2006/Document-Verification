# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Tenant Isolation & IDOR Prevention Tests (tests/backend/test_isolation.py)

import pytest
from fastapi import status


def get_token(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == status.HTTP_200_OK
    return res.json()["access_token"]


def test_tenant_isolation_on_application_detail(client):
    """Verifies that an Institution User cannot access another institution's application (IDOR Prevention)."""
    # User 1 belongs to Institution 1 (inst_01)
    token_inst1 = get_token(client, "applicant@institution.test", "Password123!")
    
    # 1. User 1 accessing own application (app_9812 / inst_01) -> 200 OK
    res_own = client.get(
        "/api/v1/applications/app_9812",
        headers={"Authorization": f"Bearer {token_inst1}"}
    )
    assert res_own.status_code == status.HTTP_200_OK
    assert res_own.json()["application_number"] == "AICTE-EOA-2026-9812"

    # 2. User 1 accessing Institution 2's application (app_9813 / inst_02) -> 404 Not Found
    res_foreign = client.get(
        "/api/v1/applications/app_9813",
        headers={"Authorization": f"Bearer {token_inst1}"}
    )
    assert res_foreign.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in res_foreign.json()["detail"].lower()


def test_tenant_isolation_on_application_listing(client):
    """Verifies that listing applications returns only records belonging to the caller's institution."""
    token_inst1 = get_token(client, "applicant@institution.test", "Password123!")
    token_inst2 = get_token(client, "applicant2@institution2.test", "Password123!")
    token_reviewer = get_token(client, "reviewer@reviewer.test", "ReviewerPass123!")

    # Institution 1 listing
    res_inst1 = client.get("/api/v1/applications", headers={"Authorization": f"Bearer {token_inst1}"})
    assert res_inst1.status_code == status.HTTP_200_OK
    apps_inst1 = res_inst1.json()
    assert len(apps_inst1) == 1
    assert apps_inst1[0]["institution_id"] == "inst_01"

    # Institution 2 listing
    res_inst2 = client.get("/api/v1/applications", headers={"Authorization": f"Bearer {token_inst2}"})
    assert res_inst2.status_code == status.HTTP_200_OK
    apps_inst2 = res_inst2.json()
    assert len(apps_inst2) == 1
    assert apps_inst2[0]["institution_id"] == "inst_02"

    # Reviewer listing (Authorized cross-institution scrutiny)
    res_rev = client.get("/api/v1/applications", headers={"Authorization": f"Bearer {token_reviewer}"})
    assert res_rev.status_code == status.HTTP_200_OK
    apps_rev = res_rev.json()
    assert len(apps_rev) >= 2
    inst_ids = {a["institution_id"] for a in apps_rev}
    assert "inst_01" in inst_ids and "inst_02" in inst_ids
