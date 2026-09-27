from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_get_activities_returns_data_without_caching(client):
    # Arrange
    expected_activity = "Soccer Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client):
    # Arrange
    email = "new-student@mergington.edu"
    activity = "Soccer Club"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    updated_activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in updated_activities[activity]["participants"]


def test_signup_for_unknown_activity_returns_not_found(client):
    # Arrange
    activity = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_duplicate_signup_returns_conflict_without_adding_participant(client):
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"
    participants_before = client.get("/activities").json()[activity]["participants"]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    participants_after = client.get("/activities").json()[activity]["participants"]

    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Student is already signed up"}
    assert participants_after == participants_before


def test_unregister_removes_participant(client):
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})
    updated_activities = client.get("/activities").json()

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in updated_activities[activity]["participants"]


def test_unregister_from_unknown_activity_returns_not_found(client):
    # Arrange
    activity = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_nonparticipant_returns_not_found(client):
    # Arrange
    activity = "Soccer Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up"}