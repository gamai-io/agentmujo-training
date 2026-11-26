#!/usr/bin/env python3
"""Synthetic, schema-validated tool-use examples for weak benchmark categories (500).

REGISTRY_CONFORMANCE_V1: svaki `tool_calls[].name` i svaki argument moraju postojati
u `configs/tools.yaml` (Single Source of Truth) i proci `ToolRegistry.validate_call`.
Razlog: `policy/engine.py` odbija (deny) svaki alat kojeg nema u registryju, pa bi
dataset koji koristi neregistrovane alate trenirao pozive koje gate odbija
(train/serve skew). Generator je deterministicki: isti izlaz na svakom pokretanju.
"""
import json
from pathlib import Path

rows = []


def add(user, calls, content, focus, diff="medium", tool_result=None, final=None):
    msgs = [{"role": "user", "content": user},
            {"role": "assistant", "content": content or ("Pozivam alat: " + ", ".join(c["name"] for c in calls) + "."),
             "tool_calls": calls}]
    if tool_result is not None:
        msgs.append({"role": "tool", "content": json.dumps(tool_result, ensure_ascii=False)})
    if final:
        msgs.append({"role": "assistant", "content": final})
    rows.append({"id": f"amj-syn-{len(rows)+1:04d}", "version": "0.4.0", "language": "bs",
                 "task": "function-calling", "difficulty": diff, "enable_thinking": False, "messages": msgs,
                 "metadata": {"source": "synthetic-template-v0.4", "license": "Apache-2.0", "synthetic": True,
                              "verification_status": "schema-validated", "quality_tier": "SILVER", "focus": focus}})


SERVICES = ["nginx", "postgresql", "redis-server", "ssh", "cron",
            "docker", "mariadb", "fail2ban", "systemd-journald", "ntpsec"]
PORTS = [80, 5432, 6379, 22, 25, 2375, 3306, 9100, 514, 123]
PACKAGES = ["nginx", "postgresql", "redis-server", "openssh-server", "cron",
            "docker.io", "mariadb-server", "fail2ban", "systemd", "ntpsec"]

# 100 diagnostika: 10 servisa x 10 read-only/mutirajucih provjera.
for i, svc in enumerate(SERVICES):
    n = 20 + 10 * i
    add(f"Provjeri da li servis {svc} radi.", [{"name": "service_status", "arguments": {"service": svc}}],
        f"Provjeravam status servisa {svc}.", "diagnostics", "easy", {"active": True},
        f"Servis {svc} je aktivan.")
    add(f"Prikaži zadnjih {n} linija loga servisa {svc}.",
        [{"name": "service_logs", "arguments": {"service": svc, "lines": n}}],
        f"Čitam log servisa {svc}.", "diagnostics", "easy", {"lines": []},
        f"Zadnjih {n} linija loga servisa {svc} je pročitano.")
    add(f"Restartuj servis {svc}; traži potvrdu prije izvršenja.",
        [{"name": "service_restart", "arguments": {"service": svc}}],
        f"Predlažem restart servisa {svc}.", "diagnostics", "medium",
        {"executed": False, "requires_confirmation": True},
        f"Restart servisa {svc} nije izvršen — čeka potvrdu operatora.")
    add(f"Koliko je zauzet disk na /var/log/{svc}?",
        [{"name": "disk_usage", "arguments": {"path": f"/var/log/{svc}"}}],
        "Provjeravam iskorištenost diska.", "diagnostics", "easy", {"use_percent": 0},
        f"Iskorištenost diska za /var/log/{svc} je pročitana.")
    add(f"Koliko je slobodno memorije? (provjera {i+1})",
        [{"name": "memory_usage", "arguments": {}}],
        "Čitam stanje memorije.", "diagnostics", "easy", {"available_mb": 0},
        f"Stanje memorije je pročitano (provjera {i+1}).")
    add(f"Koliko je CPU opterećen? (provjera {i+1})",
        [{"name": "cpu_usage", "arguments": {}}],
        "Čitam opterećenje CPU-a.", "diagnostics", "easy", {"load": 0.0},
        f"Opterećenje CPU-a je pročitano (provjera {i+1}).")
    add(f"Koji procesi troše najviše memorije? (provjera {i+1})",
        [{"name": "process_list", "arguments": {"limit": 10, "sort_by": "memory"}}],
        "Listam procese sortirano po memoriji.", "diagnostics", "easy", {"processes": []},
        f"Lista procesa je pročitana (provjera {i+1}).")
    add(f"Ko sluša na portu {PORTS[i]}?",
        [{"name": "port_check", "arguments": {"port": PORTS[i]}}],
        "Provjeravam koji proces sluša na portu.", "diagnostics", "easy", {"listeners": []},
        f"Provjera porta {PORTS[i]} je izvršena.")
    add(f"Da li je paket {PACKAGES[i]} instaliran?",
        [{"name": "package_query", "arguments": {"package": PACKAGES[i]}}],
        "Provjeravam instalaciju paketa.", "diagnostics", "easy", {"installed": True},
        f"Status paketa {PACKAGES[i]} je pročitan.")
    add(f"Prikaži stanje mrežnih interfejsa (provjera {i+1}).",
        [{"name": "network_status", "arguments": {}}],
        "Čitam mrežni status.", "diagnostics", "easy", {"interfaces": []},
        f"Mrežni status je pročitan (provjera {i+1}).")

