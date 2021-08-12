"""
2ème version du bot pour compter les sports

=> code mieux factorisé, + facile à changer / lire
=> plus lisible
"""

from typing import List, Tuple, Dict, Any  # Type hints de listes en python
import json  # Sauvegarde des données en format JSON (fichier .json)
from datetime import datetime  # Gestion de la date des messages (optimisation)

from discord.ext import commands  # API discord
from dotenv import load_dotenv  # Récupération du token secret du bot dans le fichier config
import os

load_dotenv(dotenv_path='config')  # Chargement des données 'sensibles'
# (token secret du bot, id de la conv 2-sports-preferes, stockés dans le fichier config)


## Constantes / formats
date_format = '%d/%m/%Y %H:%M:%S'  # jj/mm/yyy hh:mm:ss  (format de l'objet datetime)


## Fonctions utiles
"""
Stockage des données dans un fichier json
Objectif : garder en mémoire les anciens votes déjà comptés pour éviter d'avoir
à tout refaire à chaque appel de la commande

Format des données :
{
	"date" : date du dernier message pris en compte,

	"history" : {
		"id1" : id_vote1,
		"id2" : id_vote_2
	}
}

On garde en mémoire le dernier id de sport donné pour chaque personne qui a fait un vote valide
=> cf fonction load_data
"""


def load_data(filename : str) -> Tuple[datetime, Dict[str, int]]:
	"""
	Charge les données du fichier 'filename', et renvoie la liste des entrées correspondantes.
	
	Si le fichier n'existe pas, renvoie None pour chaque entrée demandée. De toutes façons, le fichier
	est réécrit à la fin du comptage.
	"""

	try:
		file = open(filename, 'r')  # Ouverture du fichier
		file_data = json.loads(file.read())  # données -> file_data : dict
		file.close()  # Fermeture du fichier

		date = datetime.strptime(file_data['date'], date_format)  # On charge cette dernière date (obj datetime)
		votes = file_data['history']  # On charge le dict : data[id] = id_vote

		return date, votes

	except IOError:
		print("Erreur à l'ouverture du fichier")

		return (None, None)


def write_data(filename : str, data : dict) -> None:
	"""Ecrit les données du dict dans le fichier filename,
	après avoir tout encodé au format JSON
	"""
	file = open(filename, 'w')  # 'w' : écrasage de toutes les données précédentes

	file.write(json.dumps(data, sort_keys=True, indent=4))

	file.close()  # En pratique, inutile, car l'objet file est supprimé à la fin de la fonction


def next_word(message : str, prefixes : str) -> str:
	"""
	Découpe le mot qui suit le préfixe, et le renvoie
	(il ne reste qu'à le comparer avec la liste de keywords)

	Il peut y avoir autant d'espaces, emoji, chiffres entre préfixe et mot, ils sont ignorés
	via str.isalpha

	Si aucun mot n'est détecté, renvoie None
	"""
	
	# Repérage du préfixe (par son index dans la chaine de caractères) :
	index = -1
	i = 0
	while i < len(prefixes) and index == -1:  # On parcourt tous les préfixes ('1)', '1/') et on s'arrête au 1er trouvé
		index = message.find(prefixes[i])
		i += 1


	if index == -1:  # Pas de préfixe trouvé : on ignore
		return None

	else:  # préfixe trouvé : on commence le découpage du mot qui le suit

		index += len(prefixes[i - 1])  # On passe le préfixe, ça donne l'index du 1er caractère suivant

		# Recherche de l'index du 1er caractère qui suit le préfixe
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
			return None  # aucune lettre après le préfixe, jusqu'à la fin du message


def keyword_index(keyword : str, keywords : List[List[str]]) -> int:
	"""
	Renvoie l'index d'un keyword dans une liste d'ensemble de keywords.

	Si aucune correspondance : renvoie -1
	"""
	keyword = keyword.lower()  # Passage en lowercase pour la comparaison avec des keywords en minuscule aussi.

	for i in range(len(keywords)):
		if keyword in keywords[i]:
			return i  # 1ère correspondance détectée est renvoyée
	return -1  # par défaut


def merge(last_dict : dict, new_dict : dict) -> dict:
	"""
	Ajoute les entrées de 'new_dict' à 'last_dict'
	last_dict n'est pas modifié
	"""
	merged_dict = last_dict.copy()

	for id, choix in new_dict.items():
		merged_dict[id] = choix

	return merged_dict


def count_occurences(data : Dict[Any, int], values : list) -> List[int]:
	"""
	Compte le nombre d'apparition de chaque valeur entier de 0 à max_index
	dans le dict data. Renvoie la liste des nombres d'apparition.
	values est nécessaire juste pour avoir le bon nombre.
	"""
	compteur = [0] * len(values)  # Compteur vide
	
	for id, choix in data.items():

		compteur[choix] += 1  # +1 vote sur le sport correspondant
	
	return compteur


