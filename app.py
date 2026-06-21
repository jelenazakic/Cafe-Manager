import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
import time
from dotenv import load_dotenv
from datetime import datetime

# =====================================================
# LOAD ENVIRONMENT VARIABLES & CONNECT
# =====================================================
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    st.error("SUPABASE_URL ili SUPABASE_KEY nisu pronađeni u .env fajlu.")
    st.stop()

supabase: Client = create_client(supabase_url, supabase_key)

# =====================================================
# PAGE CONFIG 
# =====================================================
st.set_page_config(
    page_title="Popis Šanka",
    page_icon="📝",
    layout="centered",
)

# =====================================================
# LOAD EXTERNAL CSS FILE
# =====================================================
def load_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/style.css")

# =====================================================
# ITEMS LIST (Exact names matching your database)
# =====================================================
ITEMS_LIST = [
    'Espresso', 'Nes kafa', 'Domaća kafa', 'Mleko', 'Čaj', 'Voda', 
    'Sok flašica', 'Next', 'Cockta', 'Orangina', 'Cedevita', 'Red Bull', 
    'Guarana', 'Vino flašica', 'Točeno pivo', 'Nikšićko pivo flašica', 'Strano pivo', 
    'Corona', 'Somersby', 'Smirnoff Ice', 'Domaća loza', 'Kovilj rakija', 
    'Kajsija', 'Viljamovka', 'Šljiva', 'Johnnie Walker', 'Chivas Regal', 
    'Jack Daniels', 'Tullamore D.E.W.', 'Dunja', 'Campari', 'Martini', 
    'Vodka', 'Tekila', 'Bacardi', 'Gin', 'Baileys', 'Jameson', 'Aperol', 
    'Ballantines', 'Pelinkovac', 'Jägermeister', 'Voda velika', 'Ivi', 'Prosecco', 'Triple Sec','Grenadine','Blue Curasao', 'Alter pivo', 'Aspal', 'Koktel Bočica'
]
INT_ITEMS = [
    'Espresso', 'Domaća kafa', 'Mleko', 'Čaj', 'Voda', 'Sok flašica', 
    'Next', 'Cockta', 'Orangina', 'Cedevita', 'Red Bull', 'Guarana', 
    'Vino flašica', 'Nikšićko pivo', 'Nikšićko pivo flašica', 'Strano pivo', 
    'Corona', 'Somersby', 'Smirnoff Ice', 'Voda velika', 'Ivi', 'Alter pivo', 'Aspal', 'Koktel Bočica'
]

# =====================================================
# HEADER & NAVIGATION TABS
# =====================================================
st.title("🍹 Šank Popis v2.0")

tab_entry, tab_view, tab_edit= st.tabs(["📝 Novi Popis", "📊 Pregled", "✏️ Ispravka"])

# =====================================================
# TAB 1: NEW ENTRY (POPIS)
# =====================================================
with tab_entry:
    st.subheader("Unesi stanje")
  
    selected_date = st.date_input("Datum popisa:", datetime.now().date())
    
    with st.form("main_inventory_form", clear_on_submit=False):
        
        entered_quantities = {}
        
        for item in ITEMS_LIST:
            if item in INT_ITEMS:
                entered_quantities[item] = st.number_input(
                    label=item, min_value=0, value=0, step=1, key=f"input_{item}"
                )
            else:
                entered_quantities[item] = st.number_input(
                    label=item, min_value=0.0, value=0.0, step=0.1, format="%.1f", key=f"input_{item}"
                )
            
        save_button = st.form_submit_button("💾 SAČUVAJ PODATKE")
        
        if save_button:
            database_payload = []
            for item, qty in entered_quantities.items():
                database_payload.append({
                    "ime_artikala": item,
                    "kolicina": qty,
                    "datum_popisa": str(selected_date)
                })
                
            try:
                supabase.table("stanje_popisa").insert(database_payload).execute()
                st.success("🎉 Popis je uspešno sačuvan u bazu!")
                st.balloons()
            except Exception as e:
                st.error(f"Greška pri čuvanju u bazu: {e}")

