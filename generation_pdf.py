import ast, json, re, logging
import streamlit as st
from fpdf import FPDF
import tempfile
from datetime import datetime
from babel.dates import format_date

logger = logging.getLogger(__name__)

def llm_output_to_dict(llm_output):
    """
    Convertit une sortie de LLM en dictionnaire Python de manière robuste.
    
    Args:
        llm_output (str): La sortie du LLM contenant un dictionnaire
        
    Returns:
        dict: Le dictionnaire Python converti
        
    Raises:
        ValueError: Si la conversion échoue
    """
    logger.debug("Début de la conversion de la sortie LLM en dictionnaire")
    
    # Nettoyer la sortie (enlever les balises markdown si présentes)
    cleaned_output = llm_output.strip()
    logger.debug(f"Sortie nettoyée, longueur: {len(cleaned_output)} caractères")
    
    # Enlever les balises de code markdown si présentes
    if cleaned_output.startswith('```'):
        logger.debug("Détection de balises markdown, nettoyage en cours")
        lines = cleaned_output.split('\n')
        # Trouver la première ligne qui ne commence pas par ```
        start_idx = 1
        for i, line in enumerate(lines):
            if not line.strip().startswith('```') and not line.strip().startswith('python'):
                start_idx = i
                break
        
        # Trouver la dernière ligne qui ne finit pas par ```
        end_idx = len(lines) - 1
        for i in range(len(lines) - 1, -1, -1):
            if not lines[i].strip().endswith('```'):
                end_idx = i
                break
        
        cleaned_output = '\n'.join(lines[start_idx:end_idx + 1])
        logger.debug(f"Balises markdown supprimées, nouvelle longueur: {len(cleaned_output)} caractères")
    
    # Méthode 1: Essayer ast.literal_eval (plus sûr)
    try:
        logger.debug("Tentative de conversion avec ast.literal_eval")
        result = ast.literal_eval(cleaned_output)
        if isinstance(result, dict):
            logger.info("Conversion réussie avec ast.literal_eval")
            return result
    except (ValueError, SyntaxError) as e:
        logger.warning(f"ast.literal_eval a échoué: {e}")
    
    # Méthode 2: Essayer json.loads
    try:
        logger.debug("Tentative de conversion avec json.loads")
        result = json.loads(cleaned_output)
        if isinstance(result, dict):
            logger.info("Conversion réussie avec json.loads")
            return result
    except json.JSONDecodeError as e:
        logger.warning(f"json.loads a échoué: {e}")
    
    # Méthode 3: Essayer de corriger les erreurs JSON communes
    try:
        logger.debug("Tentative de correction JSON et conversion")
        # Remplacer les apostrophes simples par des guillemets doubles
        json_corrected = re.sub(r"'([^']*)':", r'"\1":', cleaned_output)
        json_corrected = re.sub(r":\s*'([^']*)'", r': "\1"', json_corrected)
        
        result = json.loads(json_corrected)
        if isinstance(result, dict):
            logger.info("Conversion réussie après correction JSON")
            return result
    except json.JSONDecodeError as e:
        logger.error(f"Correction JSON a échoué: {e}")
    
    # Si tout échoue, lever une exception
    logger.error("Toutes les méthodes de conversion ont échoué")
    raise ValueError("Impossible de convertir la sortie LLM en dictionnaire")

# Fonction similaire pour facilité l'affichage des détails du rapport 

def nettoyer_sortie_llm(texte: str) -> str:
    """
    Nettoie la sortie d'un LLM en supprimant les balises Markdown de type ```...```.
    Conserve uniquement le contenu utile à afficher dans du HTML.
    """
    texte = texte.strip()
    logger.debug(f"Texte brut, longueur: {len(texte)}")

    # Supprimer les blocs ```...``` (avec ou sans langage précisé)
    blocs = re.findall(r"```(?:\w+)?\\n(.*?)```", texte, re.DOTALL)
    if blocs:
        logger.debug(f"{len(blocs)} bloc(s) détecté(s) et extrait(s).")
        texte_nettoye = "\n\n".join(blocs)
    else:
        # Pas de bloc markdown trouvé, on retire les délimiteurs bruts s'ils traînent
        texte_nettoye = texte.replace("```", "")
        logger.debug("Pas de bloc markdown structuré trouvé, suppression simple des backticks.")

    return texte_nettoye.strip()