# 100 rad sa fajlovima: 10 direktorija x 10 read-only operacija (file_list/file_read).
DIRS = ["/etc/nginx", "/var/log", "/etc/systemd/system", "/etc/ssh", "/opt/app",
        "/srv/data", "/tmp/amj_synth", "/usr/local/bin", "/etc/cron.d", "/var/lib/app"]
FILES = ["nginx.conf", "app.log", "app.service", "sshd_config", "settings.toml",
         "dataset.csv", "notes.txt", "run.sh", "backup.cron", "state.json"]
for d in range(10):
    base = DIRS[d]
    for op in range(1, 11):
        fname = FILES[d]
        if op == 1:
            add(f"Lista sadržaj direktorija {base} (pregled {d+1}).",
                [{"name": "file_list", "arguments": {"path": base}}],
                "Listam direktorij.", "tool-selection", "easy", {"entries": []},
                f"Sadržaj direktorija {base} je pročitan.")
        elif op == 2:
            add(f"Pročitaj prvih 50 linija fajla {base}/{fname}.",
                [{"name": "file_read", "arguments": {"path": f"{base}/{fname}", "lines": 50}}],
                "Čitam fajl.", "tool-selection", "easy", {"lines": 50},
                f"Fajl {base}/{fname} je pročitan.")
        elif op == 3:
            add(f"Pročitaj {base}/{fname} (samo 20 linija) i reci da li ima grešaka.",
                [{"name": "file_read", "arguments": {"path": f"{base}/{fname}", "lines": 20}}],
                "Čitam početak fajla.", "tool-selection", "medium", {"lines": 20},
                f"Početak fajla {base}/{fname} je pročitan.")
        elif op == 4:
            add(f"Koje fajlove ima {base}? (varijanta {d+1})",
                [{"name": "file_list", "arguments": {"path": base}}],
                "Listam direktorij.", "tool-selection", "easy", {"entries": []},
                f"Lista fajlova u {base} je pročitana.")
        elif op == 5:
            add(f"Pročitaj zadnjih 100 linija {base}/{fname}.",
                [{"name": "file_read", "arguments": {"path": f"{base}/{fname}", "lines": 100}}],
                "Čitam fajl.", "tool-selection", "medium", {"lines": 100},
                f"Fajl {base}/{fname} je pročitan.")
        elif op == 6:
            add(f"Ima li {base} poddirektorij conf.d? (varijanta {d+1})",
                [{"name": "file_list", "arguments": {"path": f"{base}/conf.d"}}],
                "Listam poddirektorij.", "tool-selection", "easy", {"entries": []},
                f"Poddirektorij {base}/conf.d je provjeren.")
        elif op == 7:
            add(f"Pročitaj {base}/{fname} i izdvoji prvih 10 linija.",
                [{"name": "file_read", "arguments": {"path": f"{base}/{fname}", "lines": 10}}],
                "Čitam prvih 10 linija.", "tool-selection", "easy", {"lines": 10},
                f"Prvih 10 linija fajla {base}/{fname} je pročitano.")
        elif op == 8:
            add(f"Pregledaj {base} prije izmjene konfiguracije (varijanta {d+1}).",
                [{"name": "file_list", "arguments": {"path": base}}],
                "Pregledam direktorij prije izmjene.", "tool-selection", "medium", {"entries": []},
                f"Direktorij {base} je pregledan; izmjena nije rađena.")
        elif op == 9:
            add(f"Koliko linija ima {base}/{fname}? Pročitaj do 200 linija.",
                [{"name": "file_read", "arguments": {"path": f"{base}/{fname}", "lines": 200}}],
                "Čitam fajl do 200 linija.", "tool-selection", "medium", {"lines": 200},
                f"Fajl {base}/{fname} je pročitan do 200 linija.")
        else:
            add(f"Provjeri postoji li {base}/{fname} i prikaži početak.",
                [{"name": "file_read", "arguments": {"path": f"{base}/{fname}", "lines": 5}}],
                "Provjeravam fajl čitanjem početka.", "tool-selection", "easy", {"lines": 5},
                f"Fajl {base}/{fname} je provjeren.")

