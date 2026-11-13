// Настройки синхронизации между устройствами.
// Пока FIREBASE_URL пустой, приложение работает локально: данные хранятся только в браузере этого устройства.
window.CONFIG = {
  // Адрес Firebase Realtime Database, например:
  // "https://my-project-default-rtdb.europe-west1.firebasedatabase.app"
  FIREBASE_URL: "https://basketboyz-default-rtdb.firebaseio.com",
  // Название «комнаты». Придумайте длинное и неочевидное, оно работает как пароль.
  ROOM: "bb-PKFpTlj8SPCKoBr2ft6VT4-4",
  // Статистика ведётся только в часы встречи: по субботам с MEETING_START до MEETING_END.
  // Игры, завершённые в другое время или в другой день, считаются тренировкой и в статистику не попадают.
  MEETING_DAY: 6,          // день недели: 0 — воскресенье, 6 — суббота
  MEETING_START: "07:00",
  MEETING_END: "09:30",
  // Длительность игры в минутах для таймера.
  GAME_MINUTES: 7
};
