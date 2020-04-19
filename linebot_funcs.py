import re, requests, json
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd


def toNchr(morph:str, n=3) -> str:
    """
    function for adjusting result columns
    convert into N characters text by filling full spaces
    
    >>> toNchr('で', 4)
    'で　　　　' 1 chr with 4 full spaces
    """
    return morph + (n-len(morph)) * '　'


def load_dic():
    with open('data/kanjidic.json','r', encoding='utf8') as f:
        dic = json.load(f)
    return dic

def search_kanji(dic, kanji:str):
    content = dic[kanji]
    on = content['on']
    kun = content['kun']
    imi = content['imi']
    bushu = content['bushu']
    kanken = content['kanken']
    reply = f"onyomi: {on}\nkunyomi: {kun}\nความหมาย:\n{imi}\nbushu: {bushu}\nkanken level: {kanken}"
    return reply


def get_accent(word):
    df = pd.read_csv('data/accent.csv', encoding='utf8')
    result = df[df.kanji.str.contains(word, na=False) | df.yomi.str.contains(word, na=False) | df.english.str.contains(word, na=False, case=False)]
    if len(result) == 0:
        return 'หาไม่เจอในดิกครับ\n(พิมพ์ help จะแสดงวิธีใช้)'
    else:
        text = ''
        for i, row in result.iterrows():
            word = 'word: '
            for column in row[['kanji','yomi','english']]:
                if type(column) == str:
                    word += column + ' '
            text += word.strip() + '\n' + 'accent: ' + row['accent'] + '\n\n'
    return text.strip()


##### funcs for wiki search #####

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
