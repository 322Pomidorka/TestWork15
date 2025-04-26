Необходыми 2 базы
   * основная db_name
   * тестовая db_name_test

.env:
  #database
  DB_LB_PORT=5432
  DB_LB_HOST=bd_host
  POSTGRES_DB=db_name
  DB_USER=user
  DB_PASSWORD=pass
  
  #auth
  SECRET_KEY=sercret_key
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30

Запуск через docker-compose:
  * в .env меняем DB_LB_HOST=db
  * запускаем в папке с docker-compose.yml: docker-compose up -d --build
