# Usage financier : contrôler une valorisation

## Besoin retenu

Un analyste de validation reçoit le prix d'un produit dérivé calculé par un moteur
Monte Carlo ou quasi-Monte Carlo. Il veut savoir si le calcul est suffisamment
précis sous un modèle fixé. Le prototype fournit un encadrement avec lequel
comparer ce prix, ainsi que les paramètres et données nécessaires pour le rejouer.

Il ne décide pas si le modèle décrit correctement le marché. Il peut notamment
servir de référence de contrôle sur un petit sous-ensemble de produits simples,
avant toute intégration dans un dispositif opérationnel.

## Exemple exécuté

Call européen sur un panier de deux actifs fictifs : spots 100 et 100, poids
50/50, volatilités 20 % et 25 %, corrélation 0,60, taux continûment composé 3 %,
échéance un an, strike 100. Modèle lognormal sans dividendes, sous probabilité
risque-neutre. Aucun cours de marché n'a été utilisé.

Le prix central calculé est approximativement 9,4745085 unités monétaires par
option. La demi-largeur exacte de l'encadrement est inférieure à 0,01. La partie
du prix située hors du domaine normal [-6,6] est bornée par environ 3,222e-7 ;
le calcul ne l'a donc pas simplement ignorée.

La partition finale comporte 2 040 intervalles. Dans cette exécution, le calcul
principal a pris environ 0,156 s et le rejeu environ 0,081 s, après chargement
des bibliothèques. Ces temps locaux mesurés une seule fois ne constituent pas
un benchmark industriel ni une mesure incluant installation/importation.

## Ce que le contrôle détecte

À 1 024 points, l'estimateur R₂ du prototype renvoie environ 9,5701710. Ce nombre
est supérieur à la borne du prix, proche de 9,4845041. L'erreur de cette estimation
est donc d'au moins 0,0856 unité pour ce modèle : elle n'atteint pas la tolérance
0,01. À 4 096 points, l'estimation R₂ est environ 9,4750886, à l'intérieur de
l'intervalle. L'appartenance à cet intervalle n'est pas, à elle seule, un
certificat d'erreur de 0,01 pour cette estimation particulière.

Ce seul exemple ne classe pas R₂, Halton et les autres méthodes. Les échantillons
utilisent des flottants et une transformation normale inverse, sans certificat
propre. Aucune comparaison avec Sobol ou un moteur industriel n'a encore été menée.

## Erreur numérique et sensibilité aux paramètres

On fait varier uniquement la volatilité du premier actif. Les intervalles
ci-dessous sont arrondis vers l'extérieur à quatre décimales :

| Volatilité du premier actif | Encadrement du prix | Intervalles | Calcul (s) |
|---|---:|---:|---:|
| 20 % (central) | [9.4645 ; 9.4846] | 2040 | 0.156 |
| 19 % | [9.2952 ; 9.3153] | 1993 | 0.152 |
| 21 % | [9.6347 ; 9.6548] | 2089 | 0.158 |

L'effet des scénarios est de l'ordre de 0,17 unité par rapport au scénario central,
donc nettement supérieur à la tolérance numérique 0,01. C'est une démonstration
concrète de la nécessité de distinguer précision de calcul et choix des paramètres.
Ces trois scénarios ne constituent pas une distribution d'incertitude ni un
encadrement uniforme d'un ensemble continu de calibrations.

## Vérifications

Les neuf tests ont réussi : comparaison à Black–Scholes pour un seul actif,
actifs identiques parfaitement corrélés, deuxième actif seul, volatilités nulles,
monotonie et queue, rejets de modèles invalides, budgets insuffisants, contrôle
sur un prix et plusieurs falsifications de certificats. Les contrôles analytiques
utilisent la même bibliothèque de fonctions spéciales, avec une formule de prix
distincte. Cela ne remplace pas une revue indépendante du modèle et du code.

## Innovation à poursuivre

La cible proposée est un petit outil de validation de prix : import des paramètres,
comparaison de plusieurs moteurs, encadrement numérique, scénarios et rapport
reproductible. Le développement actuel démontre cette chaîne sur un produit limité.

Les prochaines améliorations à évaluer sont :

1. Une comparaison à tolérance et modèle identiques avec une bibliothèque financière
   de référence, incluant les coûts de calcul et de rejeu.
2. Une intégration d'ordre supérieur certifiée de l'espérance conditionnelle,
   pour diminuer le nombre d'évaluations tout en conservant les bornes.
3. Un traitement certifié d'intervalles de paramètres, distinct des trois scénarios
   ponctuels actuellement calculés.
4. Un contrôle indépendant des certificats, puis seulement une extension à d'autres
   produits et facteurs de risque.

La réduction conditionnelle existe déjà (Bayer, Siebenmorgen, Tempone), tout comme
l'intégration adaptative financière et les garanties numériques d'Arb/FLINT. La
nouveauté scientifique du futur algorithme et sa valeur commerciale restent à
établir. Une publication ne devrait revendiquer que les améliorations mesurées.

## Sources principales consultées

- Bayer, Siebenmorgen et Tempone, *Smoothing the payoff for efficient computation
  of Basket option prices* : https://arxiv.org/abs/1607.05572
- De Luigi, Lelong et Maire, *Adaptive numerical integration and control variates
  for pricing Basket Options* : https://arxiv.org/abs/1210.7783
- QMCPy, démonstrations 2026 et options financières :
  https://qmcsoftware.github.io/QMCSoftware/demos/talk_paper_demos/JOSS2026/joss2026/
- FLINT/Arb, arithmétique réelle rigoureuse : https://flintlib.org/doc/arb.html

Consultation le 17 septembre 2026. La version de python-flint testée est 0.8.0.
