# streamlit_page_title: Analyse des objectifs

import streamlit as st
from features_api import assistant_pedagogique, recapitulatif
from pretraitement_obj_spe import nettoyer_objectifs_specifiques
from generation_pdf import generer_pdf, llm_output_to_dict
from style_loader import load_css
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Analyse d'objectifs pédagogiques par IA", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Chargement des styles CSS externes
load_css('styles.css')

# En-tête 
st.markdown("""
<div class="main-header">
    <h1>Analyse automatique d'objectifs pédagogiques</h1>
    <p>Remplissez les informations ci-dessous pour obtenir une analyse personnalisée de vos objectifs pédagogiques.</p>
</div>
""", unsafe_allow_html=True)


if "go" in st.query_params and st.query_params["go"] == "method":
    st.switch_page("pages/details_methode.py")
    
    
st.markdown("""
<div style="border-left: 4px solid #2c7be5; padding: 10px 20px; background-color: #c3cfe241; border-radius: 5px;">
<h4 style = "color: #667eea">Bienvenue sur votre outil d’analyse et d'amélioration des objectifs pédagogiques !</h4>
<p>Cet outil est conçu pour vous aider à évaluer la qualité des objectifs pédagogiques que vous avez formulés pour votre cours, et à les améliorer. <br>Veuillez renseigner chaque champ avec attention : à partir de vos réponses, un conseiller intelligent vous proposera un retour personnalisé et des pistes d’amélioration.<br>
<em>Cela ne prend que quelques minutes !</em><br></p>
<a href="?go=method" style = "font-size: 14px">🔍 Cliquez ici pour en savoir plus sur la méthode d’analyse.</a>
</div>
""", unsafe_allow_html=True)


st.markdown("<br>", unsafe_allow_html=True)

with st.form("formulaire_objectifs"):

    nom_cours = st.text_input("Nom du cours", placeholder="ex: Introduction à l'intelligence artificielle")
    st.info("🔸 Le nom du cours doit contenir au moins 5 caractères.")

    niveau = st.text_input("Niveau du cours", placeholder="ex: Licence 3")
    st.info("🔸 Le niveau du cours doit contenir au moins 2 caractères.")

    public = st.text_input("Public cible", placeholder="ex: Étudiants en Intelligence Artificielle")
    st.info("🔸 Le public cible doit contenir au moins 5 caractères.")

    objectif_general = st.text_area("Objectif général du cours")
    st.info("🔸 L'objectif pédagogique général du cours doit contenir au moins 20 caractères.")

    objectifs_specifiques_brut = st.text_area("Objectifs spécifiques")
    st.info("🔸 Les objectifs pédagogiques spécifiques doivent contenir au moins 20 caractères.")
    
    soumis = st.form_submit_button("Analyser", use_container_width=True)

