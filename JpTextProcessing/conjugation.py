from JpTextProcessing.tokenization import *

def shift_dan(gyou:str, n:int) -> str:
    """
    function for shifting Dan
    >>> shift('あ', 2)
    'う'
    """
    if gyou in ['な','ま','ら']:
        return chr(ord(gyou) + n)
    elif gyou in ['あ','か','が','さ','ざ']:
        return chr(ord(gyou) + n*2)
    elif gyou in ['は','ば','ぱ']:
        return chr(ord(gyou) + n*3)
    elif gyou == 'た':
        return {1:'ち', 2:'つ', 3:'て', 4:'と'}[n]
    elif gyou == 'だ':
        return {1:'ぢ', 2:'づ', 3:'で', 4:'ど'}[n]


def get_teform(lemma:str) -> str:
    """
    convert group1 verb base form into te form
    
    >>> get_teform('書く')
    書いて
    """
    if lemma == '行く':
        return '行って'
    elif lemma[-1] in ['う','つ','る']:
        return lemma[:-1] + 'って'
    elif lemma[-1] in ['ぬ','む','ぶ']:
        return lemma[:-1] + 'んで'
    elif lemma[-1] == 'く':
        return lemma[:-1] + 'いて'
    elif lemma[-1] == 'ぐ':
        return lemma[:-1] + 'いで'
    elif lemma[-1] == 'す':
        return lemma[:-1] + 'して'


def verb_conj_from_lemma(lemma:str, conjtype:str) -> list:
    """
    input: one verb, conjtype is 5th element of tokenize()
    output: list of conjugated forms


    nai, nakatta, masu, base, te, ta, imperative, conditional, potential, volitional : 9-10　forms

    verb_conj_from_lemma('行く', '五段・カ行促音')
    >>> ['行く', '行かない', '行かなかった', '行きます', '行って', '行った', '行けば', '行け', '行こう']

    verb_conj_from_lemma('食べる', '一段')
    >>> ['食べる', '食べない', '食べなかった', '食べます', '食べて', '食べた', '食べれば', '食べろ', '食べよう']
    """
    group = conjtype[:2] # conjtype = 五段・カ行, 一段
    pot = None # potential form
    
    # if verb is an irregular verb, look up the dictionary
    if lemma in IRREGULAR_VERBS:
        return IRREGULAR_VERBS[lemma]
    
    elif conjtype == 'サ変・−ズル': # e.g. 念ずる
        stem = lemma[:-2]  # 念
        nai = stem + 'じない'
        nakatta = stem + 'じなかった'
        masu = stem + 'じます'
        te = stem + 'じて'
        ta = stem + 'じた'
        imp = stem + 'じよ'
        con = stem + 'ずれば'
        vol = stem + 'じよう'
        pot = stem + 'じられる'
    
    elif group == '一段' or lemma == 'いる': # e.g. 食べる
        stem = lemma[:-1] # 食べ
        nai = stem +  'ない' # 食べない
        nakatta = stem + 'なかった' # 食べなかった
        masu = stem + 'ます' # 食べます
        te = stem + 'て' # 食べて
        ta = stem + 'た' # 食べた
        imp = stem + 'ろ' # 食べろ
        con = stem + 'れば' # 食べれば
        vol = stem + 'よう' # 食べよう
    
    elif group == '五段':
        gyou = kata2hira(conjtype[3])  # e.g. 五段・カ行　-> か (convert into ア if ワ)
        stem = lemma[:-1]  # e.g. 買う -> 買
        nai = stem + gyou + 'ない' # 買わない
        nakatta = stem + gyou + 'なかった' # 買わなかった
        # wa gyou -> a gyou
        if gyou == 'わ': 
            gyou = 'あ'
        masu = stem + shift_dan(gyou, 1) + 'ます' # 買います
        te = get_teform(lemma) # 買って
        ta = te[:-1] + te[-1].replace('て','た').replace('で','だ') # 買った
        imp = stem + shift_dan(gyou, 3) # 買え
        con = stem + shift_dan(gyou, 3) + 'ば' # 買えば
        vol = stem + shift_dan(gyou, 4) + 'う' # 買おう
    
    if pot != None:
        return [lemma] + [nai, nakatta, masu, te, ta, con, imp, vol, pot]
    else:
        return [lemma] + [nai, nakatta, masu, te, ta, con, imp, vol]


def adj_conj_from_lemma(lemma:str):
    """
    nai, nakatta, desu, base, te, ta, conditional, adverb : 8 forms
    """
    if lemma == 'いい': # exception 
        stem = 'よ'
        desu = 'いいです'
    else:
        stem = lemma[:-1]
        desu = stem + 'いです'
        
    if lemma == 'ない':
        nai = 'ない'
        nakatta = 'なかった'
    elif lemma == '無い':
        nai = '無い'
        nakatta = '無かった'
    else:    
        nai = stem + 'くない'
        nakatta = stem + 'くなかった'
    
    te = stem + 'くて'
    ta = stem + 'かった'
    con = stem + 'ければ'
    adv = stem + 'く'
    
    return [lemma, nai, nakatta, desu, te, ta, con, adv]


