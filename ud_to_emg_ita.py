import pyconll
import json
import argparse

lemma_info = []

parser = argparse.ArgumentParser(description='Convert a CoNLL-U file to EMGLEX format')
parser.add_argument('-i', '--input', type=str, help='Input CoNLL-U file name', required=True)
args = parser.parse_args()
file_name = args.input

sentences = pyconll.load_from_file(file_name)

root_token = pyconll.unit.token.Token('0\troot\t_\t_\t_\t_\t_\t_\t_\t_', True)

def get_subject(token, token_dict, original_dict):

    subject = []  
    subj_verb_fin = []
    impersonal_subj = []
    passive_subj = []
    expl_subj = token_dict[y.id]

    subj_cop = []
    modal_subj = []
    tense_subj = []
    aux_pass = []
    

    if get_verb_type(token) == 'verb_fin':
        subj_verb_fin = subject
        impersonal_subj = token_dict['0']
        passive_subj = token_dict[x.id]
        expl_subj = token_dict[y.id]

        subj_cop = token_dict[x.id]
        modal_subj = token_dict[x.id]
        tense_subj = token_dict[original_dict[original_head]]
        aux_pass = token_dict[original_dict[original_head]]
        
        for x in token_dict.values():
            if x is None:
                continue
            if get_original_head(x, original_dict) == token.id:
                if x.deprel == 'nsubj':
                    subj_verb_fin = token_dict[x.id]
                    return subj_verb_fin
                elif x.deprel == 'expl:impers':
                    impersonal_subj = token_dict['0']
                    return impersonal_subj
                elif x.deprel == 'nsubj:pass':
                    passive_subj = token_dict[x.id]
                    return passive_subj
                elif x.deprel == 'expl':
                    for y in token_dict.values():
                        if y.deprel == 'nsubj' and original_dict[y.id] == token.id:
                            expl_subj = token_dict[y.id]
                            return expl_subj
                        else:
                            continue
                        
    elif get_verb_type(token) == 'aux_copula':
        for x in token_dict.values():
            if x.head == 'nsubj' and original_dict[x.id] == original_dict[token.id]:
                 subj_cop = token_dict[x.id]
                return subj_cop
    elif get_verb_type(token) == 'aux_modal':
        for x in token_dict.values():
            if x.head == 'nsubj' and original_dict[x.id] == original_head:
                modal_subj = token_dict[x.id]
                return modal_subj
    elif get_verb_type(token) == 'aux_tense':
        for x in token_dict.values():
            if x.upos == 'VERB':
                tense_subj = token_dict[original_dict[original_head]]
                return tense_subj
    elif get_verb_type(token) == 'aux_pass':
        for x in token_dict.values():
            if x.upos == 'VERB':
                aux_pass = token_dict[original_dict[original_head]]
                return aux_pass
    return None
    
def get_verb_type(token):
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
        if 'Fin' in token.feats['VerbForm']:
            return verb_fin
        elif 'Inf' in token.feats['VerbForm']:
            return verb_inf
        elif 'Ger' in token.feats['VerbForm']:
            return verb_ger
        elif 'Part' in token.feats['VerbForm']:
            return verb_part
        
            
def extract_feats(token):
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

def get_children(father, token_dict):
    children = []
    for token in token_dict.values():
        if father.id == token.head:
            children.append(token)
    return children

def get_original_head(token, original_dict):
    original_head = original_dict[token.id]
    return original_head
    
