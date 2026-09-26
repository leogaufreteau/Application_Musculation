import os
from datetime import date

import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, jsonify, g

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Configuration correcte du dossier static
app = Flask(__name__, static_folder='static', static_url_path='/static')

ORDRE_GROUPES = [
    "Poitrine", "Dos", "Épaules", "Biceps", "Triceps", "Avant-bras",
    "Abdominaux", "Lombaires", "Quadriceps", "Ischio-jambiers", "Mollets", "Fessiers",
]

EXERCICES_INITIAUX = [
    ("Développé couché barre", "Poitrine"),
    ("Développé couché haltères", "Poitrine"),
    ("Développé incliné barre", "Poitrine"),
    ("Développé incliné haltères", "Poitrine"),
    ("Développé décliné barre", "Poitrine"),
    ("Écarté couché haltères", "Poitrine"),
    ("Écarté poulie vis-à-vis", "Poitrine"),
    ("Dips (pectoraux)", "Poitrine"),
    ("Pull-over haltère", "Poitrine"),
    ("Chest press machine", "Poitrine"),
    ("Butterfly (pec-deck)", "Poitrine"),
    ("Traction pronation", "Dos"),
    ("Traction supination", "Dos"),
    ("Tirage vertical poulie", "Dos"),
    ("Rowing barre", "Dos"),
    ("Rowing haltère", "Dos"),
    ("Tirage horizontal poulie", "Dos"),
    ("Rowing T-bar", "Dos"),
    ("Soulevé de terre", "Dos"),
    ("Tirage nuque", "Dos"),
    ("Superman", "Dos"),
    ("Développé militaire barre", "Épaules"),
    ("Développé militaire haltères", "Épaules"),
    ("Élévations latérales", "Épaules"),
    ("Élévations frontales", "Épaules"),
    ("Oiseau (élévations arrière)", "Épaules"),
    ("Shrugs (haussements d'épaules)", "Épaules"),
    ("Développé Arnold", "Épaules"),
    ("Face pull", "Épaules"),
    ("Tirage menton", "Épaules"),
    ("Curl barre", "Biceps"),
    ("Curl haltères", "Biceps"),
    ("Curl marteau", "Biceps"),
    ("Curl pupitre (Scott)", "Biceps"),
    ("Curl concentré", "Biceps"),
    ("Curl poulie basse", "Biceps"),
    ("Curl prise marteau câble", "Biceps"),
    ("Extension poulie haute (pushdown)", "Triceps"),
    ("Barre au front (skull crusher)", "Triceps"),
    ("Dips (triceps)", "Triceps"),
    ("Extension nuque haltère", "Triceps"),
    ("Kickback", "Triceps"),
    ("Développé couché prise serrée", "Triceps"),
    ("Extension poulie corde", "Triceps"),
    ("Curl poignet", "Avant-bras"),
    ("Curl poignet inversé", "Avant-bras"),
    ("Extension poignet", "Avant-bras"),
    ("Farmer's walk", "Avant-bras"),
    ("Enroulement de barre (wrist roller)", "Avant-bras"),
    ("Crunch", "Abdominaux"),
    ("Relevé de jambes", "Abdominaux"),
    ("Gainage (planche)", "Abdominaux"),
    ("Crunch poulie haute", "Abdominaux"),
    ("Russian twist", "Abdominaux"),
    ("Ab wheel (roulette abdo)", "Abdominaux"),
    ("Mountain climbers", "Abdominaux"),
    ("Gainage latéral", "Abdominaux"),
    ("Extension lombaire (banc à lombaires)", "Lombaires"),
    ("Good morning", "Lombaires"),
    ("Soulevé de terre jambes tendues", "Lombaires"),
    ("Hyperextension", "Lombaires"),
    ("Squat barre", "Quadriceps"),
    ("Presse à cuisses", "Quadriceps"),
    ("Fentes", "Quadriceps"),
    ("Leg extension", "Quadriceps"),
    ("Squat gobelet (goblet squat)", "Quadriceps"),
    ("Squat bulgare", "Quadriceps"),
    ("Hack squat", "Quadriceps"),
    ("Fentes marchées", "Quadriceps"),
    ("Soulevé de terre roumain", "Ischio-jambiers"),
    ("Leg curl allongé", "Ischio-jambiers"),
    ("Leg curl assis", "Ischio-jambiers"),
    ("Pont fessier ischio", "Ischio-jambiers"),
    ("Mollets debout (calf raise)", "Mollets"),
    ("Mollets assis", "Mollets"),
    ("Mollets à la presse à cuisses", "Mollets"),
    ("Hip thrust", "Fessiers"),
    ("Pont fessier", "Fessiers"),
    ("Squat sumo", "Fessiers"),
    ("Kickback fessier poulie", "Fessiers"),
    ("Abduction hanche machine", "Fessiers"),
    ("Fentes bulgares (fessiers)", "Fessiers"),
]

