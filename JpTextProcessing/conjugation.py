from JpTextProcessing.tokenization import *


def shift_dan(gyou:str, n:int) -> str:
    """
    >>> shift('あ', 2)
    'う'
    """
    if gyou in ['な','ま','ら']:
        return chr(ord(gyou) + n)
    elif gyou in ['あ','か','が','さ','ざ','た','だ']:
        return chr(ord(gyou) + n*2)
    elif gyou in ['は','ば','ぱ']:
        return chr(ord(gyou) + n*3)


def teform(lemma:str) -> str:
    """
    group1 base form -> te form
    teform('書く') >>> '書いて'
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
    nai, nakatta, masu, base, te, ta, imperative, conditional, potential, volitional : 9-10　forms

    verb_conj_from_lemma('行く', '五段・カ行促音')
    >>> ['行く', '行かない', '行かなかった', '行きます', '行って', '行った', '行けば', '行け', '行こう']

    verb_conj_from_lemma('食べる', '一段')
    >>> ['食べる', '食べない', '食べなかった', '食べます', '食べて', '食べた', '食べれば', '食べろ', '食べよう']
    """
    group = conjtype[:2] # conjtype = 五段・カ行, 一段
    pot = None
    
    if lemma in IRREGULAR_VERBS.keys():
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
        nai = stem +  'ない'
        nakatta = stem + 'なかった'
        masu = stem + 'ます'
        te = stem + 'て'
        ta = stem + 'た'
        imp = stem + 'ろ'
        con = stem + 'れば'
        vol = stem + 'よう'
    
    elif group == '五段':
        gyou = kata2hira(conjtype[3])  # e.g. 五段・カ行　-> か (convert into ア if ワ)
        stem = lemma[:-1]  # e.g. 行く -> 行
        nai = stem + gyou + 'ない'
        nakatta = stem + gyou + 'なかった'
        # wa gyou -> a gyou
        if gyou == 'わ': 
            gyou = 'あ'
        masu = stem + shift_dan(gyou, 1) + 'ます'
        te = teform(lemma)
        ta = te[:-1] + te[-1].replace('て','た').replace('で','だ')
        imp = stem + shift_dan(gyou, 3)
        con = stem + shift_dan(gyou, 3) + 'ば'
        vol = stem + shift_dan(gyou, 4) + 'う'
    
    if pot != None:
        return [lemma] + [nai, nakatta, masu, te, ta, con, imp, vol, pot]
    else:
        return [lemma] + [nai, nakatta, masu, te, ta, con, imp, vol]


def adj_conj_from_lemma(lemma:str):
    """
    nai, nakatta, desu, base, te, ta, conditional, adverb : 8
    """
    if lemma == 'いい':
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
    conjugate verb or i-adj
    if not, return None

    conjugate('任ずる')
    >>> ['任ずる', '任じない', '任じなかった', '任じます', '任じて', '任じた', '任ずれば', '任じよ', '任じよう', '任じられる']

    conjugate('来て')
    >>> ['来る', '来ない', '来なかった', '来ます', '来て', '来た', '来い', '来れば', '来よう', '来られる']

    
    """
    if text.endswith('ずる') and tokenize(text.replace('ずる','じる'))[0][1] == '動詞':
        return verb_conj_from_lemma(text, 'サ変・−ズル')

    tokens = tokenize(text)
    if tokens[0][1] == '動詞':
        return verb_conj_from_lemma(tokens[0][7], tokens[0][5])
    elif tokens[0][1] == '形容詞':
        return adj_conj_from_lemma(tokens[0][7])
    elif len(tokens) == 1: # only one token and neither verb nor adj
        return None 
    elif tokens[0][2] == 'サ変接続': 
        if tokens[1][7] == 'する': # e.g. 活動 + する
            return [tokens[0][0] + x for x in verb_conj_from_lemma('する','サ変')]
        elif tokens[1][2] == 'サ変接続' and tokens[2][7] == 'する': # e.g. 選挙 + 活動 + する
            return [tokens[0][0] + tokens[1][0] + x for x in verb_conj_from_lemma('する','サ変')]
    else:
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