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
    logger.info("Nettoyage des objectifs spécifiques lancé.")
    
    temps, capacite = extraire_preambules(objectif_general)

    if isinstance(objectifs_specifiques, str):
        nouveaux_temps, nouvelles_capacite = extraire_preambules(objectifs_specifiques)
        temps = nouveaux_temps or temps
        capacite = nouvelles_capacite or capacite

        preambule_pattern = re.escape(f"{temps}, {capacite}")
        objectifs_sans_preambule = re.sub(preambule_pattern, "", objectifs_specifiques, count=1, flags=re.IGNORECASE)
        objectifs_specifiques_liste = decouper_objectifs(objectifs_sans_preambule)
    else:
        objectifs_specifiques_liste = objectifs_specifiques
        obj_spe_brut = " ".join(objectifs_specifiques_liste)
        nouveaux_temps, nouvelles_capacite = extraire_preambules(obj_spe_brut)
        temps = nouveaux_temps or temps
        capacite = nouvelles_capacite or capacite

    logger.debug("Application des préambules manquants à chaque objectif.")
    objectifs_specifiques_nettoyes = []
    for i, obj in enumerate(objectifs_specifiques_liste, 1):
        temps_obj, capacite_obj = extraire_preambules(obj)
        original_obj = obj

        if not capacite_obj:
            obj = f"{capacite} {obj}"
        if not temps_obj:
            obj = f"{temps}, {obj}"

        if obj != original_obj:
            logger.info(f"Préambules ajoutés à l'objectif {i}.")

        objectifs_specifiques_nettoyes.append(obj)

    logger.info("Nettoyage terminé. Objectifs spécifiques traités : %d", len(objectifs_specifiques_nettoyes))
    return objectifs_specifiques_nettoyes
