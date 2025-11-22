#!/usr/bin/env python3
"""
Quick test script to verify the seed data fixes work.
"""
import httpx
from datetime import date, timedelta
import random

API_URL = "http://localhost:8000"

# Get admin token
print("Getting admin token...")
login_response = httpx.post(f"{API_URL}/auth/login", json={
    "email": "admin@repensar.org",
    "password": "AdminPass123!"
})

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

admin_token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {admin_token}"}
print("✅ Admin token obtained")

# Test 1: Get a volunteer
print("\n📋 Test 1: Getting volunteers...")
volunteers_response = httpx.get(f"{API_URL}/volunteers/?limit=5", headers=headers)
if volunteers_response.status_code == 200:
    volunteers = volunteers_response.json()
    if len(volunteers) > 0:
        volunteer = volunteers[0]
        volunteer_id = volunteer.get("id")
        print(f"✅ Found volunteer ID: {volunteer_id}")

        # Test 2: Create volunteer time log with correct schema
        print("\n📋 Test 2: Creating volunteer time log...")
        time_log_data = {
            "volunteer_id": volunteer_id,
            "date": (date.today() - timedelta(days=5)).isoformat(),
            "hours": 4.5,  # Changed from hours_worked
            "activity_description": "Plantou 25 mudas de espécies nativas na zona ripária"
            # Removed 'approved' field
        }

        log_response = httpx.post(
            f"{API_URL}/volunteers/{volunteer_id}/hours",
            json=time_log_data,
            headers=headers
        )

        if log_response.status_code in [200, 201]:
            print(f"✅ Time log created successfully!")
            print(f"   Response: {log_response.json()}")
        else:
            print(f"❌ Time log failed: {log_response.status_code}")
            print(f"   Error: {log_response.text}")
    else:
        print("⚠️  No volunteers found")
else:
    print(f"❌ Failed to get volunteers: {volunteers_response.status_code}")

# Test 3: Get a project for milestone/metric tests
print("\n📋 Test 3: Getting projects...")
projects_response = httpx.get(f"{API_URL}/projects/?page_size=5", headers=headers)
if projects_response.status_code == 200:
    projects_data = projects_response.json()
    # Handle both list and paginated response formats
    projects = projects_data if isinstance(projects_data, list) else projects_data.get("items", [])
    if len(projects) > 0:
        project = projects[0]
        project_id = project.get("id")
        print(f"✅ Found project ID: {project_id}")

        # Test 4: Create milestone
        print("\n📋 Test 4: Creating milestone...")
        milestone_data = {
            "project_id": project_id,  # Required by schema
            "name": "Primeira Colheita",
            "description": "Marco importante para monitoramento e avaliação do projeto.",
            "target_date": (date.today() + timedelta(days=90)).isoformat(),
            "status": "pending"
        }

        milestone_response = httpx.post(
            f"{API_URL}/projects/{project_id}/milestones",
            json=milestone_data,
            headers=headers
        )

        if milestone_response.status_code in [200, 201]:
            print(f"✅ Milestone created successfully!")
        else:
            print(f"❌ Milestone failed: {milestone_response.status_code}")
            print(f"   Error: {milestone_response.text}")

        # Test 5: Create environmental metric
        print("\n📋 Test 5: Creating environmental metric...")
        metric_data = {
            "project_id": project_id,  # Required by schema
            "metric_name": "Árvores Plantadas",
            "metric_type": "count",
            "unit": "árvores",
            "current_value": 150.0,
            "target_value": 1000.0,
            "measurement_date": date.today().isoformat()
        }

        metric_response = httpx.post(
            f"{API_URL}/projects/{project_id}/metrics",
            json=metric_data,
            headers=headers
        )

        if metric_response.status_code in [200, 201]:
            print(f"✅ Environmental metric created successfully!")
        else:
            print(f"❌ Metric failed: {metric_response.status_code}")
            print(f"   Error: {metric_response.text}")
    else:
        print("⚠️  No projects found")
else:
    print(f"❌ Failed to get projects: {projects_response.status_code}")

print("\n" + "="*60)
print("✅ Tests completed!")
print("="*60)
