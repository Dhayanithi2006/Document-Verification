# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Demo Environment Verification & Rehearsal Harness (scripts/rehearse_demo.py)

import os
import sys
import json
import requests
import sqlite3

BASE_URL = "http://localhost:3000/api/v1"

print("==================================================")
print("PHASE 5: DEMO REHEARSAL IN ISOLATED DEMO ENVIRONMENT")
print("Target: http://localhost:3000 -> Demo Backend (data/demo.db)")
print("==================================================")

# Step 1: Sign in as Institution Applicant
print("\n[Step 1] Sign in as Institution Applicant...")
res = requests.post(f"{BASE_URL}/auth/login", json={"email": "applicant@institution.test", "password": "Password123!"})
assert res.status_code == 200, f"Login failed: {res.status_code} {res.text}"
applicant_token = res.json()["access_token"]
headers_app = {"Authorization": f"Bearer {applicant_token}"}
print(f"  -> SUCCESS: Authenticated Dr. R. K. Sharma (role={res.json()['user']['role']})")

# Step 2: Upload a synthetic PDF and verify document record & file storage
print("\n[Step 2] Upload a synthetic PDF for FIRE_SAFETY_NOC into app_9812...")
pdf_payload = b"%PDF-1.4\n1 0 obj<< /Title (Fire NOC 2026) >>endobj\ntrailer<< >>\n%%EOF\n"
upload_res = requests.post(
    f"{BASE_URL}/applications/app_9812/documents",
    headers=headers_app,
    data={"document_type": "FIRE_SAFETY_NOC"},
    files={"file": ("fire_safety_noc_renewal_2026.pdf", pdf_payload, "application/pdf")}
)
assert upload_res.status_code == 201, f"Upload failed: {upload_res.status_code} {upload_res.text}"
up_json = upload_res.json()
print(f"  -> SUCCESS: Uploaded {up_json['file_name']}, status={up_json['status']}, version={up_json['version_number']}")

# Verify file exists in demo storage
expected_disk_dir = "storage/demo_documents/inst_01/app_9812"
files_on_disk = [f for f in os.listdir(expected_disk_dir) if "FIRE_SAFETY_NOC" in f]
assert len(files_on_disk) > 0, "No fire safety file found in demo storage!"
print(f"  -> SUCCESS: Verified on disk in {expected_disk_dir}/{files_on_disk[0]} ({os.path.getsize(os.path.join(expected_disk_dir, files_on_disk[0]))} bytes)")

# Step 3: Run pre-scrutiny and inspect evidence-linked findings
print("\n[Step 3] Run pre-scrutiny evaluation on app_9812...")
val_res = requests.post(f"{BASE_URL}/applications/app_9812/validate", headers=headers_app)
assert val_res.status_code == 200, f"Validation failed: {val_res.status_code} {val_res.text}"
val_data = val_res.json()
print(f"  -> SUCCESS: Pre-scrutiny evaluated {val_data['total_checks']} rules: summary={val_data['findings_summary']}")

# Retrieve findings
findings_res = requests.get(f"{BASE_URL}/applications/app_9812/findings", headers=headers_app)
assert findings_res.status_code == 200
findings = findings_res.json()["findings"]
for f in findings:
    print(f"     - [{f['rule_code']}] severity={f['severity']}, title='{f['title']}'")

# Step 4: Save draft and submit a valid correction response
print("\n[Step 4] Save draft and submit a valid correction response...")
# Find deficiency for RULE-EOA-BCC-002
bcc_finding = next(f for f in findings if f["rule_code"] == "RULE-EOA-BCC-002")

# Save draft
draft_res = requests.put(
    f"{BASE_URL}/findings/{bcc_finding['id']}/response",
    headers=headers_app,
    json={
        "response_text": "Permanent Occupancy Certificate BBMP/OC/2026/8912 is submitted. Full municipal sanction verified.",
        "response_category": "DOCUMENT_REPLACEMENT"
    }
)
assert draft_res.status_code == 200, f"Draft failed: {draft_res.status_code} {draft_res.text}"
print(f"  -> SUCCESS: Saved correction draft for finding {bcc_finding['id']}")

# Submit correction
submit_res = requests.post(
    f"{BASE_URL}/findings/{bcc_finding['id']}/submit",
    headers=headers_app,
    json={
        "response_text": "Permanent Occupancy Certificate BBMP/OC/2026/8912 is submitted. Full municipal sanction verified.",
        "response_category": "DOCUMENT_REPLACEMENT"
    }
)
assert submit_res.status_code in [200, 201], f"Submit correction failed: {submit_res.status_code} {submit_res.text}"
print(f"  -> SUCCESS: Submitted correction response (status={submit_res.json().get('status')})")

# Step 5: Sign in as Reviewer and inspect case
print("\n[Step 5] Sign in as Reviewer and inspect case app_9812...")
rev_login = requests.post(f"{BASE_URL}/auth/login", json={"email": "reviewer@reviewer.test", "password": "ReviewerPass123!"})
assert rev_login.status_code == 200
rev_token = rev_login.json()["access_token"]
headers_rev = {"Authorization": f"Bearer {rev_token}"}
print(f"  -> SUCCESS: Authenticated Prof. K. S. Krishnan (role={rev_login.json()['user']['role']})")

