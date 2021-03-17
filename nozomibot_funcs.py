import re, requests, json, os, random, csv, time, urllib.parse, mysql.connector
import pandas as pd
pd.set_option('mode.chained_assignment', None) # make warning invisible
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from JpProcessing import *


##### ENVIRONMENT VARIABLES #####
from dotenv import load_dotenv
load_dotenv()

### LINE BOT
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]

### FB BOT
FB_ACCESS_TOKEN = os.environ["FB_ACCESS_TOKEN"]
FB_VERIFY_TOKEN = os.environ["FB_VERIFY_TOKEN"]

SQL_HOSTNAME = os.environ["SQL_HOSTNAME"]
SQL_USERNAME = os.environ["SQL_USERNAME"]
SQL_PASSWORD = os.environ["SQL_PASSWORD"]


##### CONNECT SQL FUNCTION #####
def connect_sql(database:str):
	config = {'user': SQL_USERNAME,
		'password': SQL_PASSWORD,
		'host': SQL_HOSTNAME,
		'database': database}
	con = mysql.connector.connect(**config)
	cursor = con.cursor()
	return con, cursor 

##### FUNCTION TO FILL SPACE FOR LINE OUTPUT #####
def toNchr(morph:str, n=3) -> str:
	"""
	function for adjusting result columns (for Linebot)
	convert into N characters text by filling full spaces
	
	>>> toNchr('で', 4)
	'で　　　　' 
	--- 1 chr with 4 full spaces
	"""
	return morph + (n-len(morph)) * '　'

def get_time_now():
	tz = time.tzname[0]
	if tz == 'UTC': # on EC2
		return str(datetime.now()+timedelta(hours=7)).split('.')[0]
	else: # on Local
		return str(datetime.now()).split('.')[0]

################################################################################
###  NOZOMIBOT MESSENGER CORE 
################################################################################

DESCRIPTION = """< วิธีใช้ >

1. พจนานุกรม (JTDic)
พิมพ์คำศัพท์ภาษาญี่ปุ่นหรือคำศัพท์ภาษาไทยเท่านั้น
(ไม่ใช่การแปลประโยค)

2. ตัดคำ
พิมพ์: ตัด (space) ประโยค
เช่น "ตัด 昨日の夜は何を食べましたか"

3. ผันรูป
พิมพ์: ผัน (space) กริยา
เช่น "ผัน 食べた"

4. วิธีอ่าน (Roman)
พิมพ์: อ่าน (space) ประโยค
เช่น "อ่าน 昨日NHKを見ましたか"

5.  พจนานุกรมคันจิ
พิมพ์: คันจิ (space) คันจิตัวเดียว
เช่น "คันจิ 望"

6. Accent
พิมพ์: accent (space) คำ
เช่น "accent 山田"

7. สุ่มเลือกบทความ NHK News Easy
พิมพ์ "NHK" เท่านั้น

8. ตัวอย่างประโยคจาก NHK News
พิมพ์: ตัวอย่าง (space) คำ
เช่น "ตัวอย่าง 発表"

9. ตัวอย่างประโยคจาก Twitter
พิมพ์: tweet (space) คำ
เช่น "tweet コロナ"

10. wikipedia
พิมพ์: วิกิ (space) คำ
เช่น "วิกิ バンコク"

11. Joshi Quiz 
พิมพ์: "じょしテスト" "じょしクイズ" 

หากพบข้อผิดพลาดหรือ bug ต่างๆ กรุณาแจ้งให้ทราบด้วยการพิมพ์ "feedback" เว้นวรรค แล้วตามด้วยข้อความของคุณ เช่น "feedback พบคำที่สะกดผิดครับ"

---

Nozomibot Web Version

https://www.nozomi.ml/"""