def conjugate(text:str) -> list:
    """
    conjugate verb or i-adj regardless of whether it is lemma or not
    
    conjugate('任ずる')
    >>> ['任ずる', '任じない', '任じなかった', '任じます', '任じて', '任じた', '任ずれば', '任じよ', '任じよう', '任じられる']

    conjugate('来て')
    >>> ['来る', '来ない', '来なかった', '来ます', '来て', '来た', '来い', '来れば', '来よう', '来られる']

    tokenize() may return 2-3 or tokens even if it is one word 
    e.g. 
    >>> tokenize('任ずる')
    [['任', '名詞', '一般', '*', '*', '*', '*', '任', 'ニン', 'ニン'],
    ['ずる', '名詞', '一般', '*', '*', '*', '*', 'ずる', 'ズル', 'ズル']]
    >>> tokenize('選択する')
    [['選択', '名詞', 'サ変接続', '*', '*', '*', '*', '選択', 'センタク', 'センタク'],
    ['する', '動詞', '自立', '*', '*', 'サ変・スル', '基本形', 'する', 'スル', 'スル']]

    if cannot conjugate, return None
    """
    # exception -ずる動詞
    # 任ずる => 名詞, but 任じる => 動詞
    if text.endswith('ずる') and tokenize(text.replace('ずる','じる'))[0][1] == '動詞':
        return verb_conj_from_lemma(text, 'サ変・−ズル')
    try:
        tokens = tokenize(text)
        # 0:surface form, 1:pos, 2:pos2, 3:pos3, 4:pos4
        # 5:conjugation type, 6:conjugation form, 7:lemma, 8:kana, 9:phonemic
        if len(tokens) == 0:
            return None
        if tokens[0][1] == '動詞': # if first token is verb, ignore suffix
            return verb_conj_from_lemma(tokens[0][7], tokens[0][5]) # 7.lemma, 5.conjtype
        elif tokens[0][1] == '形容詞':
            return adj_conj_from_lemma(tokens[0][7])
        elif len(tokens) == 1: # only one token, but neither verb nor adj
            return None 
        elif tokens[0][2] == 'サ変接続': # token[2] = pos2, サ変接続 means 'する' will follow behind
            if tokens[1][7] == 'する': # 2 tokens e.g. 活動 + する
                return [tokens[0][0] + x for x in verb_conj_from_lemma('する','サ変')]
            elif tokens[1][2] == 'サ変接続' and tokens[2][7] == 'する': # 3 tokens e.g. 選挙 + 活動 + する
                return [tokens[0][0] + tokens[1][0] + x for x in verb_conj_from_lemma('する','サ変')]
        else:
            return None
    except:
        return None



#########################################################################################


IRREGULAR_VERBS = {
    'する': ['する', 'しない', 'しなかった', 'します', 'して', 'した', 'しろ', 'すれば', 'しよう', 'できる'],
    'くる': ['くる', 'こない', 'こなかった', 'きます', 'きて', 'きた', 'こい', 'くれば', 'こよう', 'こられる'],
    '来る': ['来る', '来ない', '来なかった', '来ます', '来て', '来た', '来い', '来れば', '来よう', '来られる'],
    'いる': ['いる', 'いない', 'いなかった', 'います', 'いて', 'いた', 'いろ', 'いれば', 'いよう', 'いられる'],
    'ある': ['ある', 'ない', 'なかった', 'あります', 'あって', 'あった', 'あれ', 'あれば', 'あろう', 'ありえる'],
    '在る': ['在る', 'ない', 'なかった', '在ります', '在って', '在った', '在れ', '在れば', '在ろう', 'ありえる'],
    '有る': ['有る', 'ない', 'なかった', '有ります', '有って', '有った', '有れ', '有れば', '有ろう', '有りえる'],
    'なさる': ['なさる','なさらない','なさらなかった','なさいます','なさって','なさった','なされ','なされば','なさろう'],
    'くださる': ['くださる',
        'くださらない',
        'くださらなかった',
        'くださいます',
        'くださって',
        'くださった',
        'くだされ',
        'くだされば',
        'くださろう'],
    'おっしゃる': ['おっしゃる',
        'おっしゃらない',
        'おっしゃらなかった',
        'おっしゃいます',
        'おっしゃって',
        'おっしゃった',
        'おっしゃれ',
        'おっしゃれば',
        'おっしゃろう'],
    'いらっしゃる': ['いらっしゃる',
        'いらっしゃらない',
        'いらっしゃらなかった',
        'いらっしゃいます',
        'いらっしゃって',
        'いらっしゃった',
        'いらっしゃれ',
        'いらっしゃれば',
        'いらっしゃろう']
}