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
                              personal_infinitive, future_subjunctive, PERSONS,
                              conjugate_br, personal_infinitive_br,
                              future_subjunctive_br, PERSONS_BR)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "vocab_pt.json")
OUT_BR = os.path.join(HERE, "..", "vocab_br.json")

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
    "outonos": "regular plural of outono; the dictionary lacks the rare plural",
    "méis": "correct plural of mel, like papel/papéis; rare, so absent",
    "sangues": "sangue is a mass noun — the plural is regular but seldom used",
    "raivas": "likewise a mass noun with a regular, rarely used plural",
    "time": "Brazilian for a sports team, from English; the dictionary is European",
    "garçom": "Brazilian for a waiter; the dictionary is European",
    "mail": "half of the Brazilian e-mail, which the tokeniser splits on the hyphen",
    # plurals of the Brazilian headwords, generated once the BR deck swaps them in
    "bebês": "plural of bebê (BR)",
    "abajures": "plural of abajur (BR)",
    "times": "plural of time (BR)",
    "garçons": "plural of garçom (BR); garçons is the usual written plural",
    "mails": "from the split of e-mails",
    "marrom": "Brazilian for brown, where Portugal says castanho",
    "marrons": "plural of marrom (BR); it has no separate feminine",
    "econômica": "Brazilian spelling of económica",
    "econômicos": "Brazilian spelling of económicos",
    "econômicas": "Brazilian spelling of económicas",
    "bilheteria": "Brazilian spelling of bilheteira",
    "bilheterias": "plural of bilheteria (BR)",
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

    # --- deepening pass: nouns ------------------------------------------
    # L1 people
    ("neto", "m", "grandson", "1"), ("neta", "f", "granddaughter", "1"),
    ("sobrinho", "m", "nephew", "1"), ("cunhado", "m", "brother-in-law", "1"),
    ("namorado", "m", "boyfriend", "1"), ("namorada", "f", "girlfriend", "1"),
    ("colega", "m", "colleague", "1"), ("chefe", "m", "boss", "1"),
    ("adulto", "m", "adult", "1"), ("jovem", "m", "young person", "1"),
    ("bebé", "m", "baby (PT)", "1"), ("casal", "m", "couple", "1"),
    ("grupo", "m", "group", "1"), ("equipa", "f", "team (PT)", "1"),
    # L2 house
    ("corredor", "m", "corridor", "2"), ("varanda", "f", "balcony", "2"),
    ("garagem", "f", "garage", "2"), ("telhado", "m", "roof", "2"),
    ("tapete", "m", "carpet, rug", "2"), ("cortina", "f", "curtain", "2"),
    ("almofada", "f", "cushion, pillow", "2"), ("lençol", "m", "sheet", "2"),
    ("cobertor", "m", "blanket", "2"), ("gaveta", "f", "drawer", "2"),
    ("estante", "f", "shelf, bookcase", "2"), ("fogão", "m", "cooker, stove", "2"),
    ("forno", "m", "oven", "2"), ("frigorífico", "m", "fridge (PT)", "2"),
    ("máquina", "f", "machine", "2"), ("lixo", "m", "rubbish", "2"),
    ("sabão", "m", "soap", "2"), ("torneira", "f", "tap", "2"),
    # L3 time
    ("madrugada", "f", "early morning", "3"), ("meio-dia", "m", "midday", "3", "meios-dias"),
    ("meia-noite", "f", "midnight", "3", "meias-noites"),
    ("estação do ano", "f", "season", "3", "estações do ano"),
    ("primavera", "f", "spring", "3"), ("verão", "m", "summer", "3"),
    ("outono", "m", "autumn", "3"), ("inverno", "m", "winter", "3"),
    ("segunda-feira", "f", "Monday", "3", "segundas-feiras"),
    ("sábado", "m", "Saturday", "3"), ("domingo", "m", "Sunday", "3"),
    ("data", "f", "date", "3"), ("prazo", "m", "deadline", "3"),
    ("atraso", "m", "delay", "3"), ("vez", "f", "time, turn", "3"),
    # L4 food
    ("refeição", "f", "meal", "4"), ("lanche", "m", "snack", "4"),
    ("prato do dia", "m", "dish of the day", "4", "pratos do dia"),
    ("entrada", "f", "starter, entrance", "4"), ("salada", "f", "salad", "4"),
    ("cebola", "f", "onion", "4"), ("alho", "m", "garlic", "4"),
    ("tomate", "m", "tomato", "4"), ("cenoura", "f", "carrot", "4"),
    ("feijão", "m", "bean", "4"), ("massa", "f", "pasta", "4"),
    ("sandes", "f", "sandwich (PT)", "4", "sandes"),
    ("bacalhau", "m", "salt cod", "4"), ("marisco", "m", "seafood", "4"),
    ("gelado", "m", "ice cream (PT)", "4"), ("pastel", "m", "pastry", "4"),
    ("bolacha", "f", "biscuit (PT)", "4"), ("chocolate", "m", "chocolate", "4"),
    ("mel", "m", "honey", "4"), ("pimenta", "f", "pepper", "4"),
    ("empregado", "m", "waiter, employee", "4"),
    ("ementa", "f", "menu (PT)", "4"), ("gorjeta", "f", "tip", "4"),
    # L5 town & travel
    ("bairro", "m", "neighbourhood", "5"), ("centro", "m", "centre", "5"),
    ("esquina", "f", "corner", "5"), ("passeio", "m", "pavement, walk (PT)", "5"),
    ("semáforo", "m", "traffic light", "5"), ("cruzamento", "m", "crossroads", "5"),
    ("paragem", "f", "stop (PT)", "5"), ("metro", "m", "underground", "5"),
    ("elétrico", "m", "tram (PT)", "5"), ("táxi", "m", "taxi", "5"),
    ("camião", "m", "lorry (PT)", "5"), ("mota", "f", "motorbike (PT)", "5"),
    ("gasolina", "f", "petrol", "5"), ("condutor", "m", "driver (PT)", "5"),
    ("polícia", "f", "police", "5"), ("bombeiro", "m", "firefighter", "5"),
    ("farol", "m", "lighthouse, headlight", "5"), ("porto", "m", "port", "5"),
    ("fronteira", "f", "border", "5"), ("passaporte", "m", "passport", "5"),
    ("quarto duplo", "m", "double room", "5", "quartos duplos"),
    ("reserva", "f", "booking", "5"), ("chegada", "f", "arrival", "5"),
    ("partida", "f", "departure", "5"),
    # L6 nature
    ("nevoeiro", "m", "fog", "6"), ("trovoada", "f", "thunderstorm", "6"),
    ("relâmpago", "m", "lightning", "6"), ("gelo", "m", "ice", "6"),
    ("sombra", "f", "shade, shadow", "6"), ("luz", "f", "light", "6"),
    ("ilha", "f", "island", "6"), ("lago", "m", "lake", "6"),
    ("vale", "m", "valley", "6"), ("colina", "f", "hill", "6"),
    ("areia", "f", "sand", "6"), ("onda", "f", "wave", "6"),
    ("folha", "f", "leaf, sheet", "6"), ("raiz", "f", "root", "6"),
    ("semente", "f", "seed", "6"), ("erva", "f", "grass, herb", "6"),
    ("porco", "m", "pig", "6"), ("ovelha", "f", "sheep", "6"),
    ("galinha", "f", "hen", "6"), ("rato", "m", "mouse, rat", "6"),
    ("abelha", "f", "bee", "6"), ("mosca", "f", "fly", "6"),
    # L7 body & health
    ("pescoço", "m", "neck", "7"), ("ombro", "m", "shoulder", "7"),
    ("joelho", "m", "knee", "7"), ("barriga", "f", "belly", "7"),
    ("peito", "m", "chest", "7"), ("pele", "f", "skin", "7"),
    ("osso", "m", "bone", "7"), ("sangue", "m", "blood", "7"),
    ("cirurgia", "f", "surgery", "7"), ("consulta", "f", "appointment", "7"),
    ("receita", "f", "prescription, recipe", "7"), ("comprimido", "m", "tablet", "7"),
    ("vacina", "f", "vaccine", "7"), ("gripe", "f", "flu", "7"),
    ("constipação", "f", "cold (PT)", "7"), ("tosse", "f", "cough", "7"),
    ("ferida", "f", "wound", "7"), ("dentista", "m", "dentist", "7"),
    # L8 work & study
    ("carreira", "f", "career", "8"), ("cargo", "m", "post, position", "8"),
    ("salário", "m", "salary", "8"), ("contrato", "m", "contract", "8"),
    ("entrevista", "f", "interview", "8"), ("colega de trabalho", "m", "workmate", "8",
     "colegas de trabalho"),
    ("prazo de entrega", "m", "delivery deadline", "8", "prazos de entrega"),
    ("relatório", "m", "report", "8"), ("apresentação", "f", "presentation", "8"),
    ("formação", "f", "training", "8"), ("licenciatura", "f", "degree (PT)", "8"),
    ("nota", "f", "mark, note", "8"), ("turma", "f", "class group", "8"),
    ("biblioteca", "f", "library", "8"), ("dicionário", "m", "dictionary", "8"),
    ("tradução", "f", "translation", "8"), ("erro", "m", "mistake", "8"),
    ("exercício", "m", "exercise", "8"), ("regra", "f", "rule", "8"),
    ("exemplo", "m", "example", "8"),
    # L9 things & tech
    ("teclado", "m", "keyboard", "9"), ("impressora", "f", "printer", "9"), ("carregador", "m", "charger", "9"),
    ("bateria", "f", "battery", "9"), ("aplicação", "f", "app", "9"),
    ("palavra-passe", "f", "password (PT)", "9", "palavras-passe"),
    ("correio eletrónico", "m", "email (PT)", "9", "correios eletrónicos"),
    ("rede", "f", "network", "9"), ("ligação", "f", "connection", "9"),
    ("notícia", "f", "news item", "9"), ("anúncio", "m", "advertisement", "9"),
    ("bilheteira", "f", "ticket office (PT)", "9"),
    ("camisola", "f", "jumper (PT)", "9"), ("vestido", "m", "dress", "9"),
    ("saia", "f", "skirt", "9"), ("meia", "f", "sock", "9"),
    ("cinto", "m", "belt", "9"), ("óculos", "m", "glasses", "9", "óculos"),
    ("anel", "m", "ring", "9"), ("carteira", "f", "wallet, handbag", "9"),
    ("guarda-chuva", "m", "umbrella", "9", "guarda-chuvas"),
    # L10 abstract
    ("ódio", "m", "hatred", "10"), ("raiva", "f", "anger", "10"),
    ("orgulho", "m", "pride", "10"), ("vergonha", "f", "shame", "10"),
    ("ciúme", "m", "jealousy", "10"), ("surpresa", "f", "surprise", "10"),
    ("desejo", "m", "wish", "10"), ("dúvida", "f", "doubt", "10"),
    ("certeza", "f", "certainty", "10"), ("segredo", "m", "secret", "10"),
    ("silêncio", "m", "silence", "10"), ("barulho", "m", "noise", "10"),
    ("cuidado", "m", "care", "10"), ("perigo", "m", "danger", "10"),
    ("risco", "m", "risk", "10"), ("erro humano", "m", "human error", "10",
     "erros humanos"),
    ("costume", "m", "custom, habit", "10"), ("cultura", "f", "culture", "10"),
    ("sociedade", "f", "society", "10"), ("governo", "m", "government", "10"),
    ("lei", "f", "law", "10"), ("imposto", "m", "tax", "10"),
    ("preço justo", "m", "fair price", "10", "preços justos"),
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

    # --- deepening pass: verbs ------------------------------------------
    ("conduzir", "to drive (PT)", "13"), ("acontecer", "to happen", "14"),
    ("existir", "to exist", "14"), ("tornar", "to make, to turn", "14"),
    ("criar", "to create, to raise", "14"), ("nascer", "to be born", "14"),
    ("morrer", "to die", "14"), ("crescer", "to grow", "14"),
    ("mostrar", "to show", "12"), ("explicar", "to explain", "12"),
    ("contar", "to tell, to count", "12"), ("repetir", "to repeat", "12"),
    ("traduzir", "to translate", "12"), ("significar", "to mean", "12"),
    ("chorar", "to cry", "14"), ("rir", "to laugh", "14"),
    ("sorrir", "to smile", "14"), ("gritar", "to shout", "14"),
    ("cumprimentar", "to greet", "14"), ("apresentar", "to introduce", "14"),
    ("convidar", "to invite", "14"), ("agradecer", "to thank", "14"),
    ("desculpar", "to forgive", "14"), ("prometer", "to promise", "14"),
    ("decidir", "to decide", "15"), ("escolher", "to choose", "15"),
    ("aceitar", "to accept", "15"), ("recusar", "to refuse", "15"),
    ("permitir", "to allow", "15"), ("proibir", "to forbid", "15"),
    ("obrigar", "to force", "15"), ("evitar", "to avoid", "15"),
    ("melhorar", "to improve", "15"), ("piorar", "to get worse", "15"),
    ("aumentar", "to increase", "15"), ("diminuir", "to decrease", "15"),
    ("acrescentar", "to add", "15"), ("retirar", "to remove", "15"),
    ("guardar", "to keep, to put away", "13"), ("arrumar", "to tidy", "13"),
    ("emprestar", "to lend", "13"), ("devolver", "to give back", "13"),
    ("receber", "to receive", "13"), ("enviar", "to send", "13"),
    ("mandar", "to send, to order", "13"), ("entregar", "to deliver", "13"),
    ("apanhar", "to catch, to pick up (PT)", "13"),
    ("atirar", "to throw", "13"), ("empurrar", "to push", "13"),
    ("puxar", "to pull", "13"), ("bater", "to hit, to knock", "13"),
    ("cortar", "to cut", "13"), ("partir_quebrar", "", ""),
    ("quebrar", "to break", "13"), ("consertar", "to repair", "13"),
    ("construir", "to build", "13"), ("desenhar", "to draw", "13"),
    ("pintar", "to paint", "13"), ("plantar", "to plant", "13"),
    ("regar", "to water", "13"), ("varrer", "to sweep", "15"),
    ("passear", "to go for a walk", "15"), ("nadar", "to swim", "15"),
    ("saltar", "to jump", "15"), ("cair", "to fall", "15"),
    ("levantar", "to lift, to get up", "15"), ("sentar", "to sit", "15"),
    ("deitar", "to lie down", "15"), ("vestir_ph", "", ""),
    ("calçar", "to put on (shoes)", "15"), ("despir", "to undress", "15"),
    ("pentear", "to comb", "15"), ("barbear", "to shave", "15"),
    ("descansar", "to rest", "15"), ("acordar_ph", "", ""),
    ("sonhar", "to dream", "14"), ("imaginar", "to imagine", "14"),
    ("duvidar", "to doubt", "14"), ("acreditar", "to believe", "14"),
    ("confiar", "to trust", "14"), ("odiar", "to hate", "14"),
    ("amar", "to love", "14"), ("adorar", "to adore, to love", "14"),
    ("detestar", "to detest", "14"), ("interessar", "to interest", "14"),
    ("importar", "to matter, to import", "14"),
    ("valer", "to be worth", "15"), ("custar", "to cost", "15"),
    ("gastar", "to spend", "15"), ("poupar", "to save", "15"),
    ("alugar", "to rent", "15"), ("visitar", "to visit", "15"),
    ("marcar", "to book, to score", "15"), ("cancelar", "to cancel", "15"),
    ("assinar", "to sign", "15"), ("carregar", "to carry, to charge", "15"),
    ("ligar", "to switch on, to phone", "9"), ("desligar", "to switch off", "9"),
    ("apagar", "to turn off, to erase", "9"), ("gravar", "to record", "9"),
    ("imprimir", "to print", "9"), ("descarregar", "to download (PT)", "9"),
    ("pesquisar", "to search", "9"), ("clicar", "to click", "9"),
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

    # --- deepening pass: adjectives --------------------------------------
    ("comprido", "long", "16"), ("estreito", "narrow", "16"),
    ("fundo", "deep", "16"), ("redondo", "round", "16"),
    ("liso", "smooth, straight", "16"), ("duro", "hard", "16"),
    ("mole", "soft", "16"), ("pesado", "heavy", "16"),
    ("leve", "light (weight)", "16"), ("claro", "light, clear", "16"),
    ("escuro", "dark", "16"), ("brilhante", "bright, shiny", "16"),
    ("simpático", "nice, friendly", "16"), ("antipático", "unfriendly", "16"),
    ("educado", "polite", "16"), ("mal-educado", "rude", "16"),
    ("generoso", "generous", "16"), ("egoísta", "selfish", "16"),
    ("honesto", "honest", "16"), ("preguiçoso", "lazy", "16"),
    ("inteligente", "intelligent", "16"), ("burro", "stupid", "16"),
    ("calmo", "calm", "17"), ("nervoso", "nervous", "17"),
    ("preocupado", "worried", "17"), ("assustado", "frightened", "17"),
    ("zangado", "angry (PT)", "17"), ("aborrecido", "bored, annoying (PT)", "17"),
    ("orgulhoso", "proud", "17"), ("envergonhado", "ashamed", "17"),
    ("apaixonado", "in love", "17"), ("solteiro", "single", "17"),
    ("casado", "married", "17"), ("ocupado", "busy", "17"),
    ("livre", "free", "17"), ("pronto", "ready", "17"),
    ("perdido", "lost", "17"), ("seguro", "safe, sure", "17"),
    ("perigoso", "dangerous", "17"), ("saudável", "healthy", "17"),
    ("fresco", "fresh, cool", "17"), ("maduro", "ripe, mature", "17"),
    ("doce", "sweet", "17"), ("amargo", "bitter", "17"),
    ("salgado", "salty", "17"), ("picante", "spicy", "17"),
    ("delicioso", "delicious", "17"), ("nojento", "disgusting", "17"),
    ("roxo", "purple", "18"), ("dourado", "golden", "18"),
    ("italiano", "Italian", "18"), ("chinês", "Chinese", "18"),
    ("japonês", "Japanese", "18"), ("americano", "American", "18"),
    ("africano", "African", "18"), ("mundial", "worldwide", "18"),
    ("nacional", "national", "18"), ("local", "local", "18"),
    ("público", "public", "18"), ("privado", "private", "18"),
    ("moderno", "modern", "18"), ("antigo", "old, ancient", "18"),
    ("famoso", "famous", "18"), ("estranho", "strange", "18"),
    ("esquisito", "odd, fussy (PT)", "18"), ("comum", "common", "18"),
    ("raro", "rare", "18"), ("útil", "useful", "18"),
    ("inútil", "useless", "18"), ("verdadeiro", "true", "18"),
    ("falso", "false", "18"), ("último", "last", "18"),
    ("próximo", "next, close", "18"), ("melhor", "better, best", "18"),
    ("pior", "worse, worst", "18"),
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
    # more vocabulary splits
    "frigorífico": "geladeira", "gelado": "sorvete", "camisola": "blusa",
    "casa de banho": "banheiro", "paragem": "ponto", "elétrico": "bonde",
    "camião": "caminhão", "mota": "moto", "condutor": "motorista",
    "empregado": "garçom", "ementa": "cardápio", "bolacha": "biscoito",
    "sandes": "sanduíche", "equipa": "time", "licenciatura": "graduação",
    "correio eletrónico": "e-mail", "palavra-passe": "senha",
    "descarregar": "baixar", "apanhar": "pegar", "constipação": "resfriado",
    "aborrecido": "chato", "zangado": "bravo", "esquisito": "estranho",
    "casaco": "jaqueta", "passeio": "calçada", "autocarro": "ônibus",
    "bilheteira": "bilheteria", "castanho": "marrom", "cinzento": "cinza",
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

    # --- deepening pass: cloze -------------------------------------------
    "pai": [("O meu {pai} trabalha num banco.", "My father works in a bank."),
            ("Os {pais} dela vivem em Braga.", "Her parents live in Braga.")],
    "mãe": [("A {mãe} do João é professora.", "João's mother is a teacher.")],
    "filho": [("Temos dois {filhos}.", "We have two children."),
              ("O {filho} mais velho estuda medicina.", "The eldest son studies medicine.")],
    "amigo": [("Ele é o meu melhor {amigo}.", "He is my best friend."),
              ("Convidei os meus {amigos} para jantar.", "I invited my friends to dinner.")],
    "criança": [("A {criança} está a dormir.", "The child is sleeping."),
                ("As {crianças} brincam no parque.", "The children play in the park.")],
    "cão": [("O {cão} do vizinho ladra muito.", "The neighbour's dog barks a lot."),
            ("Tenho dois {cães}.", "I have two dogs.")],
    "jardim": [("O {jardim} está cheio de flores.", "The garden is full of flowers."),
               ("Os {jardins} da cidade são bonitos.", "The city gardens are beautiful.")],
    "flor": [("Comprei uma {flor} para ela.", "I bought her a flower."),
             ("As {flores} cheiram bem.", "The flowers smell good.")],
    "hora": [("Que {horas} são?", "What time is it?"),
             ("Espero há uma {hora}.", "I have been waiting for an hour.")],
    "semana": [("A {semana} passou depressa.", "The week went by quickly."),
               ("Vou de férias em duas {semanas}.", "I'm going on holiday in two weeks.")],
    "manhã": [("De {manhã} bebo café.", "In the morning I drink coffee.")],
    "noite": [("Boa {noite}!", "Good night!"),
              ("Trabalho às {noites}.", "I work nights.")],
    "água": [("Quero um copo de {água}.", "I want a glass of water.")],
    "café": [("Um {café}, por favor.", "A coffee, please."),
             ("Bebemos dois {cafés}.", "We drank two coffees.")],
    "vinho": [("Este {vinho} é do Douro.", "This wine is from the Douro.")],
    "peixe": [("O {peixe} está muito fresco.", "The fish is very fresh."),
              ("Comemos {peixes} grelhados.", "We ate grilled fish.")],
    "batata": [("Quero {batatas} fritas.", "I want chips.")],
    "conta": [("A {conta}, se faz favor.", "The bill, please.")],
    "rua": [("Moro nesta {rua}.", "I live on this street."),
            ("As {ruas} estão cheias.", "The streets are full.")],
    "loja": [("A {loja} abre às nove.", "The shop opens at nine."),
             ("As {lojas} fecham ao domingo.", "The shops close on Sundays.")],
    "bilhete": [("Comprei um {bilhete} de ida e volta.", "I bought a return ticket."),
                ("Os {bilhetes} estão esgotados.", "The tickets are sold out.")],
    "viagem": [("A {viagem} demora três horas.", "The journey takes three hours."),
               ("Fizemos duas {viagens} este ano.", "We took two trips this year.")],
    "praia": [("Vamos à {praia} amanhã.", "We're going to the beach tomorrow.")],
    "sol": [("Hoje está muito {sol}.", "It's very sunny today.")],
    "chuva": [("A {chuva} não para.", "The rain doesn't stop.")],
    "árvore": [("Aquela {árvore} é muito antiga.", "That tree is very old."),
               ("As {árvores} perdem as folhas no outono.",
                "The trees lose their leaves in autumn.")],
    "cabeça": [("Dói-me a {cabeça}.", "My head hurts.")],
    "olho": [("Ela tem os {olhos} verdes.", "She has green eyes.")],
    "pé": [("Vou a {pé} para o trabalho.", "I walk to work."),
           ("Tenho os {pés} frios.", "My feet are cold.")],
    "médico": [("Tenho consulta com o {médico}.", "I have a doctor's appointment."),
               ("Os {médicos} do hospital são bons.", "The hospital doctors are good.")],
    "trabalho": [("O {trabalho} começa às nove.", "Work starts at nine.")],
    "dinheiro": [("Não tenho {dinheiro} comigo.", "I don't have money on me.")],
    "professor": [("O {professor} explicou tudo.", "The teacher explained everything."),
                  ("Os {professores} estão em reunião.", "The teachers are in a meeting.")],
    "livro": [("Este {livro} é interessante.", "This book is interesting."),
              ("Li três {livros} este mês.", "I read three books this month.")],
    "computador": [("O meu {computador} está lento.", "My computer is slow.")],
    "música": [("Gosto desta {música}.", "I like this music.")],
    "roupa": [("A {roupa} está a secar.", "The washing is drying.")],
    "amor": [("O {amor} é cego.", "Love is blind.")],
    "verdade": [("Diz-me a {verdade}.", "Tell me the truth.")],
    "razão": [("Tens {razão}.", "You are right."),
              ("Há várias {razões} para isso.", "There are several reasons for that.")],
    # verbs
    "viver": [("Eu {vivo} sozinho.", "I live alone."),
              ("Eles {vivem} no campo.", "They live in the countryside.")],
    "trabalhar": [("Eu {trabalho} numa escola.", "I work in a school."),
                  ("Tu {trabalhas} demasiado.", "You work too much.")],
    "estudar": [("Nós {estudamos} português.", "We study Portuguese.")],
    "aprender": [("Eu {aprendo} depressa.", "I learn quickly.")],
    "ler": [("Eu {leio} antes de dormir.", "I read before sleeping."),
            ("Vocês {leem} muito.", "You read a lot.")],
    "escrever": [("Eu {escrevo} um email.", "I'm writing an email.")],
    "ouvir": [("Eu não {ouço} nada.", "I can't hear anything."),
              ("Tu {ouves} música?", "Do you listen to music?")],
    "beber": [("Eu {bebo} água.", "I drink water.")],
    "abrir": [("A loja {abre} às dez.", "The shop opens at ten.")],
    "comprar": [("Eu {compro} o pão de manhã.", "I buy the bread in the morning.")],
    "pagar": [("Eu {pago} com cartão.", "I pay by card.")],
    "chegar": [("O comboio {chega} às seis.", "The train arrives at six.")],
    "voltar": [("Eu {volto} amanhã.", "I'll come back tomorrow.")],
    "esperar": [("Eu {espero} aqui.", "I'll wait here.")],
    "pensar": [("Eu {penso} que sim.", "I think so.")],
    "ajudar": [("Podes {ajudar}-me?", "Can you help me?")],
    "encontrar": [("Não {encontro} as chaves.", "I can't find the keys.")],
    "conseguir": [("Eu não {consigo} abrir isto.", "I can't manage to open this.")],
    "perder": [("Eu {perco} sempre o autocarro.", "I always miss the bus.")],
    "vestir": [("Eu {visto} um casaco.", "I put on a coat.")],
    "servir": [("Este prato {serve} duas pessoas.", "This dish serves two people.")],
    "seguir": [("Eu {sigo} a estrada principal.", "I follow the main road.")],
    "rir": [("Nós {rimos} muito ontem.", "We laughed a lot yesterday.")],
    "conduzir": [("Ele {conduz} muito depressa.", "He drives very fast.")],
    "traduzir": [("Eu {traduzo} do inglês.", "I translate from English.")],
    "passear": [("Eu {passeio} no parque.", "I stroll in the park.")],
    "proibir": [("A lei {proíbe} isso.", "The law forbids that.")],
    "construir": [("Eles {constroem} uma casa.", "They are building a house.")],
    "acreditar": [("Eu não {acredito} nisso.", "I don't believe that.")],
    "escolher": [("Tu {escolhes} o restaurante.", "You choose the restaurant.")],
    "custar": [("Quanto {custa}?", "How much does it cost?")],
    "ligar": [("Eu {ligo} mais tarde.", "I'll call later.")],
    # adjectives
    "pequeno": [("A casa é {pequena}.", "The house is small."),
                ("Os quartos são {pequenos}.", "The rooms are small.")],
    "novo": [("Comprei um carro {novo}.", "I bought a new car."),
             ("Ela é muito {nova}.", "She is very young.")],
    "velho": [("Este livro é {velho}.", "This book is old.")],
    "caro": [("O hotel é muito {caro}.", "The hotel is very expensive."),
             ("As casas estão {caras}.", "Houses are expensive.")],
    "cansado": [("Estou {cansado}.", "I'm tired."),
                ("Ela está {cansada}.", "She is tired.")],
    "contente": [("Fiquei muito {contente}.", "I was very pleased.")],
    "aberto": [("A janela está {aberta}.", "The window is open.")],
    "frio": [("A água está {fria}.", "The water is cold.")],
    "difícil": [("O exame foi {difícil}.", "The exam was difficult."),
                ("As perguntas são {difíceis}.", "The questions are difficult.")],
    "simpático": [("A tua irmã é muito {simpática}.", "Your sister is very nice.")],
    "ocupado": [("Estou {ocupado} agora.", "I'm busy now.")],
    "pronto": [("Já estás {pronta}?", "Are you ready?")],
    "espanhol": [("Ele é {espanhol}.", "He is Spanish."),
                 ("Ela é {espanhola}.", "She is Spanish.")],
    "inglês": [("O meu {inglês} não é bom.", "My English isn't good."),
               ("Eles são {ingleses}.", "They are English.")],
    "útil": [("Este livro é muito {útil}.", "This book is very useful."),
             ("Dá conselhos {úteis}.", "He gives useful advice.")],
    # invariables & phrases
    "sempre": [("Ele chega {sempre} atrasado.", "He always arrives late.")],
    "nunca": [("{Nunca} fui a Lisboa.", "I have never been to Lisbon.")],
    "talvez": [("{Talvez} venha amanhã.", "Maybe he'll come tomorrow.")],
    "depois": [("Falamos {depois}.", "We'll talk later.")],
    "bem": [("Estou {bem}, obrigado.", "I'm well, thank you.")],
    "por favor": [("Um café, {por favor}.", "A coffee, please.")],
    "bom dia": [("{Bom dia}, como está?", "Good morning, how are you?")],
    "tudo bem?": [("Olá! {Tudo bem?}", "Hi! How's it going?")],
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
     "permanent location → ficar (Portuguese prefers it to estar here)"),
    ("A casa {é} de madeira.", "The house is made of wood.", "está", "material → ser"),
    ("Eles {estão} em casa.", "They are at home.", "são", "where someone is now → estar"),
    ("O livro {é} meu.", "The book is mine.", "está", "possession → ser"),
    ("A porta {está} aberta.", "The door is open.", "é", "resulting state → estar"),
    ("Ele {fica} nervoso antes dos exames.", "He gets nervous before exams.", "é",
     "becoming → ficar"),
    ("A reunião {é} às três.", "The meeting is at three.", "está",
     "when an event takes place → ser"),
    ("{Estou} a aprender português.", "I am learning Portuguese.", "Sou",
     "estar a + infinitive is the Portuguese progressive"),
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
     "exquisito", "Spanish exquisito means delicious; Portuguese esquisito means odd"),
    ("A minha irmã está {grávida}.", "My sister is pregnant.", "embaraçada",
     "Portuguese embaraçada means embarrassed, not pregnant"),
    ("Trabalho num {escritório} no centro.", "I work in an office in the centre.",
     "oficina", "Portuguese oficina is a workshop or garage"),
    ("Deixei uma {gorjeta} ao empregado.", "I left the waiter a tip.", "propina",
     "Portuguese propina is a tuition fee"),
    ("A ponte é muito {comprida}.", "The bridge is very long.", "larga",
     "Portuguese largo means wide, not long"),
    ("Há muito {pó} na estante.", "There is a lot of dust on the shelf.", "polvo",
     "Portuguese polvo is an octopus"),
    ("A sopa está muito {salgada}.", "The soup is very salty.", "salada",
     "Portuguese salada is a salad"),
    ("Vamos {jantar} às oito.", "We are having dinner at eight.", "cear",
     "Spanish cena is dinner; Portuguese cena is a scene"),
    ("Qual é o teu {apelido}?", "What is your surname?", "apellido",
     "one l in Portuguese, two in Spanish"),
    ("Ela ficou {embaraçada} com a pergunta.", "She was embarrassed by the question.",
     "grávida", "the same trap run the other way round"),
    ("Preciso de uma {borracha} para apagar isto.",
     "I need an eraser to rub this out.", "goma", "Portuguese borracha is rubber, an eraser"),
    ("Esperei um {bocado} à porta.", "I waited a while at the door.", "rato",
     "Spanish rato is a while; Portuguese rato is a mouse"),
]

