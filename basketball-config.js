// Настройки синхронизации между устройствами.
// Пока FIREBASE_URL пустой, приложение работает локально: данные хранятся только в браузере этого устройства.
window.CONFIG = {
  // Адрес Firebase Realtime Database, например:
  // "https://my-project-default-rtdb.europe-west1.firebasedatabase.app"
  FIREBASE_URL: "https://basketboyz-default-rtdb.firebaseio.com",
  // Название «комнаты». Придумайте длинное и неочевидное, оно работает как пароль.
  ROOM: "bb-PKFpTlj8SPCKoBr2ft6VT4-4",
  // Встреча идёт до этого времени. Игры, завершённые позже, в статистику не попадают.
  MEETING_END: "10:00",
  // Длительность игры в минутах для таймера.
  GAME_MINUTES: 7
};
