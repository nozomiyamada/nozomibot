import MeCab, re, requests, random, json
tagger = MeCab.Tagger()
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd
from JapaneseCharacterTypes import JapaneseCharacterTypes as Type
import enum

###### text processing ######

class JapaneseCharacterTypes(enum.Enum):
    NOT_JAPANESE = -1
    HIRAGANA = 0 
    KATAKANA = 1 
    KANJI = 2
    
def japanese_type_of(char: str) -> Type:
    if 'ア' <= char <= 'ヶ':
        return Type.KATAKANA
    elif 'あ' <= char <= 'ゖ':
        return Type.HIRAGANA
    elif '一' <= char >= '鿯':
        return Type.KANJI
    else:
        return Type.NOT_JAPANESE

def tokenize(text:str) -> list:
    """
    tokenize sentence into list of tokens with linguistic features
    0:surface form, 1:pos, 2:pos2, 3:pos3, 4:pos4, 5:conjugation type, 6:conjugation form, 7:lemma, 8:phono, 9:phone

    >>> tokenize('大きい家は走りたくなるな')
    [['大きい', '形容詞', '自立', '*', '*', '形容詞・イ段', '基本形', '大きい', 'オオキイ', 'オーキイ'],
    ['家', '名詞', '一般', '*', '*', '*', '*', '家', 'イエ', 'イエ'],
    ['は', '助詞', '係助詞', '*', '*', '*', '*', 'は', 'ハ', 'ワ'],
    ['走り', '動詞', '自立', '*', '*', '五段・ラ行', '連用形', '走る', 'ハシリ', 'ハシリ'],
    ['たく', '助動詞', '*', '*', '*', '特殊・タイ', '連用テ接続', 'たい', 'タク', 'タク'],
    ['なる', '動詞', '自立', '*', '*', '五段・ラ行', '基本形', 'なる', 'ナル', 'ナル'],
    ['な', '助詞', '終助詞', '*', '*', '*', '*', 'な', 'ナ', 'ナ']]
    """
    # exclude final two tokens : 'EOS', ''
    tokens = tagger.parse(text).split('\n')[:-2]
    return [re.split(r'[,\t]', token) for token in tokens]

def hira2kata(hiragana:str) -> str:
    """
    convert hiragana text into katakana

    >>> hira2kata('あした５じにマルキュー')
    'アシタ５ジニマルキュー'
    """
    return ''.join([chr(ord(c)+96) if 'あ' <= c <= 'ゖ' else c for c in hiragana]) 

def kata2hira(katakana:str) -> str:
    """
    convert katakana text into hiragana
    """
    return ''.join([chr(ord(c)-96) if 'ア' <= c <= 'ゖ' else c for c in katakana])

def yomikata(text:str) -> str:
    """
    convert JP text into hiragana text

    >>> yomikata('心掛け')
    こころがけ
    """
    return ''.join([kata2hira(token[-2]) for token in tokenize(text)]).replace('*', '')

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

def toNchr(morph:str, n=3) -> str:
    """
    convert into N characters text by filling full spaces
    
    >>> toNchr('で', 5)
    'で　　　　' 1 chr with 4 full spaces
    """
    return morph + (n-len(morph)) * '　'

def verb_group(conjtype:str) -> str:
    """
    >>> verb_group('五段・カ行')
    '1'
    """
    return {'五段':'1', '一段':'2', 'サ変':'3', 'カ変':'3'}.get(conjtype[:2], '')

def masuform(verb_base:str, conjtype:str) -> str:
    """
    group1 base form -> masu form
    masuform('書く', '五段・カ行') >>> '書きます'
    masuform('なさる') >>> 'なさいます'
    """
    if verb_base in ['なさる','くださる','おっしゃる','いらっしゃる']:
        return verb_base[:-1] + 'います'
    elif conjtype[:2] == '五段':
        stem = verb_base[:-1]
        gyou = kata2hira(conjtype[3]) # '五段・カ行' -> か 
        if gyou == 'わ':
            gyou = 'あ'
        return stem + shift_dan(gyou, 1) + 'ます'

def teform(verb_base:str) -> str:
    """
    group1 base form -> te form
    teform('書く') >>> '書いて'
    """
    if verb_base == '行く':
        return '行って'
    elif verb_base[-1] in ['う','つ','る']:
        return verb_base[:-1] + 'って'
    elif verb_base[-1] in ['ぬ','む','ぶ']:
        return verb_base[:-1] + 'んで'
    elif verb_base[-1] == 'く':
        return verb_base[:-1] + 'いて'
    elif verb_base[-1] == 'ぐ':
        return verb_base[:-1] + 'いで'
    elif verb_base[-1] == 'す':
        return verb_base[:-1] + 'して'

