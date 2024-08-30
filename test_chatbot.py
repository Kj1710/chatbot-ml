import requests

url = "http://127.0.0.1:5001/"
payload = {
    "message": "Tell me about health charities"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

# Print the raw response text
print("Response Text:", response.text)

# Try to parse the JSON
try:
    print("JSON Response:", response.json())
except requests.exceptions.JSONDecodeError as e:
    print("Failed to parse JSON:", e)