import re, requests, json, random
from JpProcessing import yomikata, hira2kata, kata2hira, is_only_kana
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd
pd.set_option('mode.chained_assignment', None)


def toNchr(morph:str, n=3) -> str:
    """
    function for adjusting result columns (for Linebot)
    convert into N characters text by filling full spaces
    
    >>> toNchr('で', 4)
    'で　　　　' 
    --- 1 chr with 4 full spaces
    """
    return morph + (n-len(morph)) * '　'


########## GET WORD FROM DICTIONARY ##########

# load dictionary [yomi,word,thai]
WORD_DICT = pd.read_csv('data/jtdic.csv', encoding='utf8').fillna('-') # nan -> "-"

# FUNTION FOR SORT DATAFRAME BY LENGTH 
def sort_df(df, columns:list):
    df['length_word'] = df.word.apply(len)
    df['length_yomi'] = df.yomi.apply(len)
    return df.sort_values(columns)[['yomi','word','thai']]

def get_word_exact(word:str):
    # SEARCH BY WORD, ONLY EXACT MATCH
    return WORD_DICT[WORD_DICT.word == word].values.tolist()

def get_word(word:str, format_for_linebot=True):
    # SEARCH BY THAI WORD => 1.INITIAL MATCH, 2.LIKE MATCH
    if re.search(r'[ก-๙]+', word):
        df_initial = WORD_DICT[WORD_DICT.thai.str.startswith(word)] # 1.INITIAL MATCH
        df_initial['length_thai'] = df_initial.thai.apply(len)
        df_initial['length_yomi'] = df_initial.yomi.apply(len)
        df_initial = df_initial.sort_values(['length_thai','length_yomi'])[['yomi','word','thai']]
        df_like = WORD_DICT[WORD_DICT.thai.str.contains(word)] # 2.LIKE MATCH
        df_like['length_thai'] = df_like.thai.apply(len)
        df_like['length_yomi'] = df_like.yomi.apply(len)
        df_like = df_like.sort_values(['length_thai','length_yomi'])[['yomi','word','thai']]
        df = pd.concat([df_initial, df_like]).drop_duplicates()
    # SEARCH BY JAPANESE WORD
    else:
        # IF CONTAINS KANJI => 1.KANJI INITIAL, 2.KANA EXACT, 3.KANJI LIKE; PRIORITY TO 'word'
        if not is_only_kana(word):
            yomi_katakana = yomikata(word)
            yomi_hiragana = kata2hira(yomi_katakana)
            df_initial = WORD_DICT[WORD_DICT.word.str.startswith(word)] # 1. KANJI INITIAL MATCH
            df_initial = sort_df(df_initial, ['length_word','length_yomi'])
            df_yomi = WORD_DICT[WORD_DICT.yomi == yomi_hiragana] # 2. KANA EXACT MATCH
            df_yomi = sort_df(df_yomi, ['length_word','length_yomi'])
            df_like = WORD_DICT[WORD_DICT.word.str.contains(word)] # 3. KANJI LIKE MATCH
            df_like = sort_df(df_like, ['length_word','length_yomi'])
            df = pd.concat([df_initial, df_yomi, df_like]).drop_duplicates()
        # ONLY KANA => 1.EXACT, 2.INITIAL, 3.LIKE; PRIORITY TO 'yomi'
        else:
            yomi_katakana = hira2kata(word)
            yomi_hiragana = kata2hira(word)
            df_exact = WORD_DICT[WORD_DICT.word == word]
            df_initial = WORD_DICT[(WORD_DICT.word.str.startswith(word)) | (WORD_DICT.yomi.str.startswith(yomi_katakana)) | (WORD_DICT.yomi.str.startswith(yomi_hiragana))] 
            df_initial = sort_df(df_initial, ['length_yomi','length_word'])
            df_like = WORD_DICT[(WORD_DICT.word.str.contains(word)) | (WORD_DICT.yomi.str.contains(yomi_katakana)) | (WORD_DICT.yomi.str.contains(yomi_hiragana))]
            df_like = sort_df(df_like, ['length_yomi','length_word'])
            df = pd.concat([df_exact, df_initial, df_like]).drop_duplicates()

    if len(df) == 0:
        return None
    elif format_for_linebot:
        return '\n'.join([' '.join(x) for x in df[['word','yomi','thai']].values.tolist()[:15]])
    else:
        return df.values.tolist()[:15]


##########  KANJI DICT ##########

# load dictionary
with open('data/kanji.json','r', encoding='utf8') as f:
    KANJI_DICT = json.load(f)

