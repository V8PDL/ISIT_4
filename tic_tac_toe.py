from typing import Dict, List, TypeVar;
from random import choice, random;
from matplotlib import pyplot;

Position = TypeVar('Position');
Player = TypeVar('Player');
Board = TypeVar('Board');
Comfortable_Counter = TypeVar('Comfortable_Counter');
board_size: int = 3;
available_items: List[str] = ['x', 'o'];
default_value: float = 0.5;
win_value: float = 1.0;
lose_value: float = 0.0;
draw_value: float = 0.5;
whitespace: str = ' ';
default_alpha: float = 0.1;
default_epsilon: float = 0.05;


class Comfortable_Counter:

    current_value: int;
    step: int;

    def __init__(self, start_value: int = 0, step: int = 1) -> None:
        self.current_value = start_value;
        self.step = step;

    def __next__(self):
        self.current_value += self.step;
        return self.current_value;


class Board:

    all_positions: Dict[str, Position];
    position: Position;
    starting_position: Position;
    winning_item: str;

    def __init__(self,  winning_item: str = 'x') -> None:
        self.starting_position = Position(self, [whitespace for _ in range(0, board_size * board_size)]);
        self.all_positions = dict();
        self.all_positions[self.starting_position.to_string()] = self.starting_position;
        self.position = self.starting_position;
        self.winning_item = winning_item;

    def print(self) -> None:
        [print(f' {cell} ', end='' if (index + 1) % board_size else "\n")
         for index, cell in enumerate(self.position.items)];

    def reverse_winner(self) -> None:
        for position in self.all_positions.values():
            winner = position.get_winner();
            position.value = 1.0 if winner == self.winning_item else 0.0 if winner is not None else position.value;

    def play(self, players: List[Player], verbose: bool = False) -> None:
        self.position = self.starting_position;
        sorted_players = [next(player for player in players if player.item == item) for item in available_items];
        [player.new_game() for player in sorted_players if player is Bot];
        player_index: int = 0;
        while True:
            player = sorted_players[player_index];
            player_index = (player_index + 1) % len(sorted_players);
            if self.position.next_positions is None or len(self.position.next_positions) < 1:
                winner = self.position.get_winner();
                [player.fix_game(None if winner is None else winner == player.item) for player in sorted_players];
                return;
            next_move = player.get_move(self);
            if next_move.to_string() not in self.position.next_positions:
                print('[JustGINCS] Something gone wrong 🤡');
                return;
            self.position = next_move;
            print(f"Move of {player.name}:") if verbose and player is not Human else None;
            self.print() if verbose else None;

    def play_many(self, players: List[Player], games_count: int = 1000) -> None:
        [self.play(players) for _ in range(0, games_count)]


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
        max_value = max(position.value for position in list(
            self.next_positions.values()));
        return choice([position for position in list(self.next_positions.values()) if position.value == max_value]);

    def get_random_move(self) -> Position:
        return choice(list(self.next_positions.values()));

    def get_winner(self) -> str | None:
        for item in available_items:
            if (sum(cell == item for index, cell in enumerate(self.items)
                    if (index % board_size) == int(index / board_size)) == board_size
                or sum(cell == item for index, cell in enumerate(self.items)
                       if (board_size - 1 - (index % board_size)) == int(index / board_size)) == board_size):
                return item;
            for i in range(0, board_size):
                if (sum(cell == item for index, cell in enumerate(self.items)
                        if int(index / board_size) == i) == board_size
                    or sum(cell == item for index, cell in enumerate(self.items)
                           if (index % board_size) == i) == board_size):
                    return item;
        return None;

    def search_positions(self, item_index: int = 0) -> None:
        winner = self.get_winner();
        if winner is not None:
            self.value = win_value if winner == self.board.winning_item else lose_value;
            self.next_positions = None;
            return;
        self.value = default_value;
        self.next_positions = dict();

        new_positions: List[Position] = list();
        for index, cell in enumerate(self.items):
            if cell != whitespace:
                continue;
            new_items = self.items.copy();
            new_items[index] = available_items[item_index];
            new_position = Position(self.board, new_items);
            string_position = new_position.to_string();
            if string_position in self.board.all_positions:
                self.next_positions[string_position] = self.board.all_positions[string_position];
                continue;
            self.next_positions[string_position] = new_position;
            self.board.all_positions[string_position] = new_position;
            new_positions.append(new_position);

        [position.search_positions((item_index + 1) % len(available_items)) for position in new_positions];

    def to_string(self) -> str:
        return ''.join(self.items);