SER_ESTAR += [
    ("O bilhete {é} caro.", "The ticket is expensive.", "está",
     "a lasting property of the thing → ser"),
    ("A loja {fica} na esquina.", "The shop is on the corner.", "está",
     "a fixed address → ficar"),
    ("{Estamos} em maio.", "It is May.", "Somos", "the current month → estar em"),
    ("Ele {é} muito alto.", "He is very tall.", "está", "physical trait → ser"),
    ("A comida {está} pronta.", "The food is ready.", "é", "a state reached → estar"),
    ("Nós {ficámos} muito contentes.", "We were very pleased.", "fomos",
     "becoming pleased → ficar"),
    ("O concerto {é} no sábado.", "The concert is on Saturday.", "está",
     "when an event happens → ser"),
    ("Os miúdos {estão} a brincar.", "The kids are playing.", "são",
     "estar a + infinitive, the European progressive"),
    ("Esta cadeira {é} de plástico.", "This chair is plastic.", "está",
     "material → ser"),
    ("A porta {fica} sempre aberta.", "The door is always left open.", "é",
     "staying in a state → ficar"),
]

POR_PARA += [
    ("Comprei isto {para} a minha mãe.", "I bought this for my mother.",
     "recipient → para"),
    ("Andámos {por} toda a cidade.", "We walked all over the city.",
     "movement around → por"),
    ("Este comboio vai {para} o Porto.", "This train goes to Porto.",
     "destination → para"),
    ("Fi-lo {por} ti.", "I did it for your sake.", "on someone's behalf → por"),
    ("Saímos {para} apanhar ar.", "We went out to get some air.", "purpose → para"),
    ("Foi escrito {por} um poeta.", "It was written by a poet.", "agent → por"),
    ("Fica {para} a semana.", "Leave it for next week.", "deadline → para"),
    ("Esperei {por} ti uma hora.", "I waited for you for an hour.",
     "esperar por, and the duration → por"),
]

