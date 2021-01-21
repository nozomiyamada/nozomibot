from JpProcessing.tokenization import tokenize
from JpProcessing.characters import kata2hira
import os
import pandas as pd
ABS_DIR = os.path.dirname(__file__)
VERBS = pd.read_csv(ABS_DIR + '/verbs.csv', index_col='word')

def shift_dan(gyou:str, n:int) -> str:
	"""
	function for shifting Dan\n
	>>> shift('あ', 2)
	'う'
	"""
	if gyou in ['な','ま','ら']:
		return chr(ord(gyou) + n)
	elif gyou in ['あ','か','が','さ','ざ']:
		return chr(ord(gyou) + n*2)
	elif gyou in ['は','ば','ぱ']:
		return chr(ord(gyou) + n*3)
	elif gyou == 'た':
		return {1:'ち', 2:'つ', 3:'て', 4:'と'}[n]
	elif gyou == 'だ':
		return {1:'ぢ', 2:'づ', 3:'で', 4:'ど'}[n]


def get_teform(lemma:str) -> str:
	"""
	convert group1 verb base form into te form\n
	>>> get_teform('書く')
	書いて
	"""
	if lemma == '行く':
		return '行って'
	elif lemma == 'いく':
		return 'いって'
	elif lemma[-1] in ['う','つ','る']:
		return lemma[:-1] + 'って'
	elif lemma[-1] in ['ぬ','む','ぶ']:
		return lemma[:-1] + 'んで'
	elif lemma[-1] == 'く':
		return lemma[:-1] + 'いて'
	elif lemma[-1] == 'ぐ':
		return lemma[:-1] + 'いで'
	elif lemma[-1] == 'す':
		return lemma[:-1] + 'して'


def get_taform(lemma:str) -> str:
	"""
	convert group1 verb base form into ta form\n
	>>> get_teform('書く')
	書いた
	"""
	teform = get_teform(lemma)
	if teform[-1] == 'て':
		return teform[:-1] + 'た'
	elif teform[-1] == 'で':
		return teform[:-1] + 'だ'


##### DICTINARY & RULE-BASED CONJUGATION ##### 
def verb_conj_from_lemma(lemma:str, conjtype:str) -> list:
	"""
	input: one verb, conjtype is 5th element of tokenize()\n
	output: list of conjugated forms\n
	base, nai, nakatta, masu, te, ta, conditional, imperative, volitional, potential : 10 forms\n

	verb_conj_from_lemma('行く', '五段・カ行促音')
	>>> ['行く', '行かない', '行かなかった', '行きます', '行って', '行った', '行けば', '行け', '行こう', '行ける']

	verb_conj_from_lemma('食べる', '一段')
	>>> ['食べる', '食べない', '食べなかった', '食べます', '食べて', '食べた', '食べれば', '食べろ', '食べよう', '食べられる']
	"""
	group = conjtype[:2] # conjtype = 五段-ワア行, 上一段, 下一段, サ行変格
	pot = None # potential form
	
	### if the verb is in irregular verbs, return it
	if lemma in VERBS.index:
		return list(VERBS.loc[lemma][['base', 'nai', 'nakatta', 'masu', 'te', 'ta','con', 'imp', 'vol', 'pot']])
	
	### exception -ずる動詞
	### 任ずる => サ変, 任じる => 上一段
	elif lemma.endswith('ずる') and conjtype.startswith('サ行変格'):
		stem = lemma[:-2] # 念
		base = lemma # 念ずる
		con = stem + 'ずれば'
		# others: same as じる
		nai = stem + 'じない'
		nakatta = stem + 'じなかった'
		masu = stem + 'じます'
		te = stem + 'じて'
		ta = stem + 'じた'
		imp = stem + 'じよ'
		vol = stem + 'じよう'
		pot = stem + 'じられる'
	
	elif group in ['上一', '下一']: # e.g. 食べる
		stem = lemma[:-1] # 食べ
		base = lemma
		nai = stem +  'ない' # 食べない
		nakatta = stem + 'なかった' # 食べなかった
		masu = stem + 'ます' # 食べます
		te = stem + 'て' # 食べて
		ta = stem + 'た' # 食べた
		imp = stem + 'ろ' # 食べろ
		con = stem + 'れば' # 食べれば
		vol = stem + 'よう' # 食べよう
		pot = stem + 'られる' # 食べられる
	
	elif group == '五段':
		gyou = kata2hira(conjtype[3])  # e.g. 五段-カ行　-> か (convert into ア if ワ)
		stem = lemma[:-1]  # e.g. 会う -> 会
		nai = stem + gyou + 'ない' # 会わない
		nakatta = stem + gyou + 'なかった' # 会わなかった
		# wa gyou -> a gyou
		if gyou == 'わ': 
			gyou = 'あ'
		base = lemma
		masu = stem + shift_dan(gyou, 1) + 'ます' # 会います
		te = get_teform(lemma) # 会って
		ta = get_taform(lemma) # 会った
		imp = stem + shift_dan(gyou, 3) # 買え
		con = stem + shift_dan(gyou, 3) + 'ば' # 買えば
		vol = stem + shift_dan(gyou, 4) + 'う' # 買おう
		pot = stem + shift_dan(gyou, 3) + 'る' # 買える

	elif conjtype.startswith('サ行変格') and len(lemma) >= 3: # 座する
		stem = lemma[:-2]
		return [stem+x for x in ['する','しない','しなかった','します','して','した','すれば','しろ','しよう','せる']]
	else:
		return None
	return [base, nai, nakatta, masu, te, ta, con, imp, vol, pot]


