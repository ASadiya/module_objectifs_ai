import streamlit as st
import os

def load_css(file_name):
    """
    Charge un fichier CSS et l'injecte dans Streamlit
    
    Args:
        file_name (str): Nom du fichier CSS (avec ou sans extension)
    
    Returns:
        bool: True si le fichier a été chargé avec succès, False sinon
    """
    try:
        # Ajouter l'extension si elle n'est pas présente
        if not file_name.endswith('.css'):
            file_name += '.css'
        
        # Chemin vers le fichier CSS
        css_path = os.path.join('assets', 'styles', file_name)
        
        # Vérifier si le fichier existe
        if not os.path.exists(css_path):
            st.warning(f"⚠️ Fichier CSS non trouvé : {css_path}")
            return False
        
        # Lire et injecter le CSS
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        st.markdown(f"""
        <style>
        {css_content}
        </style>
        """, unsafe_allow_html=True)
        
        return True
        
    except Exception as e:
        st.error(f"Erreur lors du chargement du CSS : {str(e)}")
        return False

def load_multiple_css(*file_names):
    """
    Charge plusieurs fichiers CSS
    
    Args:
        *file_names: Noms des fichiers CSS à charger
    
    Returns:
        dict: Dictionnaire avec le statut de chargement de chaque fichier
    """
    results = {}
    for file_name in file_names:
        results[file_name] = load_css(file_name)
    return results

def inject_custom_css(css_string):
    """
    Injecte directement du CSS personnalisé
    
    Args:
        css_string (str): Code CSS à injecter
    """
    st.markdown(f"""
    <style>
    {css_string}
    </style>
    """, unsafe_allow_html=True)