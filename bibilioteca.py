from random import choice
from string import ascii_lowercase, digits
from datetime import date
from subprocess import run
from typing import Iterable, Callable, Any, NoReturn

class database:
    usuarios: list[Usuario]       = []
    bibliotecas: list[Biblioteca] = []
    livros: list[Livro]           = []

    class Querys:
        usuario_id: dict[UsuarioID, Usuario]          = {}
        usuario_nome: dict[str, Usuario]              = {}
        biblioteca_id: dict[BibliotecaID, Biblioteca] = {}
        biblioteca_nome: dict[str, Biblioteca]        = {}
        livro_id: dict[LivroID, Livro]                = {}
        livro_nome: dict[str, set[Livro]]             = {}

agorinha = date.today

type Titulo = str
type BibliotecaNome = str
type ID = str
type UsuarioID = ID
type BibliotecaID = ID
type LivroID = ID

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

        database.usuarios.append(self)
        database.Querys.usuario_nome  [nome] = self
        database.Querys.usuario_id [self.id] = self

    def cadastrar_biblioteca(self, nome: BibliotecaNome) -> Biblioteca:
        """Registra uma nova biblioteca vazia no banco de dados e retorna """
        if database.Querys.usuario_nome.get(nome, False):
            raise ValueError('Já existe uma biblioteca com esse nome.')

        biblioteca = Biblioteca(nome=nome, pertencente=self)
        self.bibliotecas.add(biblioteca.id)
        return biblioteca

    def cadastrar_livro(self, titulo: Titulo, conteudo: list[str]):
        """Cria um livro """
        livro = Livro(titulo, conteudo, autor=self)
        self.livros.add(livro.id)
        return livro

    def adicionar_livro_a_biblioteca(self, livro_id: LivroID, biblioteca_id: UsuarioID, estantes: Iterable[int]):
        biblioteca = database.Querys.biblioteca_id.get(biblioteca_id)
        if biblioteca is None:
            raise ValueError('Essa biblioteca não existe')

        biblioteca.adicionar_livro(self.id, livro_id, estantes)


    def modificar_livro(self, livro: Livro, pagina: int, conteudo: str):
        livro.alterar_pagina(self, pagina, conteudo)

    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value)
        EmptyClass.__setattr__(self, 'data_de_atualizacao', agorinha())


class Biblioteca:
    @staticmethod
    def permitir_somente_usuario_autorizado(method: Callable[..., Any | NoReturn]):
        def callback(self: 'Biblioteca', usuario_id: UsuarioID, *args: Any, **kwargs: Any):
            if usuario_id not in self.ids_autorizados:
                raise PermissionError('Você não tem permissão para modificar essa biblioteca.')
            return method(self, *args, **kwargs)
        return callback

    def __init__(self, nome: str, pertencente: Usuario):
        self.nome = nome
        self.id: BibliotecaID = gerar_id()
        self.pertencente = pertencente
        self.ids_autorizados = {pertencente.id}
        self.livros: set[LivroID] = set()
        self.estantes: list[set[LivroID]] = []
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        database.bibliotecas.append(self)
        database.Querys.biblioteca_id[self.id] = self
        database.Querys.biblioteca_nome[nome] = self

    def mostrar_titulos(self):
        livros = [database.Querys.livro_id[_id] for _id in self.livros]
        for livro in livros:
            print(livro.titulo)

    @permitir_somente_usuario_autorizado
    def adicionar_livro(self, livro_id: str, estantes: Iterable[int]):
        self.livros.add(livro_id)
        for i in estantes:
            estante = self.estantes[i]
            estante.add(livro_id)
    
    @permitir_somente_usuario_autorizado
    def remover_livro(self, livro_id: str, estantes: Iterable[int]):
        if len(set(estantes)) == len(self.estantes):
            self.livros.remove(livro_id)
        
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

    def __setattr__(self: Any, name: str, value: Any):
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

        database.livros.append(self)
        database.Querys.livro_id[self.id] = self

        query = database.Querys.livro_nome
        if query.get(titulo) is not None:
            query[titulo].add(self)
        else:
            query[titulo] = {self}

    def mostrar_conteudo(self, pagina: int):
        if not 0 <= pagina < len(self.conteudo):
            raise ValueError(f'Índice de página inválido: {pagina}')

        print(self.conteudo[pagina])

    def alterar_pagina(self, usuario: Usuario, pagina: int, novo_conteudo: str):
        if not usuario.id in self.ids_autorizados:
            raise PermissionError('Você não tem permissão para modificar esse livro')
        self.conteudo[pagina] = novo_conteudo

    def alterar_titulo(self, usuario: Usuario, novo_titulo: str):
        if usuario is not self.autor:
            raise PermissionError('Apenas o autor pode realizar essa ação')
        query = database.Querys.livro_nome
        query[self.titulo].remove(self)
        
        if query.get(novo_titulo) is not None:
            query[novo_titulo].add(self)
        else:
            query[novo_titulo] = {self}
        self.titulo = novo_titulo

    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value)
        EmptyClass.__setattr__(self, 'data_de_atualizacao', agorinha())


