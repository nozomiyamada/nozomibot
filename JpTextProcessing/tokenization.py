import MeCab, re
from JpTextProcessing.characters import *
tagger = MeCab.Tagger()


def tokenize(text:str, pos_thai=False) -> list:
    """
    tokenize sentence into list of tokens with linguistic features
    0:surface form, 1:pos, 2:pos2, 3:pos3, 4:pos4
    5:conjugation type, 6:conjugation form, 7:lemma, 8:kana, 9:phonemic

    >>> tokenize('大きい家は走りたくなるな')
    [['大きい', '形容詞', '自立', '*', '*', '形容詞・イ段', '基本形', '大きい', 'オオキイ', 'オーキイ'],
    ['家', '名詞', '一般', '*', '*', '*', '*', '家', 'イエ', 'イエ'],
    ['は', '助詞', '係助詞', '*', '*', '*', '*', 'は', 'ハ', 'ワ'],
    ['走り', '動詞', '自立', '*', '*', '五段・ラ行', '連用形', '走る', 'ハシリ', 'ハシリ'],
    ['たく', '助動詞', '*', '*', '*', '特殊・タイ', '連用テ接続', 'たい', 'タク', 'タク'],
    ['なる', '動詞', '自立', '*', '*', '五段・ラ行', '基本形', 'なる', 'ナル', 'ナル'],
    ['な', '助詞', '終助詞', '*', '*', '*', '*', 'な', 'ナ', 'ナ']]

    original method of MeCab returns 10 elements except for non-Japanese word like proper noun 
    so, filled with surface form instead

    >>> tokenize('アニーが怒った')
    [['アニー', '名詞', '固有名詞', '組織', '*', '*', '*', "アニー", "アニー", "アニー"],  <==  fill "アニー" 
    ['が', '助詞', '格助詞', '一般', '*', '*', '*', 'が', 'ガ', 'ガ'],
    ['怒っ', '動詞', '自立', '*', '*', '五段・ラ行', '連用タ接続', '怒る', 'オコッ', 'オコッ'],
    ['た', '助動詞', '*', '*', '*', '特殊・タ', '基本形', 'た', 'タ', 'タ']]

    >>> tokenize('アニーは怒らなかった', pos_thai=True)
    [['アニー', 'アニー', 'アニー', 'คำนาม'],
    ['は', 'ワ', 'は', 'คำช่วย'],
    ['怒ら', 'オコラ', '怒る', 'กริยากลุ่ม1'],
    ['なかっ', 'ナカッ', 'ない', 'คำช่วยที่ผันรูป'],
    ['た', 'タ', 'た', 'คำช่วยที่ผันรูป']]
    """
    pos_mapping = {'動詞':'กริยา','名詞':'คำนาม','形容詞':'i-adj','助詞':'คำช่วย','助動詞':'คำช่วยที่ผันรูป','副詞':'adv','接頭詞':'prefix',
                '連体詞':'คำขยายคำนาม','記号':'เครื่องหมาย','感動詞':'คำอุทาน','フィラー':'filler','接続詞':'คำเชื่อม','その他':'others'}

    tokens = tagger.parse(text).split('\n')[:-2] # split into tokens, exclude final two tokens: 'EOS' and ''
    tokens = [re.split(r'[,\t]', token) for token in tokens] # split by \t or comma -> make 2D list
    tokens = [x if len(x)==10 else x[:7] + [x[0]]*3 for x in tokens] # fill 7.lemma 8.kana and 9.phonemic with 0.surface
    tokens = [x[:-1] + [x[-1].replace('ヲ','オ')] for x in tokens ] # replace 'ヲ' with 'オ' in 9.phonemic
    
    if pos_thai == False: 
        return tokens # return original result
    else: # convert PoS tag into Thai
        for i, token in enumerate(tokens):  # add digit 1-3 after PoS
            if token[1] == '動詞':
                tokens[i][1] = 'กริยากลุ่ม' + get_verb_group(token[5]) # token[5] = conjtype
            else:
                tokens[i][1] = pos_mapping[token[1]]

        # return [0.surface, 9.phone, 7.lemma, 1.pos] or [0.surface, 0.surface, 0.surface, 1.pos]  
        return [[t[0],t[-1],t[7],t[1]] if len(t) == 10 else [t[0],t[0],t[0],t[1]] for t in tokens]

def get_verb_group(conjtype:str) -> str:
    """
    get verb group 1-3 from the result of tokenize
    conjtype is a 5th element of tokens list
    
    >>> get_verb_group('五段・カ行')
    '1'
    """
    return {'五段':'1', '一段':'2', 'サ変':'3', 'カ変':'3'}.get(conjtype[:2], '')


def yomikata(text:str, phonemic=False, return_list=False) -> str:
    """
    convert JP text into katakana text

    >>> yomikata('心掛け')
    ココロガケ

    >>> yomikata('私は本をNHKへ返す', phonemic=True)
    ワタシハホンヲNHKヘカエス

    >>> yomikata('ジョンとぼくはいつかは別れる', phonemic=True, return_list=True)
    ['ジョン', 'ト', 'ボク', 'ワ', 'イツカ', 'ワ', 'ワカレル']
    """
    # 8:kana, 9:phonemic
    tokens = tokenize(text)
    if phonemic:
        result = [x[9] for x in tokens]
    else:
        result = [x[8] for x in tokens]
    
    return result if return_list else ''.join(result) 


def romanize(text:str, phonemic=True) -> str:
    """
    1. check first 2 or 1 chars 
    2. if they exist in the ROMAJI_DICT, replace with ROMAJI
    3. delete the characters 

    * っ must repeat following letter, so use the temporary char ß instead

    >>> romanize('伊藤',False)
    itou

    >>> romanize('伊藤',True)
    itoo


    """
    text = yomikata(text, phonemic)
    result = ''
    while len(text) > 0:
        if len(text) >= 2 and text[1] in 'ァィゥェォヵヶャュョヮ': # 小書き文字
            try:
                result += ROMAJI_DICT[text[:2]]
            except:
                result += ROMAJI_DICT[text[0]] 
                result += ROMAJI_DICT[text[1]]
            text = text[2:] # delete first two characters
        elif text[0] == 'ッ':
            result += 'ß' # temp char for っ
            text = text[1:]
        elif text[0] == 'ー': # long vowel
            result += result[-1] # repeat previous character
            text = text[1:]
        else:
            try:
                result += ROMAJI_DICT[text[0]]
            except:
                result += text[:1] # not exist = non-JP char
            text = text[1:]
    result = re.sub(r'ß+(\w)', r'\1\1', result) # 'っ' substituted by following consonant
    result = re.sub(r'ß+$', r'ʔ', result) # 'っ' in the final position => glottal stop
    if phonemic:
        result = re.sub(r'n([mbp])', r'm\1', result) # bilabial assimilation
        result = re.sub(r'ou$', 'oo', result) # final ou -> oo
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
    'グヮ': 'gwa',
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
    'テュ': 'tyu',
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
    'ヶ': 'ke',
    'ッ': 'ß'}