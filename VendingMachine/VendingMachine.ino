void setup() {
  Serial.begin(9600);      // Настройка UART0 для взаимодействия с терминалом
  Serial1.begin(9600);     // Настройка UART1 для взаимодействия с купюроприемником
}

void loop() {
  byte poll_command[] = {127, 128, 1, 7, 18, 2};
  
  // Отправка команды в купюроприемник через UART1
  Serial1.write(poll_command, sizeof(poll_command));

  // Ожидание ответа от купюроприемника
  delay(100); // Подождите некоторое время для передачи данных
  
  // Проверка, есть ли достаточно байт для чтения ответа
  if (Serial1.available() >= sizeof(poll_command)) {
    byte receivedResponse[sizeof(poll_command)];
    Serial1.readBytes(receivedResponse, sizeof(poll_command));

    // Отправка ответа в терминал через UART0 с использованием Serial.write
    Serial.write("Response from bill acceptor: ");
    Serial.write(receivedResponse, sizeof(poll_command));
    Serial.write("\n"); // Перевод строки
  }
  
  delay(1000); // Пауза перед следующей отправкой команды
}
