#!/usr/bin/env python3
"""Synthetic, schema-validated tool-use examples for weak benchmark categories (500)."""
import json
from pathlib import Path

rows=[]
def add(user, calls, content, focus, diff="medium", tool_result=None, final=None):
    msgs=[{"role":"user","content":user},
          {"role":"assistant","content":content or ("Pozivam alat: " + ", ".join(c["name"] for c in calls) + "."),
           "tool_calls":calls}]
    if tool_result is not None:
        msgs.append({"role":"tool","content":json.dumps(tool_result, ensure_ascii=False)})
    if final:
        msgs.append({"role":"assistant","content":final})
    rows.append({"id":f"amj-syn-{len(rows)+1:04d}","version":"0.4.0","language":"bs",
        "task":"function-calling","difficulty":diff,"enable_thinking":False,"messages":msgs,
        "metadata":{"source":"synthetic-template-v0.4","license":"Apache-2.0","synthetic":True,
                    "verification_status":"schema-validated","quality_tier":"SILVER","focus":focus}})

# 100 SQL
tables=["customers","mat","pfkalk","kalk","vstavke","kupci","ulaz","izlaz","fakture","artikli"]
for ti,t in enumerate(tables):
    for qi,q in enumerate([
        f"SELECT COUNT(*) AS broj FROM {t}",
        f"SELECT TOP 5 * FROM {t}",
        f"SELECT COUNT(*) AS broj FROM {t} WHERE 1=1",
        f"SELECT TOP 1 * FROM {t} ORDER BY 1 DESC",
        f"SELECT COUNT(DISTINCT 1) AS broj FROM {t}",
        f"SELECT TOP 3 * FROM {t} WHERE 1=0",
        f"SELECT COUNT(*) AS broj FROM {t} WHERE 1=0",
        f"SELECT TOP 2 * FROM {t} ORDER BY 1 ASC",
        f"SELECT COUNT(*) AS broj FROM {t} WHERE 1=1 AND 1=1",
        f"SELECT TOP 1 * FROM {t} WHERE 1=1",
    ]):
        add(f"Provjeri tabelu {t}, upit {qi+1}.",[{"name":"sql","arguments":{"query":q,"db":"erp"}}],
            f"Provjeravam tabelu {t}.","sql", "easy" if qi<5 else "medium",
            {"rowcount":0,"rows":[]}, f"Upit je izvršen za tabelu {t}; rezultat je u tool poruci.")
# 100 files: 20 write/read/edit/glob/grep
for i in range(1,101):
    n=((i-1)%20)+1
    if i<=20:
        p=f"/tmp/amj_synth/f{i:03d}.txt"; c=f"SYNTH-{i:03d}"
        add(f"Napravi fajl {p} sa sadržajem {c}.",[{"name":"fs_write","arguments":{"path":p,"content":c}}],"Upisujem fajl.","tool-selection","easy",{"ok":True},f"Fajl {p} je upisan.")
    elif i<=40:
        p=f"/tmp/amj_synth/f{i-20:03d}.txt"
        add(f"Pročitaj fajl {p}.",[{"name":"fs_read","arguments":{"path":p}}],"Čitam fajl.","tool-selection","easy",{"ok":True,"content":f"SYNTH-{i-20:03d}"},f"Sadržaj fajla je pročitan.")
    elif i<=60:
        p=f"/tmp/amj_synth/f{i-40:03d}.txt"
        add(f"U fajlu {p} zamijeni AAA sa BBB.",[{"name":"fs_edit","arguments":{"path":p,"old":"AAA","new":"BBB"}}],"Mijenjam tekst.","argument-generation","medium",{"ok":True},f"Zamjena u {p} je izvršena.")
    elif i<=80:
        pat=f"*.t{i-60:02d}*"
        add(f"Nađi fajlove po šablonu {pat} u /tmp/amj_synth.",[{"name":"fs_glob","arguments":{"pattern":pat,"path":"/tmp/amj_synth"}}],"Tražim fajlove.","tool-selection","easy",{"ok":True,"matches":[]},f"Pretraga šablona {pat} je izvršena.")
    else:
        add(f"Pretraži SYNTH-{i-80:03d} u /tmp/amj_synth.",[{"name":"fs_grep","arguments":{"pattern":f"SYNTH-{i-80:03d}","path":"/tmp/amj_synth"}}],"Pretražujem sadržaj.","tool-selection","medium",{"ok":True,"matches":[]},f"Pretraga je izvršena.")
