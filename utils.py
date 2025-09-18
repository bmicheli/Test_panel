"""
Utility functions for PanelBuilder
Contains API calls, data processing, and helper functions
"""
import re
import requests
from functools import lru_cache
import json
import time
from collections import Counter
import requests
import pandas as pd
import numpy as np
import time
import concurrent.futures
from functools import lru_cache
import base64
import json
import os
import hashlib
import re
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
import io
from config import *


MEDICAL_TO_HPO_MAPPING = {
    # Système nerveux
    "epilepsy": ["HP:0001250", "HP:0002197", "HP:0011097", "HP:0007359", "HP:0001252", "HP:0010818"],
    "seizure": ["HP:0001250", "HP:0011097", "HP:0007359", "HP:0002069", "HP:0010818"],
    "status epilepticus": ["HP:0011143", "HP:0007359", "HP:0011097", "HP:0001250"],
    "infantile spasms": ["HP:0012469", "HP:0001250", "HP:0032793", "HP:0011097"],
    "febrile seizures": ["HP:0002373", "HP:0001250", "HP:0011097", "HP:0010818"],
    "absence seizures": ["HP:0002121", "HP:0010818", "HP:0007359", "HP:0001250"],
    "myoclonic seizures": ["HP:0002123", "HP:0010818", "HP:0002125", "HP:0001250"],
    "focal seizures": ["HP:0011097", "HP:0010818", "HP:0007359", "HP:0001250"],
    "neurodevelopmental": ["HP:0012759", "HP:0001263", "HP:0001249", "HP:0000750"],
    "intellectual": ["HP:0001249", "HP:0001263", "HP:0000750", "HP:0002342", "HP:0010864", "HP:0010862", "HP:0001256"],
    "autism": ["HP:0000717", "HP:0012759", "HP:0000729", "HP:0001249", "HP:0000750"],
    "ADHD": ["HP:0007018", "HP:0000736", "HP:0100543", "HP:0000750"],
    "microcephaly": ["HP:0000252", "HP:0001249", "HP:0002079", "HP:0001263"],
    "macrocephaly": ["HP:0000256", "HP:0001250", "HP:0002119", "HP:0004482", "HP:0001355"],
    "hydrocephalus": ["HP:0000238", "HP:0006956", "HP:0002197", "HP:0001331"],
    "hypotonia": ["HP:0001290", "HP:0012389", "HP:0001252", "HP:0002465"],
    "hypertonia": ["HP:0001276", "HP:0002061", "HP:0002063", "HP:0002395"],
    "ataxia": ["HP:0001251", "HP:0002066", "HP:0001310", "HP:0002070", "HP:0002071", "HP:0002315"],
    "spasticity": ["HP:0001257", "HP:0002061", "HP:0001276", "HP:0002395"],
    "dystonia": ["HP:0001332", "HP:0002070", "HP:0002066", "HP:0002071"],
    "parkinsonism": ["HP:0001300", "HP:0002070", "HP:0002071", "HP:0001332"],
    "tremor": ["HP:0001337", "HP:0002070", "HP:0004305", "HP:0002133"],
    "chorea": ["HP:0002072", "HP:0002070", "HP:0002071", "HP:0001332"],
    "hemiparesis": ["HP:0001269", "HP:0001250", "HP:0002315", "HP:0002070"],
    "neuropathy": ["HP:0009830", "HP:0000762", "HP:0003477", "HP:0007002"],
    "demyelinating neuropathy": ["HP:0003437", "HP:0009830", "HP:0007002", "HP:0003477"],
    "muscular": ["HP:0003560", "HP:0003198", "HP:0009063", "HP:0003324"],
    "dystrophy": ["HP:0003560", "HP:0003198", "HP:0009063", "HP:0003325"],
    "myopathy": ["HP:0003198", "HP:0009063", "HP:0003560", "HP:0003324", "HP:0004301"],
    "muscular dystrophy": ["HP:0003560", "HP:0003198", "HP:0003325", "HP:0003394"],
    "myasthenia": ["HP:0003190", "HP:0003198", "HP:0001252", "HP:0003390"],
    "developmental": ["HP:0012758", "HP:0001263", "HP:0000750", "HP:0012759"],
    "delay": ["HP:0012758", "HP:0001263", "HP:0000750", "HP:0001270"],
    "cognitive": ["HP:0001249", "HP:0000750", "HP:0002342", "HP:0001263"],
    "behavioral": ["HP:0000708", "HP:0001249", "HP:0000729", "HP:0100716"],
    "speech": ["HP:0000750", "HP:0001263", "HP:0002167", "HP:0002465"],
    "speech delay": ["HP:0000750", "HP:0002465", "HP:0002463", "HP:0002167"],
    "language": ["HP:0000750", "HP:0001263", "HP:0002167", "HP:0002463"],
    "language delay": ["HP:0002463", "HP:0000750", "HP:0002465", "HP:0002167"],
    "apraxia of speech": ["HP:0002370", "HP:0001260", "HP:0002465", "HP:0000750"],
    "dysarthria": ["HP:0001260", "HP:0002167", "HP:0002425", "HP:0009088"],
    "dysphagia": ["HP:0002015", "HP:0002013", "HP:0011968", "HP:0002020"],
    "migraine": ["HP:0002076", "HP:0002072", "HP:0002070", "HP:0001337"],
    "stroke": ["HP:0001297", "HP:0002140", "HP:0002170", "HP:0002630"],
    "TIA": ["HP:0002326", "HP:0001297", "HP:0002140", "HP:0002170"],
    "encephalopathy": ["HP:0001298", "HP:0002370", "HP:0007199", "HP:0002180"],

    # Système cardiovasculaire
    "cardiomyopathy": ["HP:0001638", "HP:0001644", "HP:0001639"],
    "dilated cardiomyopathy": ["HP:0001644", "HP:0001638", "HP:0006515", "HP:0001639"],
    "hypertrophic cardiomyopathy": ["HP:0001639", "HP:0001638", "HP:0006515", "HP:0001644"],
    "arrhythmia": ["HP:0011675", "HP:0001645", "HP:0001663", "HP:0005110"],
    "atrial fibrillation": ["HP:0005110", "HP:0011675", "HP:0001645", "HP:0001663"],
    "ventricular tachycardia": ["HP:0004756", "HP:0001663", "HP:0011675", "HP:0001645"],
    "bradycardia": ["HP:0001662", "HP:0011675", "HP:0001645", "HP:0005110"],
    "prolonged QT": ["HP:0001657", "HP:0011675", "HP:0001645", "HP:0001663"],
    "heart block": ["HP:0001678", "HP:0006682", "HP:0011675", "HP:0001645"],
    "cardiac": ["HP:0001627", "HP:0001638", "HP:0001629", "HP:0001631"],
    "heart": ["HP:0001627", "HP:0001638", "HP:0001629", "HP:0001631"],
    "heart failure": ["HP:0001635", "HP:0001643", "HP:0001642", "HP:0001641"],
    "aortic": ["HP:0002616", "HP:0001645", "HP:0001680", "HP:0004942"],
    "aortic aneurysm": ["HP:0005111", "HP:0002616", "HP:0004942", "HP:0001680"],
    "aortic dissection": ["HP:0002647", "HP:0005111", "HP:0004942", "HP:0001680"],
    "aortic stenosis": ["HP:0001643", "HP:0005111", "HP:0001680", "HP:0001647"],
    "mitral regurgitation": ["HP:0001653", "HP:0001654", "HP:0005110", "HP:0001645"],
    "congenital": ["HP:0001627", "HP:0001631", "HP:0030680", "HP:0011968"],
    "congenital heart disease": ["HP:0030680", "HP:0001627", "HP:0001631", "HP:0011968"],
    "hypertension": ["HP:0000822", "HP:0005117", "HP:0005118", "HP:0002615"],
    "hypotension": ["HP:0002615", "HP:0005117", "HP:0011108", "HP:0001635"],

    # Système respiratoire
    "asthma": ["HP:0002099", "HP:0002104", "HP:0011877", "HP:0011878"],
    "COPD": ["HP:0006510", "HP:0002097", "HP:0002100", "HP:0006533"],
    "emphysema": ["HP:0002097", "HP:0002100", "HP:0006531", "HP:0006533"],
    "bronchiectasis": ["HP:0002110", "HP:0006538", "HP:0006520", "HP:0012333"],
    "pulmonary fibrosis": ["HP:0002206", "HP:0002205", "HP:0002208", "HP:0025422"],
    "interstitial lung disease": ["HP:0006530", "HP:0002206", "HP:0025422", "HP:0002205"],
    "pneumonia": ["HP:0002090", "HP:0033214", "HP:0002088", "HP:0002878"],
    "sleep apnea": ["HP:0010535", "HP:0002878", "HP:0002875", "HP:0002104"],
    "dyspnea": ["HP:0002094", "HP:0002090", "HP:0002878", "HP:0002875"],
    "hemoptysis": ["HP:0002105", "HP:0033999", "HP:0006520", "HP:0002110"],

    # Système rénal
    "kidney": ["HP:0000077", "HP:0000083", "HP:0000107", "HP:0000822"],
    "renal": ["HP:0000077", "HP:0000083", "HP:0000107", "HP:0000822"],
    "nephritis": ["HP:0000123", "HP:0000077", "HP:0000083", "HP:0000099"],
    "cystic": ["HP:0000107", "HP:0000077", "HP:0000108", "HP:0000003"],
    "urinary": ["HP:0000119", "HP:0000077", "HP:0000014", "HP:0008677"],
    "chronic kidney disease": ["HP:0012622", "HP:0000124", "HP:0000121", "HP:0000120"],
    "acute kidney injury": ["HP:0001919", "HP:0000124", "HP:0000121", "HP:0000120"],
    "proteinuria": ["HP:0000093", "HP:0032316", "HP:0000095", "HP:0000121"],
    "hematuria": ["HP:0000790", "HP:0000121", "HP:0000120", "HP:0000124"],
    "nephrotic syndrome": ["HP:0000102", "HP:0032316", "HP:0000093", "HP:0000095"],
    "nephritic syndrome": ["HP:0012587", "HP:0000123", "HP:0000790", "HP:0000093"],
    "renal cysts": ["HP:0000107", "HP:0000003", "HP:0000803", "HP:0000802"],
    "polycystic kidney": ["HP:0000003", "HP:0000107", "HP:0000803", "HP:0000802"],
    "hydronephrosis": ["HP:0000126", "HP:0000077", "HP:0000083", "HP:0000124"],
    "vesicoureteral reflux": ["HP:0000073", "HP:0000077", "HP:0000119", "HP:0000074"],
    "urinary tract infection": ["HP:0000010", "HP:0000077", "HP:0000119", "HP:0000073"],

    # Système digestif
    "liver": ["HP:0001392", "HP:0001394", "HP:0002240", "HP:0001396"],
    "hepatic": ["HP:0001392", "HP:0001394", "HP:0002240", "HP:0001396"],
    "hepatomegaly": ["HP:0002240", "HP:0001392", "HP:0002241", "HP:0002237"],
    "splenomegaly": ["HP:0001744", "HP:0001742", "HP:0002240", "HP:0001392"],
    "cirrhosis": ["HP:0001394", "HP:0001392", "HP:0001409", "HP:0001410"],
    "cholestasis": ["HP:0001396", "HP:0002240", "HP:0006574", "HP:0002910"],
    "elevated transaminases": ["HP:0002910", "HP:0001392", "HP:0002240", "HP:0001394"],
    "steatosis": ["HP:0001397", "HP:0001392", "HP:0002240", "HP:0001394"],
    "pancreatic": ["HP:0001735", "HP:0001738", "HP:0002013", "HP:0001733"],
    "pancreatitis": ["HP:0001733", "HP:0001738", "HP:0001735", "HP:0002013"],
    "exocrine pancreatic insufficiency": ["HP:0001738", "HP:0001735", "HP:0002013", "HP:0001733"],
    "gastrointestinal": ["HP:0011024", "HP:0002013", "HP:0001396", "HP:0002019"],
    "intestinal": ["HP:0002013", "HP:0011024", "HP:0002019", "HP:0002033"],
    "diarrhea": ["HP:0002014", "HP:0002019", "HP:0012589", "HP:0002013"],
    "constipation": ["HP:0002019", "HP:0002013", "HP:0002020", "HP:0002242"],
    "malabsorption": ["HP:0002242", "HP:0011024", "HP:0002019", "HP:0002013"],
    "inflammatory bowel disease": ["HP:0002597", "HP:0002019", "HP:0011024", "HP:0002013"],
    "crohn disease": ["HP:0100280", "HP:0002597", "HP:0011024", "HP:0002019"],
    "ulcerative colitis": ["HP:0100279", "HP:0002597", "HP:0011024", "HP:0002019"],
    "celiac disease": ["HP:0002600", "HP:0002242", "HP:0011024", "HP:0002019"],

    # Métabolisme / Endocrinologie
    "diabetes": ["HP:0000819", "HP:0001998", "HP:0003074", "HP:0005978", "HP:0005977"],
    "type 1 diabetes": ["HP:0008188", "HP:0000819", "HP:0005978", "HP:0005977"],
    "type 2 diabetes": ["HP:0005977", "HP:0000819", "HP:0005978", "HP:0003074"],
    "hypoglycemia": ["HP:0001943", "HP:0005978", "HP:0005977", "HP:0003074"],
    "hyperglycemia": ["HP:0003074", "HP:0005977", "HP:0000819", "HP:0005978"],
    "obesity": ["HP:0001513", "HP:0000819", "HP:0004324", "HP:0001956", "HP:0001548"],
    "growth": ["HP:0001507", "HP:0004322", "HP:0000098", "HP:0001519"],
    "short": ["HP:0004322", "HP:0001507", "HP:0003508", "HP:0000098"],
    "short stature": ["HP:0004322", "HP:0003510", "HP:0003528", "HP:0001507"],
    "tall": ["HP:0000098", "HP:0001519", "HP:0001548", "HP:0003477"],
    "tall stature": ["HP:0000098", "HP:0001519", "HP:0001548", "HP:0003497"],
    "thyroid": ["HP:0000820", "HP:0008249", "HP:0002926", "HP:0000872"],
    "hypothyroidism": ["HP:0000821", "HP:0000853", "HP:0000846", "HP:0000860"],
    "hyperthyroidism": ["HP:0000822", "HP:0000840", "HP:0000839", "HP:0000855"],
    "adrenal insufficiency": ["HP:0008209", "HP:0000834", "HP:0000871", "HP:0000847"],
    "cushing syndrome": ["HP:0003119", "HP:0000846", "HP:0000840", "HP:0000860"],
    "hyperparathyroidism": ["HP:0000826", "HP:0000840", "HP:0000862", "HP:0002900"],
    "hypoparathyroidism": ["HP:0000829", "HP:0000862", "HP:0002900", "HP:0000860"],
    "lactic acidosis": ["HP:0003128", "HP:0002900", "HP:0001943", "HP:0001941"],
    "hyperammonemia": ["HP:0001987", "HP:0001943", "HP:0003128", "HP:0001941"],
    "endocrine": ["HP:0000818", "HP:0000819", "HP:0000820", "HP:0008249"],

    # Système hématologique
    "anemia": ["HP:0001903", "HP:0001871", "HP:0001892", "HP:0001873"],
    "microcytic anemia": ["HP:0001935", "HP:0001903", "HP:0001892", "HP:0001871"],
    "macrocytic anemia": ["HP:0001972", "HP:0001903", "HP:0001892", "HP:0001871"],
    "hemolytic anemia": ["HP:0001878", "HP:0001903", "HP:0001892", "HP:0001871"],
    "leukopenia": ["HP:0001882", "HP:0001875", "HP:0001874", "HP:0002715"],
    "lymphopenia": ["HP:0001888", "HP:0002715", "HP:0002721", "HP:0005406"],
    "neutropenia": ["HP:0001875", "HP:0001874", "HP:0001877", "HP:0005518"],
    "thrombocytopenia": ["HP:0001873", "HP:0001882", "HP:0004823", "HP:0001892"],
    "pancytopenia": ["HP:0001876", "HP:0001882", "HP:0001875", "HP:0001873"],
    "coagulopathy": ["HP:0003256", "HP:0001892", "HP:0001975", "HP:0001976"],
    "deep vein thrombosis": ["HP:0002625", "HP:0001977", "HP:0001975", "HP:0001976"],

    # Immunologie
    "immune": ["HP:0002715", "HP:0005406", "HP:0002721", "HP:0002960"],
    "immunodeficiency": ["HP:0002721", "HP:0005406", "HP:0002715", "HP:0004315"],
    "autoimmune": ["HP:0002960", "HP:0002715", "HP:0003493", "HP:0005404"],
    "infection": ["HP:0002719", "HP:0005406", "HP:0002721", "HP:0004313"],
    "recurrent infections": ["HP:0002719", "HP:0004313", "HP:0002715", "HP:0002754"],
    "inflammatory": ["HP:0002715", "HP:0002960", "HP:0001371", "HP:0032169"],

    # Système visuel
    "retinal": ["HP:0000479", "HP:0000504", "HP:0000541", "HP:0000568"],
    "retinitis pigmentosa": ["HP:0000510", "HP:0007703", "HP:0000541", "HP:0000568"],
    "retinal detachment": ["HP:0000541", "HP:0007703", "HP:0000568", "HP:0001117"],
    "coloboma": ["HP:0000589", "HP:0001120", "HP:0001103", "HP:0007792"],
    "blindness": ["HP:0000618", "HP:0000505", "HP:0000565", "HP:0007663", "HP:0000639"],
    "vision": ["HP:0000504", "HP:0000479", "HP:0000505", "HP:0007663"],
    "visual impairment": ["HP:0000505", "HP:0000618", "HP:0000481", "HP:0000496"],
    "optic": ["HP:0000648", "HP:0000504", "HP:0001138", "HP:0000543"],
    "optic atrophy": ["HP:0000648", "HP:0000543", "HP:0001138", "HP:0001103"],
    "optic nerve hypoplasia": ["HP:0000609", "HP:0000648", "HP:0000543", "HP:0001103"],
    "cataract": ["HP:0000518", "HP:0000479", "HP:0001596", "HP:0007700", "HP:0000523", "HP:0010696"],
    "glaucoma": ["HP:0000501", "HP:0000479", "HP:0001087", "HP:0012632", "HP:0001113"],
    "myopia": ["HP:0000545", "HP:0000486", "HP:0001141", "HP:0000496"],
    "hyperopia": ["HP:0000540", "HP:0000486", "HP:0001141", "HP:0000496"],
    "strabismus": ["HP:0000486", "HP:0000541", "HP:0000568", "HP:0000543"],
    "nystagmus": ["HP:0000639", "HP:0000618", "HP:0000505", "HP:0000496"],
    "eye": ["HP:0000478", "HP:0000479", "HP:0000504", "HP:0001098"],
    "ocular": ["HP:0000478", "HP:0000479", "HP:0000504", "HP:0001098"],

    # Système auditif
    "hearing": ["HP:0000365", "HP:0000407", "HP:0006824", "HP:0008527"],
    "hearing loss": ["HP:0000365", "HP:0000407", "HP:0000364", "HP:0008527"],
    "deafness": ["HP:0000365", "HP:0000407", "HP:0006824", "HP:0008527", "HP:0000359", "HP:0000400"],
    "auditory": ["HP:0000364", "HP:0000365", "HP:0000407", "HP:0006824"],
    "sensorineural": ["HP:0000407", "HP:0000365", "HP:0008527", "HP:0006824"],
    "sensorineural hearing loss": ["HP:0000407", "HP:0000365", "HP:0008527", "HP:0000370"],
    "conductive hearing loss": ["HP:0000405", "HP:0000365", "HP:0000364", "HP:0000370"],
    "mixed hearing loss": ["HP:0000406", "HP:0000365", "HP:0000407", "HP:0000405"],
    "tinnitus": ["HP:0000360", "HP:0000365", "HP:0000370", "HP:0000407"],
    "recurrent otitis media": ["HP:0010570", "HP:0000407", "HP:0000365", "HP:0000370"],

    # Dermatologie
    "eczema": ["HP:0000964", "HP:0000989", "HP:0000988", "HP:0000980"],
    "psoriasis": ["HP:0001053", "HP:0000988", "HP:0000989", "HP:0011121"],
    "ichthyosis": ["HP:0008064", "HP:0000952", "HP:0000988", "HP:0001054"],
    "alopecia": ["HP:0001596", "HP:0002205", "HP:0001595", "HP:0002212"],
    "hyperpigmentation": ["HP:0000953", "HP:0001000", "HP:0001010", "HP:0011121"],
    "hypopigmentation": ["HP:0001010", "HP:0001000", "HP:0000953", "HP:0011121"],
    "cafe au lait spots": ["HP:0000957", "HP:0000953", "HP:0001010", "HP:0011121"],
    "palmoplantar keratoderma": ["HP:0000982", "HP:0000952", "HP:0000988", "HP:0011121"],
    "nail dystrophy": ["HP:0008398", "HP:0001597", "HP:0001816", "HP:0001808"],
    "photosensitivity": ["HP:0000992", "HP:0011121", "HP:0000952", "HP:0000988"],

    # Musculosquelettique
    "skeletal": ["HP:0000924", "HP:0002652", "HP:0000929", "HP:0002813"],
    "bone": ["HP:0000924", "HP:0002652", "HP:0000929", "HP:0002813"],
    "facial": ["HP:0001999", "HP:0000271", "HP:0000234", "HP:0001574"],
    "cleft": ["HP:0000175", "HP:0001999", "HP:0000202", "HP:0000179"],
    "limb": ["HP:0040064", "HP:0002817", "HP:0001155", "HP:0002813"],
    "spine": ["HP:0002650", "HP:0000925", "HP:0002808", "HP:0100360"],
    "scoliosis": ["HP:0002650", "HP:0002655", "HP:0002751", "HP:0002943"],
    "kyphosis": ["HP:0002808", "HP:0002650", "HP:0000925", "HP:0100360"],
    "lordosis": ["HP:0002938", "HP:0000925", "HP:0002650", "HP:0100360"],
    "pectus excavatum": ["HP:0000767", "HP:0000768", "HP:0000764", "HP:0000766"],
    "pectus carinatum": ["HP:0000768", "HP:0000767", "HP:0000764", "HP:0000766"],
    "joint hypermobility": ["HP:0001388", "HP:0001382", "HP:0001371", "HP:0002972"],
    "joint contractures": ["HP:0001371", "HP:0001382", "HP:0001388", "HP:0002972"],
    "arthrogryposis": ["HP:0002804", "HP:0001371", "HP:0001382", "HP:0001388"],
    "osteopenia": ["HP:0000938", "HP:0000939", "HP:0000947", "HP:0000936"],
    "osteoporosis": ["HP:0000939", "HP:0000938", "HP:0000947", "HP:0000936"],
    "pathologic fractures": ["HP:0002659", "HP:0000939", "HP:0000938", "HP:0000947"],
    "genu valgum": ["HP:0002857", "HP:0002816", "HP:0002817", "HP:0002952"],
    "genu varum": ["HP:0002970", "HP:0002816", "HP:0002817", "HP:0002952"],
    "polydactyly": ["HP:0010442", "HP:0001159", "HP:0001161", "HP:0001160"],
    "syndactyly": ["HP:0001159", "HP:0001160", "HP:0001156", "HP:0001161"],
    "brachydactyly": ["HP:0001156", "HP:0001160", "HP:0001161", "HP:0001165"],
    "clinodactyly": ["HP:0001157", "HP:0001160", "HP:0001161", "HP:0001165"],

    # Psychiatrie
    "depression": ["HP:0000716", "HP:0000726", "HP:0000739", "HP:0100753"],
    "anxiety": ["HP:0000739", "HP:0100022", "HP:0000716", "HP:0000726"],
    "bipolar disorder": ["HP:0007302", "HP:0000716", "HP:0000745", "HP:0100753"],
    "schizophrenia": ["HP:0100753", "HP:0000709", "HP:0000745", "HP:0000726"],
    "OCD": ["HP:0100713", "HP:0000726", "HP:0000729", "HP:0000708"],
    "PTSD": ["HP:0033676", "HP:0000739", "HP:0000716", "HP:0000726"],
    "sleep disturbance": ["HP:0002360", "HP:0001250", "HP:0000739", "HP:0000716"],

    # Oncologie
    "cancer": ["HP:0002664", "HP:0030731", "HP:0100633", "HP:0006725"],
    "tumor": ["HP:0002664", "HP:0100633", "HP:0030731", "HP:0006725"],
    "malignant": ["HP:0002664", "HP:0030731", "HP:0100633", "HP:0006725"],
    "leukemia": ["HP:0001909", "HP:0002664", "HP:0005561", "HP:0004808"],
    "lymphoma": ["HP:0002665", "HP:0002664", "HP:0005561", "HP:0004808"],
    "neuroblastoma": ["HP:0006720", "HP:0002664", "HP:0006721", "HP:0005561"],
    "sarcoma": ["HP:0100245", "HP:0006726", "HP:0012115", "HP:0100640"],
    "melanoma": ["HP:0002861", "HP:0002860", "HP:0002862", "HP:0002863"],
    "glioma": ["HP:0100832", "HP:0001286", "HP:0002511", "HP:0002197"],
    "medulloblastoma": ["HP:0006777", "HP:0002197", "HP:0001286", "HP:0002511"],
    "retinoblastoma": ["HP:0009919", "HP:0001117", "HP:0000618", "HP:0000486"],

    # Système génito-urinaire
    "infertility": ["HP:0000787", "HP:0000135", "HP:0000140", "HP:0000144"],
    "amenorrhea": ["HP:0000141", "HP:0000878", "HP:0001596", "HP:0000140"],
    "oligomenorrhea": ["HP:0000876", "HP:0000141", "HP:0000878", "HP:0000140"],
    "menorrhagia": ["HP:0000132", "HP:0000878", "HP:0000141", "HP:0000140"],
    "dysmenorrhea": ["HP:0000574", "HP:0000132", "HP:0000878", "HP:0000141"],
    "cryptorchidism": ["HP:0000028", "HP:0000035", "HP:0000036", "HP:0008679"],
    "hypospadias": ["HP:0003244", "HP:0000035", "HP:0000036", "HP:0000028"],
    "polycystic ovary syndrome": ["HP:0000877", "HP:0000144", "HP:0000819", "HP:0000787"],

    # Termes génériques
    "syndrome": ["HP:0000707", "HP:0000118", "HP:0001507", "HP:0001999"],
    "disorder": ["HP:0000707", "HP:0000118", "HP:0001507", "HP:0001999"],
    "abnormality": ["HP:0000118", "HP:0000707", "HP:0001507", "HP:0001999"],
    "malformation": ["HP:0000118", "HP:0000707", "HP:0001507", "HP:0001999"],
    "dysplasia": ["HP:0009792", "HP:0000118", "HP:0000707", "HP:0001507"],
    "hypoplasia": ["HP:0025615", "HP:0000118", "HP:0000707", "HP:0001507"],
    "stenosis": ["HP:0011025", "HP:0000118", "HP:0000707", "HP:0001507"],
}


