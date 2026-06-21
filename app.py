import os
import json
import re
import httpx
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL     = "https://api.anthropic.com/v1/messages"


# ── Servir o frontend ──────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ── Endpoint principal ─────────────────────────────────────────────────────────
@app.route("/api/search", methods=["POST"])
def search():
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY não configurada no servidor."}), 500

    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()

    if not query:
        return jsonify({"error": "Parâmetro 'query' obrigatório."}), 400

    if len(query) > 200:
        return jsonify({"error": "Consulta muito longa (máx 200 caracteres)."}), 400

    system_prompt = (
        "Voce responde SOMENTE com JSON puro e valido. "
        "Sem markdown, sem blocos de codigo, sem texto fora do JSON. "
        "Use apenas aspas duplas. Nunca inclua aspas duplas dentro dos valores de string. "
        "Nao use caracteres de controle ou quebras de linha dentro de strings."
    )

    user_prompt = (
        f'Produto: "{query}". Retorne JSON com esta estrutura exata:\n'
        '{"produto":"nome","prices":['
        '{"rank":1,"store":"Mercado Livre","price":"R$ 0.000,00","detail":"info","url":"https://lista.mercadolivre.com.br/PRODUTO"},'
        '{"rank":2,"store":"Amazon","price":"R$ 0.000,00","detail":"info","url":"https://www.amazon.com.br/s?k=PRODUTO"},'
        '{"rank":3,"store":"Americanas","price":"R$ 0.000,00","detail":"info","url":"https://www.americanas.com.br/busca/PRODUTO"}'
        '],"reviews":['
        '{"name":"Nome1","source":"Mercado Livre","source_url":"https://lista.mercadolivre.com.br/PRODUTO","rating":5,"text":"comentario"},'
        '{"name":"Nome2","source":"Amazon","source_url":"https://www.amazon.com.br/s?k=PRODUTO","rating":4,"text":"comentario"},'
        '{"name":"Nome3","source":"Reclame Aqui","source_url":"https://www.reclameaqui.com.br/busca/?q=PRODUTO","rating":3,"text":"comentario"},'
        '{"name":"Nome4","source":"Shopee","source_url":"https://shopee.com.br/search?keyword=PRODUTO","rating":5,"text":"comentario"},'
        '{"name":"Nome5","source":"Americanas","source_url":"https://www.americanas.com.br/busca/PRODUTO","rating":2,"text":"comentario negativo"},'
        '{"name":"Nome6","source":"Magazine Luiza","source_url":"https://www.magazineluiza.com.br/busca/PRODUTO","rating":4,"text":"comentario"},'
        '{"name":"Nome7","source":"KaBuM","source_url":"https://www.kabum.com.br/busca/PRODUTO","rating":5,"text":"comentario"},'
        '{"name":"Nome8","source":"Zoom","source_url":"https://www.zoom.com.br/busca?q=PRODUTO","rating":1,"text":"comentario muito negativo"},'
        '{"name":"Nome9","source":"Casas Bahia","source_url":"https://www.casasbahia.com.br/busca/PRODUTO","rating":4,"text":"comentario"},'
        '{"name":"Nome10","source":"Techtudo","source_url":"https://www.techtudo.com.br/busca/?q=PRODUTO","rating":5,"text":"comentario"}'
        '],"insight":"frase de dica de compra"}\n'
        "REGRAS OBRIGATORIAS:\n"
        "- Substitua PRODUTO nas URLs pelo nome real do produto em formato URL (sem acento, espacos como +)\n"
        "- Lojas reais do Brasil, precos realistas 2025\n"
        "- Nomes brasileiros variados\n"
        "- Textos de avaliacao curtos sem aspas internas (max 90 chars)\n"
        "- Misture positivas negativas e neutras\n"
        "- Todas as URLs devem comecar com https://\n"
        "- Retorne exatamente 3 precos e 10 reviews"
    )

    headers = {
        "x-api-key":         ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }

    payload = {
        "model":      "claude-sonnet-4-6",
        "max_tokens": 3000,
        "system":     system_prompt,
        "messages":   [{"role": "user", "content": user_prompt}],
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(ANTHROPIC_URL, headers=headers, json=payload)

        if resp.status_code != 200:
            err = resp.json().get("error", {})
            return jsonify({"error": err.get("message", f"Erro HTTP {resp.status_code}")}), 502

        data = resp.json()

        # Extrai texto
        raw = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                raw += block["text"]

        # Limpa markdown residual
        raw = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"```\s*",     "", raw)
        raw = raw.strip()

        # Localiza JSON
        start = raw.find("{")
        end   = raw.rfind("}")
        if start == -1 or end == -1:
            return jsonify({"error": "A IA não retornou JSON válido. Tente novamente."}), 502

        json_str = raw[start:end + 1]

        # Remove quebras de linha dentro de strings
        def clean_string(m):
            return re.sub(r"[\r\n\t]+", " ", m.group(0))

        json_str = re.sub(r'"(?:[^"\\]|\\.)*"', clean_string, json_str)

        parsed = json.loads(json_str)
        return jsonify(parsed)

    except json.JSONDecodeError as e:
        return jsonify({"error": f"Erro ao interpretar resposta da IA: {e}"}), 502
    except httpx.TimeoutException:
        return jsonify({"error": "Tempo de resposta esgotado. Tente novamente."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
