from flask import Flask, request, abort, render_template, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, PostbackAction, URIAction
import os, random, re, time
from JpProcessing import *
from nozomibot_funcs import *

class CustomFlask(Flask):
	jinja_options = Flask.jinja_options.copy()
	jinja_options.update(dict(
		variable_start_string='((',
		variable_end_string='))',
	))

app = CustomFlask(__name__)


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
		tweet = get_tweet(word, limit=100, max_chr=60, highlighted=True)
		#print(time.time()-s)
		### get nhk
		nhk = get_nhk(word, limit=100, highlighted=True)
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


##### THAI2000 WORDS #####
THAI2000 = pd.read_csv('data/thai2000.csv')
@app.route('/thai2000', methods=['GET','POST'])
def web_thai2000():
	if request.method == 'GET':
		return render_template('thai2000.html')
	elif request.method == 'POST':
		print(request.form)
		page = int(request.form['page']) # "2" -> 2
		df_temp = THAI2000[THAI2000['No.'] == page][['日本語','タイ語読み','タイ語文字']]
		if request.form['shuffle'] == 'true':
			df_temp = df_temp.sample(frac=1).reset_index(drop=True)
		return jsonify({'result': df_temp.values.tolist()})


##### ONOMATOPOEIA #####
ONOMATO = pd.read_csv('data/onomato.csv')
@app.route('/onomato', methods=['GET','POST'])
def web_onomato():
	if request.method == 'GET':
		return render_template('onomato.html')
	elif request.method == 'POST':
		onomatotype = request.form['onomatotype'] # 'all', 'gion', 'gitai', 'gijou'
		word = request.form['word'].strip()
		df = ONOMATO.copy().fillna('-')[['タイプ','日本語','タイ語','sense']]
		if onomatotype == 'gion':
			df = df[df['タイプ']=='擬音']
		elif onomatotype == 'gitai':
			df = df[df['タイプ']=='擬態']
		elif onomatotype == 'gijou':
			df = df[df['タイプ']=='擬情']
		if word != '':
			df = df[(df['日本語'].str.contains(word)) | (df['タイ語'].str.contains(word)) | (df['sense'].str.contains(word))]
		return jsonify({'result': df.values.tolist()})


##### NHKTHAI #####
NHKTHAI = pd.read_json('data/nhk.json')
NHKTHAI['date'] = NHKTHAI.date.apply(lambda x: str(x).split(' ')[0])
@app.route('/nhkthai', methods=['GET','POST'])
def web_nhkthai():
	if request.method == 'GET':
		return render_template('nhkthai.html')
	elif request.method == 'POST':
		print(request.form)
		year = request.form['year']
		keyword = request.form['keyword'].strip()
		if year != 'ALL':
			df_temp = NHKTHAI[NHKTHAI.date.str.contains(year)]
		else:
			df_temp = NHKTHAI.copy()
		if keyword != '':
			df_temp = df_temp[(df_temp.headline.str.contains(keyword)) | (df_temp.article.str.contains(keyword))]
			df_temp['article'] = df_temp.article.apply(lambda x: highlight(x, keyword))
		df_temp = df_temp[['date','headline','article']]
		return jsonify({'result': df_temp.values.tolist()})


##### KANA #####
@app.route('/kana', methods=['GET','POST'])
def web_kana():
	if request.method == 'GET':
		return render_template('kana.html')
	elif request.method == 'POST':
		input_text = request.form['input'].split('\n')
		kanatype = request.form['kanatype']
		if kanatype == 'hiragana':
			output = '\n'.join([yomikata(line, katakana=False) for line in input_text])
		else:
			output = '\n'.join([yomikata(line, katakana=True) for line in input_text])
		return jsonify(output)


##### THAIWORD TEST #####
@app.route('/thaitest', methods=['GET','POST'])
def web_thaitest():
	if request.method == 'GET':
		return render_template('thaitest.html')


##### SINGLE WORD SEARCH : SAME AS TOP PAGE #####
@app.route('/<word>', methods=['GET'])
def web_word(word):
	return render_template('dict.html', word=word)


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


