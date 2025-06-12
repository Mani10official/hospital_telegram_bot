import telebot
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.util import antiflood
import logging
import random
import time
import DQL
import DML
import config
import jdatetime


API_TOKEN = config.API_TOKEN
bot = telebot.TeleBot(API_TOKEN)
hideboard = ReplyKeyboardRemove()
channel_cid = config.channel_cid
admins = config.admins


user_step = dict()
user_data = dict()
user_appointment = dict()
user_rate = dict()
user_resignup = dict()
spam_data = dict() 
KnownUsers = []
spam_users = dict()  
lower_spam_limit = 4
upper_spam_limit = 8
spam_score_limit = 3


commands = {
    'start'                 :       'استارت ربات',
    'help'                  :       'منوی کمک',
    'departments'           :       'لیست دپارتمان ها',
    'appointment'           :       'گرفتن نوبت',
    'doctors_list'          :       'لیست پزشکان',
    'tracking_appointment'  :       'پیگیری نوبت',
    'rate'                  :       'امتیاز به پزشکان',
    'guide'                 :       'راهنمای استفاده',
    'common_questions'      :       'سوالات متداول',
    'comments'              :       'نظر دادن',
    'contact_us'            :       'ارتباط با ما',
    'about_us'              :       'درباره ما',
    'invite_link'           :       'لینک دعوت',
    'sign_up'               :       'ثبت نام',
}

admins_commands = {
    'edit_doctor'           :        'ویرایش پزشک',
    'edit_employee'         :        'ویرایش کارمند',
    'edit_sickness'         :        'ویرایش بیماری',
    'edit_department'       :        'ویرایش دپارتمان',
    'edit_sub_branch'       :        'ویرایش بخش',
    'edit_admin'            :        'ویرایش ادمین',
}

message_ids = {
  'start'                   :           2,
  'common_questions'        :           4,
  'guide'                   :           6,
  'about_us'                :           8,
  'contact_us'              :           10,
  'add_doctor'              :           13,                 
  'delete_doctor'           :           23,                 
  'add_employee'            :           15,                 
  'delete_employee'         :           25,                 
  'add_sickness'            :           17,                 
  'delete_sickness'         :           27,                 
  'add_department'          :           19,                 
  'delete_department'       :           29,                 
  'add_sub_branch'          :           21,                 
  'delete_sub_branch'       :           31,               
  'add_admin'               :           33,               
  'delete_admin'            :           35,               
}


def check_user(cid):
    global KnownUsers
    KnownUsers = DQL.get_known_users()
    if cid in KnownUsers:
        return True
    elif cid not in KnownUsers:
        info = bot.get_chat(cid)
        first_name = info.first_name
        last_name = info.last_name
        username = info.username
        if DML.insert_users_data(cid, first_name, last_name, username):
            KnownUsers.append(cid)
            return True
        return False
    
def is_spam(cid):
    global KnownUsers
    now = time.time()
    for i in list(spam_users):
        if spam_users[i] <= now - 7200:
            del spam_users[i]
    if cid in spam_users:
        return True
    check_user(cid)
    if cid not in spam_data:
        spam_data.setdefault(cid, {'last_message_time': now, 'score': 0})
        return False
    last_message_time = spam_data[cid]['last_message_time']
    delta = now - last_message_time
    if delta < lower_spam_limit:
        spam_data[cid]['score'] += 1
        if spam_data[cid]['score'] >= spam_score_limit:
            spam_users[cid] = now
            send_message(cid, '❌ به دلیل ارسال پیاپی پیام های نامربوط اکانت شما اسپم شده و به مدت 2 ساعت غیر فعال شد ❌')
            return True
    elif delta > upper_spam_limit:
        spam_data[cid]['score'] = max(0, spam_data[cid]['score']-1)
        return False
    return False 


def send_message(*args, **kwargs):
    try:
        return antiflood(bot.send_message, *args, **kwargs)
    except telebot.apihelper.ApiTelegramException:
        logging.info('error in sending message')
    except Exception as e:
        logging.info(f'another error happened in sending message, {repr(e)}')


logging.basicConfig(filename='hospital.log', level=logging.INFO, format='%(asctime)s, %(filename)s, %(levelname)s, %(message)s', datefmt='%Y-%B-%d %A %H:%M:%S', encoding='utf-8')
def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            logging.info(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)
        elif m.content_type == 'photo':
            logging.info(f'{str(m.chat.first_name)} - {" [" + str(m.chat.id) + "]: "} - new photo recieved')
        elif m.content_type == 'document':
            logging.info(f'{str(m.chat.first_name)} - {" [" + str(m.chat.id) + "]: "} - new document recieved, file name: {m.document.file_name}')
        else:
            logging.info(f'{str(m.chat.first_name)} - {" [" + str(m.chat.id) + "]: "} - another type of message recieved, content type: {m.content_type}')
