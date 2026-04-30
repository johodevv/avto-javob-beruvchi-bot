cat > main.py << 'PYEOF'
import os
import json
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from aiohttp import web

# ===================== SOZLAMALAR =====================
API_ID = int(os.environ.get("API_ID", "28466899"))
API_HASH = os.environ.get("API_HASH", "2f1948ccca564e8973e8cf9c3204d2e9")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

print(f"DEBUG: API_ID = {API_ID}")
print(f"DEBUG: SESSION_STRING uzunligi = {len(SESSION_STRING)}")

# ===================== MA'LUMOTLAR =====================
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "is_active": False,
        "blacklist": [],
        "stats": {},
        "custom_message": "👋 Assalomu alaykum!\n\nMen Javohirning avto-javob bergichiman 🤖\n\n📩 Xabaringiz unga yetkazildi.\n⏳ U sizga tez orada javob qaytaradi — ozgina sabr qiling, iltimos!\n\n🙏 Rahmat!"
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ===================== PYROGRAM CLIENT =====================
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ===================== STATISTIKA =====================
def update_stats(user_id: str, username: str):
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in data["stats"]:
        data["stats"][user_id] = {"username": username, "count": 0, "dates": {}}
    data["stats"][user_id]["count"] += 1
    data["stats"][user_id]["dates"][today] = data["stats"][user_id]["dates"].get(today, 0) + 1
    save_data(data)

# ===================== AVTO JAVOB =====================
@app.on_message(filters.private & filters.incoming & ~filters.bot)
async def auto_reply(client, message: Message):
    if not data["is_active"]:
        return
    user_id = str(message.from_user.id)
    if user_id in data["blacklist"]:
        return
    user_name = message.from_user.first_name or "Foydalanuvchi"
    username = f"@{message.from_user.username}" if message.from_user.username else "nomalum"
    update_stats(user_id, f"{user_name} ({username})")
    await asyncio.sleep(1)
    await message.reply(data["custom_message"])
    print(f"✅ Javob berildi → {user_name}")

# ===================== BUYRUQLAR =====================
@app.on_message(filters.outgoing & filters.regex(r"^\.on$"))
async def turn_on(client, message: Message):
    data["is_active"] = True
    save_data(data)
    await message.edit("✅ Userbot **YOQILDI!**\nEndi xabarlarga avto-javob boradi.")

@app.on_message(filters.outgoing & filters.regex(r"^\.off$"))
async def turn_off(client, message: Message):
    data["is_active"] = False
    save_data(data)
    await message.edit("🔴 Userbot **O'CHIRILDI!**\nAvto-javob to'xtatildi.")

@app.on_message(filters.outgoing & filters.regex(r"^\.status$"))
async def status(client, message: Message):
    holat = "✅ YONIQ" if data["is_active"] else "🔴 O'CHIQ"
    jami = sum(v["count"] for v in data["stats"].values())
    await message.edit(
        f"📊 **Userbot Holati**\n\n"
        f"▸ Holat: {holat}\n"
        f"▸ Blacklist: {len(data['blacklist'])} ta\n"
        f"▸ Jami javob: {jami} ta\n\n"
        f"**📝 Joriy xabar:**\n{data['custom_message']}"
    )

@app.on_message(filters.outgoing & filters.regex(r"^\.setmsg (.+)"))
async def set_message(client, message: Message):
    new_msg = message.matches[0].group(1)
    data["custom_message"] = new_msg
    save_data(data)
    await message.edit(f"✅ **Xabar yangilandi!**\n\n{new_msg}")

@app.on_message(filters.outgoing & filters.regex(r"^\.block (\d+)$"))
async def block_user(client, message: Message):
    uid = message.matches[0].group(1)
    if uid not in data["blacklist"]:
        data["blacklist"].append(uid)
        save_data(data)
        await message.edit(f"🔕 `{uid}` **blacklistga qo'shildi.**")
    else:
        await message.edit("⚠️ Bu odam allaqachon blacklistda.")

@app.on_message(filters.outgoing & filters.regex(r"^\.unblock (\d+)$"))
async def unblock_user(client, message: Message):
    uid = message.matches[0].group(1)
    if uid in data["blacklist"]:
        data["blacklist"].remove(uid)
        save_data(data)
        await message.edit(f"✅ `{uid}` **blacklistdan chiqarildi.**")
    else:
        await message.edit("⚠️ Bu odam blacklistda emas.")

@app.on_message(filters.outgoing & filters.regex(r"^\.blacklist$"))
async def show_blacklist(client, message: Message):
    if not data["blacklist"]:
        await message.edit("📋 Blacklist bo'sh.")
        return
    text = "🔕 **Blacklist:**\n\n" + "\n".join([f"▸ `{uid}`" for uid in data["blacklist"]])
    await message.edit(text)

@app.on_message(filters.outgoing & filters.regex(r"^\.stats$"))
async def show_stats(client, message: Message):
    if not data["stats"]:
        await message.edit("📊 Hali statistika yo'q.")
        return
    lines = ["📊 **Xabarlar Statistikasi:**\n"]
    sorted_stats = sorted(data["stats"].items(), key=lambda x: x[1]["count"], reverse=True)
    for i, (uid, info) in enumerate(sorted_stats[:10], 1):
        lines.append(f"{i}. {info['username']} — {info['count']} ta xabar")
    total = sum(v["count"] for v in data["stats"].values())
    lines.append(f"\n**Jami: {total} ta xabar**")
    await message.edit("\n".join(lines))

@app.on_message(filters.outgoing & filters.regex(r"^\.help$"))
async def help_cmd(client, message: Message):
    await message.edit(
        "🤖 **Userbot Buyruqlari:**\n\n"
        "▸ `.on` — Yoqish\n"
        "▸ `.off` — O'chirish\n"
        "▸ `.status` — Holat ko'rish\n"
        "▸ `.setmsg <matn>` — Xabarni o'zgartirish\n"
        "▸ `.block <id>` — Bloklash\n"
        "▸ `.unblock <id>` — Blokdan chiqarish\n"
        "▸ `.blacklist` — Bloklangan ro'yxat\n"
        "▸ `.stats` — Statistika\n"
        "▸ `.help` — Shu yordam xabari"
    )

# ===================== HTTP SERVER (Render web service uchun) =====================
async def health(request):
    holat = "YONIQ" if data["is_active"] else "O'CHIQ"
    jami = sum(v["count"] for v in data["stats"].values())
    return web.Response(text=f"Userbot ishlayapti! Holat: {holat} | Jami javob: {jami} ta")

async def start_web():
    server = web.Application()
    server.router.add_get("/", health)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 HTTP server port {port} da ishlamoqda")

# ===================== ISHGA TUSHIRISH =====================
async def main():
    await start_web()
    await app.start()
    me = await app.get_me()
    print(f"✅ Userbot ishga tushdi: {me.first_name} (@{me.username})")
    print(f"📌 Holat: {'YONIQ' if data['is_active'] else 'OCHIQ — .on yozing'}")
    await asyncio.get_event_loop().create_future()

print("🚀 Userbot ishga tushmoqda...")
asyncio.run(main())
PYEOF