class GUICompleto:
    def __init__(self):
        print('\n==== REGISTRE-SE ====')
        nome = input('[*] Nome: ')
        print('======== FIM :D =======')
        self.auth_user = Usuario(nome)

    def criar_uma_biblioteca(self):
        print('\n=== CRIE UMA BIBILIOTECA ===')

        biblioteca = self.auth_user.cadastrar_biblioteca(input('[*] Nome da sua biblioteca: '))

        if input('\nDeseja autorizar mais usuários a modificar sua biblioteca? [y/N]: ').strip()[:1].lower() == 'y':
            while True:
                nome_ou_id = input('[*] Insira o nome (ou o ID): ').strip()
                querys = database.Querys
                usuario = (
                    querys.usuario_id.get(nome_ou_id) or
                    querys.usuario_nome.get(nome_ou_id)
                )

                if usuario is None:
                    raise ValueError('Usuário não existe.')

                biblioteca.autorizar_usuario(usuario.id)

                if input('Adicionar outro? [y/N]: ').strip()[:1].lower() != 'y':
                    break

    def criar_um_livro(self):
        # TODO: Implementar um editor de texto integrado tipo o vim
        print('\n==== CRIAR LIVRO ====')
        print('[LOL] Ainda não fiz um editor de texto integrado.')

        if input('Deseja continuar com bloco de notas? [y/N] ').strip()[:1].lower() != 'y':
            return

        
        titulo = input('Titulo: ')
        print('[x] Feche a janela para concluir o livro.')
        with open('temp.txt', 'w+') as arquivo:
            run(rf'notepad.exe temp.txt')
            paginas = arquivo.read().split('\n\n\n')

        livro = self.auth_user.cadastrar_livro(titulo, paginas)
        
        if input('\nAdicionar livro a alguma biblioteca? [y/N] ').strip()[:1].lower() == 'y':
            self.adicionar_livro_a_biblioteca(livro)
        
        return livro

    
    def formatar_e_exibir_estantes(self, biblioteca: Biblioteca):
        for i in range(len(biblioteca.estantes) - 1):
            livros_quantidade = len(biblioteca.estantes[i])                
            print(f'[{i}] |', "/" * livros_quantidade, end=' ')

            if livros_quantidade > 1:
                print(f'({livros_quantidade} livros)', end='')
            print()
    def adicionar_livro_a_biblioteca(self, livro: Livro):
        print('\n==== ADICIONAR LIVRO ====')
        print('[+] SUAS BIBLIOTECAS: ')
        
        bibliotecas_do_usuario: list[Biblioteca] = [database.Querys.biblioteca_id[_id] for _id in (*self.auth_user.bibliotecas, *self.auth_user.bibliotecas_externas)]
        for i, biblioteca in enumerate(bibliotecas_do_usuario):
            print(f'[{i + 1}]     {biblioteca.nome}')
        print()

        while True:
            n = int(input('[*] Insira o número da biblioteca > '))
            if 0 < n <= len(bibliotecas_do_usuario):
                break
            print('[!] NÚMERO INVÁLIDO')
        biblioteca_selecionada = bibliotecas_do_usuario[n - 1]

        print('\n==== ESTANTES ====')
        self.formatar_e_exibir_estantes(biblioteca_selecionada)
        print('==================')

        print('[?] Em quais estantes deseja adicionar seu livro?')
        while True:
            K = map(int, input('[*] Insira os números (separando por espaço) > ').split())
            if 0 < min(K) and max(K) < len(bibliotecas_do_usuario):
                break
            print('[!] NÚMERO INVÁLIDO')

        biblioteca_selecionada.adicionar_livro(livro.id, K)

    
    def gerenciar_biblioteca(self):


        print("\n==== CONSULTAR BIBLIOTECA ====")
        print('[+] BIBLIOTECAS DISPONÍVEIS: ')
        for i, biblioteca in enumerate(database.bibliotecas):
            print(f'[{i+1}]    {biblioteca.nome}')
        print()

        while True:
            biblioteca_numero = int(input('[*] Insira o número da biblioteca > '))

            if 0 < biblioteca_numero <= len(database.bibliotecas):
                break

            print('[!] NÚMERO INVÁLIDO\n')

        biblioteca = database.bibliotecas[biblioteca_numero - 1]

        print(f'[>] Biblioteca selecionada: {biblioteca.nome}')

        print(f'[?] O que deseja fazer?')
        print('[1] Listar livros')
        print('[2] Listar estantes')
        print('[3] Remover um livro')
        print('[4] Encerrar operação')

        while True:
            r = int(input(f'[*] Sua resposta > '))

            livros = tuple(database.Querys.livro_id[id] for id in biblioteca.livros)
            match r:
                case 1:
                    for livro in livros:
                        print(f'[|]    {livro.titulo}')
                case 2:
                    self.formatar_e_exibir_estantes(biblioteca)
                case 3:
                    livro = self.selecionar_livro(livros)

                    print(f'[+] "{livro.titulo}" selecionado.')
                    if input('[?] Tem certeza que deseja remover esse livro?\n  A ação apenas excluirá o livro de todas as estantes da biblioteca. [y/N] ').strip()[:1].lower() == 'n':
                        biblioteca.remover_livro(
                            self.auth_user.id, 
                            livro.id,
                            estantes=range(len(biblioteca.estantes) - 1) # todas as prateleiras
                        )
                
                case 4:
                    break
                case _:
                    print('[!] RESPOSTA INVÁLIDA\n')
        print('================================')
    def selecionar_livro(self, livros: tuple[Livro, ...]):
        print('\n==== LIVROS DISPONÍVEIS ====')
        for i, livro in enumerate(livros):
            print(f'[{i}]    {livro.titulo}')
        print('==============================')
        
        while True:
            n = int(input('[*] Número do livro:'))
            if 0 < n <= len(livros):
                break
            print('[!] NÚMERO INVÁLIDO\n')

        return livros[n - 1]