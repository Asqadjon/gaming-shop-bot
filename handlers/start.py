from aiogram import Router, F, html
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from database import add_user, get_users_count
import config

router = Router()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎮 O'yin Valyutalari (UC/Diamond/Gold)")],
        [KeyboardButton(text="💳 Karta Ma'lumotlari"), KeyboardButton(text="📊 Statistikalar (Admin)")]
    ],
    resize_keyboard=True
)

@router.message(CommandStart())
async def start_cmd(message: Message):
    add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer(
        f"Assalomu alaykum, {html.bold(message.from_user.full_name)}!\n\n"
        "🎮 **Rasmiy O'yin Donat va Valyuta Do'koniga xush kelibsiz!**\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=main_menu
    )

@router.message(F.text == "📊 Statistikalar (Admin)")
async def admin_stats(message: Message):
    if message.from_user.id == config.ADMIN_ID:
        count = get_users_count()
        await message.answer(f"📊 **Do'kon statistikasi:**\n\n👥 Foydalanuvchilar soni: <b>{count} ta</b>")
    else:
        await message.answer("❌ Bu bo'lim faqat admin uchun ochiq!")