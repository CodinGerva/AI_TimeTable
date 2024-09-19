import json
from datetime import time, datetime, timedelta
from ortools.sat.python import cp_model
from sqlalchemy import create_engine, orm, text
from sqlalchemy.orm import sessionmaker
from main_test_top import *

# Configurazione iniziale del database
engine = create_engine('mysql://root:@localhost/timetable_example')
Session = sessionmaker(bind=engine)
session = Session()

# Modello di programmazione a vincoli
model = cp_model.CpModel()

# Dati da database
materie = session.query(Materia).all()
classi = session.query(Classe).all()
aule = session.query(Aula).all()
cattedre = session.query(Cattedra).all()
disponibilita_docenti = session.query(DisponibilitaDocente).all()

# Funzione per ottenere i docenti per una cattedra


def getDocentibyCattedra(cattedra_id):
    cattedra = session.query(Cattedra).filter(
        Cattedra.id_cattedra == cattedra_id).first()
    if cattedra and cattedra.cattedra_docente:
        return [cd.docente for cd in cattedra.cattedra_docente]
    return []

# Funzione per ottenere le materie per una cattedra


def getMateriebyCattedra(cattedra_id):
    cattedra = session.query(Cattedra).filter(
        Cattedra.id_cattedra == cattedra_id).first()
    if cattedra and cattedra.cattedra_materia:
        return [cm.materia for cm in cattedra.cattedra_materia]
    return []

# Funzione per ottenere i docenti qualificati per una materia


def getDocentiByMateria(docenti, materia_id):
    return [docente for docente in docenti if any(md.id_materia == materia_id for md in docente.Materia_Docente)]

# Funzione per trovare un'aula compatibile per una materia


def findAulaForMateria(materia_id):
    materia = session.query(Materia).filter_by(id=materia_id).first()
    if materia:
        if materia.nome_materia == "motoria":
            return session.query(Aula).filter(Aula.id_materia == materia.id).first()
        indirizzi_ids = [mi.id_indirizzo for mi in materia.Materia_Indirizzo]
        if indirizzi_ids:
            aula_compatible = session.query(Aula).join(Materia, Aula.materia).filter(
                Materia.Materia_Indirizzo.any(
                    Materia_Indirizzo.id_indirizzo.in_(indirizzi_ids))
            ).first()
        else:
            aula_compatible = session.query(Aula).filter(
                Aula.id_materia == 0).first()
    else:
        aula_compatible = session.query(Aula).filter(
            Aula.id_materia == None).first()
    return aula_compatible

# Funzione per creare le lezioni per una classe specifica


def creaLezioniPerClasse(cattedra):
    lezioni_totali = []
    classe = cattedra.classe
    docenti = getDocentibyCattedra(cattedra.id_cattedra)
    for cm in cattedra.cattedra_materia:
        materia = cm.materia
        ore_materia = cm.ore_settimanali
        docenti_qualificati = getDocentiByMateria(docenti, materia.id)
        aula = findAulaForMateria(materia.id)
        if not aula:
            aula = session.query(Aula).filter(Aula.id_materia == None).first()
        aula_nome = aula.nome if aula else "Aula non specificata"
        lezione = {
            "classe": classe,
            "materia": materia.nome_materia,
            "id_materia": materia.id,
            "id_aula": aula.id if aula else None,
            "docente": ", ".join(d.cognome for d in docenti_qualificati) if docenti_qualificati else "Nessun docente",
            "aula": aula_nome,
            "orario_inizio": time(8, 0),
            "orario_fine": time(9, 0),
            "ore": ore_materia,
            "docenti": docenti_qualificati
        }
        lezioni_totali.append(lezione)
    return lezioni_totali

# Funzione per ottenere la disponibilità di un docente


def getDisponibilitaDocente(docente_id):
    return [d.numero_giorno for d in disponibilita_docenti if d.id_docente == docente_id]

# Funzione per pianificare le lezioni utilizzando il modello CP-SAT


