import msvcrt



def read_keyboard():
    while True:
        for _ in range(3):
            key = msvcrt.getch()
            print(key)
        
        if input("Não digite nada para continuar: ") != "":
            break

read_keyboard()