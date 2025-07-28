# Guide d'utilisation des rapports enrichis CyberShield

## Introduction

Les rapports de vulnérabilités CyberShield ont été enrichis pour inclure des solutions détaillées et des liens vers des ressources pertinentes pour chaque vulnérabilité détectée. Ce guide explique comment accéder à ces rapports enrichis et comment les utiliser efficacement.

## Accès aux rapports enrichis

### Via le tableau de bord

1. Connectez-vous à votre compte CyberShield
2. Accédez à la section "Historique des scans"
3. Sélectionnez un scan terminé
4. Cliquez sur "Voir le rapport détaillé"

### Formats disponibles

Les rapports sont disponibles dans plusieurs formats :

- **HTML** : Visualisation interactive dans le navigateur
- **PDF** : Document téléchargeable pour archivage ou partage
- **JSON** : Format structuré pour intégration avec d'autres outils

Pour télécharger un rapport au format PDF, cliquez sur le bouton "Télécharger en PDF" dans la vue détaillée du rapport.

## Structure des rapports enrichis

Chaque rapport enrichi comprend :

1. **Résumé du scan** : Date, cible, durée et statistiques globales
2. **Tableau récapitulatif** : Nombre de vulnérabilités par niveau de sévérité
3. **Liste détaillée des vulnérabilités** : Pour chaque vulnérabilité détectée :
   - Nom et description
   - Niveau de sévérité et score CVSS
   - **Solution recommandée** (nouveauté)
   - **Liens vers des ressources** pour corriger la vulnérabilité (nouveauté)
   - Références techniques (CVE, articles, etc.)

## Utilisation des solutions recommandées

### Comprendre les solutions

Pour chaque vulnérabilité, le rapport fournit :

- Une description claire de la solution recommandée
- Des étapes pratiques pour corriger la vulnérabilité
- Des alternatives lorsque plusieurs approches sont possibles

### Utiliser les liens de ressources

Les liens fournis dans les rapports sont classés par catégories :

- **Guides officiels** : Documentation des éditeurs (Microsoft, Apache, etc.)
- **Bulletins de sécurité** : Informations des CERT (CERT-FR, ANSSI, etc.)
- **Tutoriels pratiques** : Guides étape par étape pour appliquer les correctifs

Ces liens sont régulièrement mis à jour pour refléter les meilleures pratiques actuelles.

## Exemple d'utilisation

Prenons l'exemple d'une vulnérabilité Log4Shell (CVE-2021-44228) détectée :

1. Le rapport identifie la vulnérabilité avec sa description et sa sévérité (Critique)
2. La section "Solution recommandée" indique : "Mettre à jour Log4j vers la version 2.15.0 ou supérieure, ou désactiver la fonctionnalité JNDI."
3. Les liens de ressources incluent :
   - Le guide officiel d'Apache
   - L'alerte du CERT-FR
   - Les recommandations de l'ANSSI

En suivant ces ressources, vous pouvez rapidement comprendre et corriger la vulnérabilité.

## Avantages des rapports enrichis

- **Gain de temps** : Accès direct aux solutions sans recherches supplémentaires
- **Fiabilité** : Sources d'information vérifiées et à jour
- **Contextualisation** : Solutions adaptées à chaque type de vulnérabilité
- **Traçabilité** : Documentation complète des problèmes et de leurs résolutions

## Support

Si vous avez des questions sur l'interprétation des rapports ou la mise en œuvre des solutions recommandées, contactez notre équipe de support à support@cybershield-algeria.com.
