from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import os
from pathlib import Path

# Замени на свой токен
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния
class UserState(StatesGroup):
    choosing_currency = State()
    choosing_game = State()
    in_catalog = State()
    entering_pubg_id = State()  # Для PUBG
    entering_ff_id = State()    # Для Free Fire
    confirming_order = State()

# Данные пользователей
user_data = {}

# Админы (ID)
ADMINS = [6682444381, 6685271675]

# Описание игр и их категории (inline)
games = {
    "pubg": {
        "name": "PUBG Mobile",
        "categories": [
            {"text": "💎 Приобрести UC", "callback": "cat_pubg_uc"}
        ]
    },
    "freefire": {
        "name": "Free Fire",
        "categories": [
            {"text": "💎 Алмазы", "callback": "cat_ff_diamonds"},
            {"text": "🎟️ Ваучеры и пропуски", "callback": "cat_ff_vouchers"}
        ]
    },
    # Остальные игры закомментированы
    "brawl": {
        "name": "Brawl Stars",
        "categories": []
    },
    "clash_clans": {
        "name": "Clash of Clans",
        "categories": []
    },
    "clash_royale": {
        "name": "Clash Royale",
        "categories": []
    },
    "standoff": {
        "name": "Standoff 2",
        "categories": []
    },
    "roblox": {
        "name": "Roblox",
        "categories": []
    }
}

# Клавиатура выбора валюты (reply)
def get_currency_kb():
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="🇷🇺 Рубли"))
    kb.add(KeyboardButton(text="🇺🇦 Гривны"))
    kb.add(KeyboardButton(text="🇰🇿 Тенге"))
    kb.add(KeyboardButton(text="₿ Крипта"))
    kb.add(KeyboardButton(text="🇸🇲 Сумы"))
    kb.add(KeyboardButton(text="🇧🇾 Бел. Рубли"))
    kb.add(KeyboardButton(text="🇰🇬 Киргизский сом"))
    return kb.as_markup(resize_keyboard=True)

# Инлайн-клавиатура выбора игры
def get_game_inline_kb():
    kb = InlineKeyboardBuilder()
    game_list = ["pubg", "freefire", "brawl", "clash_clans", "clash_royale", "standoff", "roblox"]
    game_names = {
        "pubg": "PUBG Mobile",
        "freefire": "Free Fire",
        "brawl": "Brawl Stars",
        "clash_clans": "Clash of Clans",
        "clash_royale": "Clash Royale",
        "standoff": "Standoff 2",
        "roblox": "Roblox"
    }
    
    for game_id in game_list:
        kb.button(text=game_names[game_id], callback_data=f"select_game_{game_id}")
    kb.adjust(3)
    return kb.as_markup()

# Главное меню (reply) — 3 строки
def get_main_menu_kb():
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="🛒 Каталог товаров"))
    kb.row(KeyboardButton(text="🔄 Сменить игру"), KeyboardButton(text="👤 Мой профиль"))
    kb.row(KeyboardButton(text="🔥 О Лавке Марио"), KeyboardButton(text="? Поддержка"))
    return kb.as_markup(resize_keyboard=True)

# Клавиатура категорий (inline)
def get_category_inline_kb(game_id):
    if game_id not in games:
        return None
    if game_id not in ["pubg", "freefire"]:
        return None
    kb = InlineKeyboardBuilder()
    for cat in games[game_id]["categories"]:
        kb.button(text=cat["text"], callback_data=cat["callback"])
    kb.adjust(1)
    return kb.as_markup()