def build_tables_from_recap_dict(recap_dict):
    table_chif = [('Élément analysé ', 'Nombre')]
    table_chif.append(("Objectifs saisis", str(recap_dict.get('objectifs_total', 00))))
    table_chif.append(("Objectifs conformes", str(recap_dict.get('objectifs_conformes', {}).get('nbre_total', 00))))
    table_chif.append(("Objectifs à améliorer", str(recap_dict.get('objectifs_a_ameliorer', {}).get('nbre_total', 00))))
    table_chif.append(("Niveaux de Bloom représentés", ", ".join(recap_dict.get("niveaux_bloom_utilises")) if recap_dict.get("niveaux_bloom_utilises") else "Aucun niveau de Bloom identifié."
))


    table_ameliorer = [('N°', 'Objectif', 'Problème', 'Suggestion')]
    objectifs_a_ameliorer = recap_dict.get('objectifs_a_ameliorer', {}).get('liste', [])
    if objectifs_a_ameliorer:
        for obj in objectifs_a_ameliorer:
            table_ameliorer.append((
                str(obj.get('num', '')),
                str(obj.get('objectif', '')),
                str(obj.get('probleme_resume', '')),
                str(obj.get('suggestion', ''))
            ))
    else:
        table_ameliorer.append(('', 'Aucun objectif à améliorer', '', ''))


    table_conformes = [('N°', 'Objectif', 'Niveau de Bloom')]
    objectifs_conformes = recap_dict.get('objectifs_conformes', {}).get('liste', [])
    if objectifs_conformes:
        for obj in objectifs_conformes:
            table_conformes.append((
                str(obj.get('num', '')),
                str(obj.get('objectif', '')),
                str(obj.get('niveau_bloom', ''))
            ))
    else:
        table_conformes.append(('', 'Aucun objectif conforme', ''))


    table_axes = [('Points forts', 'Axes d\'amélioration')]
    pf = recap_dict.get('points_forts', [])
    ax = recap_dict.get('axes_amelioration', [])
    if pf or ax:
        for i in range(max(len(pf), len(ax))):
            table_axes.append((pf[i] if i < len(pf) else '', ax[i] if i < len(ax) else ''))
    else:
        table_axes.append(('Aucun point fort identifié', 'Aucun axe d’amélioration identifié'))


    table_recom = [('N°', 'Recommandation clée')]
    recommandations = recap_dict.get('recommandations', [])
    if recommandations:
        for i, rec in enumerate(recommandations, 1):
            table_recom.append((str(i), rec))
    else:
        table_recom.append(('', 'Aucune recommandation'))

    return table_chif, table_axes, table_recom, table_ameliorer, table_conformes