def verb_conj(lemma:str, conjtype:str):
    """
    nai, nakatta, masu, base, te, ta, imperative, conditional, potential, volitional : 10　forms
    行く, 五段・カ行促音 >>> ['行かない', '行かなかった',...]
    """
    group = conjtype[:2] # conjugation = 五段・カ行, 一段
    
    if group == 'サ変' or lemma == 'する':
        nai = 'しない'
        nakatta = 'しなかった'
        masu = 'します'
        base = 'する'
        te = 'して'
        ta = 'した'
        imp = 'しろ'
        con = 'すれば'
        pot = 'できる'
        vol = 'しよう'
    
    elif group == 'カ変':
        nai = 'こない'
        nakatta = 'こなかった'
        masu = 'きます'
        base = 'くる'
        te = 'きて'
        ta = 'きた'
        imp = 'こい'
        con = 'くれば'
        pot = 'こられる'
        vol = 'こよう'
    
    elif group == '一段' or lemma == 'いる':
        stem = lemma[:-1]  # e.g. 食べる -> 食べ
        nai = stem +  'ない'
        nakatta = stem + 'なかった'
        masu = stem + 'ます'
        base = stem + 'る'
        te = stem + 'て'
        ta = stem + 'た'
        imp = stem + 'ろ'
        con = stem + 'れば'
        pot = stem + 'られる'
        vol = stem + 'よう'
    
    elif group == '五段':
        gyou = kata2hira(conjtype[3])  # e.g. 五段・カ行　-> か, convert into ア if ワ
        stem = lemma[:-1]  # e.g. 行く -> 行, つながる -> つなが
        
        # aru
        if lemma in ['ある','有る','在る']:
            nai = 'ない'
            nakatta = 'なかった'
            pot = 'ありえる'
        else:
            nai = stem + gyou + 'ない'
            nakatta = stem + gyou + 'なかった'
            # wa gyou -> a gyou
            if gyou == 'わ': 
                gyou = 'あ'
            pot = stem + shift_dan(gyou, 3) + 'る'
        masu = masuform(lemma, conjtype)
        base = lemma
        te = teform(base)
        ta = te[:-1] + te[-1].replace('て','た').replace('で','だ')
        imp = stem + shift_dan(gyou, 3)
        con = stem + shift_dan(gyou, 3) + 'ば'
        vol = stem + shift_dan(gyou, 4) + 'う'
    
    return f'ない形:　　 {nai}\nなかった形: {nakatta}\nます形:　　 {masu}\n辞書形:　　 {base}\nて形:　　　 {te}\nた形:　　　 {ta}\nば形:　　　 {con}\n命令形:　　 {imp}\n可能形:　　 {pot}\n意志形:　　 {vol}' 


def adj_conj(lemma:str):
    """
    nai, nakatta, desu, base, te, ta, conditional, adverb : 8
    """
    stem = lemma[:-1]
    if lemma == 'ない':
        nai = 'ない'
        nakatta = 'なかった'
    elif lemma == '無い':
        nai = '無い'
        nakatta = '無かった'
    else:    
        nai = stem + 'くない'
        nakatta = stem + 'くなかった'
    desu = stem + 'いです'
    base = lemma
    te = stem + 'くて'
    ta = stem + 'かった'
    con = stem + 'ければ'
    adv = stem + 'く'
    return f'ない形:　　 {nai}\nなかった形: {nakatta}\nです形:　　 {desu}\n辞書形:　　 {base}\nて形:　　　 {te}\nた形:　　　 {ta}\nば形:　　　 {con}\n副詞化:　　 {adv}' 

##### kanji mode functions #####

