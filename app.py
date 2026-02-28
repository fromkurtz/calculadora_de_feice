from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Conexão com o banco Neon/Postgres
def get_db_connection():
    url = os.environ.get('POSTGRES_URL')
    if not url:
        # Tenta uma alternativa caso a primeira falhe
        url = os.environ.get('DATABASE_URL')
    
    # Adiciona sslmode se não estiver na URL para evitar erro de conexão segura
    if url and 'sslmode' not in url:
        separator = '&' if '?' in url else '?'
        url += f'{separator}sslmode=require'
        
    return psycopg2.connect(url)

# Criar a tabela de ranking se não existir
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ranking (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            score INTEGER NOT NULL,
            date TEXT NOT NULL
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

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
    data = request.json
    score = calculate_score(data)
    name = data.get('name', 'Anônimo')
    date = datetime.now().strftime('%d/%m/%Y %H:%M')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO ranking (name, score, date) VALUES (%s, %s, %s)', (name, score, date))
    conn.commit()
    
    # Busca o rank
    cur.execute('SELECT COUNT(*) FROM ranking WHERE score > %s', (score,))
    rank = cur.fetchone()[0] + 1
    
    cur.close()
    conn.close()
    return jsonify({'score': score, 'rank': rank})

@app.route('/api/ranking', methods=['GET'])
def get_ranking():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # REMOVIDO O "LIMIT 10" PARA PEGAR TODOS OS REGISTROS
    cur.execute('SELECT name, score, date FROM ranking ORDER BY score DESC')
    ranking = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(ranking)

app = app