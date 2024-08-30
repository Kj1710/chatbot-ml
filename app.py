from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import re
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load the sample dataset
try:
    df = pd.read_csv('C:/Users/shrey/OneDrive/Desktop/nfc cb/chatbot-ml/charity_navigator.csv')
    logging.info("Dataset loaded successfully.")
except Exception as e:
    logging.error(f"Error loading dataset: {e}")

# Function to extract cities from text
def extract_cities(text):
    cities = re.findall(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b', text)
    return list(set(cities))  # Remove duplicates

# Extract cities from mission and tagline
df['cities'] = df['mission'].fillna('') + ' ' + df['tagline'].fillna('')
df['cities'] = df['cities'].apply(extract_cities)

# Get a list of all unique cities
all_cities = list(set([city for cities in df['cities'] for city in cities]))

# HTML template with dark mode and donate button
HTML_TEMPLATE = """
<!-- Add an image next to the title -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nayi Disha Chatbot</title>
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        #chatbox {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #00ff88;
            padding: 10px;
            margin-bottom: 20px;
            background-color: #1e1e1e;
            position: relative;
            text-align: center; /* Center align content */
        }
         #chatImage {
            max-width: 300px; /* Reduced width */
            max-height: 300px; /* Reduced height */
            width: auto; /* Maintain aspect ratio */
            height: auto; /* Maintain aspect ratio */
            display: block;
            margin: 0 auto; /* Center the image */
        }
        #userInput {
            width: 87.6%;
            padding: 10px;
            color: #ffffff;
            background-color: #333333;
            border: 1px solid #00ff88;
        }
        #sendButton {
            padding: 10px 20px;
            color: #ffffff;
            background-color: #00ff88;
            border: none;
            cursor: pointer;
        }
        h1 {
            text-align: center;
            color: #00ff88;
            position: relative;
        }
        #smallChatImage {
            position: absolute;
            top: 10px;
            right: 10px;
            max-width: 50px; /* Smaller size */
            height: auto; /* Maintain aspect ratio */
            display: none; /* Initially hidden */
        }
        a {
            color: #00ff88;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>
        Nayi Disha Chatbot
    <img src="{{ url_for('static', filename='bitcoin.png') }}" alt="Chatbot Image" id="smallChatImage">
</h1>
<div id="chatbox">
    <img src="{{ url_for('static', filename='robot-assistant.png') }}" alt="Chatbot Image" id="chatImage">
</div>
    <input type="text" id="userInput" placeholder="Ask about charities (e.g., 'charities, locations, types etc..')">
    <button id="sendButton">Send</button>

    <script>
        let currentCategory = '';
        let currentCause = '';
        let currentLocation = '';
        let currentOffset = 0;

        document.getElementById('sendButton').onclick = sendMessage;
        document.getElementById('userInput').onkeypress = function(e) {
            if (e.key === 'Enter') sendMessage();
        };

        function sendMessage() {
            let userInput = document.getElementById('userInput').value;
            if (userInput.trim() === '') return;

            // Hide the large image and show the small image when a message is sent
            document.getElementById('chatImage').style.display = 'none';
            document.getElementById('smallChatImage').style.display = 'block';

            fetch('/charity_info', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: userInput, 
                    category: currentCategory, 
                    cause: currentCause,
                    location: currentLocation,
                    offset: currentOffset
                }),
            })
            .then(response => response.json())
            .then(data => {
                let chatbox = document.getElementById('chatbox');
                chatbox.innerHTML += `<p><strong>You:</strong> ${userInput}</p>`;
                chatbox.innerHTML += `<p><strong>Bot:</strong> ${data.response.replace(/\\n/g, '<br>')}</p>`;
                chatbox.scrollTop = chatbox.scrollHeight;
                document.getElementById('userInput').value = '';
                currentCategory = data.category;
                currentCause = data.cause;
                currentLocation = data.location;
                currentOffset = data.offset;
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('chatbox').innerHTML += '<p><strong>Bot:</strong> Sorry, there was an error processing your request.</p>';
            });
        }
    </script>
</body>
</html>


"""

@app.route('/charity_info', methods=['POST'])
def charity_info():
    user_input = request.json.get('message', '').lower()
    current_category = request.json.get('category', '')
    current_cause = request.json.get('cause', '')
    current_location = request.json.get('location', '')
    offset = request.json.get('offset', 0)
    response = ""

    try:
        categories = df['category'].unique()
        causes = df['cause'].unique()

        # Check for charity ID search
        if user_input.startswith("id:"):
            try:
                charity_id = int(user_input.split("id:")[1].strip())
                charity = df[df['charityid'] == charity_id]
                if not charity.empty:
                    row = charity.iloc[0]
                    response += f"Charity: {row['charityid']} (Category: {row['category']}, Cause: {row['cause']})\n"
                    response += f"Tagline: {row['tagline']}\n"
                    response += f"Mission: {row['mission']}\n"
                    response += f"Cities: {', '.join(row['cities'])}\n"
                    response += f"<a href='https://example.com/donate/{row['charityid']}' target='_blank'>Donate</a>\n\n"
                else:
                    response = f"No charity found with ID: {charity_id}"
            except ValueError:
                response = "Invalid charity ID format. Please enter a numeric ID."
        else:
            words = user_input.split()
            category = next((cat for cat in categories if cat.lower() in user_input), None)
            cause = next((c for c in causes if c.lower() in user_input), None)
            location = next((city for city in all_cities if city.lower() in user_input), None)

            if 'more' in user_input.lower():
                category = current_category
                cause = current_cause
                location = current_location

            charities = df

            if category:
                charities = charities[charities['category'].str.lower() == category.lower()]
            if cause:
                charities = charities[charities['cause'].str.lower() == cause.lower()]
            if location:
                charities = charities[charities['cities'].apply(lambda cities: any(city.lower() == location.lower() for city in cities))]

            if not charities.empty:
                response += f"Here are some charities"
                if category:
                    response += f" in the category '{category}'"
                if cause:
                    response += f" related to the cause '{cause}'"
                if location:
                    response += f" in {location}"
                response += ":\n\n"

                for _, row in charities.iloc[offset:offset+7].iterrows():
                    response += f"Charity: {row['charityid']} (Category: {row['category']}, Cause: {row['cause']})\n"
                    response += f"Tagline: {row['tagline']}\n"
                    response += f"Mission: {row['mission']}\n"
                    response += f"<a href='https://example.com/donate/{row['charityid']}' target='_blank'>Donate</a>\n\n"

                offset += 7
                if len(charities) > offset:
                    response += "Type 'More' to see more results."
            else:
                response += "No charities found for your query. Try a different category, cause, or location."

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        response = "Sorry, there was an error processing your request."

    return jsonify({
        "response": response.strip(), 
        "category": current_category, 
        "cause": current_cause, 
        "location": current_location, 
        "offset": offset
    })

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
