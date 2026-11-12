import json
from random import choice
from string import ascii_lowercase, digits
from datetime import datetime
from subprocess import run
from typing import Iterable, Callable, Any, Concatenate, Optional

DATABASE_NAME = "dados.json"
class database:
    usuarios: dict[UsuarioID, Usuario]          = {}
    bibliotecas: dict[BibliotecaID, Biblioteca] = {}
    livros: dict[LivroID, Livro]                = {}

    class UNIQUES:
        usuarios_nome: set[str] = set()
        biblioteca_nome: set[str] = set()

agorinha = datetime.now

type Titulo = str
type BibliotecaNome = str
type ID = str
type UsuarioID = ID
type BibliotecaID = ID
type LivroID = ID


red = '\033[31m'
green = '\033[32m'
yellow = '\033[33m'
blue = '\033[34m'
black = '\033[90m'
res = '\033[0m'

def int_input(prompt: str):
    """Só retorna o número quando o usuário insere um inteiro válido"""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print(f"{red} Valor não é um inteiro válido{res}\n")

def gerar_id() -> ID:
    return ''.join(choice(ascii_lowercase + digits) for _ in range(8))

class EmptyClass:
    def __init__(self):
        return None

def update(method: Any):
    if not getattr(method, '__nao_atualizar_data_de_atualizacao', False):
        EmptyClass.__setattr__(method, 'data_de_atualizacao', agorinha())

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
        update(self)
        return biblioteca

    def cadastrar_livro(self, titulo: Titulo, conteudo: list[str]) -> 'Livro':
        """Cria um livro"""
        livro = Livro(titulo, conteudo, autor=self)
        self.livros.add(livro)
        update(self)
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
            "data_de_criacao": self.data_de_criacao.strftime(r"%d/%m/%Y, %H:%M:%S"),
            "data_de_atualizacao": self.data_de_atualizacao.strftime(r"%d/%m/%Y, %H:%M:%S"),
        }
    @staticmethod
    def carregar_json(dados: dict[str, Any]):
        u = Usuario('')
        u.__nao_atualizar_data_de_atualizacao = True
        u.nome = dados["nome"]
        u.id = dados["id"]
        u.livros = {database.livros[id] for id in dados["livros"]}
        u.bibliotecas = {database.bibliotecas[id] for id in dados["bibliotecas"]}
        u.bibliotecas_externas = {database.bibliotecas[id] for id in dados["bibliotecas_externas"]}
        u.data_de_criacao = datetime.strptime(dados["data_de_criacao"], r"%d/%m/%Y, %H:%M:%S")
        u.data_de_atualizacao = datetime.strptime(dados["data_de_atualizacao"], r"%d/%m/%Y, %H:%M:%S")
        u.__nao_atualizar_data_de_atualizacao = False
        return u
    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value)
        update(self)


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

        self.__nao_atualizar_data_de_atualizacao = False
        
    def mostrar_titulos(self):
        for livro in self.livros:
            print(livro.titulo)

    @permitir_somente_usuario_autorizado
    def adicionar_estantes(self, n: int):
        for _ in range(n):
            self.estantes.append({})
        update(self)
    
    @permitir_somente_usuario_autorizado
    def adicionar_livro(self, livro: 'Livro', estantes_e_quantidade: Iterable[tuple[int, int]]):
        """# Adiciona o livro em várias estantes. Para cada estante, a quantidade de livros deve ser específica.
        
        ### Exemplo: Quero adicionar 2 livros na estante 4, 3 livros na estante 6 e 9 livros na estante 1.
        estantes: [{}, {}, {}, {}, {}, {}, {}]
        >>> blib.adicionar_livro(
        ...    meu_usuario,
        ...    livro, 
        ...    [
        ...        (4, 2),
        ...        (6, 3),
        ...        (1, 9),
        ...    ]
        ...)

        estantes (resultado): [
            {},
            {livro: 9},
            {},
            {},
            {livro: 2},
            {},
            {},
            {livro: 3},
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
        update(self)
    
    @permitir_somente_usuario_autorizado
    def remover_livro(self, livro: 'Livro', estantes_e_quantidades: Iterable[tuple[int, int]]):
        """# Remove o livro em várias estantes. Para cada estante, a quantidade de livros a ser removidos deve ser específica.
        
        * ## Detalhe:
        
        1. Se a quantidade de livros removidos for igual a quantidade de livros presentes, a chave que contém o livro é apagada, ou seja o sistema declara que aquele livro não existe mais na estante.
        2. Se todas as estantes não posssuirem mais o livro, o sistema declara que a própria biblioteca não o possui mais. O sistema faz isso somando a quantidade removida em cada estante e subtrai da quantidade atual e compara se esse valor é menor que 0.
        
        * ## Exemplo: 
        >>> estantes: [
        ...    {livro: 10}, # 0
        ...    {livro: 10}, # 1
        ...    {livro: 10}, # 2
        ...    {...}, # 3 (não contém o livro)
        ...    {livro: 10}, # 4
        ... ]
        
        ### Quero remover 2 livros na estante 4, 3 livros na estante 6 e 9 livros na estante 1.
        
        
        >>> blib.remover_livro(
            meu_usuario, # usuário autorizado
            livro,
            estantes_e_quantidade)=[
                (1, 2),
                (4, 3),
                (2, 9),
            ]
        )
        
        Resultado:
        >>> [
        ...    {livro: 10},
        ...    {livro: 8},
        ...    {livro: 1},
        ...    {...},
        ...    {livro: 7},
        ... ]
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
        update(self)

    
    @permitir_somente_usuario_autorizado
    def renomear_biblioteca(self, novo_nome: str):
        self.nome = novo_nome

    @permitir_somente_usuario_autorizado # somente um usuário autorizado pode autorizar outros usuários
    def autorizar_usuario(self, usuario: Usuario):
        self.usuarios_autorizados.add(usuario)
        if self not in usuario.bibliotecas:
            usuario.bibliotecas_externas.add(self)
        update(self)
    
    def para_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "livros": {livro.id: q for livro, q in self.livros.items()},
            "estantes": [{livro.id: q for livro, q in estante.items()}
                         for estante in self.estantes],
            "pertencente": self.pertencente.id,
            "usuarios_autorizados": [usuario.id for usuario in self.usuarios_autorizados],
            "data_de_criacao": self.data_de_criacao.strftime(r"%d/%m/%Y, %H:%M:%S"),
            "data_de_atualizacao": self.data_de_atualizacao.strftime(r"%d/%m/%Y, %H:%M:%S"),
        }
    
    @staticmethod
    def carregar_json(dados: dict[str, Any]):
        b = Biblioteca('', Usuario('')) # Uma biblioteca vazio com um usuário anômio
        b.__nao_atualizar_data_de_atualizacao = True
        b.nome = dados["nome"]
        b.id = dados["id"]
        b.livros = {database.livros[id]: q for id, q in dados["livros"].items()}
        b.estantes = [{database.livros[id]: q for id, q in estante}
                      for estante in dados["estante"]]
        b.pertencente = database.usuarios[dados["pertencente"]]
        b.usuarios_autorizados = {database.usuarios[id] for id in dados["usuarios_autorizados"]}
        b.data_de_criacao = datetime.strptime(dados["data_de_criacao"], r"%d/%m/%Y, %H:%M:%S")
        b.data_de_atualizacao = datetime.strptime(dados["data_de_atualizacao"], r"%d/%m/%Y, %H:%M:%S")
        b.__nao_atualizar_data_de_atualizacao = False
        return b
    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value)
        update(self)


