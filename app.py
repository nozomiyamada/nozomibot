from flask import Flask, request, abort, render_template, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	# receive & preprocess message
	text = str(event.message.text).strip()
	text = re.sub(r'[\s\t]+', ' ', text) # multiple spaces -> one half space

	# user info & datetime (ICT)
	profile = line_bot_api.get_profile(event.source.user_id)
	date_now = get_time_now()

	# connect SQL & insert into LOG
	con, cursor = connect_sql('jtdic')
	if str(profile.display_name) != 'Nozomi':
		cursor.execute(f"INSERT INTO querylog (date, text, username, userid) VALUES (%s, %s, %s, %s);", (date_now, text, profile.display_name, profile.user_id))
		con.commit()

	# get reply, send reply
	reply = get_reply(text, con, cursor)
	line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

	# close SQL
	cursor.close()
	con.close()

@app.after_request
def after_request(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
	response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
	return response


################################################################################
###  NOZOMIBOT WEB PAGE 
################################################################################

##### TOP PAGE : DICTIONARY & FEEDBACK #####
@app.route("/", methods=['GET', 'POST'])
def top_page():
	if request.method == 'GET':
		return render_template('dict.html', word='')
	elif request.method == 'POST':
		userip = request.remote_addr
		word = request.form['word']
		log_web('dict', word, userip) # LOG SEARCH HISTORY
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
		userip = request.remote_addr
		log_web('tokenize', text, userip) # LOG SEARCH HISTORY
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
		userip = request.remote_addr
		log_web('example', word, userip) # LOG SEARCH HISTORY
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
		userip = request.remote_addr
		log_web('nhk', f'{genre}_{keyword}', userip) # LOG SEARCH HISTORY
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
###  NOZOMIBOT LINE APP
################################################################################

description = """< วิธีใช้ >

WEB VERSION
https://nzmbot.herokuapp.com/

วิธีใช้ละเอียดและตัวอย่างดูเว็บนี้นะครับ
https://github.com/nozomiyamada/nozomibot/blob/master/README.md

1. พจนานุกรม (JTDic)
พิมพ์คำศัพท์ภาษาญี่ปุ่นหรือคำศัพท์ไทยเท่านั้น

2. การตัดคำ
ตัด (space) ประโยค
เช่น "ตัด 昨日の夜は何を食べましたか"

3. การผันรูป
ผัน (space) กริยา
เช่น "ผัน 食べた"

4. วิธีอ่าน (Kana)
คานะ (space) ประโยค
เช่น "คานะ 昨日NHKを見ましたか"

5. วิธีอ่าน (Roman)
โรมัน (space) ประโยค
เช่น "โรมัน 昨日NHKを見ましたか"

6. คันจิดิก
คันจิ (space) คันจิตัวเดียว
เช่น "คันจิ 望"

7. accent
accent (space) คำ
เช่น "accent 山田"

8. random NHK News easy
พิมพ์ NHK

9. ตัวอย่างประโยคจาก NHK News
ตัวอย่าง (space) คำ
เช่น "ตัวอย่าง 発表"

10. ตัวอย่างประโยคจาก Twitter
tweet (space) คำ
เช่น "tweet コロナ"

11. wikipedia
วิกิ (space) คำ
เช่น "วิกิ バンコク"

หากเจอข้อผิดพลาดหรือ bug ต่างๆ กรุณารบกวนแจ้งให้ทราบโดยพิมพ์ "feedback เมสเสจ" หรือติดต่อทาง Facebook (ชื่อ: Nozomi Ymd) ด้วยนะครับ ขอบคุณครับ"""


def get_reply(text:str, cn, cursor):
	# mode select
	# 0:help 1:sawasdee 2:jojo 3:feedback 4:P'No 5:incorrect 6.kanji
	if re.match(r'(help|使い方|วิธีใช้|ยังไง)$', text, flags=re.I):
		MODE = 0
	elif re.match(r'(สวัสดี|สบายดีไหม)$', text):
		MODE = 1
	elif re.match(r'(jojo|giogio|ジョジョ|โจโจ้)$', text, flags=re.I):
		MODE = 2
	elif re.match(r'feedback', text, flags=re.I):
		MODE = 3
	elif re.search(r'พี่โน', text):
		MODE = 4
	elif len(text.split(' ')) > 1 and not \
		re.match(r'(漢字|คันจิ|kanji|分けて|切って|token|ตัด|活用|conj|ผัน(รูป)?|accent|アクセント|roman|ローマ字|โรมัน|อ่าน(ว่า)?|読み(方)?|かな|カナ|kana|ค[ะา]นะ|วิกิ|wiki|ウィキ|NHK|例文|corpus|ตัวอย่าง|twitter|ツイート|ツイッター|tweet)', text, flags=re.I):
		MODE = 5
	elif re.match(r'(漢字|คันจิ|kanji) .+$', text, flags=re.I):
		MODE = 6
	elif re.match(r'(分けて|切って|token(ize)?|ตัด) ', text, flags=re.I):
		MODE = 7
	elif re.match(r'(活用|conj(ugate)?|ผัน(รูป)?) ', text, flags=re.I):
		MODE = 8
	elif re.match(r'(accent|アクセント) ', text, flags=re.I):
		MODE = 9
	elif re.match(r'(roman|โรมัน|ローマ字) ', text, flags=re.I):
		MODE = 10
	elif re.match(r'(อ่าน(ว่า)?|読み(方)?|かな|カナ|kana|ค[ะา]นะ) ', text, flags=re.I):
		MODE = 11
	elif re.match(r'(วิกิ|wiki|ウィキ) ', text, flags=re.I):
		MODE = 12
	elif re.match(r'NHK', text, flags=re.I):
		MODE = 13
	elif re.match(r'(corpus|例文|ตัวอย่าง) ',text, flags=re.I):
		MODE = 14
	elif re.match(r'(twitter|tweet|ツイッター|ツイート) ',text, flags=re.I):
		MODE = 15
	else:
		MODE = 100

	
	##### execute each mode #####

	# 0. help
	if MODE == 0:
		reply = description
	
	# 1. sawasdee
	elif MODE == 1:
		reply = random.choice(['สวัสดีครับ','หัวดดี','เป็นไงบ้าง','ไปไหนมา','อ้วนขึ้นป่าว','ทำไรอยู่','สบายดีไหม','อยากกินหมูกระทะ','คิดถึงจังเลย','ฮัลโหล','หิวแล้วอ่ะ','เย่แล้ววว','ว้าวซ่า','กินข้าวรึยัง'])
	
	# 2. JOJO
	elif MODE == 2:
		with open('data/jojo.csv', 'r', encoding='utf8') as f:
			data = list(csv.reader(f))
			line = random.choice(data)
		reply = f'{line[0]}\n\n - {line[1]}, Part {line[2]}'
	
	# 3. feedback
	elif MODE == 3:
		reply = 'ขอบคุณมากที่ส่ง feedback และช่วยพัฒนาระบบครับ❤️'
	
	# 4. P'No
	elif MODE == 4:
		reply = random.choice(['พี่โนเป็นคนสุดหล่อ','พี่โนเป็นคนใจดีสุดๆ','พี่โนเป็นคนสุดยอด','พี่โนชอบสเวนเซ่น','พี่โนชอบก๋วยเตี๋ยวเรือ','พี่โนเป็นทาสแมว','พี่โนกักตัวอยู่่','เลี้ยงข้าวพี่โนหน่อย','พี่โนชอบโจโจ้'])
	
	# 5. incorrect use
	elif MODE == 5:
		reply = "ใช้ผิดครับ พิมพ์ help จะแสดงวิธีใช้"
	
	# 6. kanji dic
	elif MODE == 6:
		kanji = text.split(' ', 1)[1]
		if len(kanji) > 1:
			reply = "พิมพ์คันจิตัวเดียวนะครับ"
		elif is_kanji(kanji) == False:
			reply = "พิมพ์คันจินะครับ"
		else:
			reply = get_kanji(kanji)

	# 7. tokenize
	elif MODE == 7:
		text = text.split(' ', 1)[1]
		tokens = tokenize(text, pos_thai=True) # token = [surface, phone, lemma, pos]
		if len(tokens) < 40:
			reply = '\n'.join([f'{toNchr(token[0])} {toNchr(token[1])} {toNchr(token[2])} {token[3]}' for token in tokens]) # SR, phone, lemma, pos
		else:
			reply = 'ประโยคยาวเกินไปครับ'

	
	# 8. conjugate 
	elif MODE == 8:
		text = text.split(' ', 1)[1]
		r = conjugate(text)
		if r == None:
			reply = 'ผันไม่ได้ครับ ต้องเป็นกริยาหรือ i-adj เท่านั้น'
		elif len(r) == 9: # verb w/o potential form
			reply = f'辞書形:　　 {r[0]}\nない形:　　 {r[1]}\nなかった形: {r[2]}\nます形:　　 {r[3]}\nて形:　　　 {r[4]}\nた形:　　　 {r[5]}\nば形:　　　 {r[6]}\n命令形:　　 {r[7]}\n意向形:　　 {r[8]}'
		elif len(r) == 10: # verb with potential form
			reply = f'辞書形:　　 {r[0]}\nない形:　　 {r[1]}\nなかった形: {r[2]}\nます形:　　 {r[3]}\nて形:　　　 {r[4]}\nた形:　　　 {r[5]}\nば形:　　　 {r[6]}\n命令形:　　 {r[7]}\n意向形:　　 {r[8]}\n可能形:　　 {r[9]}'
		elif len(r) == 8:  # adj
			reply = f'辞書形:　　 {r[0]}\nない形:　　 {r[1]}\nなかった形: {r[2]}\nです形:　　 {r[3]}\nて形:　　　 {r[4]}\nた形:　　　 {r[5]}\nば形:　　　 {r[6]}\n副詞化:　　 {r[7]}' 
			

	# 9. accent
	elif MODE == 9:
		word = text.split(' ', 1)[1]
		reply = get_accent(word)
		if reply == None:
			reply = 'หาไม่เจอในดิกครับ\n(พิมพ์ help จะแสดงวิธีใช้)'

	# 10. romanize
	elif MODE == 10:
		text = text.split(' ', 1)[1]
		try:
			reply = romanize(text)
		except:
			reply = f'เปลี่ยน {text} ไม่ได้ครับ'

	# 11. kanazation
	elif MODE == 11:
		text = text.split(' ', 1)[1]
		try:
			reply = yomikata(text)
		except:
			reply = f'เปลี่ยน {text} ไม่ได้ครับ'

	# 12. WIKI
	elif MODE == 12:
		word = text.split(' ', 1)[1]
		reply = get_wiki(word)

	# 13. NHK easy
	elif MODE == 13:
		data = pd.read_csv('data/nhkeasy.csv')
		r = random.randint(0, len(data)-1)
		row = data.loc[r]
		reply = f"{row['date']}\n{row['title']}\n\n{row['article']}"

	# 14. NHK corpus
	elif MODE == 14:
		# search
		word = text.split(' ')[1]
		if len(text.split(' ')) == 3:
			limit = int(text.split(' ')[2])
			if limit > 100:
				limit = 100
		else:
			limit = 5
		result = get_nhk(word, limit, cursor)
		if result == []:
			reply = 'หาไม่เจอในคลังข้อมูลครับ\n(พิมพ์ help จะแสดงวิธีใช้)'
		else:
			reply = ''
			for sentence in result:
				reply += '・' + sentence.strip() + '\n\n'
			reply = reply.strip()

	# 15. Twitter
	elif MODE == 15:
		# "tweet query 10"
		query = text.split(' ')[1]
		if len(text.split(' ')) == 3:
			limit = int(text.split(' ')[2])
			if limit > 100:
				limit = 100
		else:
			limit = 5
		result = get_twitter(query, limit, cursor)
		if result == []:
			reply = 'หาไม่เจอในคลังข้อมูลครับ\n(พิมพ์ help จะแสดงวิธีใช้)'
		else:
			reply = ''
			for tweet in result:
				reply += '・' + tweet.strip() + '\n\n'
			reply = reply.strip()

	# DICTIONARY MODE
	else:
		try:
			reply = get_word(text)
			if reply == None:
				reply = 'หาไม่เจอในดิกครับ\n(พิมพ์ help จะแสดงวิธีใช้)'
		except:
			reply = 'server error รอสักครู่นะครับ'

	return reply

def get_tweet(query, limit=30, max_chr=30, highlighted=True):
	con, cursor = connect_sql('nozomibot')
	### get tweet at random 
	cursor.execute(f"SELECT tweet, username FROM tweetjp WHERE tweet LIKE '%{query}%' ORDER BY RAND() LIMIT 100;")
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
		candidates = list(candidates)[:limit]
	if highlighted:
		candidates = [highlight(cand, query) for cand in candidates]
	con.close()
	return candidates

def get_nhk(query, limit=30, highlighted=True):
	con, cursor = connect_sql('nozomibot')
	### get tweet at random 
	cursor.execute(f"SELECT id, article FROM nhkweb WHERE article LIKE '%{query}%' ORDER BY RAND() LIMIT 200;")
	result = list(cursor) # [[id, article],,]
	if len(result) == 0:
		return None
	sentence_pattern = re.compile(r'(?:^|[。\s!\?！？])([^。\s!\?！？]*?{}[^。\s!\?！？]*?(?:[。\s!\?！？]+|$))'.format(query))
	candidates = set()
	for _, article in result:
		candidates |= set(re.findall(sentence_pattern, article))
	candidates = set([x.strip() for x in candidates if len(x.strip()) >= len(query)+2 and len(x)>10]) # exclude too short sentences
	if len(candidates) > limit:
		candidates = list(candidates)[:limit]
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
def log_web(mode, text, userip):
	try:
		con, cursor = connect_sql('nozomibot')
		date_now = get_time_now()
		cursor.execute(f"INSERT INTO log_web (date, mode, text, userip) VALUES (%s, %s, %s, %s);", (date_now, mode, text, userip))
		con.commit()
		con.close()
	except:
		pass

def log_line(mode, text, username, userid):
	try:
		con, cursor = connect_sql('nozomibot')
		date_now = get_time_now()
		cursor.execute(f"INSERT INTO log_line (date, mode, text, username, userid) VALUES (%s, %s, %s, %s, %s);", (date_now, mode, text, username, userid))
		con.commit()
		con.close()
	except:
		pass



###########################################################

if __name__ == "__main__":
	port = int(os.getenv("PORT", 8000))
	app.run(host="0.0.0.0", port=port, debug=True)