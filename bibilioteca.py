import json
from random import choice
from string import ascii_lowercase, digits
from datetime import datetime
from subprocess import run
from typing import Iterable, Callable, Any, Concatenate, Optional, overload, Literal
from advanced_ui import UI as ui

DATABASE_NAME = "dados.json"
json_db: dict[str, dict[str, Any]] | None = None
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

@overload
def fetch(id: UsuarioID, type: Literal['usuarios']) -> Usuario: ...
@overload
def fetch(id: BibliotecaID, type: Literal['bibliotecas']) -> Biblioteca: ...
@overload
def fetch(id: LivroID, type: Literal['livros']) -> Livro: ...

def fetch(id: ID, type: str) -> Usuario | Biblioteca | Livro:
    if type not in ("usuarios", "bibliotecas", "livros"):
        raise ValueError("Tipo inválido")
    
    finded = getattr(database, type).get(id)
    if finded:
        return finded

    if json_db is not None:
        json_finded = json_db[type].get(id)
        if json_finded:
            obj = {
                "usuarios": Usuario,
                "bibliotecas": Biblioteca,
                "livros": Livro,
            }[type]
            created = obj.carregar_json(json_finded) # Tanto Usuario, Biblioteca e Livro possuem o método `.carregar_json`. Por isso sempre funciona

            return created
    raise KeyError(f'ID não identificado: {id}')
    

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
    if not getattr(method, "__nao_atualizar_data_de_atualizacao", False):
        EmptyClass.__setattr__(method, "data_de_atualizacao", agorinha())

class Usuario:
    def __init__(self, nome: str, senha: str, salvar: bool=True):
        self.id: UsuarioID = gerar_id()
        self.nome = nome
        self.senha = senha
        self.livros: set[Livro] = set()
        self.bibliotecas: set[Biblioteca] = set()
        self.bibliotecas_externas: set[Biblioteca] = set()
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()
        self.__nao_atualizar_data_de_atualizacao = False
        if salvar:
            self.salvar()

    def cadastrar_biblioteca(self, nome: BibliotecaNome) -> 'Biblioteca':
        """Registra uma nova biblioteca vazia no banco de dados e retorna """
        if nome in database.UNIQUES.biblioteca_nome:
            raise ValueError("Já existe uma biblioteca com esse nome.")

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
            "senha": self.senha,
            "livros": [livro.id for livro in self.livros],
            "bibliotecas": [biblioteca.id for biblioteca in self.bibliotecas],
            "bibliotecas_externas": [biblioteca.id for biblioteca in self.bibliotecas_externas],
            "data_de_criacao": self.data_de_criacao.strftime(r"%d/%m/%Y, %H:%M:%S"),
            "data_de_atualizacao": self.data_de_atualizacao.strftime(r"%d/%m/%Y, %H:%M:%S"),
        }
    def salvar(self):
        database.usuarios[self.id] = self
        database.UNIQUES.usuarios_nome.add(self.nome)
    
    @staticmethod
    def carregar_json(dados: dict[str, Any]):
        u = Usuario('', '', salvar=False)
        u.__nao_atualizar_data_de_atualizacao = True
        u.id = dados["id"]
        u.nome = dados["nome"]
        u.senha = dados["senha"]
        u.data_de_criacao = datetime.strptime(dados["data_de_criacao"], r"%d/%m/%Y, %H:%M:%S")
        u.data_de_atualizacao = datetime.strptime(dados["data_de_atualizacao"], r"%d/%m/%Y, %H:%M:%S")
        u.salvar()

        u.livros = {fetch(id, "livros") for id in dados["livros"]}
        u.bibliotecas = {fetch(id, "bibliotecas") for id in dados["bibliotecas"]}
        u.bibliotecas_externas = {fetch(id, "bibliotecas") for id in dados["bibliotecas_externas"]}
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
                raise PermissionError("Você não tem permissão para modificar essa biblioteca.")
            return method(self, *args, **kwargs)
        return callback

    def __init__(self, nome: str, pertencente: Usuario, salvar: bool=True):
        self.nome = nome
        self.id: BibliotecaID = gerar_id()
        self.pertencente = pertencente
        self.usuarios_autorizados = {pertencente}
        self.livros: dict[Livro, int] = {}
        self.estantes: list[dict[Livro, int]] = []
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()

        self.__nao_atualizar_data_de_atualizacao = False
        if salvar:
            self.salvar()
        
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
        ... )

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

    def salvar(self):
        database.bibliotecas[self.id] = self
        database.UNIQUES.biblioteca_nome.add(self.nome)
    
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
        b = Biblioteca('', Usuario('', '', salvar=False), salvar=False) # Uma biblioteca vazio com um usuário anômio
        
        b.__nao_atualizar_data_de_atualizacao = True
        
        b.id = dados["id"]
        b.nome = dados["nome"]

        b.data_de_criacao = datetime.strptime(dados["data_de_criacao"], r"%d/%m/%Y, %H:%M:%S")
        b.data_de_atualizacao = datetime.strptime(dados["data_de_atualizacao"], r"%d/%m/%Y, %H:%M:%S")
        
        b.salvar()

        b.pertencente = fetch(dados["pertencente"], "usuarios")
        b.livros = {fetch(id, "livros"): q for id, q in dados["livros"].items()}
        b.estantes = [{fetch(id, "livros"): q for id, q in estante.items()}
                      for estante in dados["estantes"]]
        b.usuarios_autorizados = {fetch(id, "usuarios") for id in dados["usuarios_autorizados"]}
        
        b.__nao_atualizar_data_de_atualizacao = False
        
        return b
    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value)
        update(self)


