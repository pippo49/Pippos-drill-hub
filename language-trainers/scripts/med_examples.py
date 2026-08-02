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