# Клавиатура товаров (с пагинацией)
def get_product_kb(game_id, category=None, page=1):
    items = []
    
    if game_id == "freefire":
        if category == "diamonds":
            items = [
                {"name": "110 Алмазов", "price": 77},
                {"name": "341 Алмаз", "price": 235},
                {"name": "572 Алмаза", "price": 397},
                {"name": "1166 Алмазов", "price": 775},
                {"name": "2398 Алмазов", "price": 1570},
                {"name": "6160 Алмазов", "price": 3790},
            ]
        elif category == "vouchers":
            items = [
                {"name": "Evo Access (30 дней)", "price": 215},
                {"name": "Evo Access (3 дня)", "price": 46},
                {"name": "Evo Access (7 дней)", "price": 75},
                {"name": "Недельный ваучер Лайт", "price": 37},
                {"name": "Ваучер на неделю", "price": 130},
                {"name": "Ваучер на месяц", "price": 575},
            ]
        else:
            items = [
                {"name": "110 Алмазов", "price": 77},
                {"name": "341 Алмаз", "price": 235},
                {"name": "572 Алмаза", "price": 397},
                {"name": "1166 Алмазов", "price": 775},
                {"name": "2398 Алмазов", "price": 1570},
                {"name": "6160 Алмазов", "price": 3790},
            ]
            
    elif game_id == "pubg":
        items = [
            {"name": "60 UC", "price": 75},
            {"name": "300 + 25 UC", "price": 385},
            {"name": "600 + 60 UC", "price": 765},
            {"name": "1500 + 300 UC", "price": 1920},
            {"name": "3000 + 850 UC", "price": 3780},
            {"name": "7000 + 1100 UC", "price": 7700},
        ]
    else:
        items = []

    if not items:
        return None

    per_page = 6
    total_pages = (len(items) + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, len(items))

    kb = InlineKeyboardBuilder()
    for i in range(start_idx, end_idx):
        item = items[i]
        kb.button(
            text=f"{item['name']} • {item['price']} ₽",
            callback_data=f"buy_{game_id}_{i}"
        )

    if total_pages > 1:
        if page > 1:
            kb.button(text="⬅️ Назад", callback_data=f"prev_page_{game_id}_{category or 'default'}_{page}")
        if page < total_pages:
            kb.button(text="➡️ Вперед", callback_data=f"next_page_{game_id}_{category or 'default'}_{page}")

    kb.button(text="🔙 Назад", callback_data="back_to_catalog")
    kb.adjust(2)
    return kb.as_markup()

# Обработчики
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Начнём с простого — выберите удобную для вас валюту.\nПри желании вы сможете изменить её в любой момент 📥", reply_markup=get_currency_kb())
    await state.set_state(UserState.choosing_currency)

@dp.message(UserState.choosing_currency)
async def handle_currency(message: types.Message, state: FSMContext):
    currency = message.text
    user_data[message.from_user.id] = {"currency": currency, "game": None}
    await message.answer("🎯 Выбрана валюта: " + currency)

    await message.answer("Выберите одну из предложенных игр:", reply_markup=get_game_inline_kb())
    await state.set_state(UserState.choosing_game)

@dp.callback_query(F.data.startswith("select_game_"))
async def select_game(callback: types.CallbackQuery, state: FSMContext):
    game_id = callback.data.split("_")[2]
    user_id = callback.from_user.id
    
    if game_id not in ["pubg", "freefire"]:
        await callback.message.answer("🎮 Эта игра будет доступна позже. Пожалуйста, выберите другую игру.")
        return

    user_data[user_id]["game"] = game_id

    await callback.message.delete()

    photo_path = Path(__file__).parent / "pth.jpg"
    if not photo_path.exists():
        await callback.message.answer("Ошибка: файл pth.jpg не найден.")
        return

    await callback.message.answer_photo(
        photo=types.FSInputFile(photo_path),
        caption="Главное меню\nДля взаимодействия с ботом используйте клавиатуру 🖱️",
        reply_markup=get_main_menu_kb()
    )
    await state.clear()

@dp.message(F.text == "🛒 Каталог товаров")
async def catalog_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    game_id = user_data.get(user_id, {}).get("game")
    
    if not game_id:
        await message.answer("Сначала выберите игру.")
        return
    
    if game_id not in ["pubg", "freefire"]:
        await message.answer("🎮 Эта игра будет доступна позже. Пожалуйста, выберите другую игру.")
        return

    category_kb = get_category_inline_kb(game_id)
    if category_kb is None:
        await message.answer("🎮 Эта игра будет доступна позже. Пожалуйста, выберите другую игру.")
        return
        
    await message.answer("💡 Пожалуйста, выберите категорию товара, которую хотели бы приобрести:", reply_markup=category_kb)
    await state.set_state(UserState.in_catalog)

@dp.message(F.text == "🔥 О Лавке Марио")
async def about_handler(message: types.Message):
    await message.answer("🔥 О Лавке Марио\n\nЛавка Марио — это ваш надёжный партнёр в мире игровых покупок! Мы предлагаем лучшие цены, быструю доставку и безопасные платежи. \n\n✅ Гарантия защиты аккаунтов\n✅ Регулярные скидки и акции\n✅ Поддержка 24/7")

@dp.message(F.text == "? Поддержка")
async def support_handler(message: types.Message):
    await message.answer("❓ Поддержка\n\nНапишите нам в чат, если у вас возникли вопросы или проблемы. Мы быстро ответим!")

@dp.message(F.text == "🎮 Игры Марио")
async def games_handler(message: types.Message, state: FSMContext):
    await message.answer("Выберите игру:", reply_markup=get_game_inline_kb())
    await state.set_state(UserState.choosing_game)

@dp.message(F.text == "🔄 Сменить игру")
async def change_game_handler(message: types.Message, state: FSMContext):
    await message.answer("Выберите новую игру:", reply_markup=get_game_inline_kb())
    await state.set_state(UserState.choosing_game)