class Player:

    item: str;
    name: str;
    games_history: List[bool | None];

    def __init__(self, board: Board, item: str = 'x', name: str = None) -> None:
        self.board = board;
        self.item = item;
        self.name = name if name is not None else f"{type(self)} {item}";
        self.games_history = list();

    def set_name(self, new_name: str) -> None:
        self.name = new_name;

    def get_move(self, board: Board = None) -> Position:
        raise NotImplementedError(self);

    def fix_game(self, winner: bool | None) -> None:
        self.games_history.append(winner);

    def print_stats(self) -> None:
        if self.games_history is None or len(self.games_history) < 1:
            print("No games were played!");
            return;
        total_games = len(self.games_history);
        win_count = len([game for game in self.games_history if game]);
        lose_count = len([game for game in self.games_history if game == False]);
        draw_count = len([game for game in self.games_history if game is None]);
        print(f"""
Player: {self.name}
Winrate: {win_count / total_games} ({win_count})
LoseRate: {lose_count / total_games} ({lose_count})
DrawRate: {draw_count / total_games} ({draw_count})

Total: {total_games}""");

    def throw_me_some_numbers(self, step: int = None) -> None:
        step = int(len(self.games_history) / 100) if step is None else step;
        if step < 2:
            print("Not enough games for statistics");
            return;
        means = [self.games_history[i * step: (i + 1) * step].count(True) / step for i in range(0, 100)];
        games_counts = [step * i + step / 2 for i in range(0, 100)];
        pyplot.plot(games_counts, means);
        pyplot.ylabel('Winrate');
        pyplot.xlabel('Games count');
        pyplot.show();


class Bot(Player):

    epsilon: float;
    alfa: float;
    board: Board;
    games_history: List[bool | None];
    last_move: Position;

    def __init__(self, board: Board, epsilon: float, alfa: float, item: str = 'x', name: str = 'Bot (x)') -> None:
        self.games_history: List[bool | None] = list();
        self.epsilon = epsilon;
        self.alfa = alfa;
        self.last_move = None;
        super().__init__(board, item, name);

    def new_game(self) -> None:
        self.last_move = None;

    def get_move(self, board: Board) -> Position:
        self_position = self.board.all_positions[board.position.to_string()];
        is_greedy = random() > self.epsilon;
        move = self_position.get_best_move() if is_greedy else self_position.get_random_move();
        if self.last_move is not None:
            if move.value == 1.0:
                a = 1;
                b = 2;
            self.last_move.value += self.alfa * (move.value - self.last_move.value);
        self.last_move = move;
        return move;


class Randomer(Player):

    def get_move(self, board: Board) -> Position:
        return board.position.get_random_move();


class Smart_Randomer(Player):

    def get_move(self, board: Board = None) -> Position:
        possible_moves = list(board.position.next_positions.values());
        best_move = next((move for move in possible_moves if move.get_winner() == self.item), None);
        return best_move if best_move is not None else choice(possible_moves);