STOP_WORDS = {
    'panel', 'gene', 'genes', 'list', 'testing', 'analysis', 
    'version', 'v1', 'v2', 'v3', 'v4', 'v5', 'updated'
}


def fetch_panels(base_url):
    """Fetch list of panels from a PanelApp instance (UK or Australia)"""
    panels = []
    url = f"{base_url}panels/"
    
    try:
        while url:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch panels from {url}, status: {response.status_code}")
                return pd.DataFrame(columns=["id", "name"])
            data = response.json()
            panels.extend(data.get('results', []))
            url = data.get('next')  # For pagination
    except Exception as e:
        logger.error(f"Exception while fetching panels: {e}")
        return pd.DataFrame(columns=["id", "name"])
    
    return pd.DataFrame(panels)

def fetch_panel_genes(base_url, panel_id):
    """Fetch gene list for a specific panel ID with detailed gene information"""
    url = f"{base_url}panels/{panel_id}/"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch panel genes from {url}")
    
    panel_data = response.json()
    genes = panel_data.get("genes", [])
    
    def format_omim_links(omim_list):
        """Format OMIM IDs as clickable links"""
        if not omim_list:
            return ""
        
        links = []
        for omim_id in omim_list:
            if omim_id:
                links.append(f'[{omim_id}](https://omim.org/entry/{omim_id})')
        
        return " | ".join(links) if links else ""
    
    def format_hgnc_link(hgnc_id):
        """Format HGNC ID as clickable link"""
        if not hgnc_id:
            return ""
        
        return f'[{hgnc_id}](https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/{hgnc_id})'
    
    df_genes = pd.DataFrame([
        {
            "gene_symbol": g["gene_data"].get("gene_symbol", ""),
            "omim_id": format_omim_links(g["gene_data"].get("omim_gene", [])),
            "hgnc_id": format_hgnc_link(g["gene_data"].get("hgnc_id", "")),
            "entity_type": g.get("entity_type", ""),
            "biotype": g["gene_data"].get("biotype", ""),
            "mode_of_inheritance": g.get("mode_of_inheritance", ""),
            "confidence_level": g.get("confidence_level"),
            "penetrance": g.get("penetrance"),
            "source": g.get("source"),
        }
        for g in genes
    ])
    
    # Return panel data which includes name, version, and other metadata
    panel_info = {
        "name": panel_data.get("name"),
        "version": panel_data.get("version"),
        "id": panel_data.get("id"),
        "status": panel_data.get("status"),
        "disease_group": panel_data.get("disease_group"),
        "disease_sub_group": panel_data.get("disease_sub_group")
    }
    
    return df_genes, panel_info

