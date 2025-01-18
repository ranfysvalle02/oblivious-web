from flask import Flask, request, jsonify, render_template  
from bs4 import BeautifulSoup  
import requests  
from duckduckgo_search import DDGS  
from urllib.parse import urlparse  
import threading  
  
app = Flask(__name__)  
  
# Cache to store search results temporarily  
search_cache = {}  
  
@app.route("/")  
def home():  
    return render_template("index.html")  
  
@app.route("/search")  
def search_route():  
    query = request.args.get("query", "").strip()  
    page = int(request.args.get("page", 1))  
    results_per_page = 10  
    if query:  
        try:  
            # Generate a cache key based on the query  
            cache_key = query.lower()  
            if cache_key not in search_cache:  
                # Perform the DuckDuckGo search  
                ddgs = DDGS()  
                max_results = 30  # Limit total results to 30  
                search_results = ddgs.text(  
                    query,  
                    region='wt-wt',  
                    safesearch='Moderate',  
                    timelimit='y',  
                    max_results=max_results,  
                )  
                results_list = list(search_results)  
                # Store in cache  
                search_cache[cache_key] = results_list  
                # Clear cache after some time  
                threading.Timer(300, lambda: search_cache.pop(cache_key, None)).start()  # Clear after 5 minutes  
            else:  
                results_list = search_cache[cache_key]  
  
            total_results = len(results_list)  
            total_pages = (total_results + results_per_page - 1) // results_per_page  
            total_pages = min(total_pages, 3)  # Limit to first 3 pages  
            page = min(page, total_pages)  # Ensure current page is within bounds  
            offset = (page - 1) * results_per_page  
            results = []  
            paginated_results = results_list[offset:offset + results_per_page]  
            for result in paginated_results:  
                title = result.get('title')  
                link = result.get('href')  
                description = result.get('body', '')  
                parsed_uri = urlparse(link)  
                display_link = parsed_uri.netloc  
                favicon = f'https://www.google.com/s2/favicons?domain={parsed_uri.netloc}&sz=64'  
                results.append({  
                    'title': title,  
                    'link': link,  
                    'description': description,  
                    'favicon': favicon,  
                    'display_link': display_link  
                })  
            if results:  
                return jsonify({"results": results, "page": page, "total_pages": total_pages})  
            else:  
                return jsonify({"results": [], "page": page, "total_pages": total_pages})  
        except Exception as e:  
            return jsonify({"error": str(e)})  
    else:  
        return jsonify({"error": "Query parameter is missing or empty."})  
  
@app.route("/create_ctx", methods=["POST"])  
def create_ctx():  
    data = request.get_json()  
    urls = data.get("urls", [])  
    context = []  
  
    for url in urls:  
        try:  
            response = requests.get(url, timeout=5)  
            soup = BeautifulSoup(response.content, "html.parser")  
            # Remove script and style elements  
            for script in soup(["script", "style"]):  
                script.extract()  
            text = soup.get_text(separator=" ", strip=True)  
            context.append({"url": url, "text": text})  
        except Exception as e:  
            context.append({"url": url, "error": str(e)})  
  
    return jsonify({"context": context})  
  
@app.route("/api/ai", methods=["POST"])  
def api_ai():  
    data = request.get_json()  
    context = data.get("context", [])  
    user_input = data.get("user_input", "")  
    # For now, just echo back the context and user_input  
    return jsonify({"context": context, "user_input": user_input})  
  
if __name__ == "__main__":  
    app.run(debug=True)  