def get_reply(text:str):
	text = re.sub(r'[\s\t]+', ' ', text) # multiple spaces -> one half space
	# mode select
	if re.match(r'(help|使い方|วิธีใช้|ใช้ยังไง|ヘルプ)\s*$', text, flags=re.I):
		MODE = '0.HELP'
	elif re.match(r'(分けて|切って|token(ize)?|ตัด(คำ|ประโยค)?) ', text, flags=re.I):
		MODE = '2.TOKENIZE'
	elif re.match(r'(活用|conj(ugate)?|ผัน(รูป)?) ', text, flags=re.I):
		MODE = '3.CONJ'
	elif re.match(r'(อ่าน(ว่า)?|読み(方)?|โรมัน|ローマ字|roman) ', text, flags=re.I):
		MODE = '4.ROMAN'
	elif re.match(r'(漢字|คันจิ|kanji) .+$', text, flags=re.I):
		MODE = '5.KANJI'
	elif re.match(r'(accent|アクセント) ', text, flags=re.I):
		MODE = '6.ACCENT'
	elif re.match(r'NHK$', text, flags=re.I):
		MODE = '7.NHK-EASY'
	elif re.match(r'(corpus|例文|ตัวอย่าง) ',text, flags=re.I):
		MODE = '8.EXAMPLE-NHK'
	elif re.match(r'(twitter|tweet|ツイッター|ツイート|ทวีต) ',text, flags=re.I):
		MODE = '9.EXAMPLE-TWITTER'
	elif re.match(r'(วิกิ|wiki|ウィキ) ', text, flags=re.I):
		MODE = '10.WIKI'
	elif re.match(r'(สวัสดี|สบายดีไหม|สบายดีมั้ย|หวัดดี)(ครับ|ค่ะ|คะ)?\s*$', text):
		MODE = 'SAWASDEE'
	elif re.search(r'(((รัก|ชอบ)(คุณ|เ[ธท]อ))|(love you))\b', text, flags=re.I):
		MODE = 'LOVEYOU'
	elif re.match(r'(jojo|giogio|ジョジョ|โจโจ้)\s*$', text, flags=re.I):
		MODE = 'JOJO'
	elif re.match(r'feedback', text, flags=re.I):
		MODE = 'FEEDBACK'
	elif re.search(r'พี่โน|โนโซมิ', text):
		MODE = 'P-NO'
	elif len(text.split(' ')) > 1 and not \
		re.match(r'(help|使い方|วิธีใช้|ใช้ยังไง|ヘルプ|分けて|切って|token(ize)?|ตัด|活用|conj(ugate)?|ผัน(รูป)?|อ่าน(ว่า)?|読み(方)?|โรมัน|ローマ字|roman|漢字|คันจิ|kanji|accent|アクセント|NHK|corpus|例文|ตัวอย่าง|twitter|tweet|ツイッター|ツイート|ทวีต|วิกิ|wiki|ウィキ|สวัสดี|สบายดีไหม|สบายดีมั้ย|หวัดดี|jojo|giogio|ジョジョ|โจโจ้|feedback|พี่โน)', text, flags=re.I):
		MODE = 'EROOR'
	elif re.match(r'(助詞|じょし)(クイズ|テスト|くいず|てすと)', text) or re.match(r'joshi', text, flags=re.I):
		MODE = 'JOSHI_START'
	elif len(text) < 40:
		MODE = '1.DICT'
	else:
		MODE = 'LONG MESSAGE' # -> no reply or reply manually

	##### EXECUTE EACH MODE #####
	if MODE == '0.HELP':
		reply = DESCRIPTION

	elif MODE == '1.DICT':
		try:
			reply = get_word(text)
			if reply == None:
				reply = 'ขออภัยไม่พบคำนี้ในพจนานุกรมครับ\n(พิมพ์ "help" จะแสดงวิธีใช้)'
		except:
			reply = 'server error รอสักครู่นะครับ'

	elif MODE == '2.TOKENIZE':
		text = text.split(' ', 1)[1]
		tokens = tokenize(text, pos_thai=True) # token = [surface, phone, lemma, pos]
		if len(tokens) < 40:
			reply = '\n'.join([f'{toNchr(token[0])} {toNchr(token[1])} {toNchr(token[2])} {token[3]}' for token in tokens]) # SR, phone, lemma, pos
		else:
			reply = 'ประโยคยาวเกินไป ใช้เว็บเวอร์ชันแทนได้ไหมครับ\n\nhttps://www.nozomi.ml/tokenize'

	elif MODE == '3.CONJ':
		text = text.split(' ', 1)[1]
		r = conjugate(text)
		if r == None:
			reply = 'ผันไม่ได้ครับ ต้องเป็นกริยาหรือ i-adj เท่านั้น'
		elif len(r) == 10: # verb with
			reply = f'辞書形:　　 {r[0]}\nない形:　　 {r[1]}\nなかった形: {r[2]}\nます形:　　 {r[3]}\nて形:　　　 {r[4]}\nた形:　　　 {r[5]}\nば形:　　　 {r[6]}\n命令形:　　 {r[7]}\n意向形:　　 {r[8]}\n可能形:　　 {r[9]}'
		elif len(r) == 8:  # adj
			reply = f'辞書形:　　 {r[0]}\nない形:　　 {r[1]}\nなかった形: {r[2]}\nです形:　　 {r[3]}\nて形:　　　 {r[4]}\nた形:　　　 {r[5]}\nば形:　　　 {r[6]}\n副詞化:　　 {r[7]}' 

	elif MODE == '4.ROMAN':
		text = text.split(' ', 1)[1]
		try:
			reply = romanize(text)
		except:
			reply = 'ขอโทษที่เปลี่ยนไม่ได้ครับ'

	elif MODE == '5.KANJI':
		kanji = text.split(' ', 1)[1]
		if len(kanji) > 1:
			reply = "พิมพ์คันจิตัวเดียวนะครับ"
		elif is_kanji(kanji) == False:
			reply = "พิมพ์คันจินะครับ"
		else:
			reply = get_kanji(kanji)

	elif MODE == '6.ACCENT':
		word = text.split(' ', 1)[1]
		reply = get_accent(word)
		if reply == None:
			reply = 'ขอโทษที่หาไม่เจอ accent ในดิกครับ'

	elif MODE == '7.NHK-EASY':
		date, title, article = get_nhkeasy()
		reply = f"{date}\n{title}\n\n{article}"

	elif MODE == '8.EXAMPLE-NHK':
		word = text.split(' ')[1]
		if len(text.split(' ')) >= 3: # 3rd argument = num of result e.g. NHK 発表 10
			try:
				limit = int(text.split(' ')[2])
			except:
				limit = 5
			if limit > 100:
				limit = 100
		else:
			limit = 5
		result = get_nhk(word, limit, highlighted=False)
		if result == None:
			reply = 'ขอโทษที่หาไม่เจอในคลังข้อมูลครับ'
		else:
			reply = ''
			for sentence in result:
				reply += '・' + sentence.strip() + '\n\n'
			reply = reply.strip()

	elif MODE == '9.EXAMPLE-TWITTER':
		query = text.split(' ')[1]
		if len(text.split(' ')) >= 3: # 3rd argument = num of result e.g. tweet 発表 10
			try:
				limit = int(text.split(' ')[2])
			except:
				limit = 5
			if limit > 100:
				limit = 100
		else:
			limit = 5
		result = get_tweet(query, limit, highlighted=False)
		if result == None:
			reply = 'ขอโทษที่หาไม่เจอในคลังข้อมูลครับ'
		else:
			reply = ''
			for tweet in result:
				reply += '・' + tweet.strip() + '\n\n'
			reply = reply.strip()

	elif MODE == '10.WIKI':
		word = text.split(' ', 1)[1]
		reply = get_wiki(word)

	elif MODE == 'SAWASDEE':
		reply = random.choice(['สวัสดีครับ','หวัดดี','เป็นไงบ้าง','ไปไหนมา','อ้วนขึ้นป่าว','ทำไรอยู่','สบายดีไหม','อยากกินหมูกระทะ','คิดถึงจังเลย','ฮัลโหล','หิวแล้วอ่ะ','เย่แล้ววว','ว้าวซ่า','กินข้าวรึยัง','กักตัวอยู่ไหม'])
	
	elif MODE == 'LOVEYOU':
		reply = random.choice(['ผมก็รักเธอเหมือนกัน','เขินจัง','อยู่ดีๆ อะไรนะ','ขอคิดก่อน','เป็นเพื่อนกันดีกว่า','ผมมีแฟนแล้ว ขอโทษ','ลองคบกันไหม','ยินดีครับ'])

	elif MODE == 'JOJO':
		with open('data/jojo.csv', 'r', encoding='utf8') as f:
			data = list(csv.reader(f))
			line = random.choice(data)
		reply = f'{line[0]}\n\n - {line[1]}, Part {line[2]}'

	elif MODE == 'FEEDBACK':
		reply = 'ขอบคุณมากที่ส่ง feedback และช่วยพัฒนาระบบครับ❤️'

	elif MODE == 'P-NO':
		reply = random.choice(['พี่โนเป็นคนสุดหล่อ','พี่โนเป็นคนใจดีสุดๆ','พี่โนเป็นคนสุดยอด','พี่โนชอบสเวนเซ่น','พี่โนชอบกินก๋วยเตี๋ยวเรือ','พี่โนเป็นทาสแมว','พี่โนกักตัวอยู่่','เลี้ยงข้าวพี่โนหน่อย','พี่โนชอบโจโจ้','ราเม็งญี่ปุ่นต้องเค็มๆ','ช่วงนี้อ้วนขึ้น','นกไปแล้ว พี่โนกำลังเศร้าอยู่'])
	
	elif MODE == 'EROOR':
		reply = "น่าจะใช้ผิดครับ พิมพ์ว่า help หรือกดเมนูด้านล่างจะแสดงวิธีใช้"

	elif MODE == 'JOSHI_START':
		reply = None

	elif MODE == 'LONG MESSAGE':
		reply = None

	return MODE, reply


