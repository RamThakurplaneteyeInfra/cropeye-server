import requests
import logging

logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"


def generate_chatbot_response(message: str) -> str:
    """
    Generate chatbot response using Ollama API.
    
    Args:
        message: User's input message
        
    Returns:
        str: AI-generated response
        
    Raises:
        Exception: If API call fails
    """
    if not message or not isinstance(message, str):
        raise ValueError("Message must be a non-empty string")
    
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": message,
            "stream": False
        }
        
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        reply = data.get("response", "")
        
        if not reply:
            logger.warning("Empty response from Ollama API")
            return "I apologize, but I couldn't generate a response. Please try again."
        
        return reply.strip()
        
    except requests.exceptions.Timeout:
        logger.error("Ollama API request timed out")
        raise Exception("Request timed out. Please try again later.")
    
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Ollama API. Is Ollama running?")
        raise Exception("Chatbot service is currently unavailable. Please ensure Ollama is running on localhost:11434.")
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"Ollama API HTTP error: {e}")
        raise Exception(f"Chatbot service error: {str(e)}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API request error: {e}")
        raise Exception("An error occurred while processing your request. Please try again.")
    
    except KeyError as e:
        logger.error(f"Unexpected response format from Ollama API: {e}")
        raise Exception("Received an unexpected response from the chatbot service.")
    
    except Exception as e:
        logger.error(f"Unexpected error in generate_chatbot_response: {e}")
        raise Exception("An unexpected error occurred. Please try again later.")

