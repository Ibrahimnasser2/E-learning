#!/usr/bin/env python3
"""
Test script to verify the improved indexing system with file tracking
This script tests the new file tracking system that prevents duplicate indexing
"""

import requests
import json
import os
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_improved_indexing():
    """Test the improved indexing system with file tracking"""
    
    print("🧪 Testing Improved Indexing System with File Tracking")
    print("=" * 60)
    
    # Test 1: Register a faculty user
    print("\n1. Registering faculty user...")
    faculty_data = {
        "username": "test_faculty_v2",
        "email": "faculty2@test.com", 
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
        "username": "test_student_v2",
        "email": "student2@test.com",
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
        "username": "test_faculty_v2",
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
    
    # Create a test PDF file with programming content
    test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 200\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Programming Paradigms) Tj\n72 700 Td\n(Imperative Programming) Tj\n72 680 Td\n(Object-Oriented Programming) Tj\n72 660 Td\n(Functional Programming) Tj\n72 640 Tf\n(Logic Programming) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n453\n%%EOF"
    
    with open("test_programming.pdf", "wb") as f:
        f.write(test_pdf_content)
    
    # Upload file as faculty
    headers = {"Authorization": f"Bearer {faculty_token}"}
    files = {"file": ("test_programming.pdf", open("test_programming.pdf", "rb"), "application/pdf")}
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
        "username": "test_student_v2",
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
    
    # Test 5: First question - should trigger indexing
    print("\n5. First question - should trigger indexing...")
    chat_data = {
        "message": "What are programming paradigms?",
        "top_k": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", headers=headers, json=chat_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ First chat response received")
            print(f"Response: {chat_response.get('response', 'No response')}")
            
            # Check if indexing info is included
            context = chat_response.get('context', {})
            indexing_info = context.get('indexing_info', {})
            if indexing_info.get('files_indexed', 0) > 0:
                print(f"✅ Automatic indexing triggered: {indexing_info['message']}")
            else:
                print(f"⚠️ No files were indexed: {indexing_info.get('message', 'Unknown')}")
        else:
            print(f"❌ First chat request failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error in first chat request: {e}")
        return
    
    # Test 6: Second question - should NOT trigger indexing (files already indexed)
    print("\n6. Second question - should NOT trigger indexing...")
    chat_data = {
        "message": "Tell me about imperative programming",
        "top_k": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", headers=headers, json=chat_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Second chat response received")
            print(f"Response: {chat_response.get('response', 'No response')}")
            
            # Check if indexing info shows no new files indexed
            context = chat_response.get('context', {})
            indexing_info = context.get('indexing_info', {})
            if indexing_info.get('files_indexed', 0) == 0:
                print("✅ No new files indexed (expected, files already indexed)")
            else:
                print(f"⚠️ Unexpected: {indexing_info.get('files_indexed', 0)} files indexed in second request")
        else:
            print(f"❌ Second chat request failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error in second chat request: {e}")
        return
    
    # Test 7: Manual indexing - should show no new files
    print("\n7. Testing manual indexing endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/index-available-files", headers=headers)
        if response.status_code == 200:
            indexing_result = response.json()
            print(f"✅ Manual indexing result: {indexing_result['message']}")
            if indexing_result.get('files_indexed', 0) == 0:
                print("✅ Correctly shows no new files to index")
            else:
                print(f"⚠️ Unexpected: {indexing_result.get('files_indexed', 0)} files indexed manually")
        else:
            print(f"❌ Manual indexing failed: {response.text}")
    except Exception as e:
        print(f"❌ Error in manual indexing: {e}")
    
    # Test 8: Check stats to verify file tracking
    print("\n8. Checking RAG stats...")
    try:
        response = requests.get(f"{BASE_URL}/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Stats: {stats.get('total_documents', 0)} documents, {stats.get('total_chunks', 0)} chunks")
        else:
            print(f"❌ Failed to get stats: {response.text}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
    
    # Test 9: Upload another file and test indexing
    print("\n9. Uploading second file and testing indexing...")
    
    # Create second test PDF
    test_pdf_content2 = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 150\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Data Structures) Tj\n72 700 Td\n(Arrays and Lists) Tj\n72 680 Td\n(Stacks and Queues) Tj\n72 660 Td\n(Trees and Graphs) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n403\n%%EOF"
    
    with open("test_datastructures.pdf", "wb") as f:
        f.write(test_pdf_content2)
    
    # Upload second file as faculty
    files = {"file": ("test_datastructures.pdf", open("test_datastructures.pdf", "rb"), "application/pdf")}
    data = {"target_roles": json.dumps(["student"])}
    
    try:
        response = requests.post(f"{BASE_URL}/upload-file", headers=headers, files=files, data=data)
        if response.status_code == 200:
            print("✅ Second file uploaded successfully")
        else:
            print(f"❌ Second file upload failed: {response.text}")
    except Exception as e:
        print(f"❌ Error uploading second file: {e}")
    
    # Test 10: Ask question about new file - should trigger indexing
    print("\n10. Asking question about new file - should trigger indexing...")
    chat_data = {
        "message": "What are data structures?",
        "top_k": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", headers=headers, json=chat_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Third chat response received")
            print(f"Response: {chat_response.get('response', 'No response')}")
            
            # Check if indexing info shows new files indexed
            context = chat_response.get('context', {})
            indexing_info = context.get('indexing_info', {})
            if indexing_info.get('files_indexed', 0) > 0:
                print(f"✅ New files indexed: {indexing_info['message']}")
            else:
                print(f"⚠️ No new files indexed: {indexing_info.get('message', 'Unknown')}")
        else:
            print(f"❌ Third chat request failed: {response.text}")
    except Exception as e:
        print(f"❌ Error in third chat request: {e}")
    
    # Cleanup
    print("\n11. Cleaning up test files...")
    try:
        os.remove("test_programming.pdf")
        os.remove("test_datastructures.pdf")
        print("✅ Test files cleaned up")
    except:
        print("⚠️ Could not clean up test files")
    
    print("\n🎉 Improved indexing system test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_improved_indexing() 