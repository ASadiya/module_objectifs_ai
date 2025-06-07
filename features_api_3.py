import os
import streamlit as st
from mistralai import Mistral
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")

model = "mistral-large-latest"

@st.cache_resource
def get_client():
  return Mistral(api_key=api_key)

@st.cache_data(show_spinner=False)
def appeler_api_cached(prompt, system_prompt):
  client = get_client()
  chat_response = client.chat.complete(
    model= model,
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
)
  return chat_response.choices[0].message.content

def appeler_api(prompt, system_prompt="Tu es un expert en pédagogie universitaire."):
    logger.info("Appel de l'API Mistral...")
    try:
        response = appeler_api_cached(prompt, system_prompt)
        logger.info("Réponse reçue avec succès.")
        return response
    except Exception as e:
        logger.error(f"Erreur lors de l'appel API : {e}", exc_info=True)
        return "❌ Une erreur est survenue lors de l'appel à l'IA."


# Features

# Classification selon le niveau de Bloom

@st.cache_data(show_spinner=False)
def classifier_objectifs(objectif_general, objectifs_specifiques):
  base_connaissances = """
    Tu es un expert en pédagogie universitaire, chargé d'assister les enseignants dans la constitution d'objectifs pédagogiques optimaux pour leurs cours.
    Voici la taxonomie de Bloom et ses niveaux, du niveau inférieur au niveau supérieur, avec l'explication du niveau et des exemples de verbes d'action pour libeller les objectifs correspondants à chacun de ces niveaux :
      Connaître :
        Explication : Restituer avec justesse l’information ou procédure apprise. Collecter de l’information, la mémoriser, l’identifier, la reconnaître, la discriminer.
        Verbes : Assigner, associer, caractériser, cataloguer, citer, collecter, décrire, définir, délimiter, désigner, déterminer, enregistrer, énumérer, établir, étiqueter, examiner, expérimenter, identifier, indiquer, inventorier, lister, mémoriser, montrer, localiser, nommer, ordonner, rappeler, réciter, répéter, reconnaître, reproduire, sélectionner, situer, etc.
      Comprendre :
        Explication : Interpréter ou décrire des informations. Expliquer un concept de manière intelligible. Synthétiser un sujet. Expliciter un raisonnement. Illustrer des arguments.
        Verbes : Associer, classer, comparer, compléter, conclure, contextualiser, convertir, décrire, démontrer, déterminer, différencier, dire dans ses mots, discuter, distinguer, estimer, établir, expliquer, exprimer, extrapoler, faire une analogie, généraliser, identifier, illustrer (à l’aide d’exemples), inférer, interpréter, localiser, ordonner, paraphraser, préciser, prédire, préparer, rapporter, réarranger, redéfinir, réécrire, reformuler, regrouper, réorganiser, représenter, résumer, sélectionner, schématiser, situer, traduire, etc.
      Appliquer :
        Explication : Résoudre des problèmes en suivant une procédure établie. Calculer. Appliquer une méthode. Accomplir une tâche selon des règles. Manifester une attitude adéquate.
        Verbes : Acter, adapter, administrer, appliquer, assembler, calculer, choisir, classer, classifier, compléter, construire, contrôler, découvrir, démontrer, dessiner, déterminer, développer, employer, établir, exécuter, expérimenter, formuler, fournir, généraliser, gérer, illustrer, implanter, informer, interpréter, jouer, manipuler, mesurer, mettre en pratique, modifier, montrer, opérer, organiser, participer, planifier, pratiquer, préparer, produire, rédiger, relier, résoudre, restructurer, schématiser, simuler, traiter, transférer, trouver, utiliser, etc.
      Analyser :
        Explication : Résoudre des problèmes. Repérer les éléments d’une situation et comprendre leurs relations. Examiner des faits en isolant les causes. Interpréter des données. Percevoir des tendances.
        Verbes : Analyser, arranger, attribuer, catégoriser, choisir, classer, cibler, comparer, contraster, corréler, critiquer, décomposer, découper, déduire, délimiter, détecter, différencier, discriminer, disséquer, distinguer, diviser, examiner, expérimenter, expliquer, faire corréler, faire ressortir, générer, identifier, inférer, interpréter, limiter, mettre en priorité, mettre en relation, modéliser, morceler, nuancer, organiser, opposer, questionner, rechercher, relier, séparer, subdiviser, tester, etc.
      Évaluer :
        Explication : Porter un jugement critique personnel fondé sur des critères variés. Valider des théories. Analyser une situation afin de prendre des décisions et de les justifier.
        Verbes : Apprécier, appuyer, argumenter, attaquer, choisir, classer, comparer, conclure, considérer, contraster, contrôler, convaincre, critiquer, décider, déduire, défendre, déterminer, estimer, évaluer, expliquer, juger, justifier, mesurer, noter, persuader, prédire, produire, recadrer, recommander, résumer, sélectionner, soupeser, soutenir, standardiser, tester, valider, vérifier, etc.
      Créer :
        Explication : Mobiliser ses apprentissages pour former un tout cohérent et nouveau. Générer de nouvelles idées. Produire une œuvre personnelle. Créer une production originale. Élaborer un plan d’action personnalisé.
        Verbes : Adapter, agencer, anticiper, arranger, assembler, classer, collecter, combiner, commenter, composer, concevoir, constituer, construire, créer, déduire, dériver, développer, discuter, écrire, élaborer, exposer, formuler, généraliser, générer, imaginer, incorporer, innover, intégrer, inventer, mettre en place, modifier, organiser, planifier, préparer, produire, projeter, proposer, raconter, relater, rédiger, réorganiser, schématiser, structurer, substituer, synthétiser, transmettre, etc.
    """

  prompt = f"""
    {base_connaissances}

    Objectif général : {objectif_general}

    Objectifs spécifiques :
    {chr(10).join(f"- {obj}" for obj in objectifs_specifiques)}

    Instruction : 
        Tu es un expert en ingénierie pédagogique. Ta mission est de classer chaque objectif pédagogique fourni, général comme spécifique, selon les niveaux de la taxonomie de Bloom (connaître, comprendre, appliquer, analyser, évaluer, créer).

        Si un verbe peut correspondre à plusieurs niveaux de Bloom, utilise la DESCRIPTION COMPLETE DE L'OBJECTIF pour déterminer le bon niveau.  
        Dans le cas d’un OBJECTIF GENERAL, prends aussi en compte les objectifs spécifiques associés pour affiner la classification.

  """

  return appeler_api(prompt)