################################################################################
###  LINE WEBHOOK
################################################################################

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/line/callback", methods=['POST'])
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
		}
	]
}
"""

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	### RECEIVE MESSAGE
	text = str(event.message.text).strip()

	### GET MODE & REPLY FROM TEXT
	mode, reply = get_reply(text)

	### GET USER INFO & INSERT INTO SQL LOG
	profile = line_bot_api.get_profile(event.source.user_id)
	if profile.display_name != '':
		date_now = get_time_now()
		con, cursor = connect_sql('nozomibot')
		cursor.execute(f"INSERT INTO log_line (date, mode, text, username, userid) VALUES (%s, %s, %s, %s, %s);", (date_now, mode, text, profile.display_name, profile.user_id))
		con.commit()
		con.close()
	
	### SEND REPLY
	if reply != None:
		line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
	elif mode == 'JOSHI_START':
		items = [
			QuickReplyButton(action=PostbackAction(label="Kakujoshi 5 ข้อ", data="action=joshi&type=格助詞&num=5")),
			QuickReplyButton(action=PostbackAction(label="10 ข้อ", data="action=joshi&type=格助詞&num=10")),
			QuickReplyButton(action=PostbackAction(label="All joshi 5 ข้อ", data="action=joshi&type=all&num=5")),
			QuickReplyButton(action=PostbackAction(label="10 ข้อ", data="action=joshi&type=all&num=10"))
		]
		message = TextSendMessage(text="เลือกจำนวนข้อ", quick_reply=QuickReply(items=items))
		line_bot_api.reply_message(event.reply_token, message)
	else:
		reply = 'ขอโทษครับ บอทนี้เป็นบอทอัตโนมัติ ไม่สามารถคุยกันได้'
		line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(PostbackEvent)
def handle_postback(event):
	postback = dict([x.split('=') for x in event.postback.data.split('&')]) # action=joshi&type=格助詞&num=5&Q=0&score=0
	if postback['action'] == 'richmenu_help':
		line_bot_api.reply_message(event.reply_token, TextSendMessage(text=DESCRIPTION))
	elif postback['action'] == 'joshi':
		text, labels, datas = get_postback(postback)
		if labels != None:
			items = [QuickReplyButton(action=PostbackAction(label=label, display_text=label, data=data)) for label, data in zip(labels, datas)]
			message = TextSendMessage(text=text, quick_reply=QuickReply(items=items))
			line_bot_api.reply_message(event.reply_token, message)
		else:
			line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text)) # show result and end


@app.after_request
def after_request(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
	response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
	return response


################################################################################
###  FB MESSENGER WEBHOOK
################################################################################

@app.route('/facebook/callback', methods=['GET', 'POST'])
def receive_message():
	if request.method == 'GET':
		if request.args.get("hub.verify_token") == FB_VERIFY_TOKEN:
			return request.args.get("hub.challenge")
		else:
			return 'Invalid'
	elif request.method == 'POST':
		data = request.get_json()
		for event in data['entry']: # 'entry' is a list of events
			messaging = event['messaging']
			for message in messaging: # event['messaging'] is a list of dict {'sender':xxx,'recipient':yyy,}
				memberID = message['sender']['id'] # Facebook Messenger ID to send message back

				####################  DON'T HAVE TO EDIT ABOVE  #################### 

				##### ONLY POSTBACK (NO MESSAGE - GET STRATED OR SELECT BY PERSISTENT MENU) #####
				if message.get('postback'):
					postback_payload = message['postback']['payload']
					if postback_payload == "GET_STARTED": # get started -> greeting
						send_message(memberID, 'สวัสดีครับ นี่เป็น nozomibot เวอร์ชันเฟสบุคครับ\nกดปุ่ม ≡ ตรงด้านข้างแล้วเมนูจะขึ้นครับ')
					elif postback_payload == 'menu_quickstart':
						send_message(memberID, DESCRIPTION)

				##### MESSAGE #####
				elif message.get('message'):
					received_text = message['message'].get('text')
					quickreply_payload = message['message'].get('quick_reply',{}).get('payload')
					attachment = message['message'].get('attachments')

					#### IF USER SENT TEXT MESSAGE ###
					if received_text:
						mode, reply = get_reply(received_text)
						### SEND REPLY
						if reply != None:
							send_message(memberID, reply)
						else:
							pass
						date_now = get_time_now()
						con, cursor = connect_sql('nozomibot')
						cursor.execute(f"INSERT INTO log_fb (date, mode, text, userid) VALUES (%s, %s, %s, %s);", (date_now, mode, received_text, memberID))
						con.commit()
						con.close()
						


					### IF USER SENT NON-TEXT , e.g. picture ###
					if attachment:
						pass
		return "processed"


def send_message(memberID, message_text):
	r = requests.post("https://graph.facebook.com/v9.0/me/messages",
		params={"access_token": FB_ACCESS_TOKEN},
		headers={"Content-Type": "application/json"},
		data=json.dumps({
			"recipient": {"id": memberID},
			"message": {"text": message_text}
		})
	)



###########################################################

if __name__ == "__main__":
	port = int(os.getenv("PORT", 8000))
	app.run(host="0.0.0.0", port=port, debug=True)