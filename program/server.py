import random
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import json
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Cambia questo con una chiave segreta reale

# Configurazione del database
DATABASE_URL = "mysql://root:@localhost/timetable_example"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db_session = Session()

# Carica i dati dall'orario JSON


def load_timetable(name, type='class'):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, f"{name}_timetable.json")
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


@app.route('/api/timetable')
def api_timetable():
    name = request.args.get('name', '5A2 INF')
    type = request.args.get('type', 'class')
    timetable = load_timetable(name, type)
    return jsonify(timetable)


@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('dashboard.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            return "Login Failed"
    return render_template('login.html')


@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))


@app.route('/api/aule_nomi')
def api_aule_nomi():
    result = db_session.execute(text("SELECT nome FROM aule"))
    aule_nomi = [row[0] for row in result]
    return jsonify(aule_nomi)


@app.route('/api/getnomiclassi')
def api_getnomiclassi():
    result = db_session.execute(text("SELECT nome FROM classi"))
    classi_nomi = [row[0] for row in result]
    return jsonify(classi_nomi)


@app.route('/api/docenti', methods=['GET', 'POST'])
def api_docenti():
    if request.method == 'GET':
        result = db_session.execute(
            text("SELECT id, nome, cognome, oresettimanali FROM docenti"))
        docenti = [{"id": row[0], "nome": row[1], "cognome": row[2],
                    "oresettimanali": row[3]} for row in result]
        return jsonify(docenti)
    elif request.method == 'POST':
        data = request.json
        query = text(
            "INSERT INTO docenti (nome, cognome, oresettimanali) VALUES (:nome, :cognome, :oresettimanali)")
        db_session.execute(query, {
                           "nome": data['nome'], "cognome": data['cognome'], "oresettimanali": data['oresettimanali']})
        db_session.commit()
        return jsonify({"message": "Docente aggiunto con successo"}), 201


@app.route('/api/docenti/<int:id>', methods=['PUT'])
def update_docente(id):
    data = request.json
    query = text(
        "UPDATE docenti SET nome = :nome, cognome = :cognome, oresettimanali = :oresettimanali WHERE id = :id")
    db_session.execute(query, {
                       "id": id, "nome": data['nome'], "cognome": data['cognome'], "oresettimanali": data['oresettimanali']})
    db_session.commit()
    return jsonify({"message": "Docente aggiornato con successo"}), 200


@app.route('/api/docenti/<int:id>', methods=['DELETE'])
def delete_docente(id):
    query = text("DELETE FROM docenti WHERE id = :id")
    db_session.execute(query, {"id": id})
    db_session.commit()
    return jsonify({"message": "Docente eliminato con successo"}), 200


@app.route('/api/materie', methods=['GET', 'POST'])
def api_materie():
    if request.method == 'GET':
        result = db_session.execute(
            text("SELECT id, nome_materia, num_docenti FROM materie"))
        materie = [{"id": row[0], "nome_materia": row[1],
                    "num_docenti": row[2]} for row in result]
        return jsonify(materie)
    elif request.method == 'POST':
        data = request.json
        query = text(
            "INSERT INTO materie (nome_materia, num_docenti) VALUES (:nome_materia, :num_docenti)")
        db_session.execute(
            query, {"nome_materia": data['nome_materia'], "num_docenti": data['num_docenti']})
        db_session.commit()
        return jsonify({"message": "Materia aggiunta con successo"}), 201


@app.route('/api/materie/<int:id>', methods=['PUT'])
def update_materia(id):
    data = request.json
    query = text(
        "UPDATE materie SET nome_materia = :nome_materia, num_docenti = :num_docenti WHERE id = :id")
    db_session.execute(query, {
                       "id": id, "nome_materia": data['nome_materia'], "num_docenti": data['num_docenti']})
    db_session.commit()
    return jsonify({"message": "Materia aggiornata con successo"}), 200


@app.route('/api/materie/<int:id>', methods=['DELETE'])
def delete_materia(id):
    query = text("DELETE FROM materie WHERE id = :id")
    db_session.execute(query, {"id": id})
    db_session.commit()
    return jsonify({"message": "Materia eliminata con successo"}), 200


