import os
import streamlit as st
from mistralai import Mistral
from dotenv import load_dotenv
import logging
from langfuse import Langfuse, observe, get_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")

model = "mistral-large-latest"

#@st.cache_resource
def get_client():
  return Mistral(api_key=api_key)

#@st.cache_data(show_spinner=False)
@observe(as_type="generation")
def appeler_api_traced(**kwargs):
  # Clone kwargs to avoid modifying the original input
  kwargs_clone = kwargs.copy()
 
  # Extract relevant parameters from kwargs
  input = kwargs_clone.pop('messages', None)
  model = kwargs_clone.pop('model', None)
  min_tokens = kwargs_clone.pop('min_tokens', None)
  max_tokens = kwargs_clone.pop('max_tokens', None)
  temperature = kwargs_clone.pop('temperature', None)
  top_p = kwargs_clone.pop('top_p', None)
 
  # Filter and prepare model parameters for logging
  model_parameters = {
        "maxTokens": max_tokens,
        "minTokens": min_tokens,
        "temperature": temperature,
        "top_p": top_p
    }
  model_parameters = {k: v for k, v in model_parameters.items() if v is not None}
 
  # Log the input and model parameters before calling the LLM
  langfuse.update_current_generation(
      input=input,
      model=model,
      model_parameters=model_parameters,
      metadata=kwargs_clone,
 
  )
  
  mistral_client = get_client()
  res = mistral_client.chat.complete(**kwargs)
  
  # Log the usage details and output content after the LLM call
  langfuse.update_current_generation(
      usage_details={
          "input": res.usage.prompt_tokens,
          "output": res.usage.completion_tokens
      },
      output=res.choices[0].message.content
  )
 
  # Return the model's response object
  return res


@observe()
def appeler_api(prompt, system_prompt="Tu es un expert en pédagogie universitaire."):
    logger.info("Appel de l'API Mistral...")
    
    try:
      response = appeler_api_traced(
        model=model,
        #max_tokens=1024,
        #temperature=0.4,
        messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
        ]
      )
      logger.info("Réponse reçue avec succès.")
      
      return response.choices[0].message.content
      
    except Exception as e:
      if "429" in str(e) and "capacity exceeded" in str(e).lower():
        message = (
          "⛔ Le service est temporairement saturé.\n\n"
          "Cela signifie que la capacité du modèle Mistral est dépassée pour le moment. "
          "Veuillez patienter quelques instants et réessayer. Si le problème persiste, revenez plus tard.\n\n"
        )
        st.error(message)
        logger.error("Erreur 429 : Capacité dépassée pour le modèle.", exc_info=True)
      else:
        st.error("Une erreur est survenue lors de l'appel à l'IA.")
        logger.error(f"Erreur lors de l'appel API : {e}", exc_info=True)
        
      #modif return "Une erreur est survenue lors de l'appel à l'IA."
      return None

# Features

# Classification selon le niveau de Bloom

#@st.cache_data(show_spinner=False)
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