def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, sslmode="require")
    return g.db

def q(query, params=(), fetch=None, commit=False):
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query, params)
    result = None
    if fetch == "one":
        result = cur.fetchone()
    elif fetch == "all":
        result = cur.fetchall()
    if commit:
        db.commit()
    return result, cur

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    if not DATABASE_URL:
        print("ERREUR: DATABASE_URL n'est pas défini", flush=True)
        return
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS exercices (id SERIAL PRIMARY KEY, nom TEXT NOT NULL, groupe_musculaire TEXT NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS seances (id SERIAL PRIMARY KEY, date TEXT NOT NULL, notes TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS performances (id SERIAL PRIMARY KEY, seance_id INTEGER NOT NULL REFERENCES seances(id) ON DELETE CASCADE, exercice_id INTEGER NOT NULL REFERENCES exercices(id), poids REAL, reps INTEGER, series INTEGER, ressenti INTEGER, commentaire TEXT, est_rp INTEGER DEFAULT 0, poids_rp REAL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS seances_types (id SERIAL PRIMARY KEY, nom TEXT NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS seances_types_exercices (id SERIAL PRIMARY KEY, seance_type_id INTEGER NOT NULL REFERENCES seances_types(id) ON DELETE CASCADE, exercice_id INTEGER NOT NULL REFERENCES exercices(id), ordre INTEGER DEFAULT 0)""")
        cur.execute("SELECT COUNT(*) FROM exercices")
        count = cur.fetchone()[0]
        if count == 0:
            cur.executemany("INSERT INTO exercices (nom, groupe_musculaire) VALUES (%s, %s)", EXERCICES_INITIAUX)
        conn.commit()
        cur.close()
        conn.close()
        print("✓ BD initialisée", flush=True)
    except Exception as e:
        print(f"✗ ERREUR BD: {e}", flush=True)

def get_exercices_groupes(db_rows):
    groupes = {}
    for r in db_rows:
        groupes.setdefault(r["groupe_musculaire"], []).append(r)
    return {g_: groupes[g_] for g_ in ORDRE_GROUPES if g_ in groupes}

@app.route("/")
def index():
    try:
        seances_types, _ = q("SELECT * FROM seances_types ORDER BY nom", fetch="all")
        dernieres_seances, _ = q("SELECT * FROM seances ORDER BY date DESC, id DESC LIMIT 5", fetch="all")
        total_row, _ = q("SELECT COUNT(*) as c FROM seances", fetch="one")
        return render_template("index.html", seances_types=seances_types, dernieres_seances=dernieres_seances, total_seances=total_row["c"])
    except Exception as e:
        print(f"ERREUR: {e}", flush=True)
        return f"Erreur: {str(e)}", 500

@app.route("/nouvelle-seance", methods=["GET", "POST"])
def nouvelle_seance():
    if request.method == "POST":
        date_seance = request.form.get("date") or date.today().isoformat()
        notes = request.form.get("notes", "")
        row, _ = q("INSERT INTO seances (date, notes) VALUES (%s, %s) RETURNING id", (date_seance, notes), fetch="one", commit=True)
        seance_id = row["id"]
        exercice_ids = request.form.getlist("exercice_id[]")
        poids_list = request.form.getlist("poids[]")
        reps_list = request.form.getlist("reps[]")
        series_list = request.form.getlist("series[]")
        ressenti_list = request.form.getlist("ressenti[]")
        commentaire_list = request.form.getlist("commentaire[]")
        est_rp_list = request.form.getlist("est_rp[]")
        poids_rp_list = request.form.getlist("poids_rp[]")
        for i, ex_id in enumerate(exercice_ids):
            if not ex_id: continue
            est_rp = 1 if i < len(est_rp_list) and est_rp_list[i] == "1" else 0
            poids_rp = poids_rp_list[i] if i < len(poids_rp_list) and poids_rp_list[i] else None
            q("INSERT INTO performances (seance_id, exercice_id, poids, reps, series, ressenti, commentaire, est_rp, poids_rp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (seance_id, ex_id, poids_list[i] or None, reps_list[i] or None, series_list[i] or None, ressenti_list[i] or None, commentaire_list[i] or "", est_rp, poids_rp), commit=True)
        return redirect(url_for("historique"))
    rows, _ = q("SELECT id, nom, groupe_musculaire FROM exercices ORDER BY groupe_musculaire, nom", fetch="all")
    groupes = get_exercices_groupes(rows)
    seances_types, _ = q("SELECT * FROM seances_types ORDER BY nom", fetch="all")
    exercices_preremplis = []
    type_id = request.args.get("type_id")
    nom_type_charge = None
    if type_id:
        st, _ = q("SELECT * FROM seances_types WHERE id = %s", (type_id,), fetch="one")
        if st:
            nom_type_charge = st["nom"]
            exercices_preremplis, _ = q("SELECT e.id, e.nom FROM seances_types_exercices ste JOIN exercices e ON e.id = ste.exercice_id WHERE ste.seance_type_id = %s ORDER BY ste.ordre", (type_id,), fetch="all")
    return render_template("nouvelle_seance.html", groupes=groupes, seances_types=seances_types, exercices_preremplis=exercices_preremplis, nom_type_charge=nom_type_charge, today=date.today().isoformat())

@app.route("/historique")
def historique():
    tri = request.args.get("tri", "date")
    exercice_id = request.args.get("exercice_id", "")
    groupe = request.args.get("groupe", "")
    query = "SELECT s.id as seance_id, s.date, s.notes, p.id as perf_id, p.poids, p.reps, p.series, p.ressenti, p.commentaire, p.est_rp, p.poids_rp, e.id as exercice_id, e.nom as exercice_nom, e.groupe_musculaire FROM seances s JOIN performances p ON p.seance_id = s.id JOIN exercices e ON e.id = p.exercice_id WHERE 1=1"
    params = []
    if exercice_id:
        query += " AND e.id = %s"
        params.append(exercice_id)
    if groupe:
        query += " AND e.groupe_musculaire = %s"
        params.append(groupe)
    if tri == "exercice":
        query += " ORDER BY e.nom, s.date DESC"
    elif tri == "groupe":
        query += " ORDER BY e.groupe_musculaire, s.date DESC"
    else:
        query += " ORDER BY s.date DESC, s.id DESC"
    rows, _ = q(query, params, fetch="all")
    seances = {}
    ordre_seances = []
    for r in rows:
        sid = r["seance_id"]
        if sid not in seances:
            seances[sid] = {"id": sid, "date": r["date"], "notes": r["notes"], "performances": []}
            ordre_seances.append(sid)
        seances[sid]["performances"].append(r)
    seances_list = [seances[sid] for sid in ordre_seances]
    exercices, _ = q("SELECT id, nom FROM exercices ORDER BY nom", fetch="all")
    return render_template("historique.html", seances=seances_list, exercices=exercices, groupes=ORDRE_GROUPES, tri=tri, exercice_id=exercice_id, groupe=groupe)

@app.route("/seance/<int:seance_id>/modifier", methods=["GET", "POST"])
def modifier_seance(seance_id):
    seance, _ = q("SELECT * FROM seances WHERE id = %s", (seance_id,), fetch="one")
    if seance is None: return redirect(url_for("historique"))
    if request.method == "POST":
        date_seance = request.form.get("date")
        notes = request.form.get("notes", "")
        q("UPDATE seances SET date = %s, notes = %s WHERE id = %s", (date_seance, notes, seance_id), commit=True)
        q("DELETE FROM performances WHERE seance_id = %s", (seance_id,), commit=True)
        exercice_ids = request.form.getlist("exercice_id[]")
        poids_list = request.form.getlist("poids[]")
        reps_list = request.form.getlist("reps[]")
        series_list = request.form.getlist("series[]")
        ressenti_list = request.form.getlist("ressenti[]")
        commentaire_list = request.form.getlist("commentaire[]")
        est_rp_list = request.form.getlist("est_rp[]")
        poids_rp_list = request.form.getlist("poids_rp[]")
        for i, ex_id in enumerate(exercice_ids):
            if not ex_id: continue
            est_rp = 1 if i < len(est_rp_list) and est_rp_list[i] == "1" else 0
            poids_rp = poids_rp_list[i] if i < len(poids_rp_list) and poids_rp_list[i] else None
            q("INSERT INTO performances (seance_id, exercice_id, poids, reps, series, ressenti, commentaire, est_rp, poids_rp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (seance_id, ex_id, poids_list[i] or None, reps_list[i] or None, series_list[i] or None, ressenti_list[i] or None, commentaire_list[i] or "", est_rp, poids_rp), commit=True)
        return redirect(url_for("historique"))
    performances, _ = q("SELECT p.*, e.nom as exercice_nom FROM performances p JOIN exercices e ON e.id = p.exercice_id WHERE p.seance_id = %s", (seance_id,), fetch="all")
    rows, _ = q("SELECT id, nom, groupe_musculaire FROM exercices ORDER BY groupe_musculaire, nom", fetch="all")
    groupes = get_exercices_groupes(rows)
    return render_template("modifier_seance.html", seance=seance, performances=performances, groupes=groupes)

@app.route("/seance/<int:seance_id>/supprimer", methods=["POST"])
def supprimer_seance(seance_id):
    q("DELETE FROM performances WHERE seance_id = %s", (seance_id,), commit=True)
    q("DELETE FROM seances WHERE id = %s", (seance_id,), commit=True)
    return redirect(url_for("historique"))

@app.route("/graphiques")
def graphiques():
    exercices, _ = q("SELECT id, nom, groupe_musculaire FROM exercices ORDER BY groupe_musculaire, nom", fetch="all")
    exercice_id = request.args.get("exercice_id", "")
    return render_template("graphiques.html", exercices=exercices, exercice_id=exercice_id)

@app.route("/api/progression/<int:exercice_id>")
def api_progression(exercice_id):
    rows, _ = q("SELECT s.date, p.poids, p.reps, p.series, p.est_rp, p.poids_rp FROM performances p JOIN seances s ON s.id = p.seance_id WHERE p.exercice_id = %s ORDER BY s.date ASC", (exercice_id,), fetch="all")
    volumes_par_date = {}
    rp_max = None
    rp_date = None
    for r in rows:
        poids = float(r["poids"] or 0)
        reps = r["reps"] or 0
        series = r["series"] or 0
        volume = poids * reps * series
        volumes_par_date[r["date"]] = volumes_par_date.get(r["date"], 0) + volume
        if r["est_rp"] and r["poids_rp"]:
            if rp_max is None or float(r["poids_rp"]) > rp_max:
                rp_max = float(r["poids_rp"])
                rp_date = r["date"]
    dates = sorted(volumes_par_date.keys())
    volumes = [volumes_par_date[d] for d in dates]
    return jsonify({"dates": dates, "volumes": volumes, "rp": {"poids": rp_max, "date": rp_date} if rp_max else None})

@app.route("/seances-types")
def seances_types_liste():
    types, _ = q("SELECT * FROM seances_types ORDER BY nom", fetch="all")
    types_avec_exercices = []
    for t in types:
        exos, _ = q("SELECT e.nom FROM seances_types_exercices ste JOIN exercices e ON e.id = ste.exercice_id WHERE ste.seance_type_id = %s ORDER BY ste.ordre", (t["id"],), fetch="all")
        types_avec_exercices.append({"id": t["id"], "nom": t["nom"], "exercices": [e["nom"] for e in exos]})
    return render_template("seances_types.html", types=types_avec_exercices)

@app.route("/seances-types/nouveau", methods=["GET", "POST"])
def nouvelle_seance_type():
    if request.method == "POST":
        nom = request.form.get("nom")
        row, _ = q("INSERT INTO seances_types (nom) VALUES (%s) RETURNING id", (nom,), fetch="one", commit=True)
        type_id = row["id"]
        exercice_ids = request.form.getlist("exercice_id[]")
        for ordre, ex_id in enumerate(exercice_ids):
            if ex_id:
                q("INSERT INTO seances_types_exercices (seance_type_id, exercice_id, ordre) VALUES (%s, %s, %s)", (type_id, ex_id, ordre), commit=True)
        return redirect(url_for("seances_types_liste"))
    rows, _ = q("SELECT id, nom, groupe_musculaire FROM exercices ORDER BY groupe_musculaire, nom", fetch="all")
    groupes = get_exercices_groupes(rows)
    return render_template("modifier_seance_type.html", groupes=groupes, seance_type=None, exercices_choisis=[])

@app.route("/seances-types/<int:type_id>/modifier", methods=["GET", "POST"])
def modifier_seance_type(type_id):
    seance_type, _ = q("SELECT * FROM seances_types WHERE id = %s", (type_id,), fetch="one")
    if seance_type is None: return redirect(url_for("seances_types_liste"))
    if request.method == "POST":
        nom = request.form.get("nom")
        q("UPDATE seances_types SET nom = %s WHERE id = %s", (nom, type_id), commit=True)
        q("DELETE FROM seances_types_exercices WHERE seance_type_id = %s", (type_id,), commit=True)
        exercice_ids = request.form.getlist("exercice_id[]")
        for ordre, ex_id in enumerate(exercice_ids):
            if ex_id:
                q("INSERT INTO seances_types_exercices (seance_type_id, exercice_id, ordre) VALUES (%s, %s, %s)", (type_id, ex_id, ordre), commit=True)
        return redirect(url_for("seances_types_liste"))
    exercices_choisis_rows, _ = q("SELECT exercice_id FROM seances_types_exercices WHERE seance_type_id = %s ORDER BY ordre", (type_id,), fetch="all")
    exercices_choisis_ids = [str(e["exercice_id"]) for e in exercices_choisis_rows]
    rows, _ = q("SELECT id, nom, groupe_musculaire FROM exercices ORDER BY groupe_musculaire, nom", fetch="all")
    groupes = get_exercices_groupes(rows)
    return render_template("modifier_seance_type.html", groupes=groupes, seance_type=seance_type, exercices_choisis=exercices_choisis_ids)

@app.route("/seances-types/<int:type_id>/supprimer", methods=["POST"])
def supprimer_seance_type(type_id):
    q("DELETE FROM seances_types_exercices WHERE seance_type_id = %s", (type_id,), commit=True)
    q("DELETE FROM seances_types WHERE id = %s", (type_id,), commit=True)
    return redirect(url_for("seances_types_liste"))

if __name__ != "__main__":
    init_db()

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