PERSONAL_INF += [
    ("Antes de {partirmos}, telefona.", "Before we leave, call.", "partir", "nos",
     "antes de + personal infinitive"),
    ("É preciso {estudarem} mais.", "You need to study more.", "estudar",
     "eles_elas_voces", "impersonal expression, subject vocês"),
    ("Depois de {comermos}, saímos.", "After we eat, we'll go out.", "comer", "nos",
     "depois de + personal infinitive"),
    ("Para {viveres} bem, descansa.", "To live well, rest.", "viver", "tu",
     "para + personal infinitive with an explicit subject"),
    ("Foi bom {virem} cá.", "It was good that you came here.", "vir",
     "eles_elas_voces", "vir is regular in the personal infinitive: virem"),
    ("Sem {sabermos} a morada, é difícil.", "Without knowing the address it's hard.",
     "saber", "nos", "sem + personal infinitive; saber is regular here — sabermos"),
]

FUT_SUBJ += [
    ("Quando {vieres}, traz o livro.", "When you come, bring the book.", "vir", "tu",
     "future subjunctive vieres, not the personal infinitive vires"),
    ("Se {dermos} o nosso melhor, ganhamos.", "If we do our best, we'll win.",
     "dar", "nos", "future subjunctive dermos, not darmos"),
    ("Logo que {virem} o resultado, avisem.", "As soon as you see the result, tell us.",
     "ver", "eles_elas_voces", "ver gives virem — identical in spelling to vir's, "
     "which is why context decides"),
    ("Se {trouxeres} o carro, conduzo eu.", "If you bring the car, I'll drive.",
     "trazer", "tu", "future subjunctive trouxeres, not trazeres"),
    ("Enquanto {houver} vida, há esperança.", "While there is life, there is hope.",
     "haver", "ele_ela_voce", "future subjunctive houver, not haver"),
]

