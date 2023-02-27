from typing import List
import PySimpleGUI as psg
import socket
import threading
from random import choice, randint


def main():
    ip = "127.0.0.1"
    port = 54543
    srv = Server(ip=ip, port=port)
    game = Game()
    gui = GUI(ip=ip, port=port, game=game)

    psg.theme("BrightColors")
    window = psg.Window(title="2048 Clone", size=(830, 480), layout=gui.layout(), use_default_focus=False,
                        finalize=True)
    window.bind("<w>", "up")
    window.bind("<s>", "down")
    window.bind("<a>", "left")
    window.bind("<d>", "right")
    while True:
        event, values = window.read(timeout=int(1000 / 30))
        if event == psg.WINDOW_CLOSED:
            break
        if event == "Quit":
            break

        if event in "up":
            game.game_input(game.UP)

        if event in "down":
            game.game_input(game.DOWN)

        if event in "left":
            game.game_input(game.LEFT)

        if event in "right":
            game.game_input(game.RIGHT)

        if game.is_over:
            psg.PopupError("Game Over")

        window = gui.update(window)
    window.close()


class Game:
    def __init__(self):
        self.__score = 0
        self.__board = [[0] * 4 for _ in range(4)]

        self.__is_over = False
        self.__add()

        self.__UP: int = 0
        self.__DOWN: int = 1
        self.__RIGHT: int = 2
        self.__LEFT: int = 3

        self.__ROTATE90: int = 1
        self.__ROTATE180: int = 2
        self.__ROTATE270: int = 3

    def __add(self):
        can = set()
        for y in range(4):
            for x in range(4):
                if self.__board[y][x] == 0:
                    can.add((y, x))
        if not can:
            self.__is_over = self.__end()
            return
        y, x = choice(list(can))
        if randint(0, 9):
            self.__board[y][x] = 2
        else:
            self.__board[y][x] = 4

    def __end(self):
        near = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for i in range(4):
            for j in range(4):
                num = self.__board[i][j]
                for x, y in near:
                    v = i + y
                    u = j + x
                    if 0 <= u < 4 and 0 <= v < 4 and self.__board[v][u] == num:
                        return False
        return True

    def __calc(self):
        for x in range(4):
            count = 0
            array = [0] * 4
            for y in range(4):
                if self.__board[y][x] == 0:
                    continue
                array[count] = self.__board[y][x]
                count += 1
            index = 0
            count = 0
            a = [0] * 4
            while index < 4:
                if index != 3 and array[index] == array[index + 1] and array[index] != 0:
                    a[count] = array[index] * 2
                    self.__score += array[index] * 2
                    index += 2
                else:
                    if array[index] != 0:
                        a[count] = array[index]
                    index += 1
                count += 1
            for y, num in enumerate(a):
                self.__board[y][x] = num
        self.__add()

    def game_input(self, op: int):
        if op == self.UP:
            self.__calc()

        if op == self.RIGHT:
            self.rotate_l(self.__ROTATE90)
            self.__calc()
            self.rotate_l(self.__ROTATE270)

        if op == self.DOWN:
            self.rotate_l(self.__ROTATE180)
            self.__calc()
            self.rotate_l(self.__ROTATE180)

        if op == self.LEFT:
            self.rotate_l(self.__ROTATE270)
            self.__calc()
            self.rotate_l(self.__ROTATE90)

    def rotate_l(self, rotate: int):
        def r():
            rotated = [[0] * 4 for _ in range(4)]
            for i in range(4):
                for j in range(4):
                    rotated[4 - 1 - j][i] = self.__board[i][j]
            self.__board = rotated

        for _ in range(rotate):
            r()

    @property
    def score(self):
        return self.__score

    @property
    def board(self):
        return self.__board

    @property
    def UP(self) -> int:
        return self.__UP

    @property
    def DOWN(self) -> int:
        return self.__DOWN

    @property
    def RIGHT(self) -> int:
        return self.__RIGHT

    @property
    def LEFT(self) -> int:
        return self.__LEFT

    @property
    def is_over(self):
        return self.__is_over


