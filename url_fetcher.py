import requests
from bs4 import BeautifulSoup

def fetch_text_from_url(url: str) -> str:
    """Fetches web page content and extracts main text paragraph contents."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script, style, and navigation elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
            
        # Extract paragraph text
        paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 20]
        
        full_text = "\n\n".join(paragraphs)
        if not full_text:
            return "Could not extract sufficient text content from this URL."
            
        return full_text
    except Exception as e:
        return f"Error fetching URL: {str(e)}"