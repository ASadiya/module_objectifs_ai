# streamlit_page_title: Méthode d’analyse

import streamlit as st

st.set_page_config(
    page_title="Méthode d’analyse")

st.title("📘 Méthode d’analyse utilisée")

st.markdown(" ")
st.markdown("""
Notre assistant intelligent procède à une analyse en plusieurs étapes pour évaluer et améliorer vos objectifs pédagogiques :

---

### 1. **Classification selon la taxonomie de Bloom**
Une fiche explicative consacrée à la taxonomie révisée de Bloom, enrichie d’une base de données regroupant des verbes d’action classés selon les six niveaux hiérarchiques de cette taxonomie, permet de catégoriser rigoureusement chaque objectif pédagogique selon le niveau cognitif visé :
- Connaître
- Comprendre
- Appliquer
- Analyser
- Évaluer
- Créer

Cela permet de :
- Déterminer le niveau cognitif visé ;
- Détecter les incohérences entre les verbes et le niveau annoncé.

### 2. **Évaluation multicritère**
Chaque objectif est évalué selon plusieurs critères basé sur le modèle SMART adapté au domaine pédagogique. En effet, pour être considéré comme pertinent et rigoureux, un objectif pédagogique doit satisfaire aux critères suivants :
- **Spécifique :** L’objectif doit être clairement formulé, sans ambiguïté, à l’aide d’un vocabulaire compréhensible par les apprenant·es. Il précise des comportements observables dans un contexte donné.
- **Mesurable :** Il doit permettre une évaluation fiable des apprentissages à travers l’usage de verbes d’action observables. Un seul verbe d’action est recommandé (sauf pour l’objectif général) afin d’éviter les formulations floues ou trop larges.
- **Approprié (Cohérent) :** L’objectif doit être en adéquation avec le contenu du cours, le niveau d’étude, les caractéristiques du public cible, le programme et l’objectif général. Un objectif spécifique ne doit pas excéder le niveau taxonomique de l’objectif général.
- **Réaliste :** L’objectif doit pouvoir être atteint dans le cadre temporel et matériel du cours.
- **Temporellement défini :** Il doit comporter une indication temporelle claire (durée, échéance ou jalons). 

Ainsi que sur des règles de rédaction. 
Une note sur 5 est attribuée pour chaque critère.

### 3. **Amélioration des objectifs**
En cas de non-conformité, des suggestions d’amélioration personnalisées sont générées automatiquement selon les bonnes pratiques pédagogiques.

### 4. **Synthèse**
Une rapport structuré permet de visualiser :
- un aperçu global des résultats
- une analyse détaillée
- ainsi que des tableaux récapitulatifs.

---
""")

st.markdown("---")
st.markdown(
    "<a href='/' style='font-size: 14px;'>⬅️ Retour au formulaire principal</a>",
    unsafe_allow_html=True
)