@lru_cache(maxsize=200)
def fetch_panel_genes_cached(base_url, panel_id):
    """Cached version of fetch_panel_genes - avoids repeated API calls"""
    try:
        return fetch_panel_genes(base_url, panel_id)
    except Exception as e:
        logger.error(f"Error fetching panel {panel_id}: {e}")
        return pd.DataFrame(), {}

@lru_cache(maxsize=500)
def fetch_hpo_term_details_cached(term_id):
    """Cached version of HPO term fetching"""
    return fetch_hpo_term_details(term_id)

@lru_cache(maxsize=100)
def fetch_panel_disorders_cached(base_url, panel_id):
    """Cached version of panel disorders fetching"""
    return fetch_panel_disorders(base_url, panel_id)

def fetch_panels_parallel(uk_ids=None, au_ids=None, max_workers=5):
    """Fetch multiple panels in parallel instead of sequentially"""
    results = {}
    
    if not uk_ids and not au_ids:
        return results
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_panel = {}
        
        if uk_ids:
            for panel_id in uk_ids:
                future = executor.submit(fetch_panel_genes_cached, PANELAPP_UK_BASE, panel_id)
                future_to_panel[future] = ('UK', panel_id)
        
        if au_ids:
            for panel_id in au_ids:
                future = executor.submit(fetch_panel_genes_cached, PANELAPP_AU_BASE, panel_id)
                future_to_panel[future] = ('AU', panel_id)
        
        for future in concurrent.futures.as_completed(future_to_panel, timeout=30):
            source, panel_id = future_to_panel[future]
            try:
                df, panel_info = future.result()
                results[f"{source}_{panel_id}"] = (df, panel_info)
            except Exception as e:
                logger.error(f"Failed to fetch {source} panel {panel_id}: {e}")
                results[f"{source}_{panel_id}"] = (pd.DataFrame(), {})
    
    return results

