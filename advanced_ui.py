import msvcrt as msvcrt
from typing import Literal, Sequence, overload
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
    @overload
    @staticmethod
    def radio[T](elementos: Sequence[T], retornar_indice: Literal[False]=False) -> T: ...

    @overload
    @staticmethod
    def radio[T](elementos: Sequence[T], retornar_indice: Literal[True]) -> int: ...

    @staticmethod
    def radio[T](elementos: Sequence[T], retornar_indice: bool=False) -> T | int:
        """Garante que o usuário vai selecionar apenas um elemento."""
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
                if retornar_indice:
                    return focus
                return elementos[focus]
            
            print(f"\033[{height}A", end='')
    
    @overload
    @staticmethod
    def radio_many[T](elementos: Sequence[T], retornar_indices: Literal[False]=False) -> list[T]: ...

    @overload
    @staticmethod
    def radio_many[T](elementos: Sequence[T], retornar_indices: Literal[True]) -> list[int]: ...

    @staticmethod
    def radio_many[T](elementos: Sequence[T], retornar_indices: bool=False) -> list[T] | list[int]:
        """Permite o usuário marcar e selecionar vários elementos. Para selecionar: Espaço; Para confirmar a operação: Enter."""
        height = len(elementos)
        focus = 0
        marked: list[T] = []
        marked_indexes: list[int] = []
        while True:
            for i, elemento in enumerate(elementos):

                if i == focus and i in marked_indexes:
                    print(f'[-] \033[33m{elemento}\033[0m')
                elif i == focus:
                    print(f'[+] \033[33m{elemento}\033[0m')
                elif i in marked_indexes:
                    print(f'[+] {elemento}')
                else:
                    print(f"[ ] {elemento}")
            
            key = msvcrt.getch()
            if key == b'\xE0': # tecla especial (pode ser seta)
                focus = max(0, min(focus + map_vertical_arrow(), height - 1))
            elif key == b'\x20': # Espaço
                if focus in marked_indexes:
                    marked_indexes.remove(focus)
                    marked.remove(elementos[focus])
                else:
                    marked_indexes.append(focus)
                    marked.append(elementos[focus])
            elif key == b'\r': # Enter
                if retornar_indices:
                    return marked_indexes
                return marked
            
            print(f"\033[{height}A", end='')

    @staticmethod
    def confirmar(inverter: bool=False) -> bool:
        """O usuário precisa selecionar "Sim" ou "Não". Se selecionar Sim, a função retorna True. Se não, False.

        Ao definir o argumento `inverter` como True, o "Não" vira a primeira opção da escolha. Isso pode tornar o código menos problemático quando a confirmação é aplicada em uma ação sensível.
        """
        
        if UI.radio(("Sim", "Não") if not inverter else ("Não", "Sim")) == 'Sim':
            return True
        return False

    
    # TODO: Implementar um input com sugestões
    @staticmethod
    def search(prompt: str, suggestions: Sequence[str]) -> str: ...