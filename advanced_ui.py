import msvcrt_linux as msvcrt
from typing import Sequence
from string import ascii_letters, digits, punctuation

def read_keyboard():
    while True:
        for _ in range(4):
            key = msvcrt.getch()
            if key == b'\xE0':
                key = msvcrt.getch()
            print(key)
        
        if input("Não digite nada para continuar: ") != "":
            break

def map_vertical_arrow():
    key = msvcrt.getch() # isso não pedir outra tecla, só vai pegar o ue já estava no buffer
    return -1 if key == b'H' else (1 if key == b'P' else 0)

def selecionar():
    elementos = [
        "Arroz",
        "Feijão",
        "Farofa",
        "Carne de porco",
    ]
    selected = 0
    while True:
        for i, elemento in enumerate(elementos):
            if i == selected:
                print(f'[•] \033[33m{elemento}\033[0m')
            else:
                print(f"[ ] {elemento}")

        if msvcrt.getch() == b'\xE0':
            selected += map_vertical_arrow()
        up = len(elementos)
        print(f'\033[{up}A', end='')

inputable = ascii_letters + digits + punctuation
class UI:
    @staticmethod
    def radio[T](elementos: Sequence[T]) -> T:
        height = len(elementos)
        
        focus = 0
        while True:
            for i, elemento in enumerate(elementos):
                if i == focus:
                    print(f'[•] \033[33m{elemento}\033[0m')
                else:
                    print(f"[ ] {elemento}")
            
            key = msvcrt.getch()
            if key == b'\xE0':
                focus = max(0, min(focus + map_vertical_arrow(), height - 1))
            elif key == b'\r':
                return elementos[focus]
            
            print(f"\033[{height}A", end='')
    
    # TODO: Implementar um input com sugestões
    @staticmethod
    def search(prompt: str, suggestions: Sequence[str]) -> str: ...

print(
    "Item selecionado:", UI.radio([
        "Arroz",
        "Feijão",
        "Farofa",
        "Carne de porco",
    ])
)