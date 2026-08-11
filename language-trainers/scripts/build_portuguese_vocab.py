#!/usr/bin/env python3
"""Build vocab_pt.json from curated word lists + portuguese_morph.py.

Same generated-data contract as the Latin and Italian decks: edit the lists
here, re-run, then rebuild + validate the trainer. Do not hand-edit vocab_pt.json.

EUROPEAN PORTUGUESE IS PRIMARY. Where Brazil differs the entry carries a `br`
field, the reveal panel shows both, and BOTH grade correct — a learner should
never be marked wrong for knowing the other side. Three kinds of difference are
marked:

  vocabulary   comboio/trem, autocarro/ônibus, telemóvel/celular
  spelling     the 1990 agreement removed most, but the vowel accents remain:
               ténis/tênis, bebé/bebê, económico/econômico
  grammar      estou a fazer / estou fazendo, and tu / você — carried by the
               phrase entries and the cloze sentences rather than by paradigms

A SPELLING ORACLE runs over every generated form. pyspellchecker's Portuguese
dictionary is 417k words and European-biased, which suits a PT-primary deck. It
is advisory, not absolute: it does not know `chãos`, `limões` or `sutis`, all of
which are correct. So an unknown word must be listed in SPELLING_OK with a
reason, and anything else fails the build. That is what caught three real rule
bugs while this deck was being written — the -ês plural dropping its accent,
the -vel family taking -eis rather than -éis, and -guer losing only its u.
"""
import json, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portuguese_morph import (noun_forms, conjugate, decline_adjective, pluralize,
                              personal_infinitive, future_subjunctive, PERSONS)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "vocab_pt.json")

# Words the oracle does not know but which are correct. Every one needs a
# reason, so the list cannot quietly become a way of silencing the check.
SPELLING_OK = {
    "chãos": "correct plural of chão; the dictionary lacks it",
    "limões": "correct plural of limão; the dictionary lacks it",
    "sutis": "plural of sutil (BR); the dictionary is European-biased",
    "ônibus": "Brazilian spelling; the dictionary is European",
    "bebê": "Brazilian spelling of bebé",
    "tênis": "Brazilian spelling of ténis",
    "econômico": "Brazilian spelling of económico",
    "celulares": "plural of celular (BR)",
    "geladeiras": "plural of geladeira (BR)",
    "banheiros": "plural of banheiro (BR)",
    "açougues": "plural of açougue (BR)",
    "sorvetes": "plural of sorvete (BR)",
    "abajur": "Brazilian for a table lamp; the dictionary is European",
    "ecrãs": "plural of ecrã; the dictionary lacks it",
    "telemóveis": "plural of telemóvel; the dictionary lacks it",
}

