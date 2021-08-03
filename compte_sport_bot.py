"""
Petit bot pour compter les sports
lien à envoyer pour l'ajouter sur le groupe :
https://discord.com/api/oauth2/authorize?client_id=871442934954856478&permissions=67584&scope=bot
"""
from discord.ext import commands  # API discord

import json  # Charger l'historique des votes
from datetime import datetime  # Comparer les dates du plus récent message chargé

# Récupération du token du bot dans mon fichier config
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path='config')


bot = commands.Bot(command_prefix="!")  # Commandes s'activent avec ! en début de message


## Données des sports à identifier

sports = [  # l'index est utilisé comme un id, commun à sports, compteur, keywords
    "Handball",
    "Natation",
    "Badminton",
    "Basket",
    "Foot",
    "Escalade",
    "Volley",
    "Raid",
    "Aviron",
    "Boxe",
    "Judo",
    "Escrime",
    "Tennis",
    "Rugby",
    "Equitation",
    "Crossfit"
]

keywords = [  # On chope les keywords, et ils renvoient l'index correpsondant, tout en lowercase
    ("hand", "handball"),
    ("natation"),
    ("bad", "badmin", "badminton"),
    ("basket"),
    ("foot", "football"),
    ("escalade"),
    ("volley"),
    ("raid"),
    ("aviron"),
    ("boxe"),
    ("judo"),
    ("escrime"),
    ("tennis"),
    ("rugby"),
    ("équitation", "equitation"),
    ("crossfit")
]

prefixes = ['1)', '1/', '1.']


# Variables pour compter / vérifier les id
compteur = [0] * len(sports)
votes = {}  # Dict qui stocke les derniers choix.
# format : { int-id utilisateur : int-index du sport correspondant}

## Stockage des anciens résultats pour éviter d'avoir à relire tous les anciens messages

date = ''  # date du dernier message lu : on ne remonte pas plus loin
# type de l'objet : datetime.datetime
date_format = '%d/%m/%Y %H:%M:%S'  # année/mois/jour heure:minute:seconde
# Remarque : minuscule => 2 chiffre. maj => 4 chiffres (pour l'année, notamment)

"""
Format du dict à enregistrer en format JSON :

{
    'date' : format date discord du dernier message,

    'history' : {  # Ici, les id et leurs votes
        id1 : vote1,
        id2 : vote2,
    }
}

"""

def load_data():
    """Charge les données du fichier json"""

    global votes  # On charge tout à nouveau dans le dict votes
    global date  # dernière date où un message a été pris en compte

    # Chargement des données
    file = open("data.json")  # ouverture du fichier
    file_data = json.loads(file.read())  # données -> file_data : dict

    file.close()  # Pas nécessaire à la fin d'une fonction, parce que l'objet file sera supprimé

    date = datetime.strptime(file_data['date'], date_format)  # On charge cette dernière date
    votes = file_data['history']  # On charge le dict : data[id] = id_vote


def write_data():
    """Ecrit les dernières données dans le fichier"""
    file_data = {}
    file_data['date'] = date.strftime(date_format)  # datetime.datetime -> str
    file_data['history'] = votes

    file = open("data.json", "w")  # "w" : écrase toutes les données écrites

    # Ecriture des données dans le fichier, en gardant le truc lisible
    file.write(json.dumps(file_data, sort_keys=True, indent=4))

    file.close()  # idem


## Fonctions

def get_msg(message : str, prefixes : str) -> str:  # Renvoie le message qui suit le préfixe (découpe le mot)
    
    index = -1
    i = 0
    while i < len(prefixes) and index == -1:  # On parcourt tous les préfixes ('1)', '1/') et on s'arrête au 1er trouvé
        index = message.find(prefixes[i])
        i += 1

    if index == -1:  # Pas de préfixe trouvé : on ignore
        return None
    else:

        index += len(prefixes[i - 1])  # On passe le préfixe, ça donne l'index du 1er mot après

        while index < len(message) and not message[index].isalpha():  # tant qu'il n'y a pas de lettre (' ', emoji, ...)
            index += 1  # On passe les espaces après le préfixe

        # On a l'index du début du mot : index
        if index < len(message):
            index2 = index  # On parcourt le reste jusqu'à trouver la fin du mot

            while index2 < len(message) and message[index2].isalpha():  # tant qu'il y a des lettres : on parcourt le mot
                index2 += 1

            # On a l'index de la fin du mot : index2

            if index2 < len(message):
                # Le message va de index à index2 -1 (ex : "xxxx 1) sport blablabla")
                return message[index : index2]
            else:
                # Le message va jusqu'à la fin (ex : "xxxxx 1) sport")
                return message[index : len(message)]
        else:
            return None  # message en "xxxx1)    " sans rien


