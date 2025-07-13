import re
import logging

logger = logging.getLogger(__name__)

def extraire_preambules(texte):
    logger.debug("Début extraction des préambules.")
    
    motifs_temps = [
        r"(à|a) la fin (du|de la|de l’|de|d’)[^,:\n]+",
        r"au terme (du|de la|de l’|de|d’)[^,:\n]+",
        r"(à|a) l’issue (du|de la|de l’|de|d’)[^,:\n]+",
        r"au bout (du|de la|de l’|de|d’)[^,:\n]+"
    ]

    sujets = [
        r"(?:les|l)[’']?(?:apprenant|étudiant)(?:e|\(e\)|\.e|·e)?(?:s|\(s\)|\.s|·s)?", 
        r"il(?:s|\(s\)|\.s|·s)?", 
        r"elle(?:s|\(s\)|\.s|·s)?", 
        r"on"
    ]
    verbes = [
        r"(?:sera|seront) capable(?:s|\(s\)|\.s|·s)? (?:de|d[’'])",
        r"(?:pourra|pourront)",
        r"(?:sera|seront) en mesure (?:de|d[’'])"
    ]
    motifs_capacite = [f"{sujet} {verbe}" for sujet in sujets for verbe in verbes]

    temps = None
    capacite = None

    for motif in motifs_temps:
        match = re.search(motif, texte, flags=re.IGNORECASE)
        if match:
            temps = match.group(0).strip().capitalize()
            logger.info(f"Préambule temporel détecté : {temps}")
            break

    for motif in motifs_capacite:
        match = re.search(motif, texte, flags=re.IGNORECASE)
        if match:
            capacite = match.group(0).strip().capitalize()
            logger.info(f"Préambule de capacité détecté : {capacite}")
            break

    return temps, capacite


def decouper_objectifs(texte):
    logger.debug("Tentative de découpage des objectifs.")
    split_patterns = [
        r"(?:^|\n)\s*(?:\d+[.)])\s+",
        r"(?:^|\n)\s*[-•]\s+",
        r"(?:^|\n)\s*(?:[ivxlcdmIVXLCDM]+[.)])\s+",
        r"(?:^|\n)\s*[a-zA-Z][.)]\s+",
        r";\s*(?=\n|$)",
        r",\s*(?=\n|$)",
        r"\n{2,}",
    ]

    for pattern in split_patterns:
        parts = re.split(pattern, texte)
        parts = [p.strip(" \n\t\r:.-") for p in parts if p.strip()]
        if len(parts) > 1:
            logger.info(f"Découpage réussi avec le motif : {pattern}")
            return parts

    logger.warning("Aucun découpage réussi. Retour du texte brut.")
    return [texte.strip()]


def nettoyer_objectifs_specifiques(objectif_general, objectifs_specifiques):
    logger.info("\n\nNettoyage des objectifs spécifiques lancé.")
    
    # Étape 1: Déterminer le préambule global à partir de l'objectif général et des objectifs spécifiques bruts.
    if objectif_general :
        logger.debug(f"Extraction du préambule de l'objectif général : {objectif_general}.")
        temps, capacite = extraire_preambules(objectif_general)
    else:
        logger.debug("Aucun objectif général fourni, utilisation des préambules des objectifs spécifiques.")
        #temps, capacite = None, None

    # Convertir les objectifs spécifiques en une seule chaîne de caractères si c'est une liste
    texte_objectifs_bruts = " ".join(objectifs_specifiques) if isinstance(objectifs_specifiques, list) else objectifs_specifiques

    # Chercher un préambule dans le bloc d'objectifs spécifiques qui pourrait être plus pertinent
    nouveaux_temps, nouvelles_capacite = extraire_preambules(texte_objectifs_bruts)
    temps = nouveaux_temps or temps
    capacite = nouvelles_capacite or capacite

    # Étape 2: Retirer le préambule global du bloc de texte pour éviter les répétitions.
    objectifs_sans_preambule = texte_objectifs_bruts
    
    # On ne tente de retirer le préambule que si on en a trouvé un.
    if temps or capacite:
        pattern_parts = []
        if temps:
            pattern_parts.append(re.escape(temps))
        if capacite:
            pattern_parts.append(re.escape(capacite))
        
        # Crée un motif qui gère la virgule et les espaces entre les parties du préambule
        preambule_pattern = r'\s*,?\s*'.join(pattern_parts)
        
        # On ancre le motif au début du texte pour ne supprimer que le vrai préambule
        objectifs_sans_preambule = re.sub(f"^{preambule_pattern}", "", texte_objectifs_bruts, count=1, flags=re.IGNORECASE).strip()

    # Étape 3: Découper le bloc de texte (maintenant sans préambule) en une liste d'objectifs.
    objectifs_specifiques_liste = decouper_objectifs(objectifs_sans_preambule)

    # Étape 4: Ajouter le préambule à chaque objectif individuel qui n'en a pas.
    objectifs_specifiques_nettoyes = []
    for obj in objectifs_specifiques_liste:
        temps_obj, capacite_obj = extraire_preambules(obj)
        
        # On vérifie si le préambule global (temps, capacite) existe ET s'il n'est pas déjà dans l'objectif
        if capacite and not capacite_obj:
            obj = f"{capacite} {obj}"
        
        if temps and not temps_obj:
            # On ajoute la virgule seulement si on vient d'ajouter la capacité
            if capacite and not capacite_obj:
                obj = f"{temps}, {obj}"
            else:
                obj = f"{temps} {obj}"

        obj = obj.strip().capitalize()
        logger.info("Nouvel objectif spécifique nettoyé : %s", obj)
        objectifs_specifiques_nettoyes.append(obj)

    logger.info("Nettoyage terminé. Objectifs spécifiques traités : %d", len(objectifs_specifiques_nettoyes))
    return objectifs_specifiques_nettoyes