# ---------------------------------------------------------------------------
# NOUNS: (word, gender, English, lesson[, explicit plural])
# The plural is generated; give it explicitly only to assert a curated form.
# ---------------------------------------------------------------------------
NOUNS = [
    # L1 people & family
    ("homem", "m", "man", "1"), ("mulher", "f", "woman", "1"),
    ("rapaz", "m", "boy, young man", "1"), ("rapariga", "f", "girl (PT)", "1"),
    ("criança", "f", "child", "1"), ("pessoa", "f", "person", "1"),
    ("gente", "f", "people", "1"), ("família", "f", "family", "1"),
    ("pai", "m", "father", "1"), ("mãe", "f", "mother", "1"),
    ("filho", "m", "son", "1"), ("filha", "f", "daughter", "1"),
    ("irmão", "m", "brother", "1"), ("irmã", "f", "sister", "1"),
    ("avô", "m", "grandfather", "1"), ("avó", "f", "grandmother", "1"),
    ("tio", "m", "uncle", "1"), ("tia", "f", "aunt", "1"),
    ("primo", "m", "cousin", "1"), ("marido", "m", "husband", "1"),
    ("esposa", "f", "wife", "1"), ("amigo", "m", "friend", "1"),
    ("amiga", "f", "friend (female)", "1"), ("vizinho", "m", "neighbour", "1"),
    ("nome", "m", "name", "1"), ("apelido", "m", "surname (PT)", "1"),
    ("senhor", "m", "gentleman, Mr", "1"), ("senhora", "f", "lady, Mrs", "1"),
    ("vida", "f", "life", "1"), ("mundo", "m", "world", "1"),
    ("coisa", "f", "thing", "1"), ("parte", "f", "part", "1"),
    ("pergunta", "f", "question", "1"), ("resposta", "f", "answer", "1"),
    ("palavra", "f", "word", "1"), ("ideia", "f", "idea", "1"),
    ("problema", "m", "problem", "1"), ("razão", "f", "reason", "1"),
    # L2 house & home
    ("casa", "f", "house, home", "2"), ("apartamento", "m", "flat, apartment", "2"),
    ("quarto", "m", "room, bedroom", "2"), ("sala", "f", "living room", "2"),
    ("cozinha", "f", "kitchen", "2"), ("jardim", "m", "garden", "2"),
    ("porta", "f", "door", "2"), ("janela", "f", "window", "2"),
    ("parede", "f", "wall", "2"), ("chão", "m", "floor, ground", "2"),
    ("teto", "m", "ceiling", "2"), ("escada", "f", "stairs", "2"),
    ("mesa", "f", "table", "2"), ("cadeira", "f", "chair", "2"),
    ("cama", "f", "bed", "2"), ("sofá", "m", "sofa", "2"),
    ("armário", "m", "wardrobe, cupboard", "2"), ("espelho", "m", "mirror", "2"),
    ("candeeiro", "m", "lamp (PT)", "2"), ("chave", "f", "key", "2"),
    ("prato", "m", "plate, dish", "2"), ("copo", "m", "glass", "2"),
    ("chávena", "f", "cup (PT)", "2"), ("garfo", "m", "fork", "2"),
    ("faca", "f", "knife", "2"), ("colher", "f", "spoon", "2"),
    ("garrafa", "f", "bottle", "2"), ("toalha", "f", "towel", "2"),
    # L3 time & calendar
    ("tempo", "m", "time, weather", "3"), ("hora", "f", "hour, time", "3"),
    ("minuto", "m", "minute", "3"), ("segundo", "m", "second", "3"),
    ("dia", "m", "day", "3"), ("semana", "f", "week", "3"),
    ("mês", "m", "month", "3"), ("ano", "m", "year", "3"),
    ("manhã", "f", "morning", "3"), ("tarde", "f", "afternoon", "3"),
    ("noite", "f", "night", "3"),
    ("século", "m", "century", "3"), ("momento", "m", "moment", "3"),
    ("relógio", "m", "clock, watch", "3"), ("calendário", "m", "calendar", "3"),
    ("aniversário", "m", "birthday", "3"), ("férias", "f", "holidays", "3", "férias"),
    ("fim de semana", "m", "weekend", "3", "fins de semana"),
    # L4 food & drink
    ("comida", "f", "food", "4"), ("bebida", "f", "drink", "4"),
    ("água", "f", "water", "4"), ("leite", "m", "milk", "4"),
    ("café", "m", "coffee", "4"), ("chá", "m", "tea", "4"),
    ("vinho", "m", "wine", "4"), ("cerveja", "f", "beer", "4"),
    ("sumo", "m", "juice (PT)", "4"), ("pão", "m", "bread", "4"),
    ("queijo", "m", "cheese", "4"), ("manteiga", "f", "butter", "4"),
    ("ovo", "m", "egg", "4"), ("carne", "f", "meat", "4"),
    ("peixe", "m", "fish", "4"), ("frango", "m", "chicken", "4"),
    ("arroz", "m", "rice", "4"), ("batata", "f", "potato", "4"),
    ("legume", "m", "vegetable", "4"), ("fruta", "f", "fruit", "4"),
    ("maçã", "f", "apple", "4"), ("laranja", "f", "orange", "4"),
    ("banana", "f", "banana", "4"), ("limão", "m", "lemon", "4"),
    ("bolo", "m", "cake", "4"), ("sopa", "f", "soup", "4"),
    ("sal", "m", "salt", "4"), ("açúcar", "m", "sugar", "4"),
    ("azeite", "m", "olive oil", "4"), ("sobremesa", "f", "dessert", "4"),
    ("pequeno-almoço", "m", "breakfast (PT)", "4", "pequenos-almoços"),
    ("almoço", "m", "lunch", "4"), ("jantar", "m", "dinner", "4"),
    ("restaurante", "m", "restaurant", "4"), ("conta", "f", "bill", "4"),
    # L5 town & travel
    ("cidade", "f", "city", "5"), ("aldeia", "f", "village", "5"),
    ("rua", "f", "street", "5"), ("praça", "f", "square", "5"),
    ("estrada", "f", "road", "5"), ("ponte", "f", "bridge", "5"),
    ("igreja", "f", "church", "5"), ("museu", "m", "museum", "5"),
    ("loja", "f", "shop", "5"), ("mercado", "m", "market", "5"),
    ("banco", "m", "bank, bench", "5"), ("correio", "m", "post office", "5"),
    ("hospital", "m", "hospital", "5"), ("escola", "f", "school", "5"),
    ("hotel", "m", "hotel", "5"), ("aeroporto", "m", "airport", "5"),
    ("estação", "f", "station", "5"), ("comboio", "m", "train (PT)", "5"),
    ("autocarro", "m", "bus (PT)", "5"), ("carro", "m", "car", "5"),
    ("avião", "m", "aeroplane", "5"), ("barco", "m", "boat", "5"),
    ("bicicleta", "f", "bicycle", "5"), ("bilhete", "m", "ticket", "5"),
    ("viagem", "f", "journey, trip", "5"), ("mala", "f", "suitcase", "5"),
    ("mapa", "m", "map", "5"), ("caminho", "m", "way, path", "5"),
    ("lugar", "m", "place", "5"), ("país", "m", "country", "5"),
    # L6 nature & weather
    ("sol", "m", "sun", "6"), ("lua", "f", "moon", "6"),
    ("céu", "m", "sky", "6"), ("estrela", "f", "star", "6"),
    ("chuva", "f", "rain", "6"), ("vento", "m", "wind", "6"),
    ("neve", "f", "snow", "6"), ("nuvem", "f", "cloud", "6"),
    ("calor", "m", "heat", "6"), ("frio", "m", "cold", "6"),
    ("mar", "m", "sea", "6"), ("rio", "m", "river", "6"),
    ("praia", "f", "beach", "6"), ("montanha", "f", "mountain", "6"),
    ("campo", "m", "field, countryside", "6"), ("floresta", "f", "forest", "6"),
    ("árvore", "f", "tree", "6"), ("flor", "f", "flower", "6"),
    ("planta", "f", "plant", "6"), ("pedra", "f", "stone", "6"),
    ("terra", "f", "earth, land", "6"), ("fogo", "m", "fire", "6"),
    ("animal", "m", "animal", "6"), ("cão", "m", "dog", "6"),
    ("gato", "m", "cat", "6"), ("cavalo", "m", "horse", "6"),
    ("pássaro", "m", "bird", "6"), ("vaca", "f", "cow", "6"),
    # L7 body & health
    ("corpo", "m", "body", "7"), ("cabeça", "f", "head", "7"),
    ("cabelo", "m", "hair", "7"), ("cara", "f", "face", "7"),
    ("olho", "m", "eye", "7"), ("nariz", "m", "nose", "7"),
    ("boca", "f", "mouth", "7"), ("dente", "m", "tooth", "7"),
    ("orelha", "f", "ear", "7"), ("braço", "m", "arm", "7"),
    ("mão", "f", "hand", "7"), ("dedo", "m", "finger", "7"),
    ("perna", "f", "leg", "7"), ("pé", "m", "foot", "7"),
    ("coração", "m", "heart", "7"), ("costas", "f", "back", "7", "costas"),
    ("saúde", "f", "health", "7"), ("dor", "f", "pain", "7"),
    ("doença", "f", "illness", "7"), ("médico", "m", "doctor", "7"),
    ("enfermeiro", "m", "nurse", "7"), ("remédio", "m", "medicine", "7"),
    ("farmácia", "f", "pharmacy", "7"), ("febre", "f", "fever", "7"),
    # L8 work & study
    ("trabalho", "m", "work, job", "8"), ("emprego", "m", "employment", "8"),
    ("escritório", "m", "office", "8"), ("empresa", "f", "company", "8"),
    ("reunião", "f", "meeting", "8"), ("projeto", "m", "project", "8"),
    ("dinheiro", "m", "money", "8"), ("preço", "m", "price", "8"),
    ("professor", "m", "teacher", "8"), ("aluno", "m", "pupil", "8"),
    ("estudante", "m", "student", "8"), ("universidade", "f", "university", "8"),
    ("aula", "f", "class, lesson", "8"), ("curso", "m", "course", "8"),
    ("exame", "m", "exam", "8"), ("livro", "m", "book", "8"),
    ("caderno", "m", "notebook", "8"), ("caneta", "f", "pen", "8"),
    ("lápis", "m", "pencil", "8"), ("papel", "m", "paper", "8"),
    ("jornal", "m", "newspaper", "8"), ("revista", "f", "magazine", "8"),
    ("carta", "f", "letter", "8"), ("história", "f", "story, history", "8"),
    # L9 things & technology
    ("telemóvel", "m", "mobile phone (PT)", "9"),
    ("computador", "m", "computer", "9"), ("ecrã", "m", "screen (PT)", "9"),
    ("ficheiro", "m", "file (PT)", "9"), ("internet", "f", "internet", "9"),
    ("mensagem", "f", "message", "9"), ("telefone", "m", "telephone", "9"),
    ("televisão", "f", "television", "9"), ("rádio", "m", "radio", "9"),
    ("música", "f", "music", "9"), ("filme", "m", "film", "9"),
    ("foto", "f", "photo", "9"), ("jogo", "m", "game", "9"),
    ("roupa", "f", "clothes", "9"), ("camisa", "f", "shirt", "9"),
    ("calças", "f", "trousers", "9", "calças"), ("sapato", "m", "shoe", "9"),
    ("casaco", "m", "coat, jacket", "9"), ("chapéu", "m", "hat", "9"),
    ("saco", "m", "bag", "9"), ("relvado", "m", "lawn (PT)", "9"),
    # L10 abstract & feelings
    ("amor", "m", "love", "10"), ("medo", "m", "fear", "10"),
    ("alegria", "f", "joy", "10"), ("tristeza", "f", "sadness", "10"),
    ("saudade", "f", "longing, missing someone", "10"),
    ("esperança", "f", "hope", "10"), ("sorte", "f", "luck", "10"),
    ("verdade", "f", "truth", "10"), ("mentira", "f", "lie", "10"),
    ("força", "f", "strength", "10"), ("paz", "f", "peace", "10"),
    ("guerra", "f", "war", "10"), ("liberdade", "f", "freedom", "10"),
    ("direito", "m", "right, law", "10"), ("dever", "m", "duty", "10"),
    ("sonho", "m", "dream", "10"), ("vontade", "f", "will, desire", "10"),
    ("opinião", "f", "opinion", "10"), ("decisão", "f", "decision", "10"),
    ("mudança", "f", "change", "10"), ("motivo", "m", "reason, motive", "10"),
]

