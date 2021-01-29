# nozomibot (Last Update: 22 January 2021)

Line/FB messenger bot และ web application สำหรับผู้เรียนภาษาญี่ปุ่น


![834majrs](https://user-images.githubusercontent.com/44984892/79058885-92a1ac00-7c9d-11ea-8600-6ed00def18ca.png)

Line ID : `@834majrs`

[FB page](https://www.facebook.com/botnozomi)

[Web Application : Faster Version (AWS)](https://www.nozomi.ml/)

[Web Application : Stable Version (heroku)](https://nzmbot.herokuapp.com/)

written in `Python 3.7 (Flask 1.1) + vue.js 2.6` and `MySQL` (AWS RDS), deployed to [`heroku`](https://www.heroku.com) and [`AWS`](https://aws.amazon.com/)

# Features of Messenger Bot (Line & FB)
## linguistic information

1. [พจนานุกรม (word dictionary)](#1-พจนานุกรม-word-dictionary)
2. [การตัดคำ (tokenization)](#2-การตัดคำ-tokenization)
3. [การผันรูป (conjugation)](#3-การผันรูป-conjugation)
4. [การเปลี่ยนเป็นตัวอ่าน (romanization)](#4-การเปลี่ยนเป็นตัวอ่าน-romanization)
5. [พจนานุกรมคันจิ (kanji dictionary)](#5-พจนานุกรมคันจิ-kanji-dictionary)
6. [accent](#6-accent)

## corpus search
7. [บทความ NHK News Easy](#7-บทความ-NHK-News-Easy)
8. [ตัวอย่างประโยค NHK News Web](#8-ตัวอย่างประโยค-NHK-News-Web)
9. [ตัวอย่างประโยค Twitter](#9-ตัวอย่างประโยค-Twitter)

## extra
10. [Wikipedia search](#10-Wikipedia-search)


## 1. พจนานุกรม (word dictionary)
(basic ~ advanced) from [JTDic](http://www.jtdic.com/2008/japanese.aspx) 

พิมพ์คำศัพท์ภาษาญี่ปุ่นหรือคำศัพท์ไทย แล้วกดส่ง ระบบจะหาคำแปลใน JTDic 

พิมพ์ได้ทั้งคันจิและฮืรางานะ (ไม่ใช่การแปลทั้งประโยค)

![dic](https://user-images.githubusercontent.com/44984892/79286135-d5f05a80-7ee9-11ea-877f-2c5392765d0c.png)


## 2. การตัดคำ (tokenization)
(basic) 

ตัดคำโดยใช้โปรแกรม [`mecab-python3 1.0.3`](https://pypi.org/project/mecab-python3/)

พิมพ์คำว่า `ตัด`, `token`, `切って` หรือ `分けて` ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะตัดประโยคยาวๆ เป็นคำศัพท์สั้นๆ พร้อมทั้งอธิบายวิธีอ่าน รูปพจนานุกรมและประเภทคำ 

เช่น `ตัด 昨日の夜は何を食べましたか`

![token](https://user-images.githubusercontent.com/44984892/79700239-867da600-82be-11ea-9aec-6d5ed731d004.png)

ตารางประเภทคำ
|ใน `MeCab`|English|ใน nozomibot|
|:-:|:-:|:-:|
|動詞(どうし)|verb|กริยา|
|名詞(めいし)|noun|คำนาม|
|代名詞(だいめいし)|pronoun|สรรพนาม|
|形容詞(けいようし)|adjective|i-adj|
|形状詞(けいじょうし)|na-adjective|na-adj|
|助詞(じょし)|postposition|คำช่วย|
|助動詞(じょどうし)|auxiliary verb|คำช่วยที่ผันรูป|
|副詞(ふくし)|adverb|adv|
|接頭辞(せっとうじ)|prefix|prefix|
|接尾辞(せつびじ)|suffix|suffix|
|接続詞(せつぞくし)|conjunction|คำเชื่อม|
|連体詞(れんたいし)|determiner|คำขยายคำนาม|
|感動詞(かんどうし)|interjection|คำอุทาน|
|フィラー|filler|filler|
|記号|symbol|เครื่องหมาย|
|その他|others|อื่นๆ|


## 3. การผันรูป (conjugation)
(basic)

พิมพ์คำว่า `ผัน`, `conj` หรือ `活用` ไว้หน้าศัพท์ที่เป็นกิริยาหรือคำคุณศัพท์(i-adj)ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะผันคำกิริยาหรือคุณศัพท์เป็นรูปแบบต่างๆตามหลักไวยากรณ์ 

เช่น `ผัน 行く`

![conj](https://user-images.githubusercontent.com/44984892/79696294-182ce980-82a6-11ea-9f8d-47e4f771bcac.png)

|JP|EN|TH|
|:-:|:-:|:-:|
|辞書(じしょ)形|dic form / lemma|รูปพจนานุกรม|
|ない形|nai form|รูปปฏิเสธ|
|なかった形|nakatta form|รูปปฏิเสธ อดีต|
|ます形|masu form|คำสร้อย (รูปสุภาพ)|
|て形|te form|รูปที่เชื่อมกับคำต่างๆ|
|た形|ta form|รูปอดีต|
|ば形|ba form|รูปเงื่อนไข|
|命令(めいれい)形|imperative form|รูปคำสั่ง|
|意向(いこう)形|volitional form|จะ เถอะ|
|可能(かのう)形|potential form|รูปสามารถ|


## 4. การเปลี่ยนเป็นตัวอ่าน (romanization)
(basic)

พิมพ์คำว่า `อ่าน`, `読み方`, `โรมัน`, `roman` หรือ `ローマ字` ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะเปลี่ยนประโยคเป็นอักษรโรมันแบบ Hepburn ([คำอธิบายโดยราชบัณฑิต](https://github.com/nozomiyamada/nozomibot/blob/master/static/japanese_romanization.pdf)) ซึ่งสะกดคล้ายกับภาษาอังกฤษและใช้คนละตัวต่อ allophone เช่น

- さ/sa　し/shi　す/su　せ/se　そ/so　(พยัญชนะหน้าสระ i มักจะ palatalize)
- た/ta　ち/chi　つ/tsu　て/te　と/te　(พยัญชนะ t หน้าสระ u จะ dentalize เป็น ts)
- ほんば/homba　ほんや/honya　(พยัญชนะ n จะ assimilate)
- かっさい/kassai　まった/matta　まっちゃ/matcha　(っ เป็น consonant gemination)

แนะนำไม่ให้ใช้คันจิเยอะ เพราะอาจจะเปลี่ยนผิดก็ได้

![roman](https://user-images.githubusercontent.com/44984892/79700315-04da4800-82bf-11ea-9829-59fba1fee877.png)


## 5. พจนานุกรมคันจิ (kanji dictionary)
(intermediate ~ advanced) 

ประมาณ 3000 ตัว from [Goo辞書](https://dictionary.goo.ne.jp/kanji/)

พิมพ์คำว่า `คันจิ`, `kanji` หรือ `漢字` ไว้หน้าคันจิตัวเดียว แล้วกดส่ง ระบบจะแสดงวิธีอ่านและความหมาย

เช่น `คันจิ 望`
    
![kanji](https://user-images.githubusercontent.com/44984892/79066450-2f863880-7ce2-11ea-8c20-39dc224820ef.png)


## 6. accent
(basic ~ advanced) 

พิมพ์คำว่า `accent` หรือ `アクセント` ไว้หน้าคำศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะแสดง accent ของคำนั้น

ญ ปัจจุบันมีประมาณ 12000 คำ

เช่น `accent 人形`
    
![accent](https://user-images.githubusercontent.com/44984892/79066417-f4840500-7ce1-11ea-8786-038f2fb866ee.png)
    
ゆ/びに\んぎょう = ![yubiningyo](https://user-images.githubusercontent.com/44984892/79059193-4193b700-7ca1-11ea-931b-d52121fec7d2.png)

pitch accent ของภาษาถิ่นโตเกียว (ภาษากลาง) มีลักษณะดังนี้

- เสียงจะขึ้นลง `ระหว่างพยางค์` กล่าวคือ การขึ้นลงจะเกิดตราบใดที่มีอย่างน้อย 2 พยางค์ ไม่มีวรรณยุคต์แบบภาษาไทย ซึ่งมีการขึ้นลงของเสียงในหนึ่งพยางค์
- ตัวแรกกับตัวที่สอง ความสูงต้องต่างกัน (ตัวที่สองต้องขึ้นหรือลง)
- ในคำหนึ่ง ถ้าเสียงลงแล้ว ไม่ขึ้นอีก
- accent ของคำประสมไม่เหมือนกับคำที่เป็นส่วนประกอบ เช่น ち\ば กับ ち/ばけ\ん

อ่านเพิ่มเติม
[link (TUFS)](http://www.coelang.tufs.ac.jp/ja/th/pmod/practical/01-08-01.php)


## 7. บทความ NHK News Easy
(basic ~ intermediate) 

NHK News Web Easy : https://www3.nhk.or.jp/news/easy/ 

พิมพ์คำว่า `NHK` เท่านั้น แล้วกดส่ง ระบบจะสุ่มเลือกบทความจาก NHK web easy backnumbers (ช่วงเวลา 2013-2020 ประมาณ 6000 บทความ) ซึ่งเป็นบทความที่เขียนโดยภาษาง่ายและมีประโยชน์ในการฝึกอ่านภาษาญี่ปุ่น

![nhk](https://user-images.githubusercontent.com/44984892/79058948-705c5e00-7c9e-11ea-9d72-e4173b27c410.png)


## 8. ตัวอย่างประโยค NHK News Web
(intermediate ~ advanced) 

NHK News Web : https://www3.nhk.or.jp/news/ 

พิมพ์คำว่า `corpus`, `ตัวอย่าง` หรือ `例文` ไว้หน้าคำศัพท์ญี่ปุ่น แล้วกดส่ง ระบบจะแสดงตัวอย่างประโยคที่สุ่มเลือก (maximum 5) มาจาก NHK News Web ซึ่งช่วงเวลา 2012-2020 (ประมาณ 1.5 แสนบทความ)

เช่น `例文 注目`

ถ้าใส่ตัวเลขข้างหลัง กำหนดจำนวนที่เก็บมาได้ (แต่ไม่ควรเยอะ อาจจะพัง)

เช่น `ตัวอย่าง オリンピック 10`

ค้นหาคำศัพท์ตรงตามที่พิมพ์ เท่านั้น เช่น ค้นหาคำว่า 行きました จะได้ผลลัพธ์ของบทความที่มีแต่คำว่า 行きました ผลลัพธ์จะไม่รวมรูปอื่นๆ เช่น 行く, 行けば, 行った
    
![reibun](https://user-images.githubusercontent.com/44984892/79751872-88d31500-833d-11ea-8d13-1491146c7116.png)
![reibun2](https://user-images.githubusercontent.com/44984892/79750834-d3ec2880-833b-11ea-99b7-a405ac2faa60.png)

## 9. ตัวอย่างประโยค Twitter
(intermediate ~ advanced) 

พิมพ์คำว่า `twitter`, `tweet`, `ツイート`, `ツイッター` หรือ `ทวีต` ไว้หน้าคำศัพท์ญี่ปุ่น แล้วกดส่ง ระบบจะแสดงตัวอย่างประโยคที่สุ่มเลือก (default maximum 5 tweets) มาจาก twitter ช่วงเวลา มาราคม - สิงหาคม 2020 (ประมาณ 2 ล้านทวีต)

เช่น `tweet やばい`

ถ้าใส่ตัวเลขข้างหลัง กำหนดจำนวนที่เก็บมาได้ (แต่ไม่ควรเยอะ อาจจะพัง)

เช่น `tweet コロナ 20`

![tweet](https://user-images.githubusercontent.com/44984892/79300781-eae0e400-7f11-11ea-87b2-271291dacb2a.png)
![tweet2](https://user-images.githubusercontent.com/44984892/79750969-04cc5d80-833c-11ea-9fe5-e0c9677a1252.png)



## 10. Wikipedia search
(intermediate ~ advanced)

พิมพ์คำว่า `วิกิ`, `wiki` หรือ `ウィキ` ไว้หน้าคำศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะค้นหาใน Wikipedia Japan และแสดงย่อหน้าแรกกับลิงค์

เช่น "วิกิ AKB48"
    
![wiki](https://user-images.githubusercontent.com/44984892/79286155-e7396700-7ee9-11ea-9d12-be3f328a033d.png)



# feedback & further development

หากเจอข้อผิดพลาดหรือ bug ต่างๆ กรุณารบกวนแจ้งให้ทราบโดยพิมพ์ `feedback (เมสเสจของคุณ)`

หรือติดต่อทาง [Facebook Page](https://www.facebook.com/botnozomi) ได้ครับ 

ขอบคุณครับ
