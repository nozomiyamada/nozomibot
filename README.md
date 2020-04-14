# nozomibot

Linebot สำหรับผู้เรียนภาษาญี่ปุ่น

written in `Python 3.7 + Flask 1.1` and `MySQL` (AWS RDS), deployed to [`heroku`](https://www.heroku.com)

![834majrs](https://user-images.githubusercontent.com/44984892/79058885-92a1ac00-7c9d-11ea-8600-6ed00def18ca.png)

Line ID : @834majrs


# features
much linguistic information & corpus search

## 1. dictionary mode from [JTDic](http://www.jtdic.com/2008/japanese.aspx) (basic~advanced)
พิมพ์คำศัพท์ภาษาญี่ปุ่นหรือคำศัพท์ไทย แล้วกดส่ง ระบบจะหาคำแปลใน JTDic (ไม่ใช่การแปลทั้งประโยค) พิมพ์ได้ทั้งคันจิและฮืรางานะ
    
![dic](https://user-images.githubusercontent.com/44984892/79066435-15e4f100-7ce2-11ea-9355-3434fdd88ffb.png)


## 2. tokenization mode (basic)
(โดยใช้ [`mecab-python3 0.996.5`](https://pypi.org/project/mecab-python3/))

พิมพ์คำว่า **ตัด**, **token**, **切って** หรือ **分けて** ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะตัดประโยคยาวๆ เป็นคำศัพท์สั้นๆ พร้อมทั้งอธิบายวิธีอ่าน รูปพจนานุกรมและประเภทคำ 

เช่น "ตัด 昨日の夜は何を食べましたか"
    
![token](https://user-images.githubusercontent.com/44984892/79066334-5a23c180-7ce1-11ea-8cfd-b3606a13e5ca.png)


## 3. conjugation mode (basic)
พิมพ์คำว่า **ผัน**, **conj** หรือ **活用** ไว้หน้าศัพท์ที่เป็นกิริยาหรือคำคุณศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะผันคำกิริยาหรือคุณศัพท์เป็นรูปแบบต่างๆตามหลักไวยากรณ์ 

เช่น "ผัน 行く"

![conj](https://user-images.githubusercontent.com/44984892/79066398-d5857300-7ce1-11ea-92b6-8abd042bea75.png)


## 4. romanization mode (basic)
พิมพ์คำว่า **โรมัน**, **roman** หรือ **ローマ字** ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะเปลี่ยนประโยคเป็นอักษรโรมัน

แนะนำไม่ให้ใช้คันจิเยอะ เพราะอาจจะเปลี่ยนผิดก็ได้

![roman](https://user-images.githubusercontent.com/44984892/79187171-c9b2c180-7e45-11ea-921d-87be6e269d59.png)


## 5. random NHK News Easy article (basic~intermediate)
(ประมาณ 6000 บทความ https://www3.nhk.or.jp/news/easy/)

พิมพ์คำว่า **NHK** แล้วกดส่ง ระบบจะสุ่มเลือกบทความจาก NHK web easy backnumbers (2013-2020) ซึ่งเป็นบทความที่เขียนโดยภาษาง่ายและมีประโยชน์ในการฝึกอ่านภาษาญี่ปุ่น
    
![nhk](https://user-images.githubusercontent.com/44984892/79058948-705c5e00-7c9e-11ea-9d72-e4173b27c410.png)


## 6. kanji dictionary mode (intermediate~advanced)
(ประมาณ 3000 ตัว from [Goo](https://dictionary.goo.ne.jp/kanji/) )

พิมพ์คำว่า **คันจิ**, **kanji** หรือ **漢字** ไว้หน้าคันจิตัวเดียว แล้วกดส่ง ระบบจะแสดงวิธีอ่านและความหมาย

เช่น "คันจิ 望"
    
![kanji](https://user-images.githubusercontent.com/44984892/79066450-2f863880-7ce2-11ea-8c20-39dc224820ef.png)


## 7. accent mode (intermediate~advanced)
(ประมาณ 7000 คำ from https://accent.u-biq.org/)

พิมพ์คำว่า **accent** หรือ **アクセント** ไว้หน้าคำศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะแสดง accent ของคำนั้น

เช่น "accent 人形"
    
![accent](https://user-images.githubusercontent.com/44984892/79066417-f4840500-7ce1-11ea-8786-038f2fb866ee.png)
    
ゆ/びに\んぎょう = ![yubiningyo](https://user-images.githubusercontent.com/44984892/79059193-4193b700-7ca1-11ea-931b-d52121fec7d2.png)
    
accent system ของภาษาญี่ปุ่น [link (TUFS)](http://www.coelang.tufs.ac.jp/ja/th/pmod/practical/01-08-01.php)


## 8. [NHK News Web](https://www3.nhk.or.jp/news/) corpus (intermediate~advanced)
พิมพ์คำว่า **corpus**, **ตัวอย่าง** หรือ **例文** ไว้หน้าคำศัพท์ญี่ปุ่น แล้วกดส่ง ระบบจะแสดงตัวอย่างประโขคที่สุ่มเลือกมาจาก NHK News Web (maximum 5)

เช่น "ตัวอย่าง 注目"

ค้นหาคำศัพท์ตรงตามที่พิมพ์ เท่านั้น เช่น ค้นหาคำว่า 行きました จะได้ผลลัพธ์ของบทความที่มีแต่คำว่า 行きました ผลลัพธ์จะไม่รวมรูปอื่นๆ เช่น 行く, 行けば, 行った
    
![reibun](https://user-images.githubusercontent.com/44984892/79146927-58472480-7ded-11ea-9991-50217857c553.png)


## 9. Wikipedia searcher (intermediate~advanced)
พิมพ์คำว่า **วิกิ**, **wiki** หรือ **ウィキ** ไว้หน้าคำศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะค้นหาใน Wikipedia Japan และแสดงย่อหน้าแรกกับลิงค์

เช่น "วิกิ AKB48"
    
![wiki](https://user-images.githubusercontent.com/44984892/79066428-09609880-7ce2-11ea-8d47-6787f5363ed2.png)



# feedback & further development

หากเจอข้อผิดพลาดหรือ bug ต่างๆ กรุณารบกวนแจ้งให้ทราบโดยพิมพ์ "feedback เมสเสจ" 

หรือติดต่อทาง Facebook (ชื่อ: Nozomi Ymd) ด้วยนะครับ

ขอบคุณครับ