FALSE_FRIENDS += [
    ("Ele ficou {constipado} com o frio.", "He caught a cold in the cold weather.",
     "constipado_es", "Portuguese constipado is a head cold; in Spanish it means the opposite end"),
    ("Preciso de {tirar} férias.", "I need to take time off.", "tomar",
     "Portuguese uses tirar férias where Spanish uses tomar"),
    ("O {escritório} fica no segundo andar.", "The office is on the second floor.",
     "despacho", "Portuguese despacho is a dispatch, not an office"),
    ("Vou {apanhar} o autocarro.", "I'm going to catch the bus.", "coger",
     "coger is Spanish; in Portuguese apanhar (PT) or pegar (BR)"),
]

# Multi-word Brazilian nouns, whose plural no single-word rule can produce.
BR_COMPOUND_PLURALS = {
    "café da manhã": "cafés da manhã",
    "vaso sanitário": "vasos sanitários",
    "e-mail": "e-mails",
}

# ---------------------------------------------------------------------------
# BRAZILIAN SENTENCE VARIANTS
# Three differences are not a word swap and need the sentence rewritten:
#
#   clitic placement  Portugal puts the pronoun after the verb (chamo-me),
#                     Brazil before it (me chamo). Brazilian even starts a
#                     sentence with it, which Portugal's grammar forbids.
#   the progressive   estar a + infinitive (PT) vs the gerund (BR):
#                     está a dormir / está dormindo.
#   second person     tu with its own verb form (PT) vs você with the
#                     third-person form (BR).
#
# Keyed by the European sentence, so a European sentence that has no entry here
# is assumed to be identical in Brazil — and check_br_sentences() fails the
# build if a European-only construction slips through unrewritten.
# ---------------------------------------------------------------------------
BR_SENTENCES = {
    # clitic placement
    "Dói-me a {cabeça}.": "Minha {cabeça} está doendo.",
    "Dá-me a {mão}.": "Me dá a {mão}.",
    "Esqueci-me do {telemóvel} em casa.": "Esqueci meu {celular} em casa.",
    "Diz-me a {verdade}.": "Me diz a {verdade}.",
    "chamo-me...": "me chamo...",
    "pode ajudar-me?": "pode me ajudar?",
    "Podes {ajudar}-me?": "Você pode me {ajudar}?",
    "Lava as {mãos} antes de comer.": "Lave as {mãos} antes de comer.",
    # the progressive
    "Os {homens} estão a trabalhar.": "Os {homens} estão trabalhando.",
    "A {criança} está a dormir.": "A {criança} está dormindo.",
    "Este {mês} está a correr bem.": "Este {mês} está indo bem.",
    "A {roupa} está a secar.": "A {roupa} está secando.",
    "{Estou} a aprender português.": "{Estou} aprendendo português.",
    "A água {está} a ferver.": "A água {está} fervendo.",
    "Os {miúdos} estão a brincar.": "As crianças estão brincando.",
    "Os miúdos {estão} a brincar.": "As crianças {estão} brincando.",
    # tu -> você, with the third-person verb form
    "Tu {és} muito simpático.": "Você {é} muito simpático.",
    "Onde {estás}?": "Onde você {está}?",
    "Tu {tens} razão.": "Você {tem} razão.",
    "Tu {vais} de comboio?": "Você {vai} de trem?",
    "O que {fazes} ao fim de semana?": "O que você {faz} no fim de semana?",
    "Tu {sabes} cozinhar?": "Você {sabe} cozinhar?",
    "Tu {conheces} o João?": "Você {conhece} o João?",
    "Onde é que tu {moras}?": "Onde você {mora}?",
    "Tu {trabalhas} demasiado.": "Você {trabalha} demais.",
    "Tu {ouves} música?": "Você {ouve} música?",
    "Tu {escolhes} o restaurante.": "Você {escolhe} o restaurante.",
    "Já estás {pronta}?": "Você já está {pronta}?",
    "como estás?": "como você está?",
    "Vocês {leem} muito.": "Vocês {leem} muito.",
    # vocabulary inside a sentence
    "Apanhei o {comboio} das oito.": "Peguei o {trem} das oito.",
    "O {autocarro} está atrasado.": "O {ônibus} está atrasado.",
    "Eu {perco} sempre o autocarro.": "Eu sempre {perco} o ônibus.",
    "De {manhã} bebo café.": "De {manhã} eu tomo café.",
    "Quero {batatas} fritas.": "Quero {batatas} fritas.",
    "A {conta}, se faz favor.": "A {conta}, por favor.",
    "Um café, {por favor}.": "Um café, {por favor}.",
    "O comboio {chega} às seis.": "O trem {chega} às seis.",
    "Este comboio vai {para} o Porto.": "Este trem vai {para} o Porto.",
    "No caso de {haver} problemas, liga-me.": "No caso de {haver} problemas, me liga.",
    "Vou {apanhar} o autocarro.": "Vou {pegar} o ônibus.",
    # tu-based bank items move to você, which changes the braced verb form too
    "Se {puderes}, ajuda-me.": "Se você {puder}, me ajuda.",
    "Quando {fizeres} os anos, vamos festejar.":
        "Quando você {fizer} aniversário, vamos comemorar.",
    "Se {tiveres} tempo, telefona.": "Se você {tiver} tempo, liga.",
    "Quando {vieres}, traz o livro.": "Quando você {vier}, traz o livro.",
    "Se {trouxeres} o carro, conduzo eu.": "Se você {trouxer} o carro, eu dirijo.",
    "Para {seres} feliz, precisas de descansar.":
        "Para você {ser} feliz, precisa descansar.",
    "Trouxe o livro para {leres}.": "Trouxe o livro para você {ler}.",
    "Antes de {comeres}, lava as mãos.": "Antes de você {comer}, lave as mãos.",
    "Para {viveres} bem, descansa.": "Para você {viver} bem, descanse.",
    "Comprei um {bilhete} de ida e volta.": "Comprei uma {passagem} de ida e volta.",
    "Os {bilhetes} estão esgotados.": "As {passagens} estão esgotadas.",
    "Não {encontro} as chaves.": "Não {encontro} as chaves.",
    # the article before a possessive: Portugal keeps it, Brazil drops it
    "Aquele {homem} é o meu pai.": "Aquele {homem} é meu pai.",
    "O meu {pai} trabalha num banco.": "Meu {pai} trabalha num banco.",
    "O meu {irmão} mora no Porto.": "Meu {irmão} mora em São Paulo.",
    "Ele é o meu melhor {amigo}.": "Ele é meu melhor {amigo}.",
    "Convidei os meus {amigos} para jantar.": "Convidei meus {amigos} para jantar.",
    "A minha {casa} é pequena.": "Minha {casa} é pequena.",
    "O meu {computador} está lento.": "Meu {computador} está lento.",
    "O meu {inglês} não é bom.": "Meu {inglês} não é bom.",
    "O meu vizinho é {alemão}.": "Meu vizinho é {alemão}.",
    "A tua irmã é muito {simpática}.": "Sua irmã é muito {simpática}.",
    "O meu irmão {é} médico.": "Meu irmão {é} médico.",
    "A carta é {para} a minha mãe.": "A carta é {para} minha mãe.",
    "Comprei isto {para} a minha mãe.": "Comprei isto {para} minha mãe.",
    "Se {dermos} o nosso melhor, ganhamos.": "Se {dermos} nosso melhor, ganhamos.",
    "A minha irmã está {grávida}.": "Minha irmã está {grávida}.",
    # depressa is Portugal's; Brazil says rápido
    "A {semana} passou depressa.": "A {semana} passou rápido.",
    "O {coração} bate depressa.": "O {coração} bate rápido.",
    "Eu {aprendo} depressa.": "Eu {aprendo} rápido.",
    "Ele {conduz} muito depressa.": "Ele {conduz} a reunião com calma.",
    "Saímos {para} apanhar ar.": "Saímos {para} tomar ar.",
    "Deixei uma {gorjeta} ao empregado.": "Deixei uma {gorjeta} para o garçom.",
    # apelido is the false friend twice over: Spanish apellido is a surname, and
    # so is Portugal's apelido — but in Brazil an apelido is a NICKNAME, which
    # makes the Brazilian card a sharper version of the same lesson.
    "Qual é o teu {apelido}?": "Qual é o seu {sobrenome}?",
}

