"""Zestaw przypadków TESTU A — zwykły polski urzędowy + Unicode z PDF.

Wszystkie identyfikatory są ZMYŚLONE. NIP i PESEL mają poprawne sumy kontrolne
(liczone funkcjami poniżej), żeby tekst wyglądał jak prawdziwy zapis urzędowy.
"""
from __future__ import annotations

import unicodedata
from typing import Iterable


def _nip_check(body: str) -> str:
    w = (6, 5, 7, 2, 3, 4, 5, 6, 7)
    return str(sum(int(c) * x for c, x in zip(body, w)) % 11 % 10)


def _pesel_check(body: str) -> str:
    w = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
    return str((10 - sum(int(c) * x for c, x in zip(body, w)) % 10) % 10)


NIP9 = "123456321"
NIP = NIP9 + _nip_check(NIP9)
PESEL10 = "0021011234"
PESEL = PESEL10 + _pesel_check(PESEL10)


def cases() -> list[tuple[str, str, str]]:
    """(id, grupa, tekst) — min. 150 przypadków, każda grupa min. 10."""
    out: list[tuple[str, str, str]] = []

    def add(group: str, texts: Iterable[str], prefix: str) -> None:
        for i, t in enumerate(texts, 1):
            out.append((f"{prefix}-{i:02d}", group, t))

    # A2.1 — liczba + słowo zaczynające się jak jednostka (18 z zadania + 12)
    add("liczba+slowo", [
        "15 maja", "100 mln zł", "3 miesiące", "5 min", "2 mm", "10 km",
        "5 g", "20 l", "1 h", "12 m²", "3 mies.", "2 tys. zł", "7 dni",
        "30 grudnia", "4 lipca", "1 marca", "6 mld", "25 maja 2026 r.",
        "2 m", "3 cm", "8 kg", "40 ha", "1 szt.", "12 pc.", "500 tys.",
        "9 godz.", "6 lat", "11 osób", "20 mln euro", "14 dni roboczych",
    ], "LICZ")

    # A2.2 — daty i okresy (12 zapisów z formatów + 12)
    add("daty", [
        "2026.05.15", "2026-05-15", "15.05.2026", "5.05.2026",
        "15.05.2026 r.", "5.05.2026r.", "15/05/2026", "15 maja 2026 r.",
        "15 maja 2026r.", "z dnia 15 maja 2026 r.", "15 V 2026", "15.V.2026",
        "2024–2026", "2024-2026", "od 1.01 do 31.12.2026 r.",
        "I kwartał 2026", "XII 2025",
        "zgodnie z art. 2 ust. 1 pkt 3 w dniu 1 marca 2026 r.",
        "r. 2026", "2026 r.", "w 2026 r.", "od 2025 do 2026 r.",
        "do 31 grudnia 2026 r.", "1 stycznia 2025 r.",
    ], "DAT")

    # A2.3 — kwoty (9 zapisów z formatów + 11)
    add("kwoty", [
        "1 234,56 zł", "1234,56 zł", "1.234,56 zł", "1234.56 PLN",
        "1 234,56 PLN", "1 234 zł", "kwota brutto: 1 234,56 zł",
        "1,2 mln zł", "123 tys. zł",
        "1\u00a0234\u00a0567,89 zł", "1\u202f234\u202f567\u202f89 zł",
        "PLN 5 000", "5.000,00 zł", "5 000 000,00", "23%", "15 proc.",
        "wkład własny 10%", "0,50 zł", "12 345,67 euro", "49,99 gr",
    ], "KW")

    # A2.4 — przepisy i skróty (17 z zadania + 9)
    add("przepisy", [
        "§ 12 ust. 3 pkt 4 lit. a", "§§ 3–5", "art. 5a ust. 1 pkt 2",
        "Dz.U. z 2024 r. poz. 1320", "Dz. U.", "t.j.", "ze zm.", "m.in.",
        "tj.", "np.", "ok.", "nr", "poz.", "zał. nr 3", "rozdział IV",
        "Rozdział 2a", "§ 5", "§5", "w § 2", "zgodnie z § 14 ust. 1",
        "art. 5 § 2", "ust. 1 pkt 1 lit. b", "art. 21 ust. 1 i 2",
        "Dz.U. 2026 poz. 45", "§ 1–§ 9", "por. art. 7 ust. 3",
    ], "PRZ")

    # A2.5 — identyfikatory zmyślone ( summing valid NIP/PESEL )
    nip_dash = f"{NIP[:3]}-{NIP[3:6]}-{NIP[6:8]}-{NIP[8:]}"
    add("identyfikatory", [
        NIP, nip_dash, "1234567890", "0000123456", PESEL,
        "PL61 1090 1014 0000 0712 1981 2874", "+48 600 100 200",
        "00-950", "jan.kowalski@example.invalid", "https://example.invalid/ogl/123",
        "2026/BZP 00123456/01", "45000000-7", "REGON 123456789",
        "1/2026/BZP/00012345/01", "ul. Testowa 12/3, 00-001 Warszawa",
        "NIP " + nip_dash, "PESEL " + PESEL, "krs: 0000123456",
        "tel. +48 600 100 200", "e-mail: biuro@example.invalid",
        "PL61109010140000071219812874", "45100000-8",
    ], "ID")

    # A2.6 — superwordy wchodzące w środek słowa (znalezione w A1, 38/384 pary)
    add("superword", [
        "zgodność z", "zgodność z przepisami", "zgodność i", "kolejność z",
        "kolejność i", "informacja z", "informacja w", "informacja na",
        "kwota z", "kwota w", "wartość z", "wartość w", "liczba z",
        "suma z", "możliwość z", "odpowiedź do", "uchwała się", "ilość z",
        "zgoda na", "oferta z",
    ], "SUP")

    # A2.7 — wielkie litery i brak ogonków
    add("wielkie", [
        "OGŁOSZENIE O OTWARTYM KONKURSIE OFERT",
        "zrodla finansowania", "kwota 5000 zl", "WYNIKI POSTĘPOWANIA",
        "ZAPYTANIE OFERTOWE NR 12/2026", "LICZBA GŁOSÓW WAŻNYCH",
        "Załącznik nr 1 do uchwały", "SPRAWOZDANIE Z DZIAŁALNOŚCI",
        "zamowienie publiczne", "kwota 1234 zl 56 gr",
        "OCENA OFERT ZŁOŻONYCH", "PROTOKÓŁ Z POSIEDZENIA",
        "urzad skarbowy", "DECYZJA ADMINISTRACYJNA",
    ], "WIE")

    # A2.7 — łączniki, nazwy własne, zapożyczenia
    add("laczniki", [
        "biało-czerwony", "Kujawsko-Pomorskie", "Bielsko-Biała",
        "e-usługi", "online’owy", "ePUAP", "NGO-sów",
        "Warszawa-Śródmieście", "Polska-USA", "IX–XII 2026",
        "e-administracja", "e-zamówienia", "self-service",
        "AI-owy", "re-edycja", " mimochodem-małopolski",
    ], "LACZ")

    assert len(out) >= 150, len(out)
    assert min(len([c for c in out if c[1] == g]) for g in
               ("liczba+slowo", "daty", "kwoty", "przepisy",
                "identyfikatory", "superword", "wielkie", "laczniki")) >= 10
    # unikalność identyfikatorów
    assert len({c[0] for c in out}) == len(out)
    return out


