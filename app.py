import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime

# =====================================================
# LOAD ENVIRONMENT VARIABLES & CONNECT
# =====================================================
load_dotenv()

url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not url or not key:
    st.error("SUPABASE_URL ili SUPABASE_KEY nisu pronađeni u .env fajlu.")
    st.stop()

supabase: Client = create_client(url, key)

# =====================================================
# PAGE CONFIG 
# =====================================================
st.set_page_config(
    page_title="Popis Šanka",
    page_icon="📝",
    layout="centered",
)

# =====================================================
# CSS 
# =====================================================
st.markdown("""
<style>
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
    max-width: 100% !important;
}

h1 {
    text-align: center !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    width: 100% !important;
    display: block !important;
    margin-bottom: 1rem !important;
}

h3 {
    font-size: 18px !important;
    font-weight: 600;
}

.stNumberInput div div input {
    font-size: 16px !important; 
    height: 42px !important;
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    height: 52px;
    font-size: 16px;
    font-weight: 700;
    background-color: #2e7d32 !important;
    color: white !important;
    border: none;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
    margin-top: 1rem;
}

.popis-kartica {
    background-color: #f8f9fa;
    padding: 10px 15px;
    border-radius: 8px;
    margin-bottom: 8px;
    border-left: 4px solid #2e7d32;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# LISTA ARTIKALA (Tačni nazivi iz tvoje baze)
# =====================================================
ARTIKLI_LISTA = [
    'Espresso', 'Nes kafa', 'Domaća kafa', 'Mleko', 'Čaj', 'Voda', 
    'Sok flašica', 'Next', 'Cockta', 'Orangina', 'Cedevita', 'Red Bull', 
    'Guarana', 'Vino flašica', 'Točeno pivo', 'Nikšićko pivo', 'Strano pivo', 
    'Corona', 'Somersby', 'Smirnoff Ice', 'Domaća loza', 'Kovilj rakija', 
    'Kajsija', 'Viljamovka', 'Šljiva', 'Johnnie Walker', 'Chivas Regal', 
    'Jack Daniels', 'Tullamore D.E.W.', 'Dunja', 'Campari', 'Martini', 
    'Vodka', 'Tekila', 'Bacardi', 'Gin', 'Baileys', 'Jameson', 'Aperol', 
    'Ballantines', 'Pelinkovac', 'Jägermeister', 'Voda velika', 'Ivi', 'Prosecco'
]

# =====================================================
# NASLOV 
# =====================================================
st.title("🍹 Šank Popis v2.0")

tab_unos, tab_pregled = st.tabs(["📝 Novi Popis", "📊 Pregled"])

# =====================================================
# TAB 1: POPIS
# =====================================================
with tab_unos:
    st.subheader("Unesi stanje")
  
    izabrani_datum = st.date_input("Datum popisa:", datetime.now().date())
    
    with st.form("velika_popis_forma", clear_on_submit=False):
        
        unesene_kolicine = {}
        
        for artikal in ARTIKLI_LISTA:
            pomoćna_lista = ['Domaća loza', 'Kovilj rakija', 'Kajsija', 'Viljamovka', 'Šljiva', 
                             'Johnnie Walker', 'Chivas Regal', 'Jack Daniels', 'Tullamore D.E.W.', 
                             'Dunja', 'Campari', 'Martini', 'Vodka', 'Tekila', 'Bacardi', 'Gin', 
                             'Baileys', 'Jameson', 'Aperol', 'Ballantines', 'Pelinkovac', 'Jägermeister','Prosecco']
            if artikal in pomoćna_lista:
                        unesene_kolicine[artikal] = st.number_input(
                            label=artikal,
                            min_value=0.0,
                            value=0.0,
                            step=0.1,
                            format="%.1f",
                            key=f"input_{artikal}"
                        )
            else:
              unesene_kolicine[artikal] = st.number_input(
                            label=artikal,
                            min_value=0,
                            value=0,
                            step=1,
                            key=f"input_{artikal}"
                        )
            
        sacuvaj_button = st.form_submit_button("💾 SAČUVAJ PODATKE")
        
        if sacuvaj_button:
            podaci_za_bazu = []
            for artikal, kolicina in unesene_kolicine.items():
                podaci_za_bazu.append({
                    "ime_artikla": artikal,
                    "kolicina": kolicina,
                    "datum_popisa": str(izabrani_datum)
                })
                
            try:
                supabase.table("stanje_popisa").insert(podaci_za_bazu).execute()
                st.success("🎉 Popis je uspešno sačuvan u bazu!")
                st.balloons()
            except Exception as e:
                st.error(f"Greška pri čuvanju u bazu: {e}")

# =====================================================
# TAB 2: PREGLED PODATAKA 
# =====================================================
with tab_pregled:
    st.subheader("Poslednji unosi iz baze")
    
    if st.button("🔄 Osveži podatke"):
        st.rerun()
        
    try:
        odgovor = supabase.table("stanje_popisa").select("*").order("datum_popisa").limit(100).execute()
        podaci = odgovor.data
        
        if not podaci:
            st.info("Nema unetih popisa u bazi podataka.")
        else:
            df = pd.DataFrame(podaci)
            
            svi_datumi = df["datum_popisa"].unique()
            izabrani_filter_datum = st.selectbox("Filtriraj po datumu:", svi_datumi)
            
            filtrirani_df = df[df["datum_popisa"] == izabrani_filter_datum]
            
            st.write(f"**Popis za dan {izabrani_filter_datum}:**")
            
            for _, red in filtrirani_df.iterrows():
                st.markdown(f"""
                <div class="popis-kartica">
                    <span style="font-weight:600; color:#333;">{red['ime_artikala']}</span>
                    <span style="font-weight:700; color:#2e7d32; font-size:16px;">{red['kolicina']}</span>
                </div>
                """, unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Nije moguće učitati podatke: {e}")