# A few bank items need their DISTRACTOR changed for Brazil as well, because
# the trap itself is variety-specific. Keyed by item id.
BR_WRONG = {
    "ff009": "apelido",
}

# European-only constructions. If one of these survives into the Brazilian deck
# the sentence was never rewritten, and the drill would teach Portugal's grammar
# to a Brazilian learner — which is the whole reason this deck exists.
import re as _re
# BR_SENTENCES rewrites the sentence; the NOTE explaining it has to follow, or
# the card shows `{Estou} aprendendo` above "estar a + infinitive is the
# progressive" and teaches the construction it just replaced.
BR_NOTES = {
    "estar a + infinitive is the Portuguese progressive":
        "estar + gerund is the Brazilian progressive",
    "estar a + infinitive, the European progressive":
        "estar + gerund, the Brazilian progressive",
    # The sentence became "Antes de você {comer}" — você takes the bare form,
    # so the note about the -es ending has nothing left to point at.
    "the -es ending marks tu":
        "você adds no ending, so the plural comerem is what marks a subject",
    "one l in Portuguese, two in Spanish":
        "Brazilian apelido is a NICKNAME; the surname is sobrenome",
    "Spanish exquisito means delicious; Portuguese esquisito means odd":
        "Spanish exquisito means delicious; in Brazil esquisito means odd or "
        "off-tasting",
    # conduzir keeps its "lead, conduct" sense in Brazil; driving is dirigir,
    # which is why the sentence above stopped being about a car.
    "conduzir → conduz, like dizer → diz": "conduzir → conduz; driving is dirigir",
}

