#!/usr/bin/env python3
"""Glosses for medical terms cited inside the notes but not drilled themselves.

The notes illustrate an element with real words ("-ectomy … appendectomy,
nephrectomy"). A learner should not have to guess what those mean, so the
breakdown panel lists every cited term with its meaning.

Most citations resolve against the deck itself (an entry, its plural, or the
same word in the other spelling convention). This file covers the rest.
`build_medical_vocab.py` asserts that EVERY medical-looking word cited in a note
resolves to a gloss, so a future note cannot quietly cite an unexplained term —
it fails the build until it is either glossed here or reworded.

Spelling follows the notes, which use the British forms (-aemia, oe-); the
lookup normalises so the American deck spelling matches either way.
"""

EXAMPLE_GLOSSARY = {
    # --- general processes and states
    "acidosis": "abnormally high acidity of the blood and tissues",
    "alcoholism": "dependence on alcohol",
    "anorexia": "loss of appetite",
    "cachexia": "severe wasting and weight loss from chronic illness",
    "catabolism": "the breaking down of complex molecules to release energy",
    "metabolism": "the chemical processes that sustain life",
    "organism": "an individual living thing",
    "pathogenesis": "the way a disease develops",
    "carcinogenesis": "the process by which cancer develops",
    "fibrosis": "thickening and scarring of connective tissue",
    "steatosis": "abnormal accumulation of fat within an organ",
    "necrobiosis": "the normal death of cells within living tissue",

    # --- specialties and sciences
    "andrology": "the study of male health and reproduction",
    "audiology": "the study of hearing",
    "biology": "the study of living things",
    "embryology": "the study of embryonic development",
    "gerontology": "the study of ageing",
    "histopathology": "the study of diseased tissue under the microscope",
    "immunology": "the study of the immune system",
    "morphology": "the study of form and structure",
    "mycology": "the study of fungi",
    "psychology": "the study of the mind and behaviour",
    "radiology": "the medical use of imaging",
    "serology": "the study of blood serum, especially its antibodies",
    "toxicology": "the study of poisons",
    "virology": "the study of viruses",
    "cardiologist": "a specialist in the heart",

    # --- cardiovascular
    "atheroma": "a fatty plaque in an artery wall",
    "arteriography": "imaging of the arteries",
    "embolism": "obstruction of a vessel by material carried in the bloodstream",
    "haemangioma": "a benign tumour made of blood vessels",
    "phonocardiogram": "a recording of the heart sounds",
    "sphygmomanometer": "the instrument for measuring blood pressure",
    "thrombocyte": "a platelet",
    "valvulitis": "inflammation of a heart valve",
    "vasculitis": "inflammation of blood vessels",
    "ventriculography": "imaging of the ventricles",
    "pericardiocentesis": "puncture of the pericardium to drain fluid",
    "sternotomy": "surgical incision of the breastbone",

    # --- respiratory
    "atelectasis": "incomplete expansion or collapse of part of a lung",
    "bronchiolitis": "inflammation of the bronchioles",
    "capnography": "recording of exhaled carbon dioxide",
    "anoxia": "a complete lack of oxygen in the tissues",
    "oximetry": "measurement of blood oxygen saturation",
    "pneumonia": "infection and inflammation of the lung tissue",
    "tracheitis": "inflammation of the trachea",
    "pleurodesis": "deliberate fusion of the pleural layers to stop fluid collecting",
    "pleurodynia": "pain in the chest wall",

    # --- gastrointestinal
    "appendicectomy": "surgical removal of the appendix (the British form of appendectomy)",
    "cholaemia": "bile in the blood",
    "choledocholithiasis": "a stone in the common bile duct",
    "cirrhosis": "irreversible scarring of the liver",
    "diverticulosis": "the presence of pouches in the bowel wall, without inflammation",
    "hepatocyte": "a liver cell",
    "ileitis": "inflammation of the ileum",
    "macroglossia": "an abnormally large tongue",
    "oesophagoscopy": "visual examination of the oesophagus",
    "paracentesis": "puncture of the abdomen to drain fluid",
    "proctoscopy": "visual examination of the rectum and anus",
    "sialolith": "a stone in a salivary gland or its duct",
    "xerostomia": "dry mouth",
    "endoscopy": "visual examination inside the body with a flexible instrument",

    # --- renal and urinary
    "bacteriuria": "bacteria in the urine",
    "ketonuria": "ketones in the urine",
    "nephropexy": "surgical fixation of a mobile kidney",
    "nephroptosis": "a dropped or abnormally mobile kidney",
    "pyelogram": "an x-ray image of the renal pelvis",
    "pyuria": "pus in the urine",
    "uraemia": "a build-up of urea and other waste in the blood from kidney failure",
    "urolith": "a stone in the urinary tract",
    "cystocele": "prolapse of the bladder into the vaginal wall",
    "rectocele": "prolapse of the rectum into the vaginal wall",

    # --- nervous system and psychiatry
    "agoraphobia": "fear of open or public places",
    "ataxia": "loss of coordinated movement",
    "diplegia": "paralysis affecting the same part on both sides of the body",
    "diplopia": "double vision",
    "dyskinesia": "abnormal involuntary movement",
    "dysphonia": "impaired voice production, hoarseness",
    "ganglionectomy": "surgical removal of a ganglion",
    "glioblastoma": "an aggressive malignant brain tumour of glial cells",
    "hyperaesthesia": "abnormally increased sensitivity to sensation",
    "hypnosis": "an induced state of deep, suggestible relaxation",
    "insomnia": "inability to sleep",
    "kleptomania": "a compulsion to steal",
    "meningioma": "a usually benign tumour of the meninges",
    "neuroma": "a benign tumour of nerve tissue",
    "photophobia": "abnormal discomfort in bright light",
    "pyromania": "a compulsion to set fires",
    "schizophrenia": "a psychotic disorder with disordered thought and perception",
    "trichotillomania": "a compulsion to pull out one's own hair",

    # --- musculoskeletal
    "fasciotomy": "surgical incision of fascia to relieve pressure",
    "osteogenesis": "the formation of bone",
    "pseudohypertrophy": "apparent enlargement from fat or fibrous tissue rather than muscle",
    "synovitis": "inflammation of a synovial membrane",
    "tendinopathy": "disease of a tendon",
    "tenotomy": "surgical division of a tendon",
    "vertebroplasty": "surgical stabilisation of a fractured vertebra with cement",
    "myeloblast": "an immature bone-marrow cell",
    "myeloma": "a malignant tumour of bone-marrow plasma cells",

    # --- skin
    "albinism": "congenital absence of pigment in skin, hair and eyes",
    "keratosis": "a horny thickening of the skin",
    "psoriasis": "a chronic scaly inflammatory skin disease",
    "xanthoma": "a yellowish deposit of fat in the skin",
    "anhidrosis": "absent or greatly reduced sweating",
    "granuloma": "a small nodule of inflammatory tissue",

    # --- blood, immune and metabolic
    "granulocyte": "a white blood cell containing granules",
    "haematopoiesis": "the formation of blood cells",
    "lymphocyte": "a white blood cell of the immune system",
    "monocyte": "a large white blood cell",
    "mononucleosis": "an infection marked by a rise in mononuclear white cells",
    "pancytopenia": "a deficiency of all the blood cell lines at once",
    "toxaemia": "toxins circulating in the blood",
    "viraemia": "virus present in the blood",
    "chlorosis": "an old name for iron-deficiency anaemia with a greenish pallor",
    "coagulopathy": "a disorder of blood clotting",
    "hyperlipidaemia": "abnormally high blood lipids",
    "gluconeogenesis": "the making of glucose from non-carbohydrate sources",
    "galactosaemia": "an inherited inability to metabolise galactose",
    "thymoma": "a tumour of the thymus",
    "adenocarcinoma": "a malignant tumour arising from glandular tissue",
    "mycosis": "a fungal infection",

    # --- reproductive and obstetric
    "balanitis": "inflammation of the glans penis",
    "hydrocele": "a collection of fluid around the testis",
    "mammoplasty": "surgical reshaping of the breast",
    "mastodynia": "breast pain",
    "metrorrhagia": "uterine bleeding between periods",
    "oligospermia": "an abnormally low sperm count",
    "orchidopexy": "surgical fixation of an undescended testis in the scrotum",
    "spermatogenesis": "the production of sperm",
    "praevia": "lying in front of the presenting part, as in placenta praevia",
    "pelvimetry": "measurement of the pelvis",

    # --- eye and ENT
    "blepharoplasty": "surgical repair or reshaping of the eyelid",
    "iritis": "inflammation of the iris",
    "scleritis": "inflammation of the sclera",
    "optometry": "measurement of vision",
    "tympanostomy": "surgical creation of an opening in the eardrum",

    # --- instruments and misc
    "microscope": "an instrument for viewing very small objects",
    "thermometer": "an instrument for measuring temperature",
    "tetralogy": "a set of four features occurring together, as in Tetralogy of Fallot",
}

