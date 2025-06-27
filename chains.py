# chains.py
import os
from dotenv import load_dotenv
import json # Import json module
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq

from prompts import (
    ANALYSIS_PROMPT, DIABETIC_ANALYSIS_PROMPT, RATING_EXTRACTION_PROMPT, CHATBOT_PROMPT
)

# Load environment variables from .env file
load_dotenv()

# --- Debugging: Print the loaded API keys to check if they're being read ---
print(f"DEBUG: GROQ_API_KEY loaded: {os.getenv('GROQ_API_KEY') is not None}") # Corrected
print(f"DEBUG: GROQ_API_KEY value (first 5 chars): {os.getenv('GROQ_API_KEY')[:5] if os.getenv('GROQ_API_KEY') else 'None'}") # Corrected


# --- LLM Setup ---
llm = ChatGroq(
    temperature=0.7,
    model_name="llama-3.3-70b-versatile", # Changed model name to a commonly available one
    groq_api_key=os.getenv("GROQ_API_KEY") # Corrected: Accessing by environment variable name
)

# --- LangChain Orchestration ---

def get_restaurant_analysis_chain():
    """
    Creates and returns a simple LLMChain for restaurant analysis,
    configured to output JSON.
    """
    prompt = PromptTemplate.from_template(ANALYSIS_PROMPT)
    json_llm = ChatGroq(
        temperature=0.7,
        model_name="llama3-8b-8192",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        streaming=False,
        model_kwargs={"response_format": {"type": "json_object"}}
    )

    chain = LLMChain(llm=json_llm, prompt=prompt)
    return chain

def extract_ratings_from_text(text: str):
    """
    This function now expects to parse a JSON string and return a dictionary.
    It's primarily used for initial parsing from the analysis chain.
    """
    try:
        parsed_data = json.loads(text)
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {"summary": f"Could not parse analysis as JSON. Error: {e}\nRaw LLM output:\n{text}", "raw_output": text}
    except Exception as e:
        print(f"An unexpected error occurred in extract_ratings_from_text: {e}")
        return {"summary": f"An unexpected error occurred. Error: {e}\nRaw LLM output:\n{text}", "raw_output": text}


def _format_analysis_data_for_chatbot(data: dict) -> str:
    """
    Formats the parsed analysis dictionary into a more readable string for the chatbot's context.
    """
    formatted_string = f"Restaurant Name: {data.get('restaurant_name', 'N/A')}\n"
    formatted_string += f"Summary: {data.get('summary', 'N/A')}\n"
    formatted_string += f"Healthiness Rating: {data.get('healthiness_rating', 'N/A')}\n"
    formatted_string += f"Hygiene Rating: {data.get('hygiene_rating', 'N/A')}\n"
    formatted_string += f"Price Rating: {data.get('price_rating', 'N/A')}\n"
    formatted_string += f"Food Quality: {data.get('food_quality', 'N/A')}\n"

    dietary_options = data.get('dietary_options', {})
    formatted_string += f"Dietary Options - Vegetarian: {dietary_options.get('vegetarian', 'N/A')}\n"
    formatted_string += f"Dietary Options - Vegan: {dietary_options.get('vegan', 'N/A')}\n"
    formatted_string += f"Dietary Options - Gluten-Free: {dietary_options.get('gluten_free', 'N/A')}\n"
    formatted_string += f"Dietary Options - Other: {dietary_options.get('other_diets', 'N/A')}\n"

    formatted_string += f"Ambiance: {data.get('ambiance', 'N/A')}\n"
    formatted_string += f"Popular Dishes: {', '.join(data.get('popular_dishes', ['N/A']))}\n"
    formatted_string += f"Service Experience: {data.get('service_experience', 'N/A')}\n"
    formatted_string += f"Service Time: {data.get('service_time', 'N/A')}\n"
    formatted_string += f"Portion Quantity: {data.get('portion_quantity', 'N/A')}\n"
    formatted_string += f"Rush Hours: {data.get('rush_hours', 'N/A')}\n"

    branches = data.get('branches', {})
    formatted_string += f"Branches Count: {branches.get('count', 'N/A')}\n"
    formatted_string += f"First Branch Location: {branches.get('first_branch_location', 'N/A')}\n"

    formatted_string += f"Parking Availability: {data.get('parking_availability', 'N/A')}\n"

    return formatted_string


def get_chatbot_response(analysis_text_raw: str, user_question: str) -> str:
    """
    Generates a response to a user's question based on the provided JSON analysis text.
    The chatbot now relies on the parsed analysis data for better accuracy.
    """
    try:
        # Parse the raw JSON string into a dictionary
        parsed_analysis_data = json.loads(analysis_text_raw)
        # Format the dictionary into a human-readable string for the prompt
        formatted_analysis_content = _format_analysis_data_for_chatbot(parsed_analysis_data)
    except json.JSONDecodeError as e:
        return f"Error: Could not parse analysis for chatbot. Invalid JSON: {e}"
    except Exception as e:
        return f"Error: Failed to process analysis data for chatbot: {e}"

    prompt = PromptTemplate(
        template=CHATBOT_PROMPT,
        input_variables=["analysis_content", "question"]
    )
    chain = prompt | llm
    try:
        response = chain.invoke({"analysis_content": formatted_analysis_content, "question": user_question})
        return response.content
    except Exception as e:
        return f"Error generating chatbot response: {e}"
