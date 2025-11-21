

RAPPEL NOUVEAU LOCATAIRE : n'oubliez pas de mettre vos compteurs d'énergie à votre nom dès la signature du bail.
Contactez le 09 87 67 94 26 (non surtaxé, lundi-vendredi 8H-21H ; samedi 8H30-18H30, dimanche 9H-17H, service Selectra) pour mettre vos compteurs d'électricité et de gaz naturel à votre nom et éviter toute coupure.

# CONTRAT DE LOCATION/COLLOCATION
LOGEMENT MEUBLÉ
(Loi n°89-462 du 6 juillet 1989)

## I. DÉSIGNATION DES PARTIES
Le présent contrat est conclu entre les soussignés :


- Nom et prénom, ou dénomination du bailleur : **{{ designation_parties.bailleur.nom_prenom_ou_denomination.valeur }}**
- Domicile ou siège social du bailleur : **{{ designation_parties.bailleur.adresse_siege_social.valeur }}**
- Qualité du bailleur : **{{ designation_parties.bailleur.type_personne.valeur }}**
{% if designation_parties.bailleur.type_personne.valeur == 'Personne morale' and designation_parties.bailleur.societe_civile_familiale.valeur %}
La personne morale est une société civile constituée exclusivement entre parents et alliés jusqu'au quatrième degré inclus.
{% endif %}
- Adresse email du bailleur (facultatif) : **{{ designation_parties.bailleur.email.valeur }}**
désigné (s) ci-après le bailleur ;

Le cas échéant, représenté par le mandataire :


{% if designation_parties.bailleur.mandataire.existe.valeur %}
- Nom ou raison sociale du mandataire : **{{ designation_parties.bailleur.mandataire.details.nom_raison_sociale.valeur }}**
- Adresse du mandataire : **{{ designation_parties.bailleur.mandataire.details.adresse.valeur }}**
- Activité exercée par le mandataire : _________________________
- Le cas échéant, numéro et lieu de délivrance de la carte professionnelle : **{{ designation_parties.bailleur.mandataire.details.numero_carte_pro.valeur }}**
{% else %}
(Sans objet)
{% endif %}

- Nom et adresse du garant :
{% for garant in designation_parties.garants.liste %}
**{{ garant.noms.valeur }} - {{ garant.adresse.valeur }}**
{% else %}
(Aucun garant)
{% endfor %}

- Nom et prénom du locataire :
{% for locataire in designation_parties.locataires.liste %}
**{{ locataire.nom_prenom.valeur }}**
- Adresse email du locataire (facultatif) : **{{ locataire.email.valeur }}**
{% endfor %}
désigné (s) ci-après le locataire

Il a été convenu ce qui suit :

## II. OBJET DU CONTRAT
Le présent contrat a pour objet la location d'un logement ainsi déterminé :
A. Consistance du logement :


- Adresse du logement : **{{ objet_contrat.logement.adresse_complete.valeur }}**
- Bâtiment / escalier / étage / porte : _________________________
- Identifiant fiscal du logement : **{{ objet_contrat.logement.identifiant_fiscal.valeur }}**
- Type d'habitat : **{{ objet_contrat.logement.type_habitat.valeur }}**
- Régime juridique : **{{ objet_contrat.logement.regime_juridique.valeur }}**
- Période de construction : **{{ objet_contrat.logement.periode_construction.valeur }}**
- Surface habitable (en m²) : **{{ objet_contrat.logement.surface_habitable_m2.valeur }}**
- Nombre de pièces principales : **{{ objet_contrat.logement.nombre_pieces_principales.valeur }}**



