from typing import Dict, List, TypeVar;
from random import choice, random;

Position = TypeVar('Position');
Player = TypeVar('Player');
board_size = 3;
available_items = ['x', 'o'];
default_value = 0.5;
whitespace = ' ';

class Board:

    size: int;
    available_items: List[str];
    all_positions: Dict[str, Position];
    default_value: float;
    position: Position;
    starting_position: Position;
    winning_item: str;
    win_value: float = 1.0;
    lose_value: float = 0.0;
    draw_value: float = 0.85;

    def __init__(self, size: int = 3, available_items: List[str] = [ 'x', 'o' ], default_value = 0.5, winning_item = 'x') -> None:
        self.size = size;
        self.available_items = available_items;
        self.default_value = default_value;
        self.starting_position = Position(self, [whitespace for _ in range(0, self.size * self.size)]);
        self.all_positions = dict();
        self.all_positions[self.starting_position.to_string()] = self.starting_position;
        self.position = self.starting_position;
        self.winning_item = winning_item;

    def print(self) -> None:
        [print(f' {cell} ', end = '' if (index + 1) % self.size else "\n") for index, cell in enumerate(self.position.items)];

    def reverse_winner(self) -> None:
        for position in self.all_positions.values():
            position.value = 1 if position.value == 0 else 0 if position.value == 1 else position.value;

    def play(self, players: List[Player], verbose: bool = False) -> None:
        self.position = self.starting_position;
        [player.moves_history.clear() for player in players if player is Bot];
        while True:
            for player in players:
                if self.position.next_positions is None or len(self.position.next_positions) < 1:
                    winner = self.position.get_winner();
                    [player.fix_game(None if winner is None else winner == player.item) for player in players if player is Bot];
                    return;
                next_move = player.get_move(self);
                if next_move.to_string() not in self.position.next_positions:
                    print('[JustGINCS] Something gone wrong 🤡');
                    return;
                self.position = next_move;
                [p.fix_move() for p in players if p is Bot];
                self.print() if verbose else None;

    def play_many(self, players: List[Player], games_count: int = 1000) -> None:
        for i in range(0, games_count):
            self.play(players);
            if games_count > 20 and i % int(games_count / 20) == 0:
                print(f'[JustGINCS] {int((i / games_count) * 100)}% was played...');


class Position:

    items: List[str];
    board: Board;
    value: float;
    next_positions: Dict[str, Position];

    def __init__(self, board: Board, items: List[str], value: float = None, next_positions: Dict[str, Position] = None) -> None:
        self.items = items;
        self.board = board;
        self.value = value;
        self.next_positions = next_positions;

    def get_best_move(self) -> Position:
        max_value = max(position.value for position in list(self.next_positions.values()));
        return choice([position for position in list(self.next_positions.values()) if position.value == max_value]);

    def get_random_move(self) -> Position:
        return choice(list(self.next_positions.values()));

    def get_winner(self) -> str | None:
        for item in self.board.available_items:
            if (sum(cell == item for index, cell in enumerate(self.items)
                    if (index % self.board.size) == int(index / self.board.size)) == self.board.size
                or sum(cell == item for index, cell in enumerate(self.items)
                    if (self.board.size - (index % self.board.size)) == int(index / self.board.size)) == self.board.size):
                return item;
            for i in range(0, self.board.size):
                if (sum(cell == item for index, cell in enumerate(self.items)
                        if int(index / self.board.size) == i) == self.board.size
                    or sum(cell == item for index, cell in enumerate(self.items)
                        if (index % self.board.size) == i) == self.board.size):
                    return item;
        return None;

    def search_positions(self, item_index: int = 0, default_value: float = 0.5, recursively: bool = True) -> None:
        winner = self.get_winner();
        if winner is not None:
            self.value = self.board.win_value if winner == self.board.winning_item else self.board.lose_value;
            self.next_positions = None;
            return;
        self.value = default_value;
        self.next_positions = dict();

        new_positions: List[Position] = list();
        for index, cell in enumerate(self.items):
            if cell != self.board.whitespace:
                continue;
            new_items = self.items.copy();
            new_items[index] = self.board.available_items[item_index];
            new_position = Position(self.board, new_items);
            string_position = new_position.to_string();
            if string_position in self.board.all_positions:
                self.next_positions[string_position] = self.board.all_positions[string_position];
                continue;
            self.next_positions[string_position] = new_position;
            self.board.all_positions[string_position] = new_position;
            new_positions.append(new_position);

        [position.search_positions((item_index + 1) % len(self.board.available_items), default_value) for position in new_positions];

    def to_string(self) -> str:
        return ''.join(self.items);


class Player:

    item: str;
    name: str;

    def __init__(self, board: Board, item: str = 'x', name = None) -> None:
        self.board = board;
        self.item = item;
        self.name = name;

    def set_name(self, new_name: str) -> None:
        self.name = new_name;

    def get_move(self, board: Board = None) -> Position:
        raise NotImplementedError(self);


class Bot(Player):

    epsilon: float;
    alfa: float;
    board: Board;
    moves_history: List[Position];
    games_history: List[bool];

    def __init__(self, board: Board, epsilon: float, alfa: float, item: str = 'x', name = 'Bot') -> None:
        self.moves_history: List[Position] = list();
        self.games_history: List[bool | None] = list();
        self.epsilon = epsilon;
        self.alfa = alfa;
        super().__init__(board, item, name);

    def get_move(self, board: Board) -> Position:
        is_greedy = random() > self.epsilon;
        return board.position.get_best_move() if is_greedy else board.position.get_random_move();

    def fix_game(self, winner: bool) -> None:
        self.games_history.append(winner);
        for move in self.moves_history:
            result = 0.5 if winner is None else 1 if winner else 0;
            diff = (result - move.value) * self.alfa;
            move.value += diff;