class Livro:
    def __init__(self, titulo: Titulo, conteudo: list[str], autor: Usuario):
        self.titulo = titulo
        self.id: LivroID = gerar_id()
        self.conteudo = conteudo
        self.autor = autor
        self.usuarios_autorizados = {autor}
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()
        self.__nao_atualizar_data_de_atualizacao = False

        database.livros[self.id] = self

    def mostrar_conteudo(self, pagina: int):
        if not 0 <= pagina < len(self.conteudo):
            raise ValueError(f'Índice de página inválido: {pagina}')

        print(self.conteudo[pagina])

    def alterar_pagina(self, usuario: Usuario, pagina: int, novo_conteudo: str):
        if not usuario in self.usuarios_autorizados:
            raise PermissionError('Você não tem permissão para modificar esse livro')
        self.conteudo[pagina] = novo_conteudo
        update(self)

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
            "data_de_criacao": self.data_de_criacao.strftime(r"%d/%m/%Y, %H:%M:%S"),
            "data_de_atualizacao": self.data_de_atualizacao.strftime(r"%d/%m/%Y, %H:%M:%S"),
        }
    @staticmethod
    def carregar_json(dados: dict[str, Any]):
        l = Livro('', [], Usuario('')) # Um livro sem titulo, sem conteudo e com autor anonimo
        
        l.__nao_atualizar_data_de_atualizacao = True
        l.titulo = dados["titulo"]
        l.id = dados["id"]
        l.autor = database.usuarios[dados["autor"]]
        l.usuarios_autorizados = {database.usuarios[id] for id in dados["usuarios_autorizados"]}
        l.data_de_criacao = datetime.strptime(dados["data_de_criacao"], r"%d/%m/%Y, %H:%M:%S")
        l.data_de_atualizacao = datetime.strptime(dados["data_de_atualizacao"], r"%d/%m/%Y, %H:%M:%S")
        l.__nao_atualizar_data_de_atualizacao = False
        return l
    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value)
        update(self)