# Evaluation des objectifs

@st.cache_data(show_spinner=False)
def evaluer_objectifs(nom_cours, niveau, public, objectif_general, bloom_classification):
  base_connaissances = """
Tu es un expert en pédagogie universitaire, chargé d'assister les enseignants dans la constitution d'objectifs pédagogiques optimaux pour leurs cours.

## CRITÈRES D'ÉVALUATION (SMART+C) :
- **Spécifique**: L'objectif doit être clair et précis, formulé de manière explicite, sans ambiguïté, évitant les généralités et avec un vocabulaire compréhensible par les étudiant.es.
- **Mesurable**: Il doit utiliser des verbes d'action observables (ex. : analyser, comparer, rédiger), évitant les termes vagues (ex. : comprendre, savoir).
- **Approprié (Cohérent)**: L'objectif doit être pertinent et cohérent avec le niveau d'étude, le public cible, le programme et l'objectif général.
- **Réaliste**: L'objectif doit être réalisable dans le temps imparti et avec les ressources disponibles.
- **Temporellement défini**: L'objectif doit avoir un échéancier clair (Au terme de..., À la fin de..., etc.).
- **Complétude**: L'ensemble des objectifs spécifiques doit permettre de réaliser l'objectif général.

## RÈGLES DE RÉDACTION OBLIGATOIRES :
**STRUCTURE IMPÉRATIVE** : [Délai] + L'apprenant·e sera capable de + [UN SEUL verbe d'action] + [Contenu] + [Contexte]

**RÈGLES CRITIQUES À VÉRIFIER SYSTÉMATIQUEMENT** :
1. **UN SEUL VERBE D'ACTION PAR OBJECTIF** - JAMAIS plusieurs verbes
2. **Centré sur l'apprenant** : "L'apprenant·e sera capable de..." (PAS "Le cours permet de...")
3. **Délai explicite** : "Au terme de...", "À la fin de...", "À l'issue de..."
4. **Verbe observable** : Éviter "comprendre", "connaître", "maîtriser"
5. **Contexte précis** : Conditions, matériel, niveau d'exigence

## TAXONOMIE DE BLOOM (ordre croissant de complexité) :
1. Se souvenir (mémoriser, reconnaître, identifier...)
2. Comprendre (expliquer, résumer, interpréter...)
3. Appliquer (utiliser, exécuter, mettre en œuvre...)
4. Analyser (différencier, organiser, décomposer...)
5. Évaluer (critiquer, juger, justifier...)
6. Créer (concevoir, produire, planifier...)
"""
  
  prompt = f"""
{base_connaissances}

## INFORMATIONS DU COURS :
- Nom du cours : {nom_cours}
- Niveau : {niveau}
- Public : {public}
- Objectif général : {objectif_general}
- Classification Bloom : {bloom_classification}

## MISSION :
Effectue une évaluation RIGOUREUSE en deux phases :

### PHASE 1 : VÉRIFICATION DES RÈGLES DE RÉDACTION
Pour chaque objectif, vérifie OBLIGATOIREMENT :
✓ Structure : [Délai] + L'apprenant·e sera capable de + [UN SEUL verbe] + [Contenu] + [Contexte]
✓ Un seul verbe d'action (si plusieurs verbes → ERREUR CRITIQUE)
✓ Centré sur l'apprenant (pas sur le cours)
✓ Délai explicite présent
✓ Verbe observable et mesurable

### PHASE 2 : ÉVALUATION DES CRITÈRES SMART+C
Pour chaque objectif :

**Objectif [numéro] :** [objectif complet]
- **Niveau Bloom :** [niveau]
- **Conformité règles de rédaction :** [CONFORME/NON-CONFORME + justification détaillée]
- **Spécifique :** [analyse] Note : [1-5]
- **Mesurable :** [analyse] Note : [1-5]
- **Approprié (Cohérent) :** [analyse incluant cohérence avec le nom du cours "{nom_cours}"] Note : [1-5]
- **Réaliste :** [analyse] Note : [1-5]
- **Temporellement défini :** [analyse] Note : [1-5]

⚠️ **ALERTES CRITIQUES À SIGNALER** :
- Objectifs avec plusieurs verbes d'action
- Incohérence flagrante entre nom de cours et objectifs
- Objectifs spécifiques de niveau Bloom supérieur à l'objectif général
- Formulations centrées sur l'enseignant au lieu de l'apprenant

### COMPLÉTUDE GLOBALE :
[Évaluation de la complétude] Note : [1-5]

### RÉCAPITULATIF DES NOTES :
[Format standard avec alertes critiques en tête si présentes]
"""

  return appeler_api(prompt)

