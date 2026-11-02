import json
from random import choice
from string import ascii_lowercase, digits
from datetime import date
from subprocess import run
from typing import Iterable, Callable, Any, Concatenate, Sequence


class database:
    usuarios: dict[UsuarioID, Usuario]          = {}
    bibliotecas: dict[BibliotecaID, Biblioteca] = {}
    livros: dict[LivroID, Livro]                = {}

    class UNIQUES:
        usuarios_nome: set[str] = set()
        biblioteca_nome: set[str] = set()

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
        self.livros: set[Livro] = set()
        self.bibliotecas: set[Biblioteca] = set()
        self.bibliotecas_externas: set[Biblioteca] = set()
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        database.usuarios[self.id] = self
        database.UNIQUES.usuarios_nome.add(self.nome)
        self.__nao_atualizar_data_de_atualizacao = False

    def cadastrar_biblioteca(self, nome: BibliotecaNome) -> 'Biblioteca':
        """Registra uma nova biblioteca vazia no banco de dados e retorna """
        if nome in database.UNIQUES.biblioteca_nome:
            raise ValueError('Já existe uma biblioteca com esse nome.')

        biblioteca = Biblioteca(nome=nome, pertencente=self)
        self.bibliotecas.add(biblioteca)
        return biblioteca

    def cadastrar_livro(self, titulo: Titulo, conteudo: list[str]) -> 'Livro':
        """Cria um livro"""
        livro = Livro(titulo, conteudo, autor=self)
        self.livros.add(livro)
        return livro

    def adicionar_livro_a_biblioteca(self, livro: 'Livro', biblioteca: 'Biblioteca', estantes: Iterable[tuple[int, int]]):
        biblioteca.adicionar_livro(self, livro, estantes)

    def modificar_livro(self, livro: 'Livro', pagina: int, conteudo: str):
        livro.alterar_pagina(self, pagina, conteudo)

    def para_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "livros": [livro.id for livro in self.livros],
            "bibliotecas": [biblioteca.id for biblioteca in self.bibliotecas],
            "bibliotecas_externas": [biblioteca.id for biblioteca in self.bibliotecas_externas],
            "data_de_criacao": self.data_de_criacao,
            "data_de_atualizacao": self.data_de_atualizacao,
        }
    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value)
        if self.__nao_atualizar_data_de_atualizacao:
            return
        EmptyClass.__setattr__(self, 'data_de_atualizacao', agorinha())