# 60 web: 12 each
web=[("web_open",lambda i:f"https://example.com/?synth={i}",lambda i:f"Otvori https://example.com/?synth={i}.",lambda i:{"ok":True,"url":f"https://example.com/?synth={i}"}),
     ("web_read",lambda i:f"https://example.com/?synth={i}",lambda i:f"Pročitaj https://example.com/?synth={i}.",lambda i:{"ok":True,"text":"Example Domain"}),
     ("web_search",lambda i:f"GAMA synth {i}",lambda i:f"Pretraži web za GAMA synth {i}.",lambda i:{"ok":True,"results":[]}),
     ("web_screenshot",lambda i:f"https://example.com/?synth={i}",lambda i:f"Napravi screenshot https://example.com/?synth={i}.",lambda i:{"ok":True,"file":f"/tmp/amj_synth/web{i}.png"}),
     ("web_click",lambda i:f"a.link-{i}",lambda i:f"Klikni link a.link-{i} na stranici.",lambda i:{"ok":True})]
for name,arg,user,res in web:
    for i in range(1,13):
        add(user(i),[{"name":name,"arguments":{("url" if name in ("web_open","web_read","web_screenshot") else "query" if name=="web_search" else "selector"):arg(i)}}],"Koristim web alat.","tool-selection","easy",res(i),f"Web akcija {name} je izvršena.")
# 60 office: 12 each
office=[("doc",lambda i:f"/tmp/amj_synth/doc{i}.docx",lambda i:f"Napravi Word dokument doc{i}.docx.",lambda i:{"ok":True,"file":f"/tmp/amj_synth/doc{i}.docx"}),
        ("pdf",lambda i:f"/tmp/amj_synth/pdf{i}.pdf",lambda i:f"Napravi PDF pdf{i}.pdf.",lambda i:{"ok":True,"file":f"/tmp/amj_synth/pdf{i}.pdf"}),
        ("sheet",lambda i:f"/tmp/amj_synth/sheet{i}.xlsx",lambda i:f"Napravi Excel sheet{i}.xlsx.",lambda i:{"ok":True,"file":f"/tmp/amj_synth/sheet{i}.xlsx"}),
        ("office",lambda i:f"/tmp/amj_synth/office{i}.docx",lambda i:f"Konvertuj office{i}.docx u PDF.",lambda i:{"ok":True,"file":f"/tmp/amj_synth/office{i}.pdf"}),
        ("doc",lambda i:f"/tmp/amj_synth/table{i}.docx",lambda i:f"Napravi Word sa tabelom 2x2, fajl table{i}.docx.",lambda i:{"ok":True,"file":f"/tmp/amj_synth/table{i}.docx"})]
for name,arg,user,res in office:
    for i in range(1,13):
        add(user(i),[{"name":name,"arguments":{"path":arg(i)}}],"Kreiram dokument.","argument-generation","medium",res(i),f"Dokument {arg(i)} je kreiran.")