def fetch_hpo_terms_parallel(hpo_terms, max_workers=10):
    """Fetch multiple HPO terms in parallel"""
    if not hpo_terms:
        return []
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_term = {
            executor.submit(fetch_hpo_term_details_cached, term_id): term_id 
            for term_id in hpo_terms
        }
        
        for future in concurrent.futures.as_completed(future_to_term, timeout=20):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                term_id = future_to_term[future]
                logger.error(f"Failed to fetch HPO term {term_id}: {e}")
                results.append({
                    "id": term_id,
                    "name": term_id,
                    "definition": "Unable to fetch definition"
                })
    
    return results

def load_internal_panels_from_files(directory_path="data/internal_panels"):
    """Load internal panels directly from .txt files in the specified directory"""
    
    internal_data = []
    panel_info = []
    
    if not os.path.exists(directory_path):
        logger.warning(f"Directory {directory_path} does not exist")
        return pd.DataFrame(), pd.DataFrame()
    
    txt_files = sorted([f for f in os.listdir(directory_path) if f.endswith('.txt')])
    
    def generate_stable_id(filename):
        import hashlib
        
        base_name = filename.replace('.txt', '')
        parts = base_name.split('_')
        
        version_idx = -1
        for i, part in enumerate(parts):
            if part.startswith('v') and part[1:].isdigit():
                version_idx = i
                break
        
        if version_idx == -1:
            panel_name_for_id = base_name
        else:
            if version_idx > 0 and parts[version_idx - 1].isdigit():
                panel_name_parts = parts[:version_idx - 1]
            else:
                panel_name_parts = parts[:version_idx]
            
            panel_name_for_id = '_'.join(panel_name_parts)
        
        hash_obj = hashlib.md5(panel_name_for_id.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        hash_int = int(hash_hex, 16) % 8999 + 2000
        return hash_int
    
    for file_name in txt_files:
        try:
            base_name = file_name.replace('.txt', '')
            parts = base_name.split('_')
            
            version_idx = -1
            for i, part in enumerate(parts):
                if part.startswith('v') and part[1:].isdigit():
                    version_idx = i
                    break
            
            if version_idx == -1:
                logger.warning(f"Could not parse version from {file_name}")
                continue
            
            version = int(parts[version_idx][1:])
            
            if version_idx > 0 and parts[version_idx - 1].isdigit():
                gene_count_from_filename = int(parts[version_idx - 1])
                panel_name_parts = parts[:version_idx - 1]
            else:
                gene_count_from_filename = 0
                panel_name_parts = parts[:version_idx]
            
            panel_name = '_'.join(panel_name_parts)
            panel_id = generate_stable_id(file_name)
            
            file_path = os.path.join(directory_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                genes = [line.strip() for line in f if line.strip()]
            
            actual_gene_count = len(genes)
            
            panel_info.append({
                'panel_id': panel_id,
                'panel_name': panel_name,
                'version': version,
                'gene_count': actual_gene_count,
                'gene_count_filename': gene_count_from_filename,
                'file_name': file_name,
                'base_name': base_name
            })
            
            for gene in genes:
                internal_data.append({
                    'panel_id': panel_id,
                    'panel_name': panel_name,
                    'gene_symbol': gene,
                    'confidence_level': 3  # Default to Green confidence
                })
        
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {e}")
            continue
    
    internal_df = pd.DataFrame(internal_data)
    internal_panels = pd.DataFrame(panel_info).sort_values('panel_id')
    
    return internal_df, internal_panels

def clean_confidence_level_fast(df):
    """Vectorized confidence level cleaning - much faster than original"""
    if 'confidence_level' not in df.columns:
        return df
    
    df = df.copy()
    
    confidence_map = {
        '3': 3, '3.0': 3, 'green': 3, 'high': 3,
        '2': 2, '2.0': 2, 'amber': 2, 'orange': 2, 'medium': 2,
        '1': 1, '1.0': 1, 'red': 1, 'low': 1,
        '0': 0, '0.0': 0, '': 0, 'nan': 0, 'none': 0
    }
    
    df['confidence_level'] = (df['confidence_level']
                            .astype(str)
                            .str.lower()
                            .str.strip()
                            .map(confidence_map)
                            .fillna(0)
                            .astype(int))
    
    return df

def deduplicate_genes_fast(df_all):
    """Fast gene deduplication with proper confidence handling"""
    if df_all.empty:
        return df_all
    
    df_all["confidence_level"] = pd.to_numeric(df_all["confidence_level"], errors='coerce').fillna(0).astype(int)
    
    df_all = df_all[df_all["gene_symbol"].notna() & (df_all["gene_symbol"] != "")]
    
    df_sorted = df_all.sort_values(['confidence_level', 'gene_symbol'], 
                                ascending=[False, True])
    
    df_unique = df_sorted.drop_duplicates(subset=['gene_symbol'], keep='first')
    
    return df_unique.sort_values(['confidence_level', 'gene_symbol'], 
                                ascending=[False, True])

def fetch_panel_disorders(base_url, panel_id):
    """Fetch disorders associated with a panel to extract HPO terms"""
    try:
        base_url = base_url.rstrip('/')
        url = f"{base_url}/panels/{panel_id}/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        relevant_disorders = data.get('relevant_disorders', [])
        
        if not relevant_disorders:
            return []
        
        hpo_terms = []
        
        for disorder in relevant_disorders:
            if isinstance(disorder, str):
                hpo_matches = re.findall(r'HP:\d{7}', disorder)
                hpo_terms.extend(hpo_matches)
        
        hpo_terms = list(dict.fromkeys(hpo_terms))
        
        return hpo_terms
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Panel {panel_id} not found (404)")
        else:
            logger.error(f"HTTP error {e.response.status_code} for panel {panel_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching disorders for panel {panel_id}: {e}")
        return []

def search_hpo_terms(query, limit=100):
    """Search for HPO terms using the JAX ontology API"""
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        url = f"https://ontology.jax.org/api/hp/search?q={query}&page=0&limit={limit}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        options = []
        if 'terms' in data:
            for term in data['terms']:
                label = f"{term.get('name', '')} ({term.get('id', '')})"
                value = term.get('id', '')
                options.append({"label": label, "value": value})
        
        return options
    except Exception as e:
        logger.error(f"Error searching HPO terms: {e}")
        return []

def fetch_hpo_term_details(term_id):
    """Fetch detailed information for an HPO term"""
    try:
        url = f"https://ontology.jax.org/api/hp/terms/{term_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            term_data = response.json()
            return {
                "id": term_id,
                "name": term_data.get("name", term_id),
                "definition": term_data.get("definition", "No definition available")
            }
        else:
            return {
                "id": term_id,
                "name": term_id,
                "definition": "Unable to fetch definition"
            }
    except Exception as e:
        return {
            "id": term_id,
            "name": term_id,
            "definition": "Unable to fetch definition"
        }

def get_hpo_terms_from_panels(uk_ids=None, au_ids=None):
    """Extract HPO terms from Australia panels"""
    all_hpo_terms = set() 
    if au_ids:
        for panel_id in au_ids:
            hpo_terms = fetch_panel_disorders_cached(PANELAPP_AU_BASE, panel_id)
            all_hpo_terms.update(hpo_terms)
    
    return list(all_hpo_terms)

def create_upset_plot(gene_sets, panel_names):
    """Create an UpSet plot for visualizing intersections of multiple sets"""
    from itertools import combinations, chain
    
    all_genes = set()
    for genes in gene_sets.values():
        all_genes.update(genes)
    
    if not all_genes:
        return None
    
    gene_memberships = {}
    sets_list = list(gene_sets.keys())
    
    for gene in all_genes:
        membership = tuple(i for i, (name, genes) in enumerate(gene_sets.items()) if gene in genes)
        if membership not in gene_memberships:
            gene_memberships[membership] = []
        gene_memberships[membership].append(gene)
    
    single_sets = []
    multi_sets = []
    
    for membership, genes in gene_memberships.items():
        if len(membership) == 1:
            single_sets.append((membership, genes))
        else:
            multi_sets.append((membership, genes))
    
    single_sets.sort(key=lambda x: len(x[1]), reverse=True)
    multi_sets.sort(key=lambda x: len(x[1]), reverse=True)
    
    sorted_intersections = single_sets + multi_sets
    max_intersections = min(15, len(sorted_intersections))
    sorted_intersections = sorted_intersections[:max_intersections]
    
    num_intersections = len(sorted_intersections)
    num_sets = len(sets_list)
    figure_height = 5
    dpi = 180

    if num_intersections <= 6:
        figure_width = 6.5
    elif num_intersections <= 10:
        figure_width = 8.5
    else:
        figure_width = 10
    
    fig, (ax_bars, ax_matrix) = plt.subplots(2, 1, figsize=(figure_width, figure_height), dpi=dpi,
                                        gridspec_kw={'height_ratios': [1, 1]})
    
    if num_intersections <= 6:
        bar_width = 0.8
        title_fontsize = 14
        label_fontsize = 12
        value_fontsize = 10
        ytick_fontsize = 10
    elif num_intersections <= 10:
        bar_width = 0.7
        title_fontsize = 13
        label_fontsize = 11
        value_fontsize = 9
        ytick_fontsize = 9
    else:
        bar_width = 0.6
        title_fontsize = 12
        label_fontsize = 10
        value_fontsize = 8
        ytick_fontsize = 8
    
    intersection_sizes = [len(genes) for _, genes in sorted_intersections]
    x_pos = np.arange(len(intersection_sizes))
    
    bar_colors = []
    for membership, _ in sorted_intersections:
        if len(membership) == 1:
            bar_colors.append('#3498db')
        else:
            bar_colors.append('#2c3e50')
    
    bars = ax_bars.bar(x_pos, intersection_sizes, color=bar_colors, alpha=0.8, width=bar_width,
                    edgecolor='white', linewidth=1)
    
    ax_bars.set_ylabel('Number of Genes', fontsize=label_fontsize, fontweight='bold')
    ax_bars.set_title('Gene Panel Intersections', fontsize=title_fontsize, fontweight='bold', pad=20)
    ax_bars.set_xticks([])
    ax_bars.grid(True, alpha=0.3, axis='y')
    ax_bars.spines['top'].set_visible(False)
    ax_bars.spines['right'].set_visible(False)
    ax_bars.set_xlim(-0.5, len(sorted_intersections) - 0.5)
    
    max_height = max(intersection_sizes) if intersection_sizes else 1
    for i, (bar, size) in enumerate(zip(bars, intersection_sizes)):
        ax_bars.text(i, bar.get_height() + max_height * 0.01, 
                    str(size), ha='center', va='bottom', fontweight='bold', 
                    fontsize=value_fontsize)
    
    matrix_data = np.zeros((len(sets_list), len(sorted_intersections)))
    for j, (membership, _) in enumerate(sorted_intersections):
        for i in membership:
            matrix_data[i, j] = 1
    
    ax_matrix.clear()
    ax_matrix.set_xlim(-0.5, len(sorted_intersections) - 0.5)
    ax_matrix.set_ylim(-0.5, len(sets_list) - 0.5)
    
    circle_radius = 0.1
    line_width = 2.0
    
    for i in range(len(sets_list)):
        for j in range(len(sorted_intersections)):
            x_center = float(j)
            y_center = float(i)
            
            if matrix_data[i, j] == 1:
                circle = plt.Circle((x_center, y_center), circle_radius, 
                                color='black', zorder=2, clip_on=False)
                ax_matrix.add_patch(circle)
            else:
                empty_radius = circle_radius * 0.8
                circle = plt.Circle((x_center, y_center), empty_radius, 
                                fill=False, color='lightgray', 
                                linewidth=0.8, alpha=0.5, zorder=2, clip_on=False)
                ax_matrix.add_patch(circle)
    
    for j in range(len(sorted_intersections)):
        connected = [k for k in range(len(sets_list)) if matrix_data[k, j] == 1]
        if len(connected) > 1:
            min_y, max_y = min(connected), max(connected)
            x_line = float(j)
            ax_matrix.plot([x_line, x_line], [min_y, max_y], 'k-', linewidth=line_width, 
                        alpha=0.95, zorder=1, solid_capstyle='round')
    
    display_names = []
    for name in sets_list:
        set_size = len(gene_sets[name])
        
        if name == "Manual":
            display_names.append(f"Manual ({set_size})")
        elif name.startswith("UK_"):
            panel_id = name.replace("UK_", "")
            display_names.append(f"UK_{panel_id} ({set_size})")
        elif name.startswith("AUS_"):
            panel_id = name.replace("AUS_", "")
            display_names.append(f"AUS_{panel_id} ({set_size})")
        elif name.startswith("INT-"):
            panel_id = name.replace("INT-", "")
            display_names.append(f"INT_{panel_id} ({set_size})")
        else:
            display_names.append(f"{name} ({set_size})")
    
    ax_matrix.set_yticks(range(len(sets_list)))
    ax_matrix.set_yticklabels(display_names, fontsize=ytick_fontsize)
    ax_matrix.set_xticks([])
    ax_matrix.set_xlabel('')
    
    ax_matrix.grid(False)
    for spine in ax_matrix.spines.values():
        spine.set_visible(False)
    
    ax_matrix.invert_yaxis()
    
    if num_intersections <= 10:
        pad = 1.8
    else:
        pad = 1.2
    
    plt.tight_layout(pad=pad)
    ax_matrix.set_facecolor('white')
    ax_bars.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    return fig

def panel_options(df):
    """Generate options for panel dropdowns"""
    options = []
    for _, row in df.iterrows():
        version_text = f" v{row['version']}" if 'version' in row and pd.notna(row['version']) else ""
        label = f"{row['name']}{version_text} (ID {row['id']})"
        options.append({"label": label, "value": row["id"]})
    return options

def internal_options(df):
    """Generate options for internal panel dropdowns"""
    options = []
    for _, row in df.iterrows():
        version_text = f" v{row['version']}" if 'version' in row and pd.notna(row['version']) else ""
        display_name = row['panel_name'].replace('_', ' ')
        label = f"{display_name}{version_text} (ID {row['panel_id']})"
        options.append({"label": label, "value": row["panel_id"]})
    return options

def generate_panel_summary(uk_ids, au_ids, internal_ids, confs, manual_genes_list, panels_uk_df, panels_au_df, internal_panels):
    """Generate a formatted summary of panels and genes"""
    summary_parts = []
    
    def get_confidence_notation(conf_list):
        if not conf_list:
            return ""
        conf_set = set(conf_list)
        if conf_set == {3}:
            return "_G"
        elif conf_set == {2}:
            return "_O"  
        elif conf_set == {1}:
            return "_R"
        elif conf_set == {3, 2}:
            return "_GO"
        elif conf_set == {3, 1}:
            return "_GR"
        elif conf_set == {2, 1}:
            return "_OR"
        elif conf_set == {3, 2, 1}:
            return "_GOR"
        else:
            return ""
    
    confidence_suffix = get_confidence_notation(confs)
    
    # Process UK panels
    if uk_ids:
        for panel_id in uk_ids:
            panel_row = panels_uk_df[panels_uk_df['id'] == panel_id]
            if not panel_row.empty:
                panel_info = panel_row.iloc[0]
                panel_name = panel_info['name'].replace(' ', '_').replace('/', '_').replace(',', '_')
                version = f"_v{panel_info['version']}" if pd.notna(panel_info.get('version')) else ""
                summary_parts.append(f"PanelApp_UK({panel_id})/{panel_name}{version}{confidence_suffix}")
    
    # Process AU panels
    if au_ids:
        for panel_id in au_ids:
            panel_row = panels_au_df[panels_au_df['id'] == panel_id]
            if not panel_row.empty:
                panel_info = panel_row.iloc[0]
                panel_name = panel_info['name'].replace(' ', '_').replace('/', '_').replace(',', '_')
                version = f"_v{panel_info['version']}" if pd.notna(panel_info.get('version')) else ""
                summary_parts.append(f"PanelApp_AUS({panel_id})/{panel_name}{version}{confidence_suffix}")
    
    # Process Internal panels
    if internal_ids:
        for panel_id in internal_ids:
            panel_row = internal_panels[internal_panels['panel_id'] == panel_id]
            if not panel_row.empty:
                panel_info = panel_row.iloc[0]
                base_name = panel_info.get('base_name', panel_info['panel_name'])
                summary_parts.append(f"Panel_HUG/{base_name}")
    
    # Add manual genes
    if manual_genes_list:
        summary_parts.extend(manual_genes_list)
    
    return ",".join(summary_parts)

def extract_medical_keywords_enhanced(panel_names):
    """
    Version améliorée de l'extraction de mots-clés médicaux
    """
    if not panel_names:
        return []
    
    keywords = []
    keyword_scores = {}
    
    for name in panel_names:
        if not name:
            continue
        
        # Nettoyage et normalisation
        cleaned_name = name.lower().strip()
        
        # Remplacer les caractères spéciaux par des espaces
        cleaned_name = re.sub(r'[_\-/,;:()&]', ' ', cleaned_name)
        
        # Extraire les mots significatifs
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_name)
        
        # Traitement des mots
        for word in words:
            if (word not in STOP_WORDS and 
                len(word) >= 3 and 
                not word.isdigit() and
                not re.match(r'^v\d+$', word)):  # Éviter les versions
                
                # Calculer un score basé sur la fréquence et la pertinence
                score = 1
                
                # Bonus si le mot est dans notre mapping médical
                if word in MEDICAL_TO_HPO_MAPPING:
                    score += 5
                
                # Bonus pour les mots plus longs (souvent plus spécifiques)
                if len(word) >= 6:
                    score += 1
                
                # Accumuler les scores
                if word not in keyword_scores:
                    keyword_scores[word] = 0
                keyword_scores[word] += score
    
    # Trier par score décroissant
    sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Extraire les mots-clés avec les meilleurs scores
    keywords = [word for word, score in sorted_keywords if score >= 2]
    
    return keywords[:8]  # Limiter à 8 mots-clés maximum

@lru_cache(maxsize=100)
def search_hpo_with_fallback(query, max_results=4):  
    """
    Recherche HPO avec système de fallback amélioré
    """
    results = []
    
    try:
        # 1. Essayer d'abord notre mapping direct
        query_lower = query.lower()
        if query_lower in MEDICAL_TO_HPO_MAPPING:
            # ← CHANGÉ: Ne plus limiter les résultats du mapping direct
            mapped_hpo_ids = MEDICAL_TO_HPO_MAPPING[query_lower]  # Prendre TOUS les HPO du mapping
            for hpo_id in mapped_hpo_ids[:max_results]:  # Limiter seulement après
                try:
                    details = fetch_hpo_term_details_cached(hpo_id)
                    if details and details.get('name'):
                        results.append({
                            'value': hpo_id,
                            'label': f"{details['name']} ({hpo_id})",
                            'keyword': query,
                            'source': 'mapping',
                            'relevance': 10
                        })
                except:
                    continue
        
        # 2. Si pas assez de résultats, chercher via API
        if len(results) < max_results:
            try:
                api_results = search_hpo_via_api(query, max_results - len(results))
                for result in api_results:
                    # Éviter les doublons
                    if not any(r['value'] == result['value'] for r in results):
                        result['source'] = 'api'
                        result['relevance'] = 7
                        results.append(result)
            except Exception as e:
                logger.warning(f"API HPO search failed for '{query}': {e}")
        
        # 3. Si toujours pas assez, essayer des variations du mot
        if len(results) < max_results:
            variations = generate_query_variations(query)
            for variation in variations[:2]:  # Limiter à 2 variations
                try:
                    var_results = search_hpo_via_api(variation, 1)
                    for result in var_results:
                        if not any(r['value'] == result['value'] for r in results):
                            result['source'] = 'variation'
                            result['relevance'] = 5
                            results.append(result)
                            if len(results) >= max_results:
                                break
                except:
                    continue
                
                if len(results) >= max_results:
                    break
    
    except Exception as e:
        logger.error(f"Error in enhanced HPO search for '{query}': {e}")
    
    # Trier par pertinence
    results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
    return results[:max_results]

def search_hpo_via_api(query, limit=5):
    """
    Recherche HPO via l'API JAX avec gestion d'erreurs améliorée
    """
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        url = f"https://ontology.jax.org/api/hp/search"
        params = {
            'q': query.strip(),
            'page': 0,
            'limit': min(limit, 10)
        }
        
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        if 'terms' in data and data['terms']:
            for term in data['terms'][:limit]:
                hpo_id = term.get('id', '')
                hpo_name = term.get('name', '')
                
                if hpo_id and hpo_name:
                    results.append({
                        'value': hpo_id,
                        'label': f"{hpo_name} ({hpo_id})",
                        'keyword': query
                    })
        
        return results
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"HPO API request failed for '{query}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in HPO API search for '{query}': {e}")
        return []

