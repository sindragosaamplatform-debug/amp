# Постбеки для трекера Keitaro
URL: https://help.aff.ltd/uk/admin-panel/postbacks-for-keitaro
Category: ⚙️ Адмін-панель
Section: Постбеки
Summary: Особливості налаштування постбеків для трекера Keitaro/Кейтаро.
Updated: 3 місяці тому

## 1. Загальна інформація

У трекері Keitaro додано шаблон постбеку для наших партнерок.

Перед налаштуванням постбеків партнеру ОБОВʼЯЗКОВО слід переглянути наведені нижче приклади.

Важливі нюанси щодо трекера Keitaro:

- В архітектурі Keitaro немає поділу на кілька постбеків залежно від події – використовується один лінк із різними статусами у GET-параметрі &status=.
- Трекер Keitaro за замовчуванням підтримує 3 статуси ліда:
○ Лід – гравець здійснив реєстрацію, депозит або пройшов кваліфікацію.
○ Продаж – гравець отримав статус Approve (виплата за цього гравця отримала такий статус).
○ Відхилено – гравець отримав статус Reject (виплата за цього гравця отримала такий статус).

Шаблон, що доданий в Keitaro:

[домен трекера партнера/id]/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##
&status=reg,dep,lead,approve,reject,rebill&lead_status=reg,dep,lead
&sale_status=approve,rebill&rejected_status=reject
&payout=##CPA_AMOUNT##,##RS_AMOUNT##
&currency=rub,usd,eur
&from=[ПартнерськаПрограма]

Вище – це шаблон.

Нижче наведені приклади налаштування для кожного окремого кейсу (реєстрація, депозит, кваліфікація тощо).

Розшифрування GET-параметрів посилання:

- ?subid=##CLICK_ID## – основний параметр, у який ми передаємо click_id.
- &tid=##POSTBACK_ID## – додатковий параметр для роботи Keitaro, у який передаємо postback_id.
- &status= – передаємо статус/тип постбеку, можливі значення:
○ reg;
○ dep;
○ lead;
○ approve;
○ reject;
○ rebill.
○ У GET-параметрі &status= зазначається лише один потрібний статус
○ Розшифрування статусів наведене нижче у прикладах.
- &lead_status=reg, dep, lead – параметр навчання Keitaro, є статичним, його не змінюємо.
- &sale_status=approve, rebill – статичний параметр навчання Keitaro, не змінюємо.
- &rejected_status=reject – статичний параметр навчання Keitaro, не змінюємо.
- &payout= – сума ставки за гравця або сума виплати за RS. Вказуємо лише одне значення: ##CPA_AMOUNT## або ##RS_AMOUNT## (залежно від типу налаштованого постбеку).
- &currency= – валюта виплати, можливі значення:
○ rub;
○ usd;
○ eur.
- &from= – ПП, від якої система надсилає постбек. Беремо з шаблону постбеку, який надав партнер.

Приклад налаштування постбеків (без домену трекера) для Keitaro:

- У GET-параметрі &currency= вказуємо валюту програми (тільки одну).
- У GET-параметрі &from= (значення [ПартнерськаПрограма]) беремо зі шаблону постбеку, який надав партнер.

## 2. Базові налаштування

Всередині трекера Keitaro: наш статус Квала → це Лід, наш статус Approve → це Продаж, наш статус Reject → це Відхилено.

Якщо партнер хоче, щоб замість продажу був не Approve, а, наприклад, FD або Квала, дивіться розширені налаштування нижче.
Якщо партнеру недостатньо стандартних постбеків (Квала, Approve, Reject), дивіться Розширені.

## 2.1. Для CPA та CPFD програм трекер Keitaro підтримує лише події: Квала, Approve, Reject

2.1.1. Квала (не передаємо виплату за гравця, оскільки він ще не Approve)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=lead&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Ліди"):