#@st.cache_data(show_spinner=False)
def evaluer_objectifs(nom_cours, niveau, public, bloom_classification):
  base_connaissances = """
    Tu es un expert en pédagogie universitaire, chargé d'assister les enseignants dans la constitution d'objectifs pédagogiques optimaux pour leurs cours.
    RAPPELS PEDAGOGIQUES :
      Les objectifs doivent remplir les critères suivants :
        - Spécifique: L'objectif doit être clair et précis, formulé de manière explicite, sans ambiguïtë, évitant les généralités et avec un vocabulaire compréhensible par les étudiant.es. Les comportements attendus doivent être définis dans des contextes et des conditions spécifiques d'application.
        - Mesurable: Il doit être possible de mesurer l'avancement vers l'objectif. L'objectif doit permettre une évaluation précise des acquis grâce à l’utilisation de verbes d’action observables (ex. : analyser, comparer, rédiger), évitant les termes vagues (ex. : comprendre, savoir). Il doit contenir **un seul** verbe **d'action** afin de cibler précisément ce que l'apprenant devra faire, à l'exception de l'objectif **général**. 
        - Approprié (Cohérent): L'objectif doit être pertinent et cohérent avec le cours (se référer au nom du cours), le niveau d'étude, le public cible, le programme, son intention pédagogique si présente et son objectif général.  L'objectif, s'il s'agit d'un objectif enregistré comme 'objectif spécifique' à l'entrée  ( il ne s'agit pas là de son niveau de spécificité évalué) doit être d'un niveau (selon la taxonomie de Bloom) inférieur ou égal à celui de l'objectif général.
        - Réaliste: L'objectif doit être réalisable dans le temps imparti et avec les ressources disponibles.
        - Temporellement défini: L'objectif doit avoir un échéancier clair, avec un début et une fin, ou des jalons intermédiaires.

        L'ensemble des objectifs spécifiques doivent remplir le critère de Complétude, c'est-à-dire que l'ensemble des objectifs spécifiques doit permettre de réaliser l'objectif global/général.


      Ils doivent suivre les règles de rédaction suivantes :
        Délai + L’apprenant·e sera capable de + Verbe d’action + Quoi ? (contenu) + Comment ? (contexte)
        - Précisez le délai : Au terme de l’activité d’apprentissage..., À la fin du TP..., À l’issue de l’unité d’enseignement..., etc.
        - Centrez votre énoncé sur l’apprenant·e : Décrire le résultat produit par l’apprenant·e : ex: L’apprenant·e sera capable de …, L’étudiant·e est en mesure de …, etc. Et PAS l’intention pédagogique de l’enseignant·e :ex: Le cours permet de …, Le cours a pour objectif de présenter…, À l’issue du TP, les étudiants auront eu l’occasion de…, L’unité d’enseignement porte sur …, etc.
        - Utilisez un verbe d’action (un seul par objectif) qui décrit ce que l’étudiant·e doit pouvoir démontrer : Évitez les verbes difficilement évaluables. Choisissez un verbe qui décrit un comportement observable et mesurable.
          À l’issue du cours, l’apprenant·e sera capable de :
          – plutôt que connaître → restituer, énumérer, lister, nommer …
          – plutôt que comprendre → expliquer, illustrer, schématiser…
          – plutôt que maîtriser → appliquer, réaliser, évaluer …
        - Indiquez le contenu ou la procédure sur lequel porte le verbe d’action :
          - À l’issue du cours, les étudiant·es seront capables de décrire les structures anatomiques, leur situation et leur fonction
          - À l’issue de la formation, le/la médecin sera capable d’adopter une attitude bienveillante
          - À l’issue de la séance, l’apprenant·e sera capable de réaliser une aspiration trachéobronchique
        - Décrivez le niveau d’exigence et le contexte dans lequel l’étudiant·e doit être capable de manifester le comportement : Donner des informations sur le contexte implique de se questionner dès le départ sur l’évaluation et ses modalités. Préciser les éléments contextuels et le niveau d’exigence permet aux apprenant·es de savoir très clairement les tâches qu’ils seront amenés à réaliser lors de l’évaluation.
          – La situation dans laquelle l’apprenant·e doit manifester le comportement attendu : réelle, simulée, crayon-papier, en laboratoire …
          – Le matériel ou les ressources à exploiter pour réaliser l’action : texte, vignette clinique, résultats d’analyses biomédicales, paramètres, données statistiques, dossier médical, programme informatique …
          – Le caractère individuel ou collectif : seul, en binôme, en groupe.
          – Le temps disponible pour réaliser la tâche
          – Le niveau de performance attendu : degré de précision, la qualité du résultat …
          Par exemple :
          - À l’issue du cours, les étudiant·e·s seront capables de décrire de MANIERE EXHAUSTIVE les structures anatomiques, leur situation et leur fonction AU DEPART DE SPECIMEN EN 3 DIMENSIONS.
          - À l’issue de la formation, le/la médecin sera capable d’adopter une posture bienveillante EN UTILISANT UN LANGAGE NON STIGMATISANT À L'EGARD DES PERSONNES PRESENTANT DES ASSUETUDES EN CONSULTATION.
          - À l’issue de la séance, l’apprenant·e sera capable de réaliser une aspiration trachéobronchique SUR UN MANNEQUIN HAUTE TECHNICITE EN RESPECTANT CHAQUE ETAPE DE LA PROCEDURE EN VIGUEUR.

    """

  prompt = f"""
    Base de connaissances : {base_connaissances}

    Nom du cours : {nom_cours}
    Niveau : {niveau}
    Public : {public}
    Classification bloom des objectifs : {bloom_classification}

    Instruction :
    Pour chaque objectif, rappelle l'objectif, son niveau dans la taxonomie de bloom, puis évalue l'objectif sur les critères de : spécificité, mesurabilité, cohérence, réalime, temporalité, tels que expliqués dans la base de connaissances. 
    Au niveau de la cohérence, n'oublie pas de vérifier que l'objectif est en adéquation avec le nom du cours. Signale toute incohérence.
    
    A la fin de ton évaluation de chaque critère, attribue une note de 1 à 5 résultante de cette évaluation, et cela pour chaque objectif.
    Fais-le sous cette forme :
      Objectif [numéro de l'objectif] : [l'objectif dans son entièreté].
      - Niveau : [niveau de Bloom]
      - Spécifique : [Ton commentaire sur la spécificité de l'objectif]. Note : [La note que tu lui attribues pour ce critère]
      - Mesurable : [Ton commentaire sur la mesurabilité de l'objectif]. Note : [La note que tu lui attribues pour ce critère]
      - Approprié (Cohérent) : [Ton commentaire sur la cohérence de l'objectif]. Note : [La note que tu lui attribues pour ce critère]
      - Réaliste : [Ton commentaire sur le réalisme de l'objectif]. Note : [La note que tu lui attribues pour ce critère]
      - Temporellement défini : [Ton commentaire sur la temporalité de l'objectif]. Note : [La note que tu lui attribues pour ce critère]

    Si tu ne possèdes pas assez d'informations pour évaluer un objectif sur un critère, dis "Je ne peux pas évaluer cet objectif sur ce critère pour cause de manque d'informations sur" et tu complètes ce sur quoi porte l'information manquante.

    Après l'analyse de ces critères sur chaque objectif, tu évalues le critère de la Complétude sur l'ensemble des objectifs spécifiques, et tu lui attribues également une note.
    
    À la fin, dans le résumé, inclus le récapitulatif des notes de chaque objectif sous cette forme :
    - Objectif [numéro de l'objectif] : Spécifique ([note]/5), Mesurable ([note]/5), Approprié (Cohérent) ([note]/5), Réaliste ([note]/5), Temporellement défini ([note]/5).

    Complétude ([note]/5)

  """

  return appeler_api(prompt)