class Livro:
    def __init__(self, titulo: Titulo, conteudo: list[str], autor: Usuario, salvar: bool=True):
        self.titulo = titulo
        self.id: LivroID = gerar_id()
        self.conteudo = conteudo
        self.autor = autor
        self.usuarios_autorizados = {autor}
        self.data_de_criacao = agorinha()
        self.data_de_atualizacao = agorinha()
        self.__nao_atualizar_data_de_atualizacao = False
        
        if salvar:
            self.salvar()

    def mostrar_conteudo(self, pagina: int):
        if not 0 <= pagina < len(self.conteudo):
            raise ValueError(f"Índice de página inválido: {pagina}")

        print(self.conteudo[pagina])

    def alterar_pagina(self, usuario: Usuario, pagina: int, novo_conteudo: str):
        if not usuario in self.usuarios_autorizados:
            raise PermissionError("Você não tem permissão para modificar esse livro")
        self.conteudo[pagina] = novo_conteudo
        update(self)

    def alterar_titulo(self, usuario: Usuario, novo_titulo: str):
        if usuario is not self.autor:
            raise PermissionError("Apenas o autor pode realizar essa ação")
        self.titulo = novo_titulo

    def salvar(self):
        database.livros[self.id] = self

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
        l = Livro('', [], Usuario('', '', salvar=False), salvar=False) # Um livro sem titulo, sem conteudo e com autor anonimo
        
        l.__nao_atualizar_data_de_atualizacao = True

        l.id = dados["id"]
        l.titulo = dados["titulo"]
        l.conteudo = dados["conteudo"]
        
        l.data_de_criacao = datetime.strptime(dados["data_de_criacao"], r"%d/%m/%Y, %H:%M:%S")
        l.data_de_atualizacao = datetime.strptime(dados["data_de_atualizacao"], r"%d/%m/%Y, %H:%M:%S")
        
        l.salvar()

        l.autor = fetch(dados["autor"], "usuarios")
        l.usuarios_autorizados = {fetch(id, "usuarios") for id in dados["usuarios_autorizados"]}
        
        l.__nao_atualizar_data_de_atualizacao = False
        
        return l
    def __setattr__(self: Any, name: str, value: Any):
        EmptyClass.__setattr__(self, name, value)
        update(self)


