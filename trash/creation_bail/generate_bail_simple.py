#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Rental Contract Generator
Generates a clean PDF rental contract from JSON data
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
)
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import HRFlowable


class RentalContractGenerator:
    """
    Class to generate rental contract PDF from JSON data
    """

    def __init__(self, json_file, template_file, output_file="contrat_location.pdf"):
        """
        Initialize the generator with JSON data and template

        Args:
            json_file: Path to JSON file with contract data
            template_file: Path to template file (for reference)
            output_file: Path to output PDF file
        """
        self.json_file = json_file
        self.template_file = template_file
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
            print(f"✗ Error: Invalid JSON in {self.json_file}: {e}")
            sys.exit(1)

    def _validate_required_fields(self):
        """
        Check if all required fields have values

        Returns:
            tuple: (is_valid, missing_fields)
        """
        missing_fields = []

        def check_fields(obj, path=""):
            """Recursively check fields"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key

                    if isinstance(value, dict):
                        if "requis" in value and "valeur" in value:
                            # This is a field definition
                            if value.get("requis") == True:
                                if value.get("valeur") in [None, "", []]:
                                    missing_fields.append(new_path)
                        else:
                            # Nested object
                            check_fields(value, new_path)
                    elif key == "liste" and isinstance(value, list):
                        # Check list items
                        for i, item in enumerate(value):
                            check_fields(item, f"{new_path}[{i}]")

        check_fields(self.data)

        if missing_fields:
            return False, missing_fields
        return True, []

    def _setup_styles(self):
        """Setup custom styles for PDF generation"""
        self.styles = getSampleStyleSheet()

        # Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=14,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        # Subtitle style
        self.styles.add(
            ParagraphStyle(
                name="Subtitle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#666666"),
                alignment=TA_CENTER,
                spaceAfter=20,
                fontName="Helvetica-Oblique",
            )
        )

        # Section title style
        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading1"],
                fontSize=12,
                textColor=colors.HexColor("#000080"),
                spaceBefore=15,
                spaceAfter=10,
                fontName="Helvetica-Bold",
            )
        )

        # Field label style
        self.styles.add(
            ParagraphStyle(
                name="FieldLabel",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#333333"),
                fontName="Helvetica-Bold",
            )
        )

        # Field value style
        self.styles.add(
            ParagraphStyle(
                name="FieldValue",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#000000"),
                leftIndent=20,
            )
        )

        # Normal text justified
        self.styles.add(
            ParagraphStyle(
                name="Justified",
                parent=self.styles["Normal"],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceBefore=6,
                spaceAfter=6,
            )
        )

        # Signature style
        self.styles.add(
            ParagraphStyle(
                name="Signature",
                parent=self.styles["Normal"],
                fontSize=10,
                alignment=TA_LEFT,
                spaceBefore=30,
            )
        )

    def _get_value(self, path):
        """
        Get value from nested dictionary using dot notation

        Args:
            path: Path to value (e.g., 'bailleur.nom_prenom_ou_denomination.valeur')

        Returns:
            Value or empty string if not found
        """
        keys = path.split(".")
        value = self.data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return ""

        if isinstance(value, dict) and "valeur" in value:
            return value["valeur"] or ""

        return value or ""

    def _format_date(self, date_str):
        """Format date string to French format"""
        if not date_str:
            return ""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except:
            return date_str

    def _add_section_title(self, title):
        """Add a section title to the document"""
        self.story.append(Paragraph(title, self.styles["SectionTitle"]))
        self.story.append(
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"))
        )
        self.story.append(Spacer(1, 5 * mm))

    def _add_field(self, label, value, style="FieldValue"):
        """Add a field with label and value"""
        if value:  # Only add if value exists
            label_para = Paragraph(f"<b>{label}:</b>", self.styles["FieldLabel"])
            value_para = Paragraph(str(value), self.styles[style])
            self.story.append(label_para)
            self.story.append(value_para)
            self.story.append(Spacer(1, 2 * mm))

    def _add_inline_field(self, label, value):
        """Add a field with label and value on same line"""
        if value:
            text = f"<b>{label}:</b> {value}"
            self.story.append(Paragraph(text, self.styles["Normal"]))
            self.story.append(Spacer(1, 2 * mm))

    def generate_pdf(self):
        """Generate the PDF contract"""
        # Validate required fields
        is_valid, missing = self._validate_required_fields()

        if not is_valid:
            print("✗ Error: Missing required fields:")
            for field in missing:
                print(f"  - {field}")
            print("\nPlease fill in all required fields before generating the PDF.")
            sys.exit(1)

        # Create PDF document
        doc = SimpleDocTemplate(
            self.output_file,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        # Build document content
        self._build_content()

        # Generate PDF
        try:
            doc.build(self.story)
            print(f"✓ PDF generated successfully: {self.output_file}")
        except Exception as e:
            print(f"✗ Error generating PDF: {e}")
            sys.exit(1)

    def _build_content(self):
        """Build the document content"""
        # Title
        self.story.append(
            Paragraph(
                "CONTRAT TYPE DE LOCATION DE LOGEMENT MEUBLÉ",
                self.styles["CustomTitle"],
            )
        )

        self.story.append(
            Paragraph(
                "(Soumis au titre Ier bis de la loi du 6 juillet 1989 tendant à améliorer les rapports locatifs)",
                self.styles["Subtitle"],
            )
        )

        self.story.append(Spacer(1, 10 * mm))

        # Section I: DÉSIGNATION DES PARTIES
        self._add_section_title("I. DÉSIGNATION DES PARTIES")

        # Bailleur
        self.story.append(
            Paragraph("<b>LE BAILLEUR (Propriétaire):</b>", self.styles["FieldLabel"])
        )
        self._add_inline_field(
            "Nom et prénom",
            self._get_value("designation_parties.bailleur.nom_prenom_ou_denomination"),
        )
        self._add_inline_field(
            "Domicile",
            self._get_value("designation_parties.bailleur.adresse_siege_social"),
        )

        email_bailleur = self._get_value("designation_parties.bailleur.email")
        if email_bailleur:
            self._add_inline_field("Email", email_bailleur)

        type_personne = self._get_value("designation_parties.bailleur.type_personne")
        if type_personne:
            self._add_inline_field("Qualité du bailleur", type_personne)

        # Mandataire (if exists)
        if self._get_value("designation_parties.bailleur.mandataire.existe"):
            self.story.append(Spacer(1, 3 * mm))
            self.story.append(
                Paragraph(
                    "<b>Représenté par le MANDATAIRE:</b>", self.styles["FieldLabel"]
                )
            )
            self._add_inline_field(
                "Nom ou raison sociale",
                self._get_value(
                    "designation_parties.bailleur.mandataire.details.nom_raison_sociale"
                ),
            )
            self._add_inline_field(
                "Adresse",
                self._get_value(
                    "designation_parties.bailleur.mandataire.details.adresse"
                ),
            )
            self._add_inline_field(
                "N° carte professionnelle",
                self._get_value(
                    "designation_parties.bailleur.mandataire.details.numero_carte_pro"
                ),
            )

        self.story.append(Spacer(1, 5 * mm))

        # Locataires
        self.story.append(
            Paragraph("<b>LE(S) LOCATAIRE(S):</b>", self.styles["FieldLabel"])
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
                self._add_inline_field(f"Locataire {i+1}", nom)
                if email:
                    self._add_inline_field("Email", email)

        # Garants
        garants = (
            self.data.get("designation_parties", {}).get("garants", {}).get("liste", [])
        )
        if garants and garants[0].get("noms", {}).get("valeur"):
            self.story.append(Spacer(1, 5 * mm))
            self.story.append(
                Paragraph(
                    "<b>LE(S) GARANT(S) (Caution):</b>", self.styles["FieldLabel"]
                )
            )
            for garant in garants:
                noms = garant.get("noms", {}).get("valeur", "")
                adresse = garant.get("adresse", {}).get("valeur", "")
                if noms:
                    self._add_inline_field("Noms", noms)
                    if adresse:
                        self._add_inline_field("Adresse", adresse)

        self.story.append(Spacer(1, 10 * mm))

        # Section II: OBJET DU CONTRAT
        self._add_section_title("II. OBJET DU CONTRAT")

        self.story.append(
            Paragraph("<b>A. Consistance du logement</b>", self.styles["FieldLabel"])
        )
        self.story.append(Spacer(1, 3 * mm))

        self._add_inline_field(
            "Localisation du logement",
            self._get_value("objet_contrat.logement.adresse_complete"),
        )

        id_fiscal = self._get_value("objet_contrat.logement.identifiant_fiscal")
        if id_fiscal:
            self._add_inline_field("Identifiant fiscal", id_fiscal)

        self._add_inline_field(
            "Type d'habitat", self._get_value("objet_contrat.logement.type_habitat")
        )
        self._add_inline_field(
            "Régime juridique",
            self._get_value("objet_contrat.logement.regime_juridique"),
        )
        self._add_inline_field(
            "Période de construction",
            self._get_value("objet_contrat.logement.periode_construction"),
        )
        self._add_inline_field(
            "Surface habitable",
            f"{self._get_value('objet_contrat.logement.surface_habitable_m2')} m²",
        )
        self._add_inline_field(
            "Nombre de pièces principales",
            self._get_value("objet_contrat.logement.nombre_pieces_principales"),
        )

        # Other parts
        autres_parties = (
            self.data.get("objet_contrat", {})
            .get("logement", {})
            .get("autres_parties", {})
        )
        parts_list = []
        if autres_parties.get("terrasse", {}).get("valeur"):
            parts_list.append("Terrasse")
        if autres_parties.get("balcon", {}).get("valeur"):
            parts_list.append("Balcon")
        if autres_parties.get("cave", {}).get("valeur"):
            parts_list.append("Cave")
        if autres_parties.get("parking", {}).get("valeur"):
            parts_list.append("Parking")

        if parts_list:
            self._add_inline_field("Autres parties du logement", ", ".join(parts_list))

        # Equipment
        equipements = self._get_value("objet_contrat.logement.equipements_meubles")
        if equipements:
            self.story.append(Spacer(1, 3 * mm))
            self.story.append(
                Paragraph(
                    "<b>Éléments d'équipements du logement:</b>",
                    self.styles["FieldLabel"],
                )
            )
            self.story.append(Paragraph(equipements, self.styles["FieldValue"]))

        # Heating and hot water
        self.story.append(Spacer(1, 3 * mm))
        chauffage_mode = self._get_value("objet_contrat.logement.chauffage.mode")
        self._add_inline_field("Modalité de production de chauffage", chauffage_mode)

        if chauffage_mode == "Collectif":
            repartition = self._get_value(
                "objet_contrat.logement.chauffage.si_collectif_repartition"
            )
            if repartition:
                self._add_inline_field("Répartition", repartition)

        eau_chaude_mode = self._get_value("objet_contrat.logement.eau_chaude.mode")
        self._add_inline_field(
            "Modalité de production d'eau chaude sanitaire", eau_chaude_mode
        )

        if eau_chaude_mode == "Collectif":
            repartition = self._get_value(
                "objet_contrat.logement.eau_chaude.si_collectif_repartition"
            )
            if repartition:
                self._add_inline_field("Répartition", repartition)

        # Energy performance
        self._add_inline_field(
            "Performance énergétique (DPE)",
            f"Classe {self._get_value('objet_contrat.logement.performance_energetique.classe_dpe')}",
        )

        self.story.append(Spacer(1, 5 * mm))

        # Destination
        self.story.append(
            Paragraph("<b>B. Destination des locaux</b>", self.styles["FieldLabel"])
        )
        self._add_inline_field(
            "Usage", self._get_value("objet_contrat.destination_locaux.usage")
        )

        # Private accessories
        accessoires = self.data.get("objet_contrat", {}).get(
            "accessoires_privatifs", {}
        )
        if accessoires.get("cave", {}).get("valeur"):
            self.story.append(Spacer(1, 5 * mm))
            self.story.append(
                Paragraph(
                    "<b>C. Désignation des locaux accessoires privatifs</b>",
                    self.styles["FieldLabel"],
                )
            )
            cave_num = accessoires.get("cave_numero", {}).get("valeur", "")
            if cave_num:
                self._add_inline_field("Cave", f"N° {cave_num}")
            else:
                self._add_inline_field("Cave", "Oui")

        # Common areas
        parties_communes = self.data.get("objet_contrat", {}).get(
            "parties_communes", {}
        )
        common_list = []
        if parties_communes.get("chauffage_collectif", {}).get("valeur"):
            common_list.append("Chauffage collectif")
        if parties_communes.get("local_poubelle", {}).get("valeur"):
            common_list.append("Local poubelle")
        if parties_communes.get("garage_velo", {}).get("valeur"):
            common_list.append("Garage à vélo")
        if parties_communes.get("ascenseur", {}).get("valeur"):
            common_list.append("Ascenseur")
        if parties_communes.get("interphone", {}).get("valeur"):
            common_list.append("Interphone/Digicode")
        if parties_communes.get("fibre", {}).get("valeur"):
            common_list.append("Fibre optique")

        if common_list:
            self.story.append(Spacer(1, 5 * mm))
            self.story.append(
                Paragraph(
                    "<b>D. Parties et équipements communs</b>",
                    self.styles["FieldLabel"],
                )
            )
            self._add_inline_field("Équipements disponibles", ", ".join(common_list))

        self.story.append(Spacer(1, 10 * mm))

        # Section III: DATE DE PRISE D'EFFET ET DURÉE
        self._add_section_title("III. DATE DE PRISE D'EFFET ET DURÉE DU CONTRAT")

        date_effet = self._get_value("duree_contrat.date_prise_effet")
        self._add_inline_field("Date de prise d'effet", self._format_date(date_effet))
        self._add_inline_field(
            "Durée du contrat", self._get_value("duree_contrat.duree_bail")
        )

        self.story.append(
            Paragraph(
                "<i>Note: Pour un meublé résidence principale, la durée est de 1 an reconductible tacitement.</i>",
                self.styles["Normal"],
            )
        )

        self.story.append(Spacer(1, 10 * mm))

        # Section IV: CONDITIONS FINANCIÈRES
        self._add_section_title("IV. CONDITIONS FINANCIÈRES")

        # Loyer
        self.story.append(Paragraph("<b>A. Loyer</b>", self.styles["FieldLabel"]))
        loyer = self._get_value("conditions_financieres.loyer.montant_hors_charges")
        self._add_inline_field("Montant du loyer mensuel hors charges", f"{loyer} €")

        # Zone tendue
        if self._get_value(
            "conditions_financieres.loyer.zone_tendue_encadrement.soumis"
        ):
            self.story.append(Spacer(1, 3 * mm))
            self.story.append(
                Paragraph(
                    "<b>Zone tendue (Encadrement des loyers):</b>",
                    self.styles["FieldLabel"],
                )
            )
            loyer_ref = self._get_value(
                "conditions_financieres.loyer.zone_tendue_encadrement.loyer_reference"
            )
            loyer_maj = self._get_value(
                "conditions_financieres.loyer.zone_tendue_encadrement.loyer_reference_majore"
            )
            if loyer_ref:
                self._add_inline_field("Loyer de référence", f"{loyer_ref} €/m²")
            if loyer_maj:
                self._add_inline_field("Loyer de référence majoré", f"{loyer_maj} €/m²")

            complement = self._get_value(
                "conditions_financieres.loyer.zone_tendue_encadrement.complement_loyer"
            )
            if complement:
                self._add_inline_field("Complément de loyer", f"{complement} €")

        # Previous tenant
        if self._get_value(
            "conditions_financieres.loyer.precedent_locataire.depart_moins_18_mois"
        ):
            self.story.append(Spacer(1, 3 * mm))
            self.story.append(
                Paragraph(
                    "<b>Information loyer précédent locataire:</b>",
                    self.styles["FieldLabel"],
                )
            )
            montant_prec = self._get_value(
                "conditions_financieres.loyer.precedent_locataire.montant_dernier_loyer"
            )
            date_prec = self._get_value(
                "conditions_financieres.loyer.precedent_locataire.date_dernier_versement"
            )
            if montant_prec:
                self._add_inline_field("Montant", f"{montant_prec} €")
            if date_prec:
                self._add_inline_field(
                    "Date dernier versement", self._format_date(date_prec)
                )

        # Revision
        self.story.append(Spacer(1, 3 * mm))
        self.story.append(
            Paragraph("<b>Modalités de révision:</b>", self.styles["FieldLabel"])
        )
        self._add_inline_field(
            "Date de révision",
            self._get_value("conditions_financieres.revision_loyer.date_revision"),
        )
        self._add_inline_field(
            "Trimestre de référence IRL",
            self._get_value(
                "conditions_financieres.revision_loyer.trimestre_reference_irl"
            ),
        )

        # Charges
        self.story.append(Spacer(1, 5 * mm))
        self.story.append(
            Paragraph("<b>B. Charges récupérables</b>", self.styles["FieldLabel"])
        )
        self._add_inline_field(
            "Modalité de règlement",
            self._get_value("conditions_financieres.charges.modalite_reglement"),
        )
        self._add_inline_field(
            "Montant", f"{self._get_value('conditions_financieres.charges.montant')} €"
        )

        # Payment
        self.story.append(Spacer(1, 5 * mm))
        self.story.append(
            Paragraph("<b>C. Modalités de paiement</b>", self.styles["FieldLabel"])
        )
        self._add_inline_field("Périodicité", "Mensuelle")
        self._add_inline_field(
            "Paiement", self._get_value("conditions_financieres.paiement.type_paiement")
        )
        self._add_inline_field(
            "Date de paiement",
            f"Le {self._get_value('conditions_financieres.paiement.jour_paiement')} de chaque mois",
        )

        # First payment
        self.story.append(Spacer(1, 3 * mm))
        self.story.append(
            Paragraph("<b>Premier versement:</b>", self.styles["FieldLabel"])
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

        table_data = [
            ["", "Montant"],
            ["Loyer", f"{premier_loyer} €"],
            ["Charges", f"{premier_charges} €"],
            ["TOTAL", f"{premier_total} €"],
        ]

        table = Table(table_data, colWidths=[4 * cm, 3 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -2), colors.beige),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        self.story.append(table)

        # Energy expenses
        self.story.append(Spacer(1, 5 * mm))
        self.story.append(
            Paragraph(
                "<b>D. Dépenses énergétiques (Estimation)</b>",
                self.styles["FieldLabel"],
            )
        )
        depenses_energie = self._get_value(
            "conditions_financieres.depenses_energetiques.estimation_annuelle"
        )
        annee_ref = self._get_value(
            "conditions_financieres.depenses_energetiques.annee_reference"
        )
        self._add_inline_field(
            "Montant estimé annuel", f"{depenses_energie} (Année {annee_ref})"
        )

        self.story.append(Spacer(1, 10 * mm))

        # Section V: TRAVAUX
        if self._get_value("travaux.effectues_depuis_dernier_bail"):
            self._add_section_title("V. TRAVAUX")
            description = self._get_value("travaux.description")
            montant = self._get_value("travaux.montant")
            if description:
                self._add_inline_field("Nature des travaux", description)
            if montant:
                self._add_inline_field("Montant", f"{montant} €")
            self.story.append(Spacer(1, 10 * mm))

        # Section VI: GARANTIES
        self._add_section_title("VI. GARANTIES")
        depot = self._get_value("garanties.montant_depot_garantie")
        self._add_inline_field("Montant du dépôt de garantie", f"{depot} €")
        self.story.append(
            Paragraph(
                "<i>Rappel: Pour un meublé, maximum 2 mois de loyer hors charges.</i>",
                self.styles["Normal"],
            )
        )

        # Colocation clause
        if self._get_value("colocation.est_colocation"):
            self.story.append(Spacer(1, 10 * mm))
            self._add_section_title("VII. CLAUSE DE SOLIDARITÉ (Colocation)")
            self.story.append(
                Paragraph(
                    "Il est expressément stipulé que les copreneurs seront tenus solidairement et indivisiblement "
                    "de l'exécution des obligations du présent contrat. La solidarité d'un colocataire sortant "
                    "s'éteint lorsqu'un nouveau colocataire le remplace au bail, ou à défaut, à l'expiration "
                    "d'un délai de 6 mois après son congé.",
                    self.styles["Justified"],
                )
            )

        # Resolution clause
        self.story.append(Spacer(1, 10 * mm))
        self._add_section_title("VIII. CLAUSE RÉSOLUTOIRE")
        self.story.append(
            Paragraph(
                "Le contrat sera résilié de plein droit en cas de:",
                self.styles["Normal"],
            )
        )
        clauses = [
            "• Défaut de paiement du loyer ou des charges",
            "• Défaut de versement du dépôt de garantie",
            "• Défaut d'assurance locative",
            "• Trouble de voisinage constaté par décision de justice",
        ]
        for clause in clauses:
            self.story.append(Paragraph(clause, self.styles["Normal"]))

        # Agency fees
        if self._get_value("honoraires_location.agence_impliquee"):
            self.story.append(Spacer(1, 10 * mm))
            self._add_section_title("IX. HONORAIRES DE LOCATION")
            part_locataire = self._get_value("honoraires_location.part_locataire")
            part_bailleur = self._get_value("honoraires_location.part_bailleur")
            if part_locataire:
                self._add_inline_field(
                    "Honoraires charge locataire", f"{part_locataire} €"
                )
            if part_bailleur:
                self._add_inline_field(
                    "Honoraires charge bailleur", f"{part_bailleur} €"
                )

        # Annexes
        self.story.append(Spacer(1, 10 * mm))
        self._add_section_title("X. ANNEXES")
        self.story.append(
            Paragraph(
                "Sont annexées au présent contrat les pièces suivantes:",
                self.styles["Normal"],
            )
        )
        annexes = [
            "• Le dossier de diagnostic technique (DPE, Plomb, Amiante, Électricité, Risques)",
            "• La notice d'information relative aux droits et obligations",
            "• L'état des lieux d'entrée et l'inventaire du mobilier",
            "• Un extrait du règlement de copropriété (le cas échéant)",
        ]
        for annexe in annexes:
            self.story.append(Paragraph(annexe, self.styles["Normal"]))

        # New page for signatures
        self.story.append(PageBreak())

        # Signatures
        ville = self._get_value("signature.ville")
        date_signature = self._format_date(self._get_value("signature.date"))

        self.story.append(
            Paragraph(f"Fait à {ville}, le {date_signature}", self.styles["Normal"])
        )
        self.story.append(
            Paragraph("En 2 exemplaires originaux", self.styles["Normal"])
        )

        self.story.append(Spacer(1, 20 * mm))

        # Create signature table
        signature_data = [
            ["LE BAILLEUR", "LE(S) LOCATAIRE(S)"],
            [
                '(Signature précédée de la mention\n"Lu et approuvé")',
                '(Signature précédée de la mention\n"Lu et approuvé")',
            ],
            ["\n\n\n\n\n", "\n\n\n\n\n"],
        ]

        sig_table = Table(signature_data, colWidths=[8 * cm, 8 * cm])
        sig_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ]
            )
        )
        self.story.append(sig_table)

        # Garants signatures if exists
        garants = (
            self.data.get("designation_parties", {}).get("garants", {}).get("liste", [])
        )
        if garants and garants[0].get("noms", {}).get("valeur"):
            self.story.append(Spacer(1, 20 * mm))
            self.story.append(
                Paragraph("<b>LE(S) GARANT(S)</b>", self.styles["FieldLabel"])
            )
            self.story.append(
                Paragraph(
                    '(Signature précédée de la mention "Lu et approuvé")',
                    self.styles["Normal"],
                )
            )
            self.story.append(Spacer(1, 30 * mm))


def main():
    """Main function to run the generator"""
    print("=" * 60)
    print("RENTAL CONTRACT PDF GENERATOR")
    print("=" * 60)

    # File paths
    json_file = "contrat_data.json"
    template_file = "template_bail.txt"
    output_file = "contrat_location_meuble.pdf"

    # Create generator instance
    generator = RentalContractGenerator(json_file, template_file, output_file)

    # Generate PDF
    generator.generate_pdf()

    print("\n✓ Process completed successfully!")
    print(f"  Output file: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
