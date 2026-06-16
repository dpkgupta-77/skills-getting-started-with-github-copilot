"""
Comprehensive test suite for Mergington High School Activities API.

Tests cover:
- GET /activities endpoint
- POST /activities/{activity_name}/signup endpoint
- DELETE /activities/{activity_name}/signup endpoint
- Error handling and validation
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a known state before each test"""
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    activities.clear()
    activities.update(original)
    yield
    activities.clear()
    activities.update(original)


class TestGetActivities:
    """Tests for retrieving activities"""

    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activity_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_participants_list_contains_emails(self, client):
        """Test that participants list contains correct emails"""
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in participants
        assert "daniel@mergington.edu" in participants
        assert len(participants) == 2

    def test_activity_count_correct(self, client):
        """Test that participant count matches max_participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            count = len(activity_data["participants"])
            max_count = activity_data["max_participants"]
            assert count <= max_count, f"{activity_name} exceeds max participants"


class TestSignup:
    """Tests for signup functionality"""

    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_student(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        email = "michael@mergington.edu"
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple different activities"""
        email = "newstudent@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities_data = client.get("/activities").json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]

    def test_signup_increments_participant_count(self, client):
        """Test that signup increments the participant count"""
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count + 1

    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with email containing special characters"""
        email = "test+student@mergington.edu"
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200


class TestRemoveParticipant:
    """Tests for participant removal functionality"""

    def test_successful_removal(self, client):
        """Test successful removal of a participant"""
        email = "michael@mergington.edu"
        response = client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    def test_removal_removes_participant(self, client):
        """Test that removal actually removes the participant"""
        email = "michael@mergington.edu"
        client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]

    def test_remove_nonexistent_activity(self, client):
        """Test removal from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_remove_non_participant(self, client):
        """Test removal of a student who is not signed up"""
        response = client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_removal_decrements_participant_count(self, client):
        """Test that removal decrements the participant count"""
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count - 1

    def test_signup_after_removal(self, client):
        """Test that a student can sign up again after being removed"""
        email = "michael@mergington.edu"
        
        # Remove participant
        client.delete(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        
        # Sign up again
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify they're back in the list
        activities_data = client.get("/activities").json()
        assert email in activities_data["Chess Club"]["participants"]


class TestRootRedirect:
    """Tests for root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests for complex scenarios"""

    def test_signup_and_removal_workflow(self, client):
        """Test complete workflow: signup, verify, remove, verify removal"""
        email = "integration@mergington.edu"
        
        # Sign up
        response = client.post(
            "/activities/Gym%20Class/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify signup
        activities_data = client.get("/activities").json()
        assert email in activities_data["Gym Class"]["participants"]
        
        # Remove
        response = client.delete(
            "/activities/Gym%20Class/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify removal
        activities_data = client.get("/activities").json()
        assert email not in activities_data["Gym Class"]["participants"]

    def test_multiple_students_signup(self, client):
        """Test that multiple students can sign up for the same activity"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                "/activities/Programming%20Class/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are signed up
        activities_data = client.get("/activities").json()
        for email in emails:
            assert email in activities_data["Programming Class"]["participants"]

    def test_activity_data_persistence(self, client):
        """Test that activity data persists across multiple requests"""
        email = "persistence@mergington.edu"
        
        # First signup
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        
        # Multiple get requests should show consistent data
        for _ in range(3):
            response = client.get("/activities")
            data = response.json()
            assert email in data["Chess Club"]["participants"]