def generate_query_variations(query):
    """
    Génère des variations d'un terme de recherche pour améliorer les résultats HPO
    """
    variations = []
    
    # Version singulier/pluriel
    if query.endswith('s') and len(query) > 4:
        variations.append(query[:-1])  # Retirer le 's'
    elif not query.endswith('s'):
        variations.append(query + 's')  # Ajouter un 's'
    
    # Variations communes de terminaisons médicales
    medical_variants = {
        'ic': ['ical', 'y'],  # cardiac -> cardiacal, cardiacu
        'al': ['ic'],         # neural -> neuric
        'ism': ['tic'],       # metabolism -> metabolic
        'ity': ['ic'],        # spasticity -> spastic
        'osis': ['otic'],     # neurosis -> neurotic
        'pathy': ['pathic'],  # neuropathy -> neuropathic
    }
    
    for suffix, replacements in medical_variants.items():
        if query.endswith(suffix):
            base = query[:-len(suffix)]
            for replacement in replacements:
                variations.append(base + replacement)
    
    return variations

@lru_cache(maxsize=100)
def search_hpo_database_dynamic(query, max_results=50):  # ← CHANGÉ: 12 → 50
    """
    Recherche dynamique dans la base HPO - VERSION COMPLÈTE
    """
    if not query or len(query.strip()) < 2:
        return []
    
    results = []
    seen_ids = set()
    
    try:
        # 1. Chercher avec BEAUCOUP plus de résultats
        url = f"https://ontology.jax.org/api/hp/search"
        params = {
            'q': query.strip(),
            'page': 0,
            'limit': 100  # ← CHANGÉ: Demander 100 résultats au lieu de 17
        }
        
        response = requests.get(url, params=params, timeout=10)  # Plus de temps
        if response.status_code == 200:
            data = response.json()
            
            if 'terms' in data and data['terms']:
                print(f"🔍 API returned {len(data['terms'])} terms for '{query}'")
                
                for term in data['terms']:
                    hpo_id = term.get('id', '')
                    hpo_name = term.get('name', '')
                    
                    if hpo_id and hpo_name and hpo_id not in seen_ids:
                        results.append({
                            'value': hpo_id,
                            'label': f"{hpo_name} ({hpo_id})",
                            'keyword': query,
                            'source': 'database'
                        })
                        seen_ids.add(hpo_id)
        
        # 2. Si l'API a une limite, essayer plusieurs pages
        if len(results) >= 50:  # Si on a atteint la limite d'une page
            try:
                # Essayer page 2
                params['page'] = 1
                response2 = requests.get(url, params=params, timeout=10)
                if response2.status_code == 200:
                    data2 = response2.json()
                    if 'terms' in data2 and data2['terms']:
                        for term in data2['terms']:
                            hpo_id = term.get('id', '')
                            hpo_name = term.get('name', '')
                            
                            if hpo_id and hpo_name and hpo_id not in seen_ids:
                                results.append({
                                    'value': hpo_id,
                                    'label': f"{hpo_name} ({hpo_id})",
                                    'keyword': query,
                                    'source': 'database'
                                })
                                seen_ids.add(hpo_id)
            except:
                pass  # Page 2 optionnelle
        
        print(f"✅ Database search found {len(results)} total results for '{query}'")
        
    except Exception as e:
        logger.warning(f"Database HPO search failed for '{query}': {e}")
    
    return results[:max_results]  # Retourner jusqu'à 50 résultats

