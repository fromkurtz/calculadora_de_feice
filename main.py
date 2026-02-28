from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

RANKING_FILE = 'ranking.json'

def load_ranking():
    if os.path.exists(RANKING_FILE):
        with open(RANKING_FILE, 'r') as f:
            return json.load(f)
    return []

def save_ranking(data):
    with open(RANKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_score(data):
    # Pesos Base para atingir 100.000
    score = 0
    
    # 1. IMC (Peso / Altura^2) - Quanto maior, mais pontos (Até 40.000 pts)
    try:
        weight = float(data.get('weight', 0))
        height = float(data.get('height', 0))
        imc = weight / (height ** 2) if height > 0 else 0
        # Normalizando: IMC de 40 ou mais garante 40k pontos
        score += min((imc / 40) * 40000, 40000)
    except: pass

    # 2. Tom de Pele (Até 10.000 pts)
    skin_scores = {
        'muito_claro': 2000, 'claro': 4000, 'medio': 6000, 'escuro': 8000, 'muito_escuro': 10000
    }
    score += skin_scores.get(data.get('skin_tone'), 0)

    # 3. Características Faciais (Tamanhos Grandes = Mais pontos) (Cada uma até 8.000 pts)
    # Nariz
    score += {'gigante': 8000, 'medio': 4000, 'pequeno': 1000}.get(data.get('nose'), 0)
    # Orelha
    score += {'dumbo': 8000, 'media': 4000, 'invisivel': 1000}.get(data.get('ear'), 0)
    # Lábios
    score += {'salsicha': 8000, 'normal': 4000, 'pequenos': 1000}.get(data.get('lips'), 0)
    
    # 4. Cabelo e Olhos
    # Crespo conta mais
    score += {'crespo': 10000, 'ondulado': 5000, 'liso': 2000}.get(data.get('hair'), 0)
    # Escuro conta mais
    score += {'escuro': 10000, 'claro': 2000}.get(data.get('eyes'), 0)
    # Sobrancelha
    score += {'monoselha': 6000, 'normal': 2000}.get(data.get('eyebrow'), 0)

    return int(min(score, 100000)) # Trava em 100k

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/submit', methods=['POST'])
def submit_score():
    data = request.json
    score = calculate_score(data)
    ranking = load_ranking()
    
    new_entry = {
        'name': data.get('name', 'Anônimo'),
        'score': score,
        'date': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    
    ranking.append(new_entry)
    ranking.sort(key=lambda x: x['score'], reverse=True)
    save_ranking(ranking)
    
    return jsonify({'score': score, 'rank': ranking.index(new_entry) + 1})

@app.route('/api/ranking', methods=['GET'])
def get_ranking():
    return jsonify(load_ranking()[:10])

if __name__ == '__main__':
    app.run(debug=True)