from random import choice
from string import ascii_lowercase, digits
from datetime import date
from subprocess import run
from typing import Iterable, Callable, Any, NoReturn

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

type Titulo = str         # type: ignore
type BibliotecaNome = str # type: ignore
type ID = str             # type: ignore
type UsuarioID = ID       # type: ignore
type BibliotecaID = ID    # type: ignore
type LivroID = ID         # type: ignore

def gerar_id() -> ID:
    return ''.join(choice(ascii_lowercase + digits) for _ in range(8))


class EmptyClass:
    def __init__(self):
        return None


class Usuario:
    def __init__(self, nome: str):
        self.nome = nome
        self.id: UsuarioID = gerar_id()
        self.livros: set[LivroID] = set()
        self.bibliotecas: set[BibliotecaID] = set()
        self.bibliotecas_externas: set[BibliotecaID] = set()
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        GLOBAL_DATABASE['usuarios'].append(self)
        GLOBAL_DATABASE['querys']['U_NOME'][nome] = self
        GLOBAL_DATABASE['querys']['U_ID'][self.id] = self

    def cadastrar_biblioteca(self, nome: BibliotecaNome):
        if GLOBAL_DATABASE['querys']['B_NOME'].get(nome, False):
            raise ValueError('Já existe uma biblioteca com esse nome.')

        biblioteca = Biblioteca(nome=nome, pertencente=self)
        self.bibliotecas.add(biblioteca.id)
        return biblioteca

    def cadastrar_livro(self, titulo: Titulo, conteudo: list[str]):
        livro_existente: Livro = GLOBAL_DATABASE['querys']['L_NOME'].get(titulo)
        if livro_existente:
            if livro_existente.id in self.livros:
                raise ValueError('Você já possui um livro com esse titulo.')
            raise ValueError('Esse livro já existe.')
        
        livro = Livro(titulo, conteudo, autor=self)
        self.livros.add(livro.id)
        return livro

    def adicionar_livro_a_biblioteca(self, livro_id: LivroID, biblioteca_id, estantes: Iterable[int]):
        biblioteca: Biblioteca | None = GLOBAL_DATABASE['querys']['B_ID'].get(biblioteca_id)
        if biblioteca is None:
            raise ValueError('Essa biblioteca não existe')

        biblioteca.adicionar_livro(self.id, livro_id, estantes)


    def modificar_livro(self, livro: 'Livro', pagina: int, conteudo: str):
        livro.modificar_pagina(self, pagina, conteudo)

    def __setattr__(self, name, value):
        EmptyClass.__setattr__(self, name, value)
        EmptyClass.__setattr__(self, 'data_de_atualizacao', agorinha())


class Biblioteca:
    @staticmethod
    def permitir_somente_usuario_autorizado(method: Callable[['Biblioteca'], Any | NoReturn]):
        def callback(self: 'Biblioteca', usuario_id: UsuarioID, *args, **kwargs):
            if usuario_id not in self.ids_autorizados:
                raise PermissionError('Você não tem permissão para modificar essa biblioteca.')
            return method(self, *args, **kwargs)
        return callback

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

    @permitir_somente_usuario_autorizado
    def adicionar_livro(self, livro_id: str, estantes: Iterable[int]):
        for i in estantes:
            estante = self.estantes[i]
            estante.add(livro_id)
    
    @permitir_somente_usuario_autorizado
    def remover_livro(self, livro_id: str, estantes: Iterable[int]):
        for i in estantes:
            estante = self.estantes[i]
            estante.remove(livro_id)
    
    @permitir_somente_usuario_autorizado
    def renomear_biblioteca(self, novo_nome: str):
        self.nome = novo_nome

    @permitir_somente_usuario_autorizado # somente um usuário autorizado pode autorizar outros usuários
    def autorizar_usuario(self, usuario: Usuario):
        self.ids_autorizados.add(usuario.id)
        if self.id not in usuario.bibliotecas:
            usuario.bibliotecas_externas.add(self.id)

    def __setattr__(self, name, value):
        EmptyClass.__setattr__(self, name, value)
        EmptyClass.__setattr__(self, 'data_de_atualizacao', agorinha())


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
        EmptyClass.__setattr__(self, name, value)
        EmptyClass.__setattr__(self, 'data_de_atualizacao', agorinha())


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

        livro = self.cadastrar_livro(titulo, content)
        
        if input('Adicionar livro a alguma biblioteca? [y/N] ').strip()[:1].lower() == 'y':
            self.GUI_adicionar_livro_a_biblioteca(livro)
        
        return livro

    

    def GUI_adicionar_livro_a_biblioteca(self, livro: Livro):
        bibliotecas_do_usuario: list[Biblioteca] = [GLOBAL_DATABASE['querys']['B_ID'][_id] for _id in self.bibliotecas + self.bibliotecas_externas]

        print('==== SUAS BIBLIOTECAS ====')
        for i, biblioteca in enumerate(bibliotecas_do_usuario):
            print(f'[{i + 1}] {biblioteca.nome}')
        print('==========================')
        while True:
            n = int(input('[*] Insira o número da biblioteca > '))
            if 0 < n < len(bibliotecas_do_usuario):
                break
            print('[!] NÚMERO INVÁLIDO')
        biblioteca_selecionada = bibliotecas_do_usuario[n - 1]

        print('==== ESTANTES ====')
        for i in range(len(biblioteca_selecionada.estantes) - 1):
            livros_quantidade = len(biblioteca_selecionada.estantes[i])                
            print(f'[{i}] |', "/" * livros_quantidade, end=' ')

            if livros_quantidade > 0:
                print(f'({livros_quantidade} livros)', end='')
            print()
        print('==================')

        print('[?] Em quais estantes deseja adicionar seu livro?')
        while True:
            K = map(int, input('[*] Insira os números (separando por espaço) > ').split())
            if 0 < min(K) and max(K) < len(bibliotecas_do_usuario):
                break
            print('[!] NÚMERO INVÁLIDO')

        biblioteca_selecionada.adicionar_livro(livro.id, K)
        
