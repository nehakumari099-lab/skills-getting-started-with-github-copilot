"""
Test suite for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create a test client
client = TestClient(app)


class TestGetActivities:
    """Test suite for getting activities"""
    
    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self):
        """Test that activities response contains expected activity names"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club",
            "Basketball",
            "Tennis",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in activities, f"Expected activity '{activity}' not found"
    
    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Activity '{activity_name}' missing field '{field}'"
    
    def test_participants_is_list(self):
        """Test that participants field is a list"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list), \
                f"Participants for '{activity_name}' is not a list"


class TestSignupForActivity:
    """Test suite for signing up for activities"""
    
    def test_signup_returns_200_on_success(self):
        """Test successful signup returns 200"""
        response = client.post(
            "/activities/Chess Club/signup?email=newemail@mergington.edu"
        )
        assert response.status_code == 200
    
    def test_signup_adds_participant(self):
        """Test that signup adds participant to activity"""
        email = "test_participant@mergington.edu"
        
        # Get activities before signup
        before = client.get("/activities").json()
        before_count = len(before["Chess Club"]["participants"])
        
        # Sign up
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Get activities after signup
        after = client.get("/activities").json()
        after_count = len(after["Chess Club"]["participants"])
        
        # Verify participant was added
        assert after_count == before_count + 1
        assert email in after["Chess Club"]["participants"]
    
    def test_signup_returns_404_for_nonexistent_activity(self):
        """Test that signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_duplicate_returns_400(self):
        """Test that signing up duplicate email returns 400"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_returns_message(self):
        """Test that signup returns appropriate message"""
        email = "another_test@mergington.edu"
        response = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Basketball" in data["message"]


class TestRemoveFromActivity:
    """Test suite for removing participants from activities"""
    
    def test_remove_returns_200_on_success(self):
        """Test that removal returns 200 on success"""
        response = client.post(
            "/activities/Chess Club/remove?email=michael@mergington.edu"
        )
        assert response.status_code == 200
    
    def test_remove_deletes_participant(self):
        """Test that remove actually removes the participant"""
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Add participant first
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify participant is there
        before = client.get("/activities").json()
        assert email in before[activity_name]["participants"]
        before_count = len(before[activity_name]["participants"])
        
        # Remove participant
        response = client.post(f"/activities/{activity_name}/remove?email={email}")
        assert response.status_code == 200
        
        # Verify participant is gone
        after = client.get("/activities").json()
        after_count = len(after[activity_name]["participants"])
        assert email not in after[activity_name]["participants"]
        assert after_count == before_count - 1
    
    def test_remove_returns_404_for_nonexistent_activity(self):
        """Test that removing from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/remove?email=test@mergington.edu"
        )
        assert response.status_code == 404
    
    def test_remove_returns_400_if_not_registered(self):
        """Test that removing non-registered student returns 400"""
        response = client.post(
            "/activities/Tennis/remove?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_remove_returns_message(self):
        """Test that remove returns appropriate message"""
        email = "jordan@mergington.edu"
        response = client.post(
            f"/activities/Tennis/remove?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Tennis" in data["message"]


class TestRootRedirect:
    """Test suite for root endpoint"""
    
    def test_root_redirects_to_static_index(self):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""
    
    def test_signup_and_remove_workflow(self):
        """Test complete workflow: signup then remove"""
        email = "integration_test@mergington.edu"
        activity = "Tennis"
        
        # Get initial count
        initial = client.get("/activities").json()
        initial_count = len(initial[activity]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup worked
        after_signup = client.get("/activities").json()
        assert len(after_signup[activity]["participants"]) == initial_count + 1
        assert email in after_signup[activity]["participants"]
        
        # Remove
        remove_response = client.post(f"/activities/{activity}/remove?email={email}")
        assert remove_response.status_code == 200
        
        # Verify removal worked
        after_remove = client.get("/activities").json()
        assert len(after_remove[activity]["participants"]) == initial_count
        assert email not in after_remove[activity]["participants"]
    
    def test_multiple_signups_same_activity(self):
        """Test multiple different students can sign up for same activity"""
        activity = "Drama Club"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        initial = client.get("/activities").json()
        initial_count = len(initial[activity]["participants"])
        
        # Sign up all students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all were added
        final = client.get("/activities").json()
        assert len(final[activity]["participants"]) == initial_count + len(emails)
        for email in emails:
            assert email in final[activity]["participants"]
        
        # Clean up
        for email in emails:
            client.post(f"/activities/{activity}/remove?email={email}")