@app.route('/api/aule', methods=['GET', 'POST'])
def api_aule():
    if request.method == 'GET':
        result = db_session.execute(text(
            "SELECT a.id, a.nome, a.piano, m.nome_materia AS materia_nome, a.n_palazzina FROM aule a LEFT JOIN materie m ON a.id_materia = m.id"))
        aule = [{"id": row[0], "nome": row[1], "piano": row[2],
                 "materia_nome": row[3], "palazzina": row[4]} for row in result]
        return jsonify(aule)
    elif request.method == 'POST':
        data = request.json
        query = text(
            "INSERT INTO aule (nome, piano, id_materia, n_palazzina) VALUES (:nome, :piano, :id_materia, :n_palazzina)")
        db_session.execute(query, {"nome": data['nome'], "piano": data['piano'],
                           "id_materia": data['id_materia'], "n_palazzina": data['n_palazzina']})
        db_session.commit()
        return jsonify({"message": "Aula aggiunta con successo"}), 201


@app.route('/api/aule/<int:id>', methods=['PUT'])
def update_aula(id):
    data = request.json
    query = text(
        "UPDATE aule SET nome = :nome, piano = :piano, id_materia = :id_materia, n_palazzina = :n_palazzina WHERE id = :id")
    db_session.execute(query, {"id": id, "nome": data['nome'], "piano": data['piano'],
                       "id_materia": data['id_materia'], "n_palazzina": data['n_palazzina']})
    db_session.commit()
    return jsonify({"message": "Aula aggiornata con successo"}), 200


@app.route('/api/aule/<int:id>', methods=['DELETE'])
def delete_aula(id):
    query = text("DELETE FROM aule WHERE id = :id")
    db_session.execute(query, {"id": id})
    db_session.commit()
    return jsonify({"message": "Aula eliminata con successo"}), 200


@app.route('/docenti')
def docenti():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('docenti.html')


@app.route('/api/classi', methods=['GET', 'POST'])
def api_classi():
    if request.method == 'GET':
        query = text("""
            SELECT c.id, c.nome, c.id_indirizzo, i.nome
            FROM classi c
            JOIN indirizzi i ON c.id_indirizzo = i.id_indirizzo
        """)
        result = db_session.execute(query)
        classi = [{"id": row[0], "nome": row[1], "indirizzo": row[3]}
                  for row in result]
        return jsonify(classi)
    elif request.method == 'POST':
        data = request.json
        query = text(
            "INSERT INTO classi (nome, id_indirizzo) VALUES (:nome, :id_indirizzo)")
        db_session.execute(
            query, {"nome": data['nome'], "id_indirizzo": data['id_indirizzo']})
        db_session.commit()
        return jsonify({"message": "Classe aggiunta con successo"}), 201


@app.route('/api/classi/<int:id>', methods=['PUT'])
def update_classe(id):
    data = request.json
    query = text(
        "UPDATE classi SET nome = :nome, id_indirizzo = :id_indirizzo WHERE id = :id")
    db_session.execute(
        query, {"id": id, "nome": data['nome'], "id_indirizzo": data['id_indirizzo']})
    db_session.commit()
    return jsonify({"message": "Classe aggiornata con successo"}), 200


@app.route('/api/classi/<int:id>', methods=['DELETE'])
def delete_classe(id):
    query = text("DELETE FROM classi WHERE id = :id")
    db_session.execute(query, {"id": id})
    db_session.commit()
    return jsonify({"message": "Classe eliminata con successo"}), 200


@ app.route('/gestione_assenze')
def gestione_assenze():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('gestione_assenze.html')


def find_substitutes(day, docente_id):
    # Placeholder: replace this with actual logic to find available substitutes
    result = db_session.execute(text(
        "SELECT id, nome, cognome FROM docenti WHERE id != :docente_id"), {"docente_id": docente_id})
    all_docenti = [{"id": row[0], "nome": row[1], "cognome": row[2]}
                   for row in result]

    substitutes = []
    for hour in range(1, 7):  # Assuming a 6-hour school day
        if all_docenti:
            substitute = random.choice(all_docenti)
            substitutes.append(
                {"ora": hour, "sostituto": f"{substitute['nome']} {substitute['cognome']}"})

    return substitutes


@app.route('/api/find_substitute')
def api_find_substitute():
    day = request.args.get('day')
    docente_id = request.args.get('docente_id')
    substitutes = find_substitutes(day, docente_id)
    return jsonify(substitutes)


@app.route('/classi')
def classi():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('classi.html')


@app.route('/indirizzi')
def indirizzi():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('indirizzi.html')


@ app.route('/materie')
def materie():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('materie.html')


@app.route('/impostazioni')
def impostazioni():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('impostazioni.html')


@ app.route('/aule')
def aule():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('aule.html')


if __name__ == '__main__':
    app.run(debug=True)
