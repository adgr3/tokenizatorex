"""Generator syntetycznego korpusu JSON do wywołań narzędzi (TKX-V21-JSON).

Wszystko jest fikcyjne i wygenerowane lokalnie (licencja: nasze dane).
50 narzędzi: 40 do treningu, 10 wyłącznie do zbioru held-out.
Nazwy narzędzi: polskie bez znaków diakrytycznych i angielskie.

Formy zapisu: kompaktowa, z wcięciami, wrapper OpenAI tool_calls, definicja
schematu narzędzia (JSON Schema) i odpowiedź narzędzia.

Użycie:
  python tkx_v21/generuj_json.py --out tkx_v21/dane
"""
from __future__ import annotations

import argparse
import json
import os
import random
from typing import Any

SEED = 20261123

# 25 polskich + 25 angielskich nazw; 40 pierwszych (po przemieszaniu deterministycznym)
# idzie do treningu, 10 ostatnich tylko do held-out.
TOOLS_PL = [
    ("szukaj_konkursow", "Wyszukuje konkursy ofert według obszaru i województwa."),
    ("podaj_termin", "Zwraca termin naboru dla wskazanego konkursu."),
    ("pobierz_pogode", "Pobiera prognozę pogody dla miasta i daty."),
    ("utworz_fakture", "Tworzy fakturę dla kontrahenta na podstawie pozycji."),
    ("wyslij_email", "Wysyła wiadomość e-mail do wskazanego odbiorcy."),
    ("sprawdz_cpv", "Sprawdza, czy kod CPV pasuje do opisu przedmiotu zamówienia."),
    ("pobierz_dokument", "Pobiera dokument z repozytorium po identyfikatorze."),
    ("zapisz_plik", "Zapisuje treść w pliku w wskazanym katalogu."),
    ("kalkuluj_kwote", "Liczy kwotę brutto z netto, VAT i rabatu."),
    ("wyszukaj_firme", "Wyszukuje firmę po NIP, REGON lub nazwie."),
    ("sprawdz_krs", "Sprawdza wpis w KRS i zwraca status podmiotu."),
    ("pobierz_uchwale", "Pobiera uchwałę rady gminy z dziennika urzędowego."),
    ("utworz_zadanie", "Tworzy zadanie w systemie z terminem i priorytetem."),
    ("podaj_statystyki", "Zwraca statystyki naborów w podanym okresie."),
    ("wygeneruj_raport", "Generuje raport PDF z zestawieniem danych."),
    ("pobierz_slownik", "Pobiera słownik kodów i skrótów prawnych."),
    ("sprawdz_regon", "Weryfikuje numer REGON i zwraca dane podmiotu."),
    ("dodaj_kontakt", "Dodaje kontakt do bazy z adresem i telefonem."),
    ("zaplanuj_spotkanie", "Planuje spotkanie w kalendarzu z uczestnikami."),
    ("pobierz_zalacznik", "Pobiera załącznik z ogłoszenia o zamówieniu."),
    ("przelicz_walute", "Przelicza kwotę między walutami po kursie z dnia."),
    ("sprawdz_bzp", "Sprawdza numer ogłoszenia w Biuletynie Zamówień Publicznych."),
    ("utworz_oferte", "Tworzy ofertę z pozycjami, cenami i terminem ważności."),
    ("pobierz_liste", "Pobiera listę dokumentów spełniających filtr."),
    ("zarejestruj_wniosek", "Rejestruje wniosek o dofinansowanie w systemie."),
    ("create_invoice", "Creates an invoice for a customer with line items."),
    ("send_notification", "Sends a notification to a user or channel."),
    ("fetch_exchange_rate", "Fetches the exchange rate for a currency pair."),
    ("update_contact", "Updates a contact record with new details."),
    ("schedule_meeting", "Schedules a meeting and invites participants."),
    ("search_documents", "Searches documents by query and date range."),
    ("download_file", "Downloads a file from object storage."),
    ("create_task", "Creates a task with assignee, due date and priority."),
    ("calculate_total", "Calculates a total from items, tax and discount."),
    ("lookup_company", "Looks up a company by tax identifier or name."),
    ("check_status", "Checks the status of an order or application."),
    ("generate_report", "Generates a report in PDF or CSV format."),
    ("send_email", "Sends an email message with attachments."),
    ("convert_currency", "Converts an amount between currencies."),
    ("upload_document", "Uploads a document to a folder."),
    ("list_projects", "Lists projects filtered by owner and status."),
    ("get_weather", "Returns a weather forecast for a location."),
    ("create_calendar_event", "Creates a calendar event with reminders."),
    ("fetch_invoice", "Fetches an invoice by its identifier."),
    ("send_sms", "Sends an SMS message to a phone number."),
    ("translate_text", "Translates text between languages."),
    ("summarize_text", "Summarizes a longer text to a given length."),
    ("extract_entities", "Extracts dates, amounts and identifiers from text."),
    ("validate_address", "Validates a postal address and returns normalized form."),
    ("archive_record", "Archives a record and returns an archive identifier."),
]

