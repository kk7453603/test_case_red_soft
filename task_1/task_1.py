from datetime import datetime


def check_flight_status(schedule_time, actual_time):
    try:
        schedule_datetime = datetime.strptime(schedule_time, "%H:%M")
        actual_datetime = datetime.strptime(actual_time, "%H:%M")
    except Exception as e:
        print("Неправильный формат ввода времени прибытия. Пожалуйста используйте формат ввода: HH:MM")
        return False

    if actual_datetime < schedule_datetime:
        difference = schedule_datetime - actual_datetime
        return "Самолет прилетел раньше на {}".format(difference)
    elif actual_datetime > schedule_datetime:
        difference = actual_datetime - schedule_datetime
        return "Самолет опаздывает на {}".format(difference)
    else:
        return "Самолет прилетел вовремя"



schedule_time = input("Введите время прибытия по расписанию (в формате ЧЧ:ММ): ")
actual_time = input("Введите фактическое время прибытия (в формате ЧЧ:ММ): ")


result = check_flight_status(schedule_time, actual_time)

if result:
    print(result)
