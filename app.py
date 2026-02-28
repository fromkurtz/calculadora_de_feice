from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Como o Vercel apaga arquivos salvos, vamos usar uma lista na memória.
# Nota: O ranking vai resetar sempre que o site ficar sem acessos.
ranking_temporario = []

def calculate_score(data):
    score = 0
    try:
        weight = float(data.get('weight', 0))
        height = float(data.get('height', 0))
        imc = weight / (height ** 2) if height > 0 else 0
        score += min((imc / 40) * 40000, 40000)
    except: pass

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
    global ranking_temporario
    data = request.json
    score = calculate_score(data)
    
    new_entry = {
        'name': data.get('name', 'Anônimo'),
        'score': score,
        'date': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    
    ranking_temporario.append(new_entry)
    ranking_temporario.sort(key=lambda x: x['score'], reverse=True)
    ranking_temporario = ranking_temporario[:10] # Mantém apenas o top 10
    
    return jsonify({'score': score, 'rank': 1})

@app.route('/api/ranking', methods=['GET'])
def get_ranking():
    return jsonify(ranking_temporario)

# Garante que o objeto app seja exportado para o Vercel
app = app