import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import User
from telethon.sessions import StringSession

# ===================== SOZLAMALAR =====================
API_ID = int(os.environ.get("API_ID", "28466899"))
API_HASH = os.environ.get("API_HASH", "2f1948ccca564e8973e8cf9c3204d2e9")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# ===================== AVTO JAVOB MATNI =====================
AUTO_JAVOB = """👋 Assalomu alaykum!

Men Javohirning avto-javob bergichiman 🤖

📩 Xabaringiz unga yetkazildi.
⏳ U sizga tez orada javob qaytaradi — ozgina sabr qiling, iltimos!

🙏 Rahmat!"""

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
        "custom_message": AUTO_JAVOB
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ===================== TELEGRAM CLIENT =====================
if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
else:
    client = TelegramClient("userbot_session", API_ID, API_HASH)

# ===================== STATISTIKA =====================
def update_stats(user_id: str, username: str):
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in data["stats"]:
        data["stats"][user_id] = {"username": username, "count": 0, "dates": {}}
    data["stats"][user_id]["count"] += 1
    data["stats"][user_id]["dates"][today] = data["stats"][user_id]["dates"].get(today, 0) + 1
    save_data(data)

# ===================== AVTO JAVOB =====================
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def auto_reply(event):
    if not data["is_active"]:
        return

    sender = await event.get_sender()
    if not isinstance(sender, User) or sender.bot:
        return

    user_id = str(sender.id)

    if user_id in data["blacklist"]:
        return

    user_name = sender.first_name or "Foydalanuvchi"
    update_stats(user_id, f"{user_name} (@{sender.username or 'nomalum'})")

    await asyncio.sleep(1)
    await event.respond(data["custom_message"])
    print(f"✅ Javob berildi → {user_name}")

# ===================== BUYRUQLAR =====================

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.on$"))
async def turn_on(event):
    data["is_active"] = True
    save_data(data)
    await event.edit("✅ Userbot **YOQILDI!**\nEndi xabarlarga avto-javob boradi.")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.off$"))
async def turn_off(event):
    data["is_active"] = False
    save_data(data)
    await event.edit("🔴 Userbot **O'CHIRILDI!**\nAvto-javob to'xtatildi.")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.status$"))
async def status(event):
    holat = "✅ YONIQ" if data["is_active"] else "🔴 O'CHIQ"
    jami = sum(v["count"] for v in data["stats"].values())
    await event.edit(
        f"📊 **Userbot Holati**\n\n"
        f"▸ Holat: {holat}\n"
        f"▸ Blacklist: {len(data['blacklist'])} ta\n"
        f"▸ Jami javob: {jami} ta\n\n"
        f"**📝 Joriy xabar:**\n{data['custom_message']}"
    )

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.setmsg (.+)"))
async def set_message(event):
    new_msg = event.pattern_match.group(1)
    data["custom_message"] = new_msg
    save_data(data)
    await event.edit(f"✅ **Xabar yangilandi!**\n\n{new_msg}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.block (\d+)$"))
async def block_user(event):
    uid = event.pattern_match.group(1)
    if uid not in data["blacklist"]:
        data["blacklist"].append(uid)
        save_data(data)
        await event.edit(f"🔕 `{uid}` **blacklistga qo'shildi.**")
    else:
        await event.edit(f"⚠️ Bu odam allaqachon blacklistda.")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.unblock (\d+)$"))
async def unblock_user(event):
    uid = event.pattern_match.group(1)
    if uid in data["blacklist"]:
        data["blacklist"].remove(uid)
        save_data(data)
        await event.edit(f"✅ `{uid}` **blacklistdan chiqarildi.**")
    else:
        await event.edit(f"⚠️ Bu odam blacklistda emas.")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.blacklist$"))
async def show_blacklist(event):
    if not data["blacklist"]:
        await event.edit("📋 Blacklist bo'sh.")
        return
    text = "🔕 **Blacklist:**\n\n" + "\n".join([f"▸ `{uid}`" for uid in data["blacklist"]])
    await event.edit(text)

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.stats$"))
async def show_stats(event):
    if not data["stats"]:
        await event.edit("📊 Hali statistika yo'q.")
        return
    lines = ["📊 **Xabarlar Statistikasi:**\n"]
    sorted_stats = sorted(data["stats"].items(), key=lambda x: x[1]["count"], reverse=True)
    for i, (uid, info) in enumerate(sorted_stats[:10], 1):
        lines.append(f"{i}. {info['username']} — {info['count']} ta xabar")
    total = sum(v["count"] for v in data["stats"].values())
    lines.append(f"\n**Jami: {total} ta xabar**")
    await event.edit("\n".join(lines))

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.help$"))
async def help_cmd(event):
    await event.edit(
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

# ===================== ISHGA TUSHIRISH =====================
async def main():
    await client.start()
    me = await client.get_me()
    print(f"✅ Userbot ishga tushdi: {me.first_name} (@{me.username})")
    print(f"📌 Holat: {'YONIQ' if data['is_active'] else 'OCHIQ — .on yozing'}")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
