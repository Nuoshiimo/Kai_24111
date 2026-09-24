import random
import string

categories = [string.ascii_letters, string.digits, string.punctuation]
password = ""

print("Добро пожаловать в программу генерации паролей!")
print("Выберите сложность пароля: \n 1) Легкий \n 2) Средний \n 3) Сложный")
user_choice = int(input("Введите сложность: "))
match user_choice:
    case 1: length = 5
    case 2: length = 7
    case 3: length = 9
    case _:
        print("Такого пункта нет")
        exit()
for i in range(length):
    cat = random.choice(categories)
    password += random.choice(cat)

print("Ваш пароль:", password)