#@st.cache_data(show_spinner=False)
def auto_eval_evaluation(evaluation):
  base_connaissances = """
    Tu es un expert en pédagogie universitaire, chargé d'assister les enseignants dans la constitution d'objectifs pédagogiques optimaux pour leurs cours.
    RAPPELS PEDAGOGIQUES :
      Les objectifs doivent remplir les critères suivants :
        - Spécifique: L'objectif doit être clair et précis, formulé de manière explicite, sans ambiguïtë, évitant les généralités et avec un vocabulaire compréhensible par les étudiant.es. Il doit contenir **un seul** verbe **d'action** afin de cibler précisément ce que l'apprenant devra faire, à l'exception de l'objectif **général**. Les comportements attendus doivent être définis dans des contextes et des conditions spécifiques d'application.
        - Mesurable: Il doit être possible de mesurer l'avancement vers l'objectif. L'objectif doit permettre une évaluation précise des acquis grâce à l’utilisation de verbes d’action observables (ex. : analyser, comparer, rédiger), évitant les termes vagues (ex. : comprendre, savoir)
        - Approprié (Cohérent): L'objectif doit être pertinent et cohérent avec le cours (se référer au nom du cours), le niveau d'étude, le public cible, le programme, son intention pédagogique si présente et son objectif général.  L'objectif, s'il s'agit d'un objectif enregistré comme 'objectif spécifique' à l'entrée  ( il ne s'agit pas là de son niveau de spécificité évalué) doit être d'un niveau (selon la taxonomie de Bloom) inférieur ou égal à celui de l'objectif général.
        - Réaliste: L'objectif doit être réalisable dans le temps imparti et avec les ressources disponibles.
        - Temporellement défini: L'objectif doit avoir un échéancier clair, avec un début et une fin, ou des jalons intermédiaires.

        L'ensemble des objectifs spécifiques doivent remplir le critère de Complétude, c'est-à-dire que l'ensemble des objectifs spécifiques doit permettre de réaliser l'objectif global/général.


      Ils doivent suivre les règles de rédaction suivantes :
        Délai + L’apprenant·e sera capable de + Verbe d’action + Quoi ? (contenu) + Comment ? (contexte)
        - Précisez le délai : Au terme de l’activité d’apprentissage..., À la fin du TP..., À l’issue de l’unité d’enseignement..., etc.
        - Centrez votre énoncé sur l’apprenant·e : Décrire le résultat produit par l’apprenant·e : ex: L’apprenant·e sera capable de …, L’étudiant·e est en mesure de …, etc. Et PAS l’intention pédagogique de l’enseignant·e :ex: Le cours permet de …, Le cours a pour objectif de présenter…, À l’issue du TP, les étudiants auront eu l’occasion de…, L’unité d’enseignement porte sur …, etc.
        - Utilisez un verbe d’action (un seul par objectif) qui décrit ce que l’étudiant·e doit pouvoir démontrer : Évitez les verbes difficilement évaluables. Choisissez un verbe qui décrit un comportement observable et mesurable.
          À l’issue du cours, l’apprenant·e sera capable de :
          – plutôt que connaître → restituer, énumérer, lister, nommer …
          – plutôt que comprendre → expliquer, illustrer, schématiser…
          – plutôt que maîtriser → appliquer, réaliser, évaluer …
        - Indiquez le contenu ou la procédure sur lequel porte le verbe d’action :
          - À l’issue du cours, les étudiant·es seront capables de décrire les structures anatomiques, leur situation et leur fonction
          - À l’issue de la formation, le/la médecin sera capable d’adopter une attitude bienveillante
          - À l’issue de la séance, l’apprenant·e sera capable de réaliser une aspiration trachéobronchique
        - Décrivez le niveau d’exigence et le contexte dans lequel l’étudiant·e doit être capable de manifester le comportement : Donner des informations sur le contexte implique de se questionner dès le départ sur l’évaluation et ses modalités. Préciser les éléments contextuels et le niveau d’exigence permet aux apprenant·es de savoir très clairement les tâches qu’ils seront amenés à réaliser lors de l’évaluation.
          – La situation dans laquelle l’apprenant·e doit manifester le comportement attendu : réelle, simulée, crayon-papier, en laboratoire …
          – Le matériel ou les ressources à exploiter pour réaliser l’action : texte, vignette clinique, résultats d’analyses biomédicales, paramètres, données statistiques, dossier médical, programme informatique …
          – Le caractère individuel ou collectif : seul, en binôme, en groupe.
          – Le temps disponible pour réaliser la tâche
          – Le niveau de performance attendu : degré de précision, la qualité du résultat …
          Par exemple :
          - À l’issue du cours, les étudiant·e·s seront capables de décrire de MANIERE EXHAUSTIVE les structures anatomiques, leur situation et leur fonction AU DEPART DE SPECIMEN EN 3 DIMENSIONS.
          - À l’issue de la formation, le/la médecin sera capable d’adopter une posture bienveillante EN UTILISANT UN LANGAGE NON STIGMATISANT À L'EGARD DES PERSONNES PRESENTANT DES ASSUETUDES EN CONSULTATION.
          - À l’issue de la séance, l’apprenant·e sera capable de réaliser une aspiration trachéobronchique SUR UN MANNEQUIN HAUTE TECHNICITE EN RESPECTANT CHAQUE ETAPE DE LA PROCEDURE EN VIGUEUR.

    """

  prompt = f"""
    Base de connaissances : {base_connaissances}
    
    Tu es un expert en pédagogie universitaire. Voici une évaluation automatique d'objectifs pédagogiques.

    Ta mission :
    1. Vérifie que cette évaluation (notamment les commentaires et les notes) est correcte, complète et cohérente, compte tenu des critères de spécificité, mesurabilité, cohérence, réalisme, définition de la temporalité spécifiés dans la base de connaissances.
    2. Améliore-la si besoin, mais garde EXACTEMENT le même format de sortie pour la version révisée (numérotation, paragraphes, tirets, structure, etc.).
    3. Si tout est bon, reformule légèrement pour plus de clarté, mais sans modifier la structure.

    Evaluation à vérifier :
    {evaluation}

    # Version révisée dans le même format :
    """
  return appeler_api(prompt)