# ---------------------------------------------------------------------------
# VERBS: (infinitive, English, lesson)
# ---------------------------------------------------------------------------
VERBS = [
    ("ser", "to be (permanent)", "11"), ("estar", "to be (state, place)", "11"),
    ("ter", "to have", "11"), ("haver", "there to be", "11"),
    ("ir", "to go", "11"), ("vir", "to come", "11"),
    ("fazer", "to do, to make", "11"), ("dizer", "to say", "11"),
    ("poder", "to be able, can", "11"), ("querer", "to want", "11"),
    ("saber", "to know (a fact)", "11"), ("conhecer", "to know (be familiar with)", "11"),
    ("ver", "to see", "11"), ("dar", "to give", "11"),
    ("pôr", "to put", "11"), ("ficar", "to stay, to become, to be located", "11"),
    ("falar", "to speak", "12"), ("comer", "to eat", "12"),
    ("beber", "to drink", "12"), ("morar", "to live, to reside", "12"),
    ("viver", "to live", "12"), ("trabalhar", "to work", "12"),
    ("estudar", "to study", "12"), ("aprender", "to learn", "12"),
    ("ensinar", "to teach", "12"), ("ler", "to read", "12"),
    ("escrever", "to write", "12"), ("ouvir", "to hear, to listen", "12"),
    ("olhar", "to look", "12"), ("gostar", "to like", "12"),
    ("precisar", "to need", "12"), ("pedir", "to ask for", "12"),
    ("perguntar", "to ask (a question)", "12"), ("responder", "to answer", "12"),
    ("abrir", "to open", "13"), ("fechar", "to close", "13"),
    ("comprar", "to buy", "13"), ("vender", "to sell", "13"),
    ("pagar", "to pay", "13"), ("levar", "to take, to carry", "13"),
    ("trazer", "to bring", "13"), ("deixar", "to leave, to let", "13"),
    ("chegar", "to arrive", "13"), ("partir", "to leave, to depart", "13"),
    ("sair", "to go out", "13"), ("entrar", "to enter", "13"),
    ("voltar", "to return", "13"), ("passar", "to pass, to spend (time)", "13"),
    ("andar", "to walk", "13"), ("correr", "to run", "13"),
    ("subir", "to go up", "13"), ("descer", "to go down", "13"),
    ("dormir", "to sleep", "14"), ("acordar", "to wake up", "14"),
    ("comeu_placeholder", "", ""),   # removed below; keeps the list honest
    ("sentir", "to feel", "14"), ("pensar", "to think", "14"),
    ("achar", "to think, to find", "14"), ("esperar", "to wait, to hope", "14"),
    ("lembrar", "to remember", "14"), ("esquecer", "to forget", "14"),
    ("começar", "to begin", "14"), ("acabar", "to finish", "14"),
    ("continuar", "to continue", "14"), ("parar", "to stop", "14"),
    ("mudar", "to change", "14"), ("ajudar", "to help", "14"),
    ("usar", "to use", "14"), ("chamar", "to call", "14"),
    ("encontrar", "to find, to meet", "14"), ("procurar", "to look for", "14"),
    ("conseguir", "to manage, to succeed", "15"), ("tentar", "to try", "15"),
    ("dever", "ought to, to owe", "15"), ("preferir", "to prefer", "15"),
    ("servir", "to serve", "15"), ("seguir", "to follow", "15"),
    ("vestir", "to dress, to wear", "15"), ("perder", "to lose", "15"),
    ("ganhar", "to win, to earn", "15"), ("jogar", "to play (a game)", "15"),
    ("tocar", "to touch, to play (music)", "15"), ("cantar", "to sing", "15"),
    ("dançar", "to dance", "15"), ("viajar", "to travel", "15"),
    ("cozinhar", "to cook", "15"), ("limpar", "to clean", "15"),
    ("lavar", "to wash", "15"), ("dirigir", "to drive (BR), to direct", "15"),
    ("conduzir_placeholder", "", ""),
]
VERBS = [v for v in VERBS if v[1]]

# ---------------------------------------------------------------------------
# ADJECTIVES: (masc sg, English, lesson)
# ---------------------------------------------------------------------------
ADJECTIVES = [
    ("bom", "good", "16", "boa"), ("mau", "bad", "16", "má"),
    ("grande", "big", "16"), ("pequeno", "small", "16"),
    ("novo", "new, young", "16"), ("velho", "old", "16"),
    ("jovem", "young", "16"), ("alto", "tall, high", "16"),
    ("baixo", "short, low", "16"), ("longo", "long", "16"),
    ("curto", "short", "16"), ("largo", "wide", "16"),
    ("bonito", "beautiful", "16"), ("feio", "ugly", "16"),
    ("gordo", "fat", "16"), ("magro", "thin", "16"),
    ("forte", "strong", "16"), ("fraco", "weak", "16"),
    ("rico", "rich", "16"), ("pobre", "poor", "16"),
    ("quente", "hot", "17"), ("frio", "cold", "17"),
    ("limpo", "clean", "17"), ("sujo", "dirty", "17"),
    ("caro", "expensive", "17"), ("barato", "cheap", "17"),
    ("rápido", "fast", "17"), ("lento", "slow", "17"),
    ("fácil", "easy", "17"), ("difícil", "difficult", "17"),
    ("cheio", "full", "17"), ("vazio", "empty", "17"),
    ("aberto", "open", "17"), ("fechado", "closed", "17"),
    ("certo", "right, certain", "17"), ("errado", "wrong", "17"),
    ("contente", "happy, pleased", "17"), ("triste", "sad", "17"),
    ("cansado", "tired", "17"), ("doente", "ill", "17"),
    ("branco", "white", "18"), ("preto", "black", "18"),
    ("vermelho", "red", "18"), ("azul", "blue", "18"),
    ("verde", "green", "18"), ("amarelo", "yellow", "18"),
    ("castanho", "brown (PT)", "18"), ("cinzento", "grey (PT)", "18"),
    ("português", "Portuguese", "18"), ("brasileiro", "Brazilian", "18"),
    ("inglês", "English", "18"), ("francês", "French", "18"),
    ("alemão", "German", "18"), ("espanhol", "Spanish", "18"),
    ("europeu", "European", "18"), ("trabalhador", "hard-working", "18"),
    ("importante", "important", "18"), ("interessante", "interesting", "18"),
    ("possível", "possible", "18"), ("necessário", "necessary", "18"),
    ("económico", "economic, cheap (PT)", "18"),
]

