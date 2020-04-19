import MeCab, re
from JpTextProcessing.characters import *
tagger = MeCab.Tagger()


def tokenize(text:str, pos_thai=False) -> list:
    """
    tokenize sentence into list of tokens with linguistic features
    0:surface form, 1:pos, 2:pos2, 3:pos3, 4:pos4
    5:conjugation type, 6:conjugation form, 7:lemma, 8:phono, 9:phone

    >>> tokenize('大きい家は走りたくなるな')
    [['大きい', '形容詞', '自立', '*', '*', '形容詞・イ段', '基本形', '大きい', 'オオキイ', 'オーキイ'],
    ['家', '名詞', '一般', '*', '*', '*', '*', '家', 'イエ', 'イエ'],
    ['は', '助詞', '係助詞', '*', '*', '*', '*', 'は', 'ハ', 'ワ'],
    ['走り', '動詞', '自立', '*', '*', '五段・ラ行', '連用形', '走る', 'ハシリ', 'ハシリ'],
    ['たく', '助動詞', '*', '*', '*', '特殊・タイ', '連用テ接続', 'たい', 'タク', 'タク'],
    ['なる', '動詞', '自立', '*', '*', '五段・ラ行', '基本形', 'なる', 'ナル', 'ナル'],
    ['な', '助詞', '終助詞', '*', '*', '*', '*', 'な', 'ナ', 'ナ']]
    """
    pos_mapping = {'動詞':'กริยา','名詞':'คำนาม','形容詞':'i-adj','助詞':'คำช่วย','助動詞':'คำช่วยที่ผันรูป','副詞':'adv','接頭詞':'prefix',
                '連体詞':'คำขยายคำนาม','記号':'เครื่องหมาย','感動詞':'คำอุทาน','フィラー':'filler','接続詞':'คำเชื่อม','その他':'others'}

    # exclude final two tokens : 'EOS', ''
    tokens = tagger.parse(text).split('\n')[:-2]
    tokens = [re.split(r'[,\t]', token) for token in tokens]
    if pos_thai == False:
        return tokens
    else:
        for i, token in enumerate(tokens):  # add verb group 1-3 to PoS
            if token[1] == '動詞':
                tokens[i][1] = 'กริยากลุ่ม' + get_verb_group(token[5])
            else:
                tokens[i][1] = pos_mapping[token[1]]

        # [surface, phone, lemma, pos] or [surface, '-', surface, pos]  
        # replace ヲ -> オ
        return [[t[0],t[-1].replace('ヲ','オ'),t[7],t[1]] if len(t) == 10 else [t[0],t[0],t[0],t[1]] for t in tokens]

def get_verb_group(conjtype:str) -> str:
    """
    >>> get_verb_group('五段・カ行')
    '1'
    """
    return {'五段':'1', '一段':'2', 'サ変':'3', 'カ変':'3'}.get(conjtype[:2], '')


def yomikata(text:str, phonetic=False, return_list=False) -> str:
    """
    convert JP text into hiragana text

    >>> yomikata('心掛け')
    こころがけ

    >>> yomikata('私は本をNHKへ返す', phonetic=True)
    わたしわほんを NHK えかえす
    """
    tokens = tokenize(text)
    result = []
    for token in tokenize(text):
        if is_katakana(token[0]):  # all chars are katakana
            if phonetic and len(token) == 10:  # len(token) == 10 : with phone/phono information
                result.append(token[-1]) # token[-1] = phone
            else:
                result.append(token[0]) # token[0] = surface form
        elif len(token) == 10:  # not katakana, but phone/phono information
            if phonetic:
                result.append(token[-1]) # token[-1] = phone
            else:
                result.append(kata2hira(token[-2])) # token[-2] = phono
        else:
            result.append(token[0])
    if return_list:
        return result
    else:
        return ''.join(result)



def romanize_one_token(token:list) -> str:
    """
    input: list of tags of one token
    output: romanized katakana string (Hepburn style)

    >>> romanize_one_token(['収録', '名詞', 'サ変接続', '*', '*', '*', '*', '収録', 'シュウロク', 'シューロク'])
    shuuroku
    """
    result = ''
    if len(token) == 10:  # with phone information
        text = token[-1]  # phone
    else:
        text = hira2kata(token[0])  # surface form
    while len(text) > 0:
        if len(text) >= 2 and text[1] in 'ァィゥェォヵヶャュョヮ':
            try:
                result += ROMAJI_DICT[text[:2]]
            except:
                result += ROMAJI_DICT[text[0]]
                result += ROMAJI_DICT[text[1]]
            text = text[2:]
        elif text[0] == 'ッ':
            result += 'ß' # temp char for っ
            text = text[1:]
        elif text[0] == 'ー':
            result += result[-1]
            text = text[1:]
        else:
            try:
                result += ROMAJI_DICT[text[0]]
            except:
                result += text[:1] # NOT JP char
            text = text[1:]
    return result


