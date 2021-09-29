#stuffexchange_d_bot
#token_tg = '2028244866:AAGgH4EE9p6fSYdi5x6l5nW953f8TE45SpA'
from django.conf import settings
from django.core.management.base import BaseCommand
from ugc.models import Profile, Stuff


import logging
import random

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOICE, TITLE, PHOTO, CONTACT, LOCATION = range(5)

# БОТ - начало
def start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    update.message.reply_text(f'''
        Привет, {user.first_name}! 
        Я помогу тебе обменять что-то ненужное на очень нужное. 
        Чтобы разместить вещь к обмену напиши - “Добавить вещь”. 
        После этого тебе станут доступны вещи других пользователей. 
        Напиши “Найти вещь” и я пришлю тебе фотографии вещей для обмена. 
        Понравилась вещь - пиши “Обменяться”, нет - снова набирай “Найти вещь”. 
        Нажал “обменяться”? - если владельцу вещи понравится что-то из твоих вещей, то я пришлю контакты вам обоим.
        ''',
        )
    reply_keyboard = [['Добавить вещь', 'Найти вещь']]
    # добавляем юзера в ДБ, проверяем есть ли контакт и локация
    is_contact, is_location = add_user_to_db(update.message.chat_id, user)
    if not is_contact:
        update.message.reply_text(
            text=(f'''
                    Привет, {user.first_name}!
                    Напиши, пожалуйста, контакты для связи.
                    '''
                  )
        )
        return CONTACT
    if not is_location:
        update.message.reply_text(
            text='У меня нет твоего местоположения, отправь локацию, пожалуйста.',
        )
        return LOCATION

    update.message.reply_text('Что хочешь?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Что желаете?'
        ),
    )
    return CHOICE

#добавляем юзера в ДБ
def add_user_to_db(chat_id, user):
    profile, _ = Profile.objects.get_or_create(external_id=chat_id)

    logger.info(f'Get profile {profile}')
    profile.username = user.username or ''
    profile.first_name = user.first_name or ''
    profile.last_name = user.last_name or ''

    profile.save()

    logger.info(f'Update_user {profile.external_id}, username '
        f'{profile.username}, contact {profile.contact}')
    logger.info(f'Is user contact: {bool(profile.username or profile.contact)}')
    return profile.username or profile.contact, bool(profile.lat)


#БОТ - добавить вещь
def add_item(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("choice of %s, %s: %s", user.first_name, user.id, update.message.text)
    update.message.reply_text(
        'Ок! Напиши название вещи',
        reply_markup=ReplyKeyboardRemove(),
    )
    return TITLE

#создаем вещь в БД
def create_new_stuff(chat_id, user, title):
    profile = Profile.objects.get(external_id=chat_id)
    stuff = Stuff.objects.create(
        profile=profile,
        description=title,
    )
    return stuff.id

#БОТ - название вещи
def title(update: Update, context: CallbackContext) -> int:
    global _new_stuff_id
    user = update.message.from_user
    stuff_title = update.message.text
    stuff_id = create_new_stuff(update.message.chat_id, user,
                                stuff_title)
    _new_stuff_id = stuff_id
    logger.info("Название вещи of %s: %s", user.first_name, update.message.text)
    update.message.reply_text(f'Спасибо, вещь {stuff_title} добавлена. Загрузи фото.')
    return PHOTO

#пока не работает
def find_item(update: Update, context: CallbackContext) -> int:
    pass
    return CHOICE


#эта функция пока не рабочая, просто скопировала add_item
def want_exchange(update: Update, context: CallbackContext) -> int:
    pass
    return TITLE

#добавляем фото вещи
def add_photo_to_new_stuff(chat_id, photo_url, _new_stuff_id):
    stuff = Stuff.objects.get(id=_new_stuff_id)
    stuff.image_url = photo_url
    stuff.save()
    return stuff.id


#БОТ - добавить фото
def photo(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Добавить вещь', 'Найти вещь']]
    global _new_stuff_id
    user = update.message.from_user
    stuff_photo = update.message.photo[0]
    add_photo_to_new_stuff(update.message.chat_id, stuff_photo.file_id,
                           _new_stuff_id)
    logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
    update.message.reply_text(
        'Фото добавлено, что дальше делаем?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )
    return CHOICE

#добавляем локацию в БД
def location(update: Update, context: CallbackContext) -> int:
    profile = Profile.objects.get(external_id=update.message.chat_id)
    if update.message.location:
        profile.lat = update.message.location.latitude
        profile.lon = update.message.location.longitude
        profile.save()
        reply_keyboard = [['Добавить вещь', 'Найти вещь']]
        update.message.reply_text(
            f'Добавлено местоположение: {profile.lat}, {profile.lon},'
            f'спасибо! Итак, что желаешь?',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True
            )
        )
        logger.info(f'Пользователю {profile.external_id} добавлено '
                    f'местоположение {profile.lat}, {profile.lon}')
    return CHOICE


def stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.username}!')
    return ConversationHandler.END

def unknown(update, context):
    update.message.reply_text(chat_id=update.effective_chat.id,
                             text="Извините, не понял, что вы хотели этим сказать, нажмите /start")


class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        # Create the Updater and pass it your bot's token.
        updater = Updater("2028244866:AAGgH4EE9p6fSYdi5x6l5nW953f8TE45SpA")

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # Add conversation handler with the states CHOICE, TITLE, PHOTO, LOCATION
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                CHOICE: [
                    MessageHandler(Filters.regex('^Добавить вещь$'),
                                   add_item),
                    MessageHandler(Filters.regex('^Найти вещь$'),
                                   find_item),
                    MessageHandler(Filters.regex('^Хочу обменяться$'),
                                   want_exchange),
                    MessageHandler(Filters.text & ~Filters.command,
                                   unknown)
                ],

                TITLE: [MessageHandler(Filters.text & ~Filters.command, title)],
                PHOTO: [MessageHandler(Filters.photo, photo)],
                LOCATION: [MessageHandler(Filters.location, location)],
            },
            fallbacks=[CommandHandler('stop', stop)],
        )

        dispatcher.add_handler(conv_handler)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()