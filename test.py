from random import choice
from string import ascii_lowercase, digits

def gerar_id(n: int) -> str:
    return ''.join(choice(ascii_lowercase + digits) for _ in range(n))

def avaliar_colisoes(repeat: int):
    for _ in range(repeat):
        ids: set[str] = set()
        while True:
            id = gerar_id(4)
            if id == ids:
                break
            ids.add(id)
        print(f'Colisão após {len(ids) + 1} combinações')

avaliar_colisoes(10)