@st.cache_data(show_spinner=False)
def auto_eval_evaluation(evaluation):
  base_connaissances = """
Tu es un expert en pédagogie universitaire, chargé d'assister les enseignants dans la constitution d'objectifs pédagogiques optimaux pour leurs cours.

## CRITÈRES D'ÉVALUATION (SMART+C) :
- **Spécifique**: L'objectif doit être clair et précis, formulé de manière explicite, sans ambiguïté, évitant les généralités et avec un vocabulaire compréhensible par les étudiant.es.
- **Mesurable**: Il doit utiliser des verbes d'action observables (ex. : analyser, comparer, rédiger), évitant les termes vagues (ex. : comprendre, savoir).
- **Approprié (Cohérent)**: L'objectif doit être pertinent et cohérent avec le niveau d'étude, le public cible, le programme et l'objectif général.
- **Réaliste**: L'objectif doit être réalisable dans le temps imparti et avec les ressources disponibles.
- **Temporellement défini**: L'objectif doit avoir un échéancier clair (Au terme de..., À la fin de..., etc.).
- **Complétude**: L'ensemble des objectifs spécifiques doit permettre de réaliser l'objectif général.

## RÈGLES DE RÉDACTION OBLIGATOIRES :
**STRUCTURE IMPÉRATIVE** : [Délai] + L'apprenant·e sera capable de + [UN SEUL verbe d'action] + [Contenu] + [Contexte]

**RÈGLES CRITIQUES À VÉRIFIER SYSTÉMATIQUEMENT** :
1. **UN SEUL VERBE D'ACTION PAR OBJECTIF** - JAMAIS plusieurs verbes
2. **Centré sur l'apprenant** : "L'apprenant·e sera capable de..." (PAS "Le cours permet de...")
3. **Délai explicite** : "Au terme de...", "À la fin de...", "À l'issue de..."
4. **Verbe observable** : Éviter "comprendre", "connaître", "maîtriser"
5. **Contexte précis** : Conditions, matériel, niveau d'exigence

## TAXONOMIE DE BLOOM (ordre croissant de complexité) :
1. Se souvenir (mémoriser, reconnaître, identifier...)
2. Comprendre (expliquer, résumer, interpréter...)
3. Appliquer (utiliser, exécuter, mettre en œuvre...)
4. Analyser (différencier, organiser, décomposer...)
5. Évaluer (critiquer, juger, justifier...)
6. Créer (concevoir, produire, planifier...)
"""

  prompt = f"""
{base_connaissances}

Tu es un expert en pédagogie universitaire. Tu dois vérifier et améliorer cette évaluation d'objectifs pédagogiques.

## POINTS DE VIGILANCE PRIORITAIRES :
1. **Règles de rédaction** : L'évaluation a-t-elle bien détecté les violations (multiple verbes, structure incorrecte) ?
2. **Cohérence thématique** : Les incohérences entre nom de cours et objectifs sont-elles identifiées ?
3. **Rigueur taxonomique** : La classification Bloom est-elle correcte ?
4. **Notation justifiée** : Les notes correspondent-elles aux commentaires ?

## ÉVALUATION À VÉRIFIER :
{evaluation}

## MISSION :
1. Identifie les erreurs d'analyse (notamment sur règles de rédaction et cohérence)
2. Corrige l'évaluation en gardant EXACTEMENT le même format
3. Ajoute des alertes critiques si des problèmes graves ont été manqués

# Version révisée (même format) :
"""
  return appeler_api(prompt)


