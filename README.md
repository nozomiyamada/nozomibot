# nozomibot

Linebot สำหรับผู้เรียนภาษาญี่ปุ่น

![834majrs](https://user-images.githubusercontent.com/44984892/79058885-92a1ac00-7c9d-11ea-8600-6ed00def18ca.png)

Line ID : @834majrs

# functions

1. dictionary mode (from JTDic)
    > พิมพ์คำศัพท์ภาษาญี่ปุ่นหรือคำศัพท์ไทย แล้วกดส่ง ระบบจะหาคำแปลใน JTDic (ไม่ใช่การแปลทั้งประโยค) พิมพ์ได้ทั้งคันจิและฮืรางานะ
    
    ![dic](https://user-images.githubusercontent.com/44984892/79058956-794d2f80-7c9e-11ea-941b-439e322e6b34.png)

2. kanji mode (ประมาณ 3000 ตัว from Goo: https://dictionary.goo.ne.jp/kanji/) 
    > พิมพ์คำว่า "คันจิ" "kanji" หรือ "漢字" ไว้หน้าคันจิตัวเดียว แล้วกดส่ง ระบบจะแสดงวิธีอ่านและความหมาย
    >
    > เช่น "คันจิ 望"
    
    ![kanji](https://user-images.githubusercontent.com/44984892/79058950-74887b80-7c9e-11ea-9a5d-2e1c3a6d2c80.png)

3. tokenization mode (โดยใช้ MeCab)
    > พิมพ์คำว่า "ตัด" "token" "切って" หรือ "分けて" ไว้หน้าประโยคภาษาญี่ปุ่น แล้วกดส่ง ระบบจะตัดประโยคยาวๆ เป็นคำศัพท์สั้นๆ พร้อมทั้งอธิบายรูปพจนานุกรมและประเภทคำ 
    >
    > เช่น "ตัด 昨日の夜は何を食べましたか"
    
    ![token](https://user-images.githubusercontent.com/44984892/79058955-76ead580-7c9e-11ea-8c96-9096363ae9a5.png)

4. conjugation mode
    > พิมพ์คำว่า "ผัน" "conj" หรือ "活用" ไว้หน้าศัพท์ที่เป็นกิริยาหรือคำคุณศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะผันคำกิริยาหรือคุณศัพท์เป็นรูปแบบต่างๆตามหลักไวยากรณ์ 
    >
    > เช่น "ผัน 行く"
    
    ![conj](https://user-images.githubusercontent.com/44984892/79058953-75b9a880-7c9e-11ea-887c-08add2d5717c.png)

5. accent mode (ประมาณ 6000 คำ from https://accent.u-biq.org/)
    > พิมพ์คำว่า "accent" หรือ "アクセント" ไว้หน้าคำศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะแสดง accent ของคำนั้น
    >
    > เช่น "accent 人形"
    
    ![accent](https://user-images.githubusercontent.com/44984892/79058951-75211200-7c9e-11ea-8481-0b92ef6016a8.png)
    
    ゆ/びに\んぎょう = ![yubiningyo](https://user-images.githubusercontent.com/44984892/79059193-4193b700-7ca1-11ea-931b-d52121fec7d2.png)


6. wikipedia searcher
    > พิมพ์คำว่า "วิกิ" "wiki" หรือ "ウィキ" ไว้หน้าคำศัพท์ภาษาญี่ปุ่น แล้วกดส่ง ระบบจะค้นหาใน Wikipedia Japan และแสดงย่อหน้าแรก
    >
    > เช่น "วิกิ AKB48"
    
    ![wiki](https://user-images.githubusercontent.com/44984892/79058949-73efe500-7c9e-11ea-94f4-15ff161de270.png)

7. random NHK web easy article(ประมาณ 6000 บทความ https://www3.nhk.or.jp/news/easy/)
    > พิมพ์คำว่า "NHK" แล้วกดส่ง ระบบจะสุ่มเลือกบทความจาก NHK web easy backnumbers (2013-2020)
    
    ![nhk](https://user-images.githubusercontent.com/44984892/79058948-705c5e00-7c9e-11ea-9d72-e4173b27c410.png)

# feedback & further development

หากเจอข้อผิดพลาดหรือ bug ต่างๆ กรุณารบกวนแจ้งให้ทราบโดยพิมพ์ "feedback เมสเสจ" 

หรือติดต่อทาง Facebook (ชื่อ: Nozomi Ymd) ด้วยนะครับ

ขอบคุณครับ
