import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import bigquery

app = Flask(__name__)
CORS(app)

def is_sql(query: str) -> bool:
    """Detecta si el texto parece ser SQL."""
    return bool(re.match(r"(?i)^\s*(SELECT|INSERT|UPDATE|DELETE|WITH)", query.strip()))

def translate_to_sql(natural_text: str) -> str:
    """
    Traduce lenguaje natural a SQL.
    Por ahora, reglas simples para frases comunes.
    """
    text = natural_text.lower()

    if "5 registros más comunes" in text or "más comunes" in text:
        return """SELECT species, COUNT(*) as total 
                  FROM `bigquery-public-data.san_francisco_trees.street_trees` 
                  GROUP BY species 
                  ORDER BY total DESC 
                  LIMIT 5;"""

    if "especies únicas" in text or "total de especies" in text:
        return """SELECT COUNT(DISTINCT species) as total_especies
                  FROM `bigquery-public-data.san_francisco_trees.street_trees`;"""

    if "registro más común" in text or "especie más frecuente" in text:
        return """SELECT species, COUNT(*) as total 
                  FROM `bigquery-public-data.san_francisco_trees.street_trees` 
                  GROUP BY species 
                  ORDER BY total DESC 
                  LIMIT 1;"""

    # Si no reconoce la frase, devuelve un mensaje
    return "SELECT 'Consulta en lenguaje natural no reconocida' AS mensaje"

@app.route("/", methods=["POST"])
def query_agent():
    try:
        user_prompt = request.json.get("prompt", "")

        # Decide si es SQL o lenguaje natural
        if is_sql(user_prompt):
            sql = user_prompt
        else:
            sql = translate_to_sql(user_prompt)

        client = bigquery.Client()
        query_job = client.query(sql)
        results = query_job.result()

        output = [dict(row.items()) for row in results]
        return jsonify({"answer": output})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ⚠️ Este bloque solo se usa en local
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
