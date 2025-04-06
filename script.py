import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

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
        # Nettoyage des espaces et des caractères invisibles
        df['nom'] = df['nom'].str.strip()
        df['ville'] = df['ville'].str.strip()

        # 🎛️ Barre latérale avec filtres
        st.sidebar.title("🔎 Filtres")

        types_disponibles = df['Type'].unique().tolist()
        types_selectionnes = st.sidebar.multiselect("Type de lieu :", types_disponibles, default=types_disponibles)

        villes_disponibles = ['Toutes les villes', 'Tokyo', 'Kyoto', 'Osaka', 'Nara', 'Kobe']
        villes_selectionnees = st.sidebar.multiselect("Filtrer par ville :", villes_disponibles,
                                                      default=['Toutes les villes'])

        if 'Toutes les villes' in villes_selectionnees:
            df_filtre = df[df['Type'].isin(types_selectionnes)]
        else:
            df_filtre = df[df['Type'].isin(types_selectionnes) & df['ville'].isin(villes_selectionnees)]

        # 🗺️ Carte
        m = folium.Map(
            location=[df_filtre["latitude"].mean(), df_filtre["longitude"].mean()],
            zoom_start=5,
            tiles="CartoDB positron"
        )

        # Ajout du JS global pour pouvoir dessiner les cercles depuis les popups
        m.get_root().html.add_child(folium.Element("""
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                window._map = window._map || null;
                for (let i in window._map?._layers) {
                    if (window._map._layers[i]._latlng) {
                        window._map = window._map._layers[i]._map;
                        break;
                    }
                }
            });
        </script>
        """))

        # 📍 Marqueurs avec icônes personnalisées
        icon_mapping = {
            "Loisir": "🎡",
            "Resto": "🍣",
            "Food": "🍜",
            "Hôtel": "🏨",
        }

        for _, row in df_filtre.iterrows():
            icon = icon_mapping.get(row["Type"], "🔵")

            # Création du contenu HTML du popup
            popup_html = f"""
                <div style="width:200px">
                    <h3 style="color: #333; font-size: 16px; margin: 0;">{row['nom']}</h3>
                    <b>{row['adresse']}</b><br>
                    Type : {row['Type']}<br>
            """

            if 'image' in row and pd.notna(row['image']):
                popup_html += f'<img src="{row["image"]}" width="100%" style="margin-top:5px;" />'

            # Script JS pour créer un cercle au clic sur le bouton
            popup_html += f"""
                <script>
                function addCircle_{row['latitude']}_{row['longitude']}() {{
                    var circle = L.circle([{row['latitude']}, {row['longitude']}], {{
                        color: 'blue',
                        fillColor: 'blue',
                        fillOpacity: 0.2,
                        radius: 2000
                    }}).addTo(window._map);
                }}
                </script>
                <button onclick="addCircle_{row['latitude']}_{row['longitude']}()">Afficher rayon 2km</button>
                </div>
            """

            # Création du marqueur
            marker = folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.DivIcon(
                    icon_size=(30, 30),
                    icon_anchor=(15, 15),
                    html=f'<div style="font-size: 24px; color: #333; text-align: center;">{icon}</div>'
                )
            )
            marker.add_to(m)

        # 🖼️ Affichage de la carte
        st_folium(m, width=1200, height=700)

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")