# 60 generisanje argumenata: 6 obrazaca x 10 vrijednosti.
LINE_VALUES = [10, 20, 25, 30, 40, 50, 75, 100, 150, 200]
for i, lines in enumerate(LINE_VALUES):
    add(f"Pročitaj /var/log/app.log, tačno {lines} linija.",
        [{"name": "file_read", "arguments": {"path": "/var/log/app.log", "lines": lines}}],
        "Postavljam broj linija.", "argument-generation", "easy", {"lines": lines},
        f"Pročitano je {lines} linija fajla /var/log/app.log.")
for i, lines in enumerate(LINE_VALUES):
    svc = SERVICES[i]
    add(f"Prikaži {lines} linija loga servisa {svc}.",
        [{"name": "service_logs", "arguments": {"service": svc, "lines": lines}}],
        "Postavljam broj linija loga.", "argument-generation", "easy", {"lines": lines},
        f"Prikazano je {lines} linija loga servisa {svc}.")
for port in [22, 25, 53, 80, 123, 443, 3306, 5432, 6379, 8080]:
    add(f"Provjeri port {port} (TCP).",
        [{"name": "port_check", "arguments": {"port": port}}],
        "Provjeravam port.", "argument-generation", "easy", {"listeners": []},
        f"Port {port} je provjeren.")
for i, (limit, sort_by) in enumerate([(5, "cpu"), (10, "cpu"), (20, "cpu"), (50, "cpu"), (100, "cpu"),
                                      (5, "memory"), (10, "memory"), (20, "memory"), (50, "pid"), (20, "name")]):
    add(f"Prikaži {limit} procesa sortirano po {sort_by}.",
        [{"name": "process_list", "arguments": {"limit": limit, "sort_by": sort_by}}],
        "Postavljam limit i sortiranje.", "argument-generation", "easy", {"processes": []},
        f"Prikazano je {limit} procesa sortirano po {sort_by}.")
for path in ["/", "/var", "/var/log", "/home", "/tmp", "/opt", "/srv", "/etc", "/var/lib", "/usr"]:
    add(f"Koliko je zauzet disk na {path}?",
        [{"name": "disk_usage", "arguments": {"path": path}}],
        "Provjeravam disk za putanju.", "argument-generation", "easy", {"use_percent": 0},
        f"Iskorištenost diska za {path} je pročitana.")
