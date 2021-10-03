from environs import Env

from django.core.management.base import BaseCommand
from ugc.models import Profile, Stuff, Exchange


import logging
import random
import os
import uuid

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)


env = Env()
env.read_env()
TOKEN = env.str('TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOICE, TITLE, PHOTO, CONTACT, LOCATION = range(5)


# БОТ - начало
def start(update: Update, context: CallbackContext) -> int:
    global _want_exchange
    _want_exchange = None
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
    #if not is_contact:
    #    update.message.reply_text(
    #        text=(f'''
    #                Привет, {user.first_name}!
    #                Напиши, пожалуйста, контакты для связи.
    #                '''
    #              )
    #    )
    #    return CONTACT
    #if not is_location:
    #    keyboard_location = [
    #    [KeyboardButton('Отправить локацию 🗺️', request_location=True)],
    #]
    #    update.message.reply_text(
    #        text='У меня нет твоего местоположения, отправь локацию, пожалуйста.',
    #        reply_markup=ReplyKeyboardMarkup(
    #            keyboard_location, one_time_keyboard=True
    #        ),
    #    )
    #    return LOCATION

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
    logger.info(
        f'Is user contact: {bool(profile.username or profile.contact)}')
    return profile.username or profile.contact, bool(profile.lat)


#БОТ - добавить вещь
def add_item(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("choice of %s, %s: %s", user.first_name,
                user.id, update.message.text)
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
    logger.info("Название вещи of %s: %s",
                user.first_name, update.message.text)
    update.message.reply_text(
        f'Спасибо, вещь {stuff_title} добавлена. Загрузи фото.')
    return PHOTO


#БОТ - Обменяться
def want_exchange(update: Update, context: CallbackContext) -> int:
    global _user_id
    global _want_exchange
    global _stuff_descr
    reply_keyboard = [['Добавить вещь', 'Найти вещь', 'Обменяться']]
    find_exchangers = Exchange.objects.filter(
        second_user_id=update.message.chat_id,
        first_stuff_descr__isnull=True)
    if find_exchangers.count() == 0:
        exchange, _ = Exchange.objects.get_or_create(
            first_user_id=update.message.chat_id,
            second_user_id=_user_id,
            second_stuff_descr=_stuff_descr
        )
        exchange.save()
    else:
        for find_exchanger in find_exchangers:
            msg1 = f"УРА!!! Вашу вещь {find_exchanger.second_stuff_descr} хотят обменять на {_stuff_descr}, контакты: {find_exchanger.contact}"
            context.bot.send_message(chat_id=update.message.chat_id, text=msg1)
            msg2 = f"УРА!!! Вашу вещь {_stuff_descr} хотят обменять на {find_exchanger.second_stuff_descr}, контакты: {find_exchanger.contact}"
            context.bot.send_message(chat_id=_user_id, text=msg2)
        find_exchangers.update(first_stuff_descr=_stuff_descr)

    _want_exchange = _user_id

    update.message.reply_text(
        'Информация об обмене сохранена.',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )
    return CHOICE


#добавляем фото вещи
def add_photo_to_new_stuff(chat_id, photo_url, _new_stuff_id):
    stuff = Stuff.objects.get(id=_new_stuff_id)
    stuff.image_url = photo_url
    stuff.save()
    return stuff.id


def photo(update: Update, context: CallbackContext) -> int:
    images_dir = os.path.join(os.getcwd(), 'images')
    os.makedirs(images_dir, exist_ok=True)
    reply_keyboard = [['Добавить вещь', 'Найти вещь']]
    global _new_stuff_id
    user = update.message.from_user
    newFile = update.message.effective_attachment[-1].get_file()
    file_name = f"{str(uuid.uuid4())}.jpg"
    full_path_file = os.path.join(images_dir, file_name)
    newFile.download(full_path_file)
    add_photo_to_new_stuff(update.message.chat_id, os.path.join('images', file_name),
                           _new_stuff_id)
    logger.info("Photo of %s: %s", user.first_name, file_name)
    update.message.reply_text(
        'Фото добавлено, что дальше делаем?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )
    return CHOICE


# БОТ - найти вещь
def find_item(update: Update, context: CallbackContext) -> int:
    global _user_id
    global _stuff_descr
    reply_keyboard = [['Добавить вещь', 'Найти вещь', 'Обменяться']]
    profile = Profile.objects.get(external_id=update.message.chat_id)
    if _want_exchange:
        pk_list = [_want_exchange]
        clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i)
                           for i, pk in enumerate(pk_list)])
        ordering = 'CASE %s END' % clauses
        stuff = list(Stuff.objects.exclude(profile=profile.id).extra(
           select={'ordering': ordering}, order_by=('ordering',)))
    else:
        stuff = list(Stuff.objects.exclude(profile=profile.id))
    random_stuff = random.choice(stuff)
    _user_id = random_stuff.profile.external_id
    _stuff_descr = random_stuff.description
    logger.info(f"Show item: {random_stuff.description}")
    context.bot.send_photo(chat_id=update.message.chat_id,
                           photo=open(random_stuff.image_url, 'rb'))
    update.message.reply_text(
        f'Предлагаю вещь: {random_stuff.description}. Что теперь хочешь?',
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


#БОТ - команда стоп
def stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.first_name}!')
    return ConversationHandler.END


#БОТ - нераспознанная команда
def unknown(update, context):
    reply_keyboard = [['Добавить вещь', 'Найти вещь']]
    update.message.reply_text(
        'Извините, не понял, что вы хотели этим сказать, начнем сначала',
        reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True
        )
    )
    return CHOICE


def error(bot, update, error):
    logger.error('Update "%s" caused error "%s"', update, error)
    return CHOICE


class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        # Create the Updater and pass it your bot's token.
        updater = Updater(TOKEN)

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
                    MessageHandler(Filters.regex('^Обменяться$'),
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
        dispatcher.add_error_handler(error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