# Améliorations et recommandations

@st.cache_data(show_spinner=False)
def ameliorer_objectifs(nom_cours, niveau, public, objectif_general, evaluation_objectifs):
  base_connaissances = """
Tu es un expert en pédagogie universitaire, chargé d'assister les enseignants dans la constitution d'objectifs pédagogiques optimaux pour leurs cours.

## CRITÈRES D'ÉVALUATION (SMART+C) :
- **Spécifique**: L'objectif doit être clair et précis, formulé de manière explicite, sans ambiguïté, évitant les généralités et avec un vocabulaire compréhensible par les étudiant.es.
- **Mesurable**: Il doit utiliser des verbes d'action observables (ex. : analyser, comparer, rédiger), évitant les termes vagues (ex. : comprendre, savoir).
- **Approprié (Cohérent)**: L'objectif doit être pertinent et cohérent avec le niveau d'étude, le public cible, le programme et l'objectif général.
- **Réaliste**: L'objectif doit être réalisable dans le temps imparti et avec les ressources disponibles.
- **Temporellement défini**: L'objectif doit avoir un échéancier clair (Au terme de..., À la fin de..., etc.).
- **Complétude**: L'ensemble des objectifs spécifiques doit permettre de réaliser l'objectif général.

## RÈGLES DE RÉDACTION OBLIGATOIRES :
**STRUCTURE IMPÉRATIVE** : [Délai] + L'apprenant·e sera capable de + [UN SEUL verbe d'action] + [Contenu] + [Contexte]

**RÈGLES CRITIQUES À VÉRIFIER SYSTÉMATIQUEMENT** :
1. **UN SEUL VERBE D'ACTION PAR OBJECTIF** - JAMAIS plusieurs verbes
2. **Centré sur l'apprenant** : "L'apprenant·e sera capable de..." (PAS "Le cours permet de...")
3. **Délai explicite** : "Au terme de...", "À la fin de...", "À l'issue de..."
4. **Verbe observable** : Éviter "comprendre", "connaître", "maîtriser"
5. **Contexte précis** : Conditions, matériel, niveau d'exigence

## TAXONOMIE DE BLOOM (ordre croissant de complexité) :
1. Se souvenir (mémoriser, reconnaître, identifier...)
2. Comprendre (expliquer, résumer, interpréter...)
3. Appliquer (utiliser, exécuter, mettre en œuvre...)
4. Analyser (différencier, organiser, décomposer...)
5. Évaluer (critiquer, juger, justifier...)
6. Créer (concevoir, produire, planifier...)
"""

  prompt = f"""
{base_connaissances}

## CONTEXTE :
- Nom du cours : {nom_cours}
- Niveau : {niveau}
- Public : {public}
- Objectif général : {objectif_general}

## ÉVALUATION DÉTAILLÉE :
{evaluation_objectifs}

## MISSION D'AMÉLIORATION :
Sur la base de l'évaluation, pour chaque objectif nécessitant des améliorations, propose des recommandations PRIORITAIRES :

### PRIORITÉ 1 - CONFORMITÉ AUX RÈGLES DE RÉDACTION :
Si l'objectif viole les règles de rédaction :
- **Réécriture obligatoire** respectant la structure [Délai] + L'apprenant·e sera capable de + [UN SEUL verbe] + [Contenu] + [Contexte]
- **Correction des verbes multiples** : séparer en objectifs distincts ou choisir le verbe principal
- **Amélioration du verbe** si non observable

### PRIORITÉ 2 - COHÉRENCE THÉMATIQUE :
Si incohérence avec le nom du cours :
- **Réalignement** avec la thématique "{nom_cours}"
- **Justification** du lien avec le domaine d'étude

### PRIORITÉ 3 - OPTIMISATION CRITÈRES SMART :
Améliorations sur spécificité, mesurabilité, réalisme, temporalité

## FORMAT DE SORTIE :

#### Objectif général :
[objectif_general]
[Analyse selon le format standard]

#### Objectifs spécifiques :

**Objectif [numéro] :** [objectif original]
[Analyse complète]

**Recommandations prioritaires :**
- **Règles de rédaction :** [corrections structure/verbes] 
- **Cohérence :** [réalignement thématique si nécessaire]
- **SMART :** [améliorations critères]

**Objectif réécrit proposé :**
"[Nouvelle version corrigée respectant toutes les règles]"

[Répéter pour tous les objectifs]

**Complétude globale :** [Analyse] Note : [X/5]

### RÉSUMÉ EXÉCUTIF :
- **Alertes critiques résolues :** [liste des corrections majeures]
- **Améliorations apportées :** [synthèse des optimisations]
- **Récapitulatif des notes finales :** [après améliorations]
"""

  return appeler_api(prompt)

