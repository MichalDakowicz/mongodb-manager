import os
import platform
from pymongo import MongoClient, errors
from faker import Faker
from bson import ObjectId, json_util 
import random
import datetime
import re 
import math

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24) 

from flask.json.provider import JSONProvider
import json as std_json 

class MongoJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return std_json.dumps(obj, default=json_util.default, **kwargs)

    def loads(self, s, **kwargs):
        return std_json.loads(s, object_hook=json_util.object_hook, **kwargs)

app.json = MongoJSONProvider(app)

fake = Faker('pl_PL')

try:
    client = MongoClient('mongodb://localhost:27017/')
    client.admin.command('ping')
    print("Połączono z MongoDB!") 
except errors.ConnectionFailure as e:
    print(f"Nie można połączyć się z MongoDB: {e}")
    
db_name = "firma_db" 
db = client[db_name]
print(f"Używam bazy danych: {db_name}")

pracownicy_coll_name = "pracownicy"
produkty_coll_name = "produkty"
klienci_coll_name = "klienci"
zamowienia_coll_name = "zamowienia"

pracownicy_collection = db[pracownicy_coll_name]
produkty_collection = db[produkty_coll_name]
klienci_collection = db[klienci_coll_name]
zamowienia_collection = db[zamowienia_coll_name]

def generuj_pracownikow(liczba=10):
    pracownicy = []
    stanowiska = ["Programista", "Tester", "Analityk", "Manager Projektu", "HR", "Specjalista ds. Marketingu"]
    for _ in range(liczba):
        umiejetnosci = random.sample(["Python", "Java", "SQL", "MongoDB", "Komunikacja", "Zarządzanie Czasem", "AWS", "Docker"], k=random.randint(1,4))
        pracownik = {
            "imie": fake.first_name(),
            "nazwisko": fake.last_name(),
            "stanowisko": random.choice(stanowiska),
            "email": fake.unique.email(), 
            "data_zatrudnienia": fake.date_time_between(start_date="-5y", end_date=datetime.datetime.now()),
            "wynagrodzenie": round(random.uniform(4500, 18000), 2),
            "miasto": fake.city(),
            "umiejetnosci": umiejetnosci,
            "aktywny": random.choice([True, True, True, False])
        }
        pracownicy.append(pracownik)
    return pracownicy

def generuj_produkty(liczba=10):
    produkty = []
    kategorie = ["Elektronika", "Odzież", "Książki", "Dom i Ogród", "Sport", "Zabawki", "Kosmetyki"]
    for _ in range(liczba):
        produkt = {
            "nazwa": fake.bs().capitalize() + " " + fake.word(),
            "kategoria": random.choice(kategorie),
            "cena": round(random.uniform(5, 1500), 2),
            "dostepna_ilosc": random.randint(0, 200),
            "opis": fake.sentence(nb_words=random.randint(8,15)),
            "data_dodania": fake.date_time_this_decade(),
            "producent": fake.company(),
            "oceny_klientow": [random.randint(1,5) for _ in range(random.randint(0,10))]
        }
        produkty.append(produkt)
    return produkty

def generuj_klientow(liczba=10):
    import datetime as dt_module_for_klienci 
    klienci = []
    typy_klienta = ["Indywidualny", "Biznesowy (Mała Firma)", "Biznesowy (Korporacja)"]
    for _ in range(liczba):
        klient = {
            "imie": fake.first_name(),
            "nazwisko": fake.last_name(),
            "email": fake.unique.email(), 
            "telefon": fake.phone_number(),
            "adres": {
                "ulica": fake.street_address(),
                "miasto": fake.city(),
                "kod_pocztowy": fake.postcode()
            },
            "data_rejestracji": fake.date_time_between(start_date="-3y", end_date=datetime.datetime.now()),
            "typ_klienta": random.choice(typy_klienta),
            "zgody_marketingowe": random.choice([True, False])
        }
        klienci.append(klient)
    return klienci

def generuj_zamowienia(liczba=10, id_pracownikow=None, id_produktow=None, id_klientow=None):
    import datetime as dt_module_for_zamowienia 
    zamowienia = []
    statusy = ["Nowe", "W realizacji", "Oczekuje na płatność", "Wysłane", "Dostarczone", "Anulowane", "Zwrócone"]

    for _ in range(liczba):
        zamowione_produkty = []
        laczna_wartosc = 0
        if id_produktow and len(id_produktow) > 0:
            for _ in range(random.randint(1,3)):
                produkt_id = random.choice(id_produktow)
                produkt_doc = produkty_collection.find_one({"_id": produkt_id}, {"cena": 1})
                cena_produktu = produkt_doc["cena"] if produkt_doc else random.uniform(10, 200)
                ilosc = random.randint(1,3)
                zamowione_produkty.append({
                    "id_produktu": produkt_id,
                    "ilosc": ilosc,
                    "cena_za_sztuke": cena_produktu
                })
                laczna_wartosc += ilosc * cena_produktu

        id_prac = random.choice(id_pracownikow) if id_pracownikow and len(id_pracownikow) > 0 else ObjectId()
        id_kl = random.choice(id_klientow) if id_klientow and len(id_klientow) > 0 else ObjectId()

        zamowienie = {
            "id_klienta": id_kl,
            "produkty": zamowione_produkty,
            "id_pracownika_obslugujacego": id_prac,
            "data_zamowienia": fake.date_time_this_year(),
            "status": random.choice(statusy),
            "wartosc_zamowienia": round(laczna_wartosc, 2),
            "metoda_platnosci": random.choice(["Karta", "Przelew", "BLIK", "Pobranie"]),
            "data_ostatniej_aktualizacji": datetime.datetime.now(),
        }
        zamowienia.append(zamowienie)
    return zamowienia

def formatuj_dokument_do_wyswietlenia(doc, typ_kolekcji=None, czy_agregacja=False, opis_agregacji=""):
    if not isinstance(doc, dict):
        return str(doc)

    formatted_str = ""
    raw_doc_str = f"({doc})" 

    if czy_agregacja:
        if "_id" in doc:
            id_val = doc["_id"]
            other_parts = []
            for key, value in doc.items():
                if key != "_id":
                    if isinstance(value, float):
                        other_parts.append(f"{key.replace('_', ' ').capitalize()}: {value:.2f}")
                    else:
                        other_parts.append(f"{key.replace('_', ' ').capitalize()}: {value}")
            formatted_str = f"{id_val} - {', '.join(other_parts)}"
        elif "Średnie wynagrodzenie na stanowisko" in opis_agregacji and "srednie_wynagrodzenie" in doc and "_id" in doc:
             formatted_str = f"Stanowisko: {doc['_id']}, Średnie wynagrodzenie: {doc['srednie_wynagrodzenie']:.2f}"
        elif "Liczba zamówień i łączna sprzedaż na klient" in opis_agregacji:
            email = doc.get('email_klienta', 'Brak email')
            imie_nazwisko = f"{doc.get('imie_klienta','')} {doc.get('nazwisko_klienta','')}".strip()
            sprzedaz = f"{doc.get('laczna_sprzedaz', 0)::.2f}"
            liczba_zam = doc.get('liczba_zamowien', 0)
            formatted_str = f"Klient: {imie_nazwisko} ({email}), Łączna sprzedaż: {sprzedaz}, Zamówień: {liczba_zam}"

        if not formatted_str:
            if "_id" in doc:
                id_val = doc["_id"]
                other_parts = [f"{k.replace('_', ' ')}: {v:.2f}" if isinstance(v, float) else f"{k.replace('_', ' ')}: {v}" for k, v in doc.items() if k != "_id"]
                formatted_str = f"{id_val} {'- ' if other_parts else ''}{', '.join(other_parts)}"
            else:
                formatted_str = ", ".join([f"{k.replace('_', ' ')}: {v:.2f}" if isinstance(v, float) else f"{k.replace('_', ' ')}: {v}" for k, v in doc.items()])
    else:
        if typ_kolekcji == pracownicy_coll_name:
            imie = doc.get("imie", "")
            nazwisko = doc.get("nazwisko", "")
            stanowisko = doc.get("stanowisko", "Brak stanowiska")
            formatted_str = f"{imie} {nazwisko} - Stanowisko: {stanowisko}, Email: {doc.get('email','N/A')}"
        elif typ_kolekcji == produkty_coll_name:
            nazwa = doc.get("nazwa", "Beznazwy")
            kategoria = doc.get("kategoria", "Brak kategorii")
            cena = doc.get("cena", 0)
            formatted_str = f"{nazwa} - Kategoria: {kategoria}, Cena: {cena:.2f} PLN"
        elif typ_kolekcji == klienci_coll_name:
            imie = doc.get("imie", "")
            nazwisko = doc.get("nazwisko", "")
            email = doc.get("email", "Brak email")
            miasto = doc.get("adres", {}).get("miasto", "Brak miasta")
            formatted_str = f"{imie} {nazwisko} - Email: {email}, Miasto: {miasto}"
        elif typ_kolekcji == zamowienia_coll_name:
            status = doc.get("status", "Brak statusu")
            wartosc = doc.get("wartosc_zamowienia", 0)
            data_zam = doc.get("data_zamowienia")
            data_str = data_zam.strftime("%Y-%m-%d") if isinstance(data_zam, datetime.datetime) else "Brak daty"
            client_name = "N/A"
            if 'id_klienta' in doc and isinstance(doc['id_klienta'], ObjectId):
                klient_doc = klienci_collection.find_one({"_id": doc['id_klienta']}, {"imie":1, "nazwisko":1})
                if klient_doc:
                    client_name = f"{klient_doc.get('imie','')} {klient_doc.get('nazwisko','')}".strip()
            formatted_str = f"Klient: {client_name}, Status: {status}, Wartość: {wartosc:.2f} PLN, Data: {data_str}"


    if formatted_str:
        return formatted_str
    else:
        return str(doc)

