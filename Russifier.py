from azdk.azdkdb import AzdkDB, AzdkCmd
from azdk.azdksocket import AzdkSocket, PDSServerCmd, AzdkServerCmd, call_azdk_cmd , PDSServerCommands, AzdkServerCommands
from AzdkCommands import AzdkCommands


def Russifier(command):

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
            case AzdkCommands.REED_AZDK_REGISTR.value:
                return "Чтение регистра АЗДК"
            case AzdkCommands.REED_ANGLE_SPEED.value:
                return "Чтение угл.скор."
            case AzdkCommands.REED_ANGLE_SPEED_MODEL.value:
                return "Чтение угл.ск.модели"
            case AzdkCommands.REED_LAST_QUAT.value:
                return "Чтение послед. кватер."
            case AzdkCommands.REED_DATE_TIME.value:
                return "Чтение времени и даты"
            case AzdkCommands.REED_LIST_FOTO.value:
                return "Чтение списка фотоц."
            case AzdkCommands.REED_FRAME.value:
                return "Чтение кадра"
            case AzdkCommands.REED_SUBSCREEN.value:
                return "Чтение субкадра"
            case AzdkCommands.REED_WINDOWS.value:
                return "Чтение окон"
            case AzdkCommands.STATISTICS.value:
                return "Статистика"
            case AzdkCommands.REED_PARAMS.value:
                return "Чтение параметров"
            case AzdkCommands.REED_FOCUS_OBJECT.value:
                return "Чтение целевого объекта"
            case AzdkCommands.REED_LIST_NON_STARS.value:
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
            case AzdkCommands.REED_RAW_FRAME_MODE.value:
                return "Режим чтения сырых кадров"
            case AzdkCommands.FRAME_AVERAGE_MODE.value:
                return "Режим усреднения кадра"
            case AzdkCommands.SAVE_ALL_DATA_FLASH.value:
                return "Запись всех данных в FLASH"
            case AzdkCommands.SAVE_PROPERTIES_FLASH.value:
                return "Сохранение настроек в FLASH"
            case AzdkCommands.REED_DATA.value:
                return "Чтение данных"
            case AzdkCommands.SAVE_DATA.value:
                return "Запись данных"
            case AzdkCommands.REED_SOFT_VERSION.value:
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
    return ""