class Randomer(Player):

    def get_move(self, board: Board) -> Position:
        return board.position.get_random_move();


class Human(Player):

    def get_move(self, board: Board) -> Position:
        while True:
            player_move = input('Write your move ("x y"): ');
            if player_move == 'exit':
                return None;
            try:
                x, y = [int(i) for i in player_move.split(' ')];
                if x < 1 or y < 1 or x > board.size or y > board.size:
                    print(f'Wrong numbers, it should be more then 0 and less then board size ({board.size})');
                    continue;
                if board.position.items[(x - 1) * board.size + (y - 1)] != board.whitespace:
                    print('Cell is already taken');
                    continue;
                else:
                    new_items = board.position.items.copy();
                    new_items[(x - 1) * board.size + (y - 1)] = self.item;
                    new_position_key = "".join(new_items);
                    if new_position_key not in board.position.next_positions:
                        print('Wrong position anyway...');
                        continue;
                    new_position = board.position.next_positions[new_position_key];
                    winner = new_position.get_winner();
                    if winner is not None:
                        print(f"{self.name}, you {'won' if winner == self.item else 'lost'}!");
                    elif new_position.next_positions is None or len(new_position.next_positions) < 1:
                        print(f"{self.name}, it is draw!");
                    return new_position;
            except:
                print('Wrong input, try again. Write \'exit\' to exit.');


def input_int(message: str = None, max_value: int = None, error_message: str = None, stop_word: str = 'exit') -> int:
    while True:
        input_str = input(f'''[JustGINCS] Type "{stop_word}" to exit from dialog.\n\n{f"[JustGINCS] Choose number {f'from 1 to {max_value}' if max_value is not None else ''}" if message is None else message}''');
        if input_str.lower() == stop_word:
            return -1;
        if input_str.isdigit() and int(input_str) > 0 and (max_value is None or int(input_str) <= max_value):
            return int(input_str);
        else:
            print('[JustGINCS] Error, try again' if error_message is None else error_message);


if __name__ == '__main__':
    print('[JustGINCS] Tic-Tac-Toe bot with reinforcement learning by Gavrilyuk I.P., Efremov D.S., Ivanov A.G., Kachanov F.K.');

    print('[JustGINCS] Initializing players, wait please...');
    humans: Dict[str, Player] = dict();
    randomizers: Dict[str, Player] = dict();
    bots: Dict[str, Player] = dict();
    for item in available_items:
        new_board = Board(3, available_items, 0.5, whitespace, item);
        humans[item] = Human(new_board, item, f'Human {item}');
        randomizers[item] = Randomer(new_board, item, f'Randomizer {item}');
        bots[item] = Bot(new_board, 0.05, 0.1, item, f'AI {item}');

    print('[JustGINCS] Initializing boards, wait, please...');
    bots['x'].board.position.search_positions();
    bots['o'].board.all_positions = bots['x'].board.all_positions.copy();
    bots['o'].board.starting_position = bots['x'].board.starting_position;
    bots['o'].board.reverse_winner();

    input_number = -1;
    while True:
        input_number = input_int('''[JustGINCS] Choose what to do:
1. CHange stats of bot (x)
2. Change stats of bot (o)
3. Educate bot (x)
4. Educate bot (o)
5. Reset education (x)
6. Reset education (o)
7. Change your name (?)
8. Play with bot as x
9. Play with bot as o

Enter a value: ''', 10);
        if input_number < 0:
            break;
        elif input_number == 1 or input_number == 2:
            item = 'x' if input_number == 1 else 'o';
            parameter_number = input_int('''[JustGINCS] Set:
1. Name
2. Alpha
3. Epsilon

Value: ''', 3);
            if parameter_number < 0:
                break;
            value_str = input('[JustGINCS] Enter a value for parameter: ');
            if parameter_number == 1:
                bots[item].name = value_str;
            elif parameter_number == 2 and value_str.replace('.', '', 1).isdigit() and float(value_str) > 0 and float(value_str) < 1:
                bots[item].alfa = float(value_str);
            elif parameter_number == 3 and value_str.replace('.', '', 1).isdigit() and float(value_str) > 0 and float(value_str) < 1:
                bots[item].epsilon = float(value_str);
            else:
                print('[JustGINCS] Error, canceling operation');
        elif input_number == 3 or input_number == 4:
            games_count = input_int(message = '[JustGINCS] Enter number of games to be played: ', error_message = '[JustGINCS] Wrong games count');
            if games_count < 0:
                break;
            item = 'x' if input_number == 3 else 'o';
            reverse_item = 'o' if input_number == 3 else 'x';
            bots[item].board.play_many([bots[item], randomizers[reverse_item]], games_count);
        elif input_number == 5 or input_number == 6:
            item = 'x' if input_number == 5 else 'o';
            bots[item].board.all_positions.clear();
            bots[item].board.all_positions[bots[item].board.starting_position.to_string()] = bots[item].board.starting_position();
            bots[item].board.position = bots[item].board.starting_position;
            bots[item].board.position.search_positions();
        elif input_number == 7:
            new_name = input('[JustGINCS] Enter new name: ');
            [human.set_name(new_name) for human in humans.values()];
        elif input_number == 8:
            bots['o'].board.play([humans['x'], bots['o']], True);
        elif input_number == 9:
            bots['x'].board.play([bots['x'], humans['o']], True);