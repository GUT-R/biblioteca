from random import choice
from string import ascii_lowercase, digits
from datetime import date

GLOBAL_DATABASE = {
    'USUARIOS': [],
    'QUERYS': {
        'U_ID': {},
        'U_NOME': {}
    }
}

agorinha = date.today

type Titulo = str
type BibliotecaNome = str

def gerar_id() -> str:
    return ''.join(choice(ascii_lowercase + digits) for _ in range(3))


class Usuario:
    def __init__(self, nome: str):
        self.nome = nome
        self.id = gerar_id()
        self.livros: dict[Titulo, Livro] = {}
        self.bibliotecas: dict[BibliotecaNome, Biblioteca] = {}
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        GLOBAL_DATABASE['USUARIOS'].append(self)
        GLOBAL_DATABASE['QUERYS']['USUARIOS_NOME'] = nome
        GLOBAL_DATABASE['QUERYS']['USUARIOS_ID'] = self.id


    def cadastrar_biblioteca(self, nome: BibliotecaNome):
        if nome in self.bibliotecas.keys():
            raise ValueError('Já existe uma biblioteca com esse nome.')

        biblioteca = Biblioteca(nome=nome, pertencente=self)
        self.bibliotecas[nome] = biblioteca
        return biblioteca

    def cadastrar_livro(self, titulo: Titulo, conteudo: list[str]):
        if titulo not in self.livros.keys():
            self.livros[titulo] = Livro(titulo=titulo, conteudo=conteudo, autor=self)

    def modificar_livro(self, livro: Livro, pagina: int, conteudo: str):
        livro.modificar_pagina(self, pagina, conteudo)
    
    def __setattr__(self, name, value):
        if name == 'id':
            raise ValueError('Num pode modificar ID, imbecil.')
        
        object.__setattr__(self, name, value)
        """Implement setattr(self, name, value)."""
        self.data_de_atualizacao = agorinha()

class Biblioteca:
    def __init__(self, nome: str, pertencente: Usuario):
        self.nome = nome
        self.pertencente = pertencente
        self.ids_autorizados = {pertencente.id}
        self.estantes: list[set[Livro]] = {}

    def mostrar_titulos(self):
        for livro in self.livros:
            print(livro.titulo)

    def autorizar_usuario(self, usuario: Usuario):
        self.ids_autorizados.add(usuario.id)
    
    def __setattr__(self, name, value):
        if name in ('nome', 'pertencente', 'ids_autorizados', 'estantes'):
            raise PermissionError('Você precisa estar efetuando essa ação como um usuário válido.')
        object.__setattr__(self, name, value)
        """Implement setattr(self, name, value)."""
        self.data_de_atualizacao = agorinha()



class Livro:
    def __init__(self, titulo: Titulo, conteudo: list[str], autor: Usuario):
        self.titulo = titulo
        self.conteudo = conteudo
        self.autor = autor
        self.ids_autorizados = {autor.id}
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        self.__usuario_alterando = False # Verifica se há um usuário com permissão realizando alguma ação no momento 

    def mostrar_conteudo(self, pagina: int):
        if not 0 <= pagina < len(self.conteudo):
            raise ValueError(f'Índice de página inválido: {pagina}')

        print(self.conteudo[pagina])

    def modificar_pagina(self, usuario: Usuario, pagina: int, novo_conteudo: str):
        if not usuario.id in self.ids_autorizados:
            raise PermissionError('Você não tem permissão para modificar esse livro')
        
        self.__usuario_alterando = True
        self.conteudo[pagina] = novo_conteudo

        self.__usuario_alterando = False

    def __setattr__(self, name, value):
        if not self.__usuario_alterando:
            raise PermissionError('Você precisa estar efetuando essa ação como um usuário válido.')
        object.__setattr__(self, name, value)
        """Implement setattr(self, name, value)."""
        self.data_de_atualizacao = agorinha()


class UsuarioGUI(Usuario):
    def __init__(self):
        print('=== REGISTRE-SE ===')
        nome = input('Nome: ')
        print('===   FIM :D    ===')

        super().__init__(nome)
    def criar_uma_biblioteca(self):
        print('=== CRIE UMA BIBILIOTECA ===')

        biblioteca = self.cadastrar_biblioteca(input('NOME DA SUA BIBILIOTECA: '))

        if input('Adicionar usuário? [y/N]: ').strip()[:3].lower() == 'sim':
            while True:
                nome_ou_id = input('Insira o nome (ou o ID): ').strip()
                query = GLOBAL_DATABASE['QUERYS']
                usuario: Usuario = (
                    query['U_ID'].get(nome_ou_id) or
                    query['U_NOME'].get(nome_ou_id)
                )

                if usuario is None:
                    raise ValueError('Usuário não existe.')

                biblioteca.autorizar_usuario(usuario)

                if input('Adicionar outro? [y/N]: ').strip()[:3].lower() != 'yes':
                    break
        
