catan
-----

Package catan provides models for representing and manipulating a game of catan

`.catan` files will be written to the working directory by class Game (see [`catanlog`](https://github.com/rosshamish/catanlog)).

class Game also supports undo and redo, which is useful for building GUIs.

Supports Python 3. Might work in Python 2.

Thanks to the original author: Ross Anderson ([rosshamish](https://github.com/rosshamish)) for starting the project

> Author: Jerry Zheng ([jerry123z](https://github.com/jerry123z))

### Usage

```
import catan.board
import catan.game
import catan.trading

players = [catan.game.Player(1, 'ross', 'red'),
           catan.game.Player(2, 'josh', 'blue'),
           catan.game.Player(3, 'yuri', 'green'),
           catan.game.Player(4, 'zach', 'orange')]
board = catan.board.Board()
game = catan.game.Game(board=board)

game.start(players)
print(game.get_cur_player())  # -> ross (red)
game.buy_settlement((13,6))
game.buy_road((13,5))
game.end_turn()
...
game.roll(6)
game.trade(trade=catan.trading.CatanTrade(...))
game.undo()
game.redo()
game.play_knight(...)
game.end_turn()
...
game.end()
```

See [`catan-spectator`](https://github.com/rosshamish/catan-spectator) for extensive usage.

### File Format

<!-- remember to update this section in sync with "File Format" in github.com/rosshamish/catan-spectator/README.md -->

catan-spectator writes game logs in the `.catan` format described by package [`catanlog`](https://github.com/rosshamish/catanlog).

They look like this:

```
green rolls 6
blue buys settlement, builds at (1 NW)
orange buys city, builds at (1 SE)
red plays dev card: monopoly on ore
```

### Documentation

Most classes and modules are documented. Read the docstrings! If something is confusing or missing, open an issue.

### License

GPLv3