- Le cas échéant, autres parties du logement :
{% if objet_contrat.logement.autres_parties.grenier is defined and objet_contrat.logement.autres_parties.grenier.valeur %}- Grenier{% endif %}
{% if objet_contrat.logement.autres_parties.comble is defined and objet_contrat.logement.autres_parties.comble.valeur %}- Comble aménagé ou non{% endif %}
{% if objet_contrat.logement.autres_parties.terrasse is defined and objet_contrat.logement.autres_parties.terrasse.valeur %}- Terrasse{% endif %}
{% if objet_contrat.logement.autres_parties.balcon is defined and objet_contrat.logement.autres_parties.balcon.valeur %}- Balcon{% endif %}
{% if objet_contrat.logement.autres_parties.loggia is defined and objet_contrat.logement.autres_parties.loggia.valeur %}- Loggia{% endif %}
{% if objet_contrat.logement.autres_parties.jardin is defined and objet_contrat.logement.autres_parties.jardin.valeur %}- Jardin{% endif %}
{% if objet_contrat.logement.autres_parties.autre is defined and objet_contrat.logement.autres_parties.autre.valeur %}- Autre : _________________________{% endif %}

- Le cas échéant, éléments d'équipements du logement :
**{{ objet_contrat.logement.equipements_meubles.valeur }}**

- Modalité de production de chauffage : **{{ objet_contrat.logement.chauffage.mode.valeur }}**

Si collectif, préciser les modalités de répartition de la consommation du locataire :
**{{ objet_contrat.logement.chauffage.si_collectif_repartition.valeur }}**

- Modalité de production d'eau chaude sanitaire : **{{ objet_contrat.logement.eau_chaude.mode.valeur }}**

Si collectif, préciser les modalités de répartition de la consommation du locataire :
**{{ objet_contrat.logement.eau_chaude.si_collectif_repartition.valeur }}**

- Niveau de performance énergétique du logement : **{{ objet_contrat.logement.performance_energetique.classe_dpe.valeur }}**
« Rappel : un logement décent doit respecter les critères minimaux de performance suivants :
A) En France métropolitaine :
A.1) A compter du 1er janvier 2025, le niveau de performance minimal du logement correspond à la classe F du DPE ;
A.2) A compter du 1er janvier 2028, le niveau de performance minimal du logement correspond à la classe E du DPE ;
A.3) A compter du 1er janvier 2034, le niveau de performance minimal du logement correspond à la classe D du DPE.
B) En Guadeloupe, en Martinique, en Guyane, à La Réunion et à Mayotte :
B.1) A compter du 1er janvier 2028, le niveau de performance minimal du logement correspond à la classe F du DPE ;
B.2) A compter du 1er janvier 2031, le niveau de performance minimal du logement correspond à la classe E du DPE.

La consommation d'énergie finale et le niveau de performance du logement sont déterminés selon la méthode du diagnostic de performance énergétique mentionné à l'article L. 126-26 du code de la construction et de l'habitation. »

B. Destination des locaux : **{{ objet_contrat.destination_locaux.usage.valeur }}**

C. Le cas échéant, désignation des locaux et équipements accessoires de l'immeuble à usage privatif du locataire :
{% if objet_contrat.logement.autres_parties.cave is defined and objet_contrat.logement.autres_parties.cave.valeur %}- Cave / n°: _________________________{% endif %}
{% if objet_contrat.logement.autres_parties.parking is defined and objet_contrat.logement.autres_parties.parking.valeur %}- Parking / n°: _________________________{% endif %}
{% if objet_contrat.logement.autres_parties.garage is defined and objet_contrat.logement.autres_parties.garage.valeur %}- Garage / n°: _________________________{% endif %}
[ ] Autre : _________________________

D. Le cas échéant, énumération des locaux, parties, équipements et accessoires de l'immeuble à usage commun :
[ ] Garage à vélo
[ ] Ascenseur
[ ] Espaces verts
[ ] Aires et équipements de jeux
[ ] Laverie
[ ] Local poubelle
[ ] Gardiennage
[ ] Autres prestations et services collectifs : _________________________