[image: https://ucarecdn.com/7b8f5827-ce91-4030-a940-1f8aada79e35/164217303723_kiss_11kb.png]

2.1.2. Квала (якщо вебу потрібно і ми готові передати, передаємо понтенційну виплату за гравця)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=lead&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (окрім лідів додається ще й дохід, який ми передамо в ##CPA_AMOUNT##):

[image: https://ucarecdn.com/34dac694-34bd-4db3-8c2f-1b5ac25b2f3c/164217307366_kiss_13kb.png]

2.1.3. Approve

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=approve&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпцях "Продажі" та "Дохід"):

[image: https://ucarecdn.com/85a40be7-7fd3-4922-8092-e8c434667e05/164217313741_kiss_13kb.png]

2.1.4. Reject (якщо НЕ передавали виплату в квалі)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reject&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Відхилені"):

[image: https://ucarecdn.com/81078ac3-c4b3-4456-9e64-0a4cfd8a49ae/164217330172_kiss_5kb.png]

2.1.5. Reject (якщо передавали виплату в квалі)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reject&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Відхилені" та "Дохід" (відмови)):

[image: https://ucarecdn.com/e56619e1-c780-42ef-95ad-31fe6e4e5070/164217347038_kiss_10kb.png]

## 2.2. Для RS програм трекер Keitaro підтримує лише події: Рега або FD, Дохід за RS

2.2.1. Рега (Можна налаштовувати тільки в тому випадку, якщо не був налаштований івент FD

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reg&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Ліди"):

[image: https://ucarecdn.com/b3cb738f-e88e-4c77-a215-c3488aefca42/164217303723_kiss_11kварвптвптb (1).png]

2.2.2. FD (Саме перший депозит; можна налаштувати тільки у випадку, якщо не був налаштований івент Рега)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=dep&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Ліди"):

[image: https://ucarecdn.com/e0ee8ee7-2929-46cb-812c-c56d5817b37c/164217303723_kiss_11kварвптвптb (1).png]

2.2.3. Дохід за RS

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##RS_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Допродажі" і "Дохід", це накопичувальна подія (відображається сумарний дохід за RS за гравців за період):

[image: https://ucarecdn.com/d33f4bc8-a569-4fe4-bcc3-e83f9b3a39e5/164217531924_kiss_14kb.png]

## 2.3. Для Гібридних програм трекер Keitaro підтримує лише події: Квала, Approve, Reject, Дохід за RS

2.3.1. Квала (не передаємо виплату за гравця, оскільки він ще не Approve)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=lead&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Ліди"):

[image: https://ucarecdn.com/fd144433-8a2e-4135-ab13-f174c564a65e/164217303723_kiss_11kварвптвптb (1).png]

2.3.2. Квала (якщо вебу потрібно і ми готові передати, передаємо понтенційну виплату за гравця)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=lead&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (окрім лідів додається ще й дохід, який ми передамо в ##CPA_AMOUNT##):

[image: https://ucarecdn.com/dec386cb-4a67-4697-854c-137df1a8f6d2/164217307366_kiss_13kb (1).png]

2.3.3. Approve

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=approve&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпцях "Продажі" та "Доход"):

[image: https://ucarecdn.com/d4bb322c-4506-463d-9932-2573f15e7f1c/164217313741_kiss_13kb.png]

2.3.4. Reject (якщо НЕ передавали виплату в квалі)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reject&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Відхилені"):

[image: https://ucarecdn.com/60678086-3ebd-4390-9e08-4806ea120406/164217330172_kiss_5kb.png]

2.3.5. Reject (якщо передавали виплату в квалі)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reject&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Відхилені" та "Дохід" (відмови)):

[image: https://ucarecdn.com/0667249a-a221-43a5-962f-064dc277daec/164217347038_kiss_10kb.png]

2.3.6. Дохід за RS

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##RS_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпцях "Допродажі" та "Дохід", це накопичувальна подія (відображається сумарний дохід за RS за гравців за період)):

[image: https://ucarecdn.com/3fb91150-c93a-40f7-9c3a-ba733f61d5d3/164217531924_kiss_14kb.png]

## 3. Костилі та продвинуті налаштування. Частина 1.

Можливо тільки для чистих CPA програм та CPFD.

Для кейсів 3.1-3.4 передбачається, що наш статус Approve – це Продаж в трекері Keitaro, якщо потрібно навпаки, це буде показано в Частині 2.

## 3.1. Відстукування Реги та FD, не можна буде відстукувати Квалу, можна буде відстукати Approve та Reject (показано після 4-го кейсу).

Таким чином буде відображено в Keitaro (додається значення в стовпцях "Ліди" та "Допродажі"):

[image: https://ucarecdn.com/d10f769c-e5b5-4005-8a3a-ab651e0075aa/164218074775_kiss_8kb.png]

3.1.1. Рега

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reg&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

3.1.2. FD

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=0&currency=rub,usd,eur&from=[ПартнерськаПрограма]

## 3.2. Відстукування Реги та Депів (повторні депи та депи будуть сумуватися), не можна буде відстукувати Квалу, можна буде відстукати Approve та Reject (показано після 4-го кейсу).

3.2.1. Таким чином буде відображено в Keitaro (додається значення в стовпцях "Ліди" та "Допродажі"):

[image: https://ucarecdn.com/a3496fb4-8050-44bb-ac53-c00a5896f676/164218121502_kiss_8kb.png]

3.2.2. Рега

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reg&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

3.2.3. Депы (всі FD+RD)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=0&currency=rub,usd,eur&from=[ПартнерськаПрограма]

## 3.3. Відстукування Реги та Квалу, не можна буде відстукувати FD та Депи, можна буде відстукати Approve та Reject (показано після 4-го кейсу).

3.3.1. Таким чином буде відображено в Keitaro (додається значення в стовпцях "Ліди" та "Допродажі"):

[image: https://ucarecdn.com/29f8e252-b79f-4da4-a19d-77fe73756499/164218134125_kiss_7kb.png]

3.3.2. Рега

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reg&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

3.3.3. Квала (не передаємо виплату за гравця, оскільки він ще не Approve)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=0&currency=rub,usd,eur&from=[ПартнерськаПрограма]

3.3.4. Квала (якщо вебу потрібно і ми готові передати, передаємо понтенційну виплату за гравця)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

## 3.4. Відстукування FD та Квали, не можна буде відстукувати Реги, можна буде відстукати Approve та Reject (показано після 4-го кейсу).

3.4.1. Таким чином буде відображено в Keitaro (додається значення в стовпцях "Ліди" та "Допродажі"):

[image: https://ucarecdn.com/348d97d9-85b9-49bd-8f6e-629d0256b971/1111111164218162140_kiss_6kb.png]

3.4.2. FD

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=dep&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

3.4.3. Квала (не передаємо виплату за гравця, оскільки він ще не Approve)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=0&currency=rub,usd,eur&from=[ПартнерськаПрограма]

3.4.4. Квала (якщо вебу потрібно і ми готові передати, передаємо понтенційну виплату за гравця)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Для кейсів 1-4 Approve и Reject відстукуються стандартним чином.

Approve

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=approve&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпцях "Допродажі" та "Дохід"):

[image: https://ucarecdn.com/5fcf06da-425b-40df-ae4f-2ab3b55bb3e7/164217313741_kiss_13kb.png]

Reject (якщо НЕ передавали виплату в квалі)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reject&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Відхилені"):

[image: https://ucarecdn.com/97af6922-c52c-4c42-aae3-721be4c576ac/164217330172_kiss_5kb.png]

Reject (якщо передавали виплату в квалі)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reject&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Відхилені" та "Дохід" (відмови)):

[image: https://ucarecdn.com/f206fb52-0233-469f-b3df-b19d19d0bf9f/164217347038_kiss_10kb.png]

## 4. Костилі та продвинуті налаштування. Частина 2.

Можливі тільки для чистих CPA та CPFD оферів.

## 4.1. Якщо в якості продажу партнер хоче, щоб це був не Approve, а, наприклад, FD або Квала:

4.1.1. У випадку, якщо це FD, то за подією "Перший депозит" в адмінці ми налаштовуємо постбек на Approve (у цьому випадку бажано передавати &payout=##CPA_AMOUNT##, але це не обовʼязково, можна замість ##CPA_AMOUNT## вказати 0).

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=approve&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Продажі" та "Дохід"):

[image: https://ucarecdn.com/2efe914b-9915-445e-a08b-9ef5c92c8877/164217313741_kiss_13kb.png]

4.1.2. У випадку, якщо це Квала, то за подією "Кваліфікація" в адмінці ми налаштовуємо постбек на Approve.

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=approve&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Продажі" та "Дохід"):

[image: https://ucarecdn.com/a8ae2e5d-0416-45a6-a699-1d72cc22fba8/164217313741_kiss_13kb.png]

4.1.3. Стандартним шляхом ми можемо налаштувати подію "Реєстрація".

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reg&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Ліди"):

[image: https://ucarecdn.com/dcdbc00c-7a3f-4569-9b07-c496b0f92ad5/164217303723_kiss_11kварвптвптb (1).png]

4.1.4. Стандартним шляхом ми можемо налаштувати подію Reject (якщо вказували 0 замість ##CPA_AMOUNT##, тут також треба замінити на 0).

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reject&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

Таким чином буде відображено в Keitaro (додається значення в стовпці "Відхилені" та "Дохід" (відмови)):

[image: https://ucarecdn.com/2eb6b253-d752-4ecd-a2e3-d8f5ceff1d87/164217347038_kiss_10kb.png]
