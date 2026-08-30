# ProTeachHelper — kanallarga e'lon tarqatuvchi bot

Botni istalgan kanalingizga admin qilib qo'shasiz, u kanalni **o'zi ro'yxatga
oladi**. Keyin bitta e'lonni bir vaqtda tanlangan kanallarga yuborasiz.

- Har qanday xabar: matn, rasm, video, fayl, ovozli xabar, stiker, **albom**
- E'lon ostida havolali **inline tugmalar**
- **Ko'p admin** — ega boshqa adminlarni bot orqali qo'shadi
- Kanal avtomatik ulanadi va bot admin huquqidan mahrum bo'lsa avtomatik o'chadi
- Formatlash (qalin, kursiv, havola) to'liq saqlanadi — `copy_message` ishlatiladi

---

## Tez boshlash

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env          # Linux/macOS: cp .env.example .env
# .env ni to'ldiring, so'ng:
python bot.py
```

### `.env`

| O'zgaruvchi | Nima | Majburiymi |
|---|---|---|
| `BOT_TOKEN` | BotFather bergan token | ✅ |
| `OWNER_ID` | Bot egasining Telegram ID si. Botga `/id` yozib bilib olasiz | ✅ |
| `DATABASE_URL` | Postgres ulanish satri. Bo'sh bo'lsa SQLite ishlatiladi | Render'da ✅ |
| `DB_PATH` | SQLite fayli (standart: `data/bot.db`) | — |
| `WEBHOOK_BASE_URL` | Berilsa webhook rejimi yoqiladi. Render buni o'zi beradi | — |
| `WEBHOOK_PATH` | Webhook manzili (standart: `/webhook`) | — |
| `WEBHOOK_SECRET` | Bo'sh bo'lsa tokendan avtomatik hosil qilinadi | — |
| `PORT` | Webhook rejimidagi port (standart: `8080`) | — |
| `SEND_DELAY` | Kanallar orasidagi pauza, soniya (standart: `0.06`) | — |

---

## Kanalni ulash

1. Botni kanalingizga **qo'shing**
2. Uni **administrator** qiling va **«Post yuborish»** huquqini yoqing
3. Egaga «➕ Yangi kanal ulandi» xabari keladi — tayyor

> ⚠️ Kanalni faqat **botning admini** ulay oladi. Begona odam botni o'z kanaliga
> qo'shsa, bot o'sha kanaldan avtomatik chiqib ketadi va egaga xabar boradi.

Bot kanaldan chiqarilsa yoki admin huquqi olib qo'yilsa, kanal ro'yxatda 🔴
bo'lib qoladi va e'lon yuborilmaydi. Qayta admin qilsangiz o'zi tiklanadi.

---

## E'lon yuborish

```
📢 E'lon yuborish
   ↓
e'lonni botga yuborasiz  (matn / rasm / video / fayl / albom)
   ↓
tugma qo'shasizmi?  →  ha bo'lsa tugmalarni yozasiz
   ↓
kanal tanlash menyusi:  ☑️ Hammasi │ 📡 Kanallar tanlash │ 👀 Ko'rib chiqish │ ❌ Bekor
   ↓
👀 preview — e'lon aynan qanday ko'rinishini ko'rasiz
   ↓
🚀 yuborish  →  hisobot: nechtasi ketdi, qaysi biri xato berdi
```

### Kanal tanlash

Boshida **hech qaysi kanal tanlanmagan**. Ikki yo'l bor:

- **☑️ Hammasi** — barcha kanallar bir bosishda tanlanadi
- **📡 Kanallar tanlash** — kanallar ro'yxati ochiladi:
  - kanal ustiga bossangiz ✅ bo'ladi
  - yana bossangiz ⬜️ ga qaytadi va **o'sha kanalga e'lon bormaydi**
  - tanlab bo'lgach **✔️ Tayyor** → yuborish menyusiga qaytasiz

Ro'yxatdagi har bir bosish xabarni **joyida** yangilaydi — chatga yangi xabar
qo'shilmaydi.

Istalgan bosqichda `/cancel` yoki «❌ Bekor qilish».

### Tugmalar formati

```
📚 Kursga yozilish - https://t.me/misol
🌐 Sayt - https://misol.uz | 📸 Instagram - @misol
```

- Har bir **qator** — alohida tugmalar qatori
- `|` — bitta qatorga bir nechta tugma
- Tugma matni va havola ` - ` (bo'sh joy, chiziqcha, bo'sh joy) bilan ajratiladi
- `@username` va `t.me/...` avtomatik to'liq havolaga aylantiriladi

> **Telegram cheklovi:** albom (bir nechta rasm) ostiga inline tugma qo'yib
> bo'lmaydi. Shuning uchun albomga tugma qo'shsangiz, bot ularni albomdan keyin
> alohida xabarda yuboradi — o'sha xabar matnini bot sizdan so'raydi.

---

## Loyiha tuzilishi

```
bot.py                  ishga tushirish, polling/webhook rejimi, routerlar
config.py               .env va hosting env o'zgaruvchilari
render.yaml             Render Blueprint
Dockerfile              konteyner