@app.context_processor
def utility_processor():
    return dict(
        formatuj_dokument=formatuj_dokument_do_wyswietlenia,
        ObjectId=ObjectId,
        datetime=datetime,
        isinstance=isinstance,
        enumerate=enumerate  
    )

def get_random_id_from_collection(coll):
    doc = coll.find_one({}, {"_id": 1})
    return doc["_id"] if doc else ObjectId()

def get_random_value_from_field(coll, field):
    projection = {field: 1}
    if field in ["producent", "email", "stanowisko", "kategoria", "miasto"]:
        pipeline = [
            {"$match": {field: {"$exists": True, "$ne": None, "$ne": ""}}},
            {"$sample": {"size": 1}},
            {"$project": projection}
        ]
        result = list(coll.aggregate(pipeline))
        if result:
            return result[0].get(field)

    doc = coll.find_one({field: {"$exists": True}}, projection)
    return doc[field] if doc else "BrakWartosciDynamicznej"


wyszukiwania_pracownicy = [
    ("Pracownicy na stanowisku 'Programista'", {"stanowisko": "Programista"}),
    {
        "description": "Pracownicy z wynagrodzeniem > X",
        "params": [
            {"name": "min_salary", "label": "Minimalne Wynagrodzenie (PLN)", "type": "number", "default": 12000, "required": True}
        ],
        "definition": lambda params_values: {"wynagrodzenie": {"$gt": float(params_values["min_salary"])}}
    },
    ("Pracownicy zatrudnieni w 2023", lambda: {"data_zatrudnienia": {"$gte": datetime.datetime(2023,1,1), "$lt": datetime.datetime(2024,1,1)}}),
]
aktualizacje_pracownicy = [
    ("Zwiększ wynagrodzenie Analitykom o 10%",
     {"stanowisko": "Analityk"}, {"$mul": {"wynagrodzenie": 1.1}}),
    ("Dezaktywuj losowego pracownika",
     lambda: {"_id": get_random_id_from_collection(pracownicy_collection)},
     {"$set": {"aktywny": False, "data_dezaktywacji": datetime.datetime.now()}}),
]
agregacje_pracownicy = [
    ("Średnie wynagrodzenie na stanowisko",
     lambda: [{"$group": {"_id": "$stanowisko", "srednie_wynagrodzenie": {"$avg": "$wynagrodzenie"}}}, {"$sort": {"srednie_wynagrodzenie": -1}}]),
    ("Liczba pracowników na miasto",
     lambda: [{"$group": {"_id": "$miasto", "liczba_pracownikow": {"$sum": 1}}}, {"$sort": {"liczba_pracownikow": -1}}]),
    ("Popularność umiejętności",
     lambda: [
         {"$unwind": "$umiejetnosci"},
         {"$group": {"_id": "$umiejetnosci", "liczba_posiadajacych": {"$sum": 1}}},
         {"$sort": {"liczba_posiadajacych": -1}}
     ]),
    ("Średnie wynagrodzenie wg statusu aktywności",
     lambda: [
         {"$group": {"_id": "$aktywny", "srednie_wynagrodzenie": {"$avg": "$wynagrodzenie"}, "liczba_pracownikow": {"$sum": 1}}}
     ]),
]
usuwanie_pracownicy = [
    ("Usuń nieaktywnych pracowników", {"aktywny": False}),
    ("Usuń losowego pracownika", lambda: {"_id": get_random_id_from_collection(pracownicy_collection)}),
]
wyszukiwania_produkty = [
    ("Produkty 'Elektronika', cena > 1000 PLN", {"kategoria": "Elektronika", "cena": {"$gt": 1000}}),
    ("Produkty z zerową ilością", {"dostepna_ilosc": 0}),
]
aktualizacje_produkty = [
    ("Zwiększ cenę 'Zabawek' o 5%",
     {"kategoria": "Zabawki"}, {"$mul": {"cena": 1.05}}),
    ("Ustaw ilość na 0 dla losowego produktu",
     lambda: {"_id": get_random_id_from_collection(produkty_collection)},
     {"$set": {"dostepna_ilosc": 0}}),
]
agregacje_produkty = [
    ("Śr. cena i łączna ilość / kategoria",
     lambda: [{"$group": {"_id": "$kategoria", "srednia_cena": {"$avg": "$cena"}, "laczna_ilosc": {"$sum": "$dostepna_ilosc"}}}, {"$sort": {"_id": 1}}]),
    ("Top 5 najdroższych",
     lambda: [{"$sort": {"cena": -1}}, {"$limit": 5}, {"$project": {"nazwa": 1, "cena": 1, "kategoria": 1}}]),
    ("Liczba produktów / producent",
     lambda: [
         {"$group": {"_id": "$producent", "liczba_produktow": {"$sum": 1}}},
         {"$sort": {"liczba_produktow": -1}},
         {"$limit": 10} 
     ]),
    ("Produkty z największą liczbą ocen klientów",
     lambda: [
         {"$project": {"nazwa": 1, "kategoria": 1, "liczba_ocen": {"$size": "$oceny_klientow"}}},
         {"$sort": {"liczba_ocen": -1}},
         {"$limit": 5}
     ]),
]
usuwanie_produkty = [
    ("Usuń produkty z ilością 0 (bez tagu 'Wyprzedaż')", {"dostepna_ilosc": 0, "tagi": {"$ne": "Wyprzedaż"}}),
]
wyszukiwania_klienci = [
    ("Klienci biznesowi", {"typ_klienta": {"$regex": "Biznesowy"}}),
    ("Klienci z miasta 'Poznań'", {"adres.miasto": "Poznań"}),
]
aktualizacje_klienci = [
    ("Nadaj zgodę marketingową klientom z Warszawy",
     {"typ_klienta": "Indywidualny", "adres.miasto": "Warszawa"}, {"$set": {"zgody_marketingowe": True}}),
    ("Zmień typ losowego klienta na 'VIP'",
     lambda: {"_id": get_random_id_from_collection(klienci_collection)},
     {"$set": {"typ_klienta": "VIP", "notatka": "Upgrade do VIP "+str(datetime.date.today())}}),
]
agregacje_klienci = [
    ("Liczba klientów / typ",
     lambda: [{"$group": {"_id": "$typ_klienta", "liczba": {"$sum": 1}}}, {"$sort": {"liczba": -1}}]),
    ("Klienci zarejestrowani / rok",
     lambda: [{"$group": {"_id": {"$year": "$data_rejestracji"}, "liczba_rejestracji": {"$sum": 1}}}, {"$sort": {"_id": -1}}]),
    ("Rozkład klientów wg miast (Top 10)",
     lambda: [
         {"$group": {"_id": "$adres.miasto", "liczba_klientow": {"$sum": 1}}},
         {"$sort": {"liczba_klientow": -1}},
         {"$limit": 10}
     ]),
    ("Liczba klientów wg zgód marketingowych",
     lambda: [
         {"$group": {"_id": "$zgody_marketingowe", "liczba_klientow": {"$sum": 1}}}
     ]),
]
usuwanie_klienci = [
    ("Usuń klientów bez zgód marketingowych (typ Korporacja)", {"zgody_marketingowe": False, "typ_klienta": "Biznesowy (Korporacja)"}),
]