def get_kanji(kanji:str, format_for_linebot=True):
    """
    get kanji from dictionary 
    key is kanji, value is dictionary {'会':{...}, '眠':{...}}
    """
    dic = KANJI_DICT.get(kanji, None)
    if format_for_linebot:
        if dic == None:
            return 'ขอโทษที่หาไม่เจอในดิกครับ'
        on = dic['on']
        kun = dic['kun']
        imi = '\n'.join(dic['imi'])
        bushu = dic['bushu']
        kanken = dic['kanken']
        return f"on: {on}\nkun: {kun}\nความหมาย:\n{imi}\nbushu: {bushu}\nkanken level: {kanken}"
    else:
        if dic == None:
            return None
        return [kanji, dic['on'], dic['kun'], '<br>'.join(dic['imi'])]


########## ACCENT ##########

# LOAD CSV
ACCENT_TABLE = pd.read_csv('data/accent.csv', encoding='utf8').fillna('-') # nan -> "-"

# FUNTION FOR SORT DATAFRAME BY LENGTH 
def sort_df_accent(df, columns:list):
        df['length_word'] = df.word.apply(len)
        df['length_yomi'] = df.yomi.apply(len)
        return df.sort_values(columns)[['word','accent','english']]

def get_accent(word:str, format_for_linebot=True):
    """
    get accent from table 
    header = [accent, word, yomi, english]
    'accent' is written in Katakana e.g. カ/ンシン
    'word' is lexical entry
    'yomi' is hiragana of the word
    """
    if len(word) == 0:
        return None if format_for_linebot else []
    # SEARCH BY THAI WORD
    if re.search(r'[ก-๙]+', word):
        df_initial = ACCENT_TABLE[ACCENT_TABLE.english.str.startswith(word)]
        df_initial['english_length'] = df_initial.english.apply(len)
        df = df_initial.sort_values('english_length')[['word','accent','english']]
    # CONTAINS KANJI => 1.EXACT, 2.INITIAL, 3.EXACT OF KANA, 4.LIKE 
    elif not is_only_kana(word): 
        yomi_hiragana = yomikata(word, katakana=False)
        # 1 2.EXACT & INITIAL MATCH OF THE WORD
        df_initial = ACCENT_TABLE[ACCENT_TABLE.word.str.startswith(word)] 
        df_initial = sort_df_accent(df_initial, ['length_word','length_yomi'])
        # 3.EXACT MATCH OF THE KANA (NO SORT)
        df_yomi = ACCENT_TABLE[ACCENT_TABLE.yomi == yomi_hiragana][['word','accent','english']] 
        # 4.LIKE MATCH OF THE WORD
        df_like = ACCENT_TABLE[ACCENT_TABLE.word.str.contains(word)] 
        df_like = sort_df_accent(df_like, ['length_word','length_yomi'])
        df = pd.concat([df_initial, df_yomi, df_like]).drop_duplicates()
    # ONLY KANA => 1.EXACT, 2.INITIAL, 3.LIKE
    else:
        yomi_hiragana = kata2hira(word)
        # 1.EXACT MATCH OF THE WORD
        df_exact = ACCENT_TABLE[(ACCENT_TABLE.word == word) | (ACCENT_TABLE.yomi.str == word)][['word','accent','english']] 
        # 2.INITIAL MATCH OF (THE WORD OR THE KANA)
        df_initial = ACCENT_TABLE[(ACCENT_TABLE.word.str.startswith(word)) | (ACCENT_TABLE.yomi.str.startswith(yomi_hiragana))]
        df_initial = sort_df_accent(df_initial, ['length_yomi','length_word'])
        # 3.LIKE MATCH OF (THE WORD OR THE KANA)
        df_like = ACCENT_TABLE[(ACCENT_TABLE.word.str.contains(word)) | (ACCENT_TABLE.english.str.contains(yomi_hiragana))]
        df_like = sort_df_accent(df_like, ['length_yomi','length_word'])
        df = pd.concat([df_exact, df_initial, df_like]).drop_duplicates()
    if len(df) == 0:
        return None
    elif format_for_linebot:
        text = ''
        for _, row in df.head(5).iterrows(): # ONLY 5 ENTRIES
            word = 'word: '
            for column in row[['word','english']]:
                if column != '-':
                    word += column + ' '
            text += word.strip() + '\n' + 'accent: ' + row['accent'] + '\n\n'
        return text.strip()
    else: # FOR WEB API
        lists = df.values.tolist() # RETURN LIST OF ['word','accent','english']
        lists = [[l[0]] + [accent_to_html(l[1])] + [l[2]] for l in lists] # CONVERT ACCENT TO HTML FORMAT
        return lists[:10] # ONLY 10 ENTRIES

def accent_to_html(accent:str) -> str:
    """
    convert accent text into html, class names are "accent_high" and "accent_low" 
    'あ\\いは/んす\\る' => <span class="accent_high">あ</span><span class="accent_low">いは</span>...
    """
    accent = re.sub(r'((?<=^)|(?<=\\))(\w+?)((?=/)|(?=$))', r'<span class="accent_low">\2</span>', accent)
    accent = re.sub(r'((?<=^)|(?<=/))(\w+?)((?=\\)|(?=$))', r'<span class="accent_high">\2</span>', accent)
    accent = re.sub(r'(?<!<)([/\\])', r'<span class="accent_bar">\1</span>', accent)
    return accent