def adj_conj_from_lemma(lemma:str):
	"""
	nai, nakatta, desu, base, te, ta, conditional, adverb : 8 forms
	"""
	if lemma == 'いい': # exception 
		stem = 'よ'
		desu = 'いいです'
	else:
		stem = lemma[:-1]
		desu = stem + 'いです'
		
	if lemma == 'ない':
		nai = 'ない'
		nakatta = 'なかった'
	elif lemma == '無い':
		nai = '無い'
		nakatta = '無かった'
	else:	
		nai = stem + 'くない'
		nakatta = stem + 'くなかった'
	
	te = stem + 'くて'
	ta = stem + 'かった'
	con = stem + 'ければ'
	adv = stem + 'く'
	
	return [lemma, nai, nakatta, desu, te, ta, con, adv]


def conjugate(word:str) -> list:
	"""
	conjugate verb or i-adj regardless of whether it is lemma or not
	
	conjugate('任ずる')
	>>> ['任ずる', '任じない', '任じなかった', '任じます', '任じて', '任じた', '任ずれば', '任じよ', '任じよう', '任じられる']

	conjugate('来て')
	>>> ['来る', '来ない', '来なかった', '来ます', '来て', '来た', '来い', '来れば', '来よう', '来られる']

	tokenize() may return 2-3 or tokens even if it is one word 
	e.g. 
	>>> tokenize('勉強する')
	[['勉強', 'ベンキョー', 'ベンキョウ', '勉強', '名詞-普通名詞-サ変可能', '', '', '0'],
	['する', 'スル', 'スル', 'する', '動詞-非自立可能', 'サ行変格', '終止形-一般', '0']]
	>>> tokenize('選挙活動する')
	[['選挙', 'センキョ', 'センキョ', '選挙', '名詞-普通名詞-サ変可能', '', '', '1'],
	['活動', 'カツドー', 'カツドウ', '活動', '名詞-普通名詞-サ変可能', '', '', '0'],
	['する', 'スル', 'スル', 'する', '動詞-非自立可能', 'サ行変格', '終止形-一般', '0']]

	if cannot conjugate, return None
	"""
	try:
		tokens = tokenize(word)
		# 0.surface form  1.phonemic  2.lemma-kana  3.lemma-kanji  4.pos  5.conj type  6.conj form
		if len(tokens) == 0:
			return None
		if tokens[0][4].startswith('動詞'): # if first token is verb, ignore suffix
			return verb_conj_from_lemma(tokens[0][3], tokens[0][5]) # lemma & conjtype
		elif tokens[0][4].startswith('形容詞'):
			return adj_conj_from_lemma(tokens[0][3])
		elif len(tokens) == 1: # only one token, but neither verb nor adj
			return None 
		elif tokens[0][4].startswith('名詞'): # noun that is followed by する
			if tokens[1][3] == 'する': # 2 tokens verb e.g. 活動 + する
				return [tokens[0][0] + x for x in verb_conj_from_lemma('する', 'サ行変格')]
			elif tokens[1][4].startswith('名詞') and tokens[2][3] == 'する': # 3 tokens verb e.g. 選挙 + 活動 + する
				return [tokens[0][0] + tokens[1][0] + x for x in verb_conj_from_lemma('する','サ行変格')]
		else:
			return None
	except:
		return None



#########################################################################################


IRREGULAR_VERBS = {
	'する': ['する', 'しない', 'しなかった', 'します', 'して', 'した', 'すれば', 'しろ', 'しよう', 'できる'],
	'くる': ['くる', 'こない', 'こなかった', 'きます', 'きて', 'きた', 'くれば', 'こい', 'こよう', 'こられる'],
	'来る': ['来る', '来ない', '来なかった', '来ます', '来て', '来た', '来れば', '来い', '来よう', '来られる'],
	'行く': ['行く', '行かない', '行かなかった', '行きます', '行って', '行った', '行けば', '行け', '行こう', '行ける'],
	'いる': ['いる', 'いない', 'いなかった', 'います', 'いて', 'いた', 'いれば', 'いろ', 'いよう', 'いられる'],
	'居る': ['いる', 'いない', 'いなかった', 'います', 'いて', 'いた', 'いれば', 'いろ', 'いよう', 'いられる'],
	'ある': ['ある', 'ない', 'なかった', 'あります', 'あって', 'あった', 'あれば', 'あれ', 'あろう', 'ありえる'],
	'在る': ['在る', 'ない', 'なかった', '在ります', '在って', '在った', '在れば', '在れ', '在ろう', 'ありえる'],
	'有る': ['有る', 'ない', 'なかった', '有ります', '有って', '有った', '有れば', '有れ', '有ろう', '有りえる'],
	'なさる': ['なさる','なさらない','なさらなかった','なさいます','なさって','なさった','なされば','なされ','なさろう', '-'],
	'くださる': ['くださる',
		'くださらない',
		'くださらなかった',
		'くださいます',
		'くださって',
		'くださった',
		'くだされば',
		'くだされ',
		'くださろう'
		'-'],
	'おっしゃる': ['おっしゃる',
		'おっしゃらない',
		'おっしゃらなかった',
		'おっしゃいます',
		'おっしゃって',
		'おっしゃった',
		'おっしゃれば',
		'おっしゃれ',
		'おっしゃろう',
		'-'],
	'いらっしゃる': ['いらっしゃる',
		'いらっしゃらない',
		'いらっしゃらなかった',
		'いらっしゃいます',
		'いらっしゃって',
		'いらっしゃった',
		'いらっしゃれば',
		'いらっしゃれ',
		'いらっしゃろう',
		'-']
}