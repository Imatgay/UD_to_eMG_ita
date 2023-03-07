import pyconll
import json
import argparse

lemma_info = []

parser = argparse.ArgumentParser(description='Convert a CoNLL-U file to eMG lexicon. Language: it.')
parser.add_argument('-i', '--input', type=str, help='Input CoNLL-U file name', required=True)
args = parser.parse_args()
file_name = args.input

sentences = pyconll.load_from_file(file_name)

root_token = pyconll.unit.token.Token('0\troot\t_\tROOT\t_\t_\t0\t_\t_\t_', True) #creazione di un token ROOT, primo elemento di ogni token_dict, per gestire i token.head = 0

#####################################################################################à
#################################################################### Definiamo alcune funzioni

def get_subject_id(token, token_dict, original_dict):     ##funzione per risalire a id del soggetto, sulla base dei diversi tipi di verbi. Da implementare i rapporti con i verbi di tempo non finito
    subj_id = [] 
    if get_verb_type(token) == 'verb_fin':        
        for x in token_dict.values():
            if x is None:
                continue
            if get_original_head(x, original_dict) == token.id:
                if x.deprel == 'nsubj':
                    subj_id.append(x.id)
                    return subj_id
                elif x.deprel == 'expl:impers':
                    subj_id.append('0')
                    return subj_id
                elif x.deprel == 'nsubj:pass':
                    subj_id.append(token_dict[x.id])
                    return subj_id
                elif x.deprel == 'expl':
                    for y in token_dict.values():
                        if y.deprel == 'nsubj' and original_dict[y.id] == token.id:
                            subj_id.append(token_dict[y.id])
                            return subj_id
                        else:
                            continue
                        
    elif get_verb_type(token) == 'aux_copula':
        for x in token_dict.values():
            if x.deprel == 'nsubj' and original_dict[x.id] == original_dict[token.id]:
                subj_id.append(token_dict[x.id])
                return subj_id
    elif get_verb_type(token) == 'aux_modal':
        for x in token_dict.values():
            if x.deprel == 'nsubj' and original_dict[x.id] == original_head:
                subj_id.append(x.id)
                return subj_id
    elif get_verb_type(token) == 'aux_tense':
        for x in token_dict.values():
            if x.deprel in ['nsubj','root'] and original_dict[x.id] == original_dict[token.id]:
                subj_id.append(x.id)
                return subj_id
    elif get_verb_type(token) == 'aux_pass':
        for x in token_dict.values():
            if x.upos == 'VERB':
                subj_id.append(token_dict[original_dict[original_head]].id)
                return subj_id
    return None

    
def get_verb_type(token): ###funzione per determinare il tipo di verbo
    aux_copula = 'aux_copula'
    aux_tense = 'aux_tense'
    aux_modal = 'aux_modal'
    aux_pass = 'aux_pass'
    verb_inf = 'verb_inf'
    verb_ger = 'verb_ger'
    verb_part = 'verb_part'
    verb_fin = 'verb_fin'
    if token.upos not in ['AUX','VERB']:
        return ''
    if token.upos == 'AUX':
        if token.deprel == 'cop':
            return aux_copula
        elif token.deprel == 'aux':
            if token.lemma in ['essere','avere']:
                return aux_tense
            else: 
                return aux_modal           
        elif token.deprel == 'aux:pass':
            return aux_pass
    else:
        if 'VerbForm' in token.feats and 'Fin' in token.feats['VerbForm']:
            return verb_fin
        elif 'VerbForm' in token.feats and 'Inf' in token.feats['VerbForm']:
            return verb_inf
        elif 'VerbForm' in token.feats and 'Ger' in token.feats['VerbForm']:
            return verb_ger
        elif 'VerbForm' in token.feats and 'Part' in token.feats['VerbForm']:
            return verb_part
                    
def extract_feats(token):    ### funzione per estrarre le feats necessarie per popolare il campo agree dell'output
    if 'Number' in token.feats and 'Person' in token.feats:
        number = list(token.feats['Number'])[0]
        person = list(token.feats['Person'])[0]
        return f"{number[0].lower()}.{person.lower()}"
    elif 'Gender' in token.feats and 'Number' in token.feats:
        gender = list(token.feats['Gender'])[0]
        number = list(token.feats['Number'])[0]
        return f"{number[0].lower()}.{gender[0].lower()}"
    elif 'Gender' in token.feats and 'Number' not in token.feats:
        gender = list(token.feats['Gender'])[0]
        return f"{gender[0].lower()}."
    elif 'Number' in token.feats and 'Gender' not in token.feats:
        number = list(token.feats['Number'])[0]
        return f"{number[0].lower()}."
    else:
        return""

