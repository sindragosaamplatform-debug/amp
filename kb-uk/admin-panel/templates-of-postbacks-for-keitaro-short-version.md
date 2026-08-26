# Шаблони постбеків Keitaro (short version)
URL: https://help.aff.ltd/uk/admin-panel/templates-of-postbacks-for-keitaro-short-version
Category: ⚙️ Адмін-панель
Section: Постбеки
Summary: Список основних шаблонів постбеків для трекера Keitaro/Кейтаро.
Updated: 1 рік тому

## 1. Шаблони для CPA і CPFD оферів

1.1. Квала (не передаємо виплату за гравця)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=lead&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

1.2. Approve

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=approve&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

1.3. Reject (НЕ передавали виплату в квалі)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reject&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

## 2. Шаблони для RS оферів

2.1. Рега (Можна налаштовувати тільки у випадку, якщо івент FD не був налаштований)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reg&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

2.2. FD (Саме перший депозит; можна налаштовувати тільки у випадку, якщо івент Рега не був налаштований)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=dep&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

2.3. RS дохід

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##RS_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

## 3. Шаблони для Гібридних оферів

3.1. Квала (не передаємо виплату за гравця)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=lead&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

3.2. Approve

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=approve&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##CPA_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]

3.3. Reject (НЕ передавали виплату в квалі)

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=reject&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&from=[ПартнерськаПрограма]

3.4. RS дохід

/postback?subid=##CLICK_ID##&tid=##POSTBACK_ID##&status=rebill&lead_status=reg,dep,lead&sale_status=approve,rebill&rejected_status=reject&payout=##RS_AMOUNT##&currency=rub,usd,eur&from=[ПартнерськаПрограма]
