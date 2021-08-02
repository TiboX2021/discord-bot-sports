"""
Petit bot pour compter les sports
lien à envoyer pour l'ajouter sur le groupe :
https://discord.com/api/oauth2/authorize?client_id=871442934954856478&permissions=67584&scope=bot

"""


from discord.ext import commands  # API discord

from emoji.core import demojize

# Récupération du token du bot dans mon fichier config
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path='config')


bot = commands.Bot(command_prefix="!")  # Commandes s'activent avec ! en début de message


sports = [  # l'index est utilisé comme un index
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
]

compteur = [0] * len(sports)  # 1 index => "sport" & nombre

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
]

prefixes = ['1)', '1/']

def is_letter(char):
    """renvoie True si c'est une lettre, False si c'est un nombre, un emoji, etc
    ça permet de délimiter le sport précisé après 1)
    """

    if char == ' ' or char == '\n' or char == ':':  # début emoji, fin ligne, etc...
        return False
    else:
        return True


def get_msg(message : str, prefixes : str) -> str:  # Renvoie le message qui suit le préfixe
    
    index = -1
    i = 0
    while i < len(prefixes) and index == -1:
        index = message.find(prefixes[i])
        i += 1


    if index == -1:
        return None
    else:

        message = demojize(message)  # Faciliter le repérage des emoji, qui commencent par ':'

        index += len(prefixes[i - 1])  # On passe le préfixe, ça donne l'index du 1er mot après
        while index < len(message) and not is_letter(message[index]):
            index += 1  # On passe les espaces après le préfixe

        # On a l'index du début du mot
        if index < len(message):
            index2 = index  # On parcourt le reste jusqu'à trouver le 1er espace

            while index2 < len(message) and is_letter(message[index2]):
                index2 += 1

            if index2 < len(message):
                # Le message va de index à index2 -1
                return message[index : index2]
            else:
                # Le message va jusqu'à la fin
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


def incremente(index : int):
    # Incrémente le compteur correspondant. Prend en compte le cas -1
    if index != -1 and index < len(compteur):
        compteur[index] += 1


def message_resultats() -> str:
    # renvoie le message à afficher
    message = 'Résultats :\n'

    for i in range(len(sports)):
        message += f"{sports[i]} : {compteur[i]}\n"

    return message

id_2_sports = 871134587550593044  # Id de la conversation 2 sports
# id_2_sports = 871445114772410431  # id test  principal

# Teste si le bot est opérationnel
@bot.event
async def on_ready():
    print("le bot est prêt")


@bot.command(name="bonjour")  # commande !bonjour
async def dit_bonjour(contexte):
    await contexte.channel.send("Salut")

@bot.command(name="bot,_présente_toi")
async def presenter(contexte):

    if contexte.channel.id == id_2_sports:

        message = "Coucou,\nje suis un bot et je compte les 1ers choix des gens pour le sport.\n"
        message += "Merci de mettre '1)' puis votre premier choix, sinon j'arrive pas à lire.\n"
        message += "Evitez de voter deux fois, je suis trop con pour faire la différence.\n"
        message += "Je ne fonctionne que quand <@870249964561903617> me connecte\n"
        message += "Commandes : '!bot,_présente_toi', '!bonjour', '!compte'"
    else:
        message = "Coucou,\n"
        message += "Je suis un bot qui participe à deux-sports-preferes"

    await contexte.channel.send(message)


@bot.command(name="compte")  # commande !compte
async def compte_sports(contexte):

    if contexte.channel.id == id_2_sports:
        global compteur
        
        # Tous les messages envoyés
        messages = await contexte.channel.history().flatten()  # pas oublier le flatten!!

        # Reset du compteur
        compteur = [0] * len(sports)

        for message in messages:

            msg = get_msg(message.content, prefixes)

            if msg is not None:  # '1)' trouvé, renvoie le message qui suit

                incremente(get_index(msg))

        await contexte.channel.send(message_resultats())

    else:
        await contexte.channel.send("On n'est pas dans deux-sports-preferes...")
    

# lancement du bot
bot.run(os.getenv("TOKEN"))  # Token secret du bot