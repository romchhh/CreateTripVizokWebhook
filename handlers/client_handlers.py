from main import bot, dp, scheduler

from config import *
from ulits.filters import *
from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from keyboards.client_keyboards import get_start_keyboard, language_keyboard, get_cancel_keyboard
from keyboards.admin_keyboards import get_admin_keyboard
from ulits.translate import translate, check_user_language
from database.client_db import *
import asyncio
from data.texts import *
from ulits.client_functions import my_profile, start_message, get_trip_text, get_driver_full_info
from ulits.client_states import PhoneState, SearchUser
from ulits.cron_functions import send_reviews_to_users
from ulits.webhook_checker import start_webhook_checker


async def scheduler_jobs():
    scheduler.add_job(send_reviews_to_users, "cron", hour=20, minute=0, timezone='Europe/Kiev')


async def on_startup(dp):
    me = await bot.get_me()
    await scheduler_jobs()
    start_webhook_checker()
    print(f'Bot: @{me.username} запущений!')


async def on_shutdown(dp):
    me = await bot.get_me()
    print(f'Bot: @{me.username} зупинений!')


@dp.message_handler(IsPrivate(), commands=["start"], state='*') 
async def start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name if message.from_user.first_name else "Юзернейм відсутній"
    
    ref_code = message.get_args()
    
    print(ref_code)
    
    if not check_user(user_id):
        if ref_code:
            update_referral_clicks(ref_code)
    
    add_user(user_id, user_name, user_first_name)
    
    keyboard = get_admin_keyboard(user_id) if user_id in administrators else get_start_keyboard(user_id)

    user_language_code = check_user_language(user_id)
    greeting_message = greeting_text[user_language_code].format(user_name)
    photo_path = 'data/hello.jpg'
    
    if not check_phone_number(user_id):
        with open(photo_path, 'rb') as photo:
            await message.answer_photo(photo=photo, caption=greeting_message)
        await asyncio.sleep(0.5)
        
        share_contact_button = KeyboardButton(share_phone_text[user_language_code], request_contact=True)
        share_contact_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(share_contact_button)
        await message.answer(phone_auth_text[user_language_code], parse_mode="html", reply_markup=share_contact_keyboard)
        await PhoneState.waiting_for_phone.set()
    else:
        with open(photo_path, 'rb') as photo:
            await message.answer_photo(photo=photo, caption=greeting_message, reply_markup=keyboard)


@dp.message_handler(state=PhoneState.waiting_for_phone, content_types=['contact', 'text'])
async def process_phone_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_language_code = check_user_language(user_id)
    
    if message.content_type == 'contact' and message.contact:
        phone_number = message.contact.phone_number
    else:
        phone_number = message.text.strip()
        if len(phone_number) < 10 or len(phone_number) > 20:
            await message.answer(invalid_phone_text[user_language_code])
            return
            
    formatted_phone_number = f"+{phone_number.lstrip('+')}"
    update_user_phone(user_id, formatted_phone_number)
    await state.finish()
    await message.answer(phone_saved_text[user_language_code], reply_markup=ReplyKeyboardRemove())
    
    greeting_message = greeting_text[user_language_code].format(message.from_user.username)
    await message.answer(greeting_message, parse_mode="HTML", reply_markup=language_keyboard())
        
       
@dp.message_handler(lambda message: message.text.lower() in map(str.lower, about_us_text.values()), state='*')
async def about_us(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
        
    user_id = message.from_user.id
    user_language_code = check_user_language(user_id)
    bot_username = (await bot.get_me()).username
    
    about_text = about_us_full_text[user_language_code]
    switch_text = join_bot_text[user_language_code].format(f"https://t.me/{bot_username}?start")

    share_button = InlineKeyboardButton(
        share_button_text[user_language_code],
        switch_inline_query=switch_text
    )

    support_button = InlineKeyboardButton(
        support_button_text[user_language_code],
        url="https://t.me/Pavlo_Gromada"
    )
    
    vizok_button = InlineKeyboardButton(
        vizok_info_button_text[user_language_code],
        url="http://vizok.info/"
    )

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(share_button, support_button, vizok_button)

    await message.answer(about_text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=keyboard)
    
    

@dp.message_handler(lambda message: message.text.lower() in map(str.lower, cancel_texts.values()))
async def cancel_creation(message: Message, state: FSMContext):
    await start_message(message)
    await state.finish()
    

@dp.message_handler(lambda message: message.text.lower() in map(str.lower, search_user_text.values()), state='*')
async def search_user(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    user_id = message.from_user.id
    user_language_code = check_user_language(user_id)
    
    await message.answer(enter_search_query_text[user_language_code], reply_markup=get_cancel_keyboard(user_id))
    await SearchUser.waiting_for_user.set()

@dp.message_handler(state=SearchUser.waiting_for_user)
async def process_search_query(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_language_code = check_user_language(user_id)
    
    if message.text in cancel_texts.values() or message.text == "/start":
        await message.answer(cancel_action_text[user_language_code], reply_markup=get_start_keyboard(user_id))
        await state.finish()
        return
    
    user_input = message.text.strip()
    
        # Якщо введено номер телефону
    if user_input.replace("+", "").isdigit():
        # Видаляємо "+" якщо він є і додаємо для пошуку обидва варіанти
        clean_number = user_input.replace("+", "")
        found_user = find_user_by_username_or_phone(clean_number) or find_user_by_username_or_phone("+" + clean_number)
    else:
        found_user = find_user_by_username_or_phone(user_input)
    
    user_name = find_username_by_id(found_user)
    
    if found_user:
        await message.answer(user_found_text[user_language_code], parse_mode="HTML", reply_markup=get_start_keyboard(user_id))
        description, photo = get_driver_full_info(found_user)
        
        markup = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton(view_reviews_button_text[user_language_code], callback_data=f"view_profilereviews_{found_user}_1"),
            InlineKeyboardButton(contact_user_button_text[user_language_code], url=f"https://t.me/{user_name}")
        )

        if photo:
            with open(photo, "rb") as user_photo:
                await message.answer_photo(
                    photo=user_photo,
                    caption=description,
                    parse_mode="HTML",
                    reply_markup=markup
                )
        else:
            await message.answer(
                description,
                parse_mode="HTML",
                reply_markup=markup
            )
    else:
        await message.answer(user_not_found_text[user_language_code], reply_markup=get_start_keyboard(user_id))
    await state.finish()

    