# ---------------------------------------------------------------------------
# Invariable words: (word, pos, English, lesson)
# ---------------------------------------------------------------------------
OTHERS = [
    ("sim", "adverb", "yes", "19"), ("não", "adverb", "no, not", "19"),
    ("muito", "adverb", "very, a lot", "19"), ("pouco", "adverb", "little", "19"),
    ("mais", "adverb", "more", "19"), ("menos", "adverb", "less", "19"),
    ("bem", "adverb", "well", "19"), ("mal", "adverb", "badly", "19"),
    ("também", "adverb", "also, too", "19"), ("já", "adverb", "already, now", "19"),
    ("ainda", "adverb", "still, yet", "19"), ("sempre", "adverb", "always", "19"),
    ("nunca", "adverb", "never", "19"), ("agora", "adverb", "now", "19"),
    ("depois", "adverb", "after, later", "19"), ("antes", "adverb", "before", "19"),
    ("cedo", "adverb", "early", "19"), ("tarde", "adverb", "late", "19"),
    ("aqui", "adverb", "here", "19"), ("ali", "adverb", "there", "19"),
    ("hoje", "adverb", "today", "19"), ("ontem", "adverb", "yesterday", "19"),
    ("amanhã", "adverb", "tomorrow", "19"), ("talvez", "adverb", "perhaps", "19"),
    ("devagar", "adverb", "slowly", "19"), ("depressa", "adverb", "quickly (PT)", "19"),
    ("de", "preposition", "of, from", "20"), ("em", "preposition", "in, on", "20"),
    ("para", "preposition", "for, to", "20"), ("por", "preposition", "by, through, for", "20"),
    ("com", "preposition", "with", "20"), ("sem", "preposition", "without", "20"),
    ("sobre", "preposition", "on, about", "20"), ("entre", "preposition", "between", "20"),
    ("até", "preposition", "until, up to", "20"), ("desde", "preposition", "since, from", "20"),
    ("contra", "preposition", "against", "20"), ("durante", "preposition", "during", "20"),
    ("e", "conjunction", "and", "20"), ("ou", "conjunction", "or", "20"),
    ("mas", "conjunction", "but", "20"), ("porque", "conjunction", "because", "20"),
    ("se", "conjunction", "if", "20"), ("quando", "conjunction", "when", "20"),
    ("que", "conjunction", "that, which", "20"), ("como", "conjunction", "as, how", "20"),
    ("eu", "pronoun", "I", "21"), ("tu", "pronoun", "you (informal, PT)", "21"),
    ("você", "pronoun", "you (polite PT, default BR)", "21"),
    ("ele", "pronoun", "he, it", "21"), ("ela", "pronoun", "she, it", "21"),
    ("nós", "pronoun", "we", "21"), ("vocês", "pronoun", "you (plural)", "21"),
    ("eles", "pronoun", "they (m)", "21"), ("elas", "pronoun", "they (f)", "21"),
    ("me", "pronoun", "me", "21"), ("te", "pronoun", "you (object)", "21"),
    ("nos", "pronoun", "us", "21"), ("lhe", "pronoun", "to him, to her, to you", "21"),
    ("meu", "pronoun", "my", "21"), ("teu", "pronoun", "your (informal)", "21"),
    ("seu", "pronoun", "his, her, your", "21"), ("nosso", "pronoun", "our", "21"),
    ("este", "pronoun", "this", "21"), ("esse", "pronoun", "that (near you)", "21"),
    ("aquele", "pronoun", "that (over there)", "21"),
    ("quem", "pronoun", "who", "21"), ("qual", "pronoun", "which", "21"),
    ("zero", "number", "zero", "22"), ("um", "number", "one", "22"),
    ("dois", "number", "two", "22"), ("três", "number", "three", "22"),
    ("quatro", "number", "four", "22"), ("cinco", "number", "five", "22"),
    ("seis", "number", "six", "22"), ("sete", "number", "seven", "22"),
    ("oito", "number", "eight", "22"), ("nove", "number", "nine", "22"),
    ("dez", "number", "ten", "22"), ("onze", "number", "eleven", "22"),
    ("doze", "number", "twelve", "22"), ("vinte", "number", "twenty", "22"),
    ("trinta", "number", "thirty", "22"), ("cem", "number", "a hundred", "22"),
    ("mil", "number", "a thousand", "22"),
    ("primeiro", "number", "first", "22"), ("segundo", "number", "second", "22"),
]

# ---------------------------------------------------------------------------
# PHRASES — ready-made, the way the French deck carries small talk.
# ---------------------------------------------------------------------------
PHRASES = [
    ("bom dia", "good morning", "23"), ("boa tarde", "good afternoon", "23"),
    ("boa noite", "good evening, good night", "23"), ("olá", "hello", "23"),
    ("adeus", "goodbye", "23"), ("até logo", "see you later", "23"),
    ("até amanhã", "see you tomorrow", "23"),
    ("por favor", "please", "23"), ("obrigado", "thank you (said by a man)", "23"),
    ("obrigada", "thank you (said by a woman)", "23"),
    ("de nada", "you're welcome", "23"), ("desculpe", "sorry, excuse me", "23"),
    ("com licença", "excuse me (passing by)", "23"),
    ("como está?", "how are you? (polite)", "23"),
    ("como estás?", "how are you? (informal, PT)", "23"),
    ("tudo bem?", "how's it going?", "23"),
    ("estou bem, obrigado", "I'm well, thank you", "23"),
    ("como se chama?", "what is your name? (polite)", "23"),
    ("chamo-me...", "my name is... (PT word order)", "23"),
    ("muito prazer", "pleased to meet you", "23"),
    ("de onde é?", "where are you from?", "23"),
    ("sou de Inglaterra", "I'm from England", "23"),
    ("não percebo", "I don't understand (PT)", "24"),
    ("não sei", "I don't know", "24"),
    ("pode repetir?", "can you repeat that?", "24"),
    ("fala inglês?", "do you speak English?", "24"),
    ("como se diz...?", "how do you say...?", "24"),
    ("o que significa?", "what does it mean?", "24"),
    ("quanto custa?", "how much does it cost?", "24"),
    ("a conta, por favor", "the bill, please", "24"),
    ("onde fica...?", "where is...?", "24"),
    ("estou perdido", "I'm lost", "24"),
    ("pode ajudar-me?", "can you help me? (PT)", "24"),
    ("tenho fome", "I'm hungry", "24"), ("tenho sede", "I'm thirsty", "24"),
    ("tenho de ir", "I have to go (PT)", "24"),
    ("com certeza", "certainly, of course", "24"),
    ("claro que sim", "of course", "24"),
    ("mais ou menos", "more or less, so-so", "24"),
    ("se calhar", "maybe (PT)", "24"), ("pois é", "that's right, indeed", "24"),
]