bot.set_update_listener(listener)


# callback
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    call_id = call.id
    cid = call.message.chat.id
    mid = call.message.id
    data = call.data
    if is_spam(cid): return
    if data.startswith('ap_select_doctor:'):
        doctor_name = data.split(':')[1]
        user_appointment[cid] = {'doctor': doctor_name}
        bot.answer_callback_query(call_id, f'پزشک  با موفقیت انتخاب شد ✅')
        markup = InlineKeyboardMarkup()
        today = jdatetime.date.today()
        for i in range(7):
            future_day = today + jdatetime.timedelta(days=i)
            future_day = (str(future_day).replace('-', '/'))
            markup.add(InlineKeyboardButton(future_day, callback_data=f'ap_select_date:{future_day}'))
        bot.edit_message_text('لطفا تاریخ مراجعه را انتخاب کنید:', cid, call.message.message_id, reply_markup=markup)

    elif data.startswith('ap_select_date:'):
        date_selected = data.split(':')[1]
        user_appointment[cid]['date'] = date_selected
        bot.answer_callback_query(call_id, f'تاریخ مراجعه با موفقیت انتخاب شد ✅')
        markup = InlineKeyboardMarkup()
        doctor = user_appointment[cid]['doctor']
        doctor_ID = DQL.get_doctor_ID(doctor)['ID']
        booked_hours_ID = DQL.get_appointment_booked_hours(doctor_ID, date_selected)
        booked_hours_ID_list = []
        for i in booked_hours_ID:
            booked_hours_ID_list.append(i['hour_ID'])
        booked_hours = []
        for i in booked_hours_ID_list:
            times = DQL.get_hour_data(i)
            booked_hours.append(times['time'])
        all_hours = DQL.get_hour_time()
        available_hours  = [i for i in all_hours if i['time'] not in booked_hours]
        if len(available_hours) == 0:
            send_message(cid, f'متاسفانه ساعت خالی در تاریخ {date_selected} برای دکتر {doctor} وجود ندارد')
            user_appointment[cid] = dict()
            bot.delete_message(cid, call.message.message_id)
            button_backToMainMenu(call.message)
        else:
            for i in available_hours:
                markup.add(InlineKeyboardButton(i['time'], callback_data=f"ap_select_hour:{i['time']}"))
            bot.edit_message_text('لطفا ساعت مراجعه را انتخاب کنید:', cid, call.message.message_id, reply_markup=markup)

    elif data.startswith('ap_select_hour:'):
        hour_selected = data.split('r:')[1]
        user_appointment[cid]['hour'] = hour_selected
        bot.answer_callback_query(call_id, f'ساعت مراجعه با موفقیت انتخاب شد ✅')
        patient_data = DQL.get_patient_data(cid)
        first_name = patient_data['first_name']
        last_name = patient_data['last_name']
        national_code = patient_data['national_code']
        tracking_code = str(time.time()).replace('.', '')
        doctor = user_appointment[cid]['doctor']
        date = user_appointment[cid]['date']
        hour = user_appointment[cid]['hour']
        doctor_ID = DQL.get_doctor_ID(doctor)['ID']
        hour_ID = DQL.get_hour_ID(hour)['ID']
        send_message(cid, f"نوبت شما به شرح زیر است: \nنام و نام خانوادگی: {first_name} {last_name} \nکد ملی: {national_code} \nپزشک: دکتر {user_appointment[cid]['doctor']} \nتاریخ مراجعه: {user_appointment[cid]['date']} \nساعت مراجعه: {user_appointment[cid]['hour']} \nکد پیگیری: {tracking_code}")
        bot.delete_message(cid, call.message.message_id)
        DML.insert_appointment_data(cid, doctor_ID, hour_ID, date, tracking_code)
        user_appointment[cid] = dict()
        button_backToMainMenu(call.message)
        
        
# commands

    # start
