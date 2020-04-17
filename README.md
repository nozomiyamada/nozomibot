# nozomibot

Linebot สำหรับผู้เรียนภาษาญี่ปุ่น

written in `Python 3.7 + Flask 1.1` and `MySQL` (AWS RDS), deployed to [`heroku`](https://www.heroku.com)

![834majrs](https://user-images.githubusercontent.com/44984892/79058885-92a1ac00-7c9d-11ea-8600-6ed00def18ca.png)

Line ID : `@834majrs`


# features
## linguistic information

1. [word dictionary](#1-dictionary-mode)
2. [tokenization (การตัดคำ)](#2-tokenization-mode)
3. [conjugation (การผันรูป)](#3-conjugation-mode)
4. [romanization (การเปลี่ยนเป็นอักษรโรมัน)](#4-romanization-mode)
5. [kanji dictionary](#5-kanji-dictionary-mode)
6. [accent](#6-accent-mode)

## corpus search
7. [random NHK News Easy (สุ่มเลือกบทความ)](#7-random-nhk-news-easy-article)
8. [examples from NHK News Web corpus (การค้นหาตัวอย่างประโยค)](#8-examples-from-nhk-news-web-corpus)
9. [examples from Twitter corpus (การค้นหาตัวอย่างประโยค)](#9-examples-from-twitter-corpus)

## extra
10. [Wikipedia searcher](#10-wikipedia-searcher)


## 1. dictionary mode 
(basic~advanced)　from [JTDic](http://www.jtdic.com/2008/japanese.aspx) 

พิมพ์คำศัพท์ภาษาญี่ปุ่นหรือคำศัพท์ไทย แล้วกดส่ง ระบบจะหาคำแปลใน JTDic (ไม่ใช่การแปลทั้งประโยค) พิมพ์ได้ทั้งคันจิและฮืรางานะ
    
![dic](https://user-images.githubusercontent.com/44984892/79286135-d5f05a80-7ee9-11ea-877f-2c5392765d0c.png)


## 2. tokenization mode
(basic) โดยใช้ [`mecab-python3 0.996.5`](https://pypi.org/project/mecab-python3/)

พิมพ์คำว่า **ตัด**, **token**, **切って** หรือ **分けて** ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะตัดประโยคยาวๆ เป็นคำศัพท์สั้นๆ พร้อมทั้งอธิบายวิธีอ่าน รูปพจนานุกรมและประเภทคำ 

เช่น "ตัด 昨日の夜は何を食べましたか"
    
![token](https://user-images.githubusercontent.com/44984892/79066334-5a23c180-7ce1-11ea-8cfd-b3606a13e5ca.png)


## 3. conjugation mode
(basic)

พิมพ์คำว่า **ผัน**, **conj** หรือ **活用** ไว้หน้าศัพท์ที่เป็นกิริยาหรือคำคุณศัพท์(i-adj)ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะผันคำกิริยาหรือคุณศัพท์เป็นรูปแบบต่างๆตามหลักไวยากรณ์ 

เช่น "ผัน 行く"

![conj](https://user-images.githubusercontent.com/44984892/79417309-de28c280-7fdb-11ea-96f0-4ba4e0fb833e.png)

|JP|EN|TH|
|:-:|:-:|:-:|
|ない形|nai form|รูปปฏิเสธ|
|なかった形|nakatta form|รูปปฏิเสธ อดีต|
|ます形|masu form|คำสร้อย (รูปสุภาพ)|
|辞書(じしょ)形|dic form / lemma|รูปพจนานุกรม|
|て形|te form|รูปที่เชื่อมกับคำต่างๆ|
|た形|ta form|รูปอดีต|
|ば形|ba form|รูปเงื่อนไข|
|命令(めいれい)形|imperative form|รูปคำสั่ง|
|意向(いこう)形|volitional form|จะ เถอะ|



## 4. romanization mode
(basic)

พิมพ์คำว่า **โรมัน**, **roman** หรือ **ローマ字** ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะเปลี่ยนประโยคเป็นอักษรโรมันแบบ Hepburn ([คำอธิบายโดยราชบัณฑิต](https://github.com/nozomiyamada/nozomibot/blob/master/japanese_romanization.pdf)) ซึ่งสะกดคล้ายกับภาษาอังกฤษและใช้คนละตัวต่อ allophone เช่น

- さ/sa　し/shi　す/su　せ/se　そ/so　(พยัญชนะหน้าสระ i มักจะ palatalize)
- た/ta　ち/chi　つ/tsu　て/te　と/te　(พยัญชนะ t หน้าสระ u จะ dentalize เป็น ts)
- ほんば/homba　ほんや/honya　(พยัญชนะ n จะ assimilate)
- かっさい/kassai　まった/matta　まっちゃ/matcha　(っ เป็น consonant gemination)

แนะนำไม่ให้ใช้คันจิเยอะ เพราะอาจจะเปลี่ยนผิดก็ได้

![roman](https://user-images.githubusercontent.com/44984892/79286180-020bdb80-7eea-11ea-80ac-b16d4df4ae4e.png)


## 5. kanji dictionary mode
(intermediate~advanced) ประมาณ 3000 ตัว from [Goo](https://dictionary.goo.ne.jp/kanji/)

พิมพ์คำว่า **คันจิ**, **kanji** หรือ **漢字** ไว้หน้าคันจิตัวเดียว แล้วกดส่ง ระบบจะแสดงวิธีอ่านและความหมาย

เช่น "คันจิ 望"
    
![kanji](https://user-images.githubusercontent.com/44984892/79066450-2f863880-7ce2-11ea-8c20-39dc224820ef.png)


## 6. accent mode
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


## 7. random NHK News Easy article
(basic~intermediate) https://www3.nhk.or.jp/news/easy/ ช่วงเวลา 2013-2020 ประมาณ 6000 บทความ

พิมพ์คำว่า **NHK** แล้วกดส่ง ระบบจะสุ่มเลือกบทความจาก NHK web easy backnumbers (2013-2020) ซึ่งเป็นบทความที่เขียนโดยภาษาง่ายและมีประโยชน์ในการฝึกอ่านภาษาญี่ปุ่น
    
![nhk](https://user-images.githubusercontent.com/44984892/79058948-705c5e00-7c9e-11ea-9d72-e4173b27c410.png)


## 8. examples from NHK News Web corpus 
(intermediate~advanced) https://www3.nhk.or.jp/news/ ช่วงเวลา 2012-2019 แสนกว่าบทความ

พิมพ์คำว่า **corpus**, **ตัวอย่าง** หรือ **例文** ไว้หน้าคำศัพท์ญี่ปุ่น แล้วกดส่ง ระบบจะแสดงตัวอย่างประโยคที่สุ่มเลือก (maximum 5) มาจาก NHK News Web corpus ซึ่งตอนนี้มีประมาณแสนบทความ

เช่น "ตัวอย่าง 注目"

ค้นหาคำศัพท์ตรงตามที่พิมพ์ เท่านั้น เช่น ค้นหาคำว่า 行きました จะได้ผลลัพธ์ของบทความที่มีแต่คำว่า 行きました ผลลัพธ์จะไม่รวมรูปอื่นๆ เช่น 行く, 行けば, 行った
    
![reibun](https://user-images.githubusercontent.com/44984892/79146927-58472480-7ded-11ea-9991-50217857c553.png)


## 9. examples from Twitter corpus
(intermediate~advanced) ช่วงเวลา 1/1 - 31/3 2020 แสนกว่า tweet

พิมพ์คำว่า **twitter**, **tweet**, **ツイート** หรือ **ツイッター** ไว้หน้าคำศัพท์ญี่ปุ่น แล้วกดส่ง ระบบจะแสดงตัวอย่างประโยคที่สุ่มเลือก (default maximum 5 tweets) มาจาก twitter

เช่น "tweet やばい"

![tweet](https://user-images.githubusercontent.com/44984892/79300781-eae0e400-7f11-11ea-87b2-271291dacb2a.png)

ถ้าใส่ตัวเลขข้างหลัง กำหนดจำนวนที่เก็บได้ (แต่ไม่ควรเยอะ อาจจะพัง)

เช่น "tweet コロナ 20"

## 10. Wikipedia searcher
(intermediate~advanced)

พิมพ์คำว่า **วิกิ**, **wiki** หรือ **ウィキ** ไว้หน้าคำศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะค้นหาใน Wikipedia Japan และแสดงย่อหน้าแรกกับลิงค์

เช่น "วิกิ AKB48"
    
![wiki](https://user-images.githubusercontent.com/44984892/79286155-e7396700-7ee9-11ea-9d12-be3f328a033d.png)



# feedback & further development

หากเจอข้อผิดพลาดหรือ bug ต่างๆ กรุณารบกวนแจ้งให้ทราบโดยพิมพ์ "feedback เมสเสจ" 

หรือติดต่อทาง Facebook (ชื่อ: Nozomi Ymd) ด้วยนะครับ

ขอบคุณครับ