def generer_pdf(nom_cours, niveau, public, objectif_general, objectifs_specifiques_brut, rapport, recap_dict):

    class PDF(FPDF):
        def __init__(self):
            super().__init__()
            self.add_font("DejaVu", "", "assets/fonts/DejaVu/DejaVuSans.ttf", uni=True)
            self.add_font("DejaVu", "B", "assets/fonts/DejaVu/DejaVuSans-Bold.ttf", uni=True)
            self.add_font("DejaVu", "I", "assets/fonts/DejaVu/DejaVuSans-Oblique.ttf", uni=True)
            self.add_font("DejaVu", "BI", "assets/fonts/DejaVu/DejaVuSans-BoldOblique.ttf", uni=True)


            self.title = ""
            self.current_chapter_title = ""
            self.is_chapter_start = False
            self.is_page_de_garde = False

            self.is_annexe = False 
            
            self.table_counter = 1
            
            self.set_auto_page_break(auto=True, margin=15)


    # Traitement du texte issu du llm

        def write_rich_line(self, text):
            parts = re.split(r'(\*\*.*?\*\*)', text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    self.set_font("DejaVu", "B", 10)
                    self.write(8, part[2:-2])
                else:
                    self.set_font("DejaVu", "", 10)
                    self.write(8, part)
            self.ln()
            
        def write_markdown(self, md_text):
            lines = md_text.split('\n')
            for line in lines:
                self.set_text_color(0, 0, 0)
                line = line.strip()
                handled = False
                
                if line.startswith('**') and line.endswith('**'):
                    #self.cell(3)
                    self.set_text_color(25, 25, 112)
                    
                    
                # Cas combiné : bullet + texte enrichi (**...**)
                if (line.startswith('- ') or line.startswith('* ')) and '**' in line:
                    self.set_font("DejaVu", "", 10)
                    self.cell(3)  # indent
                    line_content = u'\u2022 ' + line[2:].strip()
                    self.write_rich_line(line_content)
                    handled = True

                # Cas simple : bullet sans enrichissement
                elif line.startswith('- ') or line.startswith('* '):
                    self.set_font("DejaVu", "", 10)
                    self.cell(3)
                    self.multi_cell(0, 7, u'\u2022 ' + line[2:], ln=True, align='J')
                    handled = True

                # Titres Markdown
                elif line.startswith('# '):
                    self.set_font("DejaVu", "B", 15)
                    self.set_text_color(25, 25, 112)
                    self.multi_cell(0, 7, line[2:], ln=True, align='J')
                    handled = True
                elif line.startswith('## '):
                    self.set_font("DejaVu", "B", 14)
                    self.set_text_color(25, 25, 112)
                    self.multi_cell(0, 7, line[3:], ln=True, align='J')
                    handled = True
                elif line.startswith('### '):
                    self.set_font("DejaVu", "B", 13)
                    self.set_text_color(25, 25, 112)
                    self.multi_cell(0, 7, line[4:], ln=True, align='J')
                    handled = True
                elif line.startswith('#### '):
                    self.set_font("DejaVu", "B", 12)
                    self.set_text_color(25, 25, 112)
                    self.multi_cell(0, 7, line[5:], ln=True, align='J')
                    handled = True

                # Cas général avec gras partiel (hors bullets)
                elif '**' in line:
                    self.write_rich_line(line)
                    handled = True

                # Cas par défaut : texte normal
                if not handled:
                    self.set_font("DejaVu", "", 10)
                    #self.cell(3)
                    self.multi_cell(0, 7, line, align='J')
                    self.ln(0)


    # Tableaux du chapitre Récapitulatif       
        
        def table_title(self, title):
            self.set_font("DejaVu", "BI", 10)
            self.set_text_color(80, 80, 80)
            self.cell(0, 6, f"Tableau {self.table_counter} : {title}", ln=True)
            self.ln(4)
            self.table_counter += 1

        def add_table_chiffres_cles(self, data):
            self.table_title("Les chiffres clés")
            self.set_font("DejaVu", "", 9)
            with self.table(width=180, col_widths=(100, 80)) as table:
                for row_data in data:
                    row = table.row()
                    for i, cell in enumerate(row_data):
                        row.cell(cell, border="BOTTOM", padding=(2, 1), align="LEFT")
                        
        def add_table_points_forts(self, data):
            self.table_title("Points forts et axes d'amélioration identifiés")
            self.set_font("DejaVu", "", 9)
            with self.table(width=180, borders_layout="MINIMAL") as table:
                for row_data in data:
                    row = table.row()
                    for cell in row_data:
                        row.cell(cell, padding=(1, 5, 1))

        def add_table_recommandations(self, data):
            self.table_title("Recommandations globales")
            self.set_font("DejaVu", "", 9)
            with self.table(width=180, col_widths=(15, 165), text_align=("CENTER", "JUSTIFY")) as table:
                for row_data in data:
                    row = table.row()
                    for cell in row_data:
                        row.cell(cell, border="BOTTOM", padding=(1, 1, 1))
                        
        def add_table_objectifs_a_ameliorer(self, data):
            self.table_title("Objectifs à améliorer")
            self.set_font("DejaVu", "", 9)
            with self.table(width=180, col_widths=(20, 70, 45, 45), text_align=("CENTER", "JUSTIFY", "JUSTIFY", "JUSTIFY")) as table:
                for row_data in data:
                    row = table.row()
                    for cell in row_data:
                        # Réduction du padding pour moins d’espace vertical
                        row.cell(cell, padding=(1.5, 2, 1.5))
                        
        def add_table_objectifs_conformes(self, data):
            self.table_title("Objectifs satisfaisants")
            self.set_font("DejaVu", "", 9)
            with self.table(width=180, text_align=("CENTER", "JUSTIFY", "CENTER")) as table:
                for row_data in data:
                    row = table.row()
                    for cell in row_data:
                        # Réduction du padding pour moins d’espace vertical
                        row.cell(cell, padding=(1.5, 2, 1.5))
                        
                        
    # Constitution du pdf

        def chapter_title(self, num, label):
            self.current_chapter_title = label
            self.set_y(30)

            self.set_fill_color(70, 130, 180)  # Badge vertical
            self.set_font("helvetica", "B", 14)
            self.cell(2, 18, "", fill=True, border=0)

            self.set_fill_color(250, 250, 250)
            self.set_text_color(25, 25, 112)
            self.set_draw_color(70, 130, 180)
            self.set_line_width(0.5)
            
            if getattr(self, "is_annexe", True):
                chapter_label = "Annexe"
                num = ""
            else:
                chapter_label = "Chapitre"
            
            self.cell(
                0,
                18,
                f"   {chapter_label} {num} : {label}",
                border="B",
                ln=True,
                align="L",
                fill=True
            )
            self.ln(6)

        def header(self):
            if self.is_page_de_garde:
                return
            
            self.set_fill_color(245, 248, 255)
            self.rect(12, 9.5, 185, 9, 'F')

            self.set_font("helvetica", "B", 10)
            self.set_draw_color(70, 130, 180)
            
            # Position initiale de la marge
            left_margin = self.l_margin
            right_margin = self.w - self.r_margin

            #self.set_y(self.get_y() + 3)
            y = self.get_y()

            # Gauche : titre fixe
            self.set_xy(left_margin, y)
            self.set_text_color(90, 90, 90)
            self.cell(0, 8, "Analyse des objectifs pédagogiques", align='L')
            
            if getattr(self, "is_chapter_start", False):
                return
            
            # Droite : nom du chapitre 
            self.set_xy(right_margin - 70, y)  
            
            self.set_text_color(25, 25, 112)
            
            if getattr(self, "is_annexe", True):
                chapter_label = "Annexe"
            else:
                chapter_label = "Chapitre"
                
            self.cell(
                70,
                8,
                f"chapter_label : {self.current_chapter_title}",
                border="B",
                ln=True,
                align="R"
            )
        
            self.ln(12)

        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", style="I", size=8)
            self.set_text_color(128)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

        def add_page_de_garde(self, titre, sous_titre, auteur=None, date=None):
            self.is_page_de_garde = True
            self.add_page()
            self.set_font("DejaVu", 'B', 20)

            # Titre principal centré
            self.ln(60)  # espace vers le bas
            self.set_text_color(25, 25, 112)
            self.multi_cell(0, 15, titre, ln=True, align='C')

            # Sous-titre
            self.set_font("DejaVu", '', 13)
            self.set_text_color(0, 0, 0)
            self.ln(10)
            self.multi_cell(0, 10, sous_titre, ln=True, align='C')

            # Auteur et date
            self.set_font("DejaVu", 'I', 12)
            self.set_text_color(100, 100, 100)
            if auteur:
                self.ln(40)
                self.cell(0, 10, f"Établi par : {auteur}", ln=True, align='C')
            if date:
                self.cell(0, 10, f"Date : {date}", ln=True, align='C')

        def add_disclaimer(self):
            self.is_page_de_garde = True
            self.add_page()
            
            # Encadré stylisé
            pdf.set_fill_color(240, 240, 255)  # Fond très léger (bleuté)
            pdf.set_draw_color(25, 25, 112)    # Bordure = couleur d'accent
            pdf.set_line_width(0.5)
            pdf.rect(x=10, y=30, w=190, h=70, style='D')  # Dessiner le cadre
            
            # Titre du disclaimer
            pdf.set_xy(10, 35)
            pdf.set_font("DejaVu", 'B', 14)
            pdf.set_text_color(25, 25, 112)  # Couleur d'accent
            pdf.cell(0, 10, "AVERTISSEMENT - Contenu généré par IA", ln=True, align="C")

            # Corps du texte
            pdf.set_xy(15, 50)
            pdf.set_font("Helvetica", size=12)
            pdf.set_text_color(0)  # Noir
            pdf.multi_cell(180, 8,
                """
                    Ces recommandations sont générées automatiquement par un système d'intelligence artificielle.
                    Elles visent à guider, non à remplacer l'expertise pédagogique humaine, et doivent être examinées avec discernement avant toute utilisation.""")

            
        # Constitution du chapitre récapitulatif
        
        def add_recap_tables(self, table_chif, table_axes, table_recom, table_ameliorer, table_conformes):
            self.current_chapter_title = "Synthèse des résultats"
            self.is_page_de_garde = False
            self.is_chapter_start = True         
            self.add_page()
            self.chapter_title(3, "Synthèse des résultats")
            self.is_chapter_start = False
            
            self.ln(10)
            
            self.add_table_objectifs_a_ameliorer(table_ameliorer)
            self.ln(14)

            self.add_table_objectifs_conformes(table_conformes)
            self.ln(14)
            
            # Ligne de séparation 
            
            self.add_table_chiffres_cles(table_chif)
            self.ln(14)
            
            self.add_table_points_forts(table_axes)
            self.ln(14)

            self.add_table_recommandations(table_recom)
            

            

        # Constitution du chapitre rappel infos cours
    
        def rappel_infos_cours(self, nom_cours, niveau, public, objectif_general, objectifs_specifiques_brut):
            self.current_chapter_title = "Rappel des informations de cours"
            self.is_page_de_garde = False
            self.is_chapter_start = True 
            self.add_page()
            self.chapter_title(1, "Rappel des informations de cours")
            self.is_chapter_start = False
            
            # Cours
            self.set_font("DejaVu", "B", 10)
            self.write(8, "Cours : ")
            self.set_font("DejaVu", "", 10)
            self.write(8, nom_cours)
            self.ln(8)
            
            # Niveau
            self.set_font("DejaVu", "B", 10)
            self.write(8, "Niveau : ")
            self.set_font("DejaVu", "", 10)
            self.write(8, niveau)
            self.ln(8)
            
            # Public cible
            self.set_font("DejaVu", "B", 10)
            self.write(8, "Public cible : ")
            self.set_font("DejaVu", "", 10)
            self.write(8, public)
            self.ln(8)
            
            # Objectif général 
            self.set_font("DejaVu", "B", 10)
            self.set_text_color(25, 25, 112)
            self.write(8, "Objectif général  :")
            
            self.ln()
            self.set_font("DejaVu", "", 10)
            self.set_text_color(0, 0, 0)
            self.cell(3)
            self.multi_cell(0, 7, objectif_general, align='J')
            self.ln(8)
            
            # Objectifs spécifiques 
            self.set_font("DejaVu", "B", 10)
            self.set_text_color(25, 25, 112)
            self.write(8, "Objectifs spécifiques  :")
            
            self.ln()
            self.set_font("DejaVu", "", 10)
            self.set_text_color(0, 0, 0)
            self.cell(3)
            self.multi_cell(0, 7, objectifs_specifiques_brut, align='J')

        def add_methode_analyse(self):
            self.is_annexe = True
            self.current_chapter_title = "Méthode d’analyse"
            self.is_page_de_garde = False
            self.is_chapter_start = True
            self.add_page()
            self.chapter_title(5, "Méthode d’analyse utilisée")

            self.set_font("DejaVu", "", 11)
            self.multi_cell(0, 8, 
                "Notre assistant intelligent procède à une analyse en plusieurs étapes pour évaluer et améliorer vos objectifs pédagogiques :",
                align="J")
            self.ln(6)

            # Étape 1
            self.set_font("DejaVu", "B", 12)
            self.set_text_color(25, 25, 112)
            self.cell(0, 8, "1. Classification selon la taxonomie de Bloom", ln=True)
            self.set_font("DejaVu", "", 11)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 8,
                "Une fiche explicative et une base de données regroupant des verbes d’action classés selon les six niveaux hiérarchiques de la taxonomie de Bloom permettent de catégoriser chaque objectif pédagogique :",
                align="J")
            self.ln(2)
            niveaux = ["- Connaître", "- Comprendre", "- Appliquer", "- Analyser", "- Évaluer", "- Créer"]
            for niveau in niveaux:
                self.cell(5)
                self.cell(0, 7, niveau, ln=True)
            self.ln(2)
            self.multi_cell(0, 8,
                "Cela permet de déterminer le niveau cognitif visé et de détecter les incohérences entre les verbes et le niveau annoncé.",
                align="J")
            self.ln(6)

            # Étape 2
            self.set_font("DejaVu", "B", 12)
            self.set_text_color(25, 25, 112)
            self.cell(0, 8, "2. Évaluation multicritère", ln=True)
            self.set_font("DejaVu", "", 11)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 8,
                "Chaque objectif est évalué selon plusieurs critères inspirés du modèle SMART, adaptés au contexte pédagogique. Pour être rigoureux, un objectif doit remplir les critères suivants :", align="J")
            self.ln(2)
            criteres = [
                ("Spécifique", "L’objectif doit être clairement formulé, sans ambiguïté, à l’aide d’un vocabulaire compréhensible. Il précise des comportements observables dans un contexte donné."),
                ("Mesurable", "Il permet une évaluation fiable grâce à des verbes d’action observables. Un seul verbe est recommandé."),
                ("Approprié (Cohérent)", "Il est aligné avec le contenu du cours, le niveau d’étude, le public cible, et l’objectif général."),
                ("Réaliste", "Il est atteignable dans le cadre temporel et matériel prévu."),
                ("Temporellement défini", "Il précise un délai, une échéance ou des jalons clairs.")
            ]
            for titre, texte in criteres:
                self.set_font("DejaVu", "B", 11)
                self.cell(0, 7, f"• {titre}", ln=True)
                self.set_font("DejaVu", "", 11)
                self.multi_cell(0, 8, texte, align="J")
                self.ln(1)
            self.multi_cell(0, 8,
                "Ces critères sont complétés par des règles de rédaction pédagogiques, et chaque objectif reçoit une note sur 5 pour chaque critère.",
                align="J")
            self.ln(6)

            # Étape 3
            self.set_font("DejaVu", "B", 12)
            self.set_text_color(25, 25, 112)
            self.cell(0, 8, "3. Amélioration des objectifs", ln=True)
            self.set_font("DejaVu", "", 11)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 8,
                "En cas de non-conformité, des suggestions d’amélioration personnalisées sont générées pour aider à reformuler les objectifs selon les bonnes pratiques.",
                align="J")
            self.ln(6)

            # Étape 4
            self.set_font("DejaVu", "B", 12)
            self.set_text_color(25, 25, 112)
            self.cell(0, 8, "4. Synthèse", ln=True)
            self.set_font("DejaVu", "", 11)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 8,
                "Un rapport structuré est généré avec un aperçu global des résultats, une analyse détaillée et plusieurs tableaux récapitulatifs.",
                align="J")

            self.is_annexe = True

        def chapter_body(self, text):
            self.set_font("DejaVu", size=12)
            self.is_chapter_start = False  
            self.write_markdown(text)
            self.ln()
            self.set_font("DejaVu", "I", 10)
            #self.cell(0, 5, "(fin du chapitre)", ln=True)

        def print_chapter(self, num, title, text):
            self.current_chapter_title = title
            self.is_page_de_garde = False
            self.is_annexe = False
            self.is_chapter_start = True  # Active la logique "pas de header"
            self.add_page()
            self.chapter_title(num, title)
            self.chapter_body(text)

    pdf = PDF()
    pdf.set_title("Analyse automatique des objectifs pédagogiques")
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    #pdf.set_author("ObjectifsAI")
    pdf.add_page_de_garde(
        titre=f"Rapport d’analyse des objectifs pédagogiques du cours de {nom_cours}",
        sous_titre="Évaluation des objectifs pédagogique selon la taxonomie de Bloom et des critères SMART adaptés au contexte pédagogique",
        #auteur="ObjectifsAI",
        date = format_date(datetime.now(), format='d MMMM y', locale='fr')    )

    pdf.add_disclaimer()
    pdf.rappel_infos_cours(nom_cours, niveau, public, objectif_general, objectifs_specifiques_brut)
    pdf.print_chapter(2, "Aperçu global de l'analyse", rapport['aperçu'])
    
    table_chif, table_axes, table_recom, table_ameliorer, table_conformes = build_tables_from_recap_dict(recap_dict)
    pdf.add_recap_tables(table_chif, table_axes, table_recom, table_ameliorer, table_conformes)
    
    pdf.print_chapter(4, "Analyse détaillée", rapport['details'])
    pdf.add_methode_analyse()

    # Sauvegarde temporaire
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name 
