"""
Furnished Lease Contract PDF Generator
Generates a clean PDF from JSON data and a template
"""

import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def load_json_data(json_file):
    """Load and validate JSON data"""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def validate_required_fields(data, path=""):
    """Check if all required fields have values"""
    missing = []

    def check_dict(d, current_path):
        for key, value in d.items():
            new_path = f"{current_path}.{key}" if current_path else key

            if isinstance(value, dict):
                if "requis" in value and "valeur" in value:
                    if value["requis"] and (
                        value["valeur"] is None or value["valeur"] == ""
                    ):
                        missing.append(new_path)
                else:
                    check_dict(value, new_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        check_dict(item, f"{new_path}[{i}]")

    check_dict(data, path)
    return missing


def get_value(field):
    """Extract value from field dictionary"""
    if isinstance(field, dict) and "valeur" in field:
        return field["valeur"]
    return field


def should_display(field):
    """Check if field should be displayed"""
    if isinstance(field, dict) and "valeur" in field:
        val = field["valeur"]
        if val is None or val == "" or val == False:
            return False
    return True


def generate_pdf(json_file, output_file):
    """Generate PDF from JSON data"""

    # Load data
    data = load_json_data(json_file)

    # Validate required fields
    missing = validate_required_fields(data)
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    # Create PDF
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=14,
        textColor="black",
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor="black",
        spaceAfter=12,
        spaceBefore=20,
        fontName="Helvetica-Bold",
    )

    subheading_style = ParagraphStyle(
        "CustomSubHeading",
        parent=styles["Heading3"],
        fontSize=10,
        textColor="black",
        spaceAfter=8,
        spaceBefore=12,
        fontName="Helvetica-Bold",
    )

    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=10,
        textColor="black",
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName="Helvetica",
    )

    # Build content
    story = []

    # Title
    story.append(
        Paragraph("FURNISHED HOUSING LEASE OR CO-LEASE AGREEMENT", title_style)
    )
    story.append(
        Paragraph("(Subject to Title I bis of the law of July 6, 1989)", normal_style)
    )
    story.append(Spacer(1, 0.5 * cm))

    # I. DESIGNATION OF PARTIES
    story.append(Paragraph("I. DESIGNATION OF PARTIES", heading_style))

    bailleur = data["designation_parties"]["bailleur"]
    story.append(Paragraph("<b>THE LESSOR (Owner):</b>", subheading_style))
    story.append(
        Paragraph(
            f"Name: {get_value(bailleur['nom_prenom_ou_denomination'])}", normal_style
        )
    )
    story.append(
        Paragraph(
            f"Address: {get_value(bailleur['adresse_siege_social'])}", normal_style
        )
    )

    if should_display(bailleur["email"]):
        story.append(Paragraph(f"Email: {get_value(bailleur['email'])}", normal_style))

    # Mandataire
    if get_value(bailleur["mandataire"]["existe"]):
        mandataire = bailleur["mandataire"]["details"]
        story.append(Paragraph("<b>Represented by AGENT:</b>", subheading_style))
        story.append(
            Paragraph(
                f"Name: {get_value(mandataire['nom_raison_sociale'])}", normal_style
            )
        )
        story.append(
            Paragraph(f"Address: {get_value(mandataire['adresse'])}", normal_style)
        )
        if should_display(mandataire["numero_carte_pro"]):
            story.append(
                Paragraph(
                    f"Professional card number: {get_value(mandataire['numero_carte_pro'])}",
                    normal_style,
                )
            )

    story.append(Spacer(1, 0.3 * cm))

    # Locataires
    story.append(Paragraph("<b>THE TENANT(S):</b>", subheading_style))
    for locataire in data["designation_parties"]["locataires"]["liste"]:
        if should_display(locataire["nom_prenom"]):
            story.append(
                Paragraph(f"Name: {get_value(locataire['nom_prenom'])}", normal_style)
            )
            if should_display(locataire["email"]):
                story.append(
                    Paragraph(f"Email: {get_value(locataire['email'])}", normal_style)
                )

    # Garants
    garants_list = data["designation_parties"]["garants"]["liste"]
    if any(should_display(g["noms"]) for g in garants_list):
        story.append(Paragraph("<b>THE GUARANTOR(S):</b>", subheading_style))
        for garant in garants_list:
            if should_display(garant["noms"]):
                story.append(
                    Paragraph(f"Name: {get_value(garant['noms'])}", normal_style)
                )
                if should_display(garant["adresse"]):
                    story.append(
                        Paragraph(
                            f"Address: {get_value(garant['adresse'])}", normal_style
                        )
                    )

    # II. PURPOSE OF THE CONTRACT
    story.append(Paragraph("II. PURPOSE OF THE CONTRACT", heading_style))

    logement = data["objet_contrat"]["logement"]
    story.append(Paragraph("<b>A. Property Description</b>", subheading_style))
    story.append(
        Paragraph(f"Location: {get_value(logement['adresse_complete'])}", normal_style)
    )

    if should_display(logement["identifiant_fiscal"]):
        story.append(
            Paragraph(
                f"Tax identifier: {get_value(logement['identifiant_fiscal'])}",
                normal_style,
            )
        )

    story.append(
        Paragraph(
            f"Type of dwelling: {get_value(logement['type_habitat'])}", normal_style
        )
    )
    story.append(
        Paragraph(
            f"Legal status: {get_value(logement['regime_juridique'])}", normal_style
        )
    )
    story.append(
        Paragraph(
            f"Construction period: {get_value(logement['periode_construction'])}",
            normal_style,
        )
    )
    story.append(
        Paragraph(
            f"Living area: {get_value(logement['surface_habitable_m2'])} m²",
            normal_style,
        )
    )
    story.append(
        Paragraph(
            f"Number of main rooms: {get_value(logement['nombre_pieces_principales'])}",
            normal_style,
        )
    )

    story.append(Paragraph(f"<b>Furniture and equipment:</b>", normal_style))
    story.append(
        Paragraph(f"{get_value(logement['equipements_meubles'])}", normal_style)
    )

    chauffage = logement["chauffage"]
    story.append(Paragraph(f"Heating: {get_value(chauffage['mode'])}", normal_style))
    if get_value(chauffage["mode"]) == "Collectif" and should_display(
        chauffage["si_collectif_repartition"]
    ):
        story.append(
            Paragraph(
                f"Distribution: {get_value(chauffage['si_collectif_repartition'])}",
                normal_style,
            )
        )

    eau_chaude = logement["eau_chaude"]
    story.append(Paragraph(f"Hot water: {get_value(eau_chaude['mode'])}", normal_style))
    if get_value(eau_chaude["mode"]) == "Collectif" and should_display(
        eau_chaude["si_collectif_repartition"]
    ):
        story.append(
            Paragraph(
                f"Distribution: {get_value(eau_chaude['si_collectif_repartition'])}",
                normal_style,
            )
        )

    story.append(
        Paragraph(
            f"Energy performance (DPE): Class {get_value(logement['performance_energetique']['classe_dpe'])}",
            normal_style,
        )
    )

    story.append(Paragraph("<b>B. Purpose of Premises</b>", subheading_style))
    story.append(
        Paragraph(
            f"Use: {get_value(data['objet_contrat']['destination_locaux']['usage'])}",
            normal_style,
        )
    )

    # Accessoires
    accessoires = data["objet_contrat"]["accessoires_privatifs"]
    has_accessoires = False
    accessoires_text = []

    if get_value(accessoires["garage_parking"]):
        accessoires_text.append("Garage/Parking")
        has_accessoires = True
    if get_value(accessoires["cave"]):
        accessoires_text.append("Cellar")
        has_accessoires = True
    if should_display(accessoires["autres"]):
        accessoires_text.append(get_value(accessoires["autres"]))
        has_accessoires = True

    if has_accessoires:
        story.append(
            Paragraph("<b>C. Private Ancillary Premises</b>", subheading_style)
        )
        story.append(Paragraph(", ".join(accessoires_text), normal_style))

    # III. EFFECTIVE DATE AND DURATION
    story.append(
        Paragraph("III. EFFECTIVE DATE AND DURATION OF CONTRACT", heading_style)
    )
    duree = data["duree_contrat"]
    story.append(
        Paragraph(
            f"Effective date: {get_value(duree['date_prise_effet'])}", normal_style
        )
    )
    story.append(Paragraph(f"Duration: {get_value(duree['duree_bail'])}", normal_style))

    # IV. FINANCIAL CONDITIONS
    story.append(Paragraph("IV. FINANCIAL CONDITIONS", heading_style))

    conditions = data["conditions_financieres"]
    loyer = conditions["loyer"]

    story.append(Paragraph("<b>A. Rent</b>", subheading_style))
    story.append(
        Paragraph(
            f"Monthly rent (excluding charges): {get_value(loyer['montant_hors_charges'])} €",
            normal_style,
        )
    )

    # Zone tendue
    zone_tendue = loyer["zone_tendue_encadrement"]
    if get_value(zone_tendue["soumis"]):
        if should_display(zone_tendue["loyer_reference_majore"]):
            story.append(
                Paragraph(
                    f"Reference rent (capped zone): {get_value(zone_tendue['loyer_reference_majore'])} €/m²",
                    normal_style,
                )
            )
        if should_display(zone_tendue["complement_loyer"]):
            story.append(
                Paragraph(
                    f"Additional rent: {get_value(zone_tendue['complement_loyer'])} €",
                    normal_style,
                )
            )

    # Previous tenant
    precedent = loyer["precedent_locataire"]
    if get_value(precedent["depart_moins_18_mois"]):
        story.append(
            Paragraph(
                f"Previous rent: {get_value(precedent['montant_dernier_loyer'])} € (last payment: {get_value(precedent['date_dernier_versement'])})",
                normal_style,
            )
        )

    # Rent revision
    revision = conditions["revision_loyer"]
    story.append(
        Paragraph(
            f"Revision date: {get_value(revision['date_revision'])}", normal_style
        )
    )
    story.append(
        Paragraph(
            f"IRL reference quarter: {get_value(revision['trimestre_reference_irl'])}",
            normal_style,
        )
    )

    story.append(Paragraph("<b>B. Recoverable Charges</b>", subheading_style))
    charges = conditions["charges"]
    story.append(
        Paragraph(
            f"Payment method: {get_value(charges['modalite_reglement'])}", normal_style
        )
    )
    story.append(Paragraph(f"Amount: {get_value(charges['montant'])} €", normal_style))

    story.append(Paragraph("<b>C. Payment Terms</b>", subheading_style))
    paiement = conditions["paiement"]
    story.append(
        Paragraph(f"Frequency: {get_value(paiement['periodicite'])}", normal_style)
    )
    story.append(
        Paragraph(f"Type: {get_value(paiement['type_paiement'])}", normal_style)
    )
    story.append(
        Paragraph(
            f"Payment day: Day {get_value(paiement['jour_paiement'])} of each month",
            normal_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>First payment total: {get_value(conditions['premier_versement']['montant_total'])} €</b>",
            normal_style,
        )
    )

    depenses = conditions["depenses_energetiques"]
    story.append(
        Paragraph(
            f"Estimated annual energy expenses: {get_value(depenses['estimation_annuelle'])} (reference year: {get_value(depenses['annee_reference'])})",
            normal_style,
        )
    )

    # V. WORKS
    story.append(Paragraph("V. WORKS", heading_style))
    travaux = data["travaux"]
    if get_value(travaux["effectues_depuis_dernier_bail"]):
        story.append(
            Paragraph(f"Description: {get_value(travaux['description'])}", normal_style)
        )
        if should_display(travaux["montant"]):
            story.append(
                Paragraph(f"Amount: {get_value(travaux['montant'])} €", normal_style)
            )
    else:
        story.append(Paragraph("No works carried out since last lease.", normal_style))

    # VI. GUARANTEES
    story.append(Paragraph("VI. GUARANTEES (Security Deposit)", heading_style))
    story.append(
        Paragraph(
            f"Security deposit amount: {get_value(data['garanties']['montant_depot_garantie'])} €",
            normal_style,
        )
    )
    story.append(
        Paragraph(
            "(Maximum 2 months' rent excluding charges for furnished property)",
            normal_style,
        )
    )

    # VII. TERMINATION CLAUSE
    story.append(Paragraph("VII. TERMINATION CLAUSE", heading_style))
    story.append(
        Paragraph(
            "The contract will be automatically terminated in case of: failure to pay rent or charges, "
            "failure to pay security deposit, lack of tenant insurance, or disturbance of neighbors "
            "confirmed by court decision.",
            normal_style,
        )
    )

    # VIII. RENTAL FEES
    story.append(Paragraph("VIII. RENTAL FEES (Agency Fees)", heading_style))
    honoraires = data["honoraires_location"]
    if get_value(honoraires["agence_impliquee"]):
        if should_display(honoraires["part_locataire"]):
            story.append(
                Paragraph(
                    f"Tenant fees: {get_value(honoraires['part_locataire'])} €",
                    normal_style,
                )
            )
        if should_display(honoraires["part_bailleur"]):
            story.append(
                Paragraph(
                    f"Lessor fees: {get_value(honoraires['part_bailleur'])} €",
                    normal_style,
                )
            )
    else:
        story.append(Paragraph("No agency involved (private rental).", normal_style))

    # IX. ANNEXES
    story.append(Paragraph("IX. ANNEXES", heading_style))
    story.append(
        Paragraph(
            "The following documents are attached to this contract:", normal_style
        )
    )
    story.append(
        Paragraph(
            "• Technical diagnostic file (DPE, Lead, Asbestos, Electricity, Risks)",
            normal_style,
        )
    )
    story.append(
        Paragraph("• Information notice on rights and obligations", normal_style)
    )
    story.append(Paragraph("• Entry inventory and furniture inventory", normal_style))
    story.append(
        Paragraph("• Extract from co-ownership rules (if applicable)", normal_style)
    )

    # Signatures
    story.append(Spacer(1, 1 * cm))
    signature = data["signature"]
    story.append(
        Paragraph(
            f"Done in {get_value(signature['ville'])}, on {get_value(signature['date'])}",
            normal_style,
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    sig_style = ParagraphStyle("Signature", parent=normal_style, alignment=TA_LEFT)
    story.append(Paragraph("<b>THE LESSOR</b>", sig_style))
    story.append(Paragraph("(Signature preceded by 'Read and approved')", sig_style))
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph("<b>THE TENANT(S)</b>", sig_style))
    story.append(Paragraph("(Signature preceded by 'Read and approved')", sig_style))
    story.append(Spacer(1, 1 * cm))

    if any(should_display(g["noms"]) for g in garants_list):
        story.append(Paragraph("<b>THE GUARANTOR(S)</b>", sig_style))
        story.append(
            Paragraph("(Signature preceded by 'Read and approved')", sig_style)
        )

    # Build PDF
    doc.build(story)
    print(f"PDF generated successfully: {output_file}")


if __name__ == "__main__":
    try:
        generate_pdf("lease_data.json", "lease_contract.pdf")
    except ValueError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print("Error: lease_data.json file not found")
    except Exception as e:
        print(f"Unexpected error: {e}")
