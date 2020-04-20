# nozomibot (Last Update: 20 April 2020)

Linebot สำหรับผู้เรียนภาษาญี่ปุ่น

written in `Python 3.7 + Flask 1.1` and `MySQL` (AWS RDS), deployed to [`heroku`](https://www.heroku.com)

![834majrs](https://user-images.githubusercontent.com/44984892/79058885-92a1ac00-7c9d-11ea-8600-6ed00def18ca.png)

Line ID : `@834majrs`


# features
## linguistic information

1. [word dictionary](#1-dictionary-mode)
2. [tokenization (การตัดคำ)](#2-tokenization-mode)
3. [conjugation (การผันรูป)](#3-conjugation-mode)
4. [kanazation (การเปลี่ยนเป็นอักษรคานะ)](#4-kanazation-mode)
5. [romanization (การเปลี่ยนเป็นอักษรโรมัน)](#5-romanization-mode)
6. [kanji dictionary](#6-kanji-dictionary-mode)
7. [accent](#7-accent-mode)

## corpus search
8. [random NHK News Easy (สุ่มเลือกบทความ)](#8-random-nhk-news-easy-article)
9. [examples from NHK News Web corpus (การค้นหาตัวอย่างประโยค)](#9-examples-from-nhk-news-web-corpus)
10. [examples from Twitter corpus (การค้นหาตัวอย่างประโยค)](#10-examples-from-twitter-corpus)

## extra
11. [Wikipedia searcher](#11-wikipedia-searcher)


## 1. dictionary mode 
(basic~advanced)　from [JTDic](http://www.jtdic.com/2008/japanese.aspx) 

พิมพ์คำศัพท์ภาษาญี่ปุ่นหรือคำศัพท์ไทย แล้วกดส่ง ระบบจะหาคำแปลใน JTDic (ไม่ใช่การแปลทั้งประโยค) พิมพ์ได้ทั้งคันจิและฮืรางานะ
    
![dic](https://user-images.githubusercontent.com/44984892/79286135-d5f05a80-7ee9-11ea-877f-2c5392765d0c.png)


## 2. tokenization mode
(basic) โดยใช้ [`mecab-python3 0.996.5`](https://pypi.org/project/mecab-python3/)

พิมพ์คำว่า **ตัด**, **token**, **切って** หรือ **分けて** ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะตัดประโยคยาวๆ เป็นคำศัพท์สั้นๆ พร้อมทั้งอธิบายวิธีอ่าน รูปพจนานุกรมและประเภทคำ 

เช่น "ตัด 昨日の夜は何を食べましたか"
    
![token](https://user-images.githubusercontent.com/44984892/79700239-867da600-82be-11ea-9aec-6d5ed731d004.png)

ตารางประเภทคำ
|JP|EN|TH|
|:-:|:-:|:-:|
|動詞(どうし)|verb|กริยา|
|名詞(めいし)|noun|คำนาม|
|形容詞(けいようし)|adjective|คำคุณศัพท์|
|副詞(ふくし)|adverb|คำวิเศษ|
|助詞(じょし)|postposition|คำช่วย|
|助動詞(じょどうし)|auxiliary verb|คำช่วยที่ผันรูป|
|接続詞(せつぞくし)|conjunction|คำเชื่อม|
|連体詞(れんたいし)|determiner|คำขยายคำนาม|
|感動詞(かんどうし)|interjection|คำอุทาน|
|接頭詞(せっとうし)|prefix|คำนำหน้า|
|フィラー|filler||
|記号|symbol|เครื่องหมาย|
|その他|others|อื่นๆ|


## 3. conjugation mode
(basic)

พิมพ์คำว่า **ผัน**, **conj** หรือ **活用** ไว้หน้าศัพท์ที่เป็นกิริยาหรือคำคุณศัพท์(i-adj)ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะผันคำกิริยาหรือคุณศัพท์เป็นรูปแบบต่างๆตามหลักไวยากรณ์ 

เช่น "ผัน 行く"

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


## 4. kanazation mode
(basic)

พิมพ์คำว่า **คานะ**, **kana** **かな** หรือ **読み方** ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะเปลี่ยนประโยคเป็นอักษรคานะ (ผสมฮิรางานะกับคาตาคานะ)

![kana](https://user-images.githubusercontent.com/44984892/79696227-9a68de00-82a5-11ea-9df5-15f954be9e82.png)


## 5. romanization mode
(basic)

พิมพ์คำว่า **โรมัน**, **roman** หรือ **ローマ字** ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะเปลี่ยนประโยคเป็นอักษรโรมันแบบ Hepburn ([คำอธิบายโดยราชบัณฑิต](https://github.com/nozomiyamada/nozomibot/blob/master/japanese_romanization.pdf)) ซึ่งสะกดคล้ายกับภาษาอังกฤษและใช้คนละตัวต่อ allophone เช่น

- さ/sa　し/shi　す/su　せ/se　そ/so　(พยัญชนะหน้าสระ i มักจะ palatalize)
- た/ta　ち/chi　つ/tsu　て/te　と/te　(พยัญชนะ t หน้าสระ u จะ dentalize เป็น ts)
- ほんば/homba　ほんや/honya　(พยัญชนะ n จะ assimilate)
- かっさい/kassai　まった/matta　まっちゃ/matcha　(っ เป็น consonant gemination)

แนะนำไม่ให้ใช้คันจิเยอะ เพราะอาจจะเปลี่ยนผิดก็ได้

![roman](https://user-images.githubusercontent.com/44984892/79700315-04da4800-82bf-11ea-9829-59fba1fee877.png)


## 6. kanji dictionary mode
(intermediate~advanced) ประมาณ 3000 ตัว from [Goo](https://dictionary.goo.ne.jp/kanji/)

พิมพ์คำว่า **คันจิ**, **kanji** หรือ **漢字** ไว้หน้าคันจิตัวเดียว แล้วกดส่ง ระบบจะแสดงวิธีอ่านและความหมาย

เช่น "คันจิ 望"
    
![kanji](https://user-images.githubusercontent.com/44984892/79066450-2f863880-7ce2-11ea-8c20-39dc224820ef.png)


## 7. accent mode
(intermediate~advanced) ประมาณ 7000 คำ from https://accent.u-biq.org/

พิมพ์คำว่า **accent** หรือ **アクセント** ไว้หน้าคำศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะแสดง accent ของคำนั้น

เช่น "accent 人形"
    
![accent](https://user-images.githubusercontent.com/44984892/79066417-f4840500-7ce1-11ea-8786-038f2fb866ee.png)
    
ゆ/びに\んぎょう = ![yubiningyo](https://user-images.githubusercontent.com/44984892/79059193-4193b700-7ca1-11ea-931b-d52121fec7d2.png)

pitch accent ของภาษาถิ่นโตเกียวมีลักษณะดังนี้

- เสียงจะขึ้นลง **ระหว่างพยางค์** กล่าวคือ การขึ้นลงจะเกิดตราบใดที่มีอย่างน้อย 2 พยางค์ ไม่มีวรรณยุคต์แบบภาษาไทย ซึ่งมีการขึ้นลงของเสียงในหนึ่งพยางค์
- ตัวแรกกับตัวที่สอง ความสูงต้องต่างกัน (ตัวที่สองต้องขึ้นหรือลง)
- ในคำหนึ่ง ถ้าเสียงลงแล้ว ไม่ขึ้นอีก
- accent ของคำประสมไม่เหมือนกับคำที่เป็นส่วนประกอบ เช่น ち\ば กับ ち/ばけ\ん

อ่านเพิ่มเติม
[link (TUFS)](http://www.coelang.tufs.ac.jp/ja/th/pmod/practical/01-08-01.php)


## 8. random NHK News Easy article
(basic~intermediate) https://www3.nhk.or.jp/news/easy/ ช่วงเวลา 2013-2020 ประมาณ 6000 บทความ

พิมพ์คำว่า **NHK** แล้วกดส่ง ระบบจะสุ่มเลือกบทความจาก NHK web easy backnumbers (2013-2020) ซึ่งเป็นบทความที่เขียนโดยภาษาง่ายและมีประโยชน์ในการฝึกอ่านภาษาญี่ปุ่น
    
![nhk](https://user-images.githubusercontent.com/44984892/79058948-705c5e00-7c9e-11ea-9d72-e4173b27c410.png)


## 9. examples from NHK News Web corpus 
(intermediate~advanced) https://www3.nhk.or.jp/news/ ช่วงเวลา 2012-2019 แสนกว่าบทความ

พิมพ์คำว่า **corpus**, **ตัวอย่าง** หรือ **例文** ไว้หน้าคำศัพท์ญี่ปุ่น แล้วกดส่ง ระบบจะแสดงตัวอย่างประโยคที่สุ่มเลือก (maximum 5) มาจาก NHK News Web corpus ซึ่งตอนนี้มีประมาณแสนบทความ

เช่น "ตัวอย่าง 注目"

ถ้าใส่ตัวเลขข้างหลัง กำหนดจำนวนที่เก็บมาได้ (แต่ไม่ควรเยอะ อาจจะพัง)

เช่น "オリンピック 10"

ค้นหาคำศัพท์ตรงตามที่พิมพ์ เท่านั้น เช่น ค้นหาคำว่า 行きました จะได้ผลลัพธ์ของบทความที่มีแต่คำว่า 行きました ผลลัพธ์จะไม่รวมรูปอื่นๆ เช่น 行く, 行けば, 行った
    
![reibun](https://user-images.githubusercontent.com/44984892/79751872-88d31500-833d-11ea-8d13-1491146c7116.png)
![reibun2](https://user-images.githubusercontent.com/44984892/79750834-d3ec2880-833b-11ea-99b7-a405ac2faa60.png)

## 10. examples from Twitter corpus
(intermediate~advanced) ช่วงเวลา 2/1 - 31/3 2020 สี่แสนกว่า tweet

พิมพ์คำว่า **twitter**, **tweet**, **ツイート** หรือ **ツイッター** ไว้หน้าคำศัพท์ญี่ปุ่น แล้วกดส่ง ระบบจะแสดงตัวอย่างประโยคที่สุ่มเลือก (default maximum 5 tweets) มาจาก twitter

เช่น "tweet やばい"

ถ้าใส่ตัวเลขข้างหลัง กำหนดจำนวนที่เก็บมาได้ (แต่ไม่ควรเยอะ อาจจะพัง)

เช่น "tweet コロナ 20"

![tweet](https://user-images.githubusercontent.com/44984892/79300781-eae0e400-7f11-11ea-87b2-271291dacb2a.png)
![tweet2](https://user-images.githubusercontent.com/44984892/79750969-04cc5d80-833c-11ea-9fe5-e0c9677a1252.png)



## 11. Wikipedia searcher
(intermediate~advanced)

พิมพ์คำว่า **วิกิ**, **wiki** หรือ **ウィキ** ไว้หน้าคำศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะค้นหาใน Wikipedia Japan และแสดงย่อหน้าแรกกับลิงค์

เช่น "วิกิ AKB48"
    
![wiki](https://user-images.githubusercontent.com/44984892/79286155-e7396700-7ee9-11ea-9d12-be3f328a033d.png)



# feedback & further development

หากเจอข้อผิดพลาดหรือ bug ต่างๆ กรุณารบกวนแจ้งให้ทราบโดยพิมพ์ "feedback เมสเสจ" 

หรือติดต่อทาง Facebook (ชื่อ: Nozomi Ymd) ด้วยนะครับ

ขอบคุณครับ
