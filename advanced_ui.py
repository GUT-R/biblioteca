import os
if os.name == "nt":
    import msvcrt
else:
    import msvcrt_linux as msvcrt
from typing import Literal, Sequence, overload, Optional
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

UP_ARROW = "↑"
DOWN_ARROW = "↓"


def map_vertical_arrow():
    """Mapeia as setas do teclado para valores numéricos: ↑ = -1 e ↓ = 1."""
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
    def radio[T](elementos: Sequence[str], retornar_indice: Literal[False]=False) -> str: ...

    @overload
    @staticmethod
    def radio[T](elementos: dict[str, T], retornar_indice: Literal[False]) -> T: ...
    
    @overload
    @staticmethod
    def radio[T](elementos: Sequence[str] | dict[str, T], retornar_indice: Literal[True]) -> int: ...
    

    @staticmethod
    def radio[T](elementos: Sequence[str] | dict[str, T], retornar_indice: bool=False) -> str | T | int:
        """Garante que o usuário vai selecionar apenas um elemento."""
        height = len(elementos)
        if height == 0:
            raise Exception("Não é possível abrir o menu sem uma sequência de elementos. O recomendado é pelo menos 2")
        
        focus = 0
        values = tuple[T, ...]()
        if isinstance(elementos, dict):
            values = tuple(elementos.values())
        
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
                if isinstance(elementos, dict):
                    return values[focus] # Extrai o elemento a partir do label extraido com a posição
                return elementos[focus]
            
            print(f"\033[{height}A", end='')
    
    @overload
    @staticmethod
    def radio_many[T](elementos: Sequence[str], retornar_indices: Literal[False]=False) -> list[str]: ...

    @overload
    @staticmethod
    def radio_many[T](elementos: Sequence[str] | dict[str, T], retornar_indices: Literal[True]) -> list[int]: ...

    @overload
    @staticmethod
    def radio_many[T](elementos: dict[str, T], retornar_indices: Literal[False]=False) -> list[T]: ...

    @staticmethod
    def radio_many[T](elementos: Sequence[str] | dict[str, T], retornar_indices: bool=False) -> list[str] | list[T] | list[int]:
        """Permite o usuário marcar e selecionar vários elementos. Para selecionar: Espaço; Para confirmar a operação: Enter."""
        height = len(elementos)
        focus = 0
        marked_indexes: list[int] = []

        values = tuple[T, ...]()
        if isinstance(elementos, dict):
            values = tuple(elementos.values())

        while True:
            for i, elemento in enumerate(elementos):
                if i == focus:
                    if i in marked_indexes:
                        print(f'[-] \033[33m{elemento}\033[0m')
                    else:
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
                else:
                    marked_indexes.append(focus)
            elif key == b'\r': # Enter
                if retornar_indices:
                    return marked_indexes
                
                if isinstance(elementos, dict):
                    return [values[marked_i] for marked_i in marked_indexes]
                return [elementos[marked_i] for marked_i in marked_indexes]
            
            print(f"\033[{height}A", end='')

    @staticmethod
    def confirmar(inverter: bool=False) -> bool:
        """O usuário precisa selecionar "Sim" ou "Não". Se selecionar Sim, a função retorna True. Se não, False.

        Ao definir o argumento `inverter` como True, o "Não" vira a primeira opção da escolha. Isso pode tornar o código menos problemático quando a confirmação é aplicada em uma ação sensível.
        """
        
        if UI.radio(("Sim", "Não") if not inverter else ("Não", "Sim")) == 'Sim':
            return True
        return False

    @staticmethod
    def inteiro(message: str, _min: Optional[int]=None, default: int=0, _max: Optional[int]=None):
        """Mostra um selecionador de números. O usuário deverá utilizar a tecla ↑ para adicionar 1, ↓ para subtrair 1 e **enter** para concluir."""
        x = default
        running = True
        while running:
            print(f"\033[1G\033[2K{message} \033[33m{x}\033[0m", end='', flush=True)
            k = msvcrt.getch()
            if k == b'\xE0':
                r = x - map_vertical_arrow()
                if not ((_min is not None and _min > r) or (_max is not None and _max < r)):
                    x = r
            elif k == b'\r':
                running = False
        return x
    
    @staticmethod
    def inteiros(data: dict[str, int | tuple[Optional[int], int, Optional[int]]]):
        """Mostra uma interface de configuração de inteiros.

        O usuário pode navegar entre os elementos utilizando as setas verticais,
        pressionar Enter para editar o elemento selecionado e Esc para finalizar
        a configuração.

        O método recebe um dicionário em que cada chave representa o label de um
        elemento e cada valor representa seu número padrão.

        Para definir limites mínimo e máximo, o valor deve ser uma tupla no formato
        (min, default, max). Os limites podem ser None para indicar ausência de
        restrição naquele extremo.

        A edição dos valores é realizada por meio de UI.inteiro. Consulte sua
        documentação para obter mais detalhes.

        Retorna:
        dict: Um dicionário contendo os labels e seus respectivos valores
        atualizados.
        """
        d: dict[int, tuple[str, tuple[Optional[int], int, Optional[int]]]] = dict(enumerate((
            (k, (None, v, None) if not isinstance(v, tuple) else v) for k, v in data.items()
        )))
        height = len(d)
        
        focus = 0
        while True:
            for i, kv in d.items():
                k, v = kv
                default = v[1]
                if focus == i:
                    print(f"\033[33m{k} \033[90m{default}\033[0m")
                else:
                    print(f"{k} \033[90m{default}\033[0m")

            key = msvcrt.getch()
            if key == b'\xE0': # Tecla especial (pode ser seta)
                focus = max(0, min(focus + map_vertical_arrow(), height - 1))
            elif key == b'\r': # Enter
                elemento, v = d[focus]
                _min, default, _max = v
                print(f"\033[{height - focus}A", end="")
                x = UI.inteiro(elemento, _min, default, _max)
                d[focus] = (elemento, (_min, x, _max))
                print(f"\033[G{f'\033[{focus}A' if focus else ''}", end='')
                continue

            elif key == b'\x1B': # Esc
                return {k: v[1] for k, v in d.values()}
            
            print(f"\033[{height}A", end='')
    
    # TODO: Implementar um input com sugestões
    @staticmethod
    def search(prompt: str, suggestions: Sequence[str]) -> str: ...

if __name__ == "__main__":
    resultado = UI.inteiros(
        {
            "Month": (1, 1, 12),
            "Day": (1, 1, 31),
            "Year": (2000, 2000, 2026),
        }
    )
    print(resultado)