def search_hpo_terms_by_keywords(keywords, max_per_keyword=8, exclude_hpo_ids=None):
    """
    VERSION COMPLÈTE - Récupère TOUS les termes disponibles
    exclude_hpo_ids: set d'IDs HPO à exclure (pour éviter les doublons avec auto-générés)
    """
    print(f"🚀 FUNCTION CALLED - search_hpo_terms_by_keywords with keywords: {keywords}")
    print(f"🚫 Excluding HPO IDs: {exclude_hpo_ids}")
    
    if not keywords:
        return []
    
    exclude_hpo_ids = exclude_hpo_ids or set()
    logger.info(f"🔍 Complete HPO search for keywords: {keywords}")
    logger.info(f"🚫 Excluding {len(exclude_hpo_ids)} auto-generated HPO terms")
    
    suggested_hpo_terms = []
    processed_hpo_ids = set()
    
    for keyword in keywords[:6]:  # Traiter max 6 mots-clés
        try:
            keyword_results = []
            
            # ÉTAPE 1: D'abord chercher dans notre dictionnaire
            query_lower = keyword.lower()
            if query_lower in MEDICAL_TO_HPO_MAPPING:
                mapped_hpo_ids = MEDICAL_TO_HPO_MAPPING[query_lower]
                
                for hpo_id in mapped_hpo_ids:
                    # AJOUT: Vérifier si l'HPO n'est pas dans les exclusions
                    if hpo_id in exclude_hpo_ids:
                        print(f"🚫 Skipping auto-generated HPO: {hpo_id}")
                        continue
                        
                    try:
                        details = fetch_hpo_term_details_cached(hpo_id)
                        if details and details.get('name'):
                            keyword_results.append({
                                'value': hpo_id,
                                'label': f"{details['name']} ({hpo_id})",
                                'keyword': keyword,
                                'source': 'mapping',
                                'relevance': 10
                            })
                    except:
                        continue
            
            # ÉTAPE 2: Chercher dans la base de données TOUS les résultats
            try:
                database_results = search_hpo_database_dynamic(keyword, max_results=50)
                
                for result in database_results:
                    hpo_id = result['value']
                    
                    # AJOUT: Vérifier si l'HPO n'est pas dans les exclusions
                    if hpo_id in exclude_hpo_ids:
                        print(f"🚫 Skipping auto-generated HPO from database: {hpo_id}")
                        continue
                    
                    # Éviter les doublons avec le dictionnaire
                    if not any(r['value'] == hpo_id for r in keyword_results):
                        result['relevance'] = 7
                        keyword_results.append(result)
            except Exception as e:
                logger.warning(f"Database search failed for '{keyword}': {e}")
            
            print(f"📊 Keyword '{keyword}': {len(keyword_results)} total results (after exclusions)")
            
            # Ajouter les résultats uniques à la liste finale
            for result in keyword_results:
                hpo_id = result['value']
                if hpo_id not in processed_hpo_ids:
                    processed_hpo_ids.add(hpo_id)
                    suggested_hpo_terms.append(result)
        
        except Exception as e:
            logger.error(f"Error processing keyword '{keyword}': {e}")
            continue
    
    # Trier par pertinence (dictionnaire d'abord, puis base de données)
    suggested_hpo_terms.sort(key=lambda x: (
        x.get('relevance', 0),
        -len(x.get('keyword', ''))
    ), reverse=True)
    
    print(f"✅ TOTAL FINAL: {len(suggested_hpo_terms)} HPO suggestions (after exclusions)")
    logger.info(f"✅ Found {len(suggested_hpo_terms)} HPO suggestions (mapping + database, after exclusions)")
    
    return suggested_hpo_terms
