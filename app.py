import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Bauma Sijoitus- ja Haastaja-analytiikka", layout="wide"
)

st.title(
    "🏗️ Bauma Messut – Sijoituskohteet & Teknologiahaastajat (Hidden Gems)"
)
st.write(
    "Tämä dashboard auttaa tunnistamaan markkinahaastajat ja innovatiiviset"
    " pienet toimijat. Voit säätää painoarvoja sivupalkista lennosta!"
)
    
try:
  df = pd.read_csv("bauma_sijoitus_analyysi.csv")

  # --- SIVUPALKKI ---
  st.sidebar.header("🎛️ Pisteytyksen painoarvot")
  paino_osuma = st.sidebar.slider("Osumatarkkuuden paino (%)", 0, 100, 40)
  paino_innovaatio = st.sidebar.slider(
      "Innovatiivisuuden paino (%)", 0, 100, 30
  )
  paino_sijoitus = st.sidebar.slider("Sijoituspotentiaalin paino (%)", 0, 100, 30)

  # Normalisoidaan painot
  paino_summa = paino_osuma + paino_innovaatio + paino_sijoitus
  if paino_summa > 0:
    p_osuma = paino_osuma / paino_summa
    p_innovaatio = paino_innovaatio / paino_summa
    p_sijoitus = paino_sijoitus / paino_summa
  else:
    p_osuma, p_innovaatio, p_sijoitus = 0.33, 0.33, 0.33

  # Lasketaan dynaamiset kokonaispisteet uudelleen käyttäjän valintojen mukaan
  df["Kokonaispisteet"] = round(
      df["Osumapisteet"] * p_osuma
      + df["Innovatiivisuuspisteet"] * p_innovaatio
      + df["Sijoituspotentiaali"] * p_sijoitus,
      1,
  )

  st.sidebar.divider()
  st.sidebar.header("🔍 Suodattimet")

  valitut_toimialat = st.sidebar.multiselect(
      "Valitse toimialat:",
      options=df["Toimiala"].unique(),
      default=df["Toimiala"].unique(),
  )

  valitut_maat = st.sidebar.multiselect(
      "Valitse maat:",
      options=df["Maa"].dropna().unique(),
      default=df["Maa"].dropna().unique(),
  )

  min_pisteet = st.sidebar.slider("Minimikokonaispisteet:", 0, 100, 0)

  # Suodatetaan data
  suodatettu_df = df[
      (df["Toimiala"].isin(valitut_toimialat))
      & (df["Maa"].isin(valitut_maat))
      & (df["Kokonaispisteet"] >= min_pisteet)
  ].sort_values(by="Kokonaispisteet", ascending=False)

  # --- KPI-LUVUT ---
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric(
        label="Yrityksiä näkyvissä",
        value=len(suodatettu_df),
        delta=f"Kaikista {len(df)}",
    )
  with col2:
    keskipisteet = (
        round(suodatettu_df["Kokonaispisteet"].mean(), 1)
        if not suodatettu_df.empty
        else 0
    )
    st.metric(label="Keskimääräiset pisteet", value=f"{keskipisteet} / 100")
  with col3:
    maat_lkm = (
        suodatettu_df["Maa"].nunique() if not suodatettu_df.empty else 0
    )
    st.metric(label="Edustetut maat", value=maat_lkm)

  st.divider()

  # --- TOP 5 SÄHKÄINEN LISTA PERUSTELUINEEN ---
  st.subheader("⭐ Top Sijoituskohteet & Haastajat")
  if not suodatettu_df.empty:
    top_5 = suodatettu_df.head(5)
    for _, row in top_5.iterrows():
      st.markdown(
          f"**{row['Yritys']}** ({row['Maa']}, {row['Paikkakunta']}) — ⭐"
          f" **Pisteet: {row['Kokonaispisteet']}**  \n> *Teknologia:* "
          f"{row['Pääteknologia']}  \n> *Sijoittaja-analyysi:* "
          f"{row['Perustelu']}"
      )
      st.write("")
  else:
    st.info("Ei yrityksiä valituilla suodattimilla.")

  st.divider()

  # --- TAULUKKO ---
  st.subheader("📋 Kaikki yritykset listattuna")
  st.dataframe(suodatettu_df, use_container_width=True)

except FileNotFoundError:
  st.warning(
      "⚠️ Tiedostoa 'bauma_sijoitus_analyysi.csv' ei löydy. Aja ensin 'python"
      " main.py'!"
  )