@st.cache_data(show_spinner=False)
def auto_eval_suggestions(suggestions):
  base_connaissances = """
Tu es un expert en pédagogie universitaire, chargé d'assister les enseignants dans la constitution d'objectifs pédagogiques optimaux pour leurs cours.

## CRITÈRES D'ÉVALUATION (SMART+C) :
- **Spécifique**: L'objectif doit être clair et précis, formulé de manière explicite, sans ambiguïté, évitant les généralités et avec un vocabulaire compréhensible par les étudiant.es.
- **Mesurable**: Il doit utiliser des verbes d'action observables (ex. : analyser, comparer, rédiger), évitant les termes vagues (ex. : comprendre, savoir).
- **Approprié (Cohérent)**: L'objectif doit être pertinent et cohérent avec le niveau d'étude, le public cible, le programme et l'objectif général.
- **Réaliste**: L'objectif doit être réalisable dans le temps imparti et avec les ressources disponibles.
- **Temporellement défini**: L'objectif doit avoir un échéancier clair (Au terme de..., À la fin de..., etc.).
- **Complétude**: L'ensemble des objectifs spécifiques doit permettre de réaliser l'objectif général.

## RÈGLES DE RÉDACTION OBLIGATOIRES :
**STRUCTURE IMPÉRATIVE** : [Délai] + L'apprenant·e sera capable de + [UN SEUL verbe d'action] + [Contenu] + [Contexte]

**RÈGLES CRITIQUES À VÉRIFIER SYSTÉMATIQUEMENT** :
1. **UN SEUL VERBE D'ACTION PAR OBJECTIF** - JAMAIS plusieurs verbes
2. **Centré sur l'apprenant** : "L'apprenant·e sera capable de..." (PAS "Le cours permet de...")
3. **Délai explicite** : "Au terme de...", "À la fin de...", "À l'issue de..."
4. **Verbe observable** : Éviter "comprendre", "connaître", "maîtriser"
5. **Contexte précis** : Conditions, matériel, niveau d'exigence

## TAXONOMIE DE BLOOM (ordre croissant de complexité) :
1. Se souvenir (mémoriser, reconnaître, identifier...)
2. Comprendre (expliquer, résumer, interpréter...)
3. Appliquer (utiliser, exécuter, mettre en œuvre...)
4. Analyser (différencier, organiser, décomposer...)
5. Évaluer (critiquer, juger, justifier...)
6. Créer (concevoir, produire, planifier...)
"""

  prompt = f"""
{base_connaissances}

Tu es un expert en ingénierie pédagogique. Tu dois vérifier et parfaire ces suggestions d'amélioration d'objectifs pédagogiques.

## POINTS DE CONTRÔLE OBLIGATOIRES :
✓ **Règles de rédaction** : Chaque objectif réécrit respecte-t-il la structure obligatoire ?
✓ **Verbe unique** : Aucun objectif amélioré ne contient plusieurs verbes d'action ?
✓ **Cohérence thématique** : Les objectifs sont-ils alignés avec le domaine du cours ?
✓ **Progression Bloom** : La hiérarchie taxonomique est-elle respectée ?
✓ **Qualité pédagogique** : Les améliorations sont-elles pertinentes et réalistes ?

## SUGGESTIONS À ÉVALUER :
{suggestions}

## MISSION :
1. Vérifie que TOUTES les règles de rédaction sont respectées dans les objectifs réécrits
2. Contrôle la cohérence thématique de chaque objectif amélioré
3. Valide la progression taxonomique
4. Corrige si nécessaire en gardant le MÊME FORMAT exact

⚠️ **ATTENTION PARTICULIÈRE** : Si un objectif réécrit contient encore plusieurs verbes ou une incohérence thématique, c'est une ERREUR CRITIQUE à corriger absolument.

# Version finale révisée (même format) :
"""
  return appeler_api(prompt)


