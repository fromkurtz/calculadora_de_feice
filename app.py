from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from vercel_kv import KV

app = Flask(__name__)
CORS(app)

# Função auxiliar para pegar a instância do KV apenas quando necessário
def get_kv():
    try:
        return KV()
    except Exception as e:
        print(f"Erro de conexão KV: {e}")
        return None

def load_ranking():
    kv = get_kv()
    if not kv: return []
    
    ranking = kv.get('ranking')
    return ranking if ranking else []

def save_ranking(data):
    kv = get_kv()
    if kv:
        kv.set('ranking', data)

def calculate_score(data):
    score = 0
    try:
        weight = float(data.get('weight', 0))
        height = float(data.get('height', 0))
        # Cálculo do IMC: peso / altura²
        imc = weight / (height ** 2) if height > 0 else 0
        # Pontuação baseada em IMC (máximo 40k)
        score += min((imc / 40) * 40000, 40000)
    except: 
        pass

    skin_scores = {'muito_claro': 2000, 'claro': 4000, 'medio': 6000, 'escuro': 8000, 'muito_escuro': 10000}
    score += skin_scores.get(data.get('skin_tone'), 0)
    
    score += {'gigante': 8000, 'medio': 4000, 'pequeno': 1000}.get(data.get('nose'), 0)
    score += {'dumbo': 8000, 'media': 4000, 'invisivel': 1000}.get(data.get('ear'), 0)
    score += {'salsicha': 8000, 'normal': 4000, 'pequenos': 1000}.get(data.get('lips'), 0)
    score += {'crespo': 10000, 'ondulado': 5000, 'liso': 2000}.get(data.get('hair'), 0)
    score += {'escuro': 10000, 'claro': 2000}.get(data.get('eyes'), 0)
    score += {'monoselha': 6000, 'normal': 2000}.get(data.get('eyebrow'), 0)

    return int(min(score, 100000))

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
    save_ranking(ranking[:50]) 
    
    # Encontrar a posição real após o sort
    rank_pos = 1
    for i, entry in enumerate(ranking):
        if entry['name'] == new_entry['name'] and entry['score'] == new_entry['score']:
            rank_pos = i + 1
            break

    return jsonify({'score': score, 'rank': rank_pos})

@app.route('/api/ranking', methods=['GET'])
def get_ranking():
    return jsonify(load_ranking()[:10])

# IMPORTANTE: Para o Vercel, o objeto 'app' deve estar disponível globalmente
# Não remova a linha abaixo.