# Améliorations et recommandations

#@st.cache_data(show_spinner=False)
def ameliorer_objectifs(nom_cours, niveau, public, evaluation_objectifs):
  base_connaissances = """
    Tu es un expert en pédagogie universitaire, chargé d'assister les enseignants dans la constitution d'objectifs pédagogiques optimaux pour leurs cours.
    RAPPELS PEDAGOGIQUES :
      Les objectifs doivent remplir les critères suivants :
        - Spécifique: L'objectif doit être clair et précis, formulé de manière explicite, sans ambiguïtë, évitant les généralités et avec un vocabulaire compréhensible par les étudiant.es. Les comportements attendus doivent être définis dans des contextes et des conditions spécifiques d'application.
        - Mesurable: Il doit être possible de mesurer l'avancement vers l'objectif. L'objectif doit permettre une évaluation précise des acquis grâce à l’utilisation de verbes d’action observables (ex. : analyser, comparer, rédiger), évitant les termes vagues (ex. : comprendre, savoir). Il doit contenir **un seul** verbe **d'action** afin de cibler précisément ce que l'apprenant devra faire, à l'exception de l'objectif **général**.
        - Approprié (Cohérent): L'objectif doit être pertinent et cohérent avec le cours (se référer au nom du cours), le niveau d'étude, le public cible, le programme, son intention pédagogique si présente et son objectif général.  L'objectif, s'il s'agit d'un objectif enregistré comme 'objectif spécifique' à l'entrée  ( il ne s'agit pas là de son niveau de spécificité évalué) doit être d'un niveau (selon la taxonomie de Bloom) inférieur ou égal à celui de l'objectif général.
        - Réaliste: L'objectif doit être réalisable dans le temps imparti et avec les ressources disponibles.
        - Temporellement défini: L'objectif doit avoir un échéancier clair, avec un début et une fin, ou des jalons intermédiaires.

        L'ensemble des objectifs spécifiques doivent remplir le critère de Complétude, c'est-à-dire que l'ensemble des objectifs spécifiques doit permettre de réaliser l'objectif global/général.


      Ils doivent suivre les règles de rédaction suivantes :
        Délai + L’apprenant·e sera capable de + Verbe d’action + Quoi ? (contenu) + Comment ? (contexte)
        - Précisez le délai : Au terme de l’activité d’apprentissage..., À la fin du TP..., À l’issue de l’unité d’enseignement..., etc.
        - Centrez votre énoncé sur l’apprenant·e : Décrire le résultat produit par l’apprenant·e : ex: L’apprenant·e sera capable de …, L’étudiant·e est en mesure de …, etc. Et PAS l’intention pédagogique de l’enseignant·e :ex: Le cours permet de …, Le cours a pour objectif de présenter…, À l’issue du TP, les étudiants auront eu l’occasion de…, L’unité d’enseignement porte sur …, etc.
        - Utilisez un verbe d’action (un seul par objectif) qui décrit ce que l’étudiant·e doit pouvoir démontrer : Évitez les verbes difficilement évaluables. Choisissez un verbe qui décrit un comportement observable et mesurable.
          À l’issue du cours, l’apprenant·e sera capable de :
          – plutôt que connaître → restituer, énumérer, lister, nommer …
          – plutôt que comprendre → expliquer, illustrer, schématiser…
          – plutôt que maîtriser → appliquer, réaliser, évaluer …
        - Indiquez le contenu ou la procédure sur lequel porte le verbe d’action :
          - À l’issue du cours, les étudiant·es seront capables de décrire les structures anatomiques, leur situation et leur fonction
          - À l’issue de la formation, le/la médecin sera capable d’adopter une attitude bienveillante
          - À l’issue de la séance, l’apprenant·e sera capable de réaliser une aspiration trachéobronchique
        - Décrivez le niveau d’exigence et le contexte dans lequel l’étudiant·e doit être capable de manifester le comportement : Donner des informations sur le contexte implique de se questionner dès le départ sur l’évaluation et ses modalités. Préciser les éléments contextuels et le niveau d’exigence permet aux apprenant·es de savoir très clairement les tâches qu’ils seront amenés à réaliser lors de l’évaluation.
          – La situation dans laquelle l’apprenant·e doit manifester le comportement attendu : réelle, simulée, crayon-papier, en laboratoire …
          – Le matériel ou les ressources à exploiter pour réaliser l’action : texte, vignette clinique, résultats d’analyses biomédicales, paramètres, données statistiques, dossier médical, programme informatique …
          – Le caractère individuel ou collectif : seul, en binôme, en groupe.
          – Le temps disponible pour réaliser la tâche
          – Le niveau de performance attendu : degré de précision, la qualité du résultat …
          Par exemple :
          - À l’issue du cours, les étudiant·e·s seront capables de décrire de MANIERE EXHAUSTIVE les structures anatomiques, leur situation et leur fonction AU DEPART DE SPECIMEN EN 3 DIMENSIONS.
          - À l’issue de la formation, le/la médecin sera capable d’adopter une posture bienveillante EN UTILISANT UN LANGAGE NON STIGMATISANT À L'EGARD DES PERSONNES PRESENTANT DES ASSUETUDES EN CONSULTATION.
          - À l’issue de la séance, l’apprenant·e sera capable de réaliser une aspiration trachéobronchique SUR UN MANNEQUIN HAUTE TECHNICITE EN RESPECTANT CHAQUE ETAPE DE LA PROCEDURE EN VIGUEUR.

    """

  prompt = f"""
      Base de connaissances : {base_connaissances}

      Nom du cours : {nom_cours}
      Niveau : {niveau}
      Public : {public}
      Evaluation des objectifs : {evaluation_objectifs}

      Instruction : 
        Sur la base des évaluations des objectifs pédagogiques, fais pour chaque objectif, si le besoin est, des recommandations afin d'améliorer le plus possible ces objectifs.
        Au niveau de chaque objectif, l'analyse sera fournie sous cette forme :
        
        - Niveau : [niveau de Bloom]
        - Spécifique : [Commentaire contenu dans l'évaluation de cet objectif sur ce critère]. Note : **[Note attribuée dans l'évaluation]**
        - Mesurable : [Commentaire contenu dans l'évaluation de cet objectif sur ce critère]. Note : **[Note attribuée dans l'évaluation]**
        - Approprié (Cohérent) : [Commentaire contenu dans l'évaluation de cet objectif sur ce critère]. **Note : [Note attribuée dans l'évaluation]**
        - Réaliste : [Commentaire contenu dans l'évaluation de cet objectif sur ce critère]. Note : **[Note attribuée dans l'évaluation]**
        - Temporellement défini : [Commentaire contenu dans l'évaluation de cet objectif sur ce critère]. Note : **[Note attribuée dans l'évaluation]**
        Recommandation(s) :
        - [Critère(s) sur lequel porte la recommandation] : [Ta recommandation pour améliorer l'objectif. Tu peux si nécessaire donner un exemple.]
        Si tu estimes que l'objectif est déjà optimal, tu peux ne pas donner de recommandations.

        La structure globale du résultat à fournir est la suivante :
        
        #### Objectif général :
          [L'objectif général dans son entièreté]
        [Analyse de l'objectif général comme spécifiée plus haut]
          
        #### Objectifs spécifiques
        
        Objectif [numéro de l'objectif] : [l'objectif dans son entièreté].
        [Analyse de cet objectif spécifique comme spécifiée plus haut]
        
        
        Objectif [numéro de l'objectif] : [l'objectif dans son entièreté].
        **[Analyse de cet objectif spécifique comme spécifiée plus haut]**
        
        
        Et ceci jusqu'à la fin des objectifs spécifiques.
        Après l'analyse de ces critères sur chaque objectif, tu évalues le critère de la Complétude sur l'ensemble des objectifs spécifiques, et tu lui attribues également une note.
        
        A la fin, fais un récapitulatif des notes pour chaque objectif (Objectif [numéro de l'objectif] : Spécifique ([note]/5), Mesurable ([note]/5), Approprié (Cohérent) ([note]/5), Réaliste ([note]/5), Temporellement défini ([note]/5)) inclus dans un résumé global de l'analyse pour conclure (ne pas oublier la complétude globale des objectifs spécifiques).
        
      """

  return appeler_api(prompt)

