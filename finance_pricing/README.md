# Contrôle de valorisation d'une option sur panier — prototype 0.1

Ce prototype calcule un encadrement du prix d'un call européen sur deux actifs,
contrôle un prix proposé et exporte un certificat rejouable. Il permet de tester
un mécanisme de validation numérique avec des données fictives.

## Installation et lancement

Python 3.10 ou supérieur ; installation de la version testée :

```sh
python3 -m pip install -r requirements.txt
python3 pricer.py examples/basket.json --tolerance 1/100 --output prix.json
python3 pricer.py --verify prix.json
python3 pricer.py --verify prix.json --quote 9.57
python3 test_pricer.py
python3 benchmark.py
```

Tous les paramètres financiers sont dans `examples/basket.json`. Utiliser des
entiers ou chaînes rationnelles (`"3/100"`), sans flottants JSON. Les prix et le
strike doivent avoir la même unité monétaire ; la maturité est en années, les
volatilités sont annualisées et le taux est continûment composé. Le modèle est
explicitement sans dividendes.

Le certificat contient les paramètres, la partition d'intégration, la borne des
queues de distribution et les bornes rationnelles du prix. Les statistiques
décimales sont des affichages approximatifs. La tolérance concerne le milieu exact
du certificat et non une estimation par échantillonnage.

## Interpréter le résultat

- `tolerance_met` : la demi-largeur de l'intervalle est au plus la tolérance.
- `budget_exhausted` : les bornes restent valides mais sont trop larges ; code de sortie 2.
- `truncation_too_small` : la borne de queue empêche d'atteindre la tolérance ;
  augmenter `--truncation` au-delà de la valeur par défaut 6 ; code de sortie 2.
- Un modèle non pris en charge est refusé ; il ne reçoit pas de certificat valide.

Le contrôle d'un prix indique s'il est au-dessus, au-dessous ou à l'intérieur de
l'intervalle du modèle. Un résultat intérieur ne prouve pas que le prix proposé
est exact, équitable ou négociable. Le contrôle est disponible même si la
tolérance n'est pas atteinte, mais l'intervalle est alors plus large.

## Périmètre

Call européen de panier arithmétique, deux actifs lognormaux corrélés, poids
positifs ou nuls de somme 1, paramètres constants, corrélation entre 0 et 1.
Les paramètres fictifs par défaut sont : spots 100/100, poids 50/50, volatilités
20 %/25 %, corrélation 0,60, taux 3 %, échéance un an, strike 100.

Le modèle ne couvre pas les produits à barrière, l'exercice anticipé, les coupons,
les dividendes, la volatilité stochastique, les corrélations négatives ou une
calibration de marché. Les tests de volatilité sont des scénarios distincts,
pas une garantie uniforme pour une plage continue de paramètres.

Le certificat borne l'erreur numérique sous ce modèle. Il ne borne pas le risque
de marché, le risque de modèle ou une perte future. Ce prototype n'est pas une
validation réglementaire et ne constitue pas un conseil de transaction.

## Éléments livrés

- `pricer.py` : moteur, contrôle d'un prix, vérificateur et estimateurs R₂/Halton.
- `METHOD.md` : hypothèses, formule conditionnelle, preuve des bornes et antécédents.
- `RAPPORT.md` : mesures réelles et proposition d'usage financier.
- `baseline_certificate.json` : résultat central.
- `vol1_*_certificate.json` : deux scénarios de volatilité.
- `benchmark_results.json` : mesures et estimations échantillonnées.
- `test_results.txt` : neuf tests exécutés, dont plusieurs altérations de certificat.

L'intégration conditionnelle et l'arithmétique de boules sont classiques. R₂ sert
uniquement de comparateur et ne fonde pas la garantie. La contribution actuelle
est un prototype de contrôle concret, pas une revendication de première mondiale.
Le vérificateur partage les formules et la bibliothèque native avec le moteur ;
ce n'est pas une preuve formelle indépendante.

Les temps du rapport mesurent le calcul local après chargement des bibliothèques,
hors écriture et hors vérification, cette dernière étant chronométrée séparément.
Ils ne permettent pas de conclure à une supériorité sur les moteurs existants.

Code et documentation sous licence MIT. Développement assisté par OpenAI Codex,
17 septembre 2026. Les droits de python-flint/FLINT restent ceux de leurs auteurs ;
les bibliothèques natives ne sont pas redistribuées dans cette archive.
