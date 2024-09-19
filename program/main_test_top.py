from sqlalchemy import Column, Integer, String, ForeignKey, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Base class for all ORM classes
Base = declarative_base()


class Classe(Base):
    __tablename__ = "classi"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String)
    id_indirizzo = Column(Integer, ForeignKey('indirizzi.id_indirizzo'))

    indirizzo = relationship("Indirizzo", back_populates="classi")
    cattedre = relationship("Cattedra", back_populates="classe")


class Aula(Base):
    __tablename__ = 'aule'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String)
    piano = Column(Integer)
    id_materia = Column(Integer, ForeignKey('materie.id'))
    n_palazzina = Column(Integer)

    materia = relationship("Materia", back_populates='aule')


class Docente(Base):
    __tablename__ = "docenti"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String)
    cognome = Column(String)
    oresettimanali = Column(Integer)

    Materia_Docente = relationship("Materia_Docente", back_populates="docente")
    Disponibilita_Docente = relationship(
        "DisponibilitaDocente", back_populates="docente")
    cattedra_docente = relationship(
        "Cattedra_Docente", back_populates="docente")


class DisponibilitaDocente(Base):
    __tablename__ = 'disponibilitadocenti'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_docente = Column(Integer, ForeignKey('docenti.id'))
    numero_giorno = Column(Integer)

    docente = relationship("Docente", back_populates="Disponibilita_Docente")


class Materia(Base):
    __tablename__ = 'materie'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_materia = Column(String)

    Materia_Docente = relationship("Materia_Docente", back_populates="materia")
    Materia_Indirizzo = relationship(
        "Materia_Indirizzo", back_populates="materia")
    aule = relationship("Aula", back_populates='materia')
    cattedra_materia = relationship(
        "Cattedra_Materia", back_populates="materia")


class Materia_Docente(Base):
    __tablename__ = 'materia_docente'

    id_docente = Column(Integer, ForeignKey('docenti.id'), primary_key=True)
    id_materia = Column(Integer, ForeignKey('materie.id'), primary_key=True)
    ore_per_materia = Column(Integer)

    docente = relationship("Docente", back_populates="Materia_Docente")
    materia = relationship("Materia", back_populates="Materia_Docente")


class Indirizzo(Base):
    __tablename__ = 'indirizzi'

    id_indirizzo = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String)

    Materia_Indirizzo = relationship(
        "Materia_Indirizzo", back_populates="indirizzo")
    classi = relationship("Classe", back_populates="indirizzo")


class Materia_Indirizzo(Base):
    __tablename__ = 'materia_indirizzo'

    id_indirizzo = Column(Integer, ForeignKey(
        'indirizzi.id_indirizzo'), primary_key=True)
    id_materia = Column(Integer, ForeignKey('materie.id'), primary_key=True)

    indirizzo = relationship("Indirizzo", back_populates="Materia_Indirizzo")
    materia = relationship("Materia", back_populates="Materia_Indirizzo")


class Cattedra(Base):
    __tablename__ = 'cattedre'

    id_cattedra = Column(Integer, primary_key=True, autoincrement=True)
    id_classe = Column(Integer, ForeignKey('classi.id'))

    classe = relationship("Classe", back_populates="cattedre")
    cattedra_docente = relationship(
        "Cattedra_Docente", back_populates="cattedra")
    cattedra_materia = relationship(
        "Cattedra_Materia", back_populates="cattedra")


class Cattedra_Docente(Base):
    __tablename__ = 'cattedradocente'

    id_cattedra = Column(Integer, ForeignKey(
        'cattedre.id_cattedra'), primary_key=True)
    id_docente = Column(Integer, ForeignKey('docenti.id'), primary_key=True)

    docente = relationship("Docente", back_populates="cattedra_docente")
    cattedra = relationship("Cattedra", back_populates="cattedra_docente")


class Cattedra_Materia(Base):
    __tablename__ = 'cattedra_materia'

    ore_settimanali = Column(Integer)
    cattedra_id = Column(Integer, ForeignKey(
        'cattedre.id_cattedra'), primary_key=True)
    materia_id = Column(Integer, ForeignKey('materie.id'), primary_key=True)

    cattedra = relationship("Cattedra", back_populates="cattedra_materia")
    materia = relationship("Materia", back_populates="cattedra_materia")


engine = create_engine('mysql://root:@localhost/timetable_example')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

giorni_settimana = ["Lunedi", "Martedi", "Mercoledi",
                    "Giovedi", "Venerdi", "Sabato", "Domenica"]


def stampa_dati():
    print("DOCENTI E LE LORO MATERIE CON RELATIVI INDIRIZZI:\n")
    for docente in session.query(Docente).all():
        print(
            f"Docente: {docente.nome} {docente.cognome} - Ore settimanali: {docente.oresettimanali}")
        if docente.Materia_Docente:
            for materia_docente in docente.Materia_Docente:
                materia = materia_docente.materia
                print(
                    f"  Materia: {materia.nome_materia} - Ore per materia: {materia_docente.ore_per_materia}")
                if materia.Materia_Indirizzo:
                    indirizzi = ', '.join(
                        [mi.indirizzo.nome for mi in materia.Materia_Indirizzo])
                    print(f"    Indirizzi: {indirizzi}")
                else:
                    print("    Indirizzi: Nessun indirizzo specifico")
        else:
            print("  Nessuna materia assegnata")
        print("")

    print("AULE E LE MATERIE CORRISPONDENTI:\n")
    for aula in session.query(Aula).all():
        materia_info = f" - Materia: {aula.materia.nome_materia}" if aula.materia else " - Nessuna materia specifica"
        print(f"Aula: {aula.nome} (Piano {aula.piano}){materia_info}")
    print("")

    print("CLASSI E I LORO INDIRIZZI:\n")
    for classe in session.query(Classe).all():
        indirizzo_info = classe.indirizzo.nome if classe.indirizzo else "Nessun indirizzo specifico"
        print(f"Classe: {classe.nome} - Indirizzo: {indirizzo_info}")
    print("")

    print("DISPONIBILITÀ DEI DOCENTI PER GIORNO:\n")
    for docente in session.query(Docente).all():
        giorni_liberi = ', '.join([giorni_settimana[disponibilita.numero_giorno]
                                  for disponibilita in docente.Disponibilita_Docente])
        print(f"Prof. {docente.cognome} ha come giorni liberi: {giorni_liberi}")
    print("")

    print("CATTEDRE: \n")
    for cattedra in session.query(Cattedra).all():
        classe_info = f"Classe: {cattedra.classe.nome}" if cattedra.classe else "Classe: Nessuna classe specificata"
        print(f"Cattedra ID: {cattedra.id_cattedra} - {classe_info}")

        # Print Docenti information
        if cattedra.cattedra_docente:
            for cattedra_docente in cattedra.cattedra_docente:
                docente = cattedra_docente.docente
                print(f"  Docente: {docente.nome} {docente.cognome}")
        else:
            print("  Nessun docente assegnato")

        # Print Materie information
        if cattedra.cattedra_materia:
            for cattedra_materia in cattedra.cattedra_materia:
                materia = cattedra_materia.materia
                print(
                    f"  Materia: {materia.nome_materia} con ore settimanali: {cattedra_materia.ore_settimanali}")
        else:
            print("  Nessuna materia assegnata")
        print("")


stampa_dati()