def get_index(message : str) -> int:
    # Renvoie l'index du message s'il est dans la liste de keywords. Sinon, -1
    message = message.lower()  # tout en minuscule pour ne pas s'emmerder

    for i in range(len(keywords)):
        if message in keywords[i]:
            return i
    return -1  # par défaut


def message_resultats() -> str:
    # renvoie le message à afficher
    message = 'Résultats :\n'

    for i in range(len(sports)):
        message += f"{sports[i]} : {compteur[i]}\n"

    return message

id_2_sports = 871134587550593044  # Id de la conversation 2 sports

## Commandes du bot

# Teste si le bot est opérationnel
@bot.event
async def on_ready():
    print("le bot est prêt")


@bot.command(name="bonjour")  # commande !bonjour
async def dit_bonjour(contexte):
    await contexte.channel.send(f"Salut, {contexte.author.name}")

@bot.command(name="bot,_présente_toi")
async def presenter(contexte):

    if contexte.channel.id == id_2_sports:

        message = "Coucou,\nje suis un bot et je compte les 1ers choix des gens pour le sport.\n"
        message += "Merci de mettre '1)' puis votre premier choix, sinon j'arrive pas à lire.\n"
        message += "Je ne fonctionne que quand <@870249964561903617> me connecte\n"
        message += "Commandes : '!bot,_présente_toi', '!dernières_nouvelles', '!bonjour', '!compte'"
    else:
        message = "Coucou,\n"
        message += "Je suis un bot qui participe à deux-sports-preferes"

    await contexte.channel.send(message)


@bot.command(name="compte")  # commande !compte
async def compte_sports(contexte):

    if contexte.channel.id == id_2_sports:
        global compteur, votes, date  # global : toutes les variables qu'on va modifier
        
        # Tous les messages envoyés
        messages = await contexte.channel.history().flatten()  # pas oublier le flatten!!

        # Reset du compteur
        compteur = [0] * len(sports)
        # Reset des votes, en chargeant les données du fichier data.json
        load_data()  # variables rechargées : votes, date

        # On parcourt tous les messages de l'historique et on stocke pour chaque utilisateur l'id
        # du sport de son 1er choix. Ca écrase automatiquement les choix antérieurs au dernier

        # REMARQUE : ça parcourt la discussion en remontant. Pour chaque message, on vérifie que l'id
        # de l'utilisateur ne présente pas déjà un sport.
        
        i = 0

        print("commande compte reçue")  # DEBUG

        # Tant qu'il reste des messages et qu'on n'est pas arrivé au plus récent chargé:
        # pour un objet datetime.datetime, supérieur (>) veut dire plus récent
        while i < len(messages) and messages[i].created_at > date:

            print("encore un message!!")
            
            if messages[i].author.id not in votes:  # C'est le 1er vote de l'utilisateur

                msg = get_msg(messages[i].content, prefixes)

                if msg is not None:  # '1)' ou '1/' trouvé, renvoie le message qui suit

                    index = get_index(msg)

                    if index != -1 and index < len(sports):
                        votes[messages[i].author.id] = index  # On stocke le sport avec l'id du 'votant'
            i += 1  # passage au message suivant


        # Tout a été stocké dans votes, 1 par personne, seulement le dernier compte
        # On parcourt maintenant le dict pour incrémenter le compteur
        for id, choix in votes.items():

            compteur[choix] += 1  # 1 vote de + sur le sport correspondant

        # Avant de finir : on récupère la dernière date lue (celle du 1er message, le + récent)
        date = messages[0].created_at  # objet datetime.datetime (python)
        
        # Enfin : affichage des résultats, et réécriture dans le fichier
        write_data()
        await contexte.channel.send(message_resultats())

    else:
        await contexte.channel.send("On n'est pas dans 2-sports-preferes...")
    

@bot.command(name="dernières_nouvelles")  # Pour annoncer les dernières updates du bot
async def annonce(contexte):

    message = "Je retiens les votes une fois qu'on m'a appelé, je n'ai plus besoin de relire tout"
    message+= " l'historique des messages à chaque fois ! Youpi."

    await contexte.channel.send(message)

# lancement du bot
bot.run(os.getenv("TOKEN"))  # Token secret du bot