HELDOUT_NAMES = {
    "list_projects", "upload_document", "create_calendar_event", "archive_record",
    "validate_address", "get_weather", "convert_currency", "summarize_text",
    "extract_entities", "fetch_invoice",
}

CITIES = ["Warszawa", "Kraków", "Gdańsk", "Wrocław", "Poznań", "Łódź", "Lublin",
          "Szczecin", "Bydgoszcz", "Białystok", "Katowice", "Rzeszów", "Toruń"]
STREETS = ["Kwiatowa", "Przemysłowa", "Słoneczna", "Leśna", "Rynek", "Fabryczna",
           "Ogrodowa", "Dworcowa", "Polna", "Krótka", "Sportowa", "Wspólna"]
COMPANIES = ["Studio Orion Sp. z o.o.", "Fundacja Dobry Start", "Nord Trans S.A.",
             "Pracownia Zielona", "Systemy Delta sp.k.", "Inicjatywa Lokalna",
             "Grupa Wisła", "Technologie Aurora", "Dom Kultury Promyk",
             "Stowarzyszenie Razem", "Przedsiębiorstwo Jantar", "Ogrody Północy"]
AREAS = ["cyfryzacja", "edukacja", "zdrowie", "kultura", "środowisko",
         "transport", "sport", "pomoc społeczna", "turystyka", "rolnictwo"]
VOIVODESHIPS = ["mazowieckie", "małopolskie", "pomorskie", "dolnośląskie",
                "wielkopolskie", "łódzkie", "lubelskie", "zachodniopomorskie"]
CURRENCIES = ["PLN", "EUR", "USD", "CHF", "GBP"]
HELDOUT_CITIES = ["Sopot", "Zakopane", "Olsztyn", "Kielce", "Opole", "Gorzów Wielkopolski",
                  "Zielona Góra", "Nowy Sącz", "Elbląg", "Koszalin", "Płock", "Sieradz"]
HELDOUT_PROPERTIES = [
    ("lokalizacja", "string"), ("data_wizyty", "date"), ("budzet_pln", "amount"),
    ("identyfikator_zlecenia", "string"), ("tryb", "string"), ("lista_pozycji", "array_object"),
    ("odbiorca", "email"), ("temat", "string"), ("zalaczniki", "array_string"),
    ("metryka", "string"), ("poziom", "integer"), ("notatka_robocza", "string"),
    ("czas_trwania", "integer"), ("strefa", "string"), ("waluta_zrodlowa", "currency"),
    ("waluta_docelowa", "currency"), ("kwota_zrodlowa", "amount"), ("rabat_procent", "number"),
    ("miasto_docelowe", "string"), ("ulica_docelowa", "string"), ("kod_docelowy", "string"),
    ("kanal", "string"), ("tresc_skrocona", "string"), ("znacznik_czasu", "date"),
    ("poziom_dostepu", "string"), ("wersja", "integer"), ("zrodlo", "string"),
    ("jezyk", "string"), ("format_wyniku", "string"), ("opiekun", "string"),
    ("status_zlecenia", "status"), ("priorytet_wysoki", "boolean"), ("indeks", "integer"),
]
CPV = ["45000000-7", "48000000-8", "72000000-5", "30000000-9", "85000000-9",
       "79000000-4", "55500000-5", "90910000-9", "33100000-1", "80500000-9"]
