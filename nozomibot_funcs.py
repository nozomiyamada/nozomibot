import re, requests, json
from JpTextProcessing import yomikata, hira2kata
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd
import numpy as np


def toNchr(morph:str, n=3) -> str:
    """
    function for adjusting result columns (for Linebot)
    convert into N characters text by filling full spaces
    
    >>> toNchr('で', 4)
    'で　　　　' 
    --- 1 chr with 4 full spaces
    """
    return morph + (n-len(morph)) * '　'


########## KANJI DICT ##########

# load dictionary
with open('data/kanji.json','r', encoding='utf8') as f:
    KANJI_DICT = json.load(f)

def get_kanji(kanji:str, format_for_linebot=True):
    """
    get kanji from dictionary 
    key is kanji, value is dictionary {'会':{...}, '眠':{...}}
    """
    content = KANJI_DICT.get(kanji, None)
    if format_for_linebot:
        if content == None:
            return 'ขอโทษที่หาไม่เจอในดิกครับ'
        on = content['on']
        kun = content['kun']
        imi = '\n'.join(content['imi'])
        bushu = content['bushu']
        kanken = content['kanken']
        return f"onyomi: {on}\nkunyomi: {kun}\nความหมาย:\n{imi}\nbushu: {bushu}\nkanken level: {kanken}"
    else:
        return content # dict


########## ACCENT ##########

# load dictionary
ACCENT_DICT = pd.read_csv('data/accent.csv', encoding='utf8').fillna('-') # nan -> "-"

def get_accent(word:str, format_for_linebot=True):
    """
    get accent from table 
    header = accent, word, yomi, english
    'accent' is primary key, written in Katakana e.g. カ/ンシン
    'word' may contain several entries e.g. 関心・感心
    'yomi' is kana of word
    """
    if len(word) == 0:
        return None if format_for_linebot else []
    # WHERE clause
    mask = (ACCENT_DICT.word.str.contains(word)) | (ACCENT_DICT.yomi.str.contains(word)) | ACCENT_DICT.english.str.contains(word,case=False)
    df = ACCENT_DICT[mask]
    df['length_word'] = df.word.apply(len)
    df['length_yomi'] = df.yomi.apply(len)
    df = df.sort_values(['length_yomi','length_word']) # ORDER BY LENGTH(yomi), LENGTH(word)
    if len(df) == 0:
        return None if format_for_linebot else []
    elif format_for_linebot:
        text = ''
        for i, row in df.iterrows():
            word = 'word: '
            for column in row[['word','yomi','english']]:
                if column != '-':
                    word += column + ' '
            text += word.strip() + '\n' + 'accent: ' + row['accent'] + '\n\n'
            if i > 5: # only 5 entries
                break
        return text.strip()
    else: # for WEB API
        lists = df.values.tolist() # return list of [accent, word, yomi, english]
        lists = [[accent_to_html(l[0])] + l[1:] for l in lists] # change accent to html format
        return lists[:10] # only 10 entries

def accent_to_html(accent:str) -> str:
    """
    convert accent text into html, class names are "accent_high" and "accent_low" 
    'あ\いは/んす\る' => <span class="accent_high">あ</span><span class="accent_low">いは</span>...
    """
    match = re.match(r'(.+?)([/\\].*)', accent) # capture first 1-2 chrs and remainings
    if match.group(2)[0] == '/':
        html = f'<span class="accent_low">{match.group(1)}</span><span class="accent_bar">/</span>'
        is_high = True
    else:
        html = f'<span class="accent_high">{match.group(1)}</span><span class="accent_bar">\\</span>'
        is_high = False
    accent = match.group(2)[1:] # cut first 1 character = / or \
    while '/' in accent or '\\' in accent: # repeat the same thing
        if is_high:
            next_tone_index = accent.index('\\')
            html += f'<span class="accent_high">{accent[:next_tone_index]}</span><span class="accent_bar">\\</span>'
        else:
            next_tone_index = accent.index('/')
            html += f'<span class="accent_low">{accent[:next_tone_index]}</span><span class="accent_bar">/</span>'
        accent = accent[next_tone_index+1:]
        is_high = not is_high
    if is_high: # the last portion
        html += f'<span class="accent_high">{accent}</span>'
    else:
        html += f'<span class="accent_low">{accent}</span>'
    return html


########## GET WORD FROM DICTIONARY ##########

# load dictionary [yomi,word,thai]
WORD_DICT = pd.read_csv('data/jtdic.csv', encoding='utf8').fillna('-') # nan -> "-"

def get_word(word:str, format_for_linebot=True):
    # SEARCH BY THAI WORD
    if re.search(r'[ก-๙]+', word):
        df = WORD_DICT[WORD_DICT.thai.str.contains(word)]
        df['length_thai'] = df.thai.apply(len)
        df['length_yomi'] = df.yomi.apply(len)
        df = df.sort_values(['length_thai','length_yomi'])
    # SEARCH BY JAPANESE WORD
    else:
        df = WORD_DICT[(WORD_DICT.word.str.contains(word)) | (WORD_DICT.yomi.str.contains(word))]
        df['length_word'] = df.word.apply(len)
        df['length_yomi'] = df.yomi.apply(len)
        df = df.sort_values(['length_word','length_yomi'])
        if len(df) == 0: # if no results, convert word into Kana and search again
            yomi = yomikata(word)
            df = WORD_DICT[WORD_DICT.yomi.str.contains(yomi)]
            df['length_word'] = df.word.apply(len)
            df['length_yomi'] = df.yomi.apply(len)
            df = df.sort_values(['length_word','length_yomi'])

    if len(df) == 0:
        return []
    elif format_for_linebot:
        return '\n'.join([' '.join(x) for x in df[['word','yomi','thai']].values.tolist()[:20]])
    else:
        return df.values.tolist()[:100]


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
        result = []
    # PoS Thai
    pos_mapping = {'動詞':'กริยา','名詞':'คำนาม','形容詞':'i-adj','助詞':'คำช่วย','助動詞':'คำช่วยที่ผันรูป','副詞':'adv','接頭辞':'prefix','接尾辞':'suffix',
        '連体詞':'คำขยายคำนาม','記号':'เครื่องหมาย','感動詞':'คำอุทาน','フィラー':'filler','接続詞':'คำเชื่อม','その他':'others'}
    for r in result:
        if r[3] in pos_mapping:
            r[3] += f' {pos_mapping[r[3]]}'
    return result

########## GET PARALLEL CORPUS ##########

NHK_PARALLEL = pd.read_json('data/nhk_parallel.json')
def get_parallel(genre:str, keyword:str):
    mask = (NHK_PARALLEL.genre.str.contains(genre)) & (NHK_PARALLEL.article_easy_ruby.str.contains(keyword) | NHK_PARALLEL.article.str.contains(keyword))
    df = NHK_PARALLEL[mask].sort_values('datePublished', ascending=False)
    df['datePublished'] = df.datePublished.apply(lambda x:x[2:10].replace('-', ' '))
    df = df[['title_easy_ruby','article_easy_ruby','title','article','datePublished', 'genre']]
    # highlight keyword in the text except for genre
    # if has more than one genre, replace "_" with <br> 
    return [[highlight(x, keyword) for x in record[:-1]] + [record[-1].replace('_', '<br><br>')] for record in df.values.tolist()]

def highlight(text:str, keyword:str):
    """
    highlight keyword in the text
    wrapped with <span class="red">...</span>
    """
    if keyword == "":
        return text
    return text.replace(keyword, f'<span class="red">{keyword}</span>')


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