def summary_msg(values : List[str], count : List[int], display_percent : bool=True, display_total : bool=True) -> str:
	"""
	Renvoie le message de décompte des valeurs, à afficher.

	percent : affiche aussi le pourcentage par rapport au total
	Le pourcentage est à une décimale (bon compromis entre précision et concision)
	total : True -> le total de votants est affiché
	"""
	total = sum(count)

	if total == 0:
		return "Aucun vote"
	else:
		message = ""

		for i in range(len(values)):

			message += f"{values[i]} : {count[i]}"  # Ajout du compte

			if display_percent:
				message += f"	({round(100*count[i]/total, 1)}%)"  # Ajout du pourcentage par rapport au total

			message += '\n'  # Retour à la ligne

		if display_total:
			# Ajout du nombre total de votes (après une ligne supplémentaire)
			message += f"\nTOTAL : {total}"

		return message


## Classe compteur (optimisé pour être réutilisable à l'infini)

# Message de fin pour les précisions sur le fonctionnement du bot

# A afficher avant les résultats du décompte
results_header = "Résultats :\n\n"

warning_msg = "\n\nTant que je ne suis pas connecté, pas la peine d'essayer de lancer des !commandes (et je suis pas souvent connecté...)"


class Compteur:
	"""classe Compteur : 
	
	Permet de gérer un compteur
	-> contient toutes les données nécessaires (fichier JSON, keywords, valeurs...)
	ainsi que les fonctions pour faire tout ça automatiquement

	* prefixes : liste des marqueurs recherchés pour identifier le vote ("1)", "1/", ...)

	* valeurs : la liste des choix possibles. Contient les str à afficher dans le message bilan

	* keywords : liste des listes des mots clés qui correspondent à chaque valeur possible.
	Une valeur peut avoir plusieurs mots-clés (ex : "Handball" : ("hand", "handball"))
	REMARQUE : ce sont des mots en Lowercase : pour ne pas avoir à gérer les MaJuScUlEs, tout est
	passé en lowercase pendant la comparaison des keywords

	* data_file : nom (chemin) vers le fichier JSON dans lequel sont stockées toutes les anciennes données,
	dans le format indiqué plus haut.

	* id_conv : l'id de la conversation concernée. Permet de réduire l'usage du compteur à une conversation
	en particulier. Si None, pas de restriction

	* conv_name : nom de la conversation. Sert à préciser la conversation à laquelle le compteur est attribué. Si
	None, le message d'erreur sera plus générique. Si id_conv=None, ce paramètre est inutile.

	* start_msg, end_msg : messages à afficher avant et après le message de décompte (titre, indications, etc)

	"""

	def __init__(self, prefixes : List[str], valeurs : List[str], keywords : List[List[str]],
		data_file : str, id_conv : int=None, conv_name : str=None,
		start_msg : str="", end_msg : str="",
		percent : bool=True, total : bool=True) -> None:
		
		self.prefixes = prefixes
		self.valeurs = valeurs
		self.keywords = keywords
		self.data_file = data_file
		self.id_conv = id_conv
		self.conv_name = conv_name

		self.start_msg = start_msg
		self.end_msg = end_msg

		self.percent, self.total = percent, total  # cf summary_msg


	async def update(self, contexte):
		"""
		(A exécuter au sein d'une fonction marquée @bot.command)
		Effectue un nouveau comptage, update les données, affiche le message bilan

		mot-clé async nécessaire.
		await Compteur.update(contexte)  # utilisation d'une fonction asynchrone

		Fonctionnement :
		1) Chargement des anciens votes (stockés sous JSON)
		2) Chargement des nouveaux votes de la conversation
		3) Mise à jour des anciens votes & réécriture sous JSON
		4) Décompte des votes puis affichage du bilan dans la conversation
		"""
		
		answer_msg = ""  # Message à renvoyer en réponse de la commande

		# Vérification de la conversation :
		if self.id_conv is not None and contexte.channel.id != self.id_conv:
			# Mauvaise conversation
			if self.conv_name is not None:

				answer_msg = f"On n'est pas dans {self.conv_name}"
			else:
				answer_msg = "On n'est pas dans la bonne conversation"

		else:
			# Commande envoyée dans la bonne conversation

			# 1) Chargement des anciens votes
			date, anciens_votes = load_data(self.data_file)

			# 2) Chargement des nouveaux messages, plus récents que la dernière date
			# Si date=None, tous les messages sont lus
			messages = await contexte.channel.history(after=date).flatten()

			nouveaux_votes = {}
			"""
			# Pour les nouveaux votes :
			# messages contient tous les messages non lus du plus récent au plus vieux
			# Pour ne garder que le choix le plus récent, on vérifie pour chaque nouveau
			# message si l'id de l'auteur n'est pas déjà dans nouveaux_votes
			# Les nouveaux votes s'ajouteront ensuite aux anciens votes en remplaçant les
			# votes qui correspondent au même id.
			"""

			for message in messages:
				
				# JSON stocke les clés (ici les id) comme des str. Faute de meilleure solution, on utilise les
				# id sous forme de str
				id_auteur = str(message.author.id)

				if id_auteur not in nouveaux_votes:  # 1er nouveau vote de l'auteur
					
					# Récupération du keyword mentionné (s'il existe, sinon None):

					keyword = next_word(message.content, self.prefixes)

					if keyword is not None:

						# Comparaison du keywords mentionné avec ceux de la liste self.keywords
						index = keyword_index(keyword, self.keywords)

						if index != -1:  # index valide, correspondance trouvée

							nouveaux_votes[id_auteur] = index  # Ajout du vote


			# 3) nouveaux_votes est complet : on les ajoute à anciens_votes
			
			if anciens_votes is not None:
				votes = merge(anciens_votes, nouveaux_votes)  # anciens_votes est mis à jour
			else:
				votes = nouveaux_votes  # Cas du 1er appel de la fonction, fichier pas créé

			# Réécriture des données :

			date = messages[0].created_at  # Date du message le plus récent

			new_data = {}

			new_data['history'] = votes
			new_data['date'] = date.strftime(date_format)

			write_data(self.data_file, new_data)  # Ecriture


			# 4) Décompte des votes par sport :

			compte = count_occurences(votes, self.valeurs)

			# Génération du message :

			answer_msg += self.start_msg

			answer_msg += summary_msg(self.valeurs, compte, self.percent, self.total)

			answer_msg += self.end_msg
			# Fin


		await contexte.channel.send(answer_msg)  # Envoi du message dans la conversation


