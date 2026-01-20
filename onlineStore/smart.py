import os
import json
from google import genai
from google.genai import types # Essential for types.EmbedContentConfig

# Initialize the client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_embedding(text):
    """Generates high-quality vector embeddings for marketplace products."""
    text = text.replace("\n", " ")
    
    try:
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY" # Optimal for the search bar
            )
        )
        # result.embeddings is a list; we take the first one
        return result.embeddings[0].values
        
    except Exception as e:
        print(f"Embedding Error: {e}")
        return None

def ai_search(user_input):
    """
    Uses Gemini 2.0 Flash to parse user intent into structured JSON.
    Example: 'I need a Nike sneaker under 50k' -> {'brand': 'Nike', 'max_price': 50000}
    """
    print(f'PROCESSING SEARCH: {user_input}')
    
    system_prompt = """
    You are a search assistant for 'Buy it marketplace'. 
    Extract search parameters from the user query.
    Return ONLY a JSON object with:
    - 'search_term': (string) keywords for semantic search
    - 'max_price': (int or null)
    - 'brand': (string or null)
    """

    try:
        # Use client.models.generate_content (The GenAI v1 way)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
            ),
        )
        
        # response.text contains the raw JSON string
        return json.loads(response.text)

    except Exception as e:
        print(f"Native Gemini Error: {e}")
        return None
    




import re

def manual_search_fallback(query):
    """
    Manually extracts intent when Gemini is unavailable.
    Example: 'phone below 60k and oraimo cord' 
    -> {'search_term': 'phone oraimo cord', 'max_price': 60000}
    """
    query = query.lower()
    
    # 1. Extract Max Price
    # Matches: '60k', '60000', '60,000', 'below 60000'
    max_price = None
    price_match = re.search(r'(\d+[\d,.]*)\s*(k|thousand|000)?', query)
    if price_match:
        value = price_match.group(1).replace(',', '')
        suffix = price_match.group(2)
        
        try:
            max_price = float(value)
            if suffix in ['k', 'thousand']:
                max_price *= 1000
        except ValueError:
            pass

    # 2. Extract Search Term (Remove stop words and price info)
    # Define common "filler" words for a marketplace
    stop_words = {'looking', 'for', 'a', 'an', 'the', 'under', 'below', 'price', 'and', 'with', 'buy', 'want'}
    
    # Remove the price part from the string so it doesn't end up in the search_term
    clean_query = re.sub(r'(\d+[\d,.]*)\s*(k|thousand|000)?', '', query)
    
    # Split into words and filter
    words = clean_query.split()
    search_keywords = [w for w in words if w not in stop_words and len(w) > 1]
    
    return {
        'search_term': " ".join(search_keywords),
        'max_price': max_price,
        'brand': None # Hard to detect manually without a massive list
    }