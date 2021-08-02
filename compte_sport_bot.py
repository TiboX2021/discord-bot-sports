"""
Petit bot pour compter les sports
lien à envoyer pour l'ajouter sur le groupe :
https://discord.com/api/oauth2/authorize?client_id=871442934954856478&permissions=67584&scope=bot
"""
from discord.ext import commands  # API discord


# Récupération du token du bot dans mon fichier config
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path='config')


bot = commands.Bot(command_prefix="!")  # Commandes s'activent avec ! en début de message


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
]

compteur = [0] * len(sports)  # 1 index => "sport" & nombre
votes = {}  # Dict qui stocke les derniers choix.
# format : { int-id utilisateur : int-index du sport correspondant}

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
]

prefixes = ['1)', '1/']


def get_msg(message : str, prefixes : str) -> str:  # Renvoie le message qui suit le préfixe
    
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
        global compteur, votes
        
        # Tous les messages envoyés
        messages = await contexte.channel.history().flatten()  # pas oublier le flatten!!

        # Reset du compteur
        compteur = [0] * len(sports)
        # Reset des votes:
        votes = {}

        # On parcourt tous les messages de l'historique et on stocke pour chaque utilisateur l'id
        # du sport de son 1er choix. Ca écrase automatiquement les choix antérieurs au dernier

        # REMARQUE : ça parcourt la discussion en remontant. Pour chaque message, on vérifie que l'id
        # de l'utilisateur ne présente pas déjà un sport.
        for message in messages:

            if message.author.id not in votes:  # C'est le 1er vote de l'utilisateur

                msg = get_msg(message.content, prefixes)

                if msg is not None:  # '1)' ou '1/' trouvé, renvoie le message qui suit

                    index = get_index(msg)

                    if index != -1 and index < len(sports):
                        votes[message.author.id] = index  # On stocke le sport avec l'id du 'votant'


        # Tout a été stocké dans votes, 1 par personne, seulement le dernier compte
        # On parcourt maintenant le dict pour incrémenter le compteur
        for id, choix in votes.items():

            compteur[choix] += 1  # 1 vote de + sur le sport correspondant
        
        # Enfin : affichage des résultats
        await contexte.channel.send(message_resultats())

    else:
        await contexte.channel.send("On n'est pas dans 2-sports-preferes...")
    

@bot.command(name="dernières_nouvelles")  # Pour annoncer les dernières updates du bot
async def annonce(contexte):

    message = "Je sais maintenant faire la différence quand une personne donne plusieurs fois ses choix, "
    message+= "et je ne prend en compte que le dernier vote ! Youpi."

    await contexte.channel.send(message)

# lancement du bot
bot.run(os.getenv("TOKEN"))  # Token secret du bot