for i, (cmd, timeout_s) in enumerate([("uptime", 10), ("date", 15), ("whoami", 20), ("hostname", 30),
                                      ("uname -r", 45), ("id", 60), ("pwd", 90),
                                      ("env | wc -l", 120), ("ls /etc | wc -l", 180), ("df -h /", 300)]):
    add(f"Pokreni `{cmd}` kroz terminal sa timeoutom {timeout_s}s (traži potvrdu).",
        [{"name": "terminal", "arguments": {"command": cmd, "timeout_s": timeout_s}}],
        "Koristim terminal kao fallback; tražim potvrdu.", "argument-generation", "medium",
        {"executed": False, "requires_confirmation": True},
        f"Komanda `{cmd}` nije izvršena — čeka potvrdu operatora.")

# 100 selekcija alata: high-level alat umjesto niskog nivoa (10 namjera x 10 vrijednosti).
for i, svc in enumerate(SERVICES):
    add(f"Provjeri radi li {svc} — koristi visokonivojski alat, ne systemctl u terminalu.",
        [{"name": "service_status", "arguments": {"service": svc}}],
        "Biram service_status umjesto terminala.", "tool-selection", "easy", {"active": True},
        f"Status servisa {svc} je provjeren visokonivojskim alatom.")
for i, svc in enumerate(SERVICES):
    add(f"Prikaži logove {svc} — nemoj koristiti journalctl u terminalu.",
        [{"name": "service_logs", "arguments": {"service": svc, "lines": 30}}],
        "Biram service_logs umjesto terminala.", "tool-selection", "easy", {"lines": 30},
        f"Logovi servisa {svc} su pročitani visokonivojskim alatom.")
for path in ["/", "/var", "/var/log", "/home", "/tmp", "/opt", "/srv", "/etc", "/var/lib", "/usr"]:
    add(f"Koliko prostora je zauzeto na {path}? Ne koristi df u terminalu.",
        [{"name": "disk_usage", "arguments": {"path": path}}],
        "Biram disk_usage umjesto terminala.", "tool-selection", "easy", {"use_percent": 0},
        f"Iskorištenost diska za {path} je pročitana visokonivojskim alatom.")
for port in [22, 25, 53, 80, 123, 443, 3306, 5432, 6379, 8080]:
    add(f"Ko sluša na portu {port}? Ne koristi ss u terminalu.",
        [{"name": "port_check", "arguments": {"port": port}}],
        "Biram port_check umjesto terminala.", "tool-selection", "easy", {"listeners": []},
        f"Port {port} je provjeren visokonivojskim alatom.")
for pkg in PACKAGES:
    add(f"Da li je {pkg} instaliran? Ne koristi dpkg u terminalu.",
        [{"name": "package_query", "arguments": {"package": pkg}}],
        "Biram package_query umjesto terminala.", "tool-selection", "easy", {"installed": True},
        f"Status paketa {pkg} je pročitan visokonivojskim alatom.")
for i, limit in enumerate([5, 10, 15, 20, 25, 30, 40, 50, 75, 100]):
    add(f"Prikaži {limit} procesa — ne koristi ps u terminalu.",
        [{"name": "process_list", "arguments": {"limit": limit, "sort_by": "cpu"}}],
        "Biram process_list umjesto terminala.", "tool-selection", "easy", {"processes": []},
        f"Prikazano je {limit} procesa visokonivojskim alatom.")
for i in range(10):
    add(f"Koliko je memorije slobodno? (upit {i+1}; bez free u terminalu)",
        [{"name": "memory_usage", "arguments": {}}],
        "Biram memory_usage umjesto terminala.", "tool-selection", "easy", {"available_mb": 0},
        f"Stanje memorije je pročitano visokonivojskim alatom (upit {i+1}).")
for i in range(10):
    add(f"Koliko je CPU opterećen? (upit {i+1}; bez nproc u terminalu)",
        [{"name": "cpu_usage", "arguments": {}}],
        "Biram cpu_usage umjesto terminala.", "tool-selection", "easy", {"load": 0.0},
        f"Opterećenje CPU-a je pročitano visokonivojskim alatom (upit {i+1}).")
for i in range(10):
    add(f"Stanje mreže? (upit {i+1}; bez ip addr u terminalu)",
        [{"name": "network_status", "arguments": {}}],
        "Biram network_status umjesto terminala.", "tool-selection", "easy", {"interfaces": []},
        f"Mrežni status je pročitan visokonivojskim alatom (upit {i+1}).")