class Biblioteca:
    @staticmethod
    def permitir_somente_usuario_autorizado[**P, R](method: Callable[Concatenate['Biblioteca', P], R]) -> Callable[Concatenate['Biblioteca', Usuario, P], R]:
        def callback(self: 'Biblioteca', usuario: Usuario, *args: Any, **kwargs: Any):
            if usuario not in self.usuarios_autorizados:
                raise PermissionError('Você não tem permissão para modificar essa biblioteca.')
            return method(self, *args, **kwargs)
        return callback

    def __init__(self, nome: str, pertencente: Usuario):
        self.nome = nome
        self.id: BibliotecaID = gerar_id()
        self.pertencente = pertencente
        self.usuarios_autorizados = {pertencente}
        self.livros: dict[Livro, int] = {}
        self.estantes: list[dict[Livro, int]] = []
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        database.bibliotecas[self.id] = self
        database.UNIQUES.biblioteca_nome.add(self.nome)
        
    def mostrar_titulos(self):
        for livro in self.livros:
            print(livro.titulo)

    @permitir_somente_usuario_autorizado
    def adicionar_livro(self, livro: 'Livro', estantes_e_quantidade: Iterable[tuple[int, int]]):
        """Adiciona o livro em várias estantes. Para cada estante, a quantidade de livros deve ser específica.
        
        Exemplo: Quero adicionar 2 livros na estante 4, 3 livros na estante 6 e 9 livros na estante 1.
        >>> estantes_e_quantidade=[
            (4, 2),
            (6, 3),
            (1, 9),
        ]
        """
        # Pega o total da quantidade de livros em cada estante. Esse total é o total de livros em toda a biblioteca
        self.livros[livro] = sum(E_e_Q[1] for E_e_Q in estantes_e_quantidade)
        
        for i, q in estantes_e_quantidade:
            estante = self.estantes[i]
            if q < 0:
                raise ValueError("Tentando adicionar um número negativo de livros?")
            
            if livro in estante:
                estante[livro] += q
            else:
                estante[livro] = q
    
    @permitir_somente_usuario_autorizado
    def remover_livro(self, livro: 'Livro', estantes_e_quantidades: Iterable[tuple[int, int]]):
        """Remove o livro em várias estantes. Para cada estante, a quantidade de livros a ser removidos deve ser específica.
        \nDetalhe:
        
        1. Se a quantidade de livros removidos for igual a quantidade de livros presentes, a chave que contém o livro é apagada, ou seja o sistema declara que aquele livro não existe mais na estante.
        2. Se todas as estantes não posssuirem mais o livro, o sistema declara que a própria biblioteca não o possui mais. O sistema faz isso somando a quantidade removida em cada estante e subtrai da quantidade atual e compara se esse valor é menor que 0.
        
        \nExemplo: Quero remover 2 livros na estante 4, 3 livros na estante 6 e 9 livros na estante 1.
        
        >>> estantes = [
        0:    {livro: 10}
        1:    {livro: 10}
        2:    {livro: 10}
        3:    {...}
        4:    {livro: 10}
        \n]
        
        >>> blib.remover_livro(
            meu_usuario,
            livro,
            estantes_e_quantidade)=[
                (1, 2),
                (4, 3),
                (2, 9),
            ]
        
        \nResultado:
        >>> [
        0:    {livro: 10}
        1:    {livro: 8}
        2:    {livro: 1}
        3:    {...}
        4:    {livro: 7}
        \n]
        """
        for i, q in estantes_e_quantidades:
            estante = self.estantes[i]
            if q < 0:
                raise ValueError("Impossivel remover um número negativo de livros.")
            if estante[livro] - q < 0:
                raise ValueError("Impossível tirar mais livros do que a estante possui")
            
            estante[livro] -= q
            if estante[livro] == 0:
                estante.pop(livro) # apaga o livro completamente da estante

        # Defalhe: 
        total_removido = sum(x[1] for x in estantes_e_quantidades)
        self.livros[livro] -= total_removido
        if self.livros[livro] < 0:
            self.livros.pop(livro)

    
    @permitir_somente_usuario_autorizado
    def renomear_biblioteca(self, novo_nome: str):
        self.nome = novo_nome

    @permitir_somente_usuario_autorizado # somente um usuário autorizado pode autorizar outros usuários
    def autorizar_usuario(self, usuario: Usuario):
        self.usuarios_autorizados.add(usuario)
        if self not in usuario.bibliotecas:
            usuario.bibliotecas_externas.add(self)
    
    def para_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "livros": {livro.id: q for livro, q in self.livros.items()},
            "estantes": [{livro.id: q for livro, q in estante.items()}
                         for estante in self.estantes],
            "pertencente": self.pertencente.id,
            "usuarios_autorizados": [usuario.id for usuario in self.usuarios_autorizados],
            "data_de_criacao": self.data_de_criacao,
            "data_de_atualizacao": self.data_de_atualizacao,
        }
    
    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value) 
        EmptyClass.__setattr__(self, 'data_de_atualizacao', agorinha())


class Livro:
    def __init__(self, titulo: Titulo, conteudo: list[str], autor: Usuario):
        self.titulo = titulo
        self.id: LivroID = gerar_id()
        self.conteudo = conteudo
        self.autor = autor
        self.usuarios_autorizados = {autor}
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        database.livros[self.id] = self

    def mostrar_conteudo(self, pagina: int):
        if not 0 <= pagina < len(self.conteudo):
            raise ValueError(f'Índice de página inválido: {pagina}')

        print(self.conteudo[pagina])

    def alterar_pagina(self, usuario: Usuario, pagina: int, novo_conteudo: str):
        if not usuario in self.usuarios_autorizados:
            raise PermissionError('Você não tem permissão para modificar esse livro')
        self.conteudo[pagina] = novo_conteudo

    def alterar_titulo(self, usuario: Usuario, novo_titulo: str):
        if usuario is not self.autor:
            raise PermissionError('Apenas o autor pode realizar essa ação')
        self.titulo = novo_titulo

    def para_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "autor": self.autor.id,
            "usuarios_autorizados": [usuario.id for usuario in self.usuarios_autorizados],
            "data_de_criacao": self.data_de_criacao,
            "data_de_atualizacao": self.data_de_atualizacao,
        }

    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value)
        EmptyClass.__setattr__(self, 'data_de_atualizacao', agorinha())