wyszukiwania_zamowienia = [
    ("Zamówienia 'Nowe' lub 'Oczekuje na płatność'", {"status": {"$in": ["Nowe", "Oczekuje na płatność"]}}),
    ("Zamówienia > 500 PLN", {"wartosc_zamowienia": {"$gt": 500}}),
]
aktualizacje_zamowienia = [
    ("Anuluj zamówienia 'Oczekuje na płatność' > 7 dni",
     lambda: {"status": "Oczekuje na płatność", "data_zamowienia": {"$lt": datetime.datetime.now() - datetime.timedelta(days=7)}},
     {"$set": {"status": "Anulowane", "powod_anulowania": "Brak płatności"}, "$currentDate": {"data_ostatniej_aktualizacji": True}}),
]
agregacje_zamowienia = [
    ("Łączna wartość zamówień / status",
     lambda: [{"$group": {"_id": "$status", "laczna_wartosc": {"$sum": "$wartosc_zamowienia"}, "liczba_zamowien": {"$sum": 1}}}, {"$sort": {"laczna_wartosc": -1}}]),
    ("Sprzedaż / klient (top 5)",
     lambda: [
         {"$group": {"_id": "$id_klienta", "laczna_sprzedaz": {"$sum": "$wartosc_zamowienia"}, "liczba_zamowien": {"$sum": 1}}},
         {"$sort": {"laczna_sprzedaz": -1}}, {"$limit": 5},
         {"$lookup": { "from": klienci_coll_name, "localField": "_id", "foreignField": "_id", "as": "dane_klienta"}},
         {"$unwind": {"path": "$dane_klienta", "preserveNullAndEmptyArrays": True}},
         {"$project": {"id_klienta_oryginalne": "$_id", "email_klienta": "$dane_klienta.email", "imie_klienta": "$dane_klienta.imie", "nazwisko_klienta": "$dane_klienta.nazwisko", "laczna_sprzedaz": 1, "liczba_zamowien": 1, "_id":0}}
     ]),
    ("Średnia wartość zamówienia / metoda płatności",
     lambda: [
         {"$group": {"_id": "$metoda_platnosci", "srednia_wartosc_zamowienia": {"$avg": "$wartosc_zamowienia"}, "liczba_zamowien": {"$sum": 1}}},
         {"$sort": {"srednia_wartosc_zamowienia": -1}}
     ]),
    ("Liczba zamówień / miesiąc",
     lambda: [
         {"$group": {
             "_id": {"rok": {"$year": "$data_zamowienia"}, "miesiac": {"$month": "$data_zamowienia"}},
             "liczba_zamowien": {"$sum": 1},
             "laczna_wartosc": {"$sum": "$wartosc_zamowienia"}
         }},
         {"$sort": {"_id.rok": -1, "_id.miesiac": -1}}
     ]),
]
usuwanie_zamowienia = [
    ("Usuń anulowane zamówienia > 1 rok", lambda: {"status": "Anulowane", "data_zamowienia": {"$lt": datetime.datetime.now() - datetime.timedelta(days=365)}}),
]

dodatkowe_wyszukiwania_pracownicy = [("Nieaktywni pracownicy", {"aktywny": False})]
dodatkowe_wyszukiwania_produkty = [("Produkty w kategorii 'Odzież' lub 'Sport'", {"kategoria": {"$in": ["Odzież", "Sport"]}})]
dodatkowe_wyszukiwania_klienci = [("Klienci indywidualni bez zgód marketingowych", {"typ_klienta": "Indywidualny", "zgody_marketingowe": False})]
dodatkowe_wyszukiwania_zamowienia = [("Zamówienia anulowane lub zwrócone", {"status": {"$in": ["Anulowane", "Zwrócone"]}})]


collection_config = {
    pracownicy_coll_name: {
        "display_name": "Pracownicy",
        "collection": pracownicy_collection,
        "generator": generuj_pracownikow,
        "searches": wyszukiwania_pracownicy,
        "additional_searches": dodatkowe_wyszukiwania_pracownicy,
        "updates": aktualizacje_pracownicy,
        "aggregations": agregacje_pracownicy,
        "deletions": usuwanie_pracownicy,
    },
    produkty_coll_name: {
        "display_name": "Produkty",
        "collection": produkty_collection,
        "generator": generuj_produkty,
        "searches": wyszukiwania_produkty,
        "additional_searches": dodatkowe_wyszukiwania_produkty,
        "updates": aktualizacje_produkty,
        "aggregations": agregacje_produkty,
        "deletions": usuwanie_produkty,
    },
    klienci_coll_name: {
        "display_name": "Klienci",
        "collection": klienci_collection,
        "generator": generuj_klientow,
        "searches": wyszukiwania_klienci,
        "additional_searches": dodatkowe_wyszukiwania_klienci,
        "updates": aktualizacje_klienci,
        "aggregations": agregacje_klienci,
        "deletions": usuwanie_klienci,
    },
    zamowienia_coll_name: {
        "display_name": "Zamówienia",
        "collection": zamowienia_collection,
        "generator": generuj_zamowienia,
        "searches": wyszukiwania_zamowienia,
        "additional_searches": dodatkowe_wyszukiwania_zamowienia,
        "updates": aktualizacje_zamowienia,
        "aggregations": agregacje_zamowienia,
        "deletions": usuwanie_zamowienia,
    }
}

@app.route('/')
def index():
    try:
        fake.unique.clear()
    except Exception as e:
        print(f"Error clearing fake.unique: {e}") 
    return render_template('index.html', collections=collection_config)

@app.route('/collection/<string:coll_name>')
def collection_menu(coll_name):
    config = collection_config.get(coll_name)
    if not config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))
    
    doc_count = config["collection"].count_documents({})
    
    sample_doc = config["collection"].find_one()
    field_names = []
    if sample_doc:
        field_names = list(sample_doc.keys()) 
    else:
        field_names = []


    return render_template('collection_menu.html', 
                           coll_name=coll_name, 
                           config=config, 
                           doc_count=doc_count,
                           field_names=field_names)

@app.route('/collection/<string:coll_name>/add', methods=['POST'])
def add_documents(coll_name):
    config = collection_config.get(coll_name)
    if not config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))

    try:
        if (coll_name == zamowienia_coll_name):
            ids_produktow = [p['_id'] for p in produkty_collection.find({}, {"_id": 1}).limit(50)]
            ids_pracownikow = [p['_id'] for p in pracownicy_collection.find({}, {"_id": 1}).limit(50)]
            ids_klientow = [k['_id'] for k in klienci_collection.find({}, {"_id": 1}).limit(50)]
            
            if not ids_produktow or not ids_pracownikow or not ids_klientow:
                 flash(f"Nie można wygenerować zamówień. Brak wystarczających danych w kolekcjach produktów, pracowników lub klientów. Wygeneruj je najpierw.", "warning")
                 return redirect(url_for('collection_menu', coll_name=coll_name))

            dokumenty = config["generator"](10, ids_pracownikow, ids_produktow, ids_klientow)
        else:
            dokumenty = config["generator"](10)

        if dokumenty:
            result = config["collection"].insert_many(dokumenty, ordered=False)
            flash(f"Dodano {len(result.inserted_ids)} dokumentów do '{config['display_name']}'.", "success")
        else:
            flash(f"Nie wygenerowano dokumentów dla '{config['display_name']}'.", "warning")
    except errors.BulkWriteError as bwe:
        inserted_count = bwe.details.get('nInserted', 0)
        error_count = len(bwe.details.get('writeErrors', []))
        flash(f"Dodano {inserted_count} dokumentów. Wystąpiły błędy (np. duplikaty unique email): {error_count} błędów.", "warning")
        fake.unique.clear() 
    except Exception as e:
        flash(f"Błąd podczas dodawania dokumentów: {e}", "danger")
        app.logger.error(f"Error adding documents to {coll_name}: {e}")

    return redirect(url_for('collection_menu', coll_name=coll_name))


@app.route('/collection/<string:coll_name>/view')
def view_documents(coll_name):
    config = collection_config.get(coll_name)
    if not config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    if limit <=0 : limit = 20
    if limit > 100: limit = 100
    if page <= 0: page = 1

    try:
        total_docs = config["collection"].count_documents({})
        if total_docs == 0:
            documents = []
            total_pages = 0
        else:
            total_pages = math.ceil(total_docs / limit)
            if page > total_pages and total_pages > 0 :
                page = total_pages
            
            skip_amount = (page - 1) * limit
            documents = list(config["collection"].find().skip(skip_amount).limit(limit))
        
    except Exception as e:
        flash(f"Błąd podczas pobierania dokumentów: {e}", "danger")
        documents = []
        total_docs = 0
        total_pages = 0
        app.logger.error(f"Error viewing documents from {coll_name}: {e}")

    return render_template('view_documents.html',
                           coll_name=coll_name,
                           config=config,
                           documents=documents,
                           current_limit=limit,
                           total_docs=total_docs,
                           current_page=page,
                           total_pages=total_pages)