def get_postback(postback:dict): # {action:joshi, type:格助詞, num:5, Q:0, score:0} -> return (text, labels:list, datas:list)
	if postback['action'] == 'joshi':
		joshi_type = postback.get('type', '格助詞') 
		max_num = int(postback.get('num', 10))
		q_num = int(postback.get('Q', 0))
		score = int(postback.get('score', 0))
		kanji_level = postback.get('level', None) # '1', '2', '3'
		answer_before = postback.get('answer', None)
		if kanji_level == None: # before start Q1
			datas = [
				f'action=joshi&type={joshi_type}&num={max_num}&Q=0&score=0&level=1',
				f'action=joshi&type={joshi_type}&num={max_num}&Q=0&score=0&level=2',
				f'action=joshi&type={joshi_type}&num={max_num}&Q=0&score=0&level=3',
				f'action=joshi&type={joshi_type}&num={max_num}&Q=0&score=0&level=4'
			]
			return 'เลือก Kanji Level', ['ง่าย','กลาง','ยาก','ยากมาก'], datas
		elif answer_before == None: # Q1
			text, answer, others = joshi_quiz(kanji_level, joshi_type) # '秋田県__人が総理大臣になるのは初めてです。', 'の', ['を', 'より', 'で', 'と']
			text = 'Q1: ' + text
		else:
			text, answer, others = joshi_quiz(kanji_level, joshi_type)
			text = f'Q{q_num} เฉลย: {answer_before}\n\nQ{q_num+1}: ' + text
		insert_i = random.randint(0,4)
		others.insert(insert_i, answer) # ['を', 'より', 'で', 'と'] -> ['を', 'より', 'で', 'の', 'と']
		datas = [f'action=joshi&type={joshi_type}&num={max_num}&Q={q_num+1}&score={score}&answer={answer}&level={kanji_level}'] * 5
		datas[insert_i] = f'action=joshi&type={joshi_type}&num={max_num}&Q={q_num+1}&score={score+1}&answer={answer}&level={kanji_level}' # correct answer
		if q_num < max_num:
			return text, others, datas
		else: # result
			if score == max_num:
				return f'Q{q_num} เฉลย: {answer_before}\n\nคะแนนของคุณ: {score}/{max_num}\nおめでとうございます！', None, None
			else:
				return f'Q{q_num} เฉลย: {answer_before}\n\nคะแนนของคุณ: {score}/{max_num}\nまたがんばって下さい！', None, None