E. Équipement d'accès aux technologies de l'information et de la communication (modalités de réception de la télévision dans l'immeuble, modalités de raccordement Internet etc) :
_________________________



## III. DATE DE PRISE D'EFFET ET DURÉE DU CONTRAT

La durée du contrat et sa date de prise d'effet sont ainsi définies :

A. Prise d'effet du contrat :


- Date de prise d'effet du contrat : **{{ duree_contrat.date_prise_effet.valeur }}**

B. Durée du contrat :
**{{ duree_contrat.duree_bail.valeur }}**
(minimum 1 an, ou 9 mois si la location est consentie à un étudiant).

A l'exception des locations consenties à un étudiant pour une durée de 9 mois, les contrats de location de logements meublés sont reconduits tacitement à leur terme pour une durée d'un an et dans les mêmes conditions. Le locataire peut mettre fin au bail à tout moment, après avoir donné congé. Le bailleur peut, quant à lui, mettre fin au bail à son échéance et après avoir donné congé, soit pour reprendre le logement en vue de l'occuper lui-même ou une personne de sa famille, soit pour le vendre, soit pour un motif sérieux et légitime. Les contrats de locations meublées consenties à un étudiant pour une durée de 9 mois ne sont pas reconduits tacitement à leur terme et le locataire peut mettre fin au bail à tout moment, après avoir donné congé. Le bailleur peut, quant à lui, mettre fin au bail à son échéance et après avoir donné congé.

## IV. CONDITIONS FINANCIÈRES

Les parties conviennent des conditions financières suivantes :

A. Loyer :

1. Fixation du loyer initial :
a) Montant du loyer mensuel **{{ conditions_financieres.loyer.montant_hors_charges.valeur }}** €

Lorsqu'un complément de loyer est appliqué, le loyer mensuel s'entend comme la somme du loyer de base et de ce complément.

b) Le cas échant, modalités particulières de fixation initiale du loyer applicables dans certaines zones tendues :
Zones d'urbanisation continue de plus de 50 000 habitants où il existe un déséquilibre marqué entre l'offre et la demande de logements, entraînant des difficultés sérieuses d'accès au logement sur l'ensemble du parc résidentiel telles que définies par décret.

- le loyer du logement objet du présent contrat est soumis au décret fixant annuellement le montant maximum d'évolution des loyers à la relocation : **{% if conditions_financieres.loyer.zone_tendue_encadrement.soumis.valeur %}Oui{% else %}Non{% endif %}**

- le loyer du logement objet du présent contrat est soumis au loyer de référence majoré fixé par arrêté préfectoral : **{% if conditions_financieres.loyer.zone_tendue_encadrement.loyer_reference.valeur %}Oui{% else %}Non{% endif %}**
{% if conditions_financieres.loyer.zone_tendue_encadrement.loyer_reference.valeur %}
- Montant du loyer de référence **{{ conditions_financieres.loyer.zone_tendue_encadrement.loyer_reference.valeur }}** €/m²
- Montant du loyer de référence majoré **{{ conditions_financieres.loyer.zone_tendue_encadrement.loyer_reference_majore.valeur }}** €/m²
{% endif %}

- un complément de loyer est prévu : **{% if conditions_financieres.loyer.zone_tendue_encadrement.complement_loyer.valeur %}Oui{% else %}Non{% endif %}**
{% if conditions_financieres.loyer.zone_tendue_encadrement.complement_loyer.valeur %}
- Montant du loyer de base (nécessairement égal au loyer de référence majoré) _________________________ €
- Montant du complément de loyer **{{ conditions_financieres.loyer.zone_tendue_encadrement.complement_loyer.valeur }}** €
- Caractéristiques du logement justifiant le complément de loyer : _________________________
{% endif %}

c) Le cas échéant, informations relatives au loyer du dernier locataire :
Mention obligatoire si le précédent locataire a quitté le logement moins de dix-huit mois avant la signature du bail.
[ ] Montant du dernier loyer acquitté par le précédent locataire (en €) : _________________________
[ ] Date de versement : _________________________
[ ] Date de la dernière révision du loyer : _________________________

