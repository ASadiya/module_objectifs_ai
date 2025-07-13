import logging
import logging.handlers
import sys

def setup_logging():
    """
    Configure un système de logging centralisé, structuré et flexible.

    Cette fonction met en place deux gestionnaires (handlers) :
    1.  StreamHandler : Affiche les logs de niveau INFO et supérieur dans la console.
        Idéal pour le suivi en temps réel pendant le développement.
    2.  RotatingFileHandler : Enregistre tous les logs (niveau DEBUG et supérieur)
        dans un fichier `app.log`. Le fichier est rotatif pour éviter qu'il
        ne devienne trop volumineux (taille max 1 Mo, 5 fichiers de sauvegarde).

    Le format des logs inclut des informations utiles pour le débogage :
    timestamp, niveau, nom du module, numéro de ligne et message.
    """
    # Créer le logger racine
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture tous les niveaux de logs

    # Éviter d'ajouter des handlers multiples si la fonction est appelée plusieurs fois
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. Handler pour la console (niveau INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 2. Handler pour un fichier rotatif (niveau DEBUG)
    file_handler = logging.handlers.RotatingFileHandler(
        'app.log', maxBytes=1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logging.info("Le système de logging a été configuré avec succès.")

