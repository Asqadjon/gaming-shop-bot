from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import config

router = Router()

class OrderState(StatesGroup):
    waiting_for_game_id = State()

games_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔥 PUBG Mobile (UC)", callback_data="game_pubg")],
        [InlineKeyboardButton(text="💎 Mobile Legends (Diamond)", callback_data="game_mlbb")],
        [InlineKeyboardButton(text="⚡ Standoff 2 (Gold)", callback_data="game_standoff")],
        [InlineKeyboardButton(text="🎮 Steam Hisob To'ldirish ($)", callback_data="game_steam")],
        [InlineKeyboardButton(text="🔥 Free Fire (Diamond)", callback_data="game_freefire")],
        [InlineKeyboardButton(text="🤖 Roblox (Robux)", callback_data="game_roblox")],
        [InlineKeyboardButton(text="⭐ Telegram Stars (Sotuv)", callback_data="game_stars")],
        [InlineKeyboardButton(text="🚀 Telegram Premium", callback_data="game_premium")]
    ]
)

@router.message(F.text == "🎮 O'yin Valyutalari (UC/Diamond/Gold)")
async def choose_game(message: Message):
    await message.answer(
        "🎮 **Qaysi xizmat yoki mahsulotni sotib olmoqchisiz?**\n\nQuyidagilardan birini tanlang:",
        reply_markup=games_keyboard
    )

@router.callback_query(F.data.startswith("game_"))
async def game_selected(call: CallbackQuery, state: FSMContext):
    game_code = call.data.split("_")[1]
    await state.update_data(game_code=game_code)
    
    packages = config.PRICES.get(game_code, {})
    buttons = []
    
    for pkg_name, details in packages.items():
        price_str = f"{details['price_sum']:,} so'm"
        buttons.append([InlineKeyboardButton(text=f"{pkg_name} — {price_str}", callback_data=f"pkg_{pkg_name}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_games")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("📦 **Kerakli paketni tanlang:**", reply_markup=markup)
    await call.answer()

@router.callback_query(F.data.startswith("pkg_"))
async def package_selected(call: CallbackQuery, state: FSMContext):
    pkg_name = call.data.split("pkg_")[1]
    await state.update_data(package_name=pkg_name)
    await state.set_state(OrderState.waiting_for_game_id)
    
    user_data = await state.get_data()
    game_code = user_data.get("game_code")
    
    if game_code in ["stars", "premium"]:
        prompt_text = "✍️ Iltimos, Telegram **username (@username)** yoki profil havolangizni yuboring:"
    elif game_code == "steam":
        prompt_text = "✍️ Iltimos, **Steam Login (Login va ID)** raqamingizni yuboring:"
    else:
        prompt_text = "✍️ Iltimos, o'yin ichidagi **ID raqamingizni** yuboring:"
    
    await call.message.edit_text(f"✅ Tanlandi: <b>{pkg_name}</b>\n\n{prompt_text}")
    await call.answer()

@router.message(OrderState.waiting_for_game_id)
async def process_game_id(message: Message, state: FSMContext):
    game_id = message.text
    await state.update_data(game_id=game_id)
    
    user_data = await state.get_data()
    game_code = user_data.get("game_code")
    pkg_name = user_data.get("package_name")
    
    pkg_details = config.PRICES[game_code][pkg_name]
    
    payment_methods = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💳 Karta orqali to'lov ({pkg_details['price_sum']:,} so'm)", 
                callback_data="pay_method_card"
            )]
        ]
    )
    
    await message.answer(
        f"🛒 **Buyurtma Tafsilotlari:**\n\n"
        f"📦 Paket: <b>{pkg_name}</b>\n"
        f"🆔 Qabul qiluvchi ID / Login: <code>{game_id}</code>\n"
        f"💰 Narxi: <b>{pkg_details['price_sum']:,} so'm</b>\n\n"
        f"👇 To'lov qilish uchun bosing:",
        reply_markup=payment_methods
    )

@router.callback_query(F.data == "back_to_games")
async def back_to_games(call: CallbackQuery):
    await call.message.edit_text("🎮 **Qaysi xizmat yoki mahsulotni sotib olmoqchisiz?**", reply_markup=games_keyboard)
    await call.answer()