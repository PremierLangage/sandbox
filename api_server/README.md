# PlayExo Sandbox

## FrozenResource

**POST loader/fr/**
Reçoit des données au format Json.  
Fais un hachage de ces données et les enregistre en base de données si elles ne sont pas présentes.  
Renvoie un code `200` et la **FrozenResource** si tout s'est bien passé, un code `-1` et la **FrozenResource** si elle était déja présente.
Si les données ne sont pas présentes ou ne sont pas au format Json, les codes d'erreur sont respectivement `-2` et `-3`.


**GET loader/fr/\<int:id>/**
Reçoit l'`id` d'une **FrozenResource** par url.  
Renvoie la **FrozenResource** si cette dernière est présente, sinon renvoie un code d'erreur `-4`.


## PlayDemo
**POST loader/demo/pl/**

### Build Exo
Reçoit au format Json un exercice PL, construit l'environnement et la config à envoyer à la sandbox.  
**1 -** Renvoit la réponse de la sandbox.

### Grade Exo
Reçoit la réponse de l'utilisateur et l'id de l'environnement build précédement.  
**1 -** Construit l'environnement et la config à envoyer à la sandbox.  
**2 -** Renvoit la réponse de la sandbox.


## PlayActivity
**POST exec/**
**Reçoit :**
| variable     | type | utilité                                                            | obligatoire                          |
| :----------: | :--: | :----------------------------------------------------------------: | :----------------------------------: |
| path_command | str  | chemin où seront exécutées les commandes                           | Oui                                  |
| command      | list | liste de commandes à exécuter dans l'environnement                 | Oui                                  |
| `frozen_id`  | str  | id d'une FrozenResource                                            | Oui si aucun `env_id` n'est donné    |
| `env_id`     | str  | id d'un environnement                                              | Oui si aucun `frozen_id` n'est donné |
| path_env     | str  | chemin où sera stocké l'environnement créé                         | Non                                  |
| result       | str  | chemin vers un fichier qui sera renvoyé dans la réponse au serveur | Non                                  |
| answer       | json | une answer si une réponse doit être exécutée                       | Non                                  |

**1 -** Si une `frozen_id` est donnée, construit l'environnement d'une activité à partir de la **FrozenResource**.  
**2 -** Sinon construit un environnement vide et en utilisera un déjà existant grâce à `env_id`  
**3 -** Construit la config à envoyer à la sandbox.  
**4 -** Renvoit la réponse de la sandbox.
