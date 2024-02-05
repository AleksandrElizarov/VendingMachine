void setup() {
  Serial.begin(9600);  // Для вывода информации на монитор порта
  Serial1.begin(9600, SERIAL_8N2); // Настройка Serial1 для взаимодействия с купюроприемником
  delay(1000); // Задержка для стабилизации вывода
  // Отправка последовательности байтов для включения купюроприемника
  
  uint8_t anable_command[] = {127, 128, 1, 10, 63, 130};
  Serial1.write(anable_command, sizeof(anable_command));
  delay(1000); // Задержка для стабилизации вывода

  pinMode(LED_BUILTIN, OUTPUT);

  
}

void loop() {
  // Ваш код для обработки данных с купюроприемника

  

  //byte poll_command[] = {127, 128, 1, 7, 18, 2};
  //Serial1.write(poll_command, sizeof(poll_command));

  Serial.print("Hello");

  uint8_t ser_num__command[] = {127, 128, 1, 12, 43, 130};
  Serial1.write(ser_num__command, sizeof(ser_num__command));

  // Пример: чтение данных с Serial1 и вывод на монитор порта
  while (Serial1.available()) {
    char data = Serial1.read();
    Serial.print(data);
  }

  // Пример: чтение данных с Serial1 и вывод на монитор порта
  while (Serial.available()) {
    digitalWrite(LED_BUILTIN, HIGH);  // turn the LED on (HIGH is the voltage level)
    delay(1000);                      // wait for a second
    digitalWrite(LED_BUILTIN, LOW);   // turn the LED off by making the voltage LOW
    delay(1000); 
    Serial.print("data");                     // wait for a second
  }

  delay(200); // Задержка для стабилизации вывода
}