@bot.message_handler(commands=['start'])
def command_start(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add( 'نوبت دهی 🕙','دپارتمان ها 👩🏻‍🤝‍🧑🏼')
    markup.add('پیگیری نوبت ✅', 'لیست پزشکان 👩‍⚕️👨‍⚕️')
    markup.add('راهنما 🗨', 'امتیاز دهی 5️⃣')
    markup.add('نظرات پیشنهادات و انتقادات 💞', 'سوالات متداول ❓')
    markup.add('درباره ما 🚑', 'تماس با ما 📱')
    markup.add('لینک دعوت 🤝', 'ثبت نام 🔀')
    bot.copy_message(cid, channel_cid, message_ids['start'], reply_markup=markup)
    
    
    # help
@bot.message_handler(commands=['help'])
def command_help(message):
    cid = message.chat.id
    if is_spam(cid): return
    text = 'منوی کمک: \n'
    for command, desc in commands.items():
        text += f'/{command}  -  {desc}\n'
    if cid in admins:
        text += '\n****   کامند های ادمین ها   ****\n'
        for command, desc in admins_commands.items():
            text += f'/{command}  -  {desc}\n'
    send_message(cid, text, reply_to_message_id=message.message_id)
    
    
    # departments
@bot.message_handler(commands=['departments'])
def command_departments(message):
    cid = message.chat.id
    if is_spam(cid): return
    deps = DQL.get_department_name()
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in deps:
        markup.add(f'{i["name"]}')
    markup.add('بازگشت به منوی اصلی 🔙')
    send_message(cid, 'لیست دپارتمان ها :', reply_markup=markup)
    user_step[cid] = 'select_dep_from_list'
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'select_dep_from_list')
def step_select_dep_from_list(message):
    cid = message.chat.id
    if is_spam(cid): return
    dep_name = message.text
    if dep_name == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        dep_ID = DQL.get_department_data_from_name(dep_name)['ID']
        sub_branch_data = DQL.get_sub_branch_data_from_dep_ID(dep_ID)
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in sub_branch_data:
            markup.add(i['name'])
        markup.add('بازگشت به منوی اصلی 🔙')
        send_message(cid, f'دپارتمان {dep_name} :', reply_markup=markup)
        user_step[cid] = 'select_dep_from_list1'    
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'select_dep_from_list1')
def step_select_dep_from_list1(message):
    cid = message.chat.id
    if is_spam(cid): return
    sub_name = message.text
    if sub_name == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        sub_desc = DQL.get_sub_branch_data_from_dep_name(sub_name)['description']
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('بازگشت به منوی اصلی 🔙')
        send_message(cid, f'بخش {sub_name} : {sub_desc}', reply_markup=markup)
        user_step[cid] = dict()
    
    
    # doctors list