STATUSES = ["nowy", "w toku", "zaakceptowany", "odrzucony", "wstrzymany", "zakończony"]


def _date(rng: random.Random) -> str:
    return f"20{rng.choice([26, 27])}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"


def _amount(rng: random.Random) -> str:
    whole = rng.randint(1, 2_000_000)
    gr = rng.randint(0, 99)
    style = rng.randrange(4)
    if style == 0:
        return f"{whole:,}".replace(",", " ") + f",{gr:02d} zł"
    if style == 1:
        s = f"{whole:,}".replace(",", ".")
        return f"{s},{gr:02d} PLN"
    if style == 2:
        return f"{whole}.{gr:02d}"
    return f"{whole} zł"


def _nip(rng: random.Random) -> str: return "".join(str(rng.randint(0, 9)) for _ in range(10))
def _regon(rng: random.Random) -> str: return "".join(str(rng.randint(0, 9)) for _ in range(9))
def _krs(rng: random.Random) -> str: return "".join(str(rng.randint(0, 9)) for _ in range(10))
def _postal(rng: random.Random) -> str: return f"{rng.randint(10, 99):02d}-{rng.randint(100, 999):03d}"
def _bzp(rng: random.Random) -> str: return f"2026/BZP {rng.randint(1, 99999999):08d}"
def _sygnatura(rng: random.Random) -> str:
    return rng.choice([f"KIO {rng.randint(1, 4000)}/26", f"II SA/Wa {rng.randint(1, 3000)}/26",
                       f"VIII SA/Wr {rng.randint(1, 2000)}/26"])
def _address(rng: random.Random) -> dict[str, Any]:
    return {"ulica": f"ul. {rng.choice(STREETS)} {rng.randint(1, 120)}",
            "kod_pocztowy": _postal(rng), "miasto": rng.choice(CITIES)}


PROPERTY_POOL = [
    ("id", "string"), ("nazwa", "string"), ("miasto", "string"), ("data_od", "date"),
    ("data_do", "date"), ("kwota", "amount"), ("waluta", "currency"), ("kod_cpv", "cpv"),
    ("nip", "nip"), ("regon", "regon"), ("krs", "krs"), ("adres", "address"),
    ("aktywny", "boolean"), ("limit", "integer"), ("procent", "number"),
    ("tagi", "array_string"), ("pozycje", "array_object"), ("opis", "string"),
    ("email", "email"), ("www", "url"), ("sygnatura", "sygnatura"),
    ("numer_bzp", "bzp"), ("status", "status"), ("wojewodztwo", "voivodeship"),
    ("obszar", "area"), ("kurs", "number"), ("waluta_z", "currency"), ("waluta_na", "currency"),
    ("telefon", "phone"), ("plik", "string"), ("folder", "string"), ("notatka", "string"),
    ("data_spotkania", "date"), ("uczestnicy", "array_string"), ("priorytet", "integer"),
    ("rabat", "number"), ("vat", "number"), ("foreign", "boolean"), ("null_value", "null"),
]


def _value(kind: str, rng: random.Random) -> Any:
    if kind == "string":
        return rng.choice(["K-0023", "ZP/26/14", "dok-8842", "raport-2026-09", "umowa_17",
                           "Wniosek o dofinansowanie", "analiza rynku", "projekt graficzny"])
    if kind == "date":
        return _date(rng)
    if kind == "amount":
        return _amount(rng)
    if kind == "currency":
        return rng.choice(CURRENCIES)
    if kind == "cpv":
        return rng.choice(CPV)
    if kind == "nip":
        return _nip(rng)
    if kind == "regon":
        return _regon(rng)
    if kind == "krs":
        return _krs(rng)
    if kind == "address":
        return _address(rng)
    if kind == "boolean":
        return rng.choice([True, False])
    if kind == "integer":
        return rng.randint(0, 5000)
    if kind == "number":
        return round(rng.uniform(0, 100), rng.choice([0, 1, 2]))
    if kind == "array_string":
        pool = ["pilne", "granty", "cpv", "2026", "uchwały", "oferty", "BZP", "samorząd"]
        return rng.sample(pool, rng.randint(1, 4))
    if kind == "array_object":
        return [{"nazwa": rng.choice(["druk", "skan", "opinia", "projekt"]),
                 "ilosc": rng.randint(1, 20),
                 "cena": rng.randint(10, 5000)} for _ in range(rng.randint(1, 3))]
    if kind == "email":
        return rng.choice(["kontakt@example.org", "biuro@firma.example", "oferty@urzad.example"])
    if kind == "url":
        return rng.choice(["https://example.org/bzp/2026", "https://example.com/docs/17",
                           "http://bip.example.pl/nabor"])
    if kind == "sygnatura":
        return _sygnatura(rng)
    if kind == "bzp":
        return _bzp(rng)
    if kind == "status":
        return rng.choice(STATUSES)
    if kind == "voivodeship":
        return rng.choice(VOIVODESHIPS)
    if kind == "area":
        return rng.choice(AREAS)
    if kind == "phone":
        return f"+48 {rng.randint(500, 899)} {rng.randint(100, 999)} {rng.randint(100, 999)}"
    if kind == "null":
        return None
    raise ValueError(kind)