#@st.cache_data(show_spinner=False)
def auto_eval_suggestions(suggestions):
  base_connaissances = """
    Tu es un expert en pédagogie universitaire, chargé d'assister les enseignants dans la constitution d'objectifs pédagogiques optimaux pour leurs cours.
    RAPPELS PEDAGOGIQUES :
      Les objectifs doivent remplir les critères suivants :
        - Spécifique: L'objectif doit être clair et précis, formulé de manière explicite, sans ambiguïtë, évitant les généralités et avec un vocabulaire compréhensible par les étudiant.es. Les comportements attendus doivent être définis dans des contextes et des conditions spécifiques d'application.
        - Mesurable: Il doit être possible de mesurer l'avancement vers l'objectif. L'objectif doit permettre une évaluation précise des acquis grâce à l’utilisation de verbes d’action observables (ex. : analyser, comparer, rédiger), évitant les termes vagues (ex. : comprendre, savoir). Il doit contenir **un seul** verbe **d'action** afin de cibler précisément ce que l'apprenant devra faire, à l'exception de l'objectif **général**.
        - Approprié (Cohérent): L'objectif doit être pertinent et cohérent avec le cours (se référer au nom du cours), le niveau d'étude, le public cible, le programme, son intention pédagogique si présente et son objectif général.  L'objectif, s'il s'agit d'un objectif enregistré comme 'objectif spécifique' à l'entrée  ( il ne s'agit pas là de son niveau de spécificité évalué) doit être d'un niveau (selon la taxonomie de Bloom) inférieur ou égal à celui de l'objectif général.
        - Réaliste: L'objectif doit être réalisable dans le temps imparti et avec les ressources disponibles.
        - Temporellement défini: L'objectif doit avoir un échéancier clair, avec un début et une fin, ou des jalons intermédiaires.

        L'ensemble des objectifs spécifiques doivent remplir le critère de Complétude, c'est-à-dire que l'ensemble des objectifs spécifiques doit permettre de réaliser l'objectif global/général.


      Ils doivent suivre les règles de rédaction suivantes :
        Délai + L’apprenant·e sera capable de + Verbe d’action + Quoi ? (contenu) + Comment ? (contexte)
        - Précisez le délai : Au terme de l’activité d’apprentissage..., À la fin du TP..., À l’issue de l’unité d’enseignement..., etc.
        - Centrez votre énoncé sur l’apprenant·e : Décrire le résultat produit par l’apprenant·e : ex: L’apprenant·e sera capable de …, L’étudiant·e est en mesure de …, etc. Et PAS l’intention pédagogique de l’enseignant·e :ex: Le cours permet de …, Le cours a pour objectif de présenter…, À l’issue du TP, les étudiants auront eu l’occasion de…, L’unité d’enseignement porte sur …, etc.
        - Utilisez un verbe d’action (un seul par objectif) qui décrit ce que l’étudiant·e doit pouvoir démontrer : Évitez les verbes difficilement évaluables. Choisissez un verbe qui décrit un comportement observable et mesurable.
          À l’issue du cours, l’apprenant·e sera capable de :
          – plutôt que connaître → restituer, énumérer, lister, nommer …
          – plutôt que comprendre → expliquer, illustrer, schématiser…
          – plutôt que maîtriser → appliquer, réaliser, évaluer …
        - Indiquez le contenu ou la procédure sur lequel porte le verbe d’action :
          - À l’issue du cours, les étudiant·es seront capables de décrire les structures anatomiques, leur situation et leur fonction
          - À l’issue de la formation, le/la médecin sera capable d’adopter une attitude bienveillante
          - À l’issue de la séance, l’apprenant·e sera capable de réaliser une aspiration trachéobronchique
        - Décrivez le niveau d’exigence et le contexte dans lequel l’étudiant·e doit être capable de manifester le comportement : Donner des informations sur le contexte implique de se questionner dès le départ sur l’évaluation et ses modalités. Préciser les éléments contextuels et le niveau d’exigence permet aux apprenant·es de savoir très clairement les tâches qu’ils seront amenés à réaliser lors de l’évaluation.
          – La situation dans laquelle l’apprenant·e doit manifester le comportement attendu : réelle, simulée, crayon-papier, en laboratoire …
          – Le matériel ou les ressources à exploiter pour réaliser l’action : texte, vignette clinique, résultats d’analyses biomédicales, paramètres, données statistiques, dossier médical, programme informatique …
          – Le caractère individuel ou collectif : seul, en binôme, en groupe.
          – Le temps disponible pour réaliser la tâche
          – Le niveau de performance attendu : degré de précision, la qualité du résultat …
          Par exemple :
          - À l’issue du cours, les étudiant·e·s seront capables de décrire de MANIERE EXHAUSTIVE les structures anatomiques, leur situation et leur fonction AU DEPART DE SPECIMEN EN 3 DIMENSIONS.
          - À l’issue de la formation, le/la médecin sera capable d’adopter une posture bienveillante EN UTILISANT UN LANGAGE NON STIGMATISANT À L'EGARD DES PERSONNES PRESENTANT DES ASSUETUDES EN CONSULTATION.
          - À l’issue de la séance, l’apprenant·e sera capable de réaliser une aspiration trachéobronchique SUR UN MANNEQUIN HAUTE TECHNICITE EN RESPECTANT CHAQUE ETAPE DE LA PROCEDURE EN VIGUEUR.

    """

  prompt = f"""
    Base de connaissances : {base_connaissances}

    Tu es un expert en ingénierie pédagogique. Voici une évaluation d'objectifs pédagogiques accompagnée de suggestions générées automatiquement pour améliorer ces objectifs.

    Ta mission :
    1. Vérifie que chaque recommandation est claire, cohérente avec le cours et son niveau, bien alignée sur la taxonomie de Bloom (dont les niveaux sont : Connaître, Comprendre, Appliquer, Analyser, Évaluer, Créer) et contribue à obtenir un objectif respectant les critères de spécificité, mesurabilité, cohérence, réalisme, définition de la temporalité, expliqués dans la base de connaissances.  
    2. Corrige ou reformule les recommandations si nécessaire, tout en RESPECTANT LE MEME FORMAT de sortie dans la version révisée que dans celle d'origine (numérotation, paragraphes, tirets, structure etc.).

    Evaluation d'objectifs pédagogiques accompagnée de recommandations à évaluer :
    {suggestions}

    # Version révisée :
    """
  return appeler_api(prompt)