def schedule_lessons(lessons):
    model = cp_model.CpModel()
    num_days = 6
    # Numero di ore per ogni giorno della settimana
    hours_per_day = [5, 5, 5, 7, 5, 5]
    slots = sum(hours_per_day)
    lesson_vars = {}

    # Creazione delle variabili per ogni lezione e slot
    for lesson_id, lesson in enumerate(lessons):
        for slot in range(slots):
            lesson_vars[(lesson_id, slot)] = model.NewBoolVar(
                f'lesson_{lesson_id}_slot_{slot}')

    # Vincolo per garantire che ogni lezione sia assegnata solo una volta
    for lesson_id, lesson in enumerate(lessons):
        model.Add(sum(lesson_vars[(lesson_id, slot)]
                  for slot in range(slots)) == lesson['ore'])

    # Vincolo per garantire che ogni classe non abbia più di una lezione per slot
    for slot in range(slots):
        for classe in set(lesson['classe'].nome for lesson in lessons):
            model.Add(sum(lesson_vars[(lesson_id, slot)] for lesson_id, lesson in enumerate(
                lessons) if lesson['classe'].nome == classe) <= 1)

    # Vincolo per garantire la disponibilità dei docenti
    for day in range(num_days):
        day_start = sum(hours_per_day[:day])
        day_end = day_start + hours_per_day[day]
        for docente in set(d.id for lesson in lessons for d in lesson['docenti']):
            disponibilita = getDisponibilitaDocente(docente)
            if day in disponibilita:
                for lesson_id, lesson in enumerate(lessons):
                    if any(d.id == docente for d in lesson['docenti']):
                        for slot in range(day_start, day_end):
                            model.Add(lesson_vars[(lesson_id, slot)] == 0)

    # Vincolo per limitare le ore consecutive di insegnamento
    for lesson_id, lesson in enumerate(lessons):
        materia = lesson['materia']
        ore_settimanali = lesson['ore']
        for day in range(num_days):
            day_start = sum(hours_per_day[:day])
            day_end = day_start + hours_per_day[day]
            slots_per_day = sum(lesson_vars[(lesson_id, slot)]
                                for slot in range(day_start, day_end))
            model.Add(slots_per_day <= 2)

        if ore_settimanali == 3:
            for day in range(num_days):
                day_start = sum(hours_per_day[:day])
                day_end = day_start + hours_per_day[day]
                slots_per_day = sum(
                    lesson_vars[(lesson_id, slot)] for slot in range(day_start, day_end))
                model.Add(slots_per_day <= 1)

    # Risoluzione del modello
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Se il modello ha una soluzione, crea il timetable
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        timetable = [[] for _ in range(num_days)]
        for lesson_id, lesson in enumerate(lessons):
            for slot in range(slots):
                if solver.Value(lesson_vars[(lesson_id, slot)]):
                    day = next(day for day in range(num_days)
                               if slot < sum(hours_per_day[:day + 1]))
                    timetable[day].append((lesson, slot % hours_per_day[day]))
        return timetable
    else:
        print("No solution found.")
        return []

# Funzione per stampare il timetable in console


def print_timetable(timetable, classe_nome):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    print(f"Timetable for class: {classe_nome}")
    for day_idx, daily_lessons in enumerate(timetable):
        day_name = days[day_idx]
        print(f"  {day_name}:")
        daily_lessons.sort(key=lambda x: x[1])
        i = 0
        while i < len(daily_lessons):
            lesson, start_slot = daily_lessons[i]
            end_slot = start_slot
            while (i + 1 < len(daily_lessons) and daily_lessons[i + 1][0]['materia'] == lesson['materia'] and daily_lessons[i + 1][1] == end_slot + 1):
                end_slot += 1
                i += 1
            start_time = (datetime.combine(datetime.today(), time(
                8, 0)) + timedelta(hours=start_slot)).time().strftime('%H:%M')
            end_time = (datetime.combine(datetime.today(), time(8, 0)) +
                        timedelta(hours=end_slot + 1)).time().strftime('%H:%M')
            print(
                f"    {start_time} - {end_time}: {lesson['materia']} in {lesson['aula']} with {lesson['docente']}")
            i += 1

# Funzione per salvare il timetable in un file JSON


def save_timetable_to_json(timetable, classe_nome):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    timetable_dict = {"classe": classe_nome, "orario": {}}

    for day_idx, daily_lessons in enumerate(timetable):
        day_name = days[day_idx]
        timetable_dict["orario"][day_name] = []
        daily_lessons.sort(key=lambda x: x[1])
        i = 0
        while i < len(daily_lessons):
            lesson, start_slot = daily_lessons[i]
            end_slot = start_slot
            while (i + 1 < len(daily_lessons) and daily_lessons[i + 1][0]['materia'] == lesson['materia'] and daily_lessons[i + 1][1] == end_slot + 1):
                end_slot += 1
                i += 1
            start_time = (datetime.combine(datetime.today(), time(
                8, 0)) + timedelta(hours=start_slot)).time().strftime('%H:%M')
            end_time = (datetime.combine(datetime.today(), time(8, 0)) +
                        timedelta(hours=end_slot + 1)).time().strftime('%H:%M')
            timetable_dict["orario"][day_name].append({
                "materia": lesson['materia'],
                "aula": lesson['aula'],
                "orario_inizio": start_time,
                "orario_fine": end_time,
                "docente": lesson['docente']
            })
            i += 1

    with open(f'{classe_nome}_timetable.json', 'w') as json_file:
        json.dump(timetable_dict, json_file, indent=4)


# Creazione e salvataggio degli orari per ogni cattedra
for cattedra in cattedre:
    lezioni = creaLezioniPerClasse(cattedra)
    timetable = schedule_lessons(lezioni)
    print_timetable(timetable, cattedra.classe.nome)  # Stampa in console
    #save_timetable_to_json(timetable, cattedra.classe.nome)  # Salva in JSON

# Chiusura della sessione del database
session.close()