################################################################################
###  FUNCTIONS TO GET INFORMATION
################################################################################

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


##########  EXAMPLE OF TWITTER  ##########
def get_tweet(query, limit=100, max_chr=35, highlighted=True):
	con, cursor = connect_sql('nozomibot')
	### get tweet at random 
	cursor.execute(f"SELECT tweet, username FROM tweetjp WHERE tweet LIKE '%{query}%' LIMIT 300;")
	result = list(cursor) # [[tweet, username],,]
	if len(result) == 0:
		return None
	#sentence_pattern = re.compile(r"""(?<=^)|(?<=[、。\s!\?！？…]) # the initial separator
	#			(?:[^、。\s!\?！？…]+?[、。\s!\?！？…]+){0,1} # sentence before query
	#			[^、。\s!\?！？…]*?""" + query + r"""[^、。\s!\?！？…]*?(?:[、。\s!\?！？…]+?|$)
	#			(?:[^、。\s!\?！？…]+?[、。\s!\?！？…]+){0,1} # sentence after query
	#			(?:[、。\s!\?！？…]+|$)""", re.X)
	sentence_pattern = re.compile(r'(?:^|[。\s!\?！？])([^。\s!\?！？]*?{}[^。\s!\?！？]*?(?:[。\s!\?！？]+|$))'.format(query))
	candidates = set()
	for tweet, _ in result:
		if len(tweet) < max_chr:
			candidates.add(tweet) # if the tweet is shorter max_chr, add whole text
		else:
			candidates |= set(re.findall(sentence_pattern, tweet)) # one tweet may contain multiple matched sentences
	candidates = set([x.strip() for x in candidates if len(x.strip()) >= len(query)+2]) # exclude too short sentences
	if len(candidates) > limit:
		candidates = random.sample(list(candidates), limit)
	if highlighted:
		candidates = [highlight(cand, query) for cand in candidates]
	con.close()
	return candidates


