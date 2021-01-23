from flask import Flask, request, abort, render_template, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, PostbackEvent
from datetime import datetime, timedelta, timezone
import os, random, re, csv, time
import mysql.connector
from JpProcessing import *
from nozomibot_funcs import *

class CustomFlask(Flask):
	jinja_options = Flask.jinja_options.copy()
	jinja_options.update(dict(
		variable_start_string='((',
		variable_end_string='))',
	))

app = CustomFlask(__name__)

##### ENVIRONMENT VARIABLES #####
from dotenv import load_dotenv
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]

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


################################################################################
###  NOZOMIBOT WEB PAGE 
################################################################################

##### TOP PAGE : DICTIONARY & FEEDBACK #####
@app.route("/", methods=['GET', 'POST'])
def top_page():
	if request.method == 'GET':
		return render_template('dict.html', word='')
	elif request.method == 'POST':
		word = request.form['word']
		log_web('dict', word) # LOG SEARCH HISTORY
		if re.search(r'[ก-๙][ก-๙\.\-]+', word): # Thai word
			meaning = get_word(word, format_for_linebot=False)# [yomi,word,thai]
			if meaning == None:
				return jsonify({'none':'true'})
			return jsonify({'meaning':meaning, 'none':'false'})
		else:
			### get meaning
			meaning = get_word(word, format_for_linebot=False)
			### get conjugation & convert to list of list [['辞書形\nรูปดิก','行く'],[...],...]
			conj = conjugate(word.strip())
			if conj != None and len(conj) == 10: # verb
				conj = [x for x in zip(['辞書形\nรูปดิก','ない形\nรูป nai','なかった形\nรูป nakatta','ます形\nรูป masu',
				'て形\nรูป te','た形\nรูป ta','ば形\nรูป ba','命令形\nรูปคำสั่ง','意向形\nรูปตั้งใจ','可能形\nรูปสามารถ'], conj)]
			elif conj != None and len(conj) == 8: # adjective
				conj = [x for x in zip(['辞書形\nรูปดิก','ない形\nรูป nai','なかった形\nรูป nakatta','です形\nรูป desu',
				'て形\nรูป te','た形\nรูป ta','ば形\nรูป ba','副詞化\nadverb'], conj)]
			### get accent
			accent = get_accent(word, format_for_linebot=False)
			### get frequency
			freq = get_rank(word)
			### get kanji [[kanji, on, kun, imi],...]
			kanjis = []
			for char in word:
				if char in KANJI_DICT:
					kanji = get_kanji(char, format_for_linebot=False)
					if kanji != None and kanji not in kanjis:
						kanjis.append(kanji)
			if kanjis == []:
				kanjis = None

		### PRINT FOR DEBUGGING ###
		#print('\nCONJUGATION:', conj, '\n')
		#print('\nFREQUENCY:', freq, '\n')
		#print('\nKANJI:', kanjis, '\n')

		if all([x == None for x in (meaning, conj, accent, kanjis)]):
			return jsonify({'none':'true'})
		else:
			return jsonify({'meaning':meaning, 'conj':conj, 'accent':accent, 'freq':freq, 'kanji':kanjis, 'none':'false'})


##### TOKENIZE PAGE #####
@app.route("/tokenize", methods=['GET', 'POST'])
def web_tokenize():
	if request.method == 'GET':
		return render_template('tokenize.html')
	elif request.method == 'POST':
		text = request.form['text'].strip() # get POST parameters: input sentences
		log_web('tokenize', text) # LOG SEARCH HISTORY
		roman = romanize(text)
		tokens = tokenize(text) # ["住ん", "スン", "スム", "住む", "動詞-一般", "五段-マ行", "連用形-撥音便", "1"]
		tokens_thai = tokenize(text, pos_thai=True) # ['住ん', 'スン', '住む', 'กริยากลุ่ม1']
		# process POS tag
		new_tokens = [] # [[SR, Phone, Lemma, PoS],...]
		for token in tokens:
			new_pos = token[4].split('-')[:2] # e.g. '名詞-固有名詞-人名-姓' -> [名詞, 固有名詞]
			if token[4].startswith('動詞'):
				new_pos.append(token[5].split('-')[0]) # e.g. '五段-マ行' -> [動詞, 一般, 五段]
			new_tokens.append([token[0], token[1], token[3], '-'.join(new_pos)]) 
		
		### PRINT FOR DEBUGGING ###
		#print('\nROMAN:', roman, '\n')

		return jsonify({'tokens':new_tokens, 'tokens2':tokens_thai, 'roman':roman})