@dp.message(F.text == "👤 Мой профиль")
async def profile_handler(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id, {})
    currency = data.get("currency", "Не выбрана")
    game_id = data.get("game", "Не выбрана")
    
    game_names = {
        "pubg": "PUBG Mobile",
        "freefire": "Free Fire",
        "brawl": "Brawl Stars",
        "clash_clans": "Clash of Clans",
        "clash_royale": "Clash Royale",
        "standoff": "Standoff 2",
        "roblox": "Roblox"
    }
    game_name = game_names.get(game_id, game_id) if game_id != "Не выбрана" else "Не выбрана"
    
    await message.answer(f"👤 Ваш профиль\n\n🎮 Игра: {game_name}\n💰 Валюта: {currency}")

@dp.callback_query(F.data.startswith("cat_"))
async def handle_category(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    game_id = user_data.get(user_id, {}).get("game")
    
    if not game_id or game_id not in ["pubg", "freefire"]:
        await callback.message.answer("🎮 Эта игра будет доступна позже. Пожалуйста, выберите другую игру.")
        return

    category = None
    if callback.data == "cat_ff_diamonds":
        category = "diamonds"
    elif callback.data == "cat_ff_vouchers":
        category = "vouchers"
    elif callback.data == "cat_pubg_uc":
        category = "uc"
    
    await state.update_data(current_category=category)
    
    product_kb = get_product_kb(game_id, category)
    if product_kb is None:
        await callback.message.edit_text("🎮 Эта игра будет доступна позже. Пожалуйста, выберите другую игру.")
        return
        
    await callback.message.edit_text("Выберите, что желаете купить:", reply_markup=product_kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_item(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    game_id = data[1]
    item_idx = int(data[2])
    
    items = []
    if game_id == "freefire":
        items = [
            {"name": "110 Алмазов", "price": 77},
            {"name": "341 Алмаз", "price": 235},
            {"name": "572 Алмаза", "price": 397},
            {"name": "1166 Алмазов", "price": 775},
            {"name": "2398 Алмазов", "price": 1570},
            {"name": "6160 Алмазов", "price": 3790},
            {"name": "Evo Access (30 дней)", "price": 215},
            {"name": "Evo Access (3 дня)", "price": 46},
            {"name": "Evo Access (7 дней)", "price": 75},
            {"name": "Недельный ваучер Лайт", "price": 37},
            {"name": "Ваучер на неделю", "price": 130},
            {"name": "Ваучер на месяц", "price": 575},
        ]
    elif game_id == "pubg":
        items = [
            {"name": "60 UC", "price": 75},
            {"name": "300 + 25 UC", "price": 385},
            {"name": "600 + 60 UC", "price": 765},
            {"name": "1500 + 300 UC", "price": 1920},
            {"name": "3000 + 850 UC", "price": 3780},
            {"name": "7000 + 1100 UC", "price": 7700},
        ]

    item = items[item_idx]
    cancel_kb = InlineKeyboardBuilder()
    cancel_kb.button(text="Отмена", callback_data="cancel_order")

    await callback.message.edit_text(
        f"Вы выбрали: {item['name']}\n\n"
        f"Стоимость: {item['price']} ₽\n\n"
        f"Пожалуйста, введите ваш {games[game_id]['name']} ID (например: 12345678):",
        reply_markup=cancel_kb.as_markup()
    )
    await state.update_data(item=item, game_id=game_id)
    if game_id == "pubg":
        await state.set_state(UserState.entering_pubg_id)
    else:
        await state.set_state(UserState.entering_ff_id)

@dp.message(UserState.entering_pubg_id)
async def handle_pubg_id(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await message.answer("Заказ отменён.")
        await state.clear()
        return

    pubg_id = message.text.strip()
    if not pubg_id.isdigit():
        await message.answer("❌ Пожалуйста, введите корректный PUBG ID (цифры).")
        return

    data = await state.get_data()
    item = data["item"]
    game_id = data["game_id"]
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет ника"

    order_msg = (
        f"📦 Новый заказ\n\n"
        f"🎮 Игра: {games[game_id]['name']}\n"
        f"🛒 Товар: {item['name']}\n"
        f"💰 Стоимость: {item['price']} ₽\n"
        f"🆔 PUBG ID: {pubg_id}\n\n"
        f"💳 Реквизиты для оплаты:\n"
        f"2200701994814470 (Т БАНК)\n"
        f"💭 Комментарий к платежу (обязателен): {username}\n\n"
        f"После оплаты нажмите кнопку '✅ Подтвердить оплату'."
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить оплату", callback_data=f"confirm_payment_{message.from_user.id}_{item['name']}_{item['price']}_{pubg_id}")
    kb.adjust(1)

    await message.answer(order_msg, reply_markup=kb.as_markup())
    await state.set_state(UserState.confirming_order)

@dp.message(UserState.entering_ff_id)
async def handle_ff_id(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await message.answer("Заказ отменён.")
        await state.clear()
        return

    ff_id = message.text.strip()
    if not ff_id.isdigit():
        await message.answer("❌ Пожалуйста, введите корректный FreeFire ID (цифры).")
        return

    data = await state.get_data()
    item = data["item"]
    game_id = data["game_id"]
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет ника"

    order_msg = (
        f"📦 Новый заказ\n\n"
        f"🎮 Игра: {games[game_id]['name']}\n"
        f"🛒 Товар: {item['name']}\n"
        f"💰 Стоимость: {item['price']} ₽\n"
        f"🆔 FreeFire ID: {ff_id}\n\n"
        f"💳 Реквизиты для оплаты:\n"
        f"2200701994814470 (Т БАНК)\n"
        f"💭 Комментарий к платежу (обязателен): {username}\n\n"
        f"После оплаты нажмите кнопку '✅ Подтвердить оплату'."
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить оплату", callback_data=f"confirm_payment_{message.from_user.id}_{item['name']}_{item['price']}_{ff_id}")
    kb.adjust(1)

    await message.answer(order_msg, reply_markup=kb.as_markup())
    await state.set_state(UserState.confirming_order)

@dp.callback_query(F.data.startswith("confirm_payment_"))
async def confirm_payment(callback: types.CallbackQuery):
    data = callback.data.split("_")
    user_id = int(data[2])
    item_name = data[3]
    price = int(data[4])
    player_id = data[5]

    # Определяем тип ID по наличию в данных
    game_id = "pubg" if "pubg" in item_name.lower() or "uc" in item_name.lower() else "freefire"
    id_type = "PUBG ID" if game_id == "pubg" else "FreeFire ID"

    # Получаем пользователя
    try:
        user = await bot.get_chat(user_id)
        username = f"@{user.username}" if user.username else "Нет ника"
        user_link = f"[{user.full_name}](tg://user?id={user_id})" if not user.username else f"@{user.username}"
    except:
        username = "Неизвестно"
        user_link = f"ID: {user_id}"

    admin_message = (
        f"📩 Новый заказ\n\n"
        f"🎮 Игра: {games[game_id]['name']}\n"
        f"🛒 Товар: {item_name}\n"
        f"💰 Стоимость: {price} ₽\n"
        f"🆔 {id_type}: {player_id}\n"
        f"👤 Покупатель: {user_link} ({username})"
    )

    # Отправляем уведомление обоим админам
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки админу {admin_id}: {e}")

    # Сообщение пользователю
    await callback.message.edit_text(
        f"✅ Оплата подтверждена!\n\n"
        f"Товар: {item_name}\n"
        f"Стоимость: {price} ₽\n"
        f"{id_type}: {player_id}\n\n"
        f"Ожидайте доставку!"
    )

@dp.callback_query(F.data.startswith("prev_page_"))
async def prev_page(callback: types.CallbackQuery):
    data = callback.data.split("_")
    game_id = data[1]
    category = data[2] if data[2] != 'default' else None
    page = int(data[3]) - 1
    product_kb = get_product_kb(game_id, category, page)
    if product_kb:
        await callback.message.edit_reply_markup(reply_markup=product_kb)

@dp.callback_query(F.data.startswith("next_page_"))
async def next_page(callback: types.CallbackQuery):
    data = callback.data.split("_")
    game_id = data[1]
    category = data[2] if data[2] != 'default' else None
    page = int(data[3]) + 1
    product_kb = get_product_kb(game_id, category, page)
    if product_kb:
        await callback.message.edit_reply_markup(reply_markup=product_kb)

@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    game_id = user_data.get(user_id, {}).get("game")
    
    if not game_id or game_id not in ["pubg", "freefire"]:
        await callback.message.answer("🎮 Эта игра будет доступна позже. Пожалуйста, выберите другую игру.")
        return
        
    category_kb = get_category_inline_kb(game_id)
    if category_kb is None:
        await callback.message.edit_text("🎮 Эта игра будет доступна позже. Пожалуйста, выберите другую игру.")
        return
        
    await callback.message.edit_text("💡 Пожалуйста, выберите категорию товара, которую хотели бы приобрести:", reply_markup=category_kb)

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    game_id = user_data.get(user_id, {}).get("game")
    
    if not game_id or game_id not in ["pubg", "freefire"]:
        await callback.message.answer("🎮 Эта игра будет доступна позже. Пожалуйста, выберите другую игру.")
        return
        
    await callback.message.edit_text("Главное меню", reply_markup=get_main_menu_kb())

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())