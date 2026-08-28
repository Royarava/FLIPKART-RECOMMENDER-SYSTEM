import os
import csv
import re
from pathlib import Path
from flask import render_template,Flask,request,Response
from prometheus_client import Counter,generate_latest
from flipkart.data_ingestion import DataIngestor
from flipkart.rag_chain import RAGChainBuilder
from flipkart.config import Config

REQUEST_COUNT = Counter("http_requests_total" , "Total HTTP Request")

# Global cache for lazy initialization
_vector_store = None
_rag_chain = None


class DemoChain:
    """Offline response provider used when external services are unavailable."""

    def __init__(self):
        data_path = Path(__file__).parent / "data" / "flipkart_product_review.csv"
        with data_path.open(newline="", encoding="utf-8") as data_file:
            self.products = list(csv.DictReader(data_file))

    def invoke(self, inputs, config=None):
        question = inputs.get("input", "").strip()
        query_words = set(re.findall(r"[a-z0-9]+", question.lower()))
        ranked_products = []
        seen_titles = set()

        for product in self.products:
            title = product.get("product_title", "")
            if title in seen_titles:
                continue
            searchable_text = " ".join(
                product.get(field, "")
                for field in ("product_title", "summary", "review")
            ).lower()
            score = sum(word in searchable_text for word in query_words)
            if score:
                ranked_products.append((score, float(product.get("rating", 0)), product))
                seen_titles.add(title)

        ranked_products.sort(key=lambda item: (item[0], item[1]), reverse=True)
        if ranked_products:
            recommendations = "\n".join(
                f"{index}. {item[2]['product_title']} (rating: {item[2]['rating']}/5)"
                for index, item in enumerate(ranked_products[:3], start=1)
            )
            answer = (
                f"Based on your request, these local products look relevant:\n{recommendations}\n\n"
                "These results come from the Flipkart review dataset. Enable live mode for "
                "full RAG answers."
            )
        else:
            answer = (
                "I could not find a close match in the local Flipkart review dataset. "
                "Try terms such as headset, headphones, gaming, battery, or bass."
            )

        return {
            "answer": answer
        }


def _get_rag_chain():
    global _vector_store, _rag_chain
    if _rag_chain is None:
        if Config.DEMO_MODE:
            _rag_chain = DemoChain()
        else:
            _vector_store = DataIngestor().ingest(load_existing=True)
            _rag_chain = RAGChainBuilder(_vector_store).build_chain()
    return _rag_chain

def create_app():

    app = Flask(__name__)

    @app.route("/")
    def index():
        REQUEST_COUNT.inc()
        return render_template("index.html")
    
    @app.route("/get" , methods=["POST"])
    def get_response():

        user_input = request.form["msg"]
        
        try:
            rag_chain = _get_rag_chain()
            reponse = rag_chain.invoke(
                {"input" : user_input},
                config={"configurable" : {"session_id" : "user-session"}}
            )["answer"]
        except Exception as e:
            error_msg = str(e)
            if "getaddrinfo failed" in error_msg or "NameResolutionError" in error_msg or "Failed to resolve" in error_msg:
                reponse = "❌ Connection Error: Cannot reach Hugging Face API. Please check your internet connection and ensure you have VPN/proxy configured if required by your network."
            elif "ConnectionError" in error_msg:
                reponse = "❌ Network Error: Unable to connect to required services (Hugging Face, Astra DB). Please verify your network connectivity."
            else:
                reponse = f"❌ Error: {error_msg[:200]}"

        return reponse
    
    @app.route("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype="text/plain")
    
    return app

if __name__=="__main__":
    app = create_app()
    app.run(host="0.0.0.0",port=5000,debug=True)