# Words that look medical to the extractor but are ordinary English or a Greek
# or Latin etymon already explained by the surrounding sentence. Listing them
# here keeps the "every cited term is glossed" assertion honest rather than
# loosening the pattern that finds them.
NOT_TERMS = {
    "arteria", "kardia", "malakia", "pnoia", "rhoia", "therapeia", "tracheia",
    "chroma", "fascia", "tibia", "media", "materia",
}


# Clinical vocabulary used in the cloze sentences. These are not word-building
# elements — they cannot be recognised by a suffix — so they are curated. Keys
# may be phrases; matching is word-bounded and case-insensitive, longest first,
# so "iliac fossa" wins over a bare "fossa".
CLINICAL_GLOSSARY = {
    # signs, symptoms and examination
    "febrile": "feverish, running a temperature",
    "palpation": "examining by feeling with the hands",
    "palpable": "able to be felt on examination",
    "tenderness": "pain produced by pressing on a part",
    "tender": "painful when pressed",
    "rigidity": "involuntary stiffness of the abdominal wall, a sign of peritoneal irritation",
    "board-like": "so rigid it feels like a board — a sign of generalised peritonitis",
    "erythema": "redness of the skin from increased blood flow",
    "lesion": "an area of damaged or abnormal tissue",
    "colic": "pain coming in waves, from a hollow organ trying to overcome an obstruction",
    "loin-to-groin": "the path of pain typical of a stone passing down the ureter",
    "migratory": "moving from one site to another over time",
    "glove-and-stocking": "affecting the hands and feet first, the pattern of a peripheral neuropathy",
    "triad": "a group of three signs occurring together",
    "prodrome": "the early symptoms that run ahead of an illness",
    "melaena": "black tarry stool from blood digested in the gut",
    "polydipsia": "excessive thirst",
    "stiffness": "resistance to movement",
    "coarse": "thickened and heavy, said of facial features",
    "bulging": "pushed outwards by pressure behind it",
    "spontaneous": "happening without an obvious trigger",
    "uncomplicated": "without additional features that would change management",
    "non-healing": "failing to close or repair over the expected time",
    "low-trauma": "following a force too small to break a healthy bone",
    "peaked": "tall and narrow, said of the T wave on an ECG",

    # anatomy and regions
    "iliac fossa": "the lower quarter of the abdomen on either side",
    "fossa": "a shallow depression or hollow",
    "costal margin": "the lower edge of the rib cage",
    "costal": "pertaining to the ribs",
    "quadrant": "one of the four regions the abdomen is divided into for examination",
    "hepatic": "pertaining to the liver",
    "cerebral": "pertaining to the cerebrum, the main mass of the brain",
    "hemisphere": "one half of the brain",
    "cervical": "pertaining to the neck — or to the cervix of the uterus",
    "vertebral": "pertaining to the bones of the spine",
    "prostatic": "pertaining to the prostate gland",
    "iliac": "pertaining to the ilium, the flared hip bone",
    "urinary tract": "the kidneys, ureters, bladder and urethra together",
    "peripheral": "at the outer parts of the body, away from the centre",
    "central": "at or near the centre of the body — central cyanosis is seen on the tongue and lips",
    "calf": "the fleshy back of the lower leg",
    "loin": "the flank, between the ribs and the hip",
    "drum": "the eardrum, the tympanic membrane",
    "media": "middle — otitis media is infection of the middle ear",

    # investigations, findings and treatment
    "amylase": "a pancreatic enzyme; a raised blood level supports pancreatitis",
    "platelet": "the blood cell fragment that plugs a damaged vessel",
    "blast cells": "immature precursor cells, not normally seen in the blood",
    "blood film": "a stained smear of blood examined under the microscope",
    "infarct": "an area of tissue killed by loss of its blood supply",
    "malignancy": "a cancerous growth that invades and spreads",
    "haematological": "pertaining to the blood",
    "ultrasound": "imaging using high-frequency sound waves",
    "staging": "working out how far a cancer has spread",
    "core biopsy": "a biopsy taking a narrow cylinder of tissue",
    "excised": "cut out surgically",
    "ulceration": "the formation of a break in a surface lining",
    "ulcer": "a break in a surface lining that does not heal",
    "diffuse": "spread widely rather than confined to one spot",
    "insulin": "the hormone that lowers blood glucose",
    "diabetes": "a disease of raised blood glucose, from lack of insulin or resistance to it",
    "postoperative": "after an operation",
    "central line": "a catheter placed into a large central vein",
    "effusion": "an abnormal collection of fluid in a body cavity",
    "obstructing": "blocking the passage through a tube or opening",
    "pigmented": "containing pigment, coloured",
    "asymmetrical": "not the same on both sides — a warning feature in a skin lesion",
    "thickened": "increased in thickness, often from chronic inflammation",
    "stroke": "sudden loss of brain function from interrupted blood supply or bleeding",
    "weakness": "reduced power in a muscle or limb",
    "confusion": "impaired ability to think clearly and orientate oneself",
    "tremor": "a rhythmic involuntary shaking",
    "intolerance": "inability to tolerate something, such as cold",
    "fracture": "a break in a bone",

    # picked up when the cloze vocabulary was reviewed word by word: clinical
    # jargon whose everyday sense is different or vaguer than the medical one
    "acute": "of sudden onset and short duration — the opposite of chronic",
    "red flag": "a feature that raises the possibility of serious disease",
    "frequency": "needing to pass urine more often than normal",
    "discharge": "fluid coming out of a body opening or wound",
    "distribution": "the pattern of body regions a sign affects",
    "dominant hemisphere": "the half of the brain that holds language, the left in most people",
    "admission": "being taken into hospital as an inpatient",
    "imaging": "producing pictures of the inside of the body",
    "iron deficiency": "too little iron to make haemoglobin normally",
    "forward-bend test": "bending forward to make a spinal curve visible — screens for scoliosis",
    "probing to bone": "a wound deep enough for a probe to touch bone, suggesting bone infection",
    "ecg": "electrocardiogram — a recording of the heart's electrical activity",
    "t waves": "part of the ECG trace; tall peaked T waves suggest a high potassium",
    "x-ray": "an image made with x-radiation",
    "artery": "a vessel carrying blood away from the heart",
    "vein": "a vessel carrying blood back to the heart",
    "gallbladder": "the small sac under the liver that stores bile",
}