def _schema_for(properties: list[tuple[str, str]], rng: random.Random) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for name, kind in properties:
        tmap = {"date": "string", "amount": "string", "cpv": "string", "nip": "string",
                "regon": "string", "krs": "string", "address": "object", "boolean": "boolean",
                "array_string": "array", "array_object": "array", "sygnatura": "string",
                "bzp": "string", "status": "string", "voivodeship": "string", "area": "string",
                "currency": "string", "email": "string", "url": "string", "phone": "string",
                "null": "null"}
        base: dict[str, Any] = {"type": tmap.get(kind, kind)}
        if kind == "date":
            base["format"] = "date"
        elif kind == "email":
            base["format"] = "email"
        elif kind == "url":
            base["format"] = "uri"
        elif kind == "array_string":
            base["items"] = {"type": "string"}
        elif kind == "array_object":
            base["items"] = {"type": "object", "properties": {
                "nazwa": {"type": "string"}, "ilosc": {"type": "integer"},
                "cena": {"type": "number"}}, "required": ["nazwa", "ilosc"]}
        elif kind == "address":
            base["properties"] = {"ulica": {"type": "string"}, "kod_pocztowy": {"type": "string"},
                                  "miasto": {"type": "string"}}
            base["required"] = ["ulica", "miasto"]
        base["description"] = rng.choice([
            "Identyfikator obiektu.", "Wartość liczbowa.", "Data w formacie ISO 8601.",
            "Kwota w złotych.", "Kod CPV.", "Adres korespondencyjny.", "Znacznik logiczny.",
            "Lista wartości.", "Numer identyfikacyjny.", "Dodatkowy opis.",
        ])
        props[name] = base
    required = [n for n, _ in properties if rng.random() < 0.7]
    if not required:
        required = [properties[0][0]]
    return {"type": "object", "properties": props, "required": required,
            "additionalProperties": False}