@st.cache_data(show_spinner=False)
def synthese(nom_cours, niveau, public, rapport):
  """ (Ancienne version)
  prompt = f""" """
    Tu es un expert pédagogique chargé de résumer un rapport d’analyse des objectifs pédagogiques d’un cours.

    Voici les informations du cours : 
    Cours : {nom_cours}
    Niveau : {niveau}
    Public cible : {public}
    
    Voici le rapport complet à analyser : 
    {rapport}

    Ta tâche est de produire une synthèse claire, concise et structurée, destinée à un enseignant ou responsable pédagogique. 
    Cette synthèse doit :
    - Résumer en quelques phrases l’objectif général du cours,
    - Mentionner brièvement le public cible et le niveau,
    - Mettre en avant les points clés des objectifs spécifiques, en indiquant leurs forces et leurs faiblesses principales (ex : clarté, mesurabilité, réalisme, temporalité),
    - Signaler les recommandations les plus importantes sans entrer dans tous les détails,
    - Être rédigée de manière fluide, synthétique et accessible, sur environ 5 à 10 phrases.
    Ne reproduis pas l’intégralité du rapport détaillé, mais fournis un aperçu qui donne envie de lire la section détaillée complète.

    ---

    Format de sortie attendu : un texte en deux ou trois paragraphes, simple, sans listes ni tableaux, clair et professionnel.

    ---

    Exemple de début de synthèse :
    "
    Le cours « **Méthodes d'analyse et de spécification** », destiné à des étudiants de Licence 3 en Intelligence Artificielle, vise à fournir les compétences essentielles pour la maîtrise des méthodologies d’analyse et conception des systèmes logiciels. 

    L’objectif général est clairement défini et les objectifs spécifiques sont majoritairement bien formulés, avec une bonne adéquation au public cible. 

    Cependant, certaines recommandations pointent un manque de précisions temporelles et de ressources explicites pour garantir la réalisation complète des objectifs. La synthèse des notes souligne un besoin d’amélioration dans la définition des délais et des techniques précises à utiliser..."

    ---
    Merci de produire uniquement la synthèse, sans autre ajout.
    """
  
  prompt = f"""
  Tu es un expert pédagogique chargé de résumer un rapport d'analyse des objectifs pédagogiques d'un cours.

  Voici les informations du cours :
  Cours : {nom_cours}
  Niveau : {niveau}
  Public cible : {public}

  Voici le rapport complet à analyser :
  {rapport}

  Ta tâche est de produire une synthèse claire, concise et structurée, destinée à un enseignant ou responsable pédagogique.

  Cette synthèse doit :
  - Résumer en une phrase l'objectif général du cours,
  - Mentionner brièvement le public cible et le niveau,
  - Évaluer la cohérence globale entre l'objectif général, les objectifs spécifiques, le niveau d'étude et le public cible (cohérence thématique, pédagogique et curriculaire),
  - Donner une appréciation générale du niveau de qualité des objectifs (excellent/bon/satisfaisant/à améliorer),
  - Mettre en avant les points clés des objectifs spécifiques selon les critères SMART+ (Spécifique, Mesurable, Approprié/Cohérent, Réaliste, Temporellement défini), en indiquant leurs forces et faiblesses principales,
  - Signaler les 2-3 recommandations les plus critiques pour l'amélioration des objectifs,
  - Être rédigée dans un ton constructif et professionnel, mettant l'accent sur les améliorations possibles plutôt que sur les défauts,
  - Être rédigée de manière fluide, synthétique et accessible, sur environ 5 à 10 phrases.

  Ne reproduis pas l'intégralité du rapport détaillé, mais fournis un aperçu qui donne envie de lire la section détaillée complète.

  ---

  Format de sortie attendu : un texte en deux ou trois paragraphes, simple, sans listes ni tableaux, clair et professionnel.

  ---

  Exemple de début de synthèse :
  "
  Le cours « **Méthodes d'analyse et de spécification** », destiné à des étudiants de Licence 3 en Intelligence Artificielle, vise à fournir les compétences essentielles pour la maîtrise des méthodologies d'analyse et conception des systèmes logiciels. L'ensemble présente une bonne cohérence thématique entre l'objectif général et les objectifs spécifiques, avec un niveau d'exigence adapté au public de L3.

  L'analyse SMART+ révèle un niveau **satisfaisant** avec un objectif général clairement défini et des objectifs spécifiques majoritairement bien formulés, montrant une bonne adéquation au public cible et une mesurabilité appropriée. Cependant, les critères temporels et de réalisme présentent des lacunes significatives qui méritent attention.

  Les recommandations prioritaires portent sur la précision des échéanciers d'apprentissage, l'explicitation des ressources nécessaires et l'ajout de contextes spécifiques pour certains objectifs. Ces améliorations permettraient d'optimiser la faisabilité et l'évaluation des apprentissages visés.
  "

  ---

  Merci de produire uniquement la synthèse, sans autre ajout.
  """
  return appeler_api(prompt)