# The European vocabulary pattern is DERIVED from BR_VARIANTS rather than
# hand-listed, because a hand-listed one only catches the words someone
# remembered: `Se falarmos devagar, ele percebe` sat in the future-subjunctive
# bank with Portugal's verb in it, and the four words in the old list did not
# include it. Every European headword the deck already knows a Brazilian
# equivalent for is a word that must not appear in a Brazilian sentence.
_EU_STEMS = sorted({w for w in BR_VARIANTS
                    if " " not in w and "-" not in w and "?" not in w},
                   key=len, reverse=True)
# Words the derived pattern flags that are in fact current in Brazil. Each
# needs a reason, like SPELLING_OK — the list is the argument, not the escape.
EU_VOCAB_OK = {
    "passeio": "a walk or outing in both varieties; only the pavement sense splits",
    "bilhete": "current in Brazil for a ticket or note; passagem is air/coach travel",
    "casaco": "current in Brazil for a coat",
    "gelado": "the adjective (iced) is current in Brazil; only the noun splits",
    "esquisito": "current in Brazil for odd or weird — which is the false friend",
}

# Whole texts the guard flags that are correct anyway, keyed by the id the
# check reports. A false-friend note NAMES the European word on purpose, and
# the article rule below is a tendency rather than an absolute: Brazil drops it
# in "meu pai" but keeps it in "qual é o seu nome?".
EU_TEXT_OK = {
    "ff009": "qual é o seu X keeps the article in Brazil too",
    "ff009 (note)": "names apelido on purpose — it is the Brazilian trap",
    "ff001 (note)": "names esquisito on purpose — it is the false friend",
    "ff016 (note)": "contrasts apanhar (PT) with pegar (BR) explicitly",
}