class UICompleto:
    def __init__(self):
        carregar_banco()
        print("Seja bem vindo!")
        r = ui.radio((
            "Registrar-se",
            "Fazer login",
            # "Entrar como anônimo",
        ))

        match r:
            case "Registrar-se":
                self.registrar_se()
            case "Fazer login":
                self.login()
            case _:
                print("Ok, isso não deveria ter acontecido.")
                return None

        self.interface()
    def registrar_se(self):
        print('\n==== REGISTRE-SE ====')
        while True:
            nome = input(f'{red}*{res} Seu nome: ')
            if nome not in database.UNIQUES.usuarios_nome:
                break
            print(f'{red}⚠{res} Já existe um usuário com esse nome.\n')
        
        while True:
            senha = input(f'{red}*{res} Senha: ')
            senha_confirma = input(f'{red}*{res} Confirmar senha: ')
            if senha == senha_confirma:
                break
            print(f"{red}⚠{res} Senha diferentes.\n")
        
        self.auth_user = Usuario(nome, senha)
        salvar_banco()
        print("=====================")
    
    def login(self):
        print('\n==== ENTRAR ====')
        if len(database.usuarios) == 0:
            print("Não existem outros usuários no banco.")
            while True:
                print("Deseja registrar-se?")
                if ui.confirmar():
                    self.registrar_se()
                    return
                else:
                    print("Você não tem outra escolha.\n")
                
        while True:
            nome = input(f'{red}*{res} Seu nome: ')
            senha = input(f'{red}*{res} Senha: ')

            usuario_encontrado = None
            for usuario in database.usuarios.values():
                if nome == usuario.nome:
                    usuario_encontrado = usuario
                    break
            if usuario_encontrado is not None:
                if usuario_encontrado.senha == senha:
                    print(f'{green}Login concluido{res}')
                    break
            print(f"{red}⚠{res} Nome ou senha incorretos.\n")
        
        self.auth_user = usuario_encontrado
        print("=====================")

    def criar_uma_biblioteca(self):
        print("\n==== CRIE UMA BIBILIOTECA ====")

        biblioteca = self.auth_user.cadastrar_biblioteca(input("Nome da sua biblioteca: "))
        biblioteca.adicionar_estantes(self.auth_user, int_input("Quantas estantes sua biblioteca terá? > "))

        if len(database.usuarios) <= 1: # Só existe um usuário em todo o banco. Não faz sentido pedir para autorizar "outros"
            return None
        
        print(f'{green}✓ Biblioteca criada com sucesso.{res}')

        print("\nDeseja autorizar mais usuários a modificar sua biblioteca?")
        if ui.confirmar():
            self.autorizar_usuarios_biblioteca(biblioteca)
                   
    def autorizar_usuarios_biblioteca(self, biblioteca: Biblioteca):
        query_name = {user.nome: user for user in database.usuarios.values()}
        
        nomes = database.UNIQUES.usuarios_nome.copy() # Eu vou remover só o nome usuário autenticado. Não quero mecher no banco, por isso faço uma cópia
        nomes.remove(self.auth_user.nome)
        nomes = tuple(nomes) # Não dá pra acessar uma set com índice inteiro. Mas com tupla dá
        
        print()
        nomes_selecionados = ui.radio_many(nomes) # Mostra todos os nomes de usuários disponíveis
        print()
        
        for nome in nomes_selecionados:
            usuario = query_name[nome]
            if usuario not in biblioteca.usuarios_autorizados:
                if len(database.usuarios) > 1:
                    biblioteca.autorizar_usuario(self.auth_user, usuario)
                else:
                    raise Exception(f"{red}⚠{res} Ainda não há outros usuários registrados no sistema.")    
            else:
                biblioteca.usuarios_autorizados.remove(usuario)
        
    def criar_um_livro(self) -> Livro | None:
        # TODO: Implementar um editor de texto integrado tipo o vim
        print('\n==== CRIAR LIVRO ====')
        print(f'{blue}[LOL] Ainda não fiz um editor de texto integrado.{res}')
        
        print(f'Deseja continuar com bloco de notas?')
        if not ui.confirmar():
            return
        print()
        
        titulo = input("Titulo: ")
        print(f"{blue}🛈{res} Você pode separar as páginas adicionando 2 linhas de espaço.")
        print(f"{red}x{res} Feche a janela para concluir o livro.")
        run(rf"notepad.exe temp.txt")
        with open("temp.txt", 'r') as arquivo:
            paginas = arquivo.read().split('\n\n\n')
        livro = self.auth_user.cadastrar_livro(titulo, paginas)
        print(f'{green}✓ Livro criado com sucesso.{res}')
        
        print(f'\nAdicionar livro a alguma biblioteca?')
        if ui.confirmar():
            self.adicionar_livro_a_biblioteca(livro)
        print()
        
        return livro
    
    def formatar_e_exibir_estantes(self, biblioteca: Biblioteca):
        print("\n----- ESTANTES -----")
        for i in range(len(biblioteca.estantes)):
            livros_quantidade = sum(biblioteca.estantes[i].values())                
            print(f"{i + 1}. ", ("/" * livros_quantidade), end=' ')

            if livros_quantidade > 1:
                print(f"({livros_quantidade} livros)", end='')
            print()
        print("---------------------")
    
    def adicionar_livro_a_biblioteca(self, livro: Livro):
        bibliotecas_do_usuario = tuple(self.auth_user.bibliotecas | self.auth_user.bibliotecas_externas)
        
        if len(bibliotecas_do_usuario) == 0:
            print("I'm sorry, mas você não possui e não é autorizado em nenhuma biblioteca.")
            return None
        biblioteca_selecionada = self.selecionar_biblioteca(bibliotecas_do_usuario)

        if len(biblioteca_selecionada.estantes) == 0:
            print(f'{blue}⚠{res} A biblioteca não possui estantes.')
            print(f'Deseja adicionar por conta própria?')
            if ui.confirmar():
                biblioteca_selecionada.adicionar_estantes(
                    self.auth_user, int_input("Insira o novo número de estantes > ")
                )
        self.formatar_e_exibir_estantes(biblioteca_selecionada)

        print("Em quais estantes deseja adicionar quantos do seu livro?")
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
        bibliotecas = tuple(bibliotecas)
        
        N = ui.radio(
            [biblioteca.nome for biblioteca in bibliotecas],
            retornar_indice=True
        )
        biblioteca = bibliotecas[N]
        
        print(f"[>] Biblioteca selecionada: {blue}{biblioteca.nome}{res}")
        return biblioteca
    
    def visitar_biblioteca(self):
        b = self.selecionar_biblioteca(database.bibliotecas.values())
        print(f"\n==== VISITANDO {b.nome} ====")
        while True:
            print("\nO quê deseja fazer?")
            r = ui.radio((
                "Listar livros",
                "Listar estantes",
                "Ler um livro",
                "Encerrar",
            ), retornar_indice=True)
            match r + 1:
                case 1:
                    for livro, tot in b.livros.items():
                        print(f"[|] {livro.titulo} {black}por: {livro.autor.nome}{res} (total: {tot})")
                case 2:
                    self.formatar_e_exibir_estantes(b)
                case 3:
                    if len(b.livros) == 0:
                        print(f"{red}🛈{res} Infelizmente a biblioteca está vazia.")
                        continue
                    livro = self.selecionar_livro(b.livros.keys(), error_msg="A biblioteca não possui nenhum livro.")
                    filename = f"{livro.id}#{livro.autor.id}.txt"
                    with open(filename, "w") as file:
                        file.write(('\n' + ('=' * 100) + '\n').join(livro.conteudo))
                    print("[x] feche o arquivo para concluir a leitura.")
                    run(f"notepad.exe {filename}")
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
            r = ui.radio((
                "Listar livros",
                "Listar estantes",
                "Adicionar um livro",
                "Remover um livro",
                "Autorizar outros usuários",
                "Encerrar operação",
            ), retornar_indice=True)
            print()
            match r + 1:
                case 1:
                    print()
                    for livro in b.livros:
                        print(f'|    {livro.titulo} {black}({livro.autor.nome}){res}')
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
                    print(f"Tem certeza que deseja remover esse livro?")
                    if ui.confirmar(inverter=True):
                        self.exibir_estantes_que_contem_livro(b, livro)
                        b.remover_livro(
                            self.auth_user,
                            livro,
                            estantes_e_quantidades=self.selecionar_estantes_e_quantidades(
                                b, estantes_validas=( i for i, estante in enumerate(b.estantes) if (livro in estante) )
                            )
                        )
                
                case 5:
                    if self.auth_user == b.pertencente:
                        self.autorizar_usuarios_biblioteca(b)
                    else:
                        print(f"{red}⚠{res} Somente o pertencente da biblioteca pode realizar está ação")
                case 6:
                    break
                case _:
                    print(f'{red}⚠{res} Resposta inálida')
        print( '==============================')
    
    def selecionar_estantes(self, biblioteca: Biblioteca, numeros_validos: Optional[Iterable[int]]=None):
        opcoes: list[str] = []
        for i, estante in enumerate(biblioteca.estantes):
            if numeros_validos:
                if i not in numeros_validos:
                    continue
            livros = sum(estante.values())
            opcoes.append('/' * livros + f" {black}({livros} livros){res}")
        return ui.radio_many(opcoes, retornar_indices=True)
      
    def selecionar_quantidades(self, estantes: Iterable[int], error_prompt: str):
        if not estantes:
            raise Exception(error_prompt)
        relacoes: list[tuple[int, int]] = []
        print(f"{blue}🛈{res} Insire a quantidade de livros em cada estante: ")
        
        for e in estantes:
            relacoes.append((
                e,
                int_input(f"Estante {e + 1} > ") # Para o usuário, as estantes começam a ser contadas a partir do 1, mas internamente elas são contadas a partir do 0
            ))
        return relacoes
    
    def selecionar_estantes_e_quantidades(self, biblioteca: Biblioteca, estantes_validas: Optional[Iterable[int]]=None):
        return self.selecionar_quantidades(
            self.selecionar_estantes(biblioteca, estantes_validas),
            error_prompt=f"Ainda não existem estantes na biblioteca {blue}{biblioteca.nome}{res}"
        )

    def selecionar_livro(self, universo: Iterable[Livro], error_msg: str):
        universo = tuple(universo)
        if len(universo) == 0:
            raise Exception(error_msg)
        opcoes: list[str] = []
        for i, livro in enumerate(universo):
            opcoes.append(f"{i + 1}. {livro.titulo} {black}({livro.autor.nome}){res}")
        
        return universo[ui.radio(opcoes, retornar_indice=True)]
    
    def interface(self):
        rodando = True
        while rodando:
            print('\n==== INTERFACE ====')
            r = ui.radio((
                "Visitar uma biblioteca",
                "Criar um livro",
                "Criar uma biblioteda",
                "Gerenciar suas bibliotecas",
                "Encerrar operação",
            ), retornar_indice=True)
            print()
            carregar_banco()
            try:
                match r + 1:
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
                print("\n[!] OPERAÇÃO CANCELADA")
            except Exception as e:
                print(f"[ERRO] {e}")
            salvar_banco()
            
def salvar_banco():
    dados = {
        "usuarios": {id: user.para_json() for id, user in database.usuarios.items()},
        "bibliotecas": {id: lib.para_json() for id, lib in database.bibliotecas.items()},
        "livros": {id: book.para_json() for id, book in database.livros.items()},
    }
    
    with open(DATABASE_NAME, "w") as file:
        json.dump(dados, file, indent=4)

def carregar_banco():
    global json_db
    try:
        with open(DATABASE_NAME, "r") as file:
            json_db = json.load(file)
    except FileNotFoundError, json.decoder.JSONDecodeError:
        return None
    
    if json_db is None:
        return None
    
    for id in json_db["usuarios"]:
        fetch(id, type="usuarios")
    
    for id in json_db["bibliotecas"]:
        fetch(id, type="bibliotecas")
    
    for id in json_db["livros"]:
        fetch(id, "livros")