# Fonction principale

def assistant_pedagogique(nom_cours, niveau, public, objectif_general, objectifs_specifiques):
  logger.info("Début de l'analyse pédagogique pour le cours : %s", nom_cours)

  try:
    # Classification selon Bloom
    logger.info("Étape 1 : Classification selon Bloom")
    st.info("Classification selon la taxonomie révisée de Bloom...")
    bloom_classification = classifier_objectifs(objectif_general, objectifs_specifiques)

    # Évaluation des objectifs
    logger.info("Étape 2 : Évaluation des objectifs")
    st.info("Évaluation des objectifs...")
    evaluations = evaluer_objectifs(nom_cours, niveau, public, objectif_general, bloom_classification)
    evaluations_revisees = auto_eval_evaluation(evaluations)

    # Recommandations
    logger.info("Étape 3 : Génération de recommandations")
    st.info("Génération de recommandations...")

    suggestions = ameliorer_objectifs(nom_cours, niveau, public, objectif_general, evaluations_revisees)
    suggestions_revisees = auto_eval_suggestions(suggestions)

    logger.info("Étape 4 : Génération du rapport final")
    st.info("Génération du rapport...")
    
    rapport = f"""
      {suggestions_revisees}
      """
    resultat_final = {
      "informations_cours": f"""
        **Cours :** {nom_cours}
        **Niveau :** {niveau}
        **Public cible :** {public} 
        **Objectif général :** 
          {objectif_general}
        **Objectifs specifiques :** 
          {objectifs_specifiques}
        """,
      "aperçu": synthese(nom_cours, niveau, public, rapport),
      "details": rapport
    }
    
    logger.info("Analyse terminée avec succès.")
    return resultat_final

  except Exception as e:
    logger.error(f"Erreur dans l'assistant pédagogique : {e}", exc_info=True)
    return {
      "aperçu": "❌ Une erreur est survenue.",
      "details": f"Erreur détaillée : {e}"
    }