database/
  db.py                 SQLite / Postgres backendlari, bir xil API
  channels.py           kanallar CRUD
  admins.py             adminlar CRUD (OWNER_ID doim admin)

handlers/
  start.py              /start, /cancel, /id, bosh menyu, umumiy bekor qilish
  channels.py           my_chat_member — avtomatik ro'yxatga olish; kanallar ro'yxati
  admins.py             admin qo'shish/o'chirish (faqat ega)
  post.py               e'lon yaratish FSM: mazmun → tugma → kanal → preview → yuborish
  fallback.py           tushunilmagan xabarlar (eng oxirgi router)

keyboards/inline.py     barcha inline klaviaturalar
middlewares/access.py   faqat shaxsiy chat + faqat adminlar
utils/
  album.py              albom (media group) yig'uvchi middleware
  buttons.py            tugmalar matnini parse qilish
  post.py               e'lonni yasash va kanallarga yetkazish
  ui.py                 safe_edit yordamchisi
```

---

## Deploy

Bot ikki rejimda ishlay oladi va rejimni **o'zi tanlaydi**:

| Rejim | Qachon yoqiladi | Qayerda |
|---|---|---|
| **polling** | standart | lokal kompyuter, VPS, Docker |
| **webhook** | `WEBHOOK_BASE_URL` yoki `RENDER_EXTERNAL_URL` mavjud bo'lsa | Render |

Baza ham shunday: `DATABASE_URL` berilgan bo'lsa **Postgres**, aks holda
**SQLite** fayli.

### Variant 1 — Render (tekin)

Render'ning ikkita xususiyatini bilib qo'yish kerak:

1. **Ochiq port talab qilinadi.** Shuning uchun bu yerda webhook rejimi
   ishlaydi — bot `$PORT` da HTTP server ochadi, Telegram unga so'rov yuboradi.
2. **Diski o'chuvchan.** `data/bot.db` har deployda va har uyg'onishda
   yo'qoladi, shuning uchun **tashqi Postgres shart**.

**1-qadam — tekin Postgres (Neon).** [neon.tech](https://neon.tech) da ro'yxatdan
o'ting → yangi project → *Connection string* ni nusxalang. U shunday ko'rinadi:

```
postgresql://user:parol@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

**2-qadam — Render.** Dashboard → **New → Blueprint** → GitHub repongizni
tanlang. `render.yaml` allaqachon repoda, shuning uchun Render hamma narsani
o'zi sozlaydi. So'ng **Environment** bo'limiga uchta qiymatni kiriting:

| Kalit | Qiymat |
|---|---|
| `BOT_TOKEN` | BotFather bergan token |
| `OWNER_ID` | sizning Telegram ID ingiz |
| `DATABASE_URL` | Neon'dan nusxalagan satr |

`WEBHOOK_BASE_URL` va `PORT` ni yozish **shart emas** — Render ularni
`RENDER_EXTERNAL_URL` va `PORT` orqali o'zi beradi. Webhook maxfiy kaliti ham
tokendan avtomatik hosil bo'ladi.

