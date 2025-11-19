#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Rental Contract Generator - Complete Version
Generates a complete PDF rental contract following the official French template
"""

import json
import sys
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    KeepTogether,
    Indenter,
    ListFlowable,
    ListItem,
)
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import HRFlowable


class CompletRentalContractGenerator:
    """
    Complete rental contract PDF generator following official French template
    """

    def __init__(self, json_file, output_file="contrat_location_complet.pdf"):
        """
        Initialize the generator

        Args:
            json_file: Path to JSON file with contract data
            output_file: Path to output PDF file
        """
        self.json_file = json_file
        self.output_file = output_file
        self.data = None
        self.story = []
        self.styles = None
        self._load_data()
        self._setup_styles()

    def _load_data(self):
        """Load and validate JSON data"""
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            print(f"✓ Data loaded from {self.json_file}")
        except FileNotFoundError:
            print(f"✗ Error: File {self.json_file} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ Error: Invalid JSON: {e}")
            sys.exit(1)

    def _setup_styles(self):
        """Setup custom styles for PDF generation"""
        self.styles = getSampleStyleSheet()

        # Main title
        self.styles.add(
            ParagraphStyle(
                name="MainTitle",
                parent=self.styles["Title"],
                fontSize=13,
                textColor=colors.black,
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        # Subtitle
        self.styles.add(
            ParagraphStyle(
                name="Subtitle",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#333333"),
                alignment=TA_CENTER,
                spaceAfter=15,
                fontName="Helvetica-Oblique",
            )
        )

        # Section title (Roman numerals)
        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading1"],
                fontSize=11,
                textColor=colors.black,
                spaceBefore=12,
                spaceAfter=8,
                fontName="Helvetica-Bold",
            )
        )

        # Subsection title (A, B, C...)
        self.styles.add(
            ParagraphStyle(
                name="SubsectionTitle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceBefore=8,
                spaceAfter=5,
                fontName="Helvetica-Bold",
            )
        )

        # Normal text
        self.styles.add(
            ParagraphStyle(
                name="NormalText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.black,
                alignment=TA_LEFT,
            )
        )

        # Justified text
        self.styles.add(
            ParagraphStyle(
                name="Justified",
                parent=self.styles["Normal"],
                fontSize=9,
                alignment=TA_JUSTIFY,
                spaceBefore=3,
                spaceAfter=3,
            )
        )

        # Small italic
        self.styles.add(
            ParagraphStyle(
                name="SmallItalic",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#666666"),
                fontName="Helvetica-Oblique",
                spaceBefore=2,
                spaceAfter=2,
            )
        )

        # Field text
        self.styles.add(
            ParagraphStyle(
                name="FieldText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.black,
                leftIndent=10,
            )
        )

        # Checkbox style
        self.styles.add(
            ParagraphStyle(
                name="Checkbox", parent=self.styles["Normal"], fontSize=9, leftIndent=20
            )
        )

    def _get_value(self, path, default=""):
        """Get value from nested dictionary"""
        keys = path.split(".")
        value = self.data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        if isinstance(value, dict) and "valeur" in value:
            return value["valeur"] or default

        return value or default

    def _format_date(self, date_str):
        """Format date to DD/MM/YYYY"""
        if not date_str:
            return ""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except:
            return date_str

    def _checkbox(self, checked=False, label=""):
        """Create checkbox representation"""
        box = "☑" if checked else "☐"
        return f"{box} {label}"

    def _add_field_line(self, label, value, bold_label=True):
        """Add a field line with label and value"""
        if value:
            if bold_label:
                text = f"<b>{label} :</b> {value}"
            else:
                text = f"{label} : {value}"
            self.story.append(Paragraph(text, self.styles["NormalText"]))

    def _add_checkbox_field(self, label, checked=False):
        """Add a checkbox field"""
        text = self._checkbox(checked, label)
        self.story.append(Paragraph(text, self.styles["Checkbox"]))

    def generate_pdf(self):
        """Generate the complete PDF"""
        # Create document
        doc = SimpleDocTemplate(
            self.output_file,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        # Build content
        self._build_complete_content()

        # Generate PDF
        try:
            doc.build(self.story)
            print(f"✓ Complete PDF generated: {self.output_file}")
        except Exception as e:
            print(f"✗ Error generating PDF: {e}")
            sys.exit(1)

    def _build_complete_content(self):
        """Build complete document content following official template"""

        # TITLE SECTION
        self.story.append(
            Paragraph(
                "CONTRAT TYPE DE LOCATION OU DE COLOCATION DE LOGEMENT MEUBLÉ",
                self.styles["MainTitle"],
            )
        )

        self.story.append(
            Paragraph(
                "(Soumis au titre Ier bis de la loi du 6 juillet 1989 tendant à améliorer les rapports locatifs<br/>"
                "et portant modification de la loi n° 86-1290 du 23 décembre 1986)",
                self.styles["Subtitle"],
            )
        )

        # Legal framework
        self.story.append(Spacer(1, 5 * mm))
        self.story.append(
            Paragraph(
                "<b>Champ du contrat type :</b> Le présent contrat type de location est applicable aux locations et aux colocations "
                "de logement meublé qui constitue la résidence principale du preneur, à l'exception :",
                self.styles["Justified"],
            )
        )
        self.story.append(
            Paragraph(
                "1 - des colocations formalisées par la conclusion de plusieurs contrats entre les locataires et le bailleur ;<br/>"
                "2 - des locations de logement appartenant à un organisme d'habitation à loyer modéré.",
                self.styles["SmallItalic"],
            )
        )

        self.story.append(Spacer(1, 8 * mm))

        # SECTION I: DÉSIGNATION DES PARTIES
        self.story.append(
            Paragraph("I. DÉSIGNATION DES PARTIES", self.styles["SectionTitle"])
        )
        self.story.append(
            Paragraph(
                "Le présent contrat est conclu entre les soussignés :",
                self.styles["NormalText"],
            )
        )
        self.story.append(Spacer(1, 3 * mm))

        # Bailleur
        self.story.append(Paragraph("<b>LE BAILLEUR :</b>", self.styles["NormalText"]))
        nom_bailleur = self._get_value(
            "designation_parties.bailleur.nom_prenom_ou_denomination"
        )
        adresse_bailleur = self._get_value(
            "designation_parties.bailleur.adresse_siege_social"
        )
        email_bailleur = self._get_value("designation_parties.bailleur.email")

        self._add_field_line("Nom et prénom, ou dénomination du bailleur", nom_bailleur)
        self._add_field_line("Domicile ou siège social du bailleur", adresse_bailleur)
        if email_bailleur:
            self._add_field_line(
                "Adresse e-mail du bailleur (facultatif)", email_bailleur
            )

        # Type de personne
        type_personne = self._get_value("designation_parties.bailleur.type_personne")
        if type_personne:
            self._add_field_line("Qualité du bailleur", type_personne)

        # Société civile familiale
        if type_personne == "Personne morale":
            is_familiale = self._get_value(
                "designation_parties.bailleur.societe_civile_familiale"
            )
            if is_familiale is not None:
                text = "Société civile constituée exclusivement entre parents et alliés jusqu'au 4ème degré inclus : "
                text += "OUI" if is_familiale else "NON"
                self.story.append(Paragraph(text, self.styles["NormalText"]))

        # Mandataire
        has_mandataire = self._get_value(
            "designation_parties.bailleur.mandataire.existe"
        )
        if has_mandataire:
            self.story.append(Spacer(1, 3 * mm))
            self.story.append(
                Paragraph(
                    "Représenté par le <b>MANDATAIRE</b> :", self.styles["NormalText"]
                )
            )
            nom_mandataire = self._get_value(
                "designation_parties.bailleur.mandataire.details.nom_raison_sociale"
            )
            adresse_mandataire = self._get_value(
                "designation_parties.bailleur.mandataire.details.adresse"
            )
            carte_pro = self._get_value(
                "designation_parties.bailleur.mandataire.details.numero_carte_pro"
            )

            self._add_field_line(
                "Nom ou raison sociale et adresse du mandataire", nom_mandataire
            )
            if adresse_mandataire:
                self._add_field_line("Adresse", adresse_mandataire)
            if carte_pro:
                self._add_field_line(
                    "N° et lieu de délivrance de la carte professionnelle", carte_pro
                )

        self.story.append(
            Paragraph("désigné(s) ci-après le « bailleur »", self.styles["SmallItalic"])
        )
        self.story.append(Spacer(1, 5 * mm))

        # Locataires
        self.story.append(Paragraph("<b>ET :</b>", self.styles["NormalText"]))
        self.story.append(
            Paragraph("<b>LE(S) LOCATAIRE(S) :</b>", self.styles["NormalText"])
        )

        locataires = (
            self.data.get("designation_parties", {})
            .get("locataires", {})
            .get("liste", [])
        )
        for i, locataire in enumerate(locataires):
            nom = locataire.get("nom_prenom", {}).get("valeur", "")
            email = locataire.get("email", {}).get("valeur", "")
            if nom:
                self._add_field_line("Nom et prénom du locataire", nom)
                if email:
                    self._add_field_line(
                        "Adresse e-mail du locataire (facultatif)", email
                    )

        # Garants
        garants = (
            self.data.get("designation_parties", {}).get("garants", {}).get("liste", [])
        )
        if garants and garants[0].get("noms", {}).get("valeur"):
            self.story.append(Spacer(1, 3 * mm))
            self.story.append(
                Paragraph("<b>LE(S) GARANT(S) :</b>", self.styles["NormalText"])
            )
            for garant in garants:
                noms = garant.get("noms", {}).get("valeur", "")
                adresse = garant.get("adresse", {}).get("valeur", "")
                if noms:
                    self._add_field_line(
                        "Noms et adresse des garants",
                        f"{noms}, {adresse}" if adresse else noms,
                    )

        self.story.append(
            Paragraph(
                "désigné(s) ci-après le « locataire »", self.styles["SmallItalic"]
            )
        )
        self.story.append(Spacer(1, 8 * mm))

        # SECTION II: OBJET DU CONTRAT
        self.story.append(
            Paragraph("II. OBJET DU CONTRAT", self.styles["SectionTitle"])
        )
        self.story.append(
            Paragraph(
                "Le présent contrat a pour objet la location d'un logement ainsi déterminé :",
                self.styles["NormalText"],
            )
        )
        self.story.append(Spacer(1, 5 * mm))

        # A. Consistance du logement
        self.story.append(
            Paragraph("A. Consistance du logement", self.styles["SubsectionTitle"])
        )

        # Address and basic info
        adresse_logement = self._get_value("objet_contrat.logement.adresse_complete")
        self._add_field_line("Localisation du logement", adresse_logement)

        id_fiscal = self._get_value("objet_contrat.logement.identifiant_fiscal")
        if id_fiscal:
            self._add_field_line("Identifiant fiscal du logement", id_fiscal)

        # Type and regime
        type_habitat = self._get_value("objet_contrat.logement.type_habitat")
        self._add_field_line("Type d'habitat", type_habitat)

        regime = self._get_value("objet_contrat.logement.regime_juridique")
        self._add_field_line("Régime juridique de l'immeuble", regime)

        # Construction period
        periode = self._get_value("objet_contrat.logement.periode_construction")
        self._add_field_line("Période de construction", periode)

        # Surface and rooms
        surface = self._get_value("objet_contrat.logement.surface_habitable_m2")
        self._add_field_line("Surface habitable", f"{surface} m²")

        pieces = self._get_value("objet_contrat.logement.nombre_pieces_principales")
        self._add_field_line("Nombre de pièces principales", str(pieces))

        # Other parts
        self.story.append(Spacer(1, 3 * mm))
        autres_parties = (
            self.data.get("objet_contrat", {})
            .get("logement", {})
            .get("autres_parties", {})
        )
        if any(autres_parties.values()):
            self.story.append(
                Paragraph("Autres parties du logement :", self.styles["NormalText"])
            )
            if autres_parties.get("terrasse", {}).get("valeur"):
                self._add_checkbox_field("Terrasse", True)
            if autres_parties.get("balcon", {}).get("valeur"):
                self._add_checkbox_field("Balcon", True)
            if autres_parties.get("cave", {}).get("valeur"):
                self._add_checkbox_field("Cave", True)
            if autres_parties.get("parking", {}).get("valeur"):
                self._add_checkbox_field("Parking", True)

        # Equipment
        equipements = self._get_value("objet_contrat.logement.equipements_meubles")
        if equipements:
            self.story.append(Spacer(1, 3 * mm))
            self._add_field_line("Éléments d'équipements du logement", equipements)

        # Heating and hot water
        self.story.append(Spacer(1, 3 * mm))
        chauffage_mode = self._get_value("objet_contrat.logement.chauffage.mode")
        self._add_field_line("Modalité de production de chauffage", chauffage_mode)

        if chauffage_mode == "Collectif":
            repartition = self._get_value(
                "objet_contrat.logement.chauffage.si_collectif_repartition"
            )
            if repartition:
                self._add_field_line(
                    "Si collectif, répartition", repartition, bold_label=False
                )

        eau_chaude = self._get_value("objet_contrat.logement.eau_chaude.mode")
        self._add_field_line(
            "Modalité de production d'eau chaude sanitaire", eau_chaude
        )

        if eau_chaude == "Collectif":
            repartition = self._get_value(
                "objet_contrat.logement.eau_chaude.si_collectif_repartition"
            )
            if repartition:
                self._add_field_line(
                    "Si collectif, répartition", repartition, bold_label=False
                )

        # Energy performance with legal reminder
        self.story.append(Spacer(1, 5 * mm))
        self.story.append(
            Paragraph(
                "<i>Rappel : un logement décent doit respecter les critères minimaux de performance suivants :<br/>"
                "a) En France métropolitaine :<br/>"
                "- À compter du 1er janvier 2025 : classe F du DPE<br/>"
                "- À compter du 1er janvier 2028 : classe E du DPE<br/>"
                "- À compter du 1er janvier 2034 : classe D du DPE</i>",
                self.styles["SmallItalic"],
            )
        )

        dpe = self._get_value(
            "objet_contrat.logement.performance_energetique.classe_dpe"
        )
        self.story.append(Spacer(1, 3 * mm))
        self._add_field_line("Niveau de performance du logement", f"Classe {dpe}")

        # B. Destination des locaux
        self.story.append(Spacer(1, 5 * mm))
        self.story.append(
            Paragraph("B. Destination des locaux", self.styles["SubsectionTitle"])
        )
        usage = self._get_value("objet_contrat.destination_locaux.usage")
        self.story.append(
            Paragraph(f"{self._checkbox(True)} {usage}", self.styles["Checkbox"])
        )

        # C. Locaux accessoires privatifs
        accessoires = self.data.get("objet_contrat", {}).get(
            "accessoires_privatifs", {}
        )
        if accessoires.get("cave", {}).get("valeur") or accessoires.get(
            "garage_parking", {}
        ).get("valeur"):
            self.story.append(Spacer(1, 5 * mm))
            self.story.append(
                Paragraph(
                    "C. Désignation des locaux et équipements accessoires privatifs",
                    self.styles["SubsectionTitle"],
                )
            )

            if accessoires.get("cave", {}).get("valeur"):
                cave_num = accessoires.get("cave_numero", {}).get("valeur", "")
                text = f"Cave lot n° {cave_num}" if cave_num else "Cave"
                self._add_checkbox_field(text, True)

            if accessoires.get("garage_parking", {}).get("valeur"):
                self._add_checkbox_field("Garage/Parking", True)

        # D. Parties communes
        parties_communes = self.data.get("objet_contrat", {}).get(
            "parties_communes", {}
        )
        if any(parties_communes.values()):
            self.story.append(Spacer(1, 5 * mm))
            self.story.append(
                Paragraph(
                    "D. Énumération des locaux, parties, équipements et accessoires à usage commun",
                    self.styles["SubsectionTitle"],
                )
            )

            if parties_communes.get("chauffage_collectif", {}).get("valeur"):
                self._add_checkbox_field("Chauffage collectif", True)
            if parties_communes.get("local_poubelle", {}).get("valeur"):
                self._add_checkbox_field("Local poubelle", True)
            if parties_communes.get("garage_velo", {}).get("valeur"):
                self._add_checkbox_field("Garage à vélo", True)
            if parties_communes.get("ascenseur", {}).get("valeur"):
                self._add_checkbox_field("Ascenseur", True)
            if parties_communes.get("interphone", {}).get("valeur"):
                self._add_checkbox_field("Interphone/Digicode", True)
            if parties_communes.get("fibre", {}).get("valeur"):
                self._add_checkbox_field("Fibre optique", True)

        self.story.append(Spacer(1, 8 * mm))

        # SECTION III: DATE DE PRISE D'EFFET ET DURÉE
        self.story.append(
            Paragraph(
                "III. DATE DE PRISE D'EFFET ET DURÉE DU CONTRAT",
                self.styles["SectionTitle"],
            )
        )
        self.story.append(
            Paragraph(
                "La durée du contrat et sa date de prise d'effet sont ainsi définies :",
                self.styles["NormalText"],
            )
        )
        self.story.append(Spacer(1, 3 * mm))

        date_effet = self._format_date(
            self._get_value("duree_contrat.date_prise_effet")
        )
        self._add_field_line("A. Date de prise d'effet du contrat", date_effet)

        duree = self._get_value("duree_contrat.duree_bail")
        self._add_field_line("B. Durée du contrat", duree)

        self.story.append(Spacer(1, 3 * mm))
        self.story.append(
            Paragraph(
                "<i>À l'exception des locations consenties à un étudiant pour une durée de neuf mois, "
                "les contrats de location de logements meublés sont reconduits tacitement à leur terme "
                "pour une durée d'un an et dans les mêmes conditions. Le locataire peut mettre fin au bail "
                "à tout moment, après avoir donné congé. Le bailleur peut, quant à lui, mettre fin au bail "
                "à son échéance et après avoir donné congé, soit pour reprendre le logement en vue de l'occuper "
                "lui-même ou une personne de sa famille, soit pour le vendre, soit pour un motif sérieux et légitime.</i>",
                self.styles["SmallItalic"],
            )
        )

        self.story.append(Spacer(1, 8 * mm))

        # SECTION IV: CONDITIONS FINANCIÈRES
        self.story.append(
            Paragraph("IV. CONDITIONS FINANCIÈRES", self.styles["SectionTitle"])
        )
        self.story.append(
            Paragraph(
                "Les parties conviennent des conditions financières suivantes :",
                self.styles["NormalText"],
            )
        )
        self.story.append(Spacer(1, 5 * mm))

        # A. Loyer
        self.story.append(Paragraph("A. Loyer", self.styles["SubsectionTitle"]))
        self.story.append(
            Paragraph("1° Fixation du loyer initial :", self.styles["NormalText"])
        )

        loyer = self._get_value("conditions_financieres.loyer.montant_hors_charges")
        self._add_field_line("a) Montant du loyer mensuel", f"{loyer} €")

        # Zone tendue
        zone_tendue = self._get_value(
            "conditions_financieres.loyer.zone_tendue_encadrement.soumis"
        )
        if zone_tendue:
            self.story.append(Spacer(1, 3 * mm))
            self.story.append(
                Paragraph(
                    "b) Modalités particulières de fixation initiale du loyer "
                    "applicables dans certaines zones tendues :",
                    self.styles["NormalText"],
                )
            )

            text = "Le loyer du logement objet du présent contrat est soumis au décret fixant "
            text += "annuellement le montant maximum d'évolution des loyers à la relocation : "
            text += "OUI" if zone_tendue else "NON"
            self.story.append(Paragraph(text, self.styles["FieldText"]))

            loyer_ref = self._get_value(
                "conditions_financieres.loyer.zone_tendue_encadrement.loyer_reference"
            )
            loyer_maj = self._get_value(
                "conditions_financieres.loyer.zone_tendue_encadrement.loyer_reference_majore"
            )
            if loyer_ref or loyer_maj:
                text = f"Montant du loyer de référence : {loyer_ref} €/m² / "
                text += f"Montant du loyer de référence majoré : {loyer_maj} €/m²"
                self.story.append(Paragraph(text, self.styles["FieldText"]))

            complement = self._get_value(
                "conditions_financieres.loyer.zone_tendue_encadrement.complement_loyer"
            )
            if complement:
                self._add_field_line(
                    "Complément de loyer", f"{complement} €", bold_label=False
                )

        # Previous tenant info
        depart_recent = self._get_value(
            "conditions_financieres.loyer.precedent_locataire.depart_moins_18_mois"
        )
        if depart_recent:
            self.story.append(Spacer(1, 3 * mm))
            self.story.append(
                Paragraph(
                    "c) Informations relatives au loyer du dernier locataire :",
                    self.styles["NormalText"],
                )
            )
            montant_prec = self._get_value(
                "conditions_financieres.loyer.precedent_locataire.montant_dernier_loyer"
            )
            date_prec = self._format_date(
                self._get_value(
                    "conditions_financieres.loyer.precedent_locataire.date_dernier_versement"
                )
            )

            if montant_prec:
                self._add_field_line(
                    "Montant du dernier loyer acquitté par le précédent locataire",
                    f"{montant_prec} €",
                    bold_label=False,
                )
            if date_prec:
                self._add_field_line("Date de versement", date_prec, bold_label=False)

        # Revision
        self.story.append(Spacer(1, 3 * mm))
        self.story.append(
            Paragraph("2° Modalités de révision :", self.styles["NormalText"])
        )
        date_rev = self._get_value(
            "conditions_financieres.revision_loyer.date_revision"
        )
        trimestre = self._get_value(
            "conditions_financieres.revision_loyer.trimestre_reference_irl"
        )

        self._add_field_line("a) Date de révision", date_rev, bold_label=False)
        self._add_field_line(
            "b) Trimestre de référence de l'IRL", trimestre, bold_label=False
        )

        # B. Charges
        self.story.append(Spacer(1, 5 * mm))
        self.story.append(
            Paragraph("B. Charges récupérables", self.styles["SubsectionTitle"])
        )

        modalite_charges = self._get_value(
            "conditions_financieres.charges.modalite_reglement"
        )
        montant_charges = self._get_value("conditions_financieres.charges.montant")

        self.story.append(
            Paragraph(
                "1. Modalité de règlement des charges récupérables :",
                self.styles["NormalText"],
            )
        )
        if modalite_charges == "Forfait":
            self._add_checkbox_field(
                "Récupération des charges par le bailleur sous la forme d'un forfait",
                True,
            )
        elif modalite_charges == "Provisions":
            self._add_checkbox_field(
                "Provisions sur charges avec régularisation annuelle", True
            )

        self._add_field_line("2. Montant", f"{montant_charges} €")

        if modalite_charges == "Forfait":
            self.story.append(
                Paragraph(
                    "3. Modalités de révision du forfait de charges : "
                    "Le montant du forfait de charges sera révisé chaque année "
                    "aux mêmes conditions que le loyer principal, selon la variation de l'IRL.",
                    self.styles["FieldText"],
                )
            )

        # C. Colocation insurance
        est_coloc = self._get_value("colocation.est_colocation")
        if est_coloc:
            self.story.append(Spacer(1, 5 * mm))
            self.story.append(
                Paragraph(
                    "C. En cas de colocation, souscription par le bailleur "
                    "d'une assurance pour le compte des colocataires",
                    self.styles["SubsectionTitle"],
                )
            )
            assurance = self._get_value("colocation.assurance_bailleur")
            text = f"Assurance souscrite : {'OUI' if assurance else 'NON'}"
            self.story.append(Paragraph(text, self.styles["NormalText"]))

            if assurance:
                montant_assur = self._get_value("colocation.montant_assurance")
                if montant_assur:
                    self._add_field_line(
                        "Montant mensuel récupérable", f"{montant_assur} €"
                    )

        # D. Payment modalities
        self.story.append(Spacer(1, 5 * mm))
        self.story.append(
            Paragraph("D. Modalités de paiement", self.styles["SubsectionTitle"])
        )

        self._add_field_line("Périodicité du paiement", "Mensuelle")
        type_paiement = self._get_value("conditions_financieres.paiement.type_paiement")
        self._add_field_line("Paiement", type_paiement)
        jour = self._get_value("conditions_financieres.paiement.jour_paiement")
        self._add_field_line("Date ou période de paiement", f"Le {jour} du mois")

        self.story.append(Spacer(1, 3 * mm))
        self.story.append(
            Paragraph(
                "Montant total dû à la première échéance de paiement :",
                self.styles["NormalText"],
            )
        )

        premier_loyer = self._get_value(
            "conditions_financieres.premier_versement.loyer"
        )
        premier_charges = self._get_value(
            "conditions_financieres.premier_versement.charges"
        )
        premier_total = self._get_value(
            "conditions_financieres.premier_versement.montant_total"
        )

        self._add_field_line("Loyer", f"{premier_loyer} €", bold_label=False)
        self._add_field_line("Charges", f"{premier_charges} €", bold_label=False)
        self._add_field_line(
            "<b>TOTAL</b>", f"<b>{premier_total} €</b>", bold_label=False
        )

        # E. Energy expenses
        self.story.append(Spacer(1, 5 * mm))
        self.story.append(
            Paragraph(
                "E. Dépenses énergétiques (pour information)",
                self.styles["SubsectionTitle"],
            )
        )

        depenses = self._get_value(
            "conditions_financieres.depenses_energetiques.estimation_annuelle"
        )
        annee_ref = self._get_value(
            "conditions_financieres.depenses_energetiques.annee_reference"
        )

        text = f"Montant estimé des dépenses annuelles d'énergie pour un usage standard : {depenses} "
        text += f"(estimation réalisée à partir des prix énergétiques de référence de l'année {annee_ref})"
        self.story.append(Paragraph(text, self.styles["NormalText"]))

        self.story.append(Spacer(1, 8 * mm))

        # SECTION V: TRAVAUX
        self.story.append(Paragraph("V. TRAVAUX", self.styles["SectionTitle"]))

        travaux_effectues = self._get_value("travaux.effectues_depuis_dernier_bail")
        if travaux_effectues:
            self.story.append(
                Paragraph(
                    "A. Montant et nature des travaux d'amélioration ou de mise en conformité "
                    "effectués depuis la fin du dernier contrat de location",
                    self.styles["SubsectionTitle"],
                )
            )

            description = self._get_value("travaux.description")
            montant = self._get_value("travaux.montant")

            if description:
                self.story.append(Paragraph(description, self.styles["NormalText"]))
            if montant:
                self._add_field_line("Montant total des travaux", f"{montant} €")
        else:
            self._add_field_line("Travaux effectués depuis le dernier bail", "Néant")

        self.story.append(Spacer(1, 3 * mm))
        self._add_field_line(
            "B. Majoration du loyer en cours de bail consécutive à des travaux", "Néant"
        )
        self._add_field_line(
            "C. Diminution de loyer en cours de bail consécutive à des travaux entrepris par le locataire",
            "Néant",
        )

        self.story.append(Spacer(1, 8 * mm))

        # SECTION VI: GARANTIES
        self.story.append(Paragraph("VI. GARANTIES", self.styles["SectionTitle"]))

        depot = self._get_value("garanties.montant_depot_garantie")
        self._add_field_line("Montant du dépôt de garantie", f"{depot} €")
        self.story.append(
            Paragraph(
                "<i>Rappel : Pour un logement meublé, le dépôt de garantie ne peut excéder deux mois de loyer hors charges.</i>",
                self.styles["SmallItalic"],
            )
        )

        self.story.append(Spacer(1, 8 * mm))

        # SECTION VII: CLAUSE DE SOLIDARITÉ
        if est_coloc:
            self.story.append(
                Paragraph("VII. CLAUSE DE SOLIDARITÉ", self.styles["SectionTitle"])
            )
            self.story.append(
                Paragraph(
                    "• Il est expressément stipulé que les copreneurs seront tenus solidairement et indivisiblement "
                    "de l'exécution des obligations du présent contrat.<br/>"
                    "• Si un colocataire délivrait congé et quittait les lieux, il resterait en tout état de cause "
                    "tenu du paiement des loyers et accessoires et de toutes les obligations du bail pendant une durée "
                    "de six mois à compter de la date d'effet du congé. Toutefois, cette solidarité prendra fin si un "
                    "nouveau colocataire, accepté par le bailleur, figure au présent contrat.<br/>"
                    "• La présente clause est une condition substantielle sans laquelle le présent bail n'aurait pas été consenti.",
                    self.styles["Justified"],
                )
            )
            self.story.append(Spacer(1, 8 * mm))

        # SECTION VIII: CLAUSE RÉSOLUTOIRE
        self.story.append(
            Paragraph("VIII. CLAUSE RÉSOLUTOIRE", self.styles["SectionTitle"])
        )
        self.story.append(
            Paragraph(
                "Le présent contrat sera résilié de plein droit :<br/>"
                "• en cas de défaut de paiement du loyer, des provisions de charge, ou de la régularisation annuelle de charge<br/>"
                "• en cas de défaut de versement du dépôt de garantie<br/>"
                "• en cas de défaut d'assurance des risques locatifs par le locataire<br/>"
                "• en cas de trouble de voisinage constaté par une décision de justice",
                self.styles["NormalText"],
            )
        )

        self.story.append(Spacer(1, 8 * mm))

        # SECTION IX: HONORAIRES
        agence = self._get_value("honoraires_location.agence_impliquee")
        if agence:
            self.story.append(
                Paragraph("IX. HONORAIRES DE LOCATION", self.styles["SectionTitle"])
            )

            self.story.append(
                Paragraph("A. Dispositions applicables", self.styles["SubsectionTitle"])
            )
            self.story.append(
                Paragraph(
                    "<i>Il est rappelé les dispositions du I de l'article 5 de la loi du 6 juillet 1989 : "
                    "La rémunération des personnes mandatées pour se livrer ou prêter leur concours à l'entremise "
                    "ou à la négociation d'une mise en location d'un logement est à la charge exclusive du bailleur, "
                    "à l'exception des honoraires liés aux prestations de visite, constitution de dossier et rédaction de bail "
                    "qui sont partagés entre le bailleur et le preneur.</i>",
                    self.styles["SmallItalic"],
                )
            )

            self.story.append(Spacer(1, 3 * mm))
            self.story.append(
                Paragraph(
                    "B. Détail et répartition des honoraires",
                    self.styles["SubsectionTitle"],
                )
            )

            part_locataire = self._get_value("honoraires_location.part_locataire")
            part_bailleur = self._get_value("honoraires_location.part_bailleur")

            if part_bailleur:
                self._add_field_line(
                    "1. Honoraires à la charge du bailleur", f"{part_bailleur} €"
                )
            if part_locataire:
                self._add_field_line(
                    "2. Honoraires à la charge du locataire", f"{part_locataire} €"
                )

        self.story.append(Spacer(1, 8 * mm))

        # SECTION X: ANNEXES
        self.story.append(Paragraph("X. ANNEXES", self.styles["SectionTitle"]))
        self.story.append(
            Paragraph(
                "Sont annexées et jointes au contrat de location les pièces suivantes :",
                self.styles["NormalText"],
            )
        )
        self.story.append(Spacer(1, 3 * mm))

        annexes = [
            "A. Un extrait du règlement concernant la destination de l'immeuble, la jouissance et l'usage "
            "des parties privatives et communes (le cas échéant)",
            "B. Un dossier de diagnostics techniques comprenant :",
            "   • un diagnostic de performance énergétique",
            "   • un constat de risque d'exposition au plomb pour les immeubles construits avant le 1er janvier 1949",
            "   • une copie d'un état mentionnant l'absence ou la présence de matériaux contenant de l'amiante",
            "   • un état de l'installation intérieure d'électricité et de gaz",
            "   • un état des risques naturels et technologiques",
            "C. Une notice d'information relative aux droits et obligations des locataires et des bailleurs",
            "D. Un état des lieux et un état détaillé du mobilier",
        ]

        for annexe in annexes:
            self.story.append(Paragraph(annexe, self.styles["NormalText"]))

        # Page break before signatures
        self.story.append(PageBreak())

        # SIGNATURES
        ville = self._get_value("signature.ville")
        date_signature = self._format_date(self._get_value("signature.date"))

        self.story.append(
            Paragraph(f"Fait à {ville}, le {date_signature}", self.styles["NormalText"])
        )
        self.story.append(Spacer(1, 10 * mm))

        # Signature table
        sig_data = [
            ["Signature du bailleur", "Signature du locataire"],
            [
                '(précédée de la mention\n"Lu et approuvé")',
                '(précédée de la mention\n"Lu et approuvé")',
            ],
            ["\n\n\n\n\n\n", "\n\n\n\n\n\n"],
        ]

        sig_table = Table(sig_data, colWidths=[8 * cm, 8 * cm])
        sig_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        self.story.append(sig_table)

        # Garant signatures if exists
        if garants and garants[0].get("noms", {}).get("valeur"):
            self.story.append(Spacer(1, 15 * mm))
            self.story.append(
                Paragraph("Signature du(des) garant(s)", self.styles["NormalText"])
            )
            self.story.append(
                Paragraph(
                    '(précédée de la mention "Lu et approuvé")',
                    self.styles["NormalText"],
                )
            )
            self.story.append(Spacer(1, 25 * mm))

        # Footer
        self.story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        self.story.append(
            Paragraph(
                "<i>Contrat type issu de l'annexe du décret du 29 mai 2015</i>",
                self.styles["SmallItalic"],
            )
        )


def main():
    """Main function"""
    print("=" * 70)
    print("COMPLETE RENTAL CONTRACT PDF GENERATOR")
    print("Following Official French Template")
    print("=" * 70)

    # Generate complete version
    generator = CompletRentalContractGenerator(
        json_file="data/sessions/2a5e56bd-ec52-4ff0-908e-64d709f25d8e.json", output_file="data/contrat_location_complet.pdf"
    )
    generator.generate_pdf()

    print("\n✓ Complete version generated successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