class GUI:
    def __init__(self, ip, port, game: Game) -> None:
        self.__tile_color: List[str] = ["OliveDrab1", "OliveDrab2"]
        self.__text_color: str = ""
        self.__new_text_color: str = ""
        self.__size = (4, 4)
        self.__game_font = ("hoge", 24)
        self.__font = ("hoge", 20)
        self.__ip = ip
        self.__port = port
        self.__game = game

    def update(self, window: psg.Window):
        board = self.__game.board
        for width in range(self.__size[0]):
            for height in range(self.__size[1]):
                if board[width][height]:
                    window[f"{width}, {height}"].update(f"\n{board[width][height]}\n")
                else:
                    window[f"{width}, {height}"].update("")
        window["score"].update(f"Score: {self.__game.score}")
        return window

    def layout(self) -> List[List]:
        gui_layout = [[self.__game_window(),
                       self.__control_panel()]]
        return gui_layout

    def __game_window(self) -> psg.Frame:
        return psg.Frame(title="",
                         layout=[[psg.Text("",
                                           font=self.__game_font,
                                           text_color="orange red",
                                           justification="c",
                                           size=(7, 3),
                                           background_color=self.__tile_color[int(height % 2 == width % 2)],
                                           key=f"{width}, {height}")
                                  for height in range(self.__size[0])] for width in range(self.__size[1])],
                         background_color="OliveDrab4")

    def __control_panel(self) -> psg.Frame:
        return psg.Frame(title=" Control Panel ", layout=[
            [self.__operation()],
            [self.__score()],
            [self.__server()],
        ], element_justification="l")

    def __operation(self) -> psg.Frame:
        return psg.Frame(title=" Operation ", layout=[
            [psg.Button(button_text="Undo", disabled=True, disabled_button_color="silver", font=self.__font),
             psg.Button(button_text="Redo", disabled=True, disabled_button_color="silver", font=self.__font)],
            [psg.Button(button_text="Continue", disabled=True, disabled_button_color="silver", font=self.__font)],
            [psg.Button(button_text="Quit", font=self.__font)]
        ], element_justification="l")

    def __score(self) -> psg.Frame:
        return psg.Frame(title=" Game Data ", layout=[
            [psg.Text(text=f"Score: {0}", font=self.__font, key="score")],
            [psg.Text(text=f"HI: {0}", font=self.__font, text_color="silver")],
            [psg.Text(text=f"Move: {0}", font=self.__font, text_color="silver")]
        ])

    def __server(self) -> psg.Frame:
        return psg.Frame(title=" Server ", layout=[
            [psg.Text(text=f"IP: {self.__ip}", font=self.__font)],
            [psg.Text(text=f"Port: {self.__port}", font=self.__font)]
        ])


class Server:
    def __init__(self, ip: str, port: int, timeout=3, callback=None):
        self.address = (ip, port)
        self.buffer_size = 4096
        self.connecting = True
        self.connection = None
        self.timeout = timeout
        self.thread = None
        self.callback = callback

    def run_server(self):
        self.thread = threading.Thread(target=self.__server_th)
        self.thread.start()

    def __server_th(self):
        if self.connection is None:
            self.server = socket.create_server(self.address)
            self.server.listen()
            self.connection, self.addr = self.server.accept()
        self.connection.settimeout(self.timeout)
        while self.connecting:
            try:
                s = self.connection.recv(self.buffer_size)
                self.on_receive(s)
            except socket.timeout:
                pass
            except:
                self.connecting = False
                self.connection.close()
                self.connection = None

    def on_receive(self, s):
        if self.callback is not None:
            self.callback(s)
        else:
            print(s)

    def send(self, s):
        if self.connection is not None:
            self.connection.send(s.encode("UTF-8"))
        else:
            print("No connection!!")

    def close(self):
        self.connecting = False
        if self.connection is not None:
            self.connection.close()
        self.thread.join()


if __name__ == '__main__':
    main()