#@st.cache_data(show_spinner=False)
def recapitulatif(rapport) -> dict:
  prompt = f"""
    Tu es un assistant pédagogique expert. À partir du rapport suivant, génère une synthèse structurée dans un dictionnaire Python avec les éléments suivants :
        
    - **points_forts** : une liste des éléments positifs remarqués dans la formulation des objectifs (clarté, niveau de Bloom, adéquation au contenu du cours, etc.)

    - **axes_amelioration** : une liste synthétique des améliorations générales suggérées (par exemple : "Certains objectifs ne sont pas assez précis, ce qui rend leur compréhension et leur évaluation difficiles.", "Certains verbes utilisés ne reflètent pas le niveau attendu selon la taxonomie de Bloom.", etc.)

    - **objectifs_total** : le nombre total d’objectifs analysés.

    - **objectifs_conformes** :
        - `nbre_total` : nombre d’objectifs conformes,
        - `liste` : une liste de dictionnaires, chacun contenant :
            - `num` : le numéro de l’objectif,
            - `objectif` : le texte de l’objectif,
            - `niveau_bloom` : le niveau de la taxonomie de Bloom identifié.

    - **objectifs_a_ameliorer** :
        - `nbre_total` : nombre d’objectifs à corriger,
        - `liste` : une liste de dictionnaires, chacun contenant :
            - `num` : le numéro de l’objectif,
            - `objectif` : le texte original,
            - `probleme_resume` : résumé du défaut,
            - `suggestion` : résumé de la proposition de reformulation ou d’amélioration.

    - **recommandations** : un résumé, sous forme de liste, des recommandations générales à l’intention de l’enseignant pour améliorer la formulation des objectifs.

    - **niveaux_bloom_utilises** : une liste récapitulative des niveaux de la taxonomie de Bloom identifiés dans l'ensemble des objectifs, qu'ils soient objectif général comme spécifique, conforme comme à améliorer. Ex : ['Connaître', 'Comprendre', etc]
    
    Les objectifs conformes sont ceux qui ont 5/5 pour tous les critères.
    Les objectifs à améliorer sont ceux qui n'ont pas obtenu 5/5 pour tous les critères.
    
    Voici le rapport à analyser :

    {rapport}

    Réponds uniquement avec un objet Python de type `dict` valide. Aucune explication. Pas de texte hors du dictionnaire.
    """
  return appeler_api(prompt)