class UICompleto:
    def __init__(self):
        print('\n==== REGISTRE-SE ====')
        nome = input('[*] Nome: ')
        print('======== FIM :D =======')
        self.auth_user = Usuario(nome)

    def criar_uma_biblioteca(self):
        print('\n==== CRIE UMA BIBILIOTECA ====')

        biblioteca = self.auth_user.cadastrar_biblioteca(input('[*] Nome da sua biblioteca: '))
        query_name = {user.nome: user for user in database.usuarios.values()}
        if input('\nDeseja autorizar mais usuários a modificar sua biblioteca? [y/N]: ').strip()[:1].lower() == 'y':
            while True:
                nome = input('[*] Insira o nome: ').strip()
                usuario = query_name.get(nome)

                if usuario is None:
                    print('[!] Usuário não existe.')
                    continue

                biblioteca.autorizar_usuario(self.auth_user, usuario)

                if input('Adicionar outro? [y/N]: ').strip()[:1].lower() != 'y':
                    break

    def criar_um_livro(self) -> Livro | None:
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
        
        bibliotecas_do_usuario = tuple(self.auth_user.bibliotecas | self.auth_user.bibliotecas_externas)
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
        print('====================')

        print('[?] Em quais estantes deseja adicionar quantos do seu livro?')

        # map: separa cada relação estante/quantidade
        # mapzinho (o filho dele): separa os dois elementos separados por espaço e converte para inteiro
        K = map(
            lambda s: tuple(map(int, s.split())),
            input('[*] Insira os números (ex: 0 0,1 1, ...)\n> ').split(',')
        )
        biblioteca_selecionada.adicionar_livro(self.auth_user, livro, K) # type: ignore

    def exibir_estantes_que_contem_livro(self, biblioteca: Biblioteca, livro: Livro):
        print("\n[•] O livro aparece nas seguintes estantes:")
        for i, estante in enumerate(biblioteca.estantes):
            if livro in estante:
                print(f"[|] {i + 1}")
    
    def selecionar_estantes_e_quantidades(self, biblioteca: Biblioteca) -> Iterable[tuple[int, int]]:
        # TODO: adicionar um validador para garantir que a entrada seja compativel com a sintaxe
        return map( # type: ignore
            lambda s: tuple(map(int, s.split())), 
            input("\n[*] Selecione as estante (ex: 0 0,1 1)\n> ").split(',')
        )
    def selecionar_biblioteca(self, bibliotecas: Iterable[Biblioteca]):
        print("[+] BIBLIOTECAS:")
        for i, biblioteca in enumerate(bibliotecas):
            print(f"[{i+1}]    {biblioteca.nome} (de {biblioteca.pertencente.nome})")
        bibliotecas = tuple(bibliotecas)
        while True:
            N = int(input("\n[*] Insira o número da biblioteca > "))
            if 0 < N <= len(bibliotecas):
                break
            print("[!] ÍNDICE INVÁLIDO")

        biblioteca = bibliotecas[N - 1]
        
        print(f'[>] Biblioteca selecionada: {biblioteca.nome}')
        return biblioteca
    
    def visitar_biblioteca(self):
        print("\n==== VISITAR BIBLIOTECA ====")
        print(  "============================")
        b = self.selecionar_biblioteca(database.bibliotecas.values())
        
        print("[?] O quê deseja fazer?")
        print("[1] Listar livros")
        print("[2] Listar estantes")
        print("[3] Ler um livro")
        print("[4] Pedir livro/s emprestado/s")
        print("[5] Devolver livro/s emprestado/s")
        print("[6] Encerrar")
        
    def gerenciar_biblioteca(self):
        print("\n==== GERENCIAR BIBLIOTECA ====")
        print(  '==============================')
        b = self.selecionar_biblioteca(
            self.auth_user.bibliotecas | self.auth_user.bibliotecas_externas
        )
        print(f'[?] O que deseja fazer?')
        print('[1] Listar livros')
        print('[2] Listar estantes')
        print("[3] Adicionar um livro")
        print('[4] Remover um livro')
        print('[5] Encerrar operação')

        while True:
            match int(input(f'[*] Sua resposta > ')):
                case 1:
                    for livro in b.livros:
                        print(f'[|]    {livro.titulo}')
                case 2:
                    self.formatar_e_exibir_estantes(b)
                case 3:
                    livro = self.selecionar_livro(b.livros.keys())
                    print(f'[>] "{livro.titulo}" (por {livro.autor.nome})')
                case 4:
                    livro = self.selecionar_livro(b.livros.keys())

                    print(f'[>] "{livro.titulo}" (por {livro.autor}) selecionado.')
                    if input('[?] Tem certeza que deseja remover esse livro?\n  A ação apenas excluirá o livro de todas as estantes da biblioteca. [y/N] ').strip()[:1].lower() == 'n':
                        self.exibir_estantes_que_contem_livro(b, livro)
                        b.remover_livro(
                            self.auth_user,
                            livro,
                            estantes_e_quantidades=self.selecionar_estantes_e_quantidades(b)
                        )
                
                case 5:
                    break
                case _:
                    print('[!] RESPOSTA INVÁLIDA\n')
    
    def selecionar_livro(self, livros: Iterable[Livro]) -> Livro:
        print('\n==== LIVROS DISPONÍVEIS ====')
        for i, livro in enumerate(livros):
            print(f'[{i}]    {livro.titulo}')
        print('==============================')
        tupl = tuple(livros)
        while True:
            n = int(input('[*] Número do livro:'))
            if 0 < n <= len(tupl):
                break
            print('[!] NÚMERO INVÁLIDO\n')

        return tupl[n - 1]

def salvar_banco(filename: str):
    data = {
        "users": {id: user.para_json() for id, user in database.usuarios.items()},
        "libs": {id: lib.para_json() for id, lib in database.bibliotecas.items()},
        "books": {id: book.para_json() for id, book in database.livros.items()},
    }
    
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)