## Compteurs


compteur_sports = Compteur(
	prefixes=['1)', '1/', '1.', '1-'],
	valeurs=[
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
		"Crossfit",
	],
	keywords=[
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
		("crossfit"),
	],
	data_file="sports_data.json",
	id_conv=int(os.getenv("DEUX_SPORTS_PREFERES")),  # Id de deux-sports-preferes (via mode développeur discord)
	conv_name="deux-sports-preferes",
	start_msg=results_header,
	end_msg=warning_msg
)


msg_ultimate = "Nombre de gens intéressés par l'ultimate :\n\n"

compteur_ultimate = Compteur(
	prefixes=['*'],
	valeurs=["Ultimate"],
	keywords=[("ultimate")],
	data_file="ultimate_data.json",
	id_conv=int(os.getenv("DEUX_SPORTS_PREFERES")),
	conv_name="deux-sports-preferes",
	start_msg=msg_ultimate,
	end_msg=warning_msg,
	percent=False,
	total=False
)


## Le Bot


bot = commands.Bot(command_prefix="!")  # Commandes s'activent avec ! en début de message

# Savoir quand le bot est prêt
@bot.event
async def on_ready():
	print("le bot est prêt")


@bot.command(name="bonjour")  # commande !bonjour
async def dit_bonjour(contexte):
	await contexte.channel.send(f"Salut, {contexte.author.name}")


@bot.command(name="aurevoir")
async def ditAurevoir(contexte):

	await contexte.channel.send(f"Au revoir, {contexte.author.name}")


# Le bot se présente
@bot.command(name="bot,_présente_toi")
async def presenter(contexte):

	if contexte.channel.id == int(os.getenv("DEUX_SPORTS_PREFERES")):

		message = "Coucou,\nje suis un bot et je compte les 1ers choix des gens pour le sport.\n"
		message += "Merci de mettre '1)' puis votre premier choix, sinon j'arrive pas à lire.\n"
		message += "Je ne fonctionne que quand <@870249964561903617> me connecte\n"
		message += "Commandes : '!bot,_présente_toi', '!bonjour', , '!aurevoir', '!compte', '!ultimate'"
	else:
		message = "Coucou,\n"
		message += "Je suis un bot qui participe à deux-sports-preferes"

	await contexte.channel.send(message)


# Commandes de décompte : 
@bot.command(name="compte")
async def comptageSports(contexte):

	await compteur_sports.update(contexte)


@bot.command(name="ultimate")
async def volontairesUltimate(contexte):

	await compteur_ultimate.update(contexte)


# Lancement du bot
bot.run(os.getenv("TOKEN"))  # Token secret du bot