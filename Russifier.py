from azdk.azdkdb import AzdkCmd
from azdk.azdksocket import PDSServerCommands, AzdkServerCommands, AzdkServerCmd, PDSServerCmd
from AzdkCommands import AzdkCommands


def Russifier_call(command):

    if isinstance(command, AzdkCmd):
        match command.code:
            case AzdkCommands.RESTART.value:
                return "Рестарт процессора"
            case AzdkCommands.RESET.value:
                return "Сброс установок"
            case AzdkCommands.DATE.value:
                return "Установка времени и даты"
            case AzdkCommands.REGISTR.value:
                return "Установка регистра АЗДК"
            case AzdkCommands.SET_FLAGS.value:
                return "Установка флагов управ."
            case AzdkCommands.CHANGE_FLAGS.value:
                return "Изменение флагов управ."
            case AzdkCommands.ANGL_SPEED_KA.value:
                return "Установка ск.движ. КА"
            case AzdkCommands.ANGL_SPEED.value:
                return "Установка угл.скор."
            case AzdkCommands.DURATION_OF_ACCUMULATION.value:
                return "Установка длит. накопления"
            case AzdkCommands.SCREEN_GEOMETRY.value:
                return "Установка геометрии кадра"
            case AzdkCommands.FPY_FLAGS.value:
                return "Установка режимов ФПУ"
            case AzdkCommands.SET_PARAMS.value:
                return "Установка параметров"
            case AzdkCommands.SET_SK_KA.value:
                return "Установка СК КА"
            case AzdkCommands.CURTAIN.value:
                return "Переключить шторку"
            case AzdkCommands.PELTIER.value:
                return "Переключить Пельтье"
            case AzdkCommands.STATE.value:
                return "Запрос слова состояния"
            case AzdkCommands.GET_AZDK_REGISTR.value:
                return "Чтение регистра АЗДК"
            case AzdkCommands.GET_ANGLE_SPEED.value:
                return "Чтение угл.скор."
            case AzdkCommands.GET_ANGLE_SPEED_MODEL.value:
                return "Чтение угл.ск.модели"
            case AzdkCommands.GET_LAST_QUAT.value:
                return "Чтение послед. кватер."
            case AzdkCommands.GET_DATE_TIME.value:
                return "Чтение времени и даты"
            case AzdkCommands.GET_LIST_FOTO.value:
                return "Чтение списка фотоц."
            case AzdkCommands.GET_FRAME.value:
                return "Чтение кадра"
            case AzdkCommands.GET_SUBSCREEN.value:
                return "Чтение субкадра"
            case AzdkCommands.GET_WINDOWS.value:
                return "Чтение окон"
            case AzdkCommands.STATISTICS.value:
                return "Статистика"
            case AzdkCommands.GET_PARAMS.value:
                return "Чтение параметров"
            case AzdkCommands.GET_FOCUS_OBJECT.value:
                return "Чтение целевого объекта"
            case AzdkCommands.GET_LIST_NON_STARS.value:
                return "Чтение списка не-звезд"
            case AzdkCommands.SET_SPEED_RS485.value:
                return "Установка скорости RS485"
            case AzdkCommands.SET_SPEED_CAN.value:
                return "Установка скорости CAN"
            case AzdkCommands.STANDBY_MODE.value:
                return "Режим ожидания"
            case AzdkCommands.AUTO_MODE.value:
                return "Режим автономной работы"
            case AzdkCommands.COMMAND_MODE.value:
                return "Режим работы по командам"
            case AzdkCommands.CALIB_DARK_CURRENT_MOD.value:
                return "Режим калибровки темнового тока"
            case AzdkCommands.CALIB_MEMS_GIRO_MOD.value:
                return "Режим калибровки MEMS-гироскопа"
            case AzdkCommands.GET_RAW_FRAME_MODE.value:
                return "Режим чтения сырых кадров"
            case AzdkCommands.FRAME_AVERAGE_MODE.value:
                return "Режим усреднения кадра"
            case AzdkCommands.SAVE_ALL_DATA_FLASH.value:
                return "Запись всех данных в FLASH"
            case AzdkCommands.SAVE_PROPERTIES_FLASH.value:
                return "Сохранение настроек в FLASH"
            case AzdkCommands.GET_DATA.value:
                return "Чтение данных"
            case AzdkCommands.SAVE_DATA.value:
                return "Запись данных"
            case AzdkCommands.GET_FW_VERSION.value:
                return "Чтение версии ПО"
            case AzdkCommands.UPDATE_SOFT.value:
                return "Обновление ПО"
            case AzdkCommands.SET_NUMBER_AZDK.value:
                return "Установка номера устройства"
            case AzdkCommands.OVERWRITING_SOFT.value:
                return "Запись ПО пошагово (+стирание)"
            case AzdkCommands.RETURN_TO_LOADER.value:
                return "Возвращение к загручику"
            case AzdkCommands.PROPERTIES_NOTIFICATION.value:
                return "Настройка оповещений"
    elif isinstance(command, AzdkServerCmd):
        match command.code:
            case AzdkServerCommands.SCMD_HELP.value:
                return "Cписок команд"
            case AzdkServerCommands.DEVICE_CMD.value:
                return "Отправка команды АЗДК-1 с параметрами"
            case AzdkServerCommands.SET_MODE.value:
                return "Переключает разные режимы отображения и рассылки информации"
            case AzdkServerCommands.GET_SERIALPORT_LIST.value:
                return "Получение списка последовательных портов"
            case AzdkServerCommands.GET_RS_PORT.value:
                return "Номер порта для RS485"
            case AzdkServerCommands.GET_CAN_PORT.value:
                return "Номер порта для CAN"
            case AzdkServerCommands.GET_TRACE_PARAM.value:
                return "Значение отслеживаемого параметра"
            case AzdkServerCommands.GET_TP_LIST.value:
                return "Список параметров отслеживания"
            case AzdkServerCommands.GET_DEVICE_INFO.value:
                return "Данные об устройстве"
            case AzdkServerCommands.SET_LOG_TEMPLATE.value:
                return "Изменение шаблона имени файла журнала"
            case AzdkServerCommands.GET_VERSION.value:
                return "Получить версию программы"
    elif isinstance(command, PDSServerCmd):
        match command.code:
            case PDSServerCommands.GET_VERSION.value:
                return "Получить версию приложения"
            case PDSServerCommands.GET_FRAME.value:
                return "Получить кадр буфера экрана"
            case PDSServerCommands.SET_RANDOM_MODE.value:
                return "Установить случайных изменений ориентации и угловой скорости"
            case PDSServerCommands.GET_STATE.value:
                return "Получить состояние"
            case PDSServerCommands.SET_STATE.value:
                return "Установить состояние"
            case PDSServerCommands.GET_ORIENT.value:
                return "Получить ориентацию (GCRS)"
            case PDSServerCommands.SET_ORIENT.value:
                return "Установить ориентацию (GCRS)"
            case PDSServerCommands.GET_POS.value:
                return "Получить положение аппарата (GCRS)"
            case PDSServerCommands.SET_POS.value:
                return "Установить положение аппарата (GCRS)"
            case PDSServerCommands.GET_ANGVEL.value:
                return "Получить угловую скорость (GCRS)"
            case PDSServerCommands.SET_ANGVEL.value:
                return "Установить угловую скорость (GCRS)"
            case PDSServerCommands.GET_POINT_SETTINGS.value:
                return "Получить настройки точек"
            case PDSServerCommands.SET_POINT_SETTINGS.value:
                return "Задать настройки для точек"
            case PDSServerCommands.GET_BACKGROUNDS.value:
                return "Получить описание фоновой засветки"
            case PDSServerCommands.SET_BACKGROUND.value:
                return "Установить фоновую засветку"
            case PDSServerCommands.GET_TEO_POS.value:
                return "Получить описание фоновой засветки"
            case PDSServerCommands.SET_TEO_POS.value:
                return "Установить фоновую засветку"
            case PDSServerCommands.GET_FOCUS.value:
                return "Получить фокус (масштабный фактор)"
            case PDSServerCommands.SET_FOCUS.value:
                return "Установить фокус (масштабный фактор)"
            case PDSServerCommands.SET_CONN_NAME.value:
                return "Поименовать соединение"
    return ""


def Russifier_answer(command):
    pass