from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
import config
from loader import bot
from database import add_order, update_order_status

router = Router()

@router.message(F.text == "💳 Karta Ma'lumotlari")
async def card_info(message: Message):
    text = (
        f"💳 <b>To'lov uchun karta ma'lumotlari:</b>\n\n"
        f"📌 Karta raqami: <code>{config.CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{config.CARD_HOLDER}</b>"
    )
    await message.answer(text)

@router.callback_query(F.data == "pay_method_card")
async def pay_method_card(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    game_code = user_data.get("game_code")
    pkg_name = user_data.get("package_name")
    game_id = user_data.get("game_id")
    
    pkg_details = config.PRICES[game_code][pkg_name]
    price = f"{pkg_details['price_sum']:,} so'm"
    
    order_id = add_order(call.from_user.id, game_code, pkg_name, game_id, price, "Karta")
    await state.update_data(current_order_id=order_id)
    
    text = (
        f"💳 <b>To'lovni amalga oshiring:</b>\n\n"
        f"📌 Karta raqami: <code>{config.CARD_NUMBER}</code>\n"
        f"👤 Egasi: <b>{config.CARD_HOLDER}</b>\n"
        f"💰 Summa: <b>{price}</b>\n\n"
        f"<i>To'lovni amalga oshirgach, chek rasmini shu chatga yuboring!</i>"
    )
    await call.message.edit_text(text)
    await call.answer()

@router.callback_query(F.data == "pay_method_stars")
async def pay_method_stars(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    game_code = user_data.get("game_code")
    pkg_name = user_data.get("package_name")
    game_id = user_data.get("game_id")
    
    pkg_details = config.PRICES[game_code][pkg_name]
    stars_qty = pkg_details['stars']
    
    order_id = add_order(call.from_user.id, game_code, pkg_name, game_id, f"{stars_qty} Stars", "Stars")
    prices = [LabeledPrice(label=f"{pkg_name} donati", amount=stars_qty)]
    
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f"{game_code.upper()} - {pkg_name}",
        description=f"O'yin ID: {game_id}",
        payload=f"order_{order_id}",
        currency="XTR",
        prices=prices
    )
    await call.answer()

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payload = message.successful_payment.invoice_payload
    order_id = payload.split("_")[1]
    
    update_order_status(int(order_id), "paid")
    await message.answer("🎉 <b>To'lovingiz Telegram Stars orqali qabul qilindi!</b>\nAdmin tez orada xizmatni yetkazadi.")
    
    if config.ADMIN_ID != 0:
        admin_markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{order_id}_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{order_id}_{message.from_user.id}")
            ]
        ])
        admin_text = (
            f"⭐ <b>STARS ORQALI YANGI BUYURTMA! (#ID_{order_id})</b>\n\n"
            f"👤 Mijoz: {message.from_user.full_name} (@{message.from_user.username or 'yoq'})\n"
            f"⭐ To'lov: {message.successful_payment.total_amount} Stars"
        )
        await bot.send_message(chat_id=config.ADMIN_ID, text=admin_text, reply_markup=admin_markup)

@router.message(F.photo)
async def get_receipt(message: Message, state: FSMContext):
    user_data = await state.get_data()
    order_id = user_data.get("current_order_id", "Noma'lum")
    
    await message.answer("✅ Chek qabul qilindi! Admin ko'rib chiqmoqda.")
    
    if config.ADMIN_ID != 0:
        admin_markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{order_id}_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{order_id}_{message.from_user.id}")
            ]
        ])
        caption = (
            f"📥 <b>YANGI CHEK VA BUYURTMA! (#ID_{order_id})</b>\n\n"
            f"👤 Mijoz: {message.from_user.full_name} (@{message.from_user.username or 'yoq'})\n"
            f"🆔 Telegram ID: <code>{message.from_user.id}</code>"
        )
        await bot.send_photo(chat_id=config.ADMIN_ID, photo=message.photo[-1].file_id, caption=caption, reply_markup=admin_markup)
    
    await state.clear()

@router.callback_query(F.data.startswith("approve_"))
async def approve_order(call: CallbackQuery):
    _, order_id, user_id = call.data.split("_")
    update_order_status(int(order_id), "approved")
    
    await bot.send_message(
        chat_id=int(user_id),
        text=f"✅ <b>Buyurtmangiz (#ID_{order_id}) muvaffaqiyatli bajarildi!</b>\nO'yiningizga hisob to'ldirildi. Rahmat!"
    )
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"✅ Buyurtma #ID_{order_id} tasdiqlandi.")
    await call.answer()

@router.callback_query(F.data.startswith("reject_"))
async def reject_order(call: CallbackQuery):
    _, order_id, user_id = call.data.split("_")
    update_order_status(int(order_id), "rejected")
    
    await bot.send_message(
        chat_id=int(user_id),
        text=f"❌ <b>Buyurtmangiz (#ID_{order_id}) rad etildi.</b>\nIltimos, qayta chek yuboring yoki adminga murojaat qiling."
    )
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"❌ Buyurtma #ID_{order_id} rad etildi.")
    await call.answer()