########## GET RANKING & FREQ ##########

# ['lemma','rank','lForm','pos','core_pmw']
BCCWJ_RANK = pd.read_csv('data/bccwj_rank.csv') 
def get_rank(word):
    yomi = hira2kata(yomikata(word))
    df = BCCWJ_RANK[(BCCWJ_RANK.lemma.str.contains(word)) | (BCCWJ_RANK.lForm == yomi)]
    if len(df) >= 2:
        result = df.iloc[0:3].values.tolist()
        # if lForm and pos are completely identical, drop
        if len(result) ==3 and result[2][2:4] == result[0][2:4]:
            result = result[:2]
        if result[1][2:4] == result[0][2:4]:
            result = [result[0]]
    elif len(df) == 1:
        result = [df.iloc[0].tolist()]
    else:
        return None
    # PoS Thai
    pos_mapping = {'動詞':'กริยา','名詞':'คำนาม','形容詞':'i-adj','助詞':'คำช่วย','助動詞':'คำช่วยที่ผันรูป','副詞':'adv','接頭辞':'prefix','接尾辞':'suffix',
        '連体詞':'คำขยายคำนาม','記号':'เครื่องหมาย','感動詞':'คำอุทาน','フィラー':'filler','接続詞':'คำเชื่อม','その他':'others'}
    for r in result:
        if r[3] in pos_mapping:
            r[3] += f' {pos_mapping[r[3]]}'
    return [list(map(str, row)) for row in result] # stringify

########## GET PARALLEL CORPUS ##########

NHK_PARALLEL = pd.read_json('data/nhkparallel.json')
def get_parallel(genre:str, keyword:str):
    mask = (NHK_PARALLEL.genre.str.contains(genre)) & (NHK_PARALLEL.article_easy_ruby.str.contains(keyword) | NHK_PARALLEL.article.str.contains(keyword))
    df = NHK_PARALLEL[mask].sort_values('datePublished', ascending=False)
    df['datePublished'] = df.datePublished.apply(lambda x:x[2:10].replace('-', '/')) # "2013-04-07T18:09" -> "13/04/07"
    df = df[['id','datePublished', 'genre', 'title_easy_ruby','article_easy_ruby','title','article', ]]
    # highlight keyword in 'title_easy_ruby', 'article_easy_ruby', 'title', 'article'
    # if has more than one genre, replace "_" with <br> 
    return [[r[0], r[1], r[2].replace('_', '<br><br>')] + [highlight(x, keyword) for x in r[3:]] for r in df.values.tolist()]

def highlight(text:str, keyword:str):
    """
    highlight keyword in the text
    wrapped with <span class="red">...</span>
    """
    if keyword == "":
        return text
    return text.replace(keyword, f'<span class="red">{keyword}</span>')

########## GET RANDOM NHK EASY ARTICLE ##########
NHKEASY_DATA = data = pd.read_csv('data/nhkeasy.csv')
def get_nhkeasy():
    r = random.randint(0, len(NHKEASY_DATA)-1)
    row = NHKEASY_DATA.iloc[r]
    return row['date'], row['title'], row['article']

########## funcs for wiki search ############

def remove_tag(text):
    text = re.sub(r'</?.+?>', '', text)
    text = re.sub(r'&#91;.+?&#93;', '', text)
    text = re.sub(r'&#.+?;', '', text)
    return text.strip()

def get_wiki(word):
    url = f'https://ja.wikipedia.org/wiki/{word}'
    response = requests.get(url)
    if response.status_code != 200:
        return 'หาไม่เจอในดิกครับ\n(พิมพ์ help จะแสดงวิธีใช้)'
    else:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        try:
            newurl = urllib.parse.unquote(soup.find('link', rel='canonical').get('href'))
        except:
            newurl = url

        # get only 1st paragraph <p><b>entry</b> ..... </p>
        content = re.search(r'<p>([『「]?<b>[\s\S]+?)</p>', html).group(1)
        content = remove_tag(content)
        
        if re.match(r'.{1,12}(\s*[\(（].+[\)）])?$', content): # content has only entry name 
            entries = soup.select('#bodyContent')
            entries = re.findall(r'<li><a.+?>(.+?)</li>', str(entries))
            return 'もしかして…\n' + '\n'.join(['・' + remove_tag(entry) for entry in entries if not re.search(r'(曖昧さ回避|ページの一覧)', entry)]) + '\n\n' + newurl
        else:
            content = re.sub(r'[,，]\s*聴く\[ヘルプ/ファイル\]', '', content)
            content = re.sub(r'\(音声ファイル\)', '', content)
            return content.strip() + '\n\n' + newurl