class UICompleto:
    def __init__(self):
        print('\n==== REGISTRE-SE ====')
        nome = input(f'{red}*{res} Seu nome: ')
        self.auth_user = Usuario(nome)
        print('=====================')
        self.interface()

    def criar_uma_biblioteca(self):
        print('\n==== CRIE UMA BIBILIOTECA ====')

        biblioteca = self.auth_user.cadastrar_biblioteca(input('Nome da sua biblioteca: '))
        biblioteca.adicionar_estantes(self.auth_user, int_input('Quantas estantes sua biblioteca terá? > '))

        if len(database.usuarios) <= 1: # Só existe um usuário em todo o banco. Não faz sentido pedir para autorizar "outros"
            return None
        query_name = {user.nome: user for user in database.usuarios.values()}
        if input(f'\nDeseja autorizar mais usuários a modificar sua biblioteca? {black}[y/N]{black}: ').strip()[:1].lower() == 'y':
            while True:
                nome = input('Nome: ').strip()
                usuario = query_name.get(nome)

                if usuario is None:
                    print(f'{red}⚠{res} Usuário não existe.')
                    continue

                biblioteca.autorizar_usuario(self.auth_user, usuario)

                if input(f'Adicionar outro? {black}[y/N]{black}: ').strip()[:1].lower() != 'y':
                    break
                print()

    def criar_um_livro(self) -> Livro | None:
        # TODO: Implementar um editor de texto integrado tipo o vim
        print('\n==== CRIAR LIVRO ====')
        print(f'{blue}[LOL] Ainda não fiz um editor de texto integrado.{res}')

        if input(f'Deseja continuar com bloco de notas? {black}[y/N]{res}: ').strip()[:1].lower() != 'y':
            return
        
        titulo = input('Titulo: ')
        print(f'{blue}🛈{res} Você pode separar as páginas adicionando 2 linhas de espaço.')
        print(f'{red}x{res} Feche a janela para concluir o livro.')
        run(rf'notepad.exe temp.txt')
        with open('temp.txt', 'r') as arquivo:
            paginas = arquivo.read().split('\n\n\n')

        livro = self.auth_user.cadastrar_livro(titulo, paginas)
        
        if input(f'\nAdicionar livro a alguma biblioteca? {black}[y/N]{res}: ').strip()[:1].lower() == 'y':
            self.adicionar_livro_a_biblioteca(livro)
        
        return livro
    
    def formatar_e_exibir_estantes(self, biblioteca: Biblioteca):
        print('\n----- ESTANTES -----')
        for i in range(len(biblioteca.estantes)):
            livros_quantidade = sum(biblioteca.estantes[i].values())                
            print(f'{i + 1}. ', ("/" * livros_quantidade), end=' ')

            if livros_quantidade > 1:
                print(f'({livros_quantidade} livros)', end='')
            print()
        print('---------------------')
    
    def adicionar_livro_a_biblioteca(self, livro: Livro):
        bibliotecas_do_usuario = tuple(self.auth_user.bibliotecas | self.auth_user.bibliotecas_externas)
        
        if len(bibliotecas_do_usuario) == 0:
            print("I'm sorry, mas você não possui e não é autorizado em nenhuma biblioteca.")
            return None
        biblioteca_selecionada = self.selecionar_biblioteca(bibliotecas_do_usuario)

        if len(biblioteca_selecionada.estantes) == 0:
            print(f'{blue}⚠{res} A biblioteca não possui estantes.')
            if input(f'Deseja adicionar por conta própria? {black}[y/N]{res}: ').strip()[:1].lower() == 'y':
                biblioteca_selecionada.adicionar_estantes(
                    self.auth_user, int_input('Insira o novo número de estantes > ')
                )
        self.formatar_e_exibir_estantes(biblioteca_selecionada)

        print('Em quais estantes deseja adicionar quantos do seu livro?')
        biblioteca_selecionada.adicionar_livro(self.auth_user, livro, self.selecionar_estantes_e_quantidades(biblioteca_selecionada))

    def exibir_estantes_que_contem_livro(self, biblioteca: Biblioteca, livro: Livro):
        print("\n---- ESTANTES ----")
        for i, estante in enumerate(biblioteca.estantes):
            if livro in estante:
                quantidade = estante[livro]
                # 1 | //// (4)
                print(f"{i + 1} |", "/" * quantidade, f"({quantidade})")
        print("------------------")
    
    def selecionar_biblioteca(self, bibliotecas: Iterable[Biblioteca], empty_msg: str="Não há bibliotecas"):
        if not bibliotecas:
            raise Exception(empty_msg)
        
        print("\n---- Bibliotecas ----")
        for i, biblioteca in enumerate(bibliotecas):
            print(f"{i+1}.    {biblioteca.nome}")
        print("---------------------")
        
        bibliotecas = tuple(bibliotecas)
        
        while True:
            N = int_input("\nInsira o índice da biblioteca > ")
            if 0 < N <= len(bibliotecas):
                break
            print(f"{red}⚠{res} Índice inválido")

        biblioteca = bibliotecas[N - 1]
        
        print(f'[>] Biblioteca selecionada: {blue}{biblioteca.nome}{res}')
        return biblioteca
    
    def visitar_biblioteca(self):
        b = self.selecionar_biblioteca(database.bibliotecas.values())
        print("\n==== VISITAR BIBLIOTECA ====")
        while True:
            print("\nO quê deseja fazer?")
            print("[1] Listar livros")
            print("[2] Listar estantes")
            print("[3] Ler um livro")
            print("[4] Encerrar")
            match int_input("Escolha > "):
                case 1:
                    for livro, tot in b.livros.items():
                        print(f"[|] {livro.titulo} {black}por: {livro.autor.nome}{res} (total: {tot})")
                case 2:
                    self.formatar_e_exibir_estantes(b)
                case 3:
                    if len(b.livros) == 0:
                        print(f'{red}🛈{res} Infelizmente a biblioteca está vazia.')
                        continue
                    livro = self.selecionar_livro(b.livros.keys(), error_msg="A biblioteca não possui nenhum livro.")
                    filename = f"{livro.id}#{livro.autor.id}.txt"
                    with open(filename, "w") as file:
                        file.write(('\n' + ('=' * 100) + '\n').join(livro.conteudo))
                    print("[x] feche o arquivo para concluir a leitura.")
                    run(f'notepad.exe {filename}')
                case 4:
                    break
                case _:
                    pass
        print( "============================")
        
    def gerenciar_biblioteca(self):
        b = self.selecionar_biblioteca(
            self.auth_user.bibliotecas | self.auth_user.bibliotecas_externas
        )
        print("\n==== GERENCIAR BIBLIOTECA ====")
        while True:
            print(f'\nO que deseja fazer?')
            print('[1] Listar livros')
            print('[2] Listar estantes')
            print("[3] Adicionar um livro")
            print('[4] Remover um livro')
            print('[5] Encerrar operação')
            match int_input(f"Opção > "):
                case 1:
                    for livro in b.livros:
                        print(f'[|]    {livro.titulo} {black}({livro.autor.nome}){res}')
                case 2:
                    self.formatar_e_exibir_estantes(b)
                case 3:
                    livro = self.selecionar_livro(database.livros.values(), error_msg="Nenhum livro foi públicado no sistema.")
                    print(f'[>] Livro "{blue}{livro.titulo}{res}" (por: {livro.autor.nome}) selecionado')
                    self.formatar_e_exibir_estantes(b)
                    estantes_e_quantidades = self.selecionar_estantes_e_quantidades(b)
                    b.adicionar_livro(self.auth_user, livro, estantes_e_quantidades)
                case 4:
                    self.formatar_e_exibir_estantes(b)
                    livro = self.selecionar_livro(b.livros.keys(), error_msg="A biblioteca selecionada ainda não possui livros.")
                    print(f'[>] "{blue}{livro.titulo}{res}" (por: {livro.autor.nome}) selecionado.')
                    if input(f'Tem certeza que deseja remover esse livro? {black}[y/N]{res}: ').strip()[:1].lower() == 'y':
                        self.exibir_estantes_que_contem_livro(b, livro)
                        b.remover_livro(
                            self.auth_user,
                            livro,
                            estantes_e_quantidades=self.selecionar_estantes_e_quantidades(
                                b, estantes_validas=(i for i, estante in enumerate(b.estantes) if livro in estante)
                            )
                        )
                
                case 5:
                    break
                case _:
                    print(f'{red}⚠{res} Resposta inálida')
        print(  '==============================')
    
    def selecionar_estantes(self, biblioteca: Biblioteca, numeros_validos: Optional[Iterable[int]]=None, not_in_valid_numbers_msg: str=""):
        estantes: set[int] = set()
        estante_valida: Callable[[int], bool] = lambda x: 0 < x <= len(biblioteca.estantes)

        _max = len(tuple(numeros_validos)) if numeros_validos is not None else len(biblioteca.estantes)
        i = 1
        print('\nInsira as estantes:', end='') # A linha já vai ser quebrada denovo no input. Não quero fazer duas quebras
        while True:
            e = int_input(f"\nEstante {i}/{_max} (insira -1 para encerrar) > ")
            if e <= -1:
                if len(estantes) == 0:
                    print(f"{red}⚠{res} Você não inseriu nenhuma estante")
                    continue
                return estantes
            if not estante_valida(e):
                print(f"{red}⚠{res} Índice inválido.")
                continue
            if numeros_validos:
                if e not in numeros_validos:
                    print(not_in_valid_numbers_msg)
                    continue
            if e in estantes:
                print(f"{red}⚠{res} Você já inseriu esse índice.")
                continue
            estantes.add(e - 1)
            i += 1
            if i > _max:
                return estantes
      
    def selecionar_quantidades(self, estantes: Iterable[int], error_prompt: str):
        if not estantes:
            raise Exception(error_prompt)
        relacoes: list[tuple[int, int]] = []
        print(f'{blue}🛈{res} Insire a quantidade de livros em cada estante: ')
        
        for e in estantes:
            relacoes.append((
                e,
                int_input(f"Estante {e + 1} > ") # Para o usuário, as estantes começam a ser contadas a partir do 1, mas internamente elas são contadas a partir do 0
            ))
        return relacoes
    
    def selecionar_estantes_e_quantidades(self, biblioteca: Biblioteca, estantes_validas: Optional[Iterable[int]]=None):
        return self.selecionar_quantidades(
            self.selecionar_estantes(biblioteca, estantes_validas, not_in_valid_numbers_msg="Esse índice não foi listado"),
            error_prompt=f"Ainda não existem estantes na biblioteca {blue}{biblioteca.nome}{res}"
        )

    def selecionar_livro(self, universo: Iterable[Livro], error_msg: str):
        universo = tuple(universo)
        if len(universo) == 0:
            raise Exception(error_msg)
        print('\n---- Livros disponíveis ----')
        for i, livro in enumerate(universo):
            print(f"{i + 1}. {livro.titulo} {black}({livro.autor.nome}){res}")
        print('----------------------------')
        
        while True:
            k = int_input("\nSelecione o índice do livro > ")
            if 0 < k <= len(universo):
                return universo[k - 1]
            print("[!] ÍNDICE INVÁLIDO")
    
    def interface(self):
        print('\n==== INTERFACE ====')
        rodando = True
        while rodando:
            carregar_banco()
            print('\n[1] Visitar biblioteca')
            print('[2] Criar um livro')
            print('[3] Fundar uma biblioteca')
            print('[4] Gerenciar sua biblioteca')
            print('[5] Encerrar')
            try:
                match int_input('[*] O que deseja fazer? > '):
                    case 1:
                        self.visitar_biblioteca()
                    case 2:
                        self.criar_um_livro()
                    case 3:
                        self.criar_uma_biblioteca()
                    case 4:
                        self.gerenciar_biblioteca()
                    case 5:
                        rodando = False
                    case _:
                        pass
            except KeyboardInterrupt:
                print('\n[!] OPERAÇÃO CANCELADA')
            except Exception as e:
                print(f'[ERRO] {e}')
            salvar_banco()
            
def salvar_banco():
    dados = {
        "users": {id: user.para_json() for id, user in database.usuarios.items()},
        "libs": {id: lib.para_json() for id, lib in database.bibliotecas.items()},
        "books": {id: book.para_json() for id, book in database.livros.items()},
    }
    
    with open(DATABASE_NAME, "w") as file:
        json.dump(dados, file, indent=4)

def carregar_banco():
    try:
        with open(DATABASE_NAME, "r") as file:
            dados = json.load(file)
    except FileNotFoundError:
        return None
    
    for id, user_data in dados["users"].items():
        user = Usuario.carregar_json(user_data)
        database.usuarios[id] = user
        database.UNIQUES.usuarios_nome.add(user.nome)
    
    for id, lib_data in dados["libs"].items():
        lib = Biblioteca.carregar_json(lib_data)
        database.bibliotecas[id] = lib
        database.UNIQUES.biblioteca_nome.add(lib.nome)
    
    for id, book_data in dados["books"].items():
        book = Livro.carregar_json(book_data)
        database.livros[id] = book