EU_ONLY = [
    (_re.compile(r"\b\w+-(me|te|nos|lhe|lhes)\b"), "clitic after the verb"),
    (_re.compile(r"\best(ou|ás|á|amos|ão)\s+a\s+\w+r\b"), "estar a + infinitive"),
    (_re.compile(r"\bTu\b|\btu\b"), "tu as the second person"),
    # Brazil drops the definite article before a possessive: "meu irmão", not
    # "o meu irmão". Portugal keeps it, and every ser/estar sentence written
    # for Portugal carried it straight into the Brazilian deck.
    (_re.compile(r"\b[oa]s?\s+(meu|minha|teu|tua|seu|sua|nosso|nossa)s?\b",
                 _re.IGNORECASE), "article before a possessive"),
    (_re.compile(r"(?<![\w-])(" + "|".join(_EU_STEMS) + r")(s|es|a|as|os|o|es)?(?![\w-])",
                 _re.IGNORECASE), "European vocabulary"),
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


def build(variant="eu"):
    """variant "eu" = European headwords with the Brazilian marked, and vice
    versa. ONE curated source produces both decks, so they cannot drift: a word
    added here appears in Portugal's and Brazil's trainer on the same run."""
    br = variant == "br"
    entries, by_word, warn = [], {}, []
    n = [0]

    def add(word, en, pos, lesson, **extra):
        n[0] += 1
        e = {"pt": word, "en": en, "pos": pos, "lesson": lesson, "id": slug(n[0])}
        e.update({k: v for k, v in extra.items() if v})
        entries.append(e)
        # Several headwords exist as more than one part of speech — frio and
        # segundo are both noun and adjective, jovem both noun and adjective.
        # Keying by word alone attached every cloze to whichever was added
        # first, so a cloze wanting the feminine "fria" landed on the noun.
        by_word.setdefault(word, []).append(e)
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
        # Brazil's paradigm has four slots: você takes the third-person form,
        # so drilling "tu falas" would teach a shape most Brazilians never use.
        add(infinitive, en, "verb", lesson,
            conjugation=(conjugate_br if br else conjugate)(infinitive),
            personal_infinitive=(personal_infinitive_br if br
                                 else personal_infinitive)(infinitive),
            future_subjunctive=(future_subjunctive_br if br
                                else future_subjunctive)(infinitive))

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

    # `alt` is the OTHER variety's form, whichever way round the deck is built,
    # so one engine serves both apps and only the two labels change.
    for eu_form, br_form in BR_VARIANTS.items():
        candidates = by_word.get(eu_form)
        assert candidates, f"variant pair for {eu_form!r}, which is not an entry"
        if eu_form == br_form:
            continue
        for e in candidates:
            if not br:
                e["alt"] = br_form
                continue
            e["pt"], e["alt"] = br_form, eu_form
            # The gloss carries a variety marker — "train (PT)" — which names
            # the variety the HEADWORD belongs to. After the swap the headword
            # is Brazil's, so the marker has to move with it, or the deck tells
            # a Brazilian learner that `trem` is what Portugal says.
            # \b, not "(PT)": the marker also appears mid-parenthesis, as in
            # "how are you? (informal, PT)" and "my name is... (PT word order)".
            e["en"] = re.sub(r"\bPT\b", "BR", e["en"])
            # The Brazilian word has its own morphology, and EVERY derived form
            # has to be recomputed from it — the plural (trem/trens, not
            # comboios), the feminine (marrom is invariable where castanho has
            # castanha) and the paradigm (baixar/baixo, not descarrego).
            # Leaving the European forms attached had the decline drill asking
            # for the feminine of `marrom` and answering `castanha`, which is
            # both varieties' word for neither thing.
            if e["pos"] == "adjective":
                e["declension"] = decline_adjective(br_form)
            elif e["pos"] == "verb":
                e["conjugation"] = conjugate_br(br_form)
                e["personal_infinitive"] = personal_infinitive_br(br_form)
                e["future_subjunctive"] = future_subjunctive_br(br_form)
            elif e["pos"] == "noun":
                if " " in br_form or "-" in br_form:
                    plural = BR_COMPOUND_PLURALS.get(br_form)
                    assert plural, (f"{br_form!r}: multi-word Brazilian noun needs "
                                    f"an entry in BR_COMPOUND_PLURALS")
                    e["plural"] = plural
                    e["noun_decl"] = {"article": e["noun_decl"]["article"],
                                      "plural": plural}
                else:
                    forms = noun_forms(br_form, e.get("gender", "m"))
                    e["plural"], e["noun_decl"] = forms["plural"], forms

    # --- cloze -------------------------------------------------------------
    for word, sentences in CLOZE.items():
        candidates = by_word.get(word)
        assert candidates, f"cloze for {word!r}, which is not an entry"
        for sentence, gloss in sentences:
            # Rewrite for Brazil FIRST: the rewritten sentence may brace a
            # different form (Tu és -> Você é), and it is that form which has to
            # exist in the entry's Brazilian paradigm.
            sentence = BR_SENTENCES.get(sentence, sentence) if br else sentence
            target = re.findall(r"\{([^}]+)\}", sentence)[0]
            # attach to the entry that actually HAS this form, so a homograph
            # cannot silently take another part of speech's sentence
            # A sentence-initial target is the same word with a capital, so
            # the comparison is case-folded rather than needing an exception
            # per sentence.
            low = target.lower()
            owner = next((c for c in candidates
                          if low in {f.lower() for f in all_forms(c)}
                          or target in CLOZE_OK), None)
            assert owner, (f"cloze target {target!r} is not a form of any "
                           f"{word!r} entry ({len(candidates)} candidates)")
            owner.setdefault("cloze", []).append({"pt": sentence, "en": gloss})

    # --- Brazilian variants ------------------------------------------------
    # --- special banks -----------------------------------------------------
    def bsent(x):
        return BR_SENTENCES.get(x, x) if br else x

    def bnote(x):
        return BR_NOTES.get(x, x) if br else x

    def bwrong(ident, trap):
        return BR_WRONG.get(ident, trap) if br else trap

    # Everything below has to agree on WHICH paradigm and WHICH person, or the
    # distractor is computed for Portugal and shipped to Brazil.
    pers_inf = personal_infinitive_br if br else personal_infinitive
    fut_sub = future_subjunctive_br if br else future_subjunctive
    conj = conjugate_br if br else conjugate

    def eff(p):
        return PERSON_BR_MAP.get(p, p) if br else p

    def pi_wrong(v, p):
        """The plain infinitive — except in the third person singular, where the
        personal infinitive already IS it, so the plural makes the contrast."""
        p = eff(p)
        return pers_inf(v)["voces_eles_elas" if br else "eles_elas_voces"] \
            if pers_inf(v)[p] == v else v

    def fs_wrong(v, p):
        """The personal infinitive — except for a regular verb, where the two
        coincide, so the present indicative carries the contrast instead."""
        p = eff(p)
        return conj(v)[p] if pers_inf(v)[p] == fut_sub(v)[p] else pers_inf(v)[p]

    special = {
        "ser_estar": [{"id": f"se{i:03d}", "pt": bsent(s), "en": t,
                       "wrong": w, "note": bnote(note)}
                      for i, (s, t, w, note) in enumerate(SER_ESTAR, 1)],
        "por_para": [{"id": f"pp{i:03d}", "pt": bsent(s), "en": t, "note": bnote(note)}
                     for i, (s, t, note) in enumerate(POR_PARA, 1)],
        # The distractor is the plain infinitive: "antes de sair" is what a
        # learner writes when they have not met the personal infinitive.
        # In the THIRD PERSON SINGULAR the personal infinitive adds no ending,
        # so it already IS the plain infinitive and there would be nothing to
        # choose between. Those cards contrast the plural instead, which is the
        # same lesson from the other side: the ending is what marks the subject.
        "personal_inf": [{"id": f"pi{i:03d}", "pt": bsent(s), "en": t, "verb": v,
                          "person": eff(p), "wrong": pi_wrong(v, p),
                          "note": bnote(note)}
                         for i, (s, t, v, p, note) in enumerate(PERSONAL_INF, 1)],
        # Here the distractor is the PERSONAL INFINITIVE, because that is the
        # form people substitute — se irmos for se formos.
        # For a REGULAR verb the two are the same word, which is precisely the
        # card's point but leaves nothing to choose between. Those contrast the
        # present indicative instead — "se falamos" for "se falarmos" is the
        # mistake people actually make.
        "fut_subj": [{"id": f"fs{i:03d}", "pt": bsent(s), "en": t, "verb": v,
                      "person": eff(p), "wrong": fs_wrong(v, p),
                      "note": bnote(note)}
                     for i, (s, t, v, p, note) in enumerate(FUT_SUBJ, 1)],
        "false_friend": [{"id": f"ff{i:03d}", "pt": bsent(s), "en": t,
                          "wrong": bwrong(f"ff{i:03d}", trap), "note": bnote(note)}
                         for i, (s, t, trap, note) in enumerate(FALSE_FRIENDS, 1)],
    }

    check_ids(entries)
    check_special(special, br)
    check_cloze(entries, warn)
    check_spelling(entries, special, warn)
    check_markers(entries, br)

    if br:
        check_br_sentences(entries, special)

    deck = {"meta": {"version": "1.1", "language": "pt",
                     "variant": "brazilian" if br else "european",
                     "reference_lang": "en", "level": "A1-A2",
                     "created": "2026-08-11"},
            "entries": entries, "special": special}
    json.dump(deck, open(OUT_BR if br else OUT, "w", encoding="utf-8"),
              ensure_ascii=False)

    pos = collections.Counter(e["pos"] for e in entries)
    lessons = len({e["lesson"] for e in entries})
    cloze = sum(len(e.get("cloze", [])) for e in entries)
    marked = sum(1 for e in entries if e.get("alt"))
    name = "vocab_br.json" if br else "vocab_pt.json"
    other = "European" if br else "Brazilian"
    print(f"{name}: {len(entries)} entries, {lessons} lessons, "
          f"{cloze} cloze sentences, {marked} marked {other} variants")
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
            assert target.lower() in {f.lower() for f in all_forms(e)}, (
                f"{e['id']}: cloze target {target!r} is not a form of {e['pt']!r}; "
                f"add it to CLOZE_OK with a reason if it is correct")


PERSON_BR_MAP = {"tu": "voce_ele_ela", "ele_ela_voce": "voce_ele_ela",
                 "eles_elas_voces": "voces_eles_elas"}


def check_special(special, br=False):
    pers_inf = personal_infinitive_br if br else personal_infinitive
    fut_sub = future_subjunctive_br if br else future_subjunctive
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
        want = pers_inf(it["verb"])[it["person"]]
        got = re.findall(r"\{([^}]+)\}", it["pt"])[0]
        assert got == want, (f"{it['id']}: sentence has {got!r} but the personal "
                             f"infinitive of {it['verb']} for {it['person']} is {want!r}")
    for it in special["fut_subj"]:
        want = fut_sub(it["verb"])[it["person"]]

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

def check_markers(entries, br):
    """A "(PT)" or "(BR)" in a gloss names a variety, so it has to be true.

    The markers were curated on the European headwords and the Brazilian deck
    swapped the headword out from under them, leaving `trem — train (PT)`: the
    deck telling a Brazilian learner that their own word is Portugal's. An
    entry that carries the OTHER variety's form in `alt` is by definition its
    own variety's word, so its marker can only be this deck's.
    """
    mine, theirs = ("BR", "PT") if br else ("PT", "BR")
    bad = [f"{e['pt']} — {e['en']}" for e in entries
           if e.get("alt") and re.search(rf"\b{theirs}\b", e["en"])]
    assert not bad, ("gloss marks the wrong variety on a paired entry: "
                     + "; ".join(bad[:6]))
    # And the marker is only meaningful on a word that is variety-specific:
    # every unpaired marker names a variety explicitly (conduzir/dirigir) and
    # must still be one of the two.
    for e in entries:
        for m in re.findall(r"\b(PT|BR)\b", e["en"]):
            assert m in (mine, theirs), e["en"]


def check_br_sentences(entries, special):
    """Nothing European-only may survive into the Brazilian deck."""
    bad = []
    texts = []
    for e in entries:
        if e["pos"] == "phrase":
            texts.append((e["id"], e["pt"]))
        for c in e.get("cloze", []):
            texts.append((e["id"], c["pt"]))
    for bank in special.values():
        for it in bank:
            if it.get("pt"):
                texts.append((it["id"], it["pt"]))
    # Notes are prose about the sentence, so a European-only construction in
    # one is exactly as wrong as in the sentence itself.
    for bank in special.values():
        for it in bank:
            if it.get("note"):
                texts.append((it["id"] + " (note)", it["note"]))
    for ident, text in texts:
        for pattern, why in EU_ONLY:
            m = pattern.search(text)
            if not m:
                continue
            if ident in EU_TEXT_OK:
                continue
            if why == "European vocabulary" and m.group(1).lower() in EU_VOCAB_OK:
                continue
            bad.append(f"{ident}: {why} — {text!r}")
    if bad:
        raise AssertionError(
            "European-only constructions left in the Brazilian deck; add a "
            "rewrite to BR_SENTENCES for each:\n  " + "\n  ".join(bad[:25]) +
            (f"\n  ... and {len(bad) - 25} more" if len(bad) > 25 else ""))


if __name__ == "__main__":
    build("eu")
    build("br")