@app.route('/collection/<string:coll_name>/<string:op_type>/<int:op_idx>', methods=['GET', 'POST'])
def execute_operation_view(coll_name, op_type, op_idx):
    config = collection_config.get(coll_name)
    if not config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))

    collection = config["collection"]
    op_type_map = {
        "search": "searches",
        "additional_search": "additional_searches",
        "aggregate": "aggregations"
    }
    if op_type not in op_type_map:
        flash(f"Nieznany typ operacji: {op_type}", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    op_list = config.get(op_type_map[op_type], [])
    if not 0 <= op_idx < len(op_list):
        flash(f"Nieprawidłowy indeks operacji: {op_idx}", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    current_op_config = op_list[op_idx]
    results = None
    error_msg = None
    query_details_str = ""
    description = ""
    is_aggregation = op_type == "aggregate"
    aggregation_description_for_formatting = ""

    if isinstance(current_op_config, dict) and "params" in current_op_config and current_op_config["params"]:
        description = current_op_config["description"]
        aggregation_description_for_formatting = description if is_aggregation else ""

        if request.method == 'GET':
            return render_template('parameter_form.html',
                                   coll_name=coll_name,
                                   op_type=op_type,
                                   op_idx=op_idx,
                                   operation=current_op_config,
                                   config=config,
                                   form_action_url=url_for('execute_operation_view', coll_name=coll_name, op_type=op_type, op_idx=op_idx)
                                   )
        
        elif request.method == 'POST':
            try:
                submitted_params = {}
                for param_def in current_op_config["params"]:
                    val = request.form.get(param_def["name"])
                    if val is None and param_def.get("required"):
                        raise ValueError(f"Parametr '{param_def['label']}' jest wymagany.")
                    
                    if val is not None: 
                        if param_def["type"] == "number":
                            try:
                                if '.' in val:
                                    submitted_params[param_def["name"]] = float(val)
                                else:
                                    submitted_params[param_def["name"]] = int(val)
                            except ValueError:
                                raise ValueError(f"Wartość dla '{param_def['label']}' musi być liczbą.")
                        elif param_def["type"] == "boolean":
                            submitted_params[param_def["name"]] = val.lower() in ['true', 'yes', '1']
                        else: 
                            submitted_params[param_def["name"]] = val
                    elif "default" in param_def:
                         submitted_params[param_def["name"]] = param_def["default"] 

                actual_query_or_pipeline = current_op_config["definition"](submitted_params)
                query_details_str = json_util.dumps(actual_query_or_pipeline, indent=2)

                if op_type == "aggregate":
                    results = list(collection.aggregate(actual_query_or_pipeline))
                else: 
                    results = list(collection.find(actual_query_or_pipeline))
                
                flash(f"Operacja '{description}' wykonana pomyślnie.", "success")

            except errors.PyMongoError as e:
                error_msg = f"Błąd MongoDB: {e}"
                app.logger.error(f"MongoDB error for {description} in {coll_name}: {e}. Query: {query_details_str}")
            except ValueError as e:
                error_msg = f"Błąd wartości parametru: {e}"
            except Exception as e:
                error_msg = f"Nieoczekiwany błąd: {e}"
                app.logger.error(f"Unexpected error for {description} in {coll_name}: {e}. Query: {query_details_str}")
            
            return render_template('view_results.html',
                                   coll_name=coll_name,
                                   description=description,
                                   results=results,
                                   error_msg=error_msg,
                                   query_details=query_details_str,
                                   config=config,
                                   op_type_display=op_type.replace("_", " ").capitalize(),
                                   is_aggregation=is_aggregation,
                                   aggregation_description_for_formatting=aggregation_description_for_formatting)

    else: 
        if isinstance(current_op_config, tuple):
            description, query_or_pipeline_def = current_op_config
            actual_query_or_pipeline = query_or_pipeline_def() if callable(query_or_pipeline_def) else query_or_pipeline_def
        elif isinstance(current_op_config, dict) and "definition" in current_op_config : 
            description = current_op_config["description"]
            actual_query_or_pipeline = current_op_config["definition"]({}) 
        else:
            flash("Nieprawidłowa konfiguracja operacji.", "danger")
            return redirect(url_for('collection_menu', coll_name=coll_name))

        aggregation_description_for_formatting = description if is_aggregation else ""
        query_details_str = json_util.dumps(actual_query_or_pipeline, indent=2)
        try:
            if op_type == "aggregate":
                results = list(collection.aggregate(actual_query_or_pipeline))
            else: 
                results = list(collection.find(actual_query_or_pipeline))
        except errors.PyMongoError as e:
            error_msg = f"Błąd MongoDB: {e}"
            app.logger.error(f"MongoDB error for {description} in {coll_name}: {e}. Query: {query_details_str}")
        except Exception as e:
            error_msg = f"Nieoczekiwany błąd: {e}"
            app.logger.error(f"Unexpected error for {description} in {coll_name}: {e}. Query: {query_details_str}")

        return render_template('view_results.html',
                               coll_name=coll_name,
                               description=description,
                               results=results,
                               error_msg=error_msg,
                               query_details=query_details_str,
                               config=config,
                               op_type_display=op_type.replace("_", " ").capitalize(),
                               is_aggregation=is_aggregation,
                               aggregation_description_for_formatting=aggregation_description_for_formatting)

@app.route('/collection/<string:coll_name>/<string:action_type>/<int:action_idx>/confirm', methods=['GET', 'POST'])
def confirm_action(coll_name, action_type, action_idx):
    config = collection_config.get(coll_name)
    if not config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))

    action_list_name_map = {"update": "updates", "delete": "deletions"}
    if action_type not in action_list_name_map:
        flash(f"Nieznany typ akcji: {action_type}", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    action_list_name = action_list_name_map[action_type]
    action_list = config.get(action_list_name)

    if not action_list or action_idx < 0 or action_idx >= len(action_list):
        flash("Nieprawidłowy indeks akcji.", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    if action_type == "update":
        opis, crit_def, op_def = action_list[action_idx]
        criteria = crit_def() if callable(crit_def) else crit_def
        operation = op_def() if callable(op_def) else op_def
        action_details = {"criteria": str(criteria), "operation": str(operation)}
    elif action_type == "delete":
        opis, crit_def = action_list[action_idx]
        criteria = crit_def() if callable(crit_def) else crit_def
        action_details = {"criteria": str(criteria)}
    
    try:
        affected_count = config["collection"].count_documents(criteria)
    except Exception as e:
        flash(f"Błąd przy szacowaniu liczby dokumentów: {e}", "warning")
        affected_count = "N/A (błąd)"
        app.logger.warning(f"Error counting docs for {action_type} on {coll_name}: {e}")


    if request.method == 'POST':
        try:
            if action_type == "update":
                if "jeden" in opis.lower() or "konkretny" in opis.lower() or ("_id" in criteria and isinstance(criteria.get("_id"), ObjectId)):
                    result = config["collection"].update_one(criteria, operation)
                    flash(f"Zaktualizowano: Dopasowano {result.matched_count}, Zmodyfikowano {result.modified_count} dokument. ({opis})", "success")
                else:
                    result = config["collection"].update_many(criteria, operation)
                    flash(f"Zaktualizowano: Dopasowano {result.matched_count}, Zmodyfikowano {result.modified_count} dokumentów. ({opis})", "success")
            elif action_type == "delete":
                if "jeden" in opis.lower() or "konkretny" in opis.lower() or ("_id" in criteria and isinstance(criteria.get("_id"), ObjectId)):
                    result = config["collection"].delete_one(criteria)
                    flash(f"Usunięto: {result.deleted_count} dokument. ({opis})", "success")
                else:
                    result = config["collection"].delete_many(criteria)
                    flash(f"Usunięto: {result.deleted_count} dokumentów. ({opis})", "success")
            return redirect(url_for('collection_menu', coll_name=coll_name))
        except errors.PyMongoError as e:
            flash(f"Błąd MongoDB podczas {action_type}: {e} ({opis})", "danger")
            app.logger.error(f"MongoDB error during {action_type} for {coll_name}: {e}")
        except Exception as e:
            flash(f"Nieoczekiwany błąd podczas {action_type}: {e} ({opis})", "danger")
            app.logger.error(f"Unexpected error during {action_type} for {coll_name}: {e}")
        return redirect(url_for('confirm_action', coll_name=coll_name, action_type=action_type, action_idx=action_idx))


    return render_template('confirm_action.html',
                           coll_name=coll_name,
                           config=config,
                           action_type=action_type,
                           action_idx=action_idx,
                           description=opis,
                           action_details=action_details,
                           affected_count=affected_count)


@app.route('/collection/<string:coll_name>/clear_all', methods=['POST'])
def clear_collection(coll_name):
    config = collection_config.get(coll_name)
    if not config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))

    try:
        if request.form.get("confirm_clear") != "yes":
            flash("Potwierdzenie usunięcia wszystkich dokumentów nie zostało zaznaczone.", "warning")
            return redirect(url_for('collection_menu', coll_name=coll_name))

        result = config["collection"].delete_many({})
        flash(f"Usunięto {result.deleted_count} dokumentów z kolekcji '{config['display_name']}'.", "success")
        if coll_name == pracownicy_coll_name or coll_name == klienci_coll_name:
            fake.unique.clear()
            flash("Pamięć unikalnych wartości Faker została wyczyszczona.", "info")
    except Exception as e:
        flash(f"Błąd podczas czyszczenia kolekcji '{config['display_name']}': {e}", "danger")
        app.logger.error(f"Error clearing collection {coll_name}: {e}")
    return redirect(url_for('collection_menu', coll_name=coll_name))