case_res = requests.get(f"{BASE_URL}/reviewer/applications/app_9812/scrutiny", headers=headers_rev)
assert case_res.status_code == 200, f"Reviewer case get failed: {case_res.status_code}"
case_data = case_res.json()
print(f"  -> SUCCESS: Reviewer retrieved case {case_data['application']['application_number']}, findings={len(case_data['findings'])}, submissions={len(case_data['correction_submissions'])}")

# Step 6: Confirm blocking deficiencies prevent prohibited clearance
print("\n[Step 6] Test Reviewer Approval Guard against open blocking deficiencies...")
signoff_res = requests.post(
    f"{BASE_URL}/reviewer/applications/app_9812/decision",
    headers=headers_rev,
    json={"decision": "PRE_SCRUTINY_RECOMMENDED_CLEAR", "remarks": "Attempting premature signoff without clearing deficiencies"}
)
print(f"  -> Signoff response code: {signoff_res.status_code}")
assert signoff_res.status_code in [400, 422], f"Expected 400/422 but got {signoff_res.status_code}"
assert "cannot recommend" in signoff_res.text.lower() or "deficiencies remain open" in signoff_res.text.lower() or "blocking" in signoff_res.text.lower()
print(f"  -> SUCCESS: System strictly blocked clearance: '{signoff_res.json()['detail']}'")

# Step 7: Record a permitted reviewer observation
print("\n[Step 7] Record permitted Reviewer Observation...")
obs_res = requests.post(
    f"{BASE_URL}/reviewer/applications/app_9812/observations",
    headers=headers_rev,
    json={
        "finding_id": bcc_finding["id"],
        "decision": "GENERAL_OBSERVATION",
        "justification": "Institutional clarification for building completion received. Committee noted pending verification of municipal registry.",
        "is_internal_note": False
    }
)
assert obs_res.status_code in [200, 201], f"Observation failed: {obs_res.status_code} {obs_res.text}"
print(f"  -> SUCCESS: Recorded committee observation ID={obs_res.json()['id']}")

# Step 8: Sign in as Administrator and inspect accounts, rules, and audit
print("\n[Step 8] Sign in as Administrator and inspect governance records...")
adm_login = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@platform.test", "password": "AdminPass123!"})
assert adm_login.status_code == 200
adm_token = adm_login.json()["access_token"]
headers_adm = {"Authorization": f"Bearer {adm_token}"}
print(f"  -> SUCCESS: Authenticated System Administrator (role={adm_login.json()['user']['role']})")

# Users list
users_res = requests.get(f"{BASE_URL}/admin/users", headers=headers_adm)
assert users_res.status_code == 200
print(f"  -> SUCCESS: Admin retrieved {len(users_res.json())} user accounts")

# Rules list
rules_res = requests.get(f"{BASE_URL}/rules", headers=headers_adm)
assert rules_res.status_code == 200
print(f"  -> SUCCESS: Admin retrieved {len(rules_res.json())} regulatory rules")

# Audit events
audit_res = requests.get(f"{BASE_URL}/admin/audit-events", headers=headers_adm)
assert audit_res.status_code == 200
events = audit_res.json()
print(f"  -> SUCCESS: Admin retrieved {len(events)} forensic audit events")
recent_actions = [e["action"] for e in events[:5]]
print(f"     Recent actions: {recent_actions}")

# Step 9: Verify consistency across roles
print("\n[Step 9] Verify cross-role consistency for app_9812...")
app_status_applicant = requests.get(f"{BASE_URL}/applications/app_9812", headers=headers_app).json()["status"]
app_status_reviewer = requests.get(f"{BASE_URL}/reviewer/applications/app_9812/scrutiny", headers=headers_rev).json()["application"]["status"]
assert app_status_applicant == app_status_reviewer, f"Mismatch: applicant sees {app_status_applicant}, reviewer sees {app_status_reviewer}"
print(f"  -> SUCCESS: Both applicant and reviewer see identical application status: '{app_status_applicant}'")

# Step 10: Refresh and confirm persisted state in data/demo.db
print("\n[Step 10] Confirm persisted database state in data/demo.db...")
demo_conn = sqlite3.connect("file:data/demo.db?mode=ro", uri=True)
c = demo_conn.cursor()
c.execute("SELECT count(*) FROM users;")
u_cnt = c.fetchone()[0]
c.execute("SELECT count(*) FROM applications;")
a_cnt = c.fetchone()[0]
c.execute("SELECT count(*) FROM documents;")
d_cnt = c.fetchone()[0]
c.execute("SELECT count(*) FROM findings;")
f_cnt = c.fetchone()[0]
c.execute("SELECT count(*) FROM correction_submissions;")
cs_cnt = c.fetchone()[0]
c.execute("SELECT count(*) FROM reviewer_observations;")
ro_cnt = c.fetchone()[0]
c.execute("SELECT count(*) FROM audit_events;")
ae_cnt = c.fetchone()[0]
demo_conn.close()

print(f"  -> Users: {u_cnt}")
print(f"  -> Applications: {a_cnt}")
print(f"  -> Documents: {d_cnt}")
print(f"  -> Findings: {f_cnt}")
print(f"  -> Correction Submissions: {cs_cnt}")
print(f"  -> Reviewer Observations: {ro_cnt}")
print(f"  -> Audit Events: {ae_cnt}")

print("\n==================================================")
print("ALL 10 DEMO REHEARSAL VERIFICATION STEPS PASSED (100%)")
print("==================================================")