def _arguments(schema: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, spec in schema["properties"].items():
        kind = "string"
        t = spec.get("type")
        if t == "string":
            if spec.get("format") == "date":
                kind = "date"
            elif spec.get("format") == "email":
                kind = "email"
            elif spec.get("format") == "uri":
                kind = "url"
            elif name in ("kwota", "wartosc", "cena", "amount"):
                kind = "amount"
            elif name in ("kod_cpv", "cpv"):
                kind = "cpv"
            elif name == "nip":
                kind = "nip"
            elif name == "regon":
                kind = "regon"
            elif name == "krs":
                kind = "krs"
            elif name == "sygnatura":
                kind = "sygnatura"
            elif name == "numer_bzp":
                kind = "bzp"
            elif name == "status":
                kind = "status"
            elif name == "wojewodztwo":
                kind = "voivodeship"
            elif name == "obszar":
                kind = "area"
            elif name == "waluta":
                kind = "currency"
            elif name == "telefon":
                kind = "phone"
        elif t == "boolean":
            kind = "boolean"
        elif t == "integer":
            kind = "integer"
        elif t == "number":
            kind = "number"
        elif t == "array":
            kind = "array_object" if spec.get("items", {}).get("type") == "object" else "array_string"
        elif t == "object":
            kind = "address"
        elif t == "null":
            kind = "null"
        if rng.random() < 0.08 and name not in schema["required"]:
            out[name] = None
        else:
            out[name] = _value(kind, rng)
    return out


def _tool_specs(rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tools = []
    for name, desc in TOOLS_PL:
        nprops = rng.randint(2, 6)
        chosen = rng.sample(PROPERTY_POOL, nprops)
        schema = _schema_for(chosen, rng)
        tools.append({"name": name, "description": desc, "schema": schema,
                      "heldout": name in HELDOUT_NAMES})
    rng.shuffle(tools)
    train = [t for t in tools if not t["heldout"]]
    held = [t for t in tools if t["heldout"]]
    return train, held


def _compact_call(t: dict[str, Any], rng: random.Random) -> str:
    args = _arguments(t["schema"], rng)
    return "<tool_call>" + json.dumps({"name": t["name"], "arguments": args},
                                      ensure_ascii=False, separators=(",", ":")) + "</tool_call>"


def _pretty_call(t: dict[str, Any], rng: random.Random) -> str:
    args = _arguments(t["schema"], rng)
    obj = {"name": t["name"], "arguments": args}
    return "<tool_call>\n" + json.dumps(obj, ensure_ascii=False, indent=2) + "\n</tool_call>"


def _openai_wrapper(t: dict[str, Any], rng: random.Random) -> str:
    args = _arguments(t["schema"], rng)
    obj = {"tool_calls": [{"id": f"call_{rng.randint(100000, 999999)}", "type": "function",
                           "function": {"name": t["name"],
                                        "arguments": json.dumps(args, ensure_ascii=False,
                                                                separators=(",", ":"))}}]}
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _schema_text(t: dict[str, Any]) -> str:
    obj = {"type": "function", "function": {"name": t["name"],
                                            "description": t["description"],
                                            "parameters": t["schema"]}}
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _result(t: dict[str, Any], rng: random.Random) -> str:
    if rng.random() < 0.5:
        obj: Any = {"ok": True, "id": f"R-{rng.randint(10000, 99999)}",
                    "status": rng.choice(STATUSES),
                    "data": _date(rng),
                    "kwota": _amount(rng),
                    "nazwa": rng.choice(COMPANIES)}
    else:
        obj = [{ "id": f"K-{rng.randint(1, 9999):04d}",
                 "nazwa": rng.choice(COMPANIES), "termin": _date(rng),
                 "kwota": _amount(rng), "aktywny": rng.choice([True, False])}
               for _ in range(rng.randint(1, 3))]
    return json.dumps(obj, ensure_ascii=False, indent=rng.choice([None, 2]))


def _heldout_value(kind: str, rng: random.Random) -> Any:
    if kind == "string":
        return rng.choice(["Z-8842/27", "wersja robocza", "kanał główny", "opis skrócony",
                           "zlecenie wewnętrzne", "format zwarty", "język polski"])
    if kind == "city":
        return rng.choice(HELDOUT_CITIES)
    if kind == "street":
        return rng.choice(["ul. Morska 14", "ul. Górska 3", "ul. Parkowa 27",
                           "ul. Portowa 8", "ul. Zielona 19"])
    if kind == "postal":
        return f"{rng.randint(10, 89):02d}-{rng.randint(100, 999):03d}"
    if kind == "date":
        return f"2027-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
    if kind == "amount":
        return f"{rng.randint(1000, 900000)},{rng.randint(0, 99):02d} PLN"
    if kind == "metric":
        return rng.choice(["czas", "koszt", "jakosc", "kompletnosc"])
    if kind == "mode":
        return rng.choice(["szybki", "pelny", "roboczy"])
    if kind == "language":
        return rng.choice(["polski", "angielski", "niemiecki"])
    if kind == "format":
        return rng.choice(["zwarty", "czytelny", "tabela"])
    if kind == "channel":
        return rng.choice(["email", "sms", "portal", "api"])
    if kind == "timezone":
        return rng.choice(["Europe/Warsaw", "UTC", "Europe/Berlin"])
    if kind == "owner":
        return rng.choice(["zespol_a", "zespol_b", "koordynator"])
    if kind == "source":
        return rng.choice(["bip", "api", "import", "formularz"])
    if kind == "text":
        return rng.choice(["krotki opis sprawy", "notatka robocza", "tresc do streszczenia"])
    if kind == "currency":
        return rng.choice(["PLN", "EUR", "USD", "CZK", "SEK"])
    if kind == "array_object":
        return [{"pozycja": rng.choice(["pozycja A", "pozycja B", "pozycja C"]),
                 "liczba": rng.randint(1, 9), "cena_netto": rng.randint(20, 900)}
                for _ in range(rng.randint(1, 3))]
    if kind == "array_string":
        return rng.sample(["zalacznik-1.pdf", "zalacznik-2.docx", "zalacznik-3.csv",
                           "zalacznik-4.txt"], rng.randint(1, 3))
    if kind == "integer":
        return rng.randint(10, 900)
    if kind == "number":
        return round(rng.uniform(0, 40), 1)
    if kind == "boolean":
        return rng.choice([True, False])
    if kind == "email":
        return rng.choice(["odbiorca@example.net", "zespol@example.org", "kontakt@example.edu"])
    if kind == "status":
        return rng.choice(["przyjety", "w realizacji", "zamkniety"])
    raise ValueError(kind)


def _heldout_specs(held_tools: list[dict[str, Any]], rng: random.Random) -> None:
    """Held-out: inne nazwy pól i wartości niż w treningu (ale ta sama gramatyka JSON)."""
    tmap = {"date": "string", "amount": "string", "array_object": "array",
            "array_string": "array", "email": "string", "status": "string",
            "integer": "integer", "number": "number", "boolean": "boolean",
            "currency": "string", "string": "string"}
    for t in held_tools:
        n = rng.randint(2, 5)
        chosen = rng.sample(HELDOUT_PROPERTIES, n)
        props: dict[str, Any] = {}
        for name, kind in chosen:
            spec: dict[str, Any] = {"type": tmap[kind],
                                    "description": "Pole zestawu held-out."}
            if kind == "date":
                spec["format"] = "date"
            elif kind == "email":
                spec["format"] = "email"
            elif kind == "array_object":
                spec["items"] = {"type": "object", "properties": {
                    "pozycja": {"type": "string"}, "liczba": {"type": "integer"},
                    "cena_netto": {"type": "number"}}}
            elif kind == "array_string":
                spec["items"] = {"type": "string"}
            props[name] = spec
        t["schema"] = {"type": "object", "properties": props,
                       "required": [chosen[0][0]], "additionalProperties": False}


def _heldout_example(t: dict[str, Any], rng: random.Random) -> tuple[str, str]:
    args = {}
    for name, spec in t["schema"]["properties"].items():
        kind = "string"
        ty = spec.get("type")
        if ty == "string":
            kind = "date" if spec.get("format") == "date" else (
                "email" if spec.get("format") == "email" else "string")
            if "waluta" in name:
                kind = "currency"
            elif "budzet" in name or "kwota" in name:
                kind = "amount"
            elif "data_" in name or name.startswith("znacznik"):
                kind = "date"
            elif "rabat" in name:
                kind = "number"
            elif "odbiorca" in name:
                kind = "email"
            elif name.startswith("miasto") or name == "lokalizacja":
                kind = "city"
            elif name.startswith("ulica"):
                kind = "street"
            elif name.startswith("kod_"):
                kind = "postal"
            elif name.startswith("status"):
                kind = "status"
            elif name == "metryka":
                kind = "metric"
            elif name == "tryb":
                kind = "mode"
            elif name == "jezyk":
                kind = "language"
            elif name == "format_wyniku":
                kind = "format"
            elif name == "kanal":
                kind = "channel"
            elif name == "strefa":
                kind = "timezone"
            elif name == "opiekun":
                kind = "owner"
            elif name == "zrodlo":
                kind = "source"
            elif name == "tresc_skrocona":
                kind = "text"
        elif ty == "array":
            kind = "array_object" if spec.get("items", {}).get("type") == "object" else "array_string"
        elif ty == "integer":
            kind = "integer"
        elif ty == "number":
            kind = "number"
        elif ty == "boolean":
            kind = "boolean"
        args[name] = _heldout_value(kind, rng)
    form = rng.choices(["compact", "pretty", "result"], weights=[50, 30, 20])[0]
    if form == "compact":
        return "<tool_call>" + json.dumps({"name": t["name"], "arguments": args},
                                          ensure_ascii=False, separators=(",", ":")) + "</tool_call>", form
    if form == "pretty":
        return "<tool_call>\n" + json.dumps({"name": t["name"], "arguments": args},
                                            ensure_ascii=False, indent=2) + "\n</tool_call>", form
    obj: Any = {"ok": True, "identyfikator": f"Z-{rng.randint(1000, 9999)}",
                "lokalizacja": rng.choice(HELDOUT_CITIES),
                "budzet_pln": f"{rng.randint(1000, 90000)} PLN",
                "tryb": rng.choice(["szybki", "pelny", "roboczy"]),
                "metryka": rng.choice(["czas", "koszt", "jakosc"])}
    return json.dumps(obj, ensure_ascii=False, indent=rng.choice([None, 2])), form


def _example(t: dict[str, Any], rng: random.Random) -> tuple[str, str]:
    form = rng.choices(["compact", "pretty", "openai", "schema", "result"],
                       weights=[40, 25, 15, 10, 10])[0]
    if form == "compact":
        return _compact_call(t, rng), form
    if form == "pretty":
        return _pretty_call(t, rng), form
    if form == "openai":
        return _openai_wrapper(t, rng), form
    if form == "schema":
        return _schema_text(t), form
    return _result(t, rng), form


def generuj(out_dir: str, train_examples: int = 50000) -> dict[str, Any]:
    rng = random.Random(SEED)
    rng_held = random.Random(SEED + 1)
    os.makedirs(out_dir, exist_ok=True)
    train_tools, held_tools = _tool_specs(rng)
    assert len(train_tools) == 40 and len(held_tools) == 10, (len(train_tools), len(held_tools))
    assert not ({t["name"] for t in train_tools} & {t["name"] for t in held_tools})

    # trening: równomiernie po 40 narzędziach, kolejność przemieszana
    texts = []
    for i in range(train_examples):
        t = train_tools[i % len(train_tools)]
        texts.append(_example(t, rng)[0])
    order = list(range(len(texts)))
    rng.shuffle(order)
    with open(os.path.join(out_dir, "json_train.txt"), "w", encoding="utf-8",
              newline="\n") as f:
        for i in order:
            f.write(texts[i].replace("\r\n", "\n").strip() + "\n\n")

    # held-out: 10 narzędzi x 20 przykładów = 100 dev + 100 test
    # (osobny RNG: zbiór held-out nie zależy od liczby przykładów treningowych)
    _heldout_specs(held_tools, rng_held)
    held_items = []
    for t in held_tools:
        for _ in range(20):
            text, form = _heldout_example(t, rng_held)
            held_items.append({"text": text, "tool": t["name"], "form": form})
    rng_held.shuffle(held_items)
    dev = held_items[:100]
    test = held_items[100:]
    for name, items in (("json_generic_heldout_dev.jsonl", dev),
                        ("json_generic_heldout_test.jsonl", test)):
        with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="\n") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False, separators=(",", ":")) + "\n")

    # manifest narzędzi (bez danych osobowych)
    manifest = {
        "seed": SEED,
        "train_tools": [t["name"] for t in train_tools],
        "heldout_tools": [t["name"] for t in held_tools],
        "train_examples": train_examples,
        "heldout_dev": len(dev), "heldout_test": len(test),
        "licencja": "dane syntetyczne wygenerowane lokalnie (nasze)",
    }
    with open(os.path.join(out_dir, "json_generic_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join("tkx_v21", "dane"))
    ap.add_argument("--train-examples", type=int, default=150000)
    a = ap.parse_args()
    m = generuj(a.out, a.train_examples)
    print(f"trening: {m['train_examples']} przykładów, narzędzia: {len(m['train_tools'])}")
    print(f"held-out: {m['heldout_dev']} dev + {m['heldout_test']} test, "
          f"narzedzia: {len(m['heldout_tools'])}")


if __name__ == "__main__":
    main()