**3-qadam — uxlab qolmasligi uchun.** Tekin Render 15 daqiqa jimlikdan keyin
uxlaydi; uyg'ongan xizmatning birinchi javobi ~50 soniya kechikadi.
[cron-job.org](https://cron-job.org) da har 10 daqiqada
`https://<xizmat-nomi>.onrender.com/healthz` manzilini so'raydigan vazifa
qo'ying — bot doim uyg'oq turadi (tekin planda 750 soat/oy bor, bitta xizmatga
aynan yetadi).

Deploy loglarida quyidagini ko'rsangiz hammasi joyida:

```
Baza: PostgreSQL
Bot ishga tushdi: @sizning_bot (id=...) — webhook rejimi
Webhook o'rnatildi: https://....onrender.com/webhook
HTTP server tinglayapti: 0.0.0.0:10000
```

> ⚠️ Render'ga qo'ygandan keyin **lokal nusxani o'chiring**. Bir token bilan
> ikkita nusxa ishlasa Telegram `Conflict: terminated by other getUpdates`
> xatosini beradi.

### Variant 2 — Oracle Cloud Always Free VM

Abadiy tekin, 4 ARM yadro / 24 GB RAM, hech qanday cheklovsiz.

```bash
# 1. VM yarating: Ampere (ARM), Ubuntu 24.04, keyin SSH bilan kiring
sudo apt update && sudo apt install -y python3-venv git

# 2. Loyihani joylashtiring
git clone <repo> ~/ProTeachHelper     # yoki scp bilan yuklang
cd ~/ProTeachHelper
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. .env ni yarating va to'ldiring
cp .env.example .env && nano .env
```

`/etc/systemd/system/proteachbot.service`:

```ini
[Unit]
Description=ProTeachHelper e'lon boti
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ProTeachHelper
ExecStart=/home/ubuntu/ProTeachHelper/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now proteachbot
sudo journalctl -u proteachbot -f     # loglarni kuzatish
```

`Restart=always` tufayli bot yiqilsa yoki server qayta yuklansa o'zi ko'tariladi.

### Variant 3 — Docker

```bash
docker build -t proteach-bot .
docker run -d --name proteach-bot --restart unless-stopped \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  proteach-bot

docker logs -f proteach-bot
```

`-v` **majburiy**: usiz konteyner qayta yaratilganda kanallar va adminlar
ro'yxati yo'qoladi.

### Backup

SQLite rejimida butun holat bitta faylda — `data/bot.db`:

```bash
sqlite3 data/bot.db ".backup '/home/ubuntu/backup/bot-$(date +%F).db'"
```

Postgres (Neon) rejimida Neon o'zi nusxa saqlaydi — qo'shimcha ish kerak emas.

---

## Xavfsizlik

- `.env` `.gitignore` va `.dockerignore` da — token repoga ham, image ichiga ham
  tushmaydi. Docker'da token faqat `--env-file` orqali beriladi.
- Token ochilib qolsa, BotFather'da `/revoke` qilib yangisini oling va `.env` ni
  yangilang.
- **Bot faqat shaxsiy chatda javob beradi.** Guruh, supergruppa va kanalda u
  butunlay jim — u yerga faqat adminning e'loni boradi, boshqa hech narsa.
- **Begona odamga hech qanday javob yo'q** — na matn, na ogohlantirish. Urinish
  faqat serverda logga tushadi (`Ruxsatsiz urinish: <ism> (id=...)`).
- Buyruqlar menyusi ham faqat shaxsiy chatda ko'rinadi
  (`BotCommandScopeAllPrivateChats`).
- Yangi admin qo'shishning eng qulay yo'li — o'sha odamning xabarini botga
  **forward** qilish: u begona bo'lgani uchun `/id` yozib o'z ID sini bila olmaydi.
- Tugma havolalarida faqat `http://`, `https://` va `tg://` sxemalariga ruxsat
  beriladi.

---

## Cheklovlar

- E'lon holati xotirada saqlanadi (`MemoryStorage`) — bot qayta ishga
  tushirilsa, tugallanmagan e'lon yo'qoladi. Kanallar va adminlar bazada,
  ular yo'qolmaydi.
- Render'ning **tekin** planida SQLite ishlatilsa, kanallar va adminlar har
  deployda hamda har uyg'onishda yo'qoladi — shuning uchun u yerda
  `DATABASE_URL` (Postgres) berilishi shart.
- Kanallar ro'yxatida obunachilar soni birinchi 25 ta kanal uchun ko'rsatiladi
  (`handlers/channels.py`, `DETAIL_LIMIT`) — Telegram API chaqiruvlarini tejash uchun.
- Rejalashtirilgan (belgilangan vaqtda) yuborish yo'q — e'lon darhol ketadi.
