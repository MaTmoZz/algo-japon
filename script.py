import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import openrouteservice

# 🔐 Clé API OpenRouteService (remplace par la tienne)
ORS_API_KEY = "5b3ce3597851110001cf624867167f0c677e46438d0503968c4631c8"
client = openrouteservice.Client(key=ORS_API_KEY, retry_over_query_limit=False)

st.set_page_config(page_title="Carte des lieux", layout="wide")
st.title("📍 Carte interactive des lieux (depuis Google Sheets)")

# 🔗 Lien CSV de Google Sheets
url_csv = "https://docs.google.com/spreadsheets/d/1bOu0G2cpaqJqG5xYTRonE5BmDptpFVInN0wdHghXNDQ/gviz/tq?tqx=out:csv"

try:
    df = pd.read_csv(url_csv)

    required_columns = ['nom', 'adresse', 'Type', 'latitude', 'longitude', 'ville']
    if not all(col in df.columns for col in required_columns):
        st.error(f"❌ Colonnes manquantes. Requises : {', '.join(required_columns)}")
    else:
        df['nom'] = df['nom'].str.strip()
        df['ville'] = df['ville'].str.strip()

        # 🎛️ Filtres
        st.sidebar.title("🔎 Filtres")

        types_disponibles = df['Type'].unique().tolist()
        types_selectionnes = st.sidebar.multiselect("Type de lieu :", types_disponibles, default=types_disponibles)

        villes_disponibles = ['Toutes les villes'] + sorted(df['ville'].dropna().unique().tolist())
        villes_selectionnees = st.sidebar.multiselect("Filtrer par ville :", villes_disponibles, default=['Toutes les villes'])

        if 'Toutes les villes' in villes_selectionnees:
            df_filtre = df[df['Type'].isin(types_selectionnes)]
        else:
            df_filtre = df[df['Type'].isin(types_selectionnes) & df['ville'].isin(villes_selectionnees)]

        # 🧭 Sélection points pour itinéraire
        st.sidebar.markdown("---")
        st.sidebar.subheader("🧭 Créer un itinéraire")

        lieux_disponibles = df_filtre['nom'].tolist()
        point_depart = st.sidebar.selectbox("Point de départ", lieux_disponibles)
        point_arrivee = st.sidebar.selectbox("Point d'arrivée", lieux_disponibles)

        # Si les itinéraires n'ont pas encore été calculés
        if "itineraire" not in st.session_state:
            st.session_state.itineraire = None

        # Calcul de l'itinéraire seulement si un changement de point se produit
        if st.sidebar.button("Afficher l'itinéraire"):
            if point_depart != point_arrivee:
                # Vérifie si les points ont changé depuis la dernière fois
                if (st.session_state.get("point_depart") != point_depart or 
                    st.session_state.get("point_arrivee") != point_arrivee):
                    
                    # Enregistre les nouveaux points
                    st.session_state.point_depart = point_depart
                    st.session_state.point_arrivee = point_arrivee

                    # Recherche des coordonnées des points de départ et arrivée
                    coord_depart = df_filtre[df_filtre['nom'] == point_depart][['longitude', 'latitude']].values[0].tolist()
                    coord_arrivee = df_filtre[df_filtre['nom'] == point_arrivee][['longitude', 'latitude']].values[0].tolist()

                    try:
                        # Récupère l'itinéraire depuis l'API OpenRouteService
                        route = client.directions(
                            coordinates=[coord_depart, coord_arrivee],
                            profile='foot-walking',
                            format='geojson'
                        )

                        # Stocke l'itinéraire dans session_state pour ne pas le recalculer
                        st.session_state.itineraire = route
                        
                        # Calcule la distance et la durée
                        distance_m = route['features'][0]['properties']['segments'][0]['distance']
                        duree_s = route['features'][0]['properties']['segments'][0]['duration']
                        distance_km = round(distance_m / 1000, 2)
                        duree_min = round(duree_s / 60)

                        # Affiche la distance et la durée
                        st.success(f"📏 Distance : **{distance_km} km** &nbsp;&nbsp; ⏱️ Durée estimée : **{duree_min} min**")

                    except Exception as e:
                        st.error(f"⚠️ Erreur lors de la génération de l'itinéraire : {e}")

        # 🗺️ Carte
        m = folium.Map(
            location=[df_filtre["latitude"].mean(), df_filtre["longitude"].mean()],
            zoom_start=5,
            tiles="CartoDB positron"
        )

        # 📍 Marqueurs
        icon_mapping = {
            "Loisir": "🎡",
            "Sushi": "🍣",
            "Ramen": "🍜",
            "Hôtel": "🏨",
            "Aéroport": "✈️",
            "Ambassade": "🏛️",
            "Onigiri": "🍙",
            "Tempura": "🍤",
            "Tour": "🗼",
            "Musée": "🏛️",
            "Temple": "🏯",
        }

        for _, row in df_filtre.iterrows():
            icon = icon_mapping.get(row["Type"], "🔵")
            popup_html = f"""
                <div style="width:200px">
                    <h3 style="color: #333; font-size: 16px; margin: 0;">{row['nom']}</h3>
                    <b>{row['adresse']}</b><br>
                    Type : {row['Type']}<br>
            """
            if 'image' in row and pd.notna(row['image']):
                popup_html += f'<img src="{row["image"]}" width="100%" style="margin-top:5px;" />'
            popup_html += "</div>"

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.DivIcon(
                    icon_size=(30, 30),
                    icon_anchor=(15, 15),
                    html=f'<div style="font-size: 24px; color: #333; text-align: center;">{icon}</div>'
                )
            ).add_to(m)

        # ➕ Affichage de l’itinéraire s’il a été calculé
        if st.session_state.get("itineraire"):
            route = st.session_state.itineraire
            folium.GeoJson(
                route,
                name='Itinéraire',
                style_function=lambda x: {
                    'color': 'blue',
                    'weight': 5,
                    'opacity': 0.8
                },
                tooltip=f"Itinéraire : {st.session_state.point_depart} → {st.session_state.point_arrivee}"
            ).add_to(m)

            coord_depart = df_filtre[df_filtre['nom'] == st.session_state.point_depart][['longitude', 'latitude']].values[0].tolist()
            coord_arrivee = df_filtre[df_filtre['nom'] == st.session_state.point_arrivee][['longitude', 'latitude']].values[0].tolist()

            folium.Marker(
                location=coord_depart[::-1],
                icon=folium.Icon(color='green', icon='play', prefix='fa'),
                popup=f"Départ : {st.session_state.point_depart}"
            ).add_to(m)

            folium.Marker(
                location=coord_arrivee[::-1],
                icon=folium.Icon(color='red', icon='stop', prefix='fa'),
                popup=f"Arrivée : {st.session_state.point_arrivee}"
            ).add_to(m)

        # 🎯 Affichage de la carte
        st_folium(m, width=1200, height=700)

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")
