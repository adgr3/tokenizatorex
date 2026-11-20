"""A2 dogledowo: regula grup V3 'po 3 cyfry od prawej'."""
import tokenizers as hf  # HF pierwszy
from tokenizers import Tokenizer
import json, pathlib, re, collections

REPO = pathlib.Path(__file__).resolve().parents[2]
HF = REPO / "hf" / "variants"
t3 = Tokenizer.from_file(str(HF / "V3-32k" / "tokenizer.json"))
vocab = json.loads((HF / "V3-32k" / "tokenizer.json").read_text(encoding="utf-8"))["model"]["vocab"]

# 1) jak wiele z wymuszonych grup faktycznie wychodzi jako jeden token
single2 = sum(len(t3.encode(f"{i:02d}", add_special_tokens=False).ids) == 1 for i in range(100))
single3 = sum(len(t3.encode(f"{i:03d}", add_special_tokens=False).ids) == 1 for i in range(1000))
single2s = sum(len(t3.encode(" " + f"{i:02d}", add_special_tokens=False).ids) == 2 for i in range(100))
single3s = sum(len(t3.encode(" " + f"{i:03d}", add_special_tokens=False).ids) == 2 for i in range(1000))

# 2) oczekiwany podzial 'grupy po 3 od prawej' dla ciagu cyfr
def expected_right_groups(s):
    """Podzial ciagu cyfr na grupy po 3 od prawej (lewy ogonek 1-2 cyfry)."""
    n = len(s)
    first = n % 3 or 3
    out = [s[:first]]
    for i in range(first, n, 3):
        out.append(s[i:i + 3])
    return out

EXAMPLES = [
    "2024", "2027", "45233140-2", "1 234 567,89", "0,125", "00-950",
    "ZP.271.12.2026", "20.11.2026", "Dz.U. z 2024 r. poz. 1320",
    "art. 275 pkt 1", "0012", "123456789012345", "COVID-19", "A4", "H2O",
]
violations = []
detail = {}
for s in EXAMPLES:
    runs = [m.group(0) for m in re.finditer(r"\d+", s)]
    exp = {r: expected_right_groups(r) for r in runs}
    enc = t3.encode(s, add_special_tokens=False)
    # cyfrowe kawalki (po usunieciu ewentualnego wiodacego 'Ġ')
    digit_pieces = [p[1:] if p.startswith("Ġ") else p for p in enc.tokens if re.search(r"\d", p)]
    # porownujemy konkatenacje cyfr w kawalkach z oczekiwanymi grupami
    got = []
    for p in enc.tokens:
        core = p[1:] if p.startswith("Ġ") else p
        if re.fullmatch(r"\d+", core):
            got.append(core)
    # got moze miec grupy rozne od oczekiwanych (np. 'Ġ2' + '024' -> '2','024')
    flat_exp = [g for r in runs for g in exp[r]]
    detail[s] = {"digit_runs": runs, "expected_groups": exp,
                 "actual_digit_pieces": digit_pieces,
                 "pieces": enc.tokens,
                 "matches_rule": got == flat_exp}
    if got != flat_exp:
        violations.append({"text": s, "expected": flat_exp, "actual": got,
                           "pieces": enc.tokens})

print("V3 single-token 2-digit:", single2, "/100 ; 3-digit:", single3, "/1000")
print("V3 with leading space (2 tokens = space+group):", single2s, "/100 ;", single3s, "/1000")
print("violations of '3 od prawej' among A2 examples:", len(violations))
for v in violations:
    print("  ", v["text"], "expected", v["expected"], "got", v["actual"], v["pieces"])

dest = REPO / "tkx_c" / "review_codex" / "results_codex.json"
r = json.loads(dest.read_text(encoding="utf-8"))
r["A2_groups3"] = {
    "single_token_2digit": single2, "single_token_3digit": single3,
    "single_token_space_2digit": single2s, "single_token_space_3digit": single3s,
    "example_details": detail, "violations": violations,
}
dest.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
print("updated", dest)