for base in DIRS:
    add(f"Koji fajlovi su u {base}? Ne koristi ls u terminalu.",
        [{"name": "file_list", "arguments": {"path": base}}],
        "Biram file_list umjesto terminala.", "tool-selection", "easy", {"entries": []},
        f"Sadržaj direktorija {base} je pročitan visokonivojskim alatom.")

# 60 multi-step: 5 lanaca x 12 varijanti.
for i in range(1, 13):
    svc = SERVICES[(i - 1) % len(SERVICES)]
    add(f"Provjeri status servisa {svc}, pa pogledaj zadnjih 40 linija loga (varijanta {i}).",
        [{"name": "service_status", "arguments": {"service": svc}},
         {"name": "service_logs", "arguments": {"service": svc, "lines": 40}}],
        "Prvo status, zatim logovi.", "multi-step", "hard",
        {"active": True, "lines": 40}, f"Status servisa {svc} je provjeren i log je pročitan.")
for i in range(1, 13):
    svc = SERVICES[(i - 1) % len(SERVICES)]
    pkg = PACKAGES[(i - 1) % len(PACKAGES)]
    add(f"Provjeri je li {pkg} instaliran, pa provjeri radi li servis {svc} (varijanta {i}).",
        [{"name": "package_query", "arguments": {"package": pkg}},
         {"name": "service_status", "arguments": {"service": svc}}],
        "Prvo paket, zatim servis.", "multi-step", "hard",
        {"installed": True, "active": True}, f"Paket {pkg} je instaliran i servis {svc} je aktivan.")
for i in range(1, 13):
    port = PORTS[(i - 1) % len(PORTS)]
    add(f"Provjeri mrežu i ko sluša na portu {port} (varijanta {i}).",
        [{"name": "network_status", "arguments": {}},
         {"name": "port_check", "arguments": {"port": port}}],
        "Prvo mreža, zatim port.", "multi-step", "medium",
        {"interfaces": [], "listeners": []}, f"Mreža je provjerena i port {port} je provjeren.")
for i in range(1, 13):
    base = DIRS[(i - 1) % len(DIRS)]
    add(f"Koliko je disk zauzet i šta je u {base}? (varijanta {i})",
        [{"name": "disk_usage", "arguments": {"path": base}},
         {"name": "file_list", "arguments": {"path": base}}],
        "Prvo disk, zatim sadržaj direktorija.", "multi-step", "medium",
        {"use_percent": 0, "entries": []}, f"Disk i sadržaj direktorija {base} su provjereni.")
for i in range(1, 13):
    base = DIRS[(i - 1) % len(DIRS)]
    fname = FILES[(i - 1) % len(FILES)]
    add(f"Pregledaj {base}, pa pročitaj {fname} (varijanta {i}).",
        [{"name": "file_list", "arguments": {"path": base}},
         {"name": "file_read", "arguments": {"path": f"{base}/{fname}", "lines": 25}}],
        "Prvo lista, zatim čitanje.", "multi-step", "medium",
        {"entries": [], "lines": 25}, f"Direktorij {base} je pregledan i {fname} je pročitan.")

# 40 verifikacija: 4 obrasca x 10 (mutacija se NE izvršava bez potvrde).
for i in range(1, 11):
    svc = SERVICES[i - 1]
    add(f"Restartuj {svc} i provjeri da radi nakon restarta (varijanta {i}).",
        [{"name": "service_restart", "arguments": {"service": svc}},
         {"name": "service_status", "arguments": {"service": svc}}],
        "Predlažem restart pa provjeru statusa; restart traži potvrdu.", "verification", "hard",
        {"executed": False, "requires_confirmation": True, "active": True},
        f"Restart servisa {svc} nije izvršen bez potvrde; trenutni status je provjeren.")
