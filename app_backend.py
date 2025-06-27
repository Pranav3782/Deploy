# app_backend.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import json

# Import your LangChain logic
from chains import get_restaurant_analysis_chain, get_chatbot_response, extract_ratings_from_text, _format_analysis_data_for_chatbot

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app) # Enable CORS for all origins, or specify origins if needed (e.g., CORS(app, origins=["http://127.0.0.1:5500"]))

# --- API Endpoints ---

@app.route('/analyze', methods=['POST'])
def analyze_restaurant():
    """
    API endpoint for initial restaurant analysis.
    Expects JSON: {"restaurant_name": "...", "analysis_type": "..."}
    Returns JSON: The AI-generated analysis of the restaurant.
    """
    try:
        data = request.json
        restaurant_name = data.get('restaurant_name')
        analysis_type = data.get('analysis_type')

        if not restaurant_name or not analysis_type:
            return jsonify({"error": "Missing 'restaurant_name' or 'analysis_type'"}), 400

        # Get the analysis chain
        analysis_chain = get_restaurant_analysis_chain()

        # Invoke the chain
        chain_input = {
            "input": restaurant_name,
            "analysis_type": analysis_type
        }
        
        # The chain should return a dictionary with a 'text' key containing the JSON string
        response = analysis_chain.invoke(chain_input)
        response_content = response['text'] # Extract the raw JSON string

        # Attempt to parse the JSON content
        try:
            parsed_analysis = json.loads(response_content)
        except json.JSONDecodeError as e:
            # If AI doesn't return perfect JSON, try to handle or log it
            print(f"Warning: AI did not return valid JSON. Error: {e}. Raw content: {response_content}")
            # Fallback for display if JSON is malformed
            parsed_analysis = {"summary": f"Analysis available, but JSON parsing failed: {e}. Raw content: {response_content}", "raw_output": response_content}

        return jsonify(parsed_analysis), 200

    except Exception as e:
        print(f"Error in /analyze: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chatbot', methods=['POST'])
def chatbot_query():
    """
    API endpoint for chatbot follow-up questions.
    Expects JSON: {"analysis_text_raw": "...", "user_question": "..."}
    Returns JSON: {"response": "..."}
    """
    try:
        data = request.json
        analysis_text_raw = data.get('analysis_text_raw')
        user_question = data.get('user_question')

        if not analysis_text_raw or not user_question:
            return jsonify({"error": "Missing 'analysis_text_raw' or 'user_question'"}), 400

        # Call the chatbot response function from chains.py
        bot_response = get_chatbot_response(analysis_text_raw, user_question)

        return jsonify({"response": bot_response}), 200

    except Exception as e:
        print(f"Error in /chatbot: {e}")
        return jsonify({"error": str(e)}), 500

#if __name__ == '__main__':
    # Ensure your GROQ_API_KEY is set in your .env file
    # For development, you can run this Flask app: python app_backend.py
    # For production, use a production WSGI server like Gunicorn
   # app.run(debug=True, port=5000) # Run on port 5000