def is_joyo(kanji):
    joyo = """亜哀挨愛曖悪握圧扱宛嵐安案暗以衣位囲医依委威為畏胃尉異移萎偉椅彙意違維慰遺緯域育一壱逸茨芋引印因咽姻
            員院淫陰飲隠韻右宇羽雨唄鬱畝浦運雲永泳英映栄営詠影鋭衛易疫益液駅悦越謁閲円延沿炎怨宴媛援園煙猿遠鉛塩
            演縁艶汚王凹央応往押旺欧殴桜翁奥横岡屋億憶臆虞乙俺卸音恩温穏下化火加可仮何花佳価果河苛科架夏家荷華菓
            貨渦過嫁暇禍靴寡歌箇稼課蚊牙瓦我画芽賀雅餓介回灰会快戒改怪拐悔海界皆械絵開階塊楷解潰壊懐諧貝外劾害崖
            涯街慨蓋該概骸垣柿各角拡革格核殻郭覚較隔閣確獲嚇穫学岳楽額顎掛潟括活喝渇割葛滑褐轄且株釜鎌刈干刊甘汗
            缶完肝官冠巻看陥乾勘患貫寒喚堪換敢棺款間閑勧寛幹感漢慣管関歓監緩憾還館環簡観韓艦鑑丸含岸岩玩眼頑顔願
            企伎危机気岐希忌汽奇祈季紀軌既記起飢鬼帰基寄規亀喜幾揮期棋貴棄毀旗器畿輝機騎技宜偽欺義疑儀戯擬犠議菊
            吉喫詰却客脚逆虐九久及弓丘旧休吸朽臼求究泣急級糾宮救球給嗅窮牛去巨居拒拠挙虚許距魚御漁凶共叫狂京享供
            協況峡挟狭恐恭胸脅強教郷境橋矯鏡競響驚仰暁業凝曲局極玉巾斤均近金菌勤琴筋僅禁緊錦謹襟吟銀区句苦駆具惧
            愚空偶遇隅串屈掘窟熊繰君訓勲薫軍郡群兄刑形系径茎係型契計恵啓掲渓経蛍敬景軽傾携継詣慶憬稽憩警鶏芸迎鯨
            隙劇撃激桁欠穴血決結傑潔月犬件見券肩建研県倹兼剣拳軒健険圏堅検嫌献絹遣権憲賢謙鍵繭顕験懸元幻玄言弦限
            原現舷減源厳己戸古呼固股虎孤弧故枯個庫湖雇誇鼓錮顧五互午呉後娯悟碁語誤護口工公勾孔功巧広甲交光向后好
            江考行坑孝抗攻更効幸拘肯侯厚恒洪皇紅荒郊香候校耕航貢降高康控梗黄喉慌港硬絞項溝鉱構綱酵稿興衡鋼講購乞
            号合拷剛傲豪克告谷刻国黒穀酷獄骨駒込頃今困昆恨根婚混痕紺魂墾懇左佐沙査砂唆差詐鎖座挫才再災妻采砕宰栽
            彩採済祭斎細菜最裁債催塞歳載際埼在材剤財罪崎作削昨柵索策酢搾錯咲冊札刷刹拶殺察撮擦雑皿三山参桟蚕惨産
            傘散算酸賛残斬暫士子支止氏仕史司四市矢旨死糸至伺志私使刺始姉枝祉肢姿思指施師恣紙脂視紫詞歯嗣試詩資飼
            誌雌摯賜諮示字寺次耳自似児事侍治持時滋慈辞磁餌璽鹿式識軸七𠮟失室疾執湿嫉漆質実芝写社車舎者射捨赦斜煮
            遮謝邪蛇尺借酌釈爵若弱寂手主守朱取狩首殊珠酒腫種趣寿受呪授需儒樹収囚州舟秀周宗拾秋臭修袖終羞習週就衆
            集愁酬醜蹴襲十汁充住柔重従渋銃獣縦叔祝宿淑粛縮塾熟出述術俊春瞬旬巡盾准殉純循順準潤遵処初所書庶暑署緒
            諸女如助序叙徐除小升少召匠床抄肖尚招承昇松沼昭宵将消症祥称笑唱商渉章紹訟勝掌晶焼焦硝粧詔証象傷奨照詳
            彰障憧衝賞償礁鐘上丈冗条状乗城浄剰常情場畳蒸縄壌嬢錠譲醸色拭食植殖飾触嘱織職辱尻心申伸臣芯身辛侵信津
            神唇娠振浸真針深紳進森診寝慎新審震薪親人刃仁尽迅甚陣尋腎須図水吹垂炊帥粋衰推酔遂睡穂随髄枢崇数据杉裾
            寸瀬是井世正生成西声制姓征性青斉政星牲省凄逝清盛婿晴勢聖誠精製誓静請整醒税夕斥石赤昔析席脊隻惜戚責跡
            積績籍切折拙窃接設雪摂節説舌絶千川仙占先宣専泉浅洗染扇栓旋船戦煎羨腺詮践箋銭潜線遷選薦繊鮮全前善然禅
            漸膳繕狙阻祖租素措粗組疎訴塑遡礎双壮早争走奏相荘草送倉捜挿桑巣掃曹曽爽窓創喪痩葬装僧想層総遭槽踪操燥
            霜騒藻造像増憎蔵贈臓即束足促則息捉速側測俗族属賊続卒率存村孫尊損遜他多汰打妥唾堕惰駄太対体耐待怠胎退
            帯泰堆袋逮替貸隊滞態戴大代台第題滝宅択沢卓拓託濯諾濁但達脱奪棚誰丹旦担単炭胆探淡短嘆端綻誕鍛団男段断
            弾暖談壇地池知値恥致遅痴稚置緻竹畜逐蓄築秩窒茶着嫡中仲虫沖宙忠抽注昼柱衷酎鋳駐著貯丁弔庁兆町長挑帳張
            彫眺釣頂鳥朝貼超腸跳徴嘲潮澄調聴懲直勅捗沈珍朕陳賃鎮追椎墜通痛塚漬坪爪鶴低呈廷弟定底抵邸亭貞帝訂庭逓
            停偵堤提程艇締諦泥的笛摘滴適敵溺迭哲鉄徹撤天典店点展添転塡田伝殿電斗吐妬徒途都渡塗賭土奴努度怒刀冬灯
            当投豆東到逃倒凍唐島桃討透党悼盗陶塔搭棟湯痘登答等筒統稲踏糖頭謄藤闘騰同洞胴動堂童道働銅導瞳峠匿特得
            督徳篤毒独読栃凸突届屯豚頓貪鈍曇丼那奈内梨謎鍋南軟難二尼弐匂肉虹日入乳尿任妊忍認寧熱年念捻粘燃悩納能
            脳農濃把波派破覇馬婆罵拝杯背肺俳配排敗廃輩売倍梅培陪媒買賠白伯拍泊迫剝舶博薄麦漠縛爆箱箸畑肌八鉢発髪
            伐抜罰閥反半氾犯帆汎伴判坂阪板版班畔般販斑飯搬煩頒範繁藩晩番蛮盤比皮妃否批彼披肥非卑飛疲秘被悲扉費碑
            罷避尾眉美備微鼻膝肘匹必泌筆姫百氷表俵票評漂標苗秒病描猫品浜貧賓頻敏瓶不夫父付布扶府怖阜附訃負赴浮婦
            符富普腐敷膚賦譜侮武部舞封風伏服副幅復福腹複覆払沸仏物粉紛雰噴墳憤奮分文聞丙平兵併並柄陛閉塀幣弊蔽餅
            米壁璧癖別蔑片辺返変偏遍編弁便勉歩保哺捕補舗母募墓慕暮簿方包芳邦奉宝抱放法泡胞俸倣峰砲崩訪報蜂豊飽褒
            縫亡乏忙坊妨忘防房肪某冒剖紡望傍帽棒貿貌暴膨謀頰北木朴牧睦僕墨撲没勃堀本奔翻凡盆麻摩磨魔毎妹枚昧埋幕
            膜枕又末抹万満慢漫未味魅岬密蜜脈妙民眠矛務無夢霧娘名命明迷冥盟銘鳴滅免面綿麺茂模毛妄盲耗猛網目黙門紋
            問冶夜野弥厄役約訳薬躍闇由油喩愉諭輸癒唯友有勇幽悠郵湧猶裕遊雄誘憂融優与予余誉預幼用羊妖洋要容庸揚揺
            葉陽溶腰様瘍踊窯養擁謡曜抑沃浴欲翌翼拉裸羅来雷頼絡落酪辣乱卵覧濫藍欄吏利里理痢裏履璃離陸立律慄略柳流
            留竜粒隆硫侶旅虜慮了両良料涼猟陵量僚領寮療瞭糧力緑林厘倫輪隣臨瑠涙累塁類令礼冷励戻例鈴零霊隷齢麗暦歴
            列劣烈裂恋連廉練錬呂炉賂路露老労弄郎朗浪廊楼漏籠六録麓論和話賄脇惑枠湾腕"""
    return kanji in joyo

def load_dic():
    with open('kanjidic.json','r', encoding='utf8') as f:
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

##### accent #####
def get_accent(word):
    df = pd.read_csv('accent.csv', encoding='utf8')
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


##### wiki #####

def remove_tag(text):
    text = re.sub(r'</?.+?>', '', text)
    text = re.sub(r'&#91;.+?&#93;', '', text)
    text = re.sub(r'&#.+?;', '', text)
    return text.strip()

def get_wiki(word):
    url = f'https://ja.wikipedia.org/wiki/{word}'
    response = requests.get(url)
    if response.status_code != 200:
        return random.choice(['หาไม่เจออ่า','พิมพ์ผิดป่าว','ไม่มีครัช'])
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