##########  EXAMPLE OF NHK NEWS WEB  ##########
def get_nhk(query, limit=100, highlighted=True):
	con, cursor = connect_sql('nozomibot')
	### get tweet at random 
	cursor.execute(f"SELECT id, article FROM nhkweb WHERE article LIKE '%{query}%' LIMIT 300;")
	result = list(cursor) # [[id, article],,]
	if len(result) == 0:
		return None
	sentence_pattern = re.compile(r'(?:^|[。\s!\?！？])([^。\s!\?！？]*?{}[^。\s!\?！？]*?(?:[。\s!\?！？]+|$))'.format(query))
	candidates = set()
	for _, article in result:
		candidates |= set(re.findall(sentence_pattern, article))
	candidates = set([x.strip() for x in candidates if len(x.strip()) >= len(query)+2 and len(x)>10]) # exclude too short sentences
	if len(candidates) > limit:
		candidates = random.sample(list(candidates), limit)
	if highlighted:
		candidates = [highlight(cand, query) for cand in candidates]
	con.close()
	return candidates


##########  GET WORD FROM DICTIONARY  ##########

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

##########  GET RANDOM NHK EASY ARTICLE  ##########
NHKEASY_DATA = data = pd.read_csv('data/nhkeasy.csv')
def get_nhkeasy():
	r = random.randint(0, len(NHKEASY_DATA)-1)
	row = NHKEASY_DATA.iloc[r]
	return row['date'], row['title'], row['article']

##########  WIKI SEARCH  ############

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


##########  JOSHI QUIZ  ##########

SENTS_EASY = pd.read_csv('data/short_sentence_easy.csv') # [[sent, sentruby, level],[],...]
SENTS_NORMAL = pd.read_csv('data/short_sentence_normal.csv') # [[sent, sentruby, level],[],...]
KAKUJOSHI = ['を','に','が','と','の','より','へ','から','で'] # 助詞-格助詞
FUKUJOSHI = ['は','か','も','など','や','まで','たり','ぐらい','だけ'] # 助詞-副助詞 / 助詞-係助詞
def joshi_quiz(level='1', joshi_type="格助詞"):
	if level == '1': # ง่าย
		df = SENTS_EASY[SENTS_EASY.level > 4.3]
	elif level == '2': # กลาง
		df = SENTS_EASY[(SENTS_EASY.level <= 4.3) & (SENTS_EASY.level > 3.6)]
	elif level == '3': # ยาก
		df = SENTS_EASY[SENTS_EASY.level < 3.6]
	elif level == '4': # ยากมาก
		df = SENTS_NORMAL
	sent = str(df.sample(1)['sent'].values[0])
	tokens = tokenize(sent)
	if joshi_type == '格助詞': # make index list of selected joshi
		joshi_index = [i for i, token in enumerate(tokens) if re.match(r'助詞-格助詞', token[4]) and token[0] in KAKUJOSHI] 
	elif joshi_type == '副助詞':
		joshi_index = [i for i, token in enumerate(tokens) if re.match(r'助詞-(副|係)助詞', token[4]) and token[0] in FUKUJOSHI]
	elif joshi_type == 'all':
		joshi_index = [i for i, token in enumerate(tokens) if re.match(r'助詞-(格|副|係)助詞', token[4]) and token[0] in FUKUJOSHI+KAKUJOSHI]
	if joshi_index == []:
		return joshi_quiz(level, joshi_type) # if not find, recurrsive
	selected_index = random.choice(joshi_index) # select one joshi at random
	answer = tokens[selected_index][0] # answer joshi
	tokens[selected_index][0] = '___' # mask answer
	### regenerate answer in order to balance
	if answer == 'の' and random.random() < 0.8:
		return joshi_quiz(level, joshi_type) # if の skip (80%) recurrsive
	elif answer in ['が','に','は'] and random.random() < 0.7:
		return joshi_quiz(level, joshi_type) 
	elif answer in ['を','て'] and random.random() < 0.6:
		return joshi_quiz(level, joshi_type)
	elif answer in ['と','で'] and random.random() < 0.5:
		return joshi_quiz(level, joshi_type)
	### make other choices
	if joshi_type == '格助詞':
		others = [x for x in KAKUJOSHI if x != answer]
	elif joshi_type == '副助詞':
		others = [x for x in FUKUJOSHI if x != answer]
	elif joshi_type == 'all':
		others = [x for x in KAKUJOSHI+FUKUJOSHI if x != answer]
	### remove ambiguous choice
	if answer in ['は', 'も'] and 'が' in others:
		others.remove('が')
	elif answer in ['が', 'も'] and 'は' in others:
		others.remove('は')
	random.shuffle(others)
	return ''.join([token[0] for token in tokens]), answer, others[:4] # '私__行きます', 'が', ['を','に','て','から']