@bot.message_handler(commands=['doctors_list'])
def command_doctors_list(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    docs = DQL.get_doctor_name()    
    for i in docs:
        if i['gender'] == 'مرد':
            m = f'آقای دکتر {i["name"]} 👨‍⚕️'
            markup.add(m)
        elif i['gender'] == 'زن':
            f = f'خانم دکتر {i["name"]} 👩‍⚕️'
            markup.add(f)
    send_message(cid, 'لیست پزشکان :', reply_markup=markup)
    user_step[cid] = 'select_doc_from_list'

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'select_doc_from_list')
def step_select_doc_from_list(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    name = message.text
    raw_name = name.split()[2] + ' ' + name.split()[3]
    disc = DQL.get_doctor_description(raw_name)
    send_message(cid, f'{name}  : \n{disc[0]["description"]}', reply_markup=markup) 
    user_step[cid] = dict()   


    # guide
@bot.message_handler(commands=['guide'])
def command_guide(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    bot.copy_message(cid, channel_cid, message_ids['guide'], reply_markup=markup)
    
    
    # common questions
@bot.message_handler(commands=['common_questions'])
def command_common_questions(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    bot.copy_message(cid, channel_cid, message_ids['common_questions'], reply_markup=markup)
    
    
    # contact us
@bot.message_handler(commands=['contact_us'])
def command_contact_us(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    bot.copy_message(cid, channel_cid, message_ids['contact_us'], reply_markup=markup)
    
    
    # about us
@bot.message_handler(commands=['about_us'])
def command_about_us(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    bot.copy_message(cid, channel_cid, message_ids['about_us'], reply_markup=markup)
    
    
    # invite link
@bot.message_handler(commands=['invite_link'])
def command_invite_link(message):
    cid = message.chat.id
    if is_spam(cid): return
    random_number1 = random.randint(100, 999)
    random_number2 = random.randint(100, 999)
    user_invite_link = f"https://t.me/iran_hospital_bot?start={random_number1}{cid}{random_number2}"
    send_message(cid, f'لینک دعوت شما : \n{user_invite_link}')
    
    
    # sign up
@bot.message_handler(commands=['sign_up'])
def command_sign_up(message):
    cid = message.chat.id
    if is_spam(cid): return
    try:
        signed_up_users = DQL.get_patient_data(cid)
        if signed_up_users['CID'] == cid:
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('پاک کردن اطلاعات 🚯')
            markup.add('بازگشت به منوی اصلی 🔙')
            send_message(cid, 'شما قبلا ثبت نام کردید 👍 \nتذکر: پاک کردن اطلاعات باعث حذف نوبت ها به صورت خودکار هم میشود 🆘', reply_markup=markup)
            user_resignup[cid] = 'resignup'
        else:
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('بازگشت به منوی اصلی 🔙')
            user_data.setdefault(cid, dict())
            send_message(cid, 'لطفا نام خود را وارد کنید', reply_markup=markup)
            user_step[cid] = 'su_fn'
    except Exception as e:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('بازگشت به منوی اصلی 🔙')
        user_data.setdefault(cid, dict())
        send_message(cid, 'لطفا نام خود را وارد کنید', reply_markup=markup)
        user_step[cid] = 'su_fn'
        
        
@bot.message_handler(func=lambda  message: user_resignup.get(message.chat.id) == 'resignup')
def step_resignup(message):
    cid = message.chat.id
    if is_spam(cid): return
    text = message.text
    if text == 'پاک کردن اطلاعات 🚯':
        DML.remove_patient_data(cid)
        send_message(cid, 'اطلاعات شما با موفقیت حذف شد ✔')
        user_resignup[cid] = dict()
        button_backToMainMenu(message)
    elif text == 'بازگشت به منوی اصلی 🔙':
        user_resignup[cid] = dict()
        button_backToMainMenu(message)
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'su_fn')
def step_su_fn(message):
    cid = message.chat.id
    if is_spam(cid): return
    first_name = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if first_name == 'بازگشت به منوی اصلی 🔙': 
        user_data[cid] = dict()
        user_step[cid] = dict()
        button_backToMainMenu(message)
    else:
        user_data[cid].setdefault('first_name', first_name)
        send_message(cid, 'لطفا نام خانوادگی خود را وارد کنید', reply_markup=markup)
        user_step[cid] = 'su_ln'
        
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'su_ln')
def step_su_ln(message):
    cid = message.chat.id
    if is_spam(cid): return
    last_name = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if last_name == 'بازگشت به منوی اصلی 🔙': 
        user_data[cid] = dict()
        user_step[cid] = dict()
        button_backToMainMenu(message)
    else:
        user_data[cid].setdefault('last_name', last_name)
        send_message(cid, 'لطفا سال تولد خود را وارد کنید', reply_markup=markup)
        user_step[cid] = 'su_by'
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'su_by')
def step_su_by(message):
    cid = message.chat.id
    if is_spam(cid): return
    birth_year = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if birth_year == 'بازگشت به منوی اصلی 🔙': 
        user_data[cid] = dict()
        user_step[cid] = dict()
        button_backToMainMenu(message)
    else:
        user_data[cid].setdefault('birth_year', birth_year)
        send_message(cid, 'لطفا کد ملی خود را وارد کنید', reply_markup=markup)
        user_step[cid] = 'su_nc'
        
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'su_nc')
def step_su_nc(message):
    cid = message.chat.id
    if is_spam(cid): return
    national_code = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if national_code == 'بازگشت به منوی اصلی 🔙': 
        user_data[cid] = dict()
        user_step[cid] = dict()
        button_backToMainMenu(message)
    else:
        user_data[cid].setdefault('national_code', national_code)
        send_message(cid, 'لطفا آدرس خود را وارد کنید', reply_markup=markup)
        user_step[cid] = 'su_address'
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'su_address')
def step_su_address(message):
    cid = message.chat.id
    if is_spam(cid): return
    address = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if address == 'بازگشت به منوی اصلی 🔙': 
        user_data[cid] = dict()
        user_step[cid] = dict()
        button_backToMainMenu(message)
    else:
        user_data[cid].setdefault('address', address)
        send_message(cid, 'لطفا شماره موبایل خود را وارد کنید', reply_markup=markup)
        user_step[cid] = 'su_phone'

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'su_phone')
def step_su_phone(message):
    cid = message.chat.id
    if is_spam(cid): return
    global user_data
    phone = message.text
    if phone == 'بازگشت به منوی اصلی 🔙': 
        user_data[cid] = dict()
        user_step[cid] = dict()
        button_backToMainMenu(message)
    else:
        info = bot.get_chat(cid)
        send_message(cid, 'سپاس اطلاعات شما با موفقیت ثبت شد')
        first_name = user_data[cid]['first_name']
        last_name = user_data[cid]['last_name']
        birth_year = str(user_data[cid]['birth_year'])
        national_code = str(user_data[cid]['national_code'])
        address = user_data[cid]['address']
        username = info.username
        phone = str(phone)
        description = None
        DML.insert_patient_data(cid, first_name, last_name, birth_year, national_code, address, username, phone, description)
        user_data[cid] = dict()
        user_step[cid] = dict()
        button_backToMainMenu(message)
    

    # appointment