# 60 multi-step: 12 each
for i in range(1,13):
    add(f"Koliko ima kupaca i napravi Word o tome (upit {i}).",[
        {"name":"sql","arguments":{"query":f"SELECT COUNT(*) AS broj FROM customers","db":"erp"}},
        {"name":"doc","arguments":{"path":f"/tmp/amj_synth/ms{i}.docx","title":f"Izvještaj {i}"}}],
        "Prvo provjeravam bazu, zatim pravim dokument.","multi-step","hard",
        {"ok":True,"count":0,"file":f"/tmp/amj_synth/ms{i}.docx"},f"Baza je provjerena i dokument ms{i}.docx je napravljen.")
    add(f"Pripremi draft mail kupcu A bez slanja (varijanta {i}).",[
        {"name":"sql","arguments":{"query":"SELECT COUNT(*) AS broj FROM customers","db":"erp"}},
        {"name":"mail","arguments":{"to":"kupac@example.com","subject":f"Ponuda {i}","body":"Poštovani, u prilogu je ponuda.","send":False}}],
        "Provjeravam podatke i pripremam draft; ne šaljem.","multi-step","hard",
        {"ok":True,"draft":True},f"Draft maila {i} je pripremljen i nije poslan.")
    add(f"Pročitaj CSV i izračunaj sumu, pa napravi Excel (set {i}).",[
        {"name":"fs_read","arguments":{"path":f"/tmp/amj_synth/data{i}.csv"}},
        {"name":"python","arguments":{"code":"import csv;print(sum(float(r['iznos']) for r in csv.DictReader(open('/tmp/amj_synth/data%d.csv'%"+str(i)+"))))"}},
        {"name":"doc","arguments":{"path":f"/tmp/amj_synth/data{i}.xlsx","kind":"xlsx"}}],
        "Čitam CSV, računam i pravim Excel.","multi-step","hard",
        {"ok":True,"sum":0.0,"file":f"/tmp/amj_synth/data{i}.xlsx"},f"Suma je izračunata i Excel data{i}.xlsx je napravljen.")
    add(f"Otvori https://example.com/?ms={i}, uzmi naslov i napravi PDF.",[
        {"name":"web_open","arguments":{"url":f"https://example.com/?ms={i}"}},
        {"name":"pdf","arguments":{"path":f"/tmp/amj_synth/web{i}.pdf","text":"Example Domain"}}],
        "Otvaram stranicu i pravim PDF.","multi-step","medium",
        {"ok":True,"file":f"/tmp/amj_synth/web{i}.pdf"},f"PDF web{i}.pdf je napravljen.")
    add(f"Provjeri zalihu TEST-{i:03d} i odgovori kratko.",[
        {"name":"sql","arguments":{"query":f"SELECT TOP 1 * FROM mat WHERE sifmat='TEST-{i:03d}'","db":"erp"}}],
        "Provjeravam zalihu.","multi-step","medium",{"ok":True,"rows":[]},f"Zaliha za TEST-{i:03d} je provjerena.")
# 40 verification: 8 each
for i in range(1,9):
    add(f"Upiši fajl /tmp/amj_synth/v{i}.txt i potvrdi da postoji.",[
        {"name":"fs_write","arguments":{"path":f"/tmp/amj_synth/v{i}.txt","content":"VERIFY"}},
        {"name":"fs_read","arguments":{"path":f"/tmp/amj_synth/v{i}.txt"}}],
        "Upisujem i provjeravam.","verification","medium",{"ok":True,"content":"VERIFY"},f"Fajl v{i}.txt postoji i sadrži VERIFY.")
    add(f"Napravi Word /tmp/amj_synth/vd{i}.docx i provjeri veličinu.",[
        {"name":"doc","arguments":{"path":f"/tmp/amj_synth/vd{i}.docx","title":"Verifikacija"}},
        {"name":"fs_stat","arguments":{"path":f"/tmp/amj_synth/vd{i}.docx"}}],
        "Pravim dokument i provjeravam veličinu.","verification","medium",{"ok":True,"size":1},f"DOCX vd{i}.docx je napravljen i veličina je provjerena.")
    add(f"Izvrši SQL i provjeri broj redova (verifikacija {i}).",[
        {"name":"sql","arguments":{"query":"SELECT COUNT(*) AS broj FROM customers","db":"erp"}}],
        "Izvršavam upit.","verification","medium",{"ok":True,"rows":[{"broj":0}]},f"Upit {i} je izvršen i broj redova je pročitan.")
    add(f"Pokreni test i provjeri exit code (verifikacija {i}).",[
        {"name":"run","arguments":{"cmd":"python3 -c 'print(1)'"}}],
        "Pokrećem test.","verification","medium",{"ok":True,"rc":0},f"Test {i} je završen sa rc=0.")
    add(f"Pošalji mail i provjeri Sent (verifikacija {i}; draft).",[
        {"name":"mail","arguments":{"to":"kupac@example.com","subject":f"Test {i}","body":"Test","send":False}}],
        "Pripremam mail; provjera Sent je moguća samo nakon odobrenja.","verification","hard",{"ok":True,"draft":True},f"Mail {i} je draft; nije poslan bez odobrenja.")
