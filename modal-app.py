import threading
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from urllib.parse import urlparse

import modal

# Install all necessary packages in your Modal image
image = modal.Image.debian_slim().pip_install(
    [
        "fastapi[standard]",
        "requests",
        "beautifulsoup4",
        "duckduckgo_search",
    ]
)

app = modal.App(name="oblivious-web", image=image)

@app.function(gpu="any", secrets=[modal.Secret.from_dotenv()])
@modal.web_endpoint(method="GET", docs=True)
def search(query: str = "", page: int = 1):
    """
    Mimics the original Flask `/search` route.
    Query params: ?query=some+search&page=1
    Returns JSON with search results from DuckDuckGo.
    """
    query = query.strip()
    results_per_page = 10
    
    if not query:
        return {"error": "Query parameter is missing or empty."}

    try:        
        # Perform the DuckDuckGo search
        ddgs = DDGS()
        max_results = 30  # Limit total results to 30
        search_results = ddgs.text(
            query,
            region="wt-wt",
            safesearch="Moderate",
            timelimit="y",
            max_results=max_results,
        )
        results_list = list(search_results)

        total_results = len(results_list)
        total_pages = (total_results + results_per_page - 1) // results_per_page
        
        # Limit to first 3 pages
        total_pages = min(total_pages, 3)
        page = min(page, total_pages) if total_pages else 1
        
        offset = (page - 1) * results_per_page
        paginated_results = results_list[offset : offset + results_per_page]

        results = []
        for result in paginated_results:
            title = result.get("title")
            link = result.get("href")
            description = result.get("body", "")
            parsed_uri = urlparse(link)
            display_link = parsed_uri.netloc
            favicon = f"https://www.google.com/s2/favicons?domain={parsed_uri.netloc}&sz=64"
            results.append({
                "title": title,
                "link": link,
                "description": description,
                "favicon": favicon,
                "display_link": display_link,
            })
        
        return {
            "results": results,
            "page": page,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"error": str(e)}


@app.function(gpu="any", secrets=[modal.Secret.from_dotenv()])
@modal.web_endpoint(method="POST", docs=True)
def create_ctx(data: dict):
    """
    Mimics the original Flask `/create_ctx` POST route.
    Expects `{"urls": [...]}`.
    Returns JSON with text content for each URL.
    """
    import os
    JINA_API_KEY = os.getenv("JINA_API_KEY")
    urls = data.get("urls", [])
    context_data = []

    for url in urls:
        try:
            # Use Jina shortlink
            headers = {
                "Authorization": f"Bearer {JINA_API_KEY}",
                "X-Timeout": "180"
            }
            response = requests.get(f"https://r.jina.ai/{url}", headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            text = soup.get_text(separator=" ", strip=True)
            
            context_data.append({"url": url, "text": text})
        except Exception as e:
            context_data.append({"url": url, "error": str(e)})
    
    return {"context": context_data}


@app.function(gpu="any", secrets=[modal.Secret.from_dotenv()])
@modal.web_endpoint(method="POST", docs=True)
def api_ai(data: dict):
    """
    Mimics the original Flask `/api/ai` POST route.
    Expects JSON with `{"context": [...], "user_input": "some question"}`.
    Returns the same content for demonstration purposes.
    """
    context = data.get("context", [])
    user_input = data.get("user_input", "")
    # For now, just echo back the context and user_input
    return {"context": context, "user_input": user_input}