@bot.message_handler(commands=['appointment'])
def command_appointment(message):
    cid = message.chat.id
    if is_spam(cid): return
    try:
        signed_up_patient = DQL.get_patient_data(cid)
        if signed_up_patient is None:
            logging.info('error happend')
    except Exception as e:
        send_message(cid, 'لطفا ابتدا ثبت نام کنید')
        command_sign_up(message)
        return
    else:
        send_message(cid, 'نوبت دهی 🕙:', reply_markup=hideboard)
        doc_names = DQL.get_doctor_name()
        markup = InlineKeyboardMarkup()
        for i in doc_names:
            if i['gender'] == 'مرد':
                markup.add(InlineKeyboardButton(f'آقای دکتر {i["name"]} 👨‍⚕️', callback_data=f'ap_select_doctor:{i["name"]}'))
            elif i['gender'] == 'زن':
                markup.add(InlineKeyboardButton(f'خانم دکتر {i["name"]} 👩‍⚕️', callback_data=f'ap_select_doctor:{i["name"]}'))
        res = send_message(cid, 'لطفا پزشک مورد نظر را انتخاب کنید:', reply_markup=markup)
    
    
    # tracking appointment
@bot.message_handler(commands=['tracking_appointment'])
def command_tracking_appointment(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    send_message(cid, 'لطفا کد پیگیری خود را وارد کنید (اعداد فقط به انگلیسی)', reply_markup=markup)
    user_step[cid] = 'input_tracking_code'
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'input_tracking_code')
def step_input_tracking_code(message):
    cid = message.chat.id
    if is_spam(cid): return
    tracking_code = message.text
    if tracking_code == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        try:
            appointments = DQL.get_appointment_data(tracking_code)
            if len(appointments) == 0:
                send_message(cid, 'نوبتی با این کد پیگیری ثبت نشده است ❌')
                user_step[cid] = dict()
                button_backToMainMenu(message)
        except Exception as e:
            send_message(cid, 'نوبتی با این کد پیگیری ثبت نشده است ❌')  
            user_step[cid] = dict()
            button_backToMainMenu(message)
        else:
            appointment_data = DQL.get_appointment_data(tracking_code)
            doctor_ID = appointment_data['doctor_ID']
            status = appointment_data['status']
            date = appointment_data['date']
            hour_ID = appointment_data['Hour_ID']
            patient_data = DQL.get_patient_data(cid)
            first_name = patient_data['first_name']
            last_name = patient_data['last_name']
            nc = patient_data['national_code']
            doctor_data = DQL.get_doctor_data(doctor_ID)
            doc_name = doctor_data['name']
            hour_time = DQL.get_hour_data(hour_ID)['time']
            send_message(cid, f"نوبت شما به شرح زیر است: \nنام و نام خانوادگی: {first_name} {last_name} \nکد ملی: {nc} \nپزشک: دکتر {doc_name} \nتاریخ مراجعه: {date} \nساعت مراجعه: {hour_time}")
            user_step[cid] = dict()
            button_backToMainMenu(message)

 
    # rate
@bot.message_handler(commands=['rate'])
def command_rate(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    docs = DQL.get_doctor_name()
    for i in docs:
        if i['gender'] == 'مرد':
            markup.add(f'آقای دکتر {i["name"]} 👨‍⚕️')
        elif i['gender'] == 'زن':
            markup.add(f'خانم دکتر {i["name"]} 👩‍⚕️')
    send_message(cid, 'لطفا پزشک مورد نظر را انتخاب کنید', reply_markup=markup)
    user_step[cid] = 'select_doc'
    user_rate.setdefault(cid, dict())
    user_rate[cid].setdefault('doctor', i)
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'select_doc')
def step_select_doc(message):
    cid = message.chat.id
    if is_spam(cid): return
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict() 
        user_rate[cid] = dict()       
        button_backToMainMenu(message)
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('بازگشت به منوی اصلی 🔙')
        send_message(cid, 'لطفا امتیاز خود را بین 1 تا 5 وارد کنید', reply_markup=markup)
        user_step[cid] = 'rate'

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'rate')
def step_rate(message):
    cid = message.chat.id
    if is_spam(cid): return
    rate = message.text
    if rate == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict() 
        user_rate[cid] = dict()       
        button_backToMainMenu(message)
    else:
        send_message(cid, 'ممنون امتیاز شما ثبت شد')
        DML.insert_rate_data(cid, rate)
        user_step[cid] = dict()
        button_backToMainMenu(message)
    
    
    # comments
@bot.message_handler(commands=['comments'])
def command_comments(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    send_message(cid, 'لطفا نظرات خود را وارد کنید', reply_markup=markup)
    user_step[cid] = 'comments'
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'comments')
def step_comments(message):
    cid = message.chat.id
    if is_spam(cid): return
    comments = message.text
    if comments == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        send_message(cid, 'ممنون نظر شما ثبت شد')
        DML.insert_comments_data(cid, comments)
        user_step[cid] = dict()
        button_backToMainMenu(message)
    

    # admin commands

        # edit doctor