2. Le cas échéant, modalités de révision :



a) Date de révision du loyer annuel : **{{ conditions_financieres.revision_loyer.date_revision.valeur }}**
b) Date ou trimestre de référence de l'Indice de Référence du Loyer : **{{ conditions_financieres.revision_loyer.trimestre_reference_irl.valeur }}**

B. Charges récupérables :
1. Modalité de règlement des charges récupérables :
{% if conditions_financieres.charges.modalite_reglement.valeur == 'Provisions' %}Provisions sur charges avec régularisation annuelle{% endif %}
{% if conditions_financieres.charges.modalite_reglement.valeur == 'Paiement périodique' %}Paiement périodique des charges sans provision{% endif %}
{% if conditions_financieres.charges.modalite_reglement.valeur == 'Forfait' %}Forfait de charges{% endif %}

2. Le cas échéant, montant des provisions sur charges ou du forfait de charges **{{ conditions_financieres.charges.montant.valeur }}** €

3. Si les parties conviennent d'un forfait de charges, ce forfait sera révisé chaque année dans les mêmes conditions que le loyer principal.

C. Le cas échéant, en cas de colocation, souscription par le bailleur d'une assurance pour le compte des colocataires : **{% if colocation.assurance_bailleur.valeur %}Oui{% else %}Non{% endif %}**
{% if colocation.assurance_bailleur.valeur %}
Montant total annuel récupérable au titre de l'assurance pour compte des colocataires **{{ colocation.montant_assurance.valeur }}** €
(montant de la prime d'assurance annuelle, éventuellement majoré dans la limite d'un montant fixé par décret en Conseil d'Etat),
Ce montant est récupérable par douzième soit _________________________ € par mois.
{% endif %}

D. Modalités de paiement :
Le loyer est payé **{{ conditions_financieres.paiement.periodicite.valeur }}**, **{{ conditions_financieres.paiement.type_paiement.valeur }}** et dû avant le **{{ conditions_financieres.paiement.jour_paiement.valeur }}** de chaque mois.
Le montant total dû pour un mois de location est de **{{ conditions_financieres.premier_versement.montant_total.valeur }}** €, détaillé comme suit :


- Loyer **{{ conditions_financieres.premier_versement.loyer.valeur }}** €
- Charges récupérables **{{ conditions_financieres.premier_versement.charges.valeur }}** €
- En cas de colocation, assurance récupérable pour le compte des colocataires _________________________ €

E. Le cas échéant, exclusivement lors d'un renouvellement de contrat, modalités de réévaluation d'un loyer manifestement sous-évalué :
Le montant de la hausse de loyer mensuelle est de _________________________ € appliquée :
[ ] par tiers* [ ] par sixième*
* selon la durée du contrat et le montant de la hausse de loyer.

## V. TRAVAUX

A. Le cas échéant, montant et nature des travaux d'amélioration ou de mise en conformité avec les caractéristiques de décence effectués depuis la fin du dernier contrat de location ou depuis le dernier renouvellement :
{% if travaux.effectues_depuis_dernier_bail.valeur %}
**{{ travaux.description.valeur }}**
Montant : **{{ travaux.montant.valeur }}** €
{% else %}
(Néant)
{% endif %}

Le cas échéant, montant des travaux d'amélioration effectués au cours des six derniers mois : _________________________

B. Le cas échéant, majoration du loyer en cours de bail consécutive à des travaux d'amélioration entrepris par le bailleur
Nature des travaux ou des équipements, modalités d'exécution, délai de réalisation ou d'acquisition : _________________________
Montant de la majoration du loyer _________________________ €
(Clause invalide pour les travaux de mise en conformité aux caractéristiques de décence)

C. Le cas échéant, diminution de loyer en cours de bail consécutive à des travaux entrepris par le locataire :
Nature des travaux : _________________________
Montant et durée de la diminution du loyer : _________________________ mois.

Modalités de dédommagement du locataire sur justification des dépenses effectuées en cas de départ anticipé : _________________________



## VI. GARANTIES

Pour la garantie de l'exécution des obligations du locataire, il est prévu un dépôt de garantie d'un montant de **{{ garanties.montant_depot_garantie.valeur }}** € (en toutes lettres _________________________ ).
*deux mois de loyer hors charges.

## VII. CLAUSE DE SOLIDARITÉ

Pour l'exécution de toutes les obligations du présent contrat en cas de pluralité de locataires, il y aura solidarité et indivisibilité entre eux.

## VIII. CLAUSE RÉSOLUTOIRE

Le présent contrat sera résilié de plein droit :


- en cas de défaut de paiement du loyer, des provisions de charge, ou de la régularisation annuelle de charge
- en cas de défaut de versement du dépôt de garantie
- en cas de défaut d'assurance des risques locatifs par le locataire (sauf si le bailleur a souscrit une assurance pour le locataire)
- en cas de trouble de voisinage constaté par une décision de justice

## IX. LE CAS ÉCHÉANT, HONORAIRES DE LOCATION

A mentionner lorsque le contrat de location est conclu avec le concours d'une personne mandatée et rémunérée à cette fin.
A. Dispositions applicables :
Il est rappelé les dispositions du I de l'article 5 (I) de la loi du 6 juillet 1989... (texte légal omis pour brièveté, voir original)

Plafonds applicables à ces honoraires :
Montant du plafond des honoraires imputables aux locataires en matière de prestation de visite du preneur, de constitution de son dossier et de rédaction de bail _________________________ €/m² de surface habitable ;
Montant du plafond des honoraires imputables aux locataires en matière d'établissement de l'état des lieux d'entrée : _________________________ €/m² de surface habitable.

B. Détail et répartition des honoraires :
1. Honoraires à la charge du bailleur :


- prestations de visite du preneur, de constitution de son dossier et de rédaction de bail : _________________________
- le cas échéant, prestation de réalisation de l'état des lieux d'entrée : _________________________
- autres prestations : _________________________

2. Honoraires à la charge du locataire :


- prestations de visite du preneur, de constitution de son dossier et de rédaction de bail : **{{ honoraires_location.part_locataire.valeur }}** €



- le cas échéant, prestation de réalisation de l'état des lieux d'entrée : _________________________

## X. AUTRES CONDITIONS PARTICULIÈRES
_________________________

## XI. ANNEXES

Sont annexées et jointes au contrat de location les pièces suivantes :
[ ] Le cas échéant, un extrait du règlement concernant la destination de l'immeuble...
[ ] Un dossier de diagnostic technique...
[ ] Une notice d'information relative aux droits et obligations des locataires et des bailleurs.
[ ] Un état des lieux, un inventaire et un état détaillé du mobilier...
[ ] Le cas échéant, une autorisation préalable de mise en location.
[ ] Le cas échéant, les références aux loyers habituellement constatés dans le voisinage...

Fait à **{{ signature.ville.valeur }}**, le **{{ signature.date.valeur }}**

Signature du bailleur (ou de son mandataire, le cas échéant)
Signature(s) précédée(s) de la mention « *Lu et approuvé* » :

_________________________

Signature du locataire
Signature(s) précédée(s) de la mention « *Lu et approuvé* » :

_________________________

Démarches électricité et gaz (locataire)
Contactez le 09 87 67 94 26 (non surtaxé, lundi-vendredi 8H-21H ; samedi 8H30-18H30, dimanche 9H-17H, service Selectra) pour mettre vos compteurs d'électricité et de gaz naturel à votre nom et éviter toute coupure.

Exemplaires originaux dont un remis à chaque signataires