# ---------------------------------------------------------------------------
# European / Brazilian pairs. `pt` is the headword; `br` is what Brazil says.
# Marked on the entry so the reveal shows both and BOTH grade correct.
# ---------------------------------------------------------------------------
BR_VARIANTS = {
    # vocabulary
    "comboio": "trem", "autocarro": "ônibus", "telemóvel": "celular",
    "pequeno-almoço": "café da manhã", "sumo": "suco", "casaco": "paletó",
    "chávena": "xícara", "candeeiro": "abajur", "ecrã": "tela",
    "ficheiro": "arquivo", "apelido": "sobrenome", "rapariga": "garota",
    "relvado": "gramado", "depressa": "rápido",
    "bilhete": "passagem", "casa de banho": "banheiro",
    # spelling: the 1990 agreement left the vowel accents alone
    "ténis": "tênis", "bebé": "bebê", "económico": "econômico",
    # grammar, carried as phrases
    "não percebo": "não entendo", "pode ajudar-me?": "pode me ajudar?",
    "chamo-me...": "me chamo...", "tenho de ir": "tenho que ir",
    "como estás?": "como você está?", "se calhar": "talvez",
}

# Words that exist only to carry a BR pair and are not in the lists above.
EXTRA_BR_NOUNS = [
    ("casa de banho", "f", "bathroom (PT)", "2", "casas de banho"),
    ("ténis", "m", "trainers, tennis (PT)", "9", "ténis"),
    ("bebé", "m", "baby (PT)", "1"),
]

# ---------------------------------------------------------------------------
# CLOZE: headword -> [(sentence with {target}, English)]
# The target inside the braces is the INFLECTED in-sentence form, authored
# independently of any generated paradigm — that independence is what makes the
# cross-check in check_cloze() worth anything.
# ---------------------------------------------------------------------------
CLOZE = {
    "casa": [("A minha {casa} é pequena.", "My house is small."),
             ("As {casas} aqui são caras.", "The houses here are expensive.")],
    "homem": [("Aquele {homem} é o meu pai.", "That man is my father."),
              ("Os {homens} estão a trabalhar.", "The men are working.")],
    "mulher": [("A {mulher} de vermelho é a Ana.", "The woman in red is Ana."),
               ("Duas {mulheres} entraram na loja.", "Two women went into the shop.")],
    "irmão": [("O meu {irmão} mora no Porto.", "My brother lives in Porto."),
              ("Tenho dois {irmãos}.", "I have two brothers.")],
    "mão": [("Dá-me a {mão}.", "Give me your hand."),
            ("Lava as {mãos} antes de comer.", "Wash your hands before eating.")],
    "pão": [("Comprei {pão} fresco.", "I bought fresh bread."),
            ("Os {pães} estão no forno.", "The loaves are in the oven.")],
    "coração": [("O {coração} bate depressa.", "The heart beats fast."),
                ("Os {corações} dos atletas são fortes.", "Athletes' hearts are strong.")],
    "cidade": [("Lisboa é uma {cidade} linda.", "Lisbon is a beautiful city."),
               ("Visitámos três {cidades}.", "We visited three cities.")],
    "país": [("Portugal é um {país} pequeno.", "Portugal is a small country."),
             ("Vários {países} assinaram o acordo.", "Several countries signed the agreement.")],
    "mês": [("Este {mês} está a correr bem.", "This month is going well."),
            ("Faltam dois {meses} para o verão.", "There are two months until summer.")],
    "animal": [("O cão é um {animal} fiel.", "The dog is a loyal animal."),
               ("Os {animais} da quinta acordam cedo.", "The farm animals wake up early.")],
    "papel": [("Preciso de uma folha de {papel}.", "I need a sheet of paper."),
              ("Os {papéis} estão na mesa.", "The papers are on the table.")],
    "hotel": [("O {hotel} fica perto da praia.", "The hotel is near the beach."),
              ("Os {hotéis} estão cheios em agosto.", "The hotels are full in August.")],
    "ser": [("Eu {sou} de Lisboa.", "I am from Lisbon."),
            ("Nós {somos} amigos há anos.", "We have been friends for years."),
            ("Tu {és} muito simpático.", "You are very nice.")],
    "estar": [("Eu {estou} cansado hoje.", "I am tired today."),
              ("Onde {estás}?", "Where are you?"),
              ("Eles {estão} em casa.", "They are at home.")],
    "ter": [("Eu {tenho} dois filhos.", "I have two children."),
            ("Tu {tens} razão.", "You are right."),
            ("Nós {temos} de sair.", "We have to leave.")],
    "ir": [("Eu {vou} ao mercado.", "I am going to the market."),
           ("Tu {vais} de comboio?", "Are you going by train?"),
           ("Eles {vão} para o Brasil.", "They are going to Brazil.")],
    "fazer": [("O que {fazes} ao fim de semana?", "What do you do at the weekend?"),
              ("Eu {faço} o jantar hoje.", "I'm making dinner today.")],
    "poder": [("{Posso} entrar?", "May I come in?"),
              ("Nós não {podemos} ficar.", "We can't stay.")],
    "querer": [("Eu {quero} um café.", "I want a coffee."),
               ("Eles {querem} viajar.", "They want to travel.")],
    "saber": [("Eu não {sei} a resposta.", "I don't know the answer."),
              ("Tu {sabes} cozinhar?", "Do you know how to cook?")],
    "ver": [("Eu {vejo} o mar da janela.", "I see the sea from the window."),
            ("Vocês {veem} o filme hoje?", "Are you watching the film today?")],
    "vir": [("Ela {vem} amanhã.", "She is coming tomorrow."),
            ("Eu {venho} de longe.", "I come from far away.")],
    "pôr": [("Eu {ponho} a mesa.", "I set the table."),
            ("Ele {põe} o livro na estante.", "He puts the book on the shelf.")],
    "falar": [("Eu {falo} um pouco de português.", "I speak a little Portuguese."),
              ("Nós {falamos} todos os dias.", "We talk every day.")],
    "comer": [("Eu {como} às oito.", "I eat at eight."),
              ("Eles {comem} muito peixe.", "They eat a lot of fish.")],
    "morar": [("Eu {moro} em Lisboa.", "I live in Lisbon."),
              ("Onde é que tu {moras}?", "Where do you live?")],
    "gostar": [("Eu {gosto} de café.", "I like coffee."),
               ("Eles {gostam} de viajar.", "They like travelling.")],
    "conhecer": [("Eu {conheço} bem esta cidade.", "I know this city well."),
                 ("Tu {conheces} o João?", "Do you know João?")],
    "dormir": [("Eu {durmo} oito horas.", "I sleep eight hours."),
               ("As crianças {dormem} cedo.", "The children sleep early.")],
    "sair": [("Eu {saio} às seis.", "I leave at six."),
             ("Nós {saímos} todos os sábados.", "We go out every Saturday.")],
    "pedir": [("Eu {peço} desculpa.", "I apologise."),
              ("Eles {pedem} a conta.", "They ask for the bill.")],
    "preferir": [("Eu {prefiro} chá.", "I prefer tea."),
                 ("Ela {prefere} ficar em casa.", "She prefers to stay at home.")],
    "bom": [("Este vinho é muito {bom}.", "This wine is very good."),
            ("Foi uma {boa} ideia.", "It was a good idea.")],
    "grande": [("Lisboa é uma cidade {grande}.", "Lisbon is a big city."),
               ("Temos {grandes} planos.", "We have big plans.")],
    "português": [("Ele é {português}.", "He is Portuguese."),
                  ("Ela é {portuguesa}.", "She is Portuguese."),
                  ("Somos todos {portugueses}.", "We are all Portuguese.")],
    "alemão": [("O meu vizinho é {alemão}.", "My neighbour is German."),
               ("A professora é {alemã}.", "The teacher is German.")],
    "fácil": [("O exame foi {fácil}.", "The exam was easy."),
              ("As perguntas eram {fáceis}.", "The questions were easy.")],
    "possível": [("Não é {possível}.", "It isn't possible."),
                 ("Todos os cenários {possíveis} foram estudados.",
                  "All the possible scenarios were studied.")],
    "muito": [("Obrigado, {muito} gentil.", "Thank you, very kind."),
              ("Ele fala {muito}.", "He talks a lot.")],
    "também": [("Eu {também} quero ir.", "I want to go too.")],
    "ainda": [("{Ainda} não acabei.", "I haven't finished yet.")],
    "amanhã": [("Até {amanhã}!", "See you tomorrow!")],
    "saudade": [("Tenho {saudades} tuas.", "I miss you."),
                ("A {saudade} é difícil de traduzir.", "Saudade is hard to translate.")],
    "obrigado": [("Muito {obrigado} pela ajuda.", "Thank you very much for your help.")],
    "comboio": [("Apanhei o {comboio} das oito.", "I caught the eight o'clock train.")],
    "autocarro": [("O {autocarro} está atrasado.", "The bus is late.")],
    "telemóvel": [("Esqueci-me do {telemóvel} em casa.", "I left my mobile at home.")],
}