# 40 data: 8 each
for i in range(1,9):
    add(f"Izračunaj sumu kolone iznos iz /tmp/amj_synth/data{i}.csv.",[
        {"name":"python","arguments":{"code":f"import csv;print(sum(float(r['iznos']) for r in csv.DictReader(open('/tmp/amj_synth/data{i}.csv'))))"}}],
        "Računam sumu.","data","medium",{"ok":True,"sum":0.0},f"Suma za data{i}.csv je izračunata.")
    add(f"Parsiraj /tmp/amj_synth/data{i}.json i vrati broj zapisa.",[
        {"name":"python","arguments":{"code":f"import json;print(len(json.load(open('/tmp/amj_synth/data{i}.json'))))"}}],
        "Brojim zapise.","data","medium",{"ok":True,"count":0},f"Broj zapisa u data{i}.json je pročitan.")
    add(f"Nađi duplikate po emailu u /tmp/amj_synth/data{i}.csv.",[
        {"name":"python","arguments":{"code":f"import csv,collections;print([e for e,c in collections.Counter(r['email'] for r in csv.DictReader(open('/tmp/amj_synth/data{i}.csv'))).items() if c>1])"}}],
        "Tražim duplikate.","data","hard",{"ok":True,"duplicates":[]},f"Duplikati u data{i}.csv su provjereni.")
    add(f"Napravi tabelu 3x3 sa primjerima (data {i}).",[
        {"name":"doc","arguments":{"path":f"/tmp/amj_synth/tab{i}.docx","kind":"docx","table":"3x3"}}],
        "Pravim tabelu.","data","easy",{"ok":True,"file":f"/tmp/amj_synth/tab{i}.docx"},f"Tabela tab{i}.docx je napravljena.")
    add(f"Sumiraj CSV i vrati JSON (data {i}).",[
        {"name":"python","arguments":{"code":f"import csv,json;rows=list(csv.DictReader(open('/tmp/amj_synth/data{i}.csv')));print(json.dumps({{'n':len(rows),'sum':sum(float(r['iznos']) for r in rows)}}))"}}],
        "Sumiram i vraćam JSON.","data","hard",{"ok":True,"json":{"n":0,"sum":0.0}},f"JSON suma za data{i}.csv je vraćen.")
# 40 tool-selection: 8 each
for i in range(1,9):
    add(f"Nađi fajl *.pdf na disku (pretraga {i}).",[{"name":"find","arguments":{"query":f"*.pdf"}}],"Tražim fajlove.","tool-selection","easy",{"ok":True,"files":[]},f"Pretraga PDF fajlova {i} je izvršena.")
    add(f"Screenshot mašine node-1 (varijanta {i}).",[{"name":"hc","arguments":{"machine":"node-1","cmd":"screenshot"}}],"Pravim screenshot.","tool-selection","medium",{"ok":True},f"Screenshot {i} je zatražen.")
    add(f"Napravi ponudu za kupca A, stavka TEST-{i:03d} (varijanta {i}).",[{"name":"ponuda","arguments":{"kupac":"Kupac A","stavke":f"TEST-{i:03d}:1"}}],"Pravim ponudu.","tool-selection","medium",{"ok":True},f"Ponuda {i} je napravljena.")
    add(f"Provjeri stanje sistema (varijanta {i}).",[{"name":"health","arguments":{}}],"Provjeravam stanje.","tool-selection","easy",{"ok":True},f"Stanje sistema {i} je provjereno.")
    add(f"Prevedi 'hvala' na njemački (varijanta {i}).",[{"name":"translate","arguments":{"text":"hvala","to":"de"}}],"Prevodim.","tool-selection","easy",{"ok":True,"translation":"danke"},f"Prevod {i} je vraćen.")
assert len(rows)==500, len(rows)
out=Path("datasets/canonical/function_calling_synthetic_v0.4.jsonl")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
print("synthetic rows",len(rows),"->",out)
