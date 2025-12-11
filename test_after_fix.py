"""
Test the resume roasting functionality after database fix
"""
import requests
import json

def test_resume_roasting():
    base_url = "https://faltuai.reddune-c0e74598.centralindia.azurecontainerapps.io"
    
    # Test health first
    print("Testing health endpoint...")
    response = requests.get(f"{base_url}/health")
    print(f"Health status: {response.status_code}")
    if response.status_code == 200:
        print(f"Health response: {response.json()}")
    
    # Test the test endpoint to see if core functionality works
    print("\nTesting core roasting functionality...")
    response = requests.get(f"{base_url}/api/v1/resume-roast/test")
    print(f"Test endpoint status: {response.status_code}")
    if response.status_code == 200:
        print("Test endpoint response:", response.json())
    else:
        print("Test endpoint error:", response.text)
    
    # Test langsmith status
    print("\nTesting LangSmith status...")
    response = requests.get(f"{base_url}/api/v1/resume-roast/langsmith-status")
    print(f"LangSmith status: {response.status_code}")
    if response.status_code == 200:
        print("LangSmith response:", response.json())

if __name__ == "__main__":
    test_resume_roasting()