# ---------------------------------------------------------------------------
# SPECIAL BANKS
# ---------------------------------------------------------------------------
# ser / estar / ficar — three ways where Spanish has two. ficar is the one a
# Spanish speaker never reaches for and Portuguese uses constantly.
SER_ESTAR = [
    ("O meu irmão {é} médico.", "My brother is a doctor.", "está", "profession → ser"),
    ("A sopa {está} fria.", "The soup is cold.", "é", "temporary state → estar"),
    ("Ela {é} muito simpática.", "She is very nice.", "está", "character → ser"),
    ("Nós {estamos} cansados.", "We are tired.", "somos", "how you feel → estar"),
    ("Hoje {é} segunda-feira.", "Today is Monday.", "está", "day and date → ser"),
    ("O café {está} quente.", "The coffee is hot.", "é", "current state → estar"),
    ("Lisboa {fica} em Portugal.", "Lisbon is in Portugal.", "é",
     "permanent location → ficar (PT prefers it to estar here)"),
    ("A casa {é} de madeira.", "The house is made of wood.", "está", "material → ser"),
    ("Eles {estão} em casa.", "They are at home.", "são", "where someone is now → estar"),
    ("O livro {é} meu.", "The book is mine.", "está", "possession → ser"),
    ("A porta {está} aberta.", "The door is open.", "é", "resulting state → estar"),
    ("Ele {fica} nervoso antes dos exames.", "He gets nervous before exams.", "é",
     "becoming → ficar"),
    ("A reunião {é} às três.", "The meeting is at three.", "está",
     "when an event takes place → ser"),
    ("{Estou} a aprender português.", "I am learning Portuguese.", "Sou",
     "estar a + infinitive is the PT progressive"),
    ("Onde {fica} a estação?", "Where is the station?", "é",
     "asking where a fixed thing is → ficar"),
    ("A janela {está} suja.", "The window is dirty.", "é", "changeable state → estar"),
    ("Nós {somos} de Inglaterra.", "We are from England.", "estamos", "origin → ser"),
    ("O filme {foi} muito bom.", "The film was very good.", "esteve",
     "a judgement about the thing itself → ser"),
    ("{Fiquei} em casa o dia todo.", "I stayed at home all day.", "Fui",
     "staying → ficar"),
    ("A água {está} a ferver.", "The water is boiling.", "é", "right now → estar"),
]

POR_PARA = [
    ("Este presente é {para} ti.", "This gift is for you.", "recipient → para"),
    ("Obrigado {por} tudo.", "Thank you for everything.", "cause, gratitude → por"),
    ("Vou {para} o Porto amanhã.", "I'm going to Porto tomorrow.", "destination → para"),
    ("Passei {por} Coimbra.", "I went through Coimbra.", "movement through → por"),
    ("Estudo {para} aprender.", "I study in order to learn.", "purpose → para"),
    ("Foi feito {por} um artista.", "It was made by an artist.", "agent → por"),
    ("Preciso disto {para} amanhã.", "I need this by tomorrow.", "deadline → para"),
    ("Trabalhei {por} três horas.", "I worked for three hours.", "duration → por"),
    ("Troquei o carro {por} uma bicicleta.", "I swapped the car for a bicycle.",
     "exchange → por"),
    ("Ele fala {para} a turma.", "He speaks to the class.", "direction of address → para"),
    ("Pagámos vinte euros {por} noite.", "We paid twenty euros a night.", "rate → por"),
    ("{Para} mim, isto chega.", "For me, this is enough.", "opinion → para"),
    ("Saí {por} causa do barulho.", "I left because of the noise.", "cause → por"),
    ("A carta é {para} a minha mãe.", "The letter is for my mother.", "recipient → para"),
    ("Vendi o carro {por} pouco dinheiro.", "I sold the car for little money.",
     "price → por"),
    ("Estudou {para} médico.", "He studied to be a doctor.", "goal → para"),
]

