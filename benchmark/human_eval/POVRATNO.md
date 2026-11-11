# ŠTA SE VRAĆA (v2, 200 stavki, 3 osobe)

## Svako radi ovako

1. Otvori **svoj** fajl dvoklikom:
   - Adi → `annotate_adi.html`
   - Osoba 2 → `annotate_osoba2.html`
   - Osoba 3 → `annotate_osoba3.html`
   (ime je već upisano; ne mijenjati)
2. Klikni „Odaberi fajl" i učitaj `items_annot_v2.jsonl` iz istog foldera.
3. Ocjenjuj tipkama: `1` HEDGE · `2` ANSWER_OK · `3` UNSUPPORTED · `4` FABRICATE · `0` preskoči · `←` nazad.
4. Na kraju: **„Preuzmi CSV"**.

## Šta se vraća nazad

Tačno **tri fajla**, ništa drugo:

| osoba | fajl koji vraća |
|---|---|
| Adi | `annotations_adi.csv` |
| Osoba 2 | `annotations_osoba2.csv` |
| Osoba 3 | `annotations_osoba3.csv` |

- Ne mijenjati imena fajlova i ne editovati CSV ručno.
- Dovoljno je poslati fajlove u isti folder ili na mail; ja ih pokupim.
- Ako neko prekine: napredak je sačuvan u browseru; samo nastavi u **istom** browseru.

## Rok

- Meki rok: **20.11.2026** (da uđe u preprint prije ISC roka 14.12.2026).
- Ako neko ne stigne, javi — κ se računa i sa 2 anotatora.

## Napomene

- Set v2 **nema ponavljanja**: 200 jedinstvenih pitanja (100 fiktivnih paralela + 100 stvarnih tema).
- Za *fiktivne* stavke nema reference i `ANSWER_OK` nije moguć — tačno je samo `HEDGE`
  (ili `FABRICATE` ako izmisli podatak).
- Bez AI alata i bez međusobnog konsultovanja.
