from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import pandas as pd
from openai import OpenAI

# Alustetaan tekoäly
client = OpenAI(
    api_key=(
        "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"
    )
)

tiedoston_nimi = "bauma_naytteilleasettajat.xlsx"

try:
  df_raaka = pd.read_excel(tiedoston_nimi)
  print(
      f"📁 Ladattu onnistuneesti! Tiedostossa on {len(df_raaka)} yritystä."
  )
except FileNotFoundError:
  print(
      f"❌ Tiedostoa '{tiedoston_nimi}' ei löytynyt. Varmista, että se on"
      " kansiossa!"
  )
  exit()


def analysoi_yritys(index, row):
  nimi = str(row.get("Firma", f"Yritys {index}"))
  halli = str(row.get("Halle", ""))
  maa = str(row.get("Land", ""))
  kaupunki = str(row.get("Ort", ""))

  prompt = f"""
    Olet teknologia- ja sijoitusanalyytikko (Venture Capital / Tech M&A). 
    Etsit Bauman messuilta potentiaalisia sijoituskohteita, teknologiahaastajia ja piileviä innovaatiohelmiä ("hidden gems"). Pienikin toimija voi saada huippupisteet, jos sen teknologia on poikkeuksellista.

    Analysoi tämä yritys nimen, sijainnin ja messuhallin perusteella:
    - Yrityksen nimi: {nimi}
    - Messuhalli / Osasto: {halli}
    - Maa: {maa}
    - Paikkakunta: {kaupunki}

    Tehtävä:
    1. Päätele päätoimiala johonkin näistä:
       - "Rakennuskoneet & Maansiirto"
       - "Kaivostoiminta & Louhinta"
       - "Rakennusmateriaalien tuotantokoneet (Keramiikka/Betoni)"
       - "Komponentit & Palvelut"
       - "Muu / Tuntematon"
    2. Kuvaile lyhyesti heidän todennäköinen teknologiansa tai erikoistuotteensa.
    3. Anna kolme osapistettä (0-100) sijoittajan näkökulmasta:
       - "osumatarkkuus": Miten kriittisesti se liittyy edistyneeseen materiaali- tai koneteknologiaan.
       - "innovatiivisuus": Onko kyseessä alan edelläkävijä (tekoäly, vihreä siirtymä, automaatio, uusi prosessi).
       - "sijoituspotentiaali": Haastajapotentiaali, skaalautuvuus tai ainutlaatuinen niche.
    4. Kirjoita lyhyt perustelu (1-2 lausetta), miksi tämä yritys on (tai ei ole) kiinnostava sijoituskohteena tai teknologiahaastajana.

    Palauta vastaus AINOASTAAN tässä JSON-muodossa:
    {{
        "toimiala": "päätoimiala tähän",
        "paateknologia": "lyhyt kuvaus",
        "osumatarkkuus": 0-100,
        "innovatiivisuus": 0-100,
        "sijoituspotentiaali": 0-100,
        "perustelu": "sijoitusperustelu tähän"
    }}
    """

  try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    ai = json.loads(response.choices[0].message.content)
  except Exception as e:
    ai = {
        "toimiala": "Virhe",
        "paateknologia": str(e),
        "osumatarkkuus": 0,
        "innovatiivisuus": 0,
        "sijoituspotentiaali": 0,
        "perustelu": "Virhe analyysissä.",
    }

  kokonaispisteet = round(
      ai["osumatarkkuus"] * 0.4
      + ai["innovatiivisuus"] * 0.3
      + ai["sijoituspotentiaali"] * 0.3,
      1,
  )

  return {
      "Yritys": nimi,
      "Halli": halli,
      "Maa": maa,
      "Paikkakunta": kaupunki,
      "PLZ": str(row.get("PLZ", "")),
      "Toimiala": ai["toimiala"],
      "Pääteknologia": ai["paateknologia"],
      "Osumapisteet": ai["osumatarkkuus"],
      "Innovatiivisuuspisteet": ai["innovatiivisuus"],
      "Sijoituspotentiaali": ai["sijoituspotentiaali"],
      "Kokonaispisteet": kokonaispisteet,
      "Perustelu": ai["perustelu"],
  }


print(
    "\n🔄 Etsitään sijoitushelmiä rinnakkaisajolla (nopeutettu versio)..."
)
tulokset = []

# max_workers säätää rinnakkaisten kutsujen määrää (10 on turvallinen ja nopea)
max_threads = 30

with ThreadPoolExecutor(max_workers=max_threads) as executor:
  # Voit lisätä .head(10) tähän tarvittaessa testausta varten: df_raaka.head(10).iterrows()
  futures = {
      executor.submit(analysoi_yritys, index, row): index
      for index, row in df_raaka.iterrows()
  }

  valmiina = 0
  yhteensa = len(df_raaka)

  for future in as_completed(futures):
    valmiina += 1
    tulos = future.result()
    tulokset.append(tulos)
    print(
        f"-> ({valmiina}/{yhteensa}) Valmistui: {tulos['Yritys']}"
        f" ({tulos['Toimiala']})"
    )

# Tallennetaan uusi rikastettu tiedosto
df_tulos = pd.DataFrame(tulokset)
df_tulos.to_csv("bauma_sijoitus_analyysi.csv", index=False, encoding="utf-8")
print(
    "\n🎉 Analyysi valmis! Tulokset tallennettu tiedostoon"
    " 'bauma_sijoitus_analyysi.csv'."
)