def romanize(sentence:str) -> str:
    """
    input: list of tokens
    output: romanized whole sentence

    >>> romanize(['収録', '名詞', 'サ変接続', '*', '*', '*', '*', '収録', 'シュウロク', 'シューロク'])
    shuuroku
    """
    tokens = tokenize(sentence)
    result =  ' '.join(romanize_one_token(token) for token in tokens)
    result = re.sub(r'ß ?(\w)', r'\1\1', result) # substituted by following consonant
    result = re.sub(r'n([mbp])', r'm\1', result) # bilabial assimilation
    result = re.sub(r'ou$', 'o', result) # final ou -> o  e.g. SATO
    result = result.replace('cch', 'tch') # イッチョウ -> itcho
    return result


ROMAJI_DICT ={
    'ァ': 'a',
    'ア': 'a',
    'ィ': 'i',
    'イ': 'i',
    'イェ': 'ye',
    'ゥ': 'u',
    'ウ': 'u',
    'ウィ': 'wi',
    'ウェ': 'we',
    'ウォ': 'wo',
    'ヴ': 'vu',
    'ヴァ': 'va',
    'ヴィ': 'vi',
    'ヴェ': 've',
    'ヴォ': 'vo',
    'ェ': 'e',
    'エ': 'e',
    'ォ': 'o',
    'オ': 'o',
    'カ': 'ka',
    'ガ': 'ga',
    'キ': 'ki',
    'キャ': 'kya',
    'キュ': 'kyu',
    'キョ': 'kyo',
    'ギ': 'gi',
    'ギャ': 'gya',
    'ギュ': 'gyu',
    'ギョ': 'gyo',
    'ク': 'ku',
    'クヮ': 'kwa',
    'クィ': 'kwi',
    'クェ': 'kwe',
    'クォ': 'kwo',
    'グ': 'gu',
    'グィ': 'gwi',
    'グェ': 'gwe',
    'グォ': 'gwo',
    'ケ': 'ke',
    'ゲ': 'ge',
    'コ': 'ko',
    'ゴ': 'go',
    'サ': 'sa',
    'ザ': 'za',
    'シ': 'shi',
    'シャ': 'sha',
    'シュ': 'shu',
    'ショ': 'sho',
    'シェ': 'she',
    'ジ': 'ji',
    'ジャ': 'ja',
    'ジュ': 'ju',
    'ジョ': 'jo',
    'ジェ': 'je',
    'ス': 'su',
    'スィ': 'si',
    'ズ': 'zu',
    'ズィ': 'zi',
    'セ': 'se',
    'ゼ': 'ze',
    'ソ': 'so',
    'ゾ': 'zo',
    'タ': 'ta',
    'ダ': 'da',
    'チ': 'chi',
    'チャ': 'cha',
    'チュ': 'chu',
    'チョ': 'cho',
    'チェ': 'che',
    'ヂ': 'ji',
    'ヂャ': 'ja',
    'ヂュ': 'ju',
    'ヂョ': 'jo',
    'ヂェ': 'je',
    'ツ': 'tsu',
    'ツァ': 'tsa',
    'ツィ': 'tsi',
    'ツェ': 'tse',
    'ツォ': 'tso',
    'ヅ': 'zu',
    'テ': 'te',
    'ティ': 'ti',
    'デ': 'de',
    'ディ': 'di',
    'ト': 'to',
    'トゥ': 'tu',
    'ド': 'do',
    'ドゥ': 'du',
    'ナ': 'na',
    'ニ': 'ni',
    'ニャ': 'nya',
    'ニュ': 'nyu',
    'ニョ': 'nyo',
    'ニェ': 'nye',
    'ヌ': 'nu',
    'ネ': 'ne',
    'ノ': 'no',
    'ハ': 'ha',
    'バ': 'ba',
    'パ': 'pa',
    'ヒ': 'hi',
    'ヒャ': 'hya',
    'ヒュ': 'hyu',
    'ヒョ': 'hyo',
    'ヒェ': 'hye',
    'ビ': 'bi',
    'ビャ': 'bya',
    'ビュ': 'byu',
    'ビョ': 'byo',
    'ビェ': 'bye',
    'ピ': 'pi',
    'ピャ': 'pya',
    'ピュ': 'pyu',
    'ピョ': 'pyo',
    'ピェ': 'pye',
    'フ': 'fu',
    'ファ': 'fa',
    'フィ': 'fi',
    'フェ': 'fe',
    'フォ': 'fo',
    'フュ': 'fyu',
    'ブ': 'bu',
    'プ': 'pu',
    'ヘ': 'he',
    'ベ': 'be',
    'ペ': 'pe',
    'ホ': 'ho',
    'ボ': 'bo',
    'ポ': 'po',
    'マ': 'ma',
    'ミ': 'mi',
    'ミャ': 'mya',
    'ミュ': 'myu',
    'ミョ': 'myo',
    'ム': 'mu',
    'メ': 'me',
    'モ': 'mo',
    'ャ': 'ya',
    'ヤ': 'ya',
    'ュ': 'yu',
    'ユ': 'yu',
    'ョ': 'yo',
    'ヨ': 'yo',
    'ラ': 'ra',
    'リ': 'ri',
    'リャ': 'rya',
    'リュ': 'ryu',
    'リョ': 'ryo',
    'リェ': 'rye',
    'ル': 'ru',
    'レ': 're',
    'ロ': 'ro',
    'ヮ': 'wa',
    'ワ': 'wa',
    'ヲ': 'o',
    'ン': 'n',
    'ヵ': 'ka',
    'ヶ': 'ke'}