# Every word used in a cloze sentence must be classified: either it has a gloss
# (deck entry, EXAMPLE_GLOSSARY or CLINICAL_GLOSSARY) or it is ordinary English
# and listed here. `build_medical_vocab.py` fails on anything else, so a new
# cloze sentence CANNOT introduce an unexplained clinical word — the author is
# forced to decide which of the two it is. Generated once from the sentences in
# the deck and then reviewed by hand; add to it deliberately, not to silence a
# failure you have not read.
ORDINARY_WORDS = set("""
    a abdominal acquired adolescent's adult affected affecting after an
    antibiotics any area as assessment at athlete's attributed beats below
    better beyond bleeding bruising burning but cause caused chest child's
    classic climbing cm cold combination commonest condition confirmed
    confirming count course described despite detected diagnosed discussed
    ear edge enlargement enlarging establish eye family fatigue fatty
    features fever finding flight fluid following for forward-bend found
    frankly from gain general gut had hands he him his history hour hours in
    increasing indicate indicated indicates infection insertion
    investigation irregular is jaw joints kg labelled left limit lips
    liquids liver long-standing loss man massive may meal middle minute ml
    more neck needing needs new night no normal of older on over pain
    painless patient patient's per performed persistent persisting pillows
    point possibility presented procedure produce profound progressive
    prominent prompted raise raises raising reflect remained reported
    resolved rest resting revealed review right right-sided several severe
    she short should showed side simple single six solids spreading stairs
    stone suggested suggests supports suspicion sweating swollen taken than
    the then three times tissue tongue treated treating treatment typical
    under upper use usually visible vision wall warm warrants was weeks
    weight well which with without woman worrying worse young
""".split())