#@st.cache_data(show_spinner=False)
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
#modif 
with st.spinner('Analyse en cours, veuillez patienter...'):
  def assistant_pedagogique(nom_cours, niveau, public, objectif_general, objectifs_specifiques):
    logger.info("Début de l'analyse pédagogique pour le cours : %s", nom_cours)

    try:
      # Classification selon Bloom
      logger.info("Étape 1 : Classification selon Bloom")
      st.info("Classification selon la taxonomie révisée de Bloom...")
      
      bloom_classification = classifier_objectifs(objectif_general, objectifs_specifiques)
      
      if bloom_classification is None:
        st.warning("L'analyse a échoué dès la classification des objectifs. Veuillez réessayer.")
        logger.error("Échec de la classification des objectifs selon Bloom.")
        st.stop()
        return None
        
      # Évaluation des objectifs
      logger.info("Étape 2 : Évaluation des objectifs")
      st.info("Évaluation des objectifs...")
      
      evaluations = evaluer_objectifs(nom_cours, niveau, public, bloom_classification)
      if evaluations is None:
        st.warning("L'évaluation des objectifs n’a pas pu être effectuée. Veuillez réessayer.")
        logger.error("Échec de l'évaluation des objectifs.")
        st.stop()
        return None
      
      evaluations_revisees = auto_eval_evaluation(evaluations)
      if evaluations_revisees is None:
        st.warning("L'évaluation des objectifs n’a pas pu être réalisée. Veuillez réessayer.")
        logger.error("Échec de la vérification de l'évaluation des objectifs.")
        st.stop()   
        return None
      
      # Recommandations
      logger.info("Étape 3 : Génération de recommandations")
      st.info("Génération de recommandations...")

      suggestions = ameliorer_objectifs(nom_cours, niveau, public, evaluations_revisees)
      if suggestions is None:
        st.warning("La génération de recommandations n’a pas pu être effectuée. Veuillez réessayer.")
        logger.error("Échec de la génération des recommandations.")
        st.stop()
        return None

      suggestions_revisees = auto_eval_suggestions(suggestions)
      if suggestions_revisees is None:
        st.warning("La génération de recommandations n’a pas pu être réalisée.")
        logger.error("Échec de la vérification  recommandations générées.")
        st.stop()
        return None

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


langfuse.flush()