@bot.message_handler(commands=['edit_doctor'])
def command_edit_doctor(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('حذف', 'افزودن')
    markup.add('بازگشت به منوی اصلی 🔙')
    send_message(cid, 'ویرایش پزشک:', reply_markup=markup)
    user_step[cid] = 'edit_doctor'  

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'edit_doctor')
def step_edit_doctor(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    elif message.text == 'افزودن':
        bot.copy_message(cid, channel_cid,  message_ids['add_doctor'], reply_markup=markup)
        user_step[cid] = 'add_doctor'  
    elif message.text == 'حذف':
        bot.copy_message(cid, channel_cid,  message_ids['delete_doctor'], reply_markup=markup)
        user_step[cid] = 'delete_doctor'  
   
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'add_doctor')
def step_add_doctor(message):
    cid = message.chat.id
    if is_spam(cid): return  
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        try:
            doctor_info = message.text.split('\n')
            name = doctor_info[0]
            national_code = doctor_info[1]
            birth_year = doctor_info[2]
            gender = doctor_info[3]
            phone = doctor_info[4]
            medical_code = doctor_info[5]
            email = doctor_info[6]
            Department_ID = doctor_info[7]
            description = doctor_info[8]
            password = doctor_info[9]        
            DML.insert_doctor_data(name, national_code, birth_year, gender, phone, medical_code, email, None, None, Department_ID, description, password)
            send_message(cid, 'پزشک جدید با موفقیت ثبت شد')
        except Exception as e:
            send_message(cid, 'متاسفانه ثبت پزشک جدید با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message)
        
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'delete_doctor')
def step_delete_doctor(message):
    cid = message.chat.id
    if is_spam(cid): return 
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        try:
            doctor_info = message.text.split('\n')
            name = doctor_info[0]
            national_code = doctor_info[1]
            DML.remove_doctor_data(name, national_code)
            send_message(cid, 'پزشک با موفقیت حذف شد')
        except Exception as e:
            send_message(cid, 'متاسفانه حذف پزشک با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message)
      

        # edit employee
@bot.message_handler(commands=['edit_employee'])
def command_edit_employee(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('حذف', 'افزودن')
    markup.add('بازگشت به منوی اصلی 🔙')
    send_message(cid, 'ویرایش کارمند:', reply_markup=markup)
    user_step[cid] = 'edit_employee' 
        
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'edit_employee')
def step_edit_employee(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    elif message.text == 'افزودن':
        bot.copy_message(cid, channel_cid,  message_ids['add_employee'], reply_markup=markup)
        user_step[cid] = 'add_employee'  
    elif message.text == 'حذف':
        bot.copy_message(cid, channel_cid,  message_ids['delete_employee'], reply_markup=markup)
        user_step[cid] = 'delete_employee'   

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'add_employee')
def step_add_employee(message):
    cid = message.chat.id
    if is_spam(cid): return  
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        try:
            employee_info = message.text.split('\n')
            name = employee_info[0]
            birth_year = employee_info[1]
            phone = employee_info[2]
            national_code = employee_info[3]
            Department_ID = employee_info[4]
            DML.insert_employee_data(name, birth_year, phone, national_code, None, None, Department_ID, None, None)
            send_message(cid, 'کارمند جدید با موفقیت ثبت شد')
        except Exception as e:
            send_message(cid, 'متاسفانه ثبت کارمند جدید با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message)  
   
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'delete_employee')
def step_delete_employee(message):
    cid = message.chat.id
    if is_spam(cid): return 
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:   
        try:
            employee_info = message.text.split('\n')
            name = employee_info[0]
            national_code = employee_info[1] 
            DML.remove_employee_data(name, national_code)
            send_message(cid, 'کارمند با موفقیت حذف شد')
        except Exception as e:
            send_message(cid, 'متاسفانه حذف کارمند با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message) 
   
      
        # edit sickness
@bot.message_handler(commands=['edit_sickness'])
def command_edit_sickness(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('حذف', 'افزودن')
    markup.add('بازگشت به منوی اصلی 🔙')
    send_message(cid, 'ویرایش بیماری:', reply_markup=markup)
    user_step[cid] = 'edit_sickness'  

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'edit_sickness')
def step_edit_sickness(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    elif message.text == 'افزودن':
        bot.copy_message(cid, channel_cid,  message_ids['add_sickness'], reply_markup=markup)
        user_step[cid] = 'add_sickness'  
    elif message.text == 'حذف':
        bot.copy_message(cid, channel_cid,  message_ids['delete_sickness'], reply_markup=markup)
        user_step[cid] = 'delete_sickness' 
        
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'add_sickness')
def step_add_sickness(message):
    cid = message.chat.id
    if is_spam(cid): return  
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        try:
            sickness_info = message.text.split('\n')
            title = sickness_info[0]
            Department_ID = sickness_info[1]
            DML.insert_sickness_data(title, Department_ID, None)
            send_message(cid, 'بیماری جدید با موفقیت ثبت شد')
        except Exception as e:
            send_message(cid, 'متاسفانه ثبت بیماری جدید با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message) 

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'delete_sickness')
def step_delete_sickness(message):
    cid = message.chat.id
    if is_spam(cid): return 
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:   
        try:
            sickness_name = message.text
            DML.remove_sickness_data(sickness_name)
            send_message(cid, 'بیماری با موفقیت حذف شد')
        except Exception as e:
            send_message(cid, 'متاسفانه حذف بیماری با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message)
    
    
        # edit department
@bot.message_handler(commands=['edit_department'])
def command_edit_department(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('حذف', 'افزودن')
    markup.add('بازگشت به منوی اصلی 🔙')
    send_message(cid, 'ویرایش دپارتمان:', reply_markup=markup)
    user_step[cid] = 'edit_department'  

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'edit_department')
def step_edit_department(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    elif message.text == 'افزودن':
        bot.copy_message(cid, channel_cid,  message_ids['add_department'], reply_markup=markup)
        user_step[cid] = 'add_department'  
    elif message.text == 'حذف':
        bot.copy_message(cid, channel_cid,  message_ids['delete_department'], reply_markup=markup)
        user_step[cid] = 'delete_department' 
        
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'add_department')
def step_add_department(message):
    cid = message.chat.id
    if is_spam(cid): return  
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        try:
            department_name = message.text
            DML.insert_department_data(department_name, None)
            send_message(cid, 'دپارتمان جدید با موفقیت ثبت شد')
        except Exception as e:
            send_message(cid, 'متاسفانه ثبت دپارتمان جدید با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message) 
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'delete_department')
def step_delete_department(message):
    cid = message.chat.id
    if is_spam(cid): return 
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:   
        try:
            department_name = message.text
            DML.remove_department_data(department_name)
            send_message(cid, 'دپارتمان با موفقیت حذف شد')
        except Exception as e:
            send_message(cid, 'متاسفانه حذف دپارتمان با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message)
    
    
        # edit sub_branch
@bot.message_handler(commands=['edit_sub_branch'])
def command_edit_sub_branch(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('حذف', 'افزودن')
    markup.add('بازگشت به منوی اصلی 🔙')
    send_message(cid, 'ویرایش بخش:', reply_markup=markup)
    user_step[cid] = 'edit_sub_branch'  

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'edit_sub_branch')
def step_edit_sub_branch(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    elif message.text == 'افزودن':
        bot.copy_message(cid, channel_cid,  message_ids['add_sub_branch'], reply_markup=markup)
        user_step[cid] = 'add_sub_branch'  
    elif message.text == 'حذف':
        bot.copy_message(cid, channel_cid,  message_ids['delete_sub_branch'], reply_markup=markup)
        user_step[cid] = 'delete_sub_branch' 

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'add_sub_branch')
def step_add_sub_branch(message):
    cid = message.chat.id
    if is_spam(cid): return  
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        try:
            sub_branch_info = message.text.split('\n')
            name = sub_branch_info[0]
            Department_ID = sub_branch_info[1]
            description = sub_branch_info[2]
            DML.insert_sub_branch_data(name, Department_ID, description)
            send_message(cid, 'بخش جدید با موفقیت ثبت شد')
        except Exception as e:
            send_message(cid, 'متاسفانه ثبت بخش جدید با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message) 

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'delete_sub_branch')
def step_delete_sub_branch(message):
    cid = message.chat.id
    if is_spam(cid): return 
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:   
        try:
            sub_branch_name = message.text
            DML.remove_sub_branch_data(sub_branch_name)
            send_message(cid, 'بخش با موفقیت حذف شد')
        except Exception as e:
            send_message(cid, 'متاسفانه حذف بخش با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message)
    
    
        # edit admin
@bot.message_handler(commands=['edit_admin'])
def command_edit_admin(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('حذف', 'افزودن')
    markup.add('بازگشت به منوی اصلی 🔙')
    send_message(cid, 'ویرایش ادمین:', reply_markup=markup)
    user_step[cid] = 'edit_admin'  

@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'edit_admin')
def step_edit_admin(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('بازگشت به منوی اصلی 🔙')
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    elif message.text == 'افزودن':
        bot.copy_message(cid, channel_cid,  message_ids['add_admin'], reply_markup=markup)
        user_step[cid] = 'add_admin'  
    elif message.text == 'حذف':
        bot.copy_message(cid, channel_cid,  message_ids['delete_admin'], reply_markup=markup)
        user_step[cid] = 'delete_admin' 
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'add_admin')
def step_add_admin(message):
    cid = message.chat.id
    if is_spam(cid): return  
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:
        try:
            admin_CID = message.text
            config.admins.append(admin_CID)
            send_message(cid, 'ادمین جدید با موفقیت ثبت شد')
            logging.info(cid, 'ادمین جدید با موفقیت ثبت شد')
        except Exception as e:
            send_message(cid, 'متاسفانه ثبت ادمین جدید با خطا مواجه شد')
            logging.info(cid, 'متاسفانه ثبت ادمین جدید با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message)    
    
@bot.message_handler(func=lambda  message: user_step.get(message.chat.id) == 'delete_admin')
def step_delete_admin(message):
    cid = message.chat.id
    if is_spam(cid): return 
    if message.text == 'بازگشت به منوی اصلی 🔙':
        user_step[cid] = dict()        
        button_backToMainMenu(message)
    else:   
        try:
            admin_CID = message.text
            config.admins.remove(admin_CID)
            send_message(cid, 'ادمین با موفقیت حذف شد')
            logging.info(cid, 'ادمین با موفقیت حذف شد')
        except Exception as e:
            send_message(cid, 'متاسفانه حذف ادمین با خطا مواجه شد')
            logging.info(cid, 'متاسفانه حذف ادمین با خطا مواجه شد')
        user_step[cid] = dict()
        button_backToMainMenu(message) 
       
   
  
  
    
# functions (text)
@bot.message_handler(func=lambda message: message.text=='بازگشت به منوی اصلی 🔙')
def button_backToMainMenu(message):
    cid = message.chat.id
    if is_spam(cid): return
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('نوبت دهی 🕙','دپارتمان ها 👩🏻‍🤝‍🧑🏼')
    markup.add('پیگیری نوبت ✅', 'لیست پزشکان 👩‍⚕️👨‍⚕️')
    markup.add('راهنما 🗨', 'امتیاز دهی 5️⃣')
    markup.add('نظرات پیشنهادات و انتقادات 💞', 'سوالات متداول ❓')
    markup.add('درباره ما 🚑', 'تماس با ما 📱')
    markup.add('لینک دعوت 🤝', 'ثبت نام 🔀')
    send_message(cid, 'منوی اصلی :', reply_markup=markup)

    # departments
@bot.message_handler(func=lambda message: message.text=='دپارتمان ها 👩🏻‍🤝‍🧑🏼')
def button_departments(message):
    command_departments(message)

    # doctors list
@bot.message_handler(func=lambda message: message.text=='لیست پزشکان 👩‍⚕️👨‍⚕️')
def button_doctors_list(message):
    command_doctors_list(message)

    # guide
@bot.message_handler(func=lambda message: message.text=='راهنما 🗨')
def button_guide(message):
    command_guide(message)
    
    # common questions
@bot.message_handler(func=lambda message: message.text=='سوالات متداول ❓')
def button_common_questions(message):
    command_common_questions(message)
    
    # contact us
@bot.message_handler(func=lambda message: message.text=='تماس با ما 📱')
def button_contact_us(message):
    command_contact_us(message)
       
    # about us
@bot.message_handler(func=lambda message: message.text=='درباره ما 🚑')
def button_about_us(message):
    command_about_us(message)
    
    # invite link
@bot.message_handler(func=lambda message: message.text=='لینک دعوت 🤝')
def button_invite_link(message):
    command_invite_link(message)
    
    # sign up
@bot.message_handler(func=lambda message: message.text=='ثبت نام 🔀')
def button_sign_up(message):
    command_sign_up(message)
    
    # appointment
@bot.message_handler(func=lambda message: message.text=='نوبت دهی 🕙')
def button_appointment(message):
    command_appointment(message)
    
    # tracking appointment
@bot.message_handler(func=lambda message: message.text=='پیگیری نوبت ✅')
def button_tracking_appointment(message):
    command_tracking_appointment(message)
    
    # rate
@bot.message_handler(func=lambda message: message.text=='امتیاز دهی 5️⃣')
def button_rate(message):
    command_rate(message)
      
    # comments
@bot.message_handler(func=lambda message: message.text=='نظرات پیشنهادات و انتقادات 💞')
def button_comments(message):
    command_comments(message)


# anything
@bot.message_handler(func=lambda message: True, content_types=['text'])
def command_default(m):
    cid = m.chat.id
    if is_spam(cid): return
    send_message(cid, f'متاسفانه متوجه این متن " {m.text} " نمیشم\nبهتره منوی کمک {"/help"} را امتحان کنید')
bot.infinity_polling()