# Ilmkon School — Qayta Aloqa Boti

Taklif va e'tirozlar boti: majburiy kanal a'zoligi, admin/operator rollari, reklama (forward broadcast), Excel hisobot, rangli inline tugmalar (Bot API 9.4).

## Imkoniyatlar

- 🔒 **Majburiy kanal a'zoligi** — middleware orqali, bir nechta kanal qo'llanadi
- 📝 **Ro'yxatdan o'tish** — ism, telefon (Share Contact), rol (ota-ona / o'quvchi / xodim)
- 💡 **Taklif** va ⚠️ **E'tiroz** yuborish — anonim rejim bilan
- 🆔 Unikal raqamlar: `TAK-2026-0001` / `ETR-2026-0001`
- 👨‍💼 Admin guruhga real-time yo'naltirish, **Javob berish** / **Yopish** tugmalari
- 💬 Javob to'g'ridan-to'g'ri foydalanuvchiga yetadi
- 📣 **Reklama** — istalgan xabarni forward qilish (flood himoyasi bilan), admin + operatorlar
- 📊 **Excel hisobot** — 3 varaq (Murojaatlar / Foydalanuvchilar / Statistika), faqat adminlar
- 📈 Statistika paneli
- 🎨 Rangli inline tugmalar (primary/success/danger)

## O'rnatish

```bash
pip install -r requirements.txt
cp .env.example .env   # va to'ldiring
python bot.py
```

## Sozlash bo'yicha muhim eslatmalar

1. **Admin guruh:** botni guruhga qo'shing, guruh ID sini oling (masalan @userinfobot orqali) va `ADMIN_GROUP_ID` ga yozing.
2. **Kanallar:** bot majburiy kanallarning har birida **admin** bo'lishi shart, aks holda a'zolikni tekshira olmaydi.
3. **ADMIN_IDS:** o'z Telegram ID raqamingizni yozing.
4. Rangli tugmalar uchun `aiogram >= 3.28.2` kerak (requirements.txt da bor). Eski versiyada tugmalar oddiy ko'rinishda ishlayveradi.

## Struktura

```
bot.py                  — kirish nuqtasi
config.py               — .env sozlamalari
database/models.py      — User, Appeal modellari
database/repo.py        — baza operatsiyalari
middlewares/core.py     — Config, DbSession, Subscription
handlers/start.py       — start, registratsiya, menyu
handlers/feedback.py    — taklif/e'tiroz oqimi
handlers/admin.py       — javob, yopish, Excel, statistika
handlers/broadcast.py   — reklama (forward)
keyboards/              — inline (rangli) va reply klaviaturalar
utils/excel.py          — openpyxl hisobot
states/forms.py         — FSM holatlar
```