##### EXAMPLE PAGE #####
@app.route("/example", methods=['GET','POST'])
def web_example():
	if request.method == 'GET':
		return render_template('example.html')
	elif request.method == 'POST':
		word = request.form['word'].strip() # get POST parameters: input sentences
		log_web('example', word) # LOG SEARCH HISTORY
		### get tweet
		#s = time.time()
		tweet = get_tweet(word, limit=50, max_chr=60, highlighted=True)
		#print(time.time()-s)
		### get nhk
		nhk = get_nhk(word, limit=50, highlighted=True)
		#print(time.time()-s)
		# make result json
		result = {}
		if tweet != None:
			result['tweet'] = tweet
			result['tweet_num'] = len(tweet)
		if nhk != None:
			result['nhk'] = nhk
			result['nhk_num'] = len(nhk)
		return jsonify(result)


##### NHK PARALLEL CORPUS PAGE #####
@app.route("/nhk", methods=['GET','POST'])
def web_nhkweb():
	if request.method == 'GET':
		return render_template('nhk.html')
	elif request.method == 'POST':
		genre = request.form['genre'] # get POST parameters: genre
		keyword = request.form['keyword'].strip() # get POST parameters: input keyword
		log_web('nhk', f'{genre}_{keyword}') # LOG SEARCH HISTORY
		articles = get_parallel(genre, keyword) # id, title_easy_ruby, article_easy_ruby, title, article, date, genre 
		return jsonify({'article':articles, 'nums':len(articles)})


##### REQUEST & COMMENT AJAX #####
@app.route("/request", methods=['POST'])
def web_request():
	text = request.form['comment'].strip() # get POST parameters: text
	name = request.form['name'].strip() # get POST parameters: username
	try:
		con, cursor = connect_sql('nozomibot')
		date_now = get_time_now()
		cursor.execute(f"INSERT INTO feedback (date, feedback, name) VALUES (%s, %s, %s);", (date_now, text, name))
		con.commit()
		con.close()
	except Exception as e:
		print(e)
	return jsonify({'result':'success'})
	

##### SINGLE WORD SEARCH : SAME AS TOP PAGE #####
@app.route('/<word>', methods=['GET'])
def web_word(word):
	return render_template('dict.html', word=word)

########################################################################################################################

################################################################################
###  LINE WEBHOOK
################################################################################

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
	# get X-Line-Signature header value
	signature = request.headers['X-Line-Signature']

	# get request body as text
	body = request.get_data(as_text=True)
	#app.logger.info("Request body: " + body)

	# HANDLE WEBHOOK BODY
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)
	return 'OK'

""" EXAMPLE OF WEBHOOK
{
	"destination": "1654034294",
	"events": [
		{
			"replyToken": "0f3779fba3b349968c5d07db31eab56f",
			"type": "message",
			"mode": "active",
			"timestamp": 1462629479859,
			"source": {
				"type": "user",
				"userId": "Ua5a81fcab991a3f24e44ae4bfc89a"
			},
			"message": {
				"id": "325708",
				"type": "text",
				"text": "Hello, world"
			}
		},
		{
			"replyToken": "b60d432864f44d079f6d8efe86cf404b",
			"type": "postback",
			"mode": "active",
			"source": {
				"userId": "U91eeaf62d...",
				"type": "user"
			},
			"timestamp": 1513669370317,
			"postback": {
				"data": "storeId=12345",
				"params": {
					"datetime": "2017-12-25T01:00"
				}
			}
		},
		{
			"replyToken": "8cf9239d56244f4197887e939187e19e",
			"type": "follow",
			"mode": "active",
			"timestamp": 1462629479859,
			"source": {
				"type": "user",
				"userId": "U4af4980629..."
			}
		}
	]
}
"""

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	### RECEIVE MESSAGE
	text = str(event.message.text).strip()
	text = re.sub(r'[\s\t]+', ' ', text) # multiple spaces -> one half space

	### CONNECT SQL -> GET MODE & REPLY FROM TEXT
	con, cursor = connect_sql('nozomibot')
	mode, reply = get_reply(text, con, cursor)

	### GET USER INFO & INSERT INTO SQL LOG
	profile = line_bot_api.get_profile(event.source.user_id)
	date_now = get_time_now()
	cursor.execute(f"INSERT INTO log_line (date, mode, text, username, userid) VALUES (%s, %s, %s, %s, %s);", (date_now, mode, text, profile.display_name, profile.user_id))
	con.commit()
	con.close()
	
	### SEND REPLY
	line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(PostbackEvent)
def handle_postback(event):
	postback = str(event.postback.data).strip()
	if postback == 'richmenu_help':
		line_bot_api.reply_message(event.reply_token, TextSendMessage(text=DESCRIPTION))


