#!/usr/bin/env python3
"""
Test script to verify the indexing fix
This script simulates the scenario where files are visible to users but not indexed in PGVector
"""

import requests
import json
import os

# API base URL
BASE_URL = "http://localhost:8000"

def test_indexing_fix():
    """Test the indexing fix for the RAG system"""
    
    print("🧪 Testing Indexing Fix for RAG System")
    print("=" * 50)
    
    # Test 1: Register a faculty user
    print("\n1. Registering faculty user...")
    faculty_data = {
        "username": "test_faculty",
        "email": "faculty@test.com", 
        "password": "testpass123",
        "role": "faculty"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=faculty_data)
        if response.status_code == 200:
            print("✅ Faculty user registered successfully")
        else:
            print(f"❌ Failed to register faculty user: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error registering faculty user: {e}")
        return
    
    # Test 2: Register a student user
    print("\n2. Registering student user...")
    student_data = {
        "username": "test_student",
        "email": "student@test.com",
        "password": "testpass123", 
        "role": "student"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=student_data)
        if response.status_code == 200:
            print("✅ Student user registered successfully")
        else:
            print(f"❌ Failed to register student user: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error registering student user: {e}")
        return
    
    # Test 3: Login as faculty and upload a file for students
    print("\n3. Logging in as faculty and uploading file...")
    login_data = {
        "username": "test_faculty",
        "password": "testpass123",
        "role": "faculty"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            faculty_token = response.json()["access_token"]
            print("✅ Faculty login successful")
        else:
            print(f"❌ Faculty login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error logging in as faculty: {e}")
        return
    
    # Create a test PDF file
    test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test document for students) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
    
    with open("test_document.pdf", "wb") as f:
        f.write(test_pdf_content)
    
    # Upload file as faculty
    headers = {"Authorization": f"Bearer {faculty_token}"}
    files = {"file": ("test_document.pdf", open("test_document.pdf", "rb"), "application/pdf")}
    data = {"target_roles": json.dumps(["student"])}
    
    try:
        response = requests.post(f"{BASE_URL}/upload-file", headers=headers, files=files, data=data)
        if response.status_code == 200:
            print("✅ File uploaded successfully by faculty")
        else:
            print(f"❌ File upload failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        return
    
    # Test 4: Login as student and check if file is visible
    print("\n4. Logging in as student and checking file visibility...")
    login_data = {
        "username": "test_student",
        "password": "testpass123",
        "role": "student"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            student_token = response.json()["access_token"]
            print("✅ Student login successful")
        else:
            print(f"❌ Student login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error logging in as student: {e}")
        return
    
    # Check if file is visible to student
    headers = {"Authorization": f"Bearer {student_token}"}
    try:
        response = requests.get(f"{BASE_URL}/files", headers=headers)
        if response.status_code == 200:
            files_data = response.json()
            if files_data.get("files") and len(files_data["files"]) > 0:
                print("✅ File is visible to student")
            else:
                print("❌ File is not visible to student")
                return
        else:
            print(f"❌ Failed to get files: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error getting files: {e}")
        return
    
    # Test 5: Ask a question as student (this should trigger automatic indexing)
    print("\n5. Asking question as student (should trigger automatic indexing)...")
    chat_data = {
        "message": "What is this document about?",
        "top_k": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", headers=headers, json=chat_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Chat response received")
            print(f"Response: {chat_response.get('response', 'No response')}")
            
            # Check if indexing info is included
            context = chat_response.get('context', {})
            indexing_info = context.get('indexing_info', {})
            if indexing_info.get('files_indexed', 0) > 0:
                print(f"✅ Automatic indexing triggered: {indexing_info['message']}")
            else:
                print(f"⚠️ No files were indexed: {indexing_info.get('message', 'Unknown')}")
        else:
            print(f"❌ Chat request failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error in chat request: {e}")
        return
    
    # Test 6: Ask another question to verify indexing worked
    print("\n6. Asking follow-up question to verify indexing...")
    chat_data = {
        "message": "Can you tell me more about the content?",
        "top_k": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", headers=headers, json=chat_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Follow-up response received")
            print(f"Response: {chat_response.get('response', 'No response')}")
            
            # Check if indexing info shows no new files indexed (since they should already be indexed)
            context = chat_response.get('context', {})
            indexing_info = context.get('indexing_info', {})
            if indexing_info.get('files_indexed', 0) == 0:
                print("✅ No new files indexed (expected, since files were already indexed)")
            else:
                print(f"ℹ️ {indexing_info.get('files_indexed', 0)} files indexed in follow-up")
        else:
            print(f"❌ Follow-up chat request failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error in follow-up chat request: {e}")
        return
    
    # Test 7: Test manual indexing endpoint
    print("\n7. Testing manual indexing endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/index-available-files", headers=headers)
        if response.status_code == 200:
            indexing_result = response.json()
            print(f"✅ Manual indexing result: {indexing_result['message']}")
        else:
            print(f"❌ Manual indexing failed: {response.text}")
    except Exception as e:
        print(f"❌ Error in manual indexing: {e}")
    
    # Cleanup
    print("\n8. Cleaning up test files...")
    try:
        os.remove("test_document.pdf")
        print("✅ Test file cleaned up")
    except:
        print("⚠️ Could not clean up test file")
    
    print("\n🎉 Indexing fix test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_indexing_fix() 