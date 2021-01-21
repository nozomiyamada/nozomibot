import MeCab, re
from JpProcessing.characters import kata2hira, is_only_kana, is_hiragana
tagger = MeCab.Tagger()

def clean(text:str):
	text = re.sub(r'[“”„]', '"', text) # convert double quotations into "
	text = re.sub(r'[‘’`]', "'", text) # convert single quotations into '
	text = re.sub(r'[ \u00a0\xa0\u3000\u2002-\u200a\t]+', ' ', text) # shrink spaces e.g. good  boy -> good boy
	text = re.sub(r'[\r\u200b\ufeff]+', '', text) # remove non-breaking space
	return text.strip()


POS_MAPPING = {
	'動詞':'กริยา',
	'名詞':'คำนาม',
	'代名詞':'สรรพนาม',
	'形容詞':'i-adj',
	'助詞':'คำช่วย',
	'助動詞':'คำช่วยที่ผันรูป',
	'副詞':'adv',
	'接頭辞':'prefix',
	'接尾辞':'suffix',
	'形状詞':'na-adj',
	'連体詞':'คำขยายคำนาม',
	'記号':'เครื่องหมาย',
	'補助記号':'เครื่องหมาย',
	'感動詞':'คำอุทาน',
	'フィラー':'filler',
	'接続詞':'คำเชื่อม',
	'その他':'อื่นๆ'
}

def tokenize(text:str, pos_thai=False) -> list:
	"""
	tokenize sentence into list of tokens with linguistic features (nothing : *)
		0: surface form
		1: phonemic
		2: lemma-kana
		3: lemma-kanji
		4: pos - subcategory - subsubcategory
		5: conjugation type
		6: conjugation form
		7: ???

	>>> tokenize('大きい家は, 走りたくなるな')
	[['大きい', 'オーキー', 'オオキイ', '大きい', '形容詞-一般', '形容詞', '連体形-一般', '3'],
	['家', 'イエ', 'イエ', '家', '名詞-普通名詞-一般', '', '', '2'],
	['は', 'ワ', 'ハ', 'は', '助詞-係助詞', '', '', ''],
	['走り', 'ハシリ', 'ハシル', '走る', '動詞-一般', '五段-ラ行', '連用形-一般', '2'],
	['たく', 'タク', 'タイ', 'たい', '助動詞', '助動詞-タイ', '連用形-一般', ''],
	['なる', 'ナル', 'ナル', '成る', '動詞-非自立可能', '五段-ラ行', '終止形-一般', '1'],
	['な', 'ナ', 'ナ', 'な', '助詞-終助詞', '', '', '']]

	original method of MeCab returns 7-8 elements
	if less than 10, filled with surface form instead

	>>> tokenize('アニーが念じた')
	[['アニー', 'アニー', 'アニー', 'アニー-外国', '名詞-固有名詞-人名-一般', '', '', '1'],
	['が', 'ガ', 'ガ', 'が', '助詞-格助詞', '', '', ''],
	['怒っ', 'オコッ', 'オコル', '怒る', '動詞-一般', '五段-ラ行', '連用形-促音便', '2'],
	['た', 'タ', 'タ', 'た', '助動詞', '助動詞-タ', '終止形-一般', '']]

	>>> tokenize('大きい家は, 走って見たくなるな', pos_thai=True)
	[['大きい', 'オーキー', '大きい', 'i-adj'],
	['家', 'イエ', '家', 'คำนาม'],
	['は', 'ワ', 'は', 'คำช่วย'],
	[',', ',', ',', 'คำนาม'],
	['走っ', 'ハシッ', '走る', 'กริยากลุ่ม1'],
	['て', 'テ', 'て', 'คำช่วย'],
	['見', 'ミ', '見る', 'กริยากลุ่ม2'],
	['たく', 'タク', 'たい', 'คำช่วยที่ผันรูป'],
	['なる', 'ナル', '成る', 'กริยากลุ่ม1'],
	['な', 'ナ', 'な', 'คำช่วย']]

	"""
	### clean text
	text = clean(text) 
	### first, capture any digits and replace with index 1,2,3 ... in order to treat as 1 token
	### '-273.15度から5,000度まで' => '1度から2度まで', [-273.15, 5,000]
	digit_pattern = re.compile(r'[+-]?\d[\d,]*(?:\.\d+)?') # e.g. -273.15  +1,234.56
	original_nums = re.findall(digit_pattern, text) # caputure digits as list
	for i, digit in enumerate(original_nums): # replace digit with index 0,1,2,...
		text = text.replace(digit, str(i), 1)
	### tokenize
	tokens = tagger.parse(text).split('\n')[:-2] # split into tokens, exclude final two tokens: 'EOS' and ''
	tokens = [token.split('\t') for token in tokens] # split by \t -> make 2D list
	##### ITERATE EACH TOKEN AND CHECK #####
	recover_index = 0 # from 0 to len(original_digits) - 1
	for i, token in enumerate(tokens):
		### decrypt index into original number
		if token[0] == str(recover_index):
			tokens[i] = [str(original_nums[recover_index])] * 4 + tokens[i][4:]
			recover_index += 1
		### fill punctuation
		elif token[1] == '': # punctuation e.g. "。" token[1] and token[2] are empty
			tokens[i][1] = token[0]
			tokens[i][2] = token[0]
		### する problem: lemma is changed to 為る regardless of charcter type
		elif token[3] == '為る' and token[5] == 'サ行変格':
			tokens[i][3] = 'する'
		### くる problem: lemma is changed to 来る regardless of charcter type
		elif token[3] == '来る' and token[5] == 'カ行変格' and token[0][0] != '来': # if case of Hiragana
			tokens[i][3] = 'くる'
		### -ずる動詞 problem: both 念じる(上一段) and 念ずる(サ変) -> lemma 念ずる(サ変) WHYYYY???
		### check surface form and correct it
		elif token[3].endswith('ずる') and token[4].startswith('動詞') and token[5] in ['サ行変格','上一段-ザ行']:
			stem = token[3][:-2] # 念ずる -> 念
			if token[0].startswith(stem + 'じ'): # 念じ...
				tokens[i][2] = token[2].replace('ズル', 'ジル')
				tokens[i][3] = stem + 'じる' # replace lemma with -じる
				tokens[i][5] = '上一段-ザ行'
		### proper noun problem: 東京 -> トウキョウ
		elif token[4].startswith('名詞') and token[0] != token[3]:
			tokens[i][3] = token[0]
		### Kana Problem: e.g. おいしかった -> 美味しかった
		elif is_hiragana(token[0]): # surface form is only hiragana
			tokens[i][3] = kata2hira(token[2]) # replace lemma-kanji with lemma-kana
		### allograph problem: e.g. 刺す,挿す,指す -> lemma 差す-他動詞 WHYYYY???
		### compare the first character of surface and lemma
		elif '-' in token[3] or token[0][0] != token[3][0]:
			tokens[i][3] = token[0][0] + token[3][1:].split('-')[0] # replace first character and remove also -他動詞


	### convert PoS tag into Thai
	if pos_thai == False: 
		return tokens # return original list
	else:
		for i, token in enumerate(tokens):  # add digit 1-3 after PoS
			if token[4].startswith('動詞') and get_verb_group(token[5]) != None: # token[5] = conjtype
				tokens[i][4] = 'กริยากลุ่ม' + get_verb_group(token[5]) 
			else:
				tokens[i][4] = POS_MAPPING[token[4].split('-')[0]] # POS = 動詞-XX-XX

		# return [0.surface, 1.phone, 3.lemma, 4.pos]  
		return [[t[0],t[1],t[3],t[4]] for t in tokens]