# =====================================================
# TAB 2: VIEW LOGS (PREGLED PODATAKA)
# =====================================================
with tab_view:
    st.subheader("Sačuvana stanja na šanku")
    
    if st.button("🔄 Osveži tabelu", key="refresh_view"):
        st.rerun()
        
    try:
        # Selektujemo tačan naziv kolone: 'ime_artikala'
        response = supabase.table("stanje_popisa").select("id, ime_artikala, kolicina, datum_popisa").order("datum_popisa").limit(200).execute()
        records_data = response.data
        
        if not records_data:
            st.info("Nema unetih popisa u bazi podataka.")
        else:
            df = pd.DataFrame(records_data)

            df['ime_artikala'] = pd.Categorical(df['ime_artikala'], categories=ITEMS_LIST, ordered=True)

            unique_dates = sorted(df["datum_popisa"].unique(), reverse=True)
            selected_filter_date = st.selectbox("Filtriraj po datumu:", unique_dates, key="filter_date_view")
            
            filtered_df = df[df["datum_popisa"] == selected_filter_date]

            filtered_df = filtered_df.sort_values("ime_artikala")

            st.write(f"**Trenutni popis za dan {selected_filter_date}:**")
            
            for _, row in filtered_df.iterrows():
                st.markdown(f"""
                <div class="popis-kartica">
                    <span style="font-weight:600; color:#333;">{row['ime_artikala']}</span>
                    <span style="font-weight:700; color:#2e7d32; font-size:16px;">{float(row['kolicina'])}</span>
                </div>
                """, unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Nije moguće učitati podatke: {e}")


# =====================================================
# TAB 3: CORRECTIONS PANEL 
# =====================================================
with tab_edit:
    st.subheader("Izmeni pogrešan unos")
    
    try:
        response = supabase.table("stanje_popisa").select("id, ime_artikala, kolicina, datum_popisa").order("datum_popisa").limit(200).execute()
        records_data = response.data
        
        if not records_data:
            st.info("Nema podataka dostupnih za izmenu.")
        else:
            df = pd.DataFrame(records_data)

            df['ime_artikala'] = pd.Categorical(df['ime_artikala'], categories=ITEMS_LIST, ordered=True)
            
            unique_dates = sorted(df["datum_popisa"].unique(), reverse=True)
            selected_filter_date = st.selectbox("1. Izaberi datum popisa:", unique_dates, key="filter_date_edit")
            
            filtered_df = df[df["datum_popisa"] == selected_filter_date]
            
            filtered_df = filtered_df.sort_values("ime_artikala")
            
            item_options = {f"{row['ime_artikala']} (Trenutno: {row['kolicina']})": row for _, row in filtered_df.iterrows()}
            
            if item_options:
                with st.form("isolated_edit_form", clear_on_submit=False):
                    selected_item_label = st.selectbox("2. Izaberi artikal za ispravku:", list(item_options.keys()))
                    target_row = item_options[selected_item_label]
                    
                    decimal_step_items = [
                        'Domaća loza', 'Kovilj rakija', 'Kajsija', 'Viljamovka', 'Šljiva', 
                        'Johnnie Walker', 'Chivas Regal', 'Jack Daniels', 'Tullamore D.E.W.', 
                        'Dunja', 'Campari', 'Martini', 'Vodka', 'Tekila', 'Bacardi', 'Gin', 
                        'Baileys', 'Jameson', 'Aperol', 'Ballantines', 'Pelinkovac', 'Jägermeister', 'Prosecco'
                    ]
                    
                    if target_row['ime_artikala'] in decimal_step_items:
                        new_qty = st.number_input(
                            "3. Unesi novu TAČNU količinu:",
                            min_value=0.0, value=float(target_row['kolicina']), step=0.1, format="%.1f", key="isolated_edit_qty"
                        )
                    else:
                        new_qty = st.number_input(
                            "3. Unesi novu TAČNU količinu:",
                            min_value=0, value=int(target_row['kolicina']), step=1, key="isolated_edit_qty"
                        )
                    
                    submit_edit = st.form_submit_button("💾 SAČUVAJ ISPRAVKU")
                    
                    if submit_edit:
                        try:
                            supabase.table("stanje_popisa").update({"kolicina": new_qty}).eq("id", target_row['id']).execute()
                            st.success(f"Uspešno izmenjeno! {target_row['ime_artikala']} je sada: {new_qty}")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Greška pri izmeni u bazi: {e}")
            else:
                st.warning("Nema unetih artikala za ovaj datum.")

            st.markdown("---") 
            st.subheader("🚨 Obriši ceo dan popisa")
            st.warning(f"Pažnja: Sledeća akcija će trajno obrisati SVE artikle koji su uneti za datum: **{selected_filter_date}**.")
            
            potvrda_brisanja = st.checkbox(f"Potvrđujem da želim da obrišem kompletan popis za {selected_filter_date}", key="potvrda_delete_dan")
            
            if st.button("🔥 OBRIŠI CEO DAN POPISA", type="primary", disabled=not potvrda_brisanja):
                try:
                    supabase.table("stanje_popisa").delete().eq("datum_popisa", selected_filter_date).execute()
                    
                    st.success(f"Uspešno obrisan kompletan popis za dan: {selected_filter_date}!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Greška pri brisanju dana iz baze: {e}")
    except Exception as e:
        st.error(f"Greška pri učitavanju panela za izmene: {e}")