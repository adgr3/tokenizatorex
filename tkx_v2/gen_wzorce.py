import json
from collections import Counter

items = []
idx = 0
def add(cat, pat):
    global idx
    idx += 1
    contexts = [
        f"{pat} jest elementem dokumentu.",
        f"tekst {pat} tekst",
        f"({pat}) opis",
        f"slowo, {pat} slowo",
        f"jeden dwa {pat} trzy cztery",
    ]
    items.append({"id": f"W{idx:04d}", "category": cat, "pattern": pat, "contexts": contexts})

skroty = ["art. 12", "art. 12 ust. 3", "ust. 4 pkt 2", "pkt 3 lit. a", "poz. 1539",
          "Dz. U. 2026 poz. 1", "Dz.U. 2026 poz. 1", "M.P. 2026 poz. 5", "t.j. ustawy",
          "tj. rozporzadzenie", "ze zm.", "Pzp art. 96", "KPA art. 10", "k.c. art. 415",
          "art. 96 ust. 1 pkt 4", "ust. 2", "pkt 10", "lit. b", "poz. 100", "Dz. U. poz. 5"]
for p in skroty: add("skroty_prawne", p)

syg = ["KIO 1234/26", "KIO 89/25", "II SA/Wa 123/26", "II GSK 456/24", "I OSK 789/23",
       "KIO 1/26", "KIO 9999/26", "V SA/Wa 10/25", "III SA/Gd 44/24", "KIO 500/26"]
for p in syg: add("sygnatury", p)

ids = ["NIP 1234567890", "NIP: 9876543210", "REGON 123456789", "REGON 12345678901234",
       "KRS 0000123456", "KRS 0000987654", "NIP 5260250274", "REGON 012345678",
       "KRS 0000001234", "NIP 1111111111", "REGON 987654321", "KRS 0000555555",
       "NIP 2222222222", "REGON 111222333", "KRS 0000777777"]
for p in ids: add("identyfikatory", p)

kp = ["00-001", "35-001", "02-679", "80-123", "61-890", "15-001", "20-030", "40-001", "90-001", "05-090"]
for p in kp: add("kody_pocztowe", p)

bzp = ["2026/BZP 00514538", "2026/BZP 00000001", "2026/BZP 00123456", "2025/BZP 00999999",
       "2026/BZP 00432100", "2026/BZP 00777777", "2026/BZP 00111111", "2026/BZP 00222222",
       "2026/BZP 00333333", "2026/BZP 00444444"]
for p in bzp: add("numery_bzp", p)

for d in [1,2,15,25,31]:
    for m in ["stycznia","września","grudnia"]:
        add("daty_slowne", f"{d} {m} 2026 r.")
while len([i for i in items if i['category']=='daty_slowne']) < 15:
    add("daty_slowne", "25 września 2026 r.")

kwoty = ["1 234 567,89 zł", "1.234.567,89 PLN", "1234567.89", "45 000,00 zł", "1 000 000,00 PLN",
         "999,99 zł", "0,00 zł", "12 345,67 zł", "1.234,56 PLN", "500000.00",
         "3 456 789,01 zł", "7.654.321,00 PLN", "100,00 zł", "2 000 000,50 zł", "9.999,99 PLN"]
for p in kwoty: add("kwoty", p)

for d in ["2026-01-02","2026-09-25","2026-12-31"]:
    add("daty_iso", d)
    add("daty_iso", d.replace("-","."))
    dd,mm,yyyy = d.split("-")[2], d.split("-")[1], d.split("-")[0]
    add("daty_iso", f"{dd}.{mm}.{yyyy}")
    add("daty_iso", f"{dd}/{mm}/{yyyy}")
    add("daty_iso", f"{yyyy}/{mm}/{dd}")
# trim daty_iso to 15
iso_items = [i for i in items if i['category']=='daty_iso']
# remove excess
excess = len(iso_items) - 15
if excess > 0:
    # remove last excess items with category daty_iso
    removed = 0
    new_items = []
    for i in items:
        if i['category']=='daty_iso' and removed < excess:
            removed += 1
            continue
        new_items.append(i)
    items = new_items
    # reindex
    for k,it in enumerate(items,1):
        it['id'] = f"W{k:04d}"

cpv = ["45000000-7", "45233120-6", "33600000-6", "72000000-5", "90910000-9",
       "48000000-8", "50000000-5", "60000000-8", "70000000-1", "71000000-8",
       "73000000-2", "75000000-6", "79000000-4", "80000000-4", "85000000-9"]
for p in cpv: add("cpv", p)

jsons = [
  '<tool_call>{"name": "szukaj", "arguments": {"q": "przetarg"}}</tool_call>',
  '<tool_call>{"name": "pobierz", "arguments": {"id": "2026/BZP 00514538"}}</tool_call>',
  '<tool_call>{"name": "klasyfikuj_cpv", "arguments": {"tekst": "dostawa"}}</tool_call>',
  '{"kwota": "1 234,56 zł", "termin": "2026-01-02"}',
  '{"nip": "1234567890", "regon": "123456789"}',
  '<tool_call>{"name": "analizuj", "arguments": {"data": "2026-09-25"}}</tool_call>',
  '{"cpv": "45000000-7", "wartosc": "100000.00"}',
  '<tool_call>{"name": "sprawdz", "arguments": {"sygnatura": "KIO 1234/26"}}</tool_call>',
  '{"adres": "ul. Test 1, 00-001 Warszawa"}',
  '{"email": "a@b.pl", "www": "https://example.com"}',
]
for p in jsons: add("json_tool_calls", p)

adresy = ["https://www.gov.pl", "http://example.com/path", "user@example.com", "biuro@urzad.gov.pl",
          "https://ezamowienia.gov.pl", "kontakt@firma.pl", "www.test.pl", "https://api.sejm.gov.pl/eli",
          "info@grant.org.pl", "https://bip.gov.pl"]
for p in adresy: add("adresy", p)

firmy = ["Sp. z o.o.", "S.A.", "Fundacja Pomoc", "Stowarzyszenie Razem", "Zespół Szkół nr 1",
         "Urząd Miasta", "Gmina Warta", "Powiat Kielecki", "Województwo Śląskie", "NGO Grantos"]
for p in firmy: add("nazwy_firm", p)

while len(items) < 150:
    add(items[-1]["category"], items[-1]["pattern"])

# reindex
for k,it in enumerate(items,1):
    it['id'] = f"W{k:04d}"

print("total", len(items))
print(Counter(i["category"] for i in items))

with open("tkx_v2/wzorce.json","w",encoding="utf-8") as f:
    json.dump({"version":"1.0","seed":20261123,"count":len(items),"items":items}, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("written")
