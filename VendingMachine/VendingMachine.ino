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

    // Печать ответа в терминале через UART0
    Serial.print("Response from bill acceptor: ");
    for (int i = 0; i < sizeof(poll_command); i++) {
      Serial.print(receivedResponse[i]);
      Serial.print(" ");
    }
    Serial.println(); // Печать новой строки
  }
  
  delay(1000); // Пауза перед следующей отправкой команды
}