if soumis:
    st.success("✅ Formulaire envoyé avec succès !")
    
    # Nettoyage et transformation des objectifs spécifiques en liste
    objectifs_specifiques = nettoyer_objectifs_specifiques(objectif_general, objectifs_specifiques_brut)
    st.info("✅ Données valides, lancement de l'analyse...")
    
    with st.spinner('Analyse en cours, veuillez patienter...'):
        try:
            # Appel du pipeline principal
            rapport = assistant_pedagogique(nom_cours, niveau, public, objectif_general, objectifs_specifiques)
        
            st.success("Analyse terminée avec succès !")
        except Exception as e:
            st.error(f"Une erreur est survenue pendant l'analyse. Veuillez réessayer.")
            logger.warning(f"Une erreur est survenue pendant l'analyse. : {str(e)}")
            st.stop()


    # Récapitulatif
    try:
        recap = recapitulatif(rapport['details'])
        logger.info("Récapitulatif fait !")
    except Exception as e:
        st.error(f"Un problème est survenu pendant l'analyse. Veuillez réessayer.")
        logger.warning(f"Le récapitulatif a échoué : {str(e)}")

    try:
        recap_dict = llm_output_to_dict(recap)
        logger.info("Conversion du récapitulatif faite.")
    except Exception as e:
        st.error(f"Un problème est survenu pendant le récapitulatif de l'analyse. Veuillez réessayer.")
        logger.warning(f"La conversion du récapitulatif a échouée : {str(e)}")

    # Séparation visuelle
    st.markdown("---")
    
    # Section résultats améliorée
    st.markdown("## Résultats de l'analyse")
    
    # Métriques en colonnes
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-titre" style="font-size: 15px">📚 Cours analysé</div>
            <p style="font-size: 20px;">{nom_cours}</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-titre" style="font-size: 15px">🎯 Niveau</div>
            <p style="font-size: 20px;">{niveau}</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-titre" style="font-size: 15px">👥 Public cible</div>
            <p style="font-size: 20px;">{public}</p>
        </div>""", unsafe_allow_html=True)


    # Synthèse dans une boîte stylisée
    st.markdown("""
    <div class="resultats-section">
        <h3>Aperçu global</h3>
    </div>""", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="synthese-box">
        <h4>📄 Résumé de l'analyse</h4>
        <p style="font-size: 16px; line-height: 1.6; margin-bottom: 0;">{rapport["aperçu"]}</p>
    </div>
    """, unsafe_allow_html=True)

    # Rapport détaillé avec onglets
    st.markdown("""
    <div class="resultats-section">
        <h3>Rapport détaillé</h3>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    /* Texte des onglets (non actifs) */
    .stTabs [data-baseweb="tab"] {
        color: #666666;
    }

    /* Onglet actif : texte et soulignement */
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #667eea !important;
    }
    </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Rapport complet", "💡 Points clés", "📈 Recommandations"])
    
    with tab1:
        st.markdown(f"""
        <div class="rapport-section">
            {rapport["details"]}
        </div>
        """, unsafe_allow_html=True)
    
    if not(isinstance(recap_dict, dict)):
        logger.warning("Le récapitulatif n'est pas un dictionnaire valide.")
        #st.stop()  
        
        with tab2:
            # Extraction des points clés
            st.markdown("#### Points importants identifiés")
            st.info("Cette section présente les points clés du rapport.")
            st.error("Le récapitulatif n'a pas pu être généré correctement.")
            
        with tab3:
            st.markdown("#### Suggestions d'amélioration")
            st.info("Cette section présente les recommandations prioritaires.")
                        
            with st.container():
                st.markdown("**Recommandations prioritaires :**")
                st.error("Le récapitulatif n'a pas pu être généré correctement.")
        
    else:    
        with tab2:
            # Extraction des points clés
            st.markdown("#### Points importants identifiés")
            st.info("Cette section présente les points clés du rapport.")
            
            col1, col2 = st.columns(2)
                
            points_forts = recap_dict.get('points_forts', []) 
            axes_amelioration = recap_dict.get('axes_amelioration', [])

            with col1:
                st.markdown("**✅ Points forts détectés :**")
                if points_forts:
                    for point in points_forts:
                        st.markdown(f"- {point}")
                else:
                    st.markdown("_Aucun point fort détecté._")

            with col2:
                st.markdown("**⚠️ Axes d'amélioration :**")
                if axes_amelioration:
                    for point in axes_amelioration:
                        st.markdown(f"- {point}")
                else:
                    st.markdown("_Aucun axe d'amélioration détecté._")
            
        with tab3:
            st.markdown("#### Suggestions d'amélioration")
            st.info("Cette section présente les recommandations prioritaires.")
            
            recommandation = recap_dict.get('recommandations', [])
            
            with st.container():
                st.markdown("**Recommandations prioritaires :**")
                if recommandation:
                    for point in recommandation:
                        st.markdown(f"- {point}")
                else:
                    st.markdown("_Aucune recommandation détectée._")

    # Avertissement IA 
    st.markdown("""
    <div class="info-banner">
        <h5>⚠ Important : Utilisation de l'IA</h5>
        <p style="margin-bottom: 0;">
        Ces recommandations sont générées automatiquement par un système d'intelligence artificielle. 
        Elles visent à guider, non à remplacer l'expertise pédagogique humaine, et doivent être examinées avec discernement avant toute utilisation.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Section téléchargement stylisée
    st.markdown("### 📥 Télécharger le rapport")
    st.markdown(" ")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Génération de PDF temporaire
        chemin_pdf = generer_pdf(nom_cours, niveau, public, objectif_general, objectifs_specifiques_brut, rapport, recap_dict)
        with open(chemin_pdf, "rb") as f:
            st.download_button(
                "📄 Télécharger le rapport PDF", 
                f, 
                file_name=f"rapport_analyse_objectifs_{nom_cours.replace(' ', '_').lower()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: gray;'>🤖 Analyse générée par IA • Développé pour l'amélioration pédagogique</p>", 
        unsafe_allow_html=True
    )