class Human(Player):

    def get_move(self, board: Board) -> Position:
        while True:
            player_move = input('Write your move ("x y"): ')
            if player_move == 'exit':
                return None
            try:
                x, y = [int(i) for i in player_move.split(' ')]
                if x < 1 or y < 1 or x > board_size or y > board_size:
                    print(f'Wrong numbers, it should be more then 0 and less then board size ({board_size})');
                    continue;
                if board.position.items[(x - 1) * board_size + (y - 1)] != whitespace:
                    print('Cell is already taken');
                    continue;
                else:
                    new_items = board.position.items.copy();
                    new_items[(x - 1) * board_size + (y - 1)] = self.item;
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
        input_str = input(
            f'''\n[JustGINCS] Type "{stop_word}" to exit from dialog.\n\n{f"[JustGINCS] Choose number {f'from 1 to {max_value}' if max_value is not None else ''}" if message is None else message}''');
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
    smart_randomizers: Dict[str, Player] = dict();
    bots: Dict[str, Player] = dict();
    for item in available_items:
        new_board = Board(item);
        humans[item] = Human(new_board, item, f'Human {item}');
        randomizers[item] = Randomer(new_board, item, f'Randomizer {item}');
        smart_randomizers[item] = Smart_Randomer(new_board, item, f"Smart Randomizer ({item})");
        bots[item] = Bot(new_board, default_epsilon, default_alpha, item, f'AI {item}');

    players = list(humans.values()) + list(randomizers.values()) + list(smart_randomizers.values()) + list(bots.values());

    print('[JustGINCS] Initializing boards, wait, please...');
    [bot.board.position.search_positions() for bot in bots.values()];

    while True:
        number = Comfortable_Counter();
        input_number = input_int(f"""[JustGINCS] Choose what to do:

{''.join([f"{next(number)}. Change properties of bot {bot.name}🤡" for bot in bots.values()])}
{''.join([f"{next(number)}. Educate bot {bot.name} with randomizer🤡" for bot in bots.values()])}
{''.join([f"{next(number)}. Educate bot {bot.name} with smart randomizer🤡" for bot in bots.values()])}
{''.join([f"{next(number)}. Reset education for bot {bot.name}🤡" for bot in bots.values()])}
{''.join([f"{next(number)}. Play with bot as {item}🤡" for item in bots.keys()])}
{''.join([f"{next(number)}. Get statistic of {player.name}🤡" for player in players])}
{''.join([f"{next(number)}. Clear statistic of {player.name}🤡" for player in players])}
{''.join([f"{next(number)}. Print graph for {player.name}🤡" for player in players])}

Enter a value: """.replace('🤡', '\n'), number.current_value);
        if input_number < 0:
            break;
        elif input_number <= 1 * len(bots):
            item = available_items[(input_number - 1) % len(bots)];
            parameter_number = input_int('''[JustGINCS] Set:
1. Name
2. Alpha
3. Epsilon

Enter a value: ''', 3);
            if parameter_number < 0:
                continue;
            value_str = input('[JustGINCS] Enter a value for parameter: ');
            if parameter_number == 1:
                bots[item].name = value_str;
            elif parameter_number == 2 and value_str.replace('.', '', 1).isdigit() and float(value_str) > 0:
                bots[item].alfa = float(value_str);
            elif parameter_number == 3 and value_str.replace('.', '', 1).isdigit() and float(value_str) > 0 and float(value_str) <= 1:
                bots[item].epsilon = float(value_str);
            else:
                print('[JustGINCS] Error, canceling operation');
        elif input_number <= 3 * len(bots):
            games_count = input_int(
                message ='[JustGINCS] Enter number of games to be played: ', error_message='[JustGINCS] Wrong games count');
            if games_count < 0:
                continue;
            item = available_items[(input_number - 1) % len(bots)];
            opponents = [bot for bot in randomizers.values() if bot.item != item] if input_number <= 2 * len(bots) else [bot for bot in smart_randomizers.values() if bot.item != item]
            opponents.append(bots[item])
            bots[item].board.play_many(opponents, games_count);
        elif input_number <= 4 * len(bots):
            item = available_items[(input_number - 1) % len(bots)];
            bots[item].board = Board(item);
        elif input_number <= 5 * len(bots):
            item = available_items[(input_number - 1) % len(bots)];
            opponents = [bot for bot in bots.values() if bot.item != item];
            opponents.append(humans[item]);
            choice(opponents).board.play(opponents, True);
        elif input_number <= 5 * len(bots) + len(players):
            index = input_number - 5 * len(bots) - 1;
            players[index].print_stats();
        elif input_number <= 5 * len(bots) + 2 * len(players):
            index = input_number - 5 * len(bots) - len(players) - 1;
            players[index].games_history = list();
        elif input_number <= 5 * len(bots) + 3 * len(players):
            index = input_number - 5 * len(bots) - 2 * len(players) - 1;
            players[index].throw_me_some_numbers();