#def search_hpo_terms_by_keywords_enhanced(keywords, max_per_keyword=4):  # ← CHANGÉ: 2 → 4
    """
    Version améliorée de la recherche HPO basée sur les mots-clés
    """
    if not keywords:
        return []
    
    logger.info(f"🔍 Searching HPO terms for keywords: {keywords}")
    
    suggested_hpo_terms = []
    processed_hpo_ids = set()
    
    # Traiter chaque mot-clé
    for keyword in keywords[:6]:  # Limiter à 6 mots-clés pour éviter trop d'appels API
        try:
            # Utiliser notre fonction améliorée avec plus de résultats
            keyword_results = search_hpo_with_fallback(keyword, max_per_keyword)
            
            for result in keyword_results:
                hpo_id = result['value']
                
                # Éviter les doublons
                if hpo_id not in processed_hpo_ids:
                    processed_hpo_ids.add(hpo_id)
                    suggested_hpo_terms.append(result)
        
        except Exception as e:
            logger.error(f"Error processing keyword '{keyword}': {e}")
            continue
    
    # Trier par pertinence (les résultats du mapping direct en premier)
    suggested_hpo_terms.sort(key=lambda x: (
        x.get('relevance', 0),
        -len(x.get('keyword', ''))  # Préférer les mots-clés plus longs
    ), reverse=True)
    
    logger.info(f"✅ Found {len(suggested_hpo_terms)} HPO suggestions")
    
    return suggested_hpo_terms[:12]  # ← CHANGÉ: 8 → 12 pour permettre plus de suggestions =============================================================================