@app.route('/collection/<string:coll_name>/custom_update', methods=['POST'])
def custom_update_document(coll_name):
    config = collection_config.get(coll_name)
    if not config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))

    collection = config["collection"]
    
    doc_id_str = request.form.get('doc_id_str')
    field_to_update_selected = request.form.get('field_to_update')
    other_field_name = request.form.get('other_field_name')
    new_value_str = request.form.get('new_value_str')
    value_type = request.form.get('value_type')

    if not doc_id_str or new_value_str is None or not value_type:
        flash("ID dokumentu, nowa wartość i typ wartości są wymagane.", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    field_to_update = other_field_name.strip() if field_to_update_selected == '__OTHER__' and other_field_name else field_to_update_selected
    
    if not field_to_update:
        flash("Pole do aktualizacji jest wymagane.", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    try:
        doc_id = ObjectId(doc_id_str)
    except Exception as e:
        flash(f"Nieprawidłowy format ID dokumentu: '{doc_id_str}'. Błąd: {e}", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    converted_value = None
    try:
        if value_type == "Number":
            try:
                converted_value = float(new_value_str)
                if converted_value.is_integer():
                    converted_value = int(converted_value)
            except ValueError:
                flash(f"Nie można przekonwertować '{new_value_str}' na liczbę.", "danger")
                return redirect(url_for('collection_menu', coll_name=coll_name))
        elif value_type == "Boolean":
            if new_value_str.lower() == 'true':
                converted_value = True
            elif new_value_str.lower() == 'false':
                converted_value = False
            else:
                flash(f"Nie można przekonwertować '{new_value_str}' na wartość logiczną (oczekiwano 'true' lub 'false').", "danger")
                return redirect(url_for('collection_menu', coll_name=coll_name))
        else:
            converted_value = new_value_str
    except Exception as e:
        flash(f"Błąd konwersji wartości '{new_value_str}' na typ '{value_type}': {e}", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    try:
        result = collection.update_one(
            {"_id": doc_id},
            {"$set": {field_to_update: converted_value}}
        )
        if result.matched_count == 0:
            flash(f"Nie znaleziono dokumentu o ID: {doc_id_str}.", "warning")
        elif result.modified_count == 0:
            flash(f"Dokument o ID: {doc_id_str} został znaleziony, ale nie został zmodyfikowany (możliwe, że nowa wartość jest taka sama jak istniejąca lub pole nie istnieje na najwyższym poziomie).", "info")
        else:
            flash(f"Dokument o ID: {doc_id_str} został pomyślnie zaktualizowany. Pole '{field_to_update}' zmieniono.", "success")
    except errors.PyMongoError as e:
        flash(f"Błąd MongoDB podczas aktualizacji: {e}", "danger")
        app.logger.error(f"MongoDB error during custom update for {coll_name}: {e}")
    except Exception as e:
        flash(f"Nieoczekiwany błąd podczas aktualizacji: {e}", "danger")
        app.logger.error(f"Unexpected error during custom update for {coll_name}: {e}")
from datetime import datetime as DateTimeClass
import re 

from bson.errors import InvalidId


def parse_value(value_str, type_str):
    if type_str == "Null":
        return None

    if type_str in ["StringList", "NumberList", "ObjectIdList"]:
        if value_str is None or value_str.strip() == '':
            return []
        
    if value_str is None or value_str.strip() == '':
        if type_str == "String":
            return "" 
        else:
            raise ValueError(f"Wartość dla typu '{type_str}' nie może być pusta.")

    try:
        if type_str == "String":
            return str(value_str)
        elif type_str == "Number":
            try:
                return int(value_str)
            except ValueError:
                return float(value_str)
        elif type_str == "Boolean":
            return value_str.lower() in ['true', '1', 'yes', 'on']
        elif type_str == "ObjectId":
            return ObjectId(value_str)
        elif type_str == "Date_ISO": 
            return DateTimeClass.fromisoformat(value_str)
        elif type_str == "StringList":
            return [s.strip() for s in value_str.split(',') if s.strip()]
        elif type_str == "NumberList":
            numbers = []
            for item in value_str.split(','):
                item_stripped = item.strip()
                if item_stripped:
                    try:
                        numbers.append(int(item_stripped))
                    except ValueError:
                        numbers.append(float(item_stripped))
            return numbers
        elif type_str == "ObjectIdList":
            return [ObjectId(s.strip()) for s in value_str.split(',') if s.strip()]
        elif type_str == "JSON":
            try:
                return json_util.loads(value_str) 
            except Exception as e_json:
                raise ValueError(f"Nieprawidłowy ciąg JSON: {value_str}. Błąd: {e_json}")
        else:
            app.logger.warning(f"Nieznany typ wartości '{type_str}' napotkany dla wartości '{value_str}'. Traktowanie jako String.")
            return str(value_str)
    except InvalidId as e_id: 
        raise ValueError(f"Nieprawidłowy ObjectId '{value_str}' dla typu '{type_str}'. Błąd: {e_id}")
    except Exception as e:
        app.logger.error(f"Błąd parsowania wartości '{value_str}' jako typ '{type_str}': {e}")
        raise ValueError(f"Nieprawidłowa wartość '{value_str}' dla typu '{type_str}'. Błąd: {e}")

@app.route('/collection/<string:coll_name>/dynamic_search', methods=['POST'])
def dynamic_search_view(coll_name):
    current_config = collection_config.get(coll_name)
    if not current_config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))

    collection_to_search = current_config["collection"]
    query = {}
    results = []
    error_message = None
    search_summary_parts = ["Dynamiczne Wyszukiwanie"] 

    try:
        form_data = request.form
        
        parsed_criteria_from_form = []
        i = 0
        while True:
            field_key = f'criteria[{i}][field]'
            if field_key not in form_data: 
                break 

            field = form_data.get(field_key)
            operator = form_data.get(f'criteria[{i}][operator]')
            value_str = form_data.get(f'criteria[{i}][value]') 
            type_str = form_data.get(f'criteria[{i}][type]', 'String') 

            if not field or not operator:
                app.logger.warning(f"Dynamic search: Incomplete criterion at index {i} for collection {coll_name}. Field: '{field}', Operator: '{operator}'. Skipping.")
                i += 1
                continue

            parsed_criteria_from_form.append({
                "field": field,
                "operator": operator,
                "value_str": value_str, 
                "type_str": type_str,
                "original_index": i 
            })
            i += 1
        
        if not parsed_criteria_from_form and not form_data.get('sort_field') and not form_data.get('limit_results', '0').isdigit():
             flash("Nie zdefiniowano żadnych kryteriów wyszukiwania, sortowania ani limitu.", "info")
        
        mongo_conditions = []
        human_readable_conditions = [] 

        for criterion in parsed_criteria_from_form:
            field = criterion['field']
            operator = criterion['operator']
            value_str = criterion['value_str']
            type_str = criterion['type_str']
            
            condition_part = {}

            if operator == '$exists':
                condition_part[field] = {"$exists": True}
                human_readable_conditions.append(f"'{field}' istnieje")
            elif operator == '$notExists':
                condition_part[field] = {"$exists": False}
                human_readable_conditions.append(f"'{field}' nie istnieje")
            else: 
                try:
                    parsed_value = parse_value(value_str, type_str)
                except ValueError as e:
                    error_message = f"Błąd konwersji wartości dla pola '{field}' (kryterium {criterion['original_index'] + 1}): {e}"
                    flash(error_message, "danger")
                    break 

                if parsed_value is None and type_str != "Null":
                    if operator not in ['$eq', '$ne']: 
                        flash(f"Pominięto kryterium dla pola '{field}' (kryterium {criterion['original_index'] + 1}) z operatorem '{operator}' z powodu pustej/nieprawidłowej wartości.", "warning")
                        continue 
                
                if operator == '$eq':
                    condition_part[field] = parsed_value
                    human_readable_conditions.append(f"'{field}' = {json_util.dumps(parsed_value)}")
                elif operator == '$ne':
                    condition_part[field] = {"$ne": parsed_value}
                    human_readable_conditions.append(f"'{field}' != {json_util.dumps(parsed_value)}")
                elif operator == '$gt':
                    condition_part[field] = {"$gt": parsed_value}
                    human_readable_conditions.append(f"'{field}' > {json_util.dumps(parsed_value)}")
                elif operator == '$gte':
                    condition_part[field] = {"$gte": parsed_value}
                    human_readable_conditions.append(f"'{field}' >= {json_util.dumps(parsed_value)}")
                elif operator == '$lt':
                    condition_part[field] = {"$lt": parsed_value}
                    human_readable_conditions.append(f"'{field}' < {json_util.dumps(parsed_value)}")
                elif operator == '$lte':
                    condition_part[field] = {"$lte": parsed_value}
                    human_readable_conditions.append(f"'{field}' <= {json_util.dumps(parsed_value)}")
                elif operator == '$regex_contains':
                    condition_part[field] = {"$regex": str(parsed_value), "$options": "i"}
                    human_readable_conditions.append(f"'{field}' zawiera (tekst) '{parsed_value}'")
                elif operator == '$regex_starts':
                    condition_part[field] = {"$regex": f"^{re.escape(str(parsed_value))}", "$options": "i"}
                    human_readable_conditions.append(f"'{field}' zaczyna się od '{parsed_value}'")
                elif operator == '$regex_ends':
                    condition_part[field] = {"$regex": f"{re.escape(str(parsed_value))}$", "$options": "i"}
                    human_readable_conditions.append(f"'{field}' kończy się na '{parsed_value}'")
                elif operator == '$in':
                    if not isinstance(parsed_value, list): parsed_value = [parsed_value]
                    condition_part[field] = {"$in": parsed_value}
                    human_readable_conditions.append(f"'{field}' jest jednym z {json_util.dumps(parsed_value)}")
                elif operator == '$nin':
                    if not isinstance(parsed_value, list): parsed_value = [parsed_value]
                    condition_part[field] = {"$nin": parsed_value}
                    human_readable_conditions.append(f"'{field}' nie jest jednym z {json_util.dumps(parsed_value)}")
                elif operator == '$all':
                    if not isinstance(parsed_value, list):
                        flash(f"Wartość dla operatora '$all' (pole '{field}') musi być listą. Otrzymano: {type(parsed_value)}.", "warning")
                        continue
                    condition_part[field] = {"$all": parsed_value}
                    human_readable_conditions.append(f"'{field}' zawiera wszystkie z {json_util.dumps(parsed_value)}")
                elif operator == '$size':
                    if not isinstance(parsed_value, int):
                        flash(f"Wartość dla operatora '$size' (pole '{field}') musi być liczbą całkowitą. Otrzymano: {type(parsed_value)}.", "warning")
                        continue
                    condition_part[field] = {"$size": parsed_value}
                    human_readable_conditions.append(f"'{field}' ma rozmiar {parsed_value}")
                elif operator == '$elemMatch':
                    if not isinstance(parsed_value, dict):
                        flash(f"Wartość dla operatora '$elemMatch' (pole '{field}') musi być obiektem JSON. Otrzymano: {type(parsed_value)}.", "warning")
                        continue
                    condition_part[field] = {"$elemMatch": parsed_value}
                    human_readable_conditions.append(f"'{field}' zawiera element pasujący do {json_util.dumps(parsed_value)}")
                else:
                    flash(f"Nierozpoznany lub nieobsługiwany operator '{operator}' dla pola '{field}'.", "warning")
                    continue 
            
            if condition_part:
                mongo_conditions.append(condition_part)
        
        if error_message: 
            pass 
        elif mongo_conditions:
            query = {"$and": mongo_conditions} if len(mongo_conditions) > 1 else mongo_conditions[0]
            search_summary_parts.append("Kryteria: " + " ORAZ ".join(human_readable_conditions))
        elif parsed_criteria_from_form: 
             flash("Podane kryteria nie mogły zostać przetworzone na zapytanie MongoDB.", "warning")
        
        sort_field = form_data.get('sort_field')
        sort_order_str = form_data.get('sort_order', 'asc')
        sort_order = 1 if sort_order_str == 'asc' else -1
        sort_params = []
        if sort_field:
            sort_params.append((sort_field, sort_order))
            search_summary_parts.append(f"Sortowanie: {sort_field} ({sort_order_str.upper()})")

        limit_results_str = form_data.get('limit_results')
        limit = 0 
        if limit_results_str and limit_results_str.isdigit() and int(limit_results_str) > 0:
            limit = int(limit_results_str)
            if limit > 500: 
                limit = 500
                flash("Przekroczono maksymalny limit wyników (500). Wyniki zostały ograniczone.", "warning")
            search_summary_parts.append(f"Limit: {limit}")

        if not error_message: 
            cursor = collection_to_search.find(query)
            if sort_params:
                cursor = cursor.sort(sort_params)
            if limit > 0: 
                cursor = cursor.limit(limit)
            
            results = list(cursor) 

            if not results and (query or parsed_criteria_from_form): 
                flash("Nie znaleziono dokumentów pasujących do kryteriów.", "info")
            elif not results and not query and not parsed_criteria_from_form and not sort_field and not limit_results_str : 
                 pass
            elif not results and not query and not parsed_criteria_from_form and (sort_field or limit_results_str): 
                 flash("Kolekcja jest pusta lub nie znaleziono dokumentów.", "info")


    except errors.PyMongoError as e:
        app.logger.error(f"MongoDB Error during dynamic search in {coll_name}: {e}. Query: {json_util.dumps(query)}")
        error_message = f"Błąd bazy danych: {e}"
        flash(error_message, "danger")
        results = [] 
    except Exception as e:
        app.logger.error(f"General Error during dynamic search in {coll_name}: {e}. Query: {json_util.dumps(query)}")
        error_message = f"Wystąpił nieoczekiwany błąd: {e}"
        flash(error_message, "danger")
        results = [] 
    
    final_search_summary = " | ".join(filter(None,search_summary_parts))
    if final_search_summary == "Dynamiczne Wyszukiwanie": 
        final_search_summary = "Dynamiczne Wyszukiwanie (bez filtrów)"


    return render_template('view_results.html',
                           coll_name=coll_name,
                           config=current_config, 
                           results=results,
                           op_type_display="Dynamiczne Wyszukiwanie", 
                           query_details=json_util.dumps(query, indent=2), 
                           description=final_search_summary,
                           typ_kolekcji=coll_name, 
                           error_msg=error_message if error_message else None, 
                           is_aggregation=False, 
                           aggregation_description_for_formatting="") 

@app.route('/collection/<string:coll_name>/dynamic_update', methods=['POST'])
def dynamic_update_view(coll_name):
    current_config = collection_config.get(coll_name)
    if not current_config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))

    collection_to_update = current_config["collection"]
    form_data = request.form
    
    mongo_criteria_list = []
    human_readable_criteria = []
    final_criteria_query = {}

    i = 0
    while True:
        field_key = f'criteria[{i}][field]'
        if field_key not in form_data:
            break
        
        field = form_data.get(field_key)
        operator = form_data.get(f'criteria[{i}][operator]')
        value_str = form_data.get(f'criteria[{i}][value]')
        type_str = form_data.get(f'criteria[{i}][type]', 'String')

        if not field or not operator:
            i += 1
            continue
        
        try:
            condition_part = {}
            if operator == '$exists':
                condition_part[field] = {"$exists": True}
                human_readable_criteria.append(f"'{field}' istnieje")
            elif operator == '$notExists': 
                condition_part[field] = {"$exists": False}
                human_readable_criteria.append(f"'{field}' nie istnieje")
            else:
                parsed_value = parse_value(value_str, type_str)
                if parsed_value is None and type_str != "Null" and operator not in ['$eq', '$ne']:
                    flash(f"Pominięto kryterium dla pola '{field}' (operator '{operator}') z powodu pustej wartości (typ: {type_str}).", "warning")
                    i+=1
                    continue

                if operator == '$eq': condition_part[field] = parsed_value
                elif operator == '$ne': condition_part[field] = {"$ne": parsed_value}
                elif operator == '$gt': condition_part[field] = {"$gt": parsed_value}
                elif operator == '$gte': condition_part[field] = {"$gte": parsed_value}
                elif operator == '$lt': condition_part[field] = {"$lt": parsed_value}
                elif operator == '$lte': condition_part[field] = {"$lte": parsed_value}
                elif operator == '$in':
                    if not isinstance(parsed_value, list): parsed_value = [parsed_value]
                    condition_part[field] = {"$in": parsed_value}
                elif operator == '$nin':
                    if not isinstance(parsed_value, list): parsed_value = [parsed_value]
                    condition_part[field] = {"$nin": parsed_value}
                else: 
                    condition_part[field] = {operator: parsed_value}
                
                human_readable_criteria.append(f"'{field}' {operator} {json_util.dumps(parsed_value)}")

            if condition_part:
                mongo_criteria_list.append(condition_part)
        except ValueError as e:
            flash(f"Błąd w kryterium {i+1} (pole '{field}'): {e}", "danger")
            return redirect(url_for('collection_menu', coll_name=coll_name))
        i += 1

    if not mongo_criteria_list:
        final_criteria_query = {}
    elif len(mongo_criteria_list) == 1:
        final_criteria_query = mongo_criteria_list[0]
    else:
        final_criteria_query = {"$and": mongo_criteria_list}

    mongo_update_doc = {}
    human_readable_updates = []
    j = 0
    while True:
        op_key = f'updates[{j}][operator]'
        if op_key not in form_data:
            break

        update_operator = form_data.get(op_key)
        update_field = form_data.get(f'updates[{j}][field]')
        update_value_str = form_data.get(f'updates[{j}][value]')
        update_type_str = form_data.get(f'updates[{j}][type]', 'String')

        if not update_operator or (not update_field and update_operator not in ['$rename']): 
            if update_operator == '$unset' and update_field: 
                 pass 
            else:
                j += 1
                continue
        
        try:
            parsed_update_value = None
            
            if update_operator == '$unset':
                if not update_field:
                    flash(f"Dla operacji '$unset' (operacja {j+1}) nazwa pola jest wymagana.", "danger")
                    return redirect(url_for('collection_menu', coll_name=coll_name))
                parsed_update_value = "" 
                human_readable_updates.append(f"'{update_operator}' dla pola '{update_field}'")
            elif update_operator == '$currentDate':
                if update_value_str.lower() == 'true':
                    parsed_update_value = True
                else:
                    try:
                        parsed_update_value = json_util.loads(update_value_str) 
                    except Exception:
                        flash(f"Nieprawidłowa wartość dla '$currentDate' (operacja {j+1}, pole '{update_field}'). Oczekiwano 'true' lub obiektu JSON (np. {{'$type':'timestamp'}}).", "danger")
                        return redirect(url_for('collection_menu', coll_name=coll_name))
                human_readable_updates.append(f"'{update_operator}' dla pola '{update_field}' na {update_value_str}")
            elif update_operator == '$rename':
                 if not update_field or not update_value_str: 
                    flash(f"Dla operacji '$rename' (operacja {j+1}) wymagane jest podanie starej i nowej nazwy pola.", "danger")
                    return redirect(url_for('collection_menu', coll_name=coll_name))
                 if '$rename' not in mongo_update_doc: mongo_update_doc['$rename'] = {}
                 mongo_update_doc['$rename'][update_field] = update_value_str 
                 human_readable_updates.append(f"'{update_operator}' pola '{update_field}' na '{update_value_str}'")
                 j += 1
                 continue 
            else: 
                if update_value_str is None: 
                    flash(f"Wartość dla operatora '{update_operator}' (operacja {j+1}, pole '{update_field}') jest wymagana.", "danger")
                    return redirect(url_for('collection_menu', coll_name=coll_name))
                parsed_update_value = parse_value(update_value_str, update_type_str)
                human_readable_updates.append(f"'{update_operator}' dla pola '{update_field}' z wartością {json_util.dumps(parsed_update_value)}")

            if update_operator not in mongo_update_doc:
                mongo_update_doc[update_operator] = {}
            
            mongo_update_doc[update_operator][update_field] = parsed_update_value

        except ValueError as e:
            flash(f"Błąd w operacji aktualizacji {j+1} (operator '{update_operator}', pole '{update_field}'): {e}", "danger")
            return redirect(url_for('collection_menu', coll_name=coll_name))
        j += 1
        
    if not mongo_update_doc:
        flash("Brak zdefiniowanych operacji aktualizacji.", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    update_scope = form_data.get('update_scope', 'many') 
    upsert = form_data.get('upsert_document') == 'true'


    try:
        summary_criteria = " AND ".join(human_readable_criteria) if human_readable_criteria else "Wszystkie dokumenty"
        summary_updates = ", ".join(human_readable_updates)
        
        if update_scope == 'one':
            result = collection_to_update.update_one(final_criteria_query, mongo_update_doc, upsert=upsert)
            flash_msg = f"UpdateOne wykonane. Kryteria: [{summary_criteria}]. Operacje: [{summary_updates}]. "
            flash_msg += f"Dopasowano: {result.matched_count}, Zmodyfikowano: {result.modified_count}."
            if upsert and result.upserted_id:
                flash_msg += f" Wstawiono nowy dokument z ID: {result.upserted_id}."
            flash(flash_msg, "success")
        else: 
            result = collection_to_update.update_many(final_criteria_query, mongo_update_doc, upsert=upsert)
            flash_msg = f"UpdateMany wykonane. Kryteria: [{summary_criteria}]. Operacje: [{summary_updates}]. "
            flash_msg += f"Dopasowano: {result.matched_count}, Zmodyfikowano: {result.modified_count}."
            if upsert and result.upserted_id: 
                flash_msg += f" Wstawiono nowy dokument z ID: {result.upserted_id}."
            flash(flash_msg, "success")

    except errors.PyMongoError as e:
        flash(f"Błąd MongoDB podczas dynamicznej aktualizacji: {e}. Kryteria: {json_util.dumps(final_criteria_query)}, Update: {json_util.dumps(mongo_update_doc)}", "danger")
        app.logger.error(f"MongoDB error during dynamic update for {coll_name}: {e}")
    except Exception as e:
        flash(f"Nieoczekiwany błąd podczas dynamicznej aktualizacji: {e}", "danger")
        app.logger.error(f"Unexpected error during dynamic update for {coll_name}: {e}")

    return redirect(url_for('collection_menu', coll_name=coll_name))


@app.route('/collection/<string:coll_name>/dynamic_delete', methods=['POST'])
def dynamic_delete_view(coll_name):
    current_config = collection_config.get(coll_name)
    if not current_config:
        flash(f"Nieznana kolekcja: {coll_name}", "danger")
        return redirect(url_for('index'))

    collection_to_update = current_config["collection"]
    form_data = request.form
    
    mongo_criteria_list = []
    human_readable_criteria = []
    final_criteria_query = {}

    i = 0
    while True:
        field_key = f'criteria[{i}][field]'
        if field_key not in form_data:
            break
        
        field = form_data.get(field_key)
        operator = form_data.get(f'criteria[{i}][operator]')
        value_str = form_data.get(f'criteria[{i}][value]')
        type_str = form_data.get(f'criteria[{i}][type]', 'String')

        if not field or not operator: 
            app.logger.warning(f"Dynamic delete: Incomplete criterion at index {i} for {coll_name}. Skipping.")
            i += 1
            continue
        
        try:
            condition_part = {}
            if operator == '$exists':
                condition_part[field] = {"$exists": True}
                human_readable_criteria.append(f"'{field}' istnieje")
            elif operator == '$notExists': 
                condition_part[field] = {"$exists": False}
                human_readable_criteria.append(f"'{field}' nie istnieje")
            else: 
                parsed_value = parse_value(value_str, type_str)
                if parsed_value is None and type_str != "Null" and operator not in ['$eq', '$ne']:
                    flash(f"Pominięto kryterium usuwania dla pola '{field}' (operator '{operator}') z powodu pustej/nieprawidłowej wartości (typ: {type_str}).", "warning")
                    i+=1
                    continue
                
                if operator == '$eq': condition_part[field] = parsed_value
                elif operator == '$ne': condition_part[field] = {"$ne": parsed_value}
                elif operator == '$gt': condition_part[field] = {"$gt": parsed_value}
                elif operator == '$gte': condition_part[field] = {"$gte": parsed_value}
                elif operator == '$lt': condition_part[field] = {"$lt": parsed_value}
                elif operator == '$lte': condition_part[field] = {"$lte": parsed_value}
                elif operator == '$in':
                    if not isinstance(parsed_value, list): parsed_value = [parsed_value]
                    condition_part[field] = {"$in": parsed_value}
                elif operator == '$nin':
                    if not isinstance(parsed_value, list): parsed_value = [parsed_value]
                    condition_part[field] = {"$nin": parsed_value}
                elif operator == '$regex': 
                    condition_part[field] = {"$regex": str(parsed_value)} 
                else:
                    flash(f"Nierozpoznany lub nieobsługiwany operator '{operator}' dla kryterium usuwania pola '{field}'.", "warning")
                    i+=1
                    continue
                
                human_readable_criteria.append(f"'{field}' {operator} {json_util.dumps(parsed_value)}")

            if condition_part:
                mongo_criteria_list.append(condition_part)
        except ValueError as e:
            flash(f"Błąd w kryterium usuwania {i+1} (pole '{field}'): {e}", "danger")
            return redirect(url_for('collection_menu', coll_name=coll_name))
        i += 1

    if not mongo_criteria_list:
        flash("Operacja usuwania wymaga zdefiniowania co najmniej jednego kryterium. Operacja anulowana.", "danger")
        return redirect(url_for('collection_menu', coll_name=coll_name))

    if len(mongo_criteria_list) == 1:
        final_criteria_query = mongo_criteria_list[0]
    else:
        final_criteria_query = {"$and": mongo_criteria_list}

    delete_scope = form_data.get('delete_scope', 'many') 

    try:
        summary_criteria = " AND ".join(human_readable_criteria)
        deleted_count = 0

        if delete_scope == 'one':
            result = collection_to_update.delete_one(final_criteria_query)
            deleted_count = result.deleted_count
            flash_msg = f"DeleteOne wykonane. Kryteria: [{summary_criteria}]. "
            flash_msg += f"Usunięto dokumentów: {deleted_count}."
        else: 
            result = collection_to_update.delete_many(final_criteria_query)
            deleted_count = result.deleted_count
            flash_msg = f"DeleteMany wykonane. Kryteria: [{summary_criteria}]. "
            flash_msg += f"Usunięto dokumentów: {deleted_count}."
        
        if deleted_count > 0:
            flash(flash_msg, "success")
        else:
            flash(f"Nie znaleziono dokumentów pasujących do kryteriów [{summary_criteria}]. Nic nie usunięto.", "info")


    except errors.PyMongoError as e:
        flash(f"Błąd MongoDB podczas dynamicznego usuwania: {e}. Kryteria: {json_util.dumps(final_criteria_query)}", "danger")
        app.logger.error(f"MongoDB error during dynamic delete for {coll_name}: {e}")
    except Exception as e:
        flash(f"Nieoczekiwany błąd podczas dynamicznego usuwania: {e}", "danger")
        app.logger.error(f"Unexpected error during dynamic delete for {coll_name}: {e}")

    return redirect(url_for('collection_menu', coll_name=coll_name))


import json
from bson import ObjectId, json_util

def parse_form_value(value_str):
    if not isinstance(value_str, str):
        return value_str 

    if value_str.lower() == 'true':
        return True
    if value_str.lower() == 'false':
        return False

    if len(value_str) == 24:
       
        try:
            return ObjectId(value_str)
        except Exception:
            pass 
    
    try:
        return int(value_str)
    except ValueError:
        pass 

    try:
        return float(value_str)
    except ValueError:
        pass 

    try:
        if value_str.strip().startswith(('{', '[')):
            return json.loads(value_str)
    except json.JSONDecodeError:
        pass 

    return value_str

@app.route('/<db_name>/<collection_name>/dynamic_aggregation', methods=['POST'])
def dynamic_aggregation_view(db_name, collection_name):
    if db_name not in client.list_database_names():
        flash(f"Baza danych '{db_name}' nie istnieje.", 'danger')
        return redirect(url_for('index'))
    if collection_name not in client[db_name].list_collection_names():
        flash(f"Kolekcja '{collection_name}' nie istnieje w bazie '{db_name}'.", 'danger')
        return redirect(url_for('index'))

    collection = client[db_name][collection_name]
    pipeline = []
    human_readable_pipeline = []

    form_stages = request.form.to_dict(flat=False)
    
    parsed_stages = {}
    for key, value_list in form_stages.items():
        value = value_list[0] if value_list else None 
        if not value: continue

        parts = key.replace(']', '').split('[') 
        stage_idx = int(parts[1])
        
        if stage_idx not in parsed_stages:
            parsed_stages[stage_idx] = {}

        if parts[2] == 'type':
            parsed_stages[stage_idx]['type'] = value
        elif parts[2] == 'config':
            if len(parts) == 3: 
                try:
                    parsed_stages[stage_idx]['config_data'] = json.loads(value)
                except json.JSONDecodeError:
                    flash(f"Błąd parsowania JSON dla etapu {stage_idx + 1}: {value}", 'danger')
                    return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            elif len(parts) == 4: 
                if 'config_data' not in parsed_stages[stage_idx]:
                    parsed_stages[stage_idx]['config_data'] = {}
                
                config_key = parts[3]
                if parsed_stages[stage_idx].get('type') == '$group' and config_key == 'accumulators':
                    try:
                        parsed_stages[stage_idx]['config_data'][config_key] = json.loads(value)
                    except json.JSONDecodeError:
                        flash(f"Błąd parsowania JSON dla akumulatorów w etapie $group {stage_idx + 1}: {value}", 'danger')
                        return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
                elif parsed_stages[stage_idx].get('type') == '$unwind' and config_key == 'preserveNullAndEmptyArrays':
                     parsed_stages[stage_idx]['config_data'][config_key] = (value == 'on') 
                elif parsed_stages[stage_idx].get('type') in ['$limit', '$skip']:
                    try:
                        parsed_stages[stage_idx]['config_data'][config_key] = int(value)
                    except ValueError:
                        flash(f"Nieprawidłowa wartość liczbowa dla {config_key} w etapie {stage_idx + 1}: {value}", 'danger')
                        return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
                else:
                    parsed_stages[stage_idx]['config_data'][config_key] = parse_form_value(value)
        
        elif parts[2] == 'config_json' and value.strip(): 
            try:
                parsed_stages[stage_idx]['config_data'] = json.loads(value)
                parsed_stages[stage_idx]['using_config_json'] = True
            except json.JSONDecodeError:
                flash(f"Błąd parsowania JSON dla 'config_json' w etapie {stage_idx + 1}: {value}", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))

    for idx in sorted(parsed_stages.keys()):
        stage_data = parsed_stages[idx]
        stage_type = stage_data.get('type')
        config = stage_data.get('config_data', {})

        if not stage_type:
            flash(f"Typ etapu {idx + 1} nie został określony.", 'warning')
            continue

        current_stage = {}
        human_readable_stage = f"Etap {idx + 1}: {stage_type}"

        if stage_type == '$match':
            if not isinstance(config, dict):
                flash(f"Konfiguracja dla $match w etapie {idx+1} musi być obiektem JSON.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            current_stage[stage_type] = config
            human_readable_stage += f" z kryteriami: {json.dumps(config, indent=2, default=str)}"
        elif stage_type == '$group':
            group_config = {}
            if '_id' not in config:
                flash(f"Brak '_id' w konfiguracji $group dla etapu {idx+1}.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            group_config['_id'] = config['_id'] 
            
            if 'accumulators' in config and isinstance(config['accumulators'], dict):
                for key, acc_value in config['accumulators'].items():
                    group_config[key] = acc_value 
            current_stage[stage_type] = group_config
            human_readable_stage += f" grupujący po: {config['_id']}, akumulatory: {json.dumps(config.get('accumulators',{}), indent=2, default=str)}"
        elif stage_type == '$sort':
            if not isinstance(config, dict):
                flash(f"Konfiguracja dla $sort w etapie {idx+1} musi być obiektem JSON.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            current_stage[stage_type] = config
            human_readable_stage += f" sortujący według: {json.dumps(config, indent=2, default=str)}"
        elif stage_type == '$project':
            if not isinstance(config, dict):
                flash(f"Konfiguracja dla $project w etapie {idx+1} musi być obiektem JSON.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            current_stage[stage_type] = config
            human_readable_stage += f" projekcja: {json.dumps(config, indent=2, default=str)}"
        elif stage_type == '$limit':
            if 'limit' not in config or not isinstance(config['limit'], int):
                flash(f"Nieprawidłowa lub brakująca wartość 'limit' dla etapu $limit {idx+1}.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            current_stage[stage_type] = config['limit']
            human_readable_stage += f" limit: {config['limit']}"
        elif stage_type == '$skip':
            if 'skip' not in config or not isinstance(config['skip'], int):
                flash(f"Nieprawidłowa lub brakująca wartość 'skip' dla etapu $skip {idx+1}.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            current_stage[stage_type] = config['skip']
            human_readable_stage += f" pomiń: {config['skip']}"
        elif stage_type == '$unwind':
            if 'path' not in config or not isinstance(config['path'], str):
                flash(f"Nieprawidłowa lub brakująca ścieżka ('path') dla etapu $unwind {idx+1}.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            unwind_spec = {'path': config['path']}
            if config.get('preserveNullAndEmptyArrays', False):
                unwind_spec['preserveNullAndEmptyArrays'] = True
            current_stage[stage_type] = unwind_spec
            human_readable_stage += f" rozwijanie: {config['path']}"
            if unwind_spec.get('preserveNullAndEmptyArrays'):
                 human_readable_stage += " (zachowaj puste/null)"
        elif stage_type == '$lookup':
            if stage_data.get('using_config_json') and isinstance(config, dict):
                current_stage[stage_type] = config
                human_readable_stage += f" lookup (JSON): {json.dumps(config, indent=2, default=str)}"
            elif isinstance(config, dict):
                required_fields = ['from', 'localField', 'foreignField', 'as']
                if not all(k in config for k in required_fields):
                    flash(f"Brakujące pola dla podstawowego $lookup w etapie {idx+1}. Wymagane: {', '.join(required_fields)}.", 'danger')
                    return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
                current_stage[stage_type] = {
                    'from': config['from'],
                    'localField': config['localField'],
                    'foreignField': config['foreignField'],
                    'as': config['as']
                }
                human_readable_stage += f" łączący z '{config['from']}' jako '{config['as']}' przez {config['localField']}={config['foreignField']}"
            else:
                flash(f"Nieprawidłowa konfiguracja dla $lookup w etapie {idx+1}.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
        elif stage_type == '$addFields':
            if not isinstance(config, dict):
                flash(f"Konfiguracja dla $addFields w etapie {idx+1} musi być obiektem JSON.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            current_stage[stage_type] = config
            human_readable_stage += f" dodający pola: {json.dumps(config, indent=2, default=str)}"
        elif stage_type == '$count':
            if 'output_field_name' not in config or not isinstance(config['output_field_name'], str):
                flash(f"Nieprawidłowa lub brakująca nazwa pola wyjściowego dla etapu $count {idx+1}.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            current_stage[stage_type] = config['output_field_name']
            human_readable_stage += f" liczący dokumenty do pola: {config['output_field_name']}"
        elif stage_type == '$out':
            if 'collection_name' not in config or not isinstance(config['collection_name'], str):
                flash(f"Nieprawidłowa lub brakująca nazwa kolekcji docelowej dla etapu $out {idx+1}.", 'danger')
                return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))
            current_stage[stage_type] = config['collection_name']
            human_readable_stage += f" zapisujący do kolekcji: {config['collection_name']}"
        else:
            flash(f"Nierozpoznany typ etapu: {stage_type} w etapie {idx + 1}.", 'warning')
            continue
        
        if current_stage:
            pipeline.append(current_stage)
            human_readable_pipeline.append(human_readable_stage)

    if not pipeline:
        flash("Potok agregacji jest pusty. Dodaj co najmniej jeden etap.", 'warning')
        return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))

    try:
        app.logger.info(f"Wykonywanie agregacji dla {db_name}/{collection_name} z potokiem: {json.dumps(pipeline, default=str)}")
        results = list(collection.aggregate(pipeline))
        
        # Convert the list to a formatted string
        query_details_str = "\n".join(human_readable_pipeline)
        
        if pipeline[-1].get('$out'):
            out_collection_name = pipeline[-1]['$out']
            flash(f"Wyniki agregacji zostały zapisane do kolekcji '{out_collection_name}'.", 'success')
            return render_template('view_results.html', 
                                db_name=db_name, 
                                collection_name=collection_name, 
                                results=[], 
                                count=0, 
                                query_type='Agregacja (z $out)', 
                                query_details=query_details_str,
                                message=f"Dane zapisane do kolekcji '{out_collection_name}'. Potok wykonany pomyślnie.")

        flash(f"Agregacja wykonana pomyślnie. Znaleziono {len(results)} dokumentów.", 'success')
        return render_template('view_results.html', 
                            db_name=db_name, 
                            collection_name=collection_name, 
                            results=results, 
                            count=len(results), 
                            query_type='Agregacja Dynamiczna', 
                            query_details=query_details_str)
    except Exception as e:
        app.logger.error(f"Błąd podczas wykonywania agregacji: {e}")
        app.logger.error(f"Potok: {json.dumps(pipeline, default=str)}")
        flash(f"Błąd podczas wykonywania agregacji: {e}", 'danger')
        return redirect(url_for('collection_menu', db_name=db_name, collection_name=collection_name))

if __name__ == '__main__':
    app.run(debug=True)