def unicode_cases() -> list[tuple[str, str, str, str]]:
    """(id, grupa, tekst, wersja 'czysta' do porównania)"""
    zrodlo_nfc = "źródło"
    return [
        ("UNI-01", "NFC/NFD", zrodlo_nfc, zrodlo_nfc),
        ("UNI-02", "NFC/NFD", unicodedata.normalize("NFD", zrodlo_nfc), zrodlo_nfc),
        ("UNI-03", "NFC/NFD", "złożenie", "złożenie"),
        ("UNI-04", "NFC/NFD", unicodedata.normalize("NFD", "złożenie"), "złożenie"),
        ("UNI-05", "białe", "1\u00a0234\u00a0567,89 zł", "1 234 567,89 zł"),
        ("UNI-06", "białe", "1\u202f234\u202f567,89 zł", "1 234 567,89 zł"),
        ("UNI-07", "białe", "ala\u00admakota", "alamakota"),
        ("UNI-08", "białe", "ala\u200bmakota", "alamakota"),
        ("UNI-09", "białe", "\ufeffPodpisano", "Podpisano"),
        ("UNI-10", "białe", "a\r\nb", "a\nb"),
        ("UNI-11", "białe", "a\nb", "a\nb"),
        ("UNI-12", "białe", "a\t\tb", "a b"),
        ("UNI-13", "białe", "wiele   spacji   w   tekście", "wiele spacji w tekście"),
        ("UNI-14", "interpunkcja", "„cytat” i «z»", '"cytat" i "z"'),
        ("UNI-15", "interpunkcja", "’apostrof’ ' \"", "'apostrof' ' \""),
        ("UNI-16", "interpunkcja", "półpauza – i pauza — oraz …", "półpauza - i pauza - oraz ..."),
        ("UNI-17", "ligatury", "ﬁ ﬂ ﬀ ligatury", "fi fl ff ligatury"),
        ("UNI-18", "sobowtóry", "piaстka złożeние", "piastka zlozenie"),
        ("UNI-19", "emoji", "Podpisano ✅ 📄 🎉", "Podpisano"),
        ("UNI-20", "poza BMP", "Znak 𝔘 i 𐐷", "Znak U i"),
        ("UNI-21", "mojibake", "Å¼ Ä… Å›", "ż ę ś"),
        ("UNI-22", "mojibake", "Å‚aÅ›Ä‡", "ziałaść"),
        ("UNI-23", "NFC/NFD", unicodedata.normalize("NFD", "król Michał"), "król Michał"),
        ("UNI-24", "emoji", " Kwota 123 zł 💶", "Kwota 123 zł"),
    ]
