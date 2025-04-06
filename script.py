import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

st.set_page_config(page_title="Carte des lieux", layout="wide")
st.title("📍 Carte interactive des lieux (depuis Google Sheets)")

# 🔗 Lien vers la Google Sheet en CSV
url_csv = "https://docs.google.com/spreadsheets/d/1bOu0G2cpaqJqG5xYTRonE5BmDptpFVInN0wdHghXNDQ/gviz/tq?tqx=out:csv"

try:
    df = pd.read_csv(url_csv)

    # ✅ Vérification des colonnes
    required_columns = ['nom', 'adresse', 'Type', 'latitude', 'longitude', 'ville']
    if not all(col in df.columns for col in required_columns):
        st.error(f"❌ Colonnes manquantes. Requises : {', '.join(required_columns)}")
    else:
        # Nettoyage des espaces et des caractères invisibles dans les colonnes "nom" et "ville"
        df['nom'] = df['nom'].str.strip()
        df['ville'] = df['ville'].str.strip()

        # 🎛️ Barre latérale avec filtres
        st.sidebar.title("🔎 Filtres")

        # Filtre par Type
        types_disponibles = df['Type'].unique().tolist()
        types_selectionnes = st.sidebar.multiselect("Type de lieu :", types_disponibles, default=types_disponibles)

        # Filtre par Ville avec l'option "Toutes les villes"
        villes_disponibles = ['Toutes les villes', 'Tokyo', 'Kyoto', 'Osaka', 'Nara', 'Kobe']
        villes_selectionnees = st.sidebar.multiselect("Filtrer par ville :", villes_disponibles, default=['Toutes les villes'])

        # 📄 Filtrage par Type et Ville
        if 'Toutes les villes' in villes_selectionnees:
            df_filtre = df[df['Type'].isin(types_selectionnes)]  # Pas de filtre sur les villes
        else:
            df_filtre = df[df['Type'].isin(types_selectionnes) & df['ville'].isin(villes_selectionnees)]

        # 🗺️ Carte
        m = folium.Map(
            location=[df_filtre["latitude"].mean(), df_filtre["longitude"].mean()],
            zoom_start=5,
            tiles="CartoDB positron"
        )

        # 📍 Marqueurs avec icônes personnalisées
        icon_mapping = {
            "Loisir": "🎡",    # Parc d'attraction
            "Resto": "🍣",     # Restaurant
            "Food": "🍜",      # Nourriture
            "Hôtel": "🏨",     # Hôtel
        }

        for _, row in df_filtre.iterrows():
            icon = icon_mapping.get(row["Type"], "🔵")  # Icône par défaut (si type non défini)

            # HTML du popup
            popup_html = f"""
                <div style="width:200px">
                    <h3 style="color: #333; font-size: 16px; margin: 0;">{row['nom']}</h3>  <!-- Nom plus gros -->
                    <b>{row['adresse']}</b><br>
                    Type : {row['Type']}<br>
            """

            if 'image' in row and pd.notna(row['image']):
                popup_html += f'<img src="{row["image"]}" width="100%" style="margin-top:5px;" />'

            popup_html += "</div>"

            # Création du marqueur avec icône personnalisée
            marker = folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.DivIcon(
                    icon_size=(30, 30),
                    icon_anchor=(15, 15),
                    html=f'<div style="font-size: 24px; color: #333; text-align: center;">{icon}</div>'  # Icône centrée
                )
            ).add_to(m)

            # Ajout du cercle de 2 km autour du marqueur
            circle = folium.Circle(
                location=[row["latitude"], row["longitude"]],
                radius=2000,  # Rayon de 2 km
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.2,
                # Le cercle est invisible au début
                opacity=0
            ).add_to(m)

            # JavaScript pour afficher le cercle au clic sur le marqueur
            marker.add_child(folium.Popup('Cliquez sur ce marqueur').add_child(folium.ClickForMarker(
                options={"event": "click", "handler": f"function() {{ {circle.get_name()}.setStyle({{ opacity: 1 }}); }}"})
            ))

        # 🖼️ Affichage de la carte en grand
        folium_static(m, width=1200, height=700)

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")
