import asyncio
import json
import requests
from os import getenv
from aiogram.types import Message
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.filters import Command
from html import escape
from config import TOKEN, ALLOWED_USERS, BASE_URL, USERNAME, PASSWORD

dp = Dispatcher()

#######################################################################################
################################### TASKS #############################################
#######################################################################################
# fix diag
# GLOBAL (MOVE FROM HTML TO MARKDOWN2)
# Fix shown time
# Add <>spoiler<> to additional info 
# Add reminder
################################---------------MAIN------------########################################
board_id = ''

# === AUTHENTICATION ===
def authenticate(base_url: str, username: str, password: str) -> dict:
    response = requests.post(
        base_url + 'api/access-tokens',
        data={'emailOrUsername': username, 'password': password}
    )
    response.raise_for_status()
    token = response.json()['item']
    headers = {'Authorization': f'Bearer {token}'}
    return headers

# === PROJECTS ===
def get_projects(base_url: str, headers: dict) -> list:
    response = requests.get(base_url + 'api/projects/', headers=headers)
    response.raise_for_status()
    return response.json()['items']


def show_projects(projects: list):
    output = "\n=== PROJECTS LIST ===\n"
    for i, project in enumerate(projects):
        output += f"[{i}] {project['name']}\n"
        output += f"Description: {project['description']}\n"
        output += "---------\n"
    return output

# === BOARDS ===
def get_boards(base_url: str, headers: dict, project_id: str) -> list:
    response = requests.get(base_url + 'api/projects/', headers=headers)
    response.raise_for_status()
    data = response.json()

    boards = [
        board for board in data['included']['boards']
        if board['projectId'] == project_id
    ]
    return boards


def show_boards(boards: list) -> str:
    output = "\n=== BOARDS LIST ===\n"
    for i, board in enumerate(boards):
        output += f"[{i}] {board['name']} \n"
    return output

def get_boards_info(base_url: str, headers: dict, board_id: str):
    response = requests.get(base_url + f'api/boards/{board_id}', headers=headers)
    data = response.json()
    
    # === INFO ===
    output = ''
    lists = data["included"]["lists"]
    cards = data["included"]["cards"]
    labels = data["included"]["labels"]
    card_labels = data["included"]["cardLabels"]
    

    for label in labels:
        label['cardLabels'] = []
        for cardlabel in card_labels:
            if cardlabel["labelId"] == label["id"]:
                label['cardLabels'].append(cardlabel["cardId"])

        for card in cards:
            if 'cardLabels' not in card.keys():
                card['cardLabels'] = []
            if card['id'] in label['cardLabels']:
                card['cardLabels'].append(label)

    for list in lists:
        list["cards"] = []
        for card in cards:
            if card["listId"] == list["id"]:
                list["cards"].append(card)  

    ##### create new func??? 

    colors = {
        'berry-red':'🔴',
        'pumpkin-orange':'🟡',
        'lagoon-blue':'🔵',
        'pink-tulip':'👚',
        'light-mud':'📦',
        'orange-peel':'🟠',
        'bright-moss':'🟢',
        'antique-blue':'🔵',
        'dark-granite':'📁',
        'turquoise-sea':'🔵',
        }
    
    for list in lists:
        
        if list['type'] == 'active':                        # NEED FIX(1)
            #if list['color'] != None:                      # NEED FIX(1)
            #    output += f'{colors[list['color']]} '      # NEED FIX(1)
            output += f"🗒 List: <b>{list['name']}</b>\n\n" # NEED FIX(1)
            for card in list['cards']:
                card_add_info = {
                    'labels':'',
                    'dueDate': '',
                    'description': '',
                    'color':''
                }
                if card['cardLabels'] != []:
                    for label in card['cardLabels']:
                        card_add_info['labels'] += f'📌 {label['name']}\n'
                if card['description'] != None: card_add_info['description'] = f'\n📝 {card['description']}\n\n'
                if card['dueDate'] != None: card_add_info['dueDate'] = f' (⏰ {card['dueDate']})'
                if list['color'] != None: card_add_info['color'] = f'{colors[list['color']]}' # NEED FIX(1)
                output += f"{card_add_info['color']} Card: <i><b>{card['name']}</b></i>{card_add_info['dueDate']}\n{escape(card_add_info['description'], quote=True)}{card_add_info['labels']}<a href='{BASE_URL}cards/{card['id']}'>🔗Link</a>\n\n"
                 
    return output

headers = authenticate(BASE_URL, USERNAME, PASSWORD)#

# +++ KEYBOARD +++

keyboard_project = ReplyKeyboardMarkup(#
    keyboard=[
        [KeyboardButton(text="📁Select project")]
    ],
    resize_keyboard=True
)

keyboard_board = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏄‍♀️Select board")]
    ],
    resize_keyboard=True
)

def check(user_id):
    if user_id in ALLOWED_USERS:
        return True
    return False

# Command handler
@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    await message.answer("Hello! I'm bot created to manage your Planka. Select next step", reply_markup=keyboard_project)
    if not check(str(message.from_user.id)): 
        return await message.reply("You're not allowed access to the bot") 

@dp.message(F.text == "📁Select project")
async def select_project(message: Message):
    projects = get_projects(BASE_URL, headers)
    projects_show = show_projects(projects=projects)
    project_dict = dict()
    buttons = list()

    for key in projects:
        project_dict[key['name']] = key['id']
        buttons.append([KeyboardButton(text=f'project: {key['name']} ({key['id']})')])

    keyboard_project_option = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.reply(str(projects_show), reply_markup = keyboard_project_option)

@dp.message(F.text.startswith("project:"))
async def show_info(message: Message):
    #_, key = message.text.split(":", 1)                            #NEED FIX(2) 
    #_, project_id = key.replace("(","").replace(")","").split()    #NEED FIX(2) 
    r_message = message.text[::-1].split('(')[0].split(')')[-1]     #NEED FIX(2) 
    project_id = r_message[::-1]                                    #NEED FIX(2) 

    boards = get_boards(BASE_URL, headers, project_id)

    buttons = list()
    for key in boards:
        buttons.append([KeyboardButton(text=f'board: {key['name']} ({key['id']})')])

    keyboard_boards_option = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

    await message.answer(f'🏄‍♀️Выберите доску', reply_markup=keyboard_boards_option)

@dp.message(F.text.startswith("board:"))
async def show_board_tasks(message: Message):
    global board_id_global
    #_, key = message.text.split(":", 1)                            #NEED FIX(2) 
    #_, board_id = key.replace("(","").replace(")","").split()      #NEED FIX(2) 
    r_message = message.text[::-1].split('(')[0].split(')')[-1]     #NEED FIX(2) 
    board_id = r_message[::-1]                                      #NEED FIX(2) 
    
    board_id_global = board_id

    await message.answer(get_boards_info(BASE_URL, headers, board_id_global), parse_mode="HTML", disable_web_page_preview=True)


@dp.message()
async def test(message: Message) -> None:
    await message.send_copy(chat_id=message.chat.id)

async def main() -> None:
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())