@app.after_request
def after_request(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
	response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
	return response




################################################################################
###  NOZOMIBOT LINE APP
################################################################################

DESCRIPTION = """< วิธีใช้ >

- nozomibot Web Version 
(มีสองที่ กดเมนูด้านล่างก็เข้าไปเว็บได้)
https://www.nozomi.ml/
https://nzmbot.herokuapp.com/

1. พจนานุกรม (JTDic)
พิมพ์คำศัพท์ภาษาญี่ปุ่นหรือคำศัพท์ไทยเท่านั้น

2. การตัดคำ
ตัด (space) ประโยค
เช่น "ตัด 昨日の夜は何を食べましたか"

3. การผันรูป
ผัน (space) กริยา
เช่น "ผัน 食べた"

4. วิธีอ่าน (Roman)
อ่าน (space) ประโยค
เช่น "อ่าน 昨日NHKを見ましたか"

5. คันจิดิก
คันจิ (space) คันจิตัวเดียว
เช่น "คันจิ 望"

6. accent
accent (space) คำ
เช่น "accent 山田"

7. สุ่มเลือกบทความ NHK News Easy
พิมพ์ NHK

8. ตัวอย่างประโยคจาก NHK News
ตัวอย่าง (space) คำ
เช่น "ตัวอย่าง 発表"

9. ตัวอย่างประโยคจาก Twitter
tweet (space) คำ
เช่น "tweet コロナ"

10. wikipedia
วิกิ (space) คำ
เช่น "วิกิ バンコク"

หากเจอข้อผิดพลาดหรือ bug ต่างๆ กรุณารบกวนแจ้งให้ทราบโดยพิมพ์ "feedback เมสเสจ" หรือติดต่อทาง Facebook Page ด้วยนะครับ ขอบคุณครับ
"""


def get_reply(text:str, con, cursor):
	# mode select
	if re.match(r'(help|使い方|วิธีใช้|ใช้ยังไง|ヘルプ)\s*$', text, flags=re.I):
		MODE = '0.HELP'
	elif re.match(r'(分けて|切って|token(ize)?|ตัด) ', text, flags=re.I):
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
	elif re.match(r'(สวัสดี|สบายดีไหม|สบายดีมั้ย|หวัดดี)\s*$', text):
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
	else:
		MODE = '1.DICT'

	##### EXECUTE EACH MODE #####
	if MODE == '0.HELP':
		reply = DESCRIPTION

	elif MODE == '1.DICT':
		try:
			reply = get_word(text)
			if reply == None:
				reply = 'ขอโทษที่หาไม่เจอในดิกครับ\n(พิมพ์ help จะแสดงวิธีใช้)'
		except:
			reply = 'server error รอสักครู่นะครับ'

	elif MODE == '2.TOKENIZE':
		text = text.split(' ', 1)[1]
		tokens = tokenize(text, pos_thai=True) # token = [surface, phone, lemma, pos]
		if len(tokens) < 40:
			reply = '\n'.join([f'{toNchr(token[0])} {toNchr(token[1])} {toNchr(token[2])} {token[3]}' for token in tokens]) # SR, phone, lemma, pos
		else:
			reply = 'ประโยคยาวเกินไปครับ'

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
		reply = random.choice(['สวัสดีครับ','หัวดดี','เป็นไงบ้าง','ไปไหนมา','อ้วนขึ้นป่าว','ทำไรอยู่','สบายดีไหม','อยากกินหมูกระทะ','คิดถึงจังเลย','ฮัลโหล','หิวแล้วอ่ะ','เย่แล้ววว','ว้าวซ่า','กินข้าวรึยัง','กักตัวอยู่ไหม'])
	
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
		reply = "น่าจะใช้ผิดครับ พิมพ์ help จะแสดงวิธีใช้"

	return MODE, reply

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


##### EXAMPLE OF NHK NEWS WEB #####
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

def get_time_now():
	tz = time.tzname[0]
	if tz == 'UTC': # on EC2
		return str(datetime.now()+timedelta(hours=7)).split('.')[0]
	else: # on Local
		return str(datetime.now()).split('.')[0]

##### SQL LOG FUNCTION #####
def log_web(mode, text):
	try:
		con, cursor = connect_sql('nozomibot')
		date_now = get_time_now()
		cursor.execute(f"INSERT INTO log_web (date, mode, text) VALUES (%s, %s, %s);", (date_now, mode, text))
		con.commit()
		con.close()
	except:
		pass



###########################################################

if __name__ == "__main__":
	port = int(os.getenv("PORT", 8000))
	app.run(host="0.0.0.0", port=port, debug=True)