def get_children(father, token_dict):  ###funzione per individuare tutti i token che nella treebank originaria dipendono dal token corrente (father)
    children = []
    for token in token_dict.values():
        if father.id == token.head:
            children.append(token)
    return children

def get_original_head(token, original_dict):   ###funzione per individuare la head originaria (= il suo id) del token, senza accedere al token_dict (in cui le dipendenze sono sovrascritte)
    original_head = original_dict[token.id]
    return original_head
###########################################################################################
###########################################################  Passiamo all'analisi delle frasi
for sentence in sentences: 
    original_dict = {'0':''}  ###dizionario che sarà popolato con coppie token.id : token.head 
    token_dict = {'0':root_token} ###dizionario che sarà popolato con coppie 'n':token (la chiave n sarà sempre uguale al token.id), su cui saranno rivalutate le dipendenze
    expect = []  ### inizializzazione dizionario utile per poi popolare il campo 'expect' dell'output
    
    for token in sentence:
        if '-' in token.id: ###non inserire multiwords (es. preposizioni articolate) in token_dict 
            continue
        token_dict[token.id] = token ### popoliamo il token_dict
        original_dict[token.id] = token.head ###popoliamo l'original_dict
    
    for token in token_dict.values():
        if token.form == 'root': 
            continue
        original_head = get_original_head(token, original_dict) ### inizializziamo per ogni token la sua original_head, tranne che per il token root
        
  ########################
  ########################  APPLICAZIONE DI UNA SERIE DI REGOLE PER RIVALUTARE LE DIPENDEZE NELLA PROSPETTIVA DEL CAMPO EXPECT DELL'OUTPUT
        
        ## rapport ausiliare/VERB: AUX seleziona il proprio verbo di riferimento, non il contrario
      
        if token.upos == 'AUX' and token_dict[original_head].upos == 'VERB':
            token_dict[original_head].head = token.id
            
        ##verbi composti (regola 'lineare')
        
        if token.upos == 'AUX' and str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)+1)].upos == 'AUX':
            token_dict[str(int(token.id)+1)].head = token.id
            
        ### costruzioni passive: rivalutare l'ausiliare come selezionato dal soggetto 
        if token.deprel == 'aux:pass':
            for x in token_dict.values():
                if x.deprel == 'nsubj:pass' and original_dict[x.id] == original_dict[token.id]: #se è una costruzione verbale composta (aux+aux+part), bisogna considerare il primo aux
                    if str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)-1)].upos == 'AUX':
                        token_dict[str(int(token.id)-1)].head = x.id
                      
                    else: #per le costruzioni passive semplici (aux + part)
                     token_dict[token.id].head = x.id
        
        ##costruzioni copulari
        if token.deprel == 'cop':
            token_dict[original_head].head = token.id
            for x in token_dict.values():
                subj = False
                if x.deprel == 'nsubj' and original_dict[x.id] == original_dict[token.id]:
                    subj = True
                    complex_verb_construction= False
                    if token_dict[str(int(token.id)-1)].upos != 'AUX':
                        complex_verb_construction= True
                        token_dict[token.id].head = x.id
                    else:
                        token_dict[str(int(token.id)-1)].head = x.id        
        
        #costruzioni come "caso di pensare"
        if token.upos == 'VERB' and token.deprel == 'acl' and token_dict[original_head].upos == 'NOUN':
            for x in token_dict.values():
                if x.deprel == 'mark' and original_dict[x.id] == token.id:
                    token_dict[token.id].head = x.id
                    token_dict[x.id].head = original_dict[token.id]                
        
        #il verbo seleziona il det o l'adp successivo ????? 
        if token.upos in ['AUX','VERB'] and str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)+1)].upos in ['DET','ADP']:
            token_dict[str(int(token.id)+1)].head = token.id

        #se ci sono due det in sequenza, il primo seleziona il secondo
        if token.upos == 'DET' and str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)+1)].upos == 'DET':
            token_dict[str(int(token.id)+1)].head = token.id

        #è il det a selezionare il noun,pron,propn
        if token.upos == 'DET':
            if token_dict[original_head].upos in ['PROPN','PRON','NOUN']:
                token_dict[original_head].head = token.id 
            elif token_dict[original_head].upos not in ['PROPN','PRON','NOUN']: ##per eventuali situazioni come numerali (numerale selezionato non direttamente da det)
                r = token_dict[original_head].head
                if token_dict[r].upos in ['PROPN','PRON','NOUN']:
                    token_dict[r].head = token.id
                    

        #preposizioni e nomi (se è preposizione con case e la sua original head è posizionata dopo nella frase, l'ADP la seleziona)
        if token.upos == 'ADP' and token.deprel == 'case':
            if int(original_dict[token.id]) > int(token.id):
                token_dict[original_head].head = token.id
                
        #trattamento preposizioni articolate                
        if token.upos == 'ADP' and str(int(token.id)+1) in token_dict and 'DET' in token_dict[str(int(token.id)+1)].upos:
            token_dict[str(int(token.id)+1)].head = token.id
            prev_token = False
            
            #e di rapporto token/proposizione articolata con case/fixed (la seleziona sempre)
            
            if token.deprel in ['case','fixed'] and str(int(token.id)-1) in token_dict and token_dict[str(int(token.id)-1)].upos != 'ADJ':
                prev_token = True
                token_dict[token.id].head = token_dict[str(int(token.id)-1)].id

        #fare dipendere pronomi relativi da "antecedenti"
        if token.upos == 'PRON' and ('PronType' in token.feats and 'Rel' in token.feats['PronType']):
            s = original_dict[original_head]
            if s != '':
                token_dict[token.id].head = token_dict[s].id
                if token_dict[original_head].upos in ['AUX','VERB']: ###e il VERB o l'AUX della relativa dal PronRel
                    token_dict[original_head].head = token.id
                else:
                    continue
            
                
        #gestione di introduzione di subordinate
        if token.deprel == 'mark':
            
            if token.upos == 'ADP':  ### introdotte da adp
                if get_verb_type(token_dict[original_head]) == 'verb_inf': #preposizione è head di verbo all'infinito
                    token_dict[original_head].head = token.id
                
            elif token.upos == 'ADV':  ### introdotte da avverbi 
                if str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)+1)].deprel == 'fixed':
                    token_dict[str(int(token.id)+1)].head = token.id
                    token_dict[original_head].head = token_dict[str(int(token.id)+1)].id ##original head è sempre il verbo della subordinata
                
            elif token.upos == 'SCONJ':     ### introdotte da coniugazioni subordinanti
                r = token_dict[original_head].head                
                token_dict[token.id].head = token_dict[r].id
                token_dict[original_head].head = token.id
                for x in token_dict.values():
                    if x.deprel == 'nsubj' and original_dict[x.id] == original_dict[token.id]:
                        for y in token_dict.values():
                            if y.upos == 'DET' and original_dict[y.id] == x.id:
                                token_dict[y.id].head = token.id
                            else:
                                token_dict[x.id].head = token.id

    # rapporto soggeto/verbo   
        if token.upos in ['AUX','VERB']:
            subj_id = get_subject_id(token,token_dict, original_dict)
            if subj_id is not None:
                token_dict[token.id].head = subj_id[0]

    #rapporto verbo/oggetto introdotto da det (il verbo seleziona il det) 
        if token.deprel == 'obj':
            for x in token_dict.values():
                if x.upos == 'DET' and original_dict[x.id] == token.id:
                    token_dict[x.id].head = original_dict[token.id]
 ###############################################################################
 ###############################################################################
 ###############################################################################     
 ###### Dopo le rivalutazioni delle dipendenze, sovrascritte nei token che sono i value nel token_dict, estraiamo il campo expect per ogni token
    for token in sentence:
        expect_dict = {}  #inizializziamo il dizionario per gli elementi 'expect'
        children = get_children(token, token_dict) #individuiamo i children di ogni token lavorando sul token_dict
        for child in children:
            expect_dict[len(expect_dict)] = child.upos   ###aggiungiamo ogni children come valore nell'expect_dict, con chiave crescente da 0 a len(expect_dict)
        expect.append(expect_dict) ### aggiungiamo l'expect_dict nella lista expect[] inizializzata prima, a livello della sentence

        # inseriamo i dati estratti e rilevanti in lemma_info (lista unica inizializzata a inizio programma da cui attingeremo per produrre l'output)
        lemma_info.append(
            [
                token.form,
                {
                    'label': [{str(0): token.upos}],
                    'expected': [{str(0): token.upos}],
                    'expect': [{str(i): expect_dict[i]} for i in range(len(expect_dict))],
                    'agree': extract_feats(token),
                },
            ]
        )

 #################################################
 ##############################  Scriviamo output
        
with open('emglex.json', 'w', encoding='utf-8') as f:  
    f.write('{\n')
    for i, (lemma, info) in enumerate(lemma_info):
        f.write(f'"{lemma}": {json.dumps(info)}')
        if i < len(lemma_info) - 1:
            f.write(',\n')
    f.write('\n}')