for sentence in sentences:
    original_dict = {'0':''}
    token_dict = {'0':root_token}
    results = []
    sentence_info = {}
    expect = []
    
    for token in sentence:
        if '-' in token.id:
            continue
        token_dict[token.id] = token
        original_dict[token.id] = token.head
    
    for token in token_dict.values():
        if token.form == 'root':
            continue
        original_head = get_original_head(token, original_dict)
        
        ##l'ausiliare seleziona il proprio verbo di riferimento, non il contrario
      
        if token.upos == 'AUX' and token_dict[original_head].upos == 'VERB':
            token_dict[original_head].head = token.id
            
        ##verbi composti 
        
        if token.upos == 'AUX' and str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)+1)].upos == 'AUX':
            token_dict[str(int(token.id)+1)].head = token.id
            
        ### costruzioni passive, rendere il soggetto passivo head dell'ausiliare

        if token.deprel == 'aux:pass':
            for x in token_dict.values():
                if x.deprel == 'nsubj:pass' and original_dict[x.id] == original_dict[token.id]: #se è una costruzione verbale composta (aux+aux+part), bisogna considerare il primo aux
                    if str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)-1)].upos == 'AUX':
                        token_dict[str(int(token.id)-1)].head = x.id
                    #per le costruzioni passive semplici (aux + part)  
                    else: 
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
        
        #gestioni di costruzioni relative come "caso di pensare"
        if token.upos == 'VERB' and token.deprel == 'acl' and token_dict[original_head].upos == 'NOUN':
            for x in token_dict.values():
                if x.deprel == 'mark' and original_dict[x.id] == token.id:
                    token_dict[token.id].head = x.id
                    token_dict[x.id].head = original_dict[token.id]                
        
        #il verbo seleziona il det o l'adp successivo 
        if token.upos in ['AUX','VERB'] and str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)+1)].upos in ['DET','ADP']:
            token_dict[str(int(token.id)+1)].head = token.id

        #se ci sono due det in sequenza, il primo seleziona il secondo
        if token.upos == 'DET' and str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)+1)].upos == 'DET':
            token_dict[str(int(token.id)+1)].head = token.id

        #è il det a selezionare il noun,pron
        if token.upos == 'DET':
            if token_dict[original_head].upos in ['PROPN','PRON','NOUN']:
                token_dict[original_head].head = token.id 
            elif token_dict[original_head].upos not in ['PROPN','PRON','NOUN']: ##per eventuali situazioni come numerali (numerale selezionato non direttamente da det)
                r = token_dict[original_head].head
                if token_dict[r].upos in ['PROPN','PRON','NOUN']:
                    token_dict[r].head = token.id
                    

        #preposizioni e nomi
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
        if token.upos == 'PRON' and 'Rel' in token.feats['PronType']:
            s = token_dict[original_head].head                
            token_dict[token.id].head = token_dict[s].id

            if token_dict[original_head].upos in ['AUX','VERB']:
                if get_subject(token_dict[original_head], token_dict, original_dict) == token:
                    token_dict[original_head].head = token.id
            else:
                continue
                    
                
            
                
        #gestione di introduzione di subordinate
        if token.deprel == 'mark':
            
            if token.upos == 'ADP':
                if get_verb_type(token_dict[original_head]) == 'verb_inf': #preposizione è head di verbo all'infinito
                    token_dict[original_head].head = token.id
                
            elif token.upos == 'ADV':
                if str(int(token.id)+1) in token_dict and token_dict[str(int(token.id)+1)].deprel == 'fixed':
                    token_dict[str(int(token.id)+1)].head = token.id
                    token_dict[original_head].head = token_dict[str(int(token.id)+1)].id ##original head è sempre il verbo della subordinata
                
            elif token.upos == 'SCONJ':
                r = token_dict[original_head].head                
                token_dict[token.id].head = token_dict[r].id
                token_dict[original_head].head = token.id
            
    # Populate expected list for each token in the sentence
    for token in sentence:
        expect_dict = {}
        children = get_children(token, token_dict)
        for child in children:
            expect_dict[len(expect_dict)] = child.upos
        expect.append(expect_dict)

        # Add current token information to lemma_info
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

        
        
with open('_emglex_frase.json', 'w', encoding='utf-8') as f:  # Write the JSON data to a file
    # Exclude punctuation and "X" tokens from the final output
    lemma_info = [x for x in lemma_info if x[1]['label'] not in ("PUNCT", "X")]
    f.write('{\n')
    for i, (lemma, info) in enumerate(lemma_info):
        f.write(f'"{lemma}": {json.dumps(info)}')
        if i < len(lemma_info) - 1:
            f.write(',\n')
    f.write('\n}')
