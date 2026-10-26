from random import choice
from string import ascii_lowercase, digits
from datetime import date
from subprocess import run

GLOBAL_DATABASE = {
    'usuarios': [],
    'bibliotecas': [],
    'livros': [],
    'querys': {
        # U: Usuário
        # B: Biblioteca
        # L: Livro
        'U_ID': {},
        'B_ID': {},
        'L_ID': {},
        'U_NOME': {},
        'B_NOME': {},
        'L_NOME': {},
    }
}

agorinha = date.today

type Titulo = str
type BibliotecaNome = str
type ID = str
type UsuarioID = ID
type BibliotecaID = ID
type LivroID = ID

def gerar_id() -> ID:
    return ''.join(choice(ascii_lowercase + digits) for _ in range(8))


class Usuario:
    def __init__(self, nome: str):
        self.nome = nome
        self.id: UsuarioID = gerar_id()
        self.livros: set[LivroID] = {}
        self.bibliotecas: set[BibliotecaID] = {}
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        GLOBAL_DATABASE['usuarios'].append(self)
        GLOBAL_DATABASE['querys']['U_NOME'][nome] = self
        GLOBAL_DATABASE['querys']['U_ID'][self.id] = self

    def cadastrar_biblioteca(self, nome: BibliotecaNome):
        if GLOBAL_DATABASE['querys']['B_NOME'].get(nome, False):
            raise ValueError('Já existe uma biblioteca com esse nome.')

        biblioteca = Biblioteca(nome=nome, pertencente=self)
        self.bibliotecas[biblioteca.id] = biblioteca
        return biblioteca

    def cadastrar_livro(self, titulo: Titulo, conteudo: list[str]):
        livro: Livro = GLOBAL_DATABASE['querys']['L_NOME'].get(titulo)
        if livro:
            if livro.id in self.livros:
                raise ValueError('Você já possui um livro com esse nome.')
            raise ValueError('Esse livro já existe.')
        self.livros[titulo] = Livro(titulo=titulo, conteudo=conteudo, autor=self)

    def modificar_livro(self, livro: Livro, pagina: int, conteudo: str):
        livro.modificar_pagina(self, pagina, conteudo)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name != 'data_de_atualizacao':
            object.__setattr__(self, 'data_de_atualizacao', agorinha())


class Biblioteca:
    def __init__(self, nome: str, pertencente: Usuario):
        self.nome = nome
        self.id: BibliotecaID = gerar_id()
        self.pertencente = pertencente
        self.ids_autorizados = {pertencente.id}
        self.estantes: list[set[Livro]] = {}
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        GLOBAL_DATABASE['bibliotecas'].append(self)
        GLOBAL_DATABASE['querys']['B_ID'][self.id] = self
        GLOBAL_DATABASE['querys']['B_NOME'][nome] = self

    def mostrar_titulos(self):
        for livro in self.livros:
            print(livro.titulo)

    def remover_livro(self, livro_id: str, estantes: list[int] | None=None):
        for i in estantes:
            estante = self.estantes[i]
            estante.remove(livro_id)

    def autorizar_usuario(self, usuario: Usuario):
        self.ids_autorizados.add(usuario.id)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name != 'data_de_atualizacao':
            object.__setattr__(self, 'data_de_atualizacao', agorinha())


class Livro:
    def __init__(self, titulo: Titulo, conteudo: list[str], autor: Usuario):
        self.titulo = titulo
        self.id: LivroID = gerar_id()
        self.conteudo = conteudo
        self.autor = autor
        self.ids_autorizados = {autor.id}
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        GLOBAL_DATABASE['livros'].append(self)
        GLOBAL_DATABASE['querys']['L_ID'][self.id] = self
        GLOBAL_DATABASE['querys']['L_NOME'][titulo] = self

    def mostrar_conteudo(self, pagina: int):
        if not 0 <= pagina < len(self.conteudo):
            raise ValueError(f'Índice de página inválido: {pagina}')

        print(self.conteudo[pagina])

    def modificar_pagina(self, usuario: Usuario, pagina: int, novo_conteudo: str):
        if not usuario.id in self.ids_autorizados:
            raise PermissionError('Você não tem permissão para modificar esse livro')
        self.conteudo[pagina] = novo_conteudo

    def modificar_titulo(self, usuario: Usuario, novo_titulo: str):
        if usuario is not self.autor:
            raise PermissionError('Apenas o autor pode realizar essa ação')
        self.titulo = novo_titulo

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name != 'data_de_atualizacao':
            object.__setattr__(self, 'data_de_atualizacao', agorinha())


class UsuarioGUI(Usuario):
    def __init__(self):
        print('=== REGISTRE-SE ===')
        nome = input('Nome: ')
        print('===   FIM :D    ===')

        super().__init__(nome)
    def criar_uma_biblioteca(self):
        print('=== CRIE UMA BIBILIOTECA ===')

        biblioteca = self.cadastrar_biblioteca(input('nome da sua biblioteca: '))


        if input('Deseja autorizar mais usuários a modificar sua biblioteca? [y/N]: ').strip()[:3].lower() == 'sim':
            while True:
                nome_ou_id = input('Insira o nome (ou o ID): ').strip()
                querys = GLOBAL_DATABASE['querys']
                usuario: Usuario = (
                    querys['U_ID'].get(nome_ou_id) or
                    querys['U_NOME'].get(nome_ou_id)
                )

                if usuario is None:
                    raise ValueError('Usuário não existe.')

                biblioteca.autorizar_usuario(usuario)

                if input('Adicionar outro? [y/N]: ').strip()[:3].lower() != 'yes':
                    break

    def criar_um_livro(self):
        # TODO: Implementar um editor de texto integrado aproveitando a biblioteca Keyboard
        print('=== CRIAR LIVRO ===')
        print('Ainda não fiz um editor de texto integrado.')

        if input('Deseja continuar com bloco de notas? [s/N] ').strip()[:1].lower() != 's':
            return

        
        titulo = input('Titulo: ')
        run(rf'notepad.exe {__file__}\temp.txt')
        with open('temp.txt', 'r') as paginas:
            content = paginas.read().split('\n\n\n')

        self.cadastrar_livro(titulo, content)