def extract_keywords_from_panel_names(panel_names):
    """
    Version mise à jour qui utilise le système amélioré
    """
    return extract_medical_keywords_enhanced(panel_names)

#def search_hpo_terms_by_keywords(keywords, max_per_keyword=4):
    """
    Version mise à jour qui utilise le système amélioré
    """
    return search_hpo_terms_by_keywords_enhanced(keywords, max_per_keyword)

def validate_hpo_suggestions(panel_names, suggested_hpo_terms):
    """
    Fonction pour valider la qualité des suggestions HPO
    """
    if not panel_names or not suggested_hpo_terms:
        return {"score": 0, "details": "No data to validate"}
    
    validation_score = 0
    details = []
    
    # Extraire les mots-clés des panels
    keywords = extract_medical_keywords_enhanced(panel_names)
    
    for suggestion in suggested_hpo_terms:
        hpo_name = suggestion.get('label', '').lower()
        keyword = suggestion.get('keyword', '').lower()
        
        # Points si le mot-clé apparaît dans le nom HPO
        if keyword in hpo_name:
            validation_score += 2
            details.append(f"✓ '{keyword}' found in '{hpo_name}'")
        
        # Points si c'est un mapping direct
        if suggestion.get('source') == 'mapping':
            validation_score += 3
            details.append(f"✓ Direct mapping for '{keyword}'")
    
    return {
        "score": validation_score,
        "max_possible": len(suggested_hpo_terms) * 3,
        "percentage": (validation_score / max(len(suggested_hpo_terms) * 3, 1)) * 100,
        "details": details
    }

def get_panel_names_from_selections(uk_ids, au_ids, internal_ids, panels_uk_df, panels_au_df, internal_panels):
    """Extract panel names from current selections for keyword analysis"""
    panel_names = []
    
    # UK panels
    if uk_ids and panels_uk_df is not None:
        for panel_id in uk_ids:
            panel_row = panels_uk_df[panels_uk_df['id'] == panel_id]
            if not panel_row.empty:
                panel_names.append(panel_row.iloc[0]['name'])
    
    # AU panels
    if au_ids and panels_au_df is not None:
        for panel_id in au_ids:
            panel_row = panels_au_df[panels_au_df['id'] == panel_id]
            if not panel_row.empty:
                panel_names.append(panel_row.iloc[0]['name'])
    
    # Internal panels
    if internal_ids and internal_panels is not None:
        for panel_id in internal_ids:
            panel_row = internal_panels[internal_panels['panel_id'] == panel_id]
            if not panel_row.empty:
                panel_names.append(panel_row.iloc[0]['panel_name'].replace('_', ' '))
    
    return panel_names