from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    original = deepcopy(app_module.activities)
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original))
    yield
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original))


def test_get_activities_returns_activity_catalog():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["max_participants"] == 12
    assert "participants" in payload["Chess Club"]


def test_signup_for_activity_adds_student_and_avoids_duplicates():
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/Basketball Club/signup?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Basketball Club"
    assert email in app_module.activities["Basketball Club"]["participants"]

    duplicate_response = client.post(f"/activities/Basketball Club/signup?email={email}")
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_404_when_activity_does_not_exist():
    response = client.post("/activities/Unknown Club/signup?email=student@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_activities_that_are_full():
    app_module.activities["Test Club"] = {
        "description": "A test club",
        "schedule": "Mondays, 4:00 PM - 5:00 PM",
        "max_participants": 1,
        "participants": ["existing@mergington.edu"],
    }

    response = client.post("/activities/Test Club/signup?email=new@mergington.edu")

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_removes_student_and_returns_404_when_missing():
    email = "test@mergington.edu"
    app_module.activities["Basketball Club"]["participants"].append(email)

    response = client.delete(f"/activities/Basketball Club/signup?email={email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Basketball Club"
    assert email not in app_module.activities["Basketball Club"]["participants"]

    missing_response = client.delete("/activities/Basketball Club/signup?email=missing@mergington.edu")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Student is not signed up for this activity"