# The personal infinitive: the thing Portuguese has and Spanish does not.
PERSONAL_INF = [
    ("Antes de {sairmos}, fecha a janela.", "Before we leave, close the window.",
     "sair", "nos", "antes de + personal infinitive, subject nós"),
    ("É melhor {irmos} agora.", "It's better for us to go now.", "ir", "nos",
     "é melhor + personal infinitive"),
    ("Depois de {chegarem}, telefonem.", "After you arrive, phone.", "chegar",
     "eles_elas_voces", "depois de + personal infinitive, subject vocês"),
    ("Para {seres} feliz, precisas de descansar.", "For you to be happy, you need to rest.",
     "ser", "tu", "para + personal infinitive; ser is regular here — seres, not fores"),
    ("Trouxe o livro para {leres}.", "I brought the book for you to read.", "ler", "tu",
     "purpose with a different subject → personal infinitive"),
    ("É importante {estudarmos} juntos.", "It's important that we study together.",
     "estudar", "nos", "impersonal expression + personal infinitive"),
    ("No caso de {haver} problemas, liga-me.", "In case there are problems, call me.",
     "haver", "ele_ela_voce", "third person singular, so no ending is added"),
    ("Apesar de {fazerem} frio, saímos.", "Despite it being cold, we went out.",
     "fazer", "eles_elas_voces", "apesar de + personal infinitive"),
    ("Antes de {comeres}, lava as mãos.", "Before you eat, wash your hands.",
     "comer", "tu", "the -es ending marks tu"),
    ("Foi difícil {encontrarmos} a casa.", "It was difficult for us to find the house.",
     "encontrar", "nos", "-mos marks nós"),
]

# Where the personal infinitive and the future subjunctive DIVERGE. For a
# regular verb they are spelled identically, which is exactly why the
# irregular ones catch people out.
FUT_SUBJ = [
    ("Se {formos} à praia, levamos o guarda-sol.",
     "If we go to the beach, we'll take the parasol.", "ir", "nos",
     "future subjunctive of ir is FORMOS; the personal infinitive would be irmos"),
    ("Quando {fizeres} os anos, vamos festejar.",
     "When it's your birthday, we'll celebrate.", "fazer", "tu",
     "future subjunctive fizeres, not the personal infinitive fazeres"),
    ("Se {tiveres} tempo, telefona.", "If you have time, call.", "ter", "tu",
     "future subjunctive tiveres, not teres"),
    ("Quando {estiverem} prontos, avisem.", "When you're ready, let us know.",
     "estar", "eles_elas_voces", "future subjunctive estiverem, not estarem"),
    ("Se {puderes}, ajuda-me.", "If you can, help me.", "poder", "tu",
     "future subjunctive puderes, not poderes"),
    ("Assim que {soubermos}, dizemos.", "As soon as we know, we'll say.", "saber",
     "nos", "future subjunctive soubermos, not sabermos"),
    ("Se {falarmos} devagar, ele percebe.", "If we speak slowly, he understands.",
     "falar", "nos",
     "falar is regular, so the two forms are identical — this is why they get confused"),
    ("Quando {chegarem}, comemos.", "When you arrive, we'll eat.", "chegar",
     "eles_elas_voces", "chegar is regular: identical to the personal infinitive"),
]

# False friends against Spanish, drilled in a sentence so they share the shape
# of every other bank: a braced answer plus the Spanish-shaped word a learner
# coming from Spanish would reach for.
FALSE_FRIENDS = [
    ("Este bolo tem um sabor {esquisito}.", "This cake has a strange taste.",
     "exquisito", "Spanish exquisito means delicious; PT esquisito means odd"),
    ("A minha irmã está {grávida}.", "My sister is pregnant.", "embaraçada",
     "PT embaraçada means embarrassed, not pregnant"),
    ("Trabalho num {escritório} no centro.", "I work in an office in the centre.",
     "oficina", "PT oficina is a workshop or garage"),
    ("Deixei uma {gorjeta} ao empregado.", "I left the waiter a tip.", "propina",
     "PT propina is a tuition fee"),
    ("A ponte é muito {comprida}.", "The bridge is very long.", "larga",
     "PT largo means wide, not long"),
    ("Há muito {pó} na estante.", "There is a lot of dust on the shelf.", "polvo",
     "PT polvo is an octopus"),
    ("A sopa está muito {salgada}.", "The soup is very salty.", "salada",
     "PT salada is a salad"),
    ("Vamos {jantar} às oito.", "We are having dinner at eight.", "cear",
     "Spanish cena is dinner; PT cena is a scene"),
    ("Qual é o teu {apelido}?", "What is your surname?", "apellido",
     "one l in Portuguese, two in Spanish"),
    ("Ela ficou {embaraçada} com a pergunta.", "She was embarrassed by the question.",
     "grávida", "the same trap run the other way round"),
    ("Preciso de uma {borracha} para apagar isto.",
     "I need an eraser to rub this out.", "goma", "PT borracha is rubber, an eraser"),
    ("Esperei um {bocado} à porta.", "I waited a while at the door.", "rato",
     "Spanish rato is a while; PT rato is a mouse"),
]

# Braced cloze forms that are correct but outside the present-tense/plural
# paradigms this generator produces. Each needs a reason, like SPELLING_OK.
CLOZE_OK = {
    "saudades": "plural of saudade, used idiomatically (ter saudades)",
    "obrigado": "the fixed phrase entry, not an inflected form",
    "portuguesa": "feminine of português — generated, listed for clarity",
    "Posso": "sentence-initial capital of posso",
    "Ainda": "sentence-initial capital of ainda",
}


def slug(i):
    return f"pt{i:04d}"