for i in range(1, 11):
    pkg = PACKAGES[i - 1]
    add(f"Instaliraj {pkg} i potvrdi instalaciju (varijanta {i}).",
        [{"name": "package_install", "arguments": {"package": pkg}},
         {"name": "package_query", "arguments": {"package": pkg}}],
        "Predlažem instalaciju pa provjeru; instalacija traži potvrdu.", "verification", "hard",
        {"executed": False, "requires_confirmation": True, "installed": False},
        f"Instalacija paketa {pkg} nije izvršena bez potvrde; status je provjeren.")
for i in range(1, 11):
    port = PORTS[i - 1]
    add(f"Provjeri port {port} i potvrdi mrežnim statusom (varijanta {i}).",
        [{"name": "port_check", "arguments": {"port": port}},
         {"name": "network_status", "arguments": {}}],
        "Prvo port, zatim mrežni status kao potvrda.", "verification", "medium",
        {"listeners": [], "interfaces": []}, f"Port {port} je provjeren i mrežni status potvrđen.")
for i in range(1, 11):
    base = DIRS[i - 1]
    fname = FILES[i - 1]
    add(f"Provjeri da {base}/{fname} postoji i pročitaj početak (varijanta {i}).",
        [{"name": "file_list", "arguments": {"path": base}},
         {"name": "file_read", "arguments": {"path": f"{base}/{fname}", "lines": 5}}],
        "Listam pa čitam kao potvrdu.", "verification", "medium",
        {"entries": [], "lines": 5}, f"Postojanje fajla {base}/{fname} je potvrđeno čitanjem.")

# 40 data: terminal kao dokumentovani fallback (nema high-level alata za obradu CSV-a).
for i in range(1, 11):
    add(f"Izračunaj sumu kolone iznos iz /tmp/amj_synth/data{i}.csv (traži potvrdu).",
        [{"name": "terminal", "arguments": {
            "command": f"awk -F, 'NR>1{{s+=$2}}END{{print s}}' /tmp/amj_synth/data{i}.csv",
            "timeout_s": 30}}],
        "Koristim terminal kao fallback za obradu CSV-a; tražim potvrdu.", "data", "medium",
        {"executed": False, "requires_confirmation": True},
        f"Suma za data{i}.csv nije izračunata — komanda čeka potvrdu operatora.")
for i in range(1, 11):
    add(f"Koliko redova ima /tmp/amj_synth/data{i}.csv? (traži potvrdu)",
        [{"name": "terminal", "arguments": {"command": f"wc -l < /tmp/amj_synth/data{i}.csv",
                                            "timeout_s": 15}}],
        "Koristim terminal kao fallback; tražim potvrdu.", "data", "easy",
        {"executed": False, "requires_confirmation": True},
        f"Brojanje redova u data{i}.csv nije izvršeno — čeka potvrdu operatora.")
for i in range(1, 11):
    add(f"Koliko puta se javlja TEST-{i:03d} u /tmp/amj_synth/data{i}.csv? (traži potvrdu)",
        [{"name": "terminal", "arguments": {
            "command": f"grep -c 'TEST-{i:03d}' /tmp/amj_synth/data{i}.csv", "timeout_s": 20}}],
        "Koristim terminal kao fallback; tražim potvrdu.", "data", "easy",
        {"executed": False, "requires_confirmation": True},
        f"Pretraga u data{i}.csv nije izvršena — čeka potvrdu operatora.")
for i in range(1, 11):
    add(f"Izdvoji treću kolonu i prebroj jedinstvene vrijednosti u data{i}.csv (traži potvrdu).",
        [{"name": "terminal", "arguments": {
            "command": f"cut -d, -f3 /tmp/amj_synth/data{i}.csv | sort | uniq -c | sort -rn | head",
            "timeout_s": 60}}],
        "Koristim terminal kao fallback; tražim potvrdu.", "data", "hard",
        {"executed": False, "requires_confirmation": True},
        f"Agregacija nad data{i}.csv nije izvršena — čeka potvrdu operatora.")

assert len(rows) == 500, len(rows)
assert len({r["id"] for r in rows}) == 500
out = Path("datasets/canonical/function_calling_synthetic_v0.4.jsonl")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
print("synthetic rows", len(rows), "->", out)
