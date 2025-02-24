**Основные технологии**

Pygame — для графического интерфейса и обработки игровой логики.

SQLite — для хранения данных о пользователях, их уровнях и очках.

OS и Random — для работы с файловой системой и случайными значениями.

**Структура проекта**

1. Инициализация

Происходит настройка экрана, создание подключения к базе данных, определение основных цветов и шрифтов, а также задание глобальных параметров, таких как поле зрения (FOV) и дальность обзора (VIEW_DISTANCE).

2. База данных

Подключение к SQLite и создание таблицы players (если она отсутствует).

Проверка наличия игрока в базе, добавление нового при необходимости.

3. Основные классы

Класс DroneОтвечает за управление дроном, его движение, изменение размера в зависимости от высоты и подсчет очков.

Класс ObstacleСоздает препятствия, проверяет столкновения с дроном. При столкновении ниже допустимой высоты происходит "авария".

Класс CheckPointЯвляется положительным объектом, при пересечении которого начисляются очки.

Класс TurbulenceДобавляет эффект случайного отклонения дрона при попадании в зону турбулентности.

4.4. Интерфейс и игровые режимы

Главное меню с выбором режимов: уровни, свободный режим, лидерборд.

Лидерборд с отображением лучших игроков.

Ввод никнейма при запуске игры для сохранения прогресса.