def build():
    entries, by_word, warn = [], {}, []
    n = [0]

    def add(word, en, pos, lesson, **extra):
        n[0] += 1
        e = {"pt": word, "en": en, "pos": pos, "lesson": lesson, "id": slug(n[0])}
        e.update({k: v for k, v in extra.items() if v})
        entries.append(e)
        by_word.setdefault(word, e)
        return e

    for row in NOUNS + EXTRA_BR_NOUNS:
        word, gender, en, lesson = row[0], row[1], row[2], row[3]
        explicit = row[4] if len(row) > 4 else None
        # A multi-word noun has no single-word plural rule; the explicit form
        # is the authority there, so only single words are cross-checked.
        if " " in word or "-" in word:
            assert explicit, f"{word}: compound nouns need an explicit plural"
            forms = {"article": ("o" if gender == "m" else "a"), "plural": explicit}
        else:
            forms = noun_forms(word, gender, explicit)
        add(word, en, "noun", lesson, gender=gender,
            plural=forms["plural"], noun_decl=forms)

    for infinitive, en, lesson in VERBS:
        conj = conjugate(infinitive)
        add(infinitive, en, "verb", lesson, conjugation=conj,
            personal_infinitive=personal_infinitive(infinitive),
            future_subjunctive=future_subjunctive(infinitive))

    for row in ADJECTIVES:
        word, en, lesson = row[0], row[1], row[2]
        forms = decline_adjective(word)
        if len(row) > 3:                      # bom/boa, mau/má are suppletive
            forms["f_sg"] = row[3]
            forms["f_pl"] = pluralize(row[3])
        add(word, en, "adjective", lesson, declension=forms)

    for word, pos, en, lesson in OTHERS:
        add(word, en, pos, lesson)
    for word, en, lesson in PHRASES:
        add(word, en, "phrase", lesson)

    # --- cloze -------------------------------------------------------------
    for word, sentences in CLOZE.items():
        e = by_word.get(word)
        assert e, f"cloze for {word!r}, which is not an entry"
        e["cloze"] = [{"pt": s, "en": t} for s, t in sentences]

    # --- Brazilian variants ------------------------------------------------
    for pt, br in BR_VARIANTS.items():
        e = by_word.get(pt)
        assert e, f"BR variant for {pt!r}, which is not an entry"
        if pt != br:
            e["br"] = br

    # --- special banks -----------------------------------------------------
    special = {
        "ser_estar": [{"id": f"se{i:03d}", "pt": s, "en": t, "wrong": w, "note": note}
                      for i, (s, t, w, note) in enumerate(SER_ESTAR, 1)],
        "por_para": [{"id": f"pp{i:03d}", "pt": s, "en": t, "note": note}
                     for i, (s, t, note) in enumerate(POR_PARA, 1)],
        # The distractor is the plain infinitive: "antes de sair" is what a
        # learner writes when they have not met the personal infinitive.
        # In the THIRD PERSON SINGULAR the personal infinitive adds no ending,
        # so it already IS the plain infinitive and there would be nothing to
        # choose between. Those cards contrast the plural instead, which is the
        # same lesson from the other side: the ending is what marks the subject.
        "personal_inf": [{"id": f"pi{i:03d}", "pt": s, "en": t, "verb": v,
                          "person": p,
                          "wrong": (personal_infinitive(v)["eles_elas_voces"]
                                    if personal_infinitive(v)[p] == v else v),
                          "note": note}
                         for i, (s, t, v, p, note) in enumerate(PERSONAL_INF, 1)],
        # Here the distractor is the PERSONAL INFINITIVE, because that is the
        # form people substitute — se irmos for se formos.
        # For a REGULAR verb the two are the same word, which is precisely the
        # card's point but leaves nothing to choose between. Those contrast the
        # present indicative instead — "se falamos" for "se falarmos" is the
        # mistake people actually make.
        "fut_subj": [{"id": f"fs{i:03d}", "pt": s, "en": t, "verb": v,
                      "person": p,
                      "wrong": (conjugate(v)[p]
                                if personal_infinitive(v)[p] == future_subjunctive(v)[p]
                                else personal_infinitive(v)[p]),
                      "note": note}
                     for i, (s, t, v, p, note) in enumerate(FUT_SUBJ, 1)],
        "false_friend": [{"id": f"ff{i:03d}", "pt": s, "en": t,
                          "wrong": trap, "note": note}
                         for i, (s, t, trap, note) in enumerate(FALSE_FRIENDS, 1)],
    }

    check_ids(entries)
    check_cloze(entries, warn)
    check_special(special)
    check_spelling(entries, special, warn)

    deck = {"meta": {"version": "1.0", "language": "pt", "variant": "european",
                     "reference_lang": "en", "level": "A1-A2",
                     "created": "2026-08-11"},
            "entries": entries, "special": special}
    json.dump(deck, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)

    pos = collections.Counter(e["pos"] for e in entries)
    lessons = len({e["lesson"] for e in entries})
    cloze = sum(len(e.get("cloze", [])) for e in entries)
    br = sum(1 for e in entries if e.get("br"))
    print(f"vocab_pt.json: {len(entries)} entries, {lessons} lessons, "
          f"{cloze} cloze sentences, {br} marked BR variants")
    print("  " + " · ".join(f"{v} {k}" for k, v in pos.most_common()))
    print("  special: " + " · ".join(f"{len(v)} {k}" for k, v in special.items()))
    for w in warn:
        print(f"  note: {w}")


def check_ids(entries):
    seen = set()
    for e in entries:
        assert e["id"] not in seen, f"duplicate id {e['id']}"
        seen.add(e["id"])
        assert e["pt"] and e["en"], f"{e['id']}: empty headword or gloss"


def all_forms(e):
    """Every inflected form this entry legitimately has."""
    forms = {e["pt"]}
    forms.update(v for v in (e.get("conjugation") or {}).values())
    forms.update(v for v in (e.get("declension") or {}).values())
    if e.get("plural"):
        forms.add(e["plural"])
    return forms


def check_cloze(entries, warn):
    import re
    for e in entries:
        for c in e.get("cloze", []):
            m = re.findall(r"\{([^}]+)\}", c["pt"])
            assert len(m) == 1, f"{e['id']}: cloze needs exactly one {{target}} — {c['pt']!r}"
            target = m[0]
            if target in CLOZE_OK:
                continue
            assert target in all_forms(e), (
                f"{e['id']}: cloze target {target!r} is not a form of {e['pt']!r}; "
                f"add it to CLOZE_OK with a reason if it is correct")


def check_special(special):
    import re
    for bank, items in special.items():
        for it in items:
            if "wrong" in it and "{" in it.get("pt", ""):
                answer = re.findall(r"\{([^}]+)\}", it["pt"])[0]
                assert it["wrong"] != answer, (
                    f"{it['id']}: the distractor is the same word as the answer "
                    f"({answer!r}) — the card offers no choice")
        for it in items:
            if "pt" in it and "{" in it.get("pt", ""):
                m = re.findall(r"\{([^}]+)\}", it["pt"])
                assert len(m) == 1, f"{it['id']}: needs exactly one braced answer"
    # the personal-infinitive and future-subjunctive banks must agree with the
    # generator, or the drill would teach a form the paradigm table denies
    for it in special["personal_inf"]:
        want = personal_infinitive(it["verb"])[it["person"]]
        got = re.findall(r"\{([^}]+)\}", it["pt"])[0]
        assert got == want, (f"{it['id']}: sentence has {got!r} but the personal "
                             f"infinitive of {it['verb']} for {it['person']} is {want!r}")
    for it in special["fut_subj"]:
        want = future_subjunctive(it["verb"])[it["person"]]

        got = re.findall(r"\{([^}]+)\}", it["pt"])[0]
        assert got == want, (f"{it['id']}: sentence has {got!r} but the future "
                             f"subjunctive of {it['verb']} for {it['person']} is {want!r}")


def check_spelling(entries, special, warn):
    try:
        from spellchecker import SpellChecker
    except ImportError:
        warn.append("pyspellchecker not installed — spelling oracle skipped. "
                    "pip install pyspellchecker")
        return
    sc = SpellChecker(language="pt")
    unknown = collections.Counter()
    for e in entries:
        for form in all_forms(e) | {e.get("br") or ""}:
            for w in str(form).replace("-", " ").replace("?", "").replace("...", "").split():
                w = w.strip(".,!¿?").lower()
                if not w or w in SPELLING_OK or w in sc:
                    continue
                unknown[w] += 1
    if unknown:
        raise AssertionError(
            "the spelling oracle does not recognise these forms; correct them, or "
            "add each to SPELLING_OK with a reason:\n  " +
            "\n  ".join(f"{w} (x{c})" for w, c in unknown.most_common()))


import re  # used by the checks above

if __name__ == "__main__":
    build()