def get_verb_group(conjtype:str) -> str:
	"""
	get verb group 1-3 from the result of tokenize
	conjtype is a 5th element of tokens list
	
	>>> get_verb_group('五段-ラ行')
	'1'
	"""
	return {'五段':'1', '上一':'2', '下一':'2', 'サ行':'3', 'カ行':'3'}.get(conjtype[:2], None)


def yomikata(text:str, katakana=True, sep='', return_list=False) -> str:
	"""
	convert JP text into katakana text
	: katakana : katakana or hiragana

	>>> yomikata('心掛け')
	ココロガケ
	>>> yomikata('私は本をNHKへ返す')
	'ワタシハホンヲNHKヘカエス'
	"""
	# 1. tokenize
	# 2. check POS tags, if 助動詞 or 助詞-接続助詞 or 接尾辞-名詞的-一般, make it to one word
	# 3. make list of phonemics (katakana)
	# 4. check first 2 or 1 chars 
	# 5. if they exist in the ROMAJI_DICT, replace with ROMAJI
	# 6. delete the characters 
	# っ must duplicate following letter, so use the temporary char Q instead
	tokens = tokenize(text)
	phones = [] # katakana
	for token in tokens:
		pos = token[4]
		if not pos.startswith('助動詞') and not pos.startswith('助詞-接続助詞') and pos != '接尾辞-名詞的-一般':
			phones.append(token[1]) # append phonemic as new word
		else:
			phones[-1] += token[1]
	if katakana == False:
		phones = [kata2hira(w) for w in phones]
	return phones if return_list else sep.join(phones) 


def romanize(text:str) -> str:
	"""
	>>> romanize('伊藤')
	itoo
	"""
	text = yomikata(text, sep=' ')
	result = ''
	while len(text) > 0:
		if text[0] == ' ':
			result += ' '
			text = text[1:]
		elif len(text) >= 2 and text[1] in 'ァィゥェォヵヶャュョヮ': # 小書き文字
			try:
				result += ROMAJI_DICT[text[:2]]
			except:
				result += ROMAJI_DICT[text[0]] 
				result += ROMAJI_DICT[text[1]]
			text = text[2:] # delete first two characters
		elif text[0] == 'ッ':
			result += 'Q' # temp char for っ
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
	result = re.sub(r'Q+ ?(\w)', r'\1\1', result) # 'っ' substituted by following consonant
	result = re.sub(r'Q+$', r'ʔ', result) # 'っ' in the final position => glottal stop
	result = re.sub(r'n([mbp])', r'm\1', result) # bilabial assimilation
	result = re.sub(r'o ?u$', 'oo', result) # final ou -> oo
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
	'クァ': 'kwa',
	'クィ': 'kwi',
	'クェ': 'kwe',
	'クォ': 'kwo',
	'グ': 'gu',
	'グヮ': 'gwa',
	'グァ': 'gwa',
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
	'デュ': 'dyu',
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
	'ッ': 'Q'
}