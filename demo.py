from flask import Flask, request, jsonify, render_template_string
from bs4 import BeautifulSoup
import requests
from duckduckgo_search import DDGS

app = Flask(__name__)

@app.route("/")
def home():
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Search Experience</title>
        <!-- Tailwind CSS CDN -->
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            /* Background Gradient */
            body {
                background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
                font-family: 'Inter', sans-serif;
                overflow: hidden;
                transition: background 0.5s;
            }

            /* Search Input Styling */
            #search-input {
                animation: pop-in 1s cubic-bezier(0.5, 1.4, 0.5, 1.4);
                border: none;
                outline: none;
                background: linear-gradient(90deg, #fff, #f7f7f7);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                transition: all 0.3s ease-in-out;
            }

            #search-input:focus {
                transform: scale(1.05);
                box-shadow: 0 8px 20px rgba(255, 255, 255, 0.4), 0 4px 15px rgba(0, 0, 0, 0.2);
            }

            /* Search Button Styling */
            #search-button {
                background: linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%);
                color: white;
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: 9999px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                transition: all 0.3s ease-in-out;
            }

            #search-button:hover {
                transform: scale(1.05);
                box-shadow: 0 8px 20px rgba(255, 126, 95, 0.4), 0 4px 15px rgba(0, 0, 0, 0.2);
            }

            /* Modal Entrance Animation */
            @keyframes slide-in-up {
                from {
                    opacity: 0;
                    transform: translateY(100%);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            /* Search Results List */
            .result-item {
                transition: transform 0.2s ease-in-out, box-shadow 0.2s ease;
                cursor: pointer;
                background: linear-gradient(to right, #f7f7f7, #e4e4e4);
                animation: fade-in 0.5s cubic-bezier(0.5, 1.4, 0.5, 1.4) forwards;
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .result-item:hover {
                transform: scale(1.05);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
                background: linear-gradient(to right, #e8f0ff, #d3e7ff);
            }

            .result-icon {
                width: 2rem;
                height: 2rem;
                margin-right: 1rem;
            }

            /* Modal Styling */
            .modal {
                animation: slide-in-up 0.6s ease-in-out forwards;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
                border-radius: 20px;
            }

            /* Button */
            #close-modal:hover {
                transform: rotate(90deg);
                transition: transform 0.3s ease-in-out;
            }

            /* Animations */
            @keyframes fade-in {
                from {
                    opacity: 0;
                }
                to {
                    opacity: 1;
                }
            }

            @keyframes pop-in {
                0% {
                    transform: scale(0.8);
                    opacity: 0;
                }
                100% {
                    transform: scale(1);
                    opacity: 1;
                }
            }

            /* Canvas for Stars */
            canvas {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: -1;
            }

            /* Hyperspace Effect */
            @keyframes hyperspace {
                0% {
                    opacity: 1;
                    transform: scale(1);
                }
                50% {
                    opacity: 0;
                    transform: scale(0.5) rotateY(180deg);
                }
                100% {
                    opacity: 1;
                    transform: scale(1) rotateY(360deg);
                }
            }

            .hyperspace {
                animation: hyperspace 1s ease-in-out forwards;
            }

            /* Loading Spinner */
            .spinner {
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-top: 4px solid #fff;
                border-radius: 50%;
                width: 2rem;
                height: 2rem;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(360deg);
                }
            }
        </style>
    </head>
    <body class="flex items-center justify-center min-h-screen">
        <!-- Canvas for Stars -->
        <canvas id="stars"></canvas>

        <!-- Search Container -->
        <div class="text-center w-full max-w-xl">
            <h1 class="text-5xl font-extrabold text-white mb-8 tracking-wide animate-bounce">
                Search the Universe <img src="https://bulloch.solutions/wp-content/uploads/2024/08/home-hero.png" style="width:5rem; float: right; margin-top: -1em;" />
            </h1>
            <div class="flex items-center">
                <input
                    type="text"
                    id="search-input"
                    class="w-full px-6 py-4 text-lg rounded-full focus:outline-none shadow-lg placeholder-gray-500"
                    placeholder="Search for knowledge..."
                />
                <button
                    id="search-button"
                    class="ml-4 px-6 py-4 text-lg rounded-full bg-white text-gray-700 shadow-lg hover:bg-gray-100"
                >
                    Search
                </button>
                <div id="loading-spinner" class="spinner hidden ml-4"></div>
            </div>
        </div>

        <!-- Results Modal -->
        <div
            id="results-modal"
            class="modal hidden fixed inset-0 bg-white p-10 flex flex-col items-center space-y-6 z-50"
        >
            <button
                id="close-modal"
                class="text-gray-500 text-3xl hover:text-gray-800 transform transition-transform"
            >
                ✖
            </button>
            <h2 class="text-4xl font-bold text-gray-800">Search Results</h2>
            <ul id="results-list" class="space-y-4 w-full max-w-md"></ul>
            <button
                id="create-context-button"
                class="px-6 py-4 text-lg rounded-full bg-blue-500 text-white shadow-lg hover:bg-blue-600"
            >
                Create Context
            </button>
        </div>

        <!-- JavaScript -->
        <script>
            const input = document.getElementById('search-input');
            const modal = document.getElementById('results-modal');
            const resultsList = document.getElementById('results-list');
            const closeModal = document.getElementById('close-modal');
            const searchButton = document.getElementById('search-button');
            const loadingSpinner = document.getElementById('loading-spinner');
            const createContextButton = document.getElementById('create-context-button');

            // Handle search with hyperspace effect
            const performSearch = () => {
                if (input.value.trim()) {
                    document.body.classList.add('hyperspace');
                    input.disabled = true;
                    searchButton.classList.add('hidden');
                    loadingSpinner.classList.remove('hidden');
                    setTimeout(() => {
                        fetch(`/search?query=${encodeURIComponent(input.value)}`)
                            .then((res) => res.json())
                            .then((data) => {
                                if (data.results) {
                                    resultsList.innerHTML = data.results
                                        .map((item, index) => `
                                            <li class="result-item">
                                                <input type="checkbox" id="result-${index}" value="${item.link}" class="mr-2">
                                                <img src="${item.thumbnail}" class="result-icon" alt="icon">
                                                <a href="${item.link}" target="_blank" style="width:100%;">${item.title}</a>
                                            </li>
                                        `)
                                        .join('');
                                } else {
                                    resultsList.innerHTML = '<li class="result-item">No results found.</li>';
                                }
                                modal.classList.remove('hidden');
                                document.body.classList.remove('hyperspace');
                                input.disabled = false;
                                searchButton.classList.remove('hidden');
                                loadingSpinner.classList.add('hidden');
                            });
                    }, 1000); // Match the duration of the hyperspace animation
                }
            };

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });

            searchButton.addEventListener('click', performSearch);

            // Close modal
            closeModal.addEventListener('click', () => {
                modal.classList.add('hidden');
            });

            // Create context
            createContextButton.addEventListener('click', () => {
                const selectedUrls = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
                    .map(checkbox => checkbox.value);

                fetch('/create_ctx', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ urls: selectedUrls }),
                })
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    alert('Context created successfully!');
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });

            // Animate stars
            const canvas = document.getElementById('stars');
            const ctx = canvas.getContext('2d');
            let stars = [];

            const createStars = () => {
                for (let i = 0; i < 100; i++) {
                    stars.push({
                        x: Math.random() * canvas.width,
                        y: Math.random() * canvas.height,
                        radius: Math.random() * 1.5,
                        alpha: Math.random()
                    });
                }
            };

            const drawStars = () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                stars.forEach(star => {
                    ctx.beginPath();
                    ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(255, 255, 255, ${star.alpha})`;
                    ctx.fill();
                });
            };

            const animateStars = () => {
                stars.forEach(star => {
                    star.y += 0.5;
                    if (star.y > canvas.height) {
                        star.y = 0;
                        star.x = Math.random() * canvas.width;
                    }
                });
                drawStars();
                requestAnimationFrame(animateStars);
            };

            const resizeCanvas = () => {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
                drawStars();
            };

            window.addEventListener('resize', resizeCanvas);
            resizeCanvas();
            createStars();
            animateStars();

            // Animate background gradient
            document.addEventListener('mousemove', (e) => {
                const x = e.clientX / window.innerWidth;
                const y = e.clientY / window.innerHeight;
                document.body.style.background = `linear-gradient(135deg, rgba(${106 + x * 50}, 17, 203, 1) 0%, rgba(${37 + y * 50}, 117, 252, 1) 100%)`;
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route("/search")
def search_route():
    query = request.args.get("query", "").strip()
    if query:
        try:
            # Perform the DuckDuckGo search
            search_results = DDGS().text(f"{query}", max_results=5, safesearch='Moderate')
            results = []
            for result in search_results:
                title = result.get('title')
                link = result.get('href')
                # DuckDuckGo doesn't provide direct thumbnail links in its search results
                # You might need to implement additional logic to fetch thumbnails if required
                thumbnail = "https://cdn-icons-png.flaticon.com/512/4548/4548489.png"
                results.append({'title': title, 'link': link, 'thumbnail': thumbnail})

            if results:
                return jsonify({"results": results})
            else:
                return jsonify({"results": ["No results found."]})
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
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            context.append({"url": url, "text": text})
        except Exception as e:
            context.append({"url": url, "error": str(e)})

    return jsonify({"context": context})

if __name__ == "__main__":
    app.run(debug=True)
