# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "pydantic",
#     "pygame",
#     "pyyaml",
# ]
# ///
import random
import sys
from typing import Dict, Tuple

import click
import pygame
import yaml  # for loading YAML config
from pydantic import BaseModel


# --- New config model (using pydantic) ---
class GameConfig(BaseModel):
    background_color: Tuple[int, int, int] = (250, 248, 239)
    grid_color: Tuple[int, int, int] = (187, 173, 160)
    text_color: Tuple[int, int, int] = (119, 110, 101)
    light_text: Tuple[int, int, int] = (249, 246, 242)
    empty_tile: Tuple[int, int, int, int] = (205, 193, 180, 50)
    tile_colors: Dict[int, Tuple[int, ...]] = {
        0: (205, 193, 180, 50),
        2: (238, 228, 218),
        4: (237, 224, 200),
        8: (242, 177, 121),
        16: (245, 149, 99),
        32: (246, 124, 95),
        64: (246, 94, 59),
        128: (237, 207, 114),
        256: (237, 204, 97),
        512: (237, 200, 80),
        1024: (237, 197, 63),
        2048: (237, 194, 46),
    }
    text_colors: Dict[int, Tuple[int, int, int]] = {
        2: (119, 110, 101),
        4: (119, 110, 101),
    }


# --- New Game class holding the game logic ---
class Game:
    """Handles game state and logic for 2048."""

    def __init__(self, grid_size: int) -> None:
        self.grid_size = grid_size
        self.board = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        self.score = 0
        self.game_over = False
        self.new_tile_position = None
        self.animation_start_time = 0
        self.empty_cells: set[tuple[int, int]] = {
            (i, j) for i in range(grid_size) for j in range(grid_size)
        }
        self.last_move_time: int = 0  # for debouncing moves

    def update_empty_cells(self) -> None:
        self.empty_cells = {
            (i, j)
            for i in range(self.grid_size)
            for j in range(self.grid_size)
            if self.board[i][j] == 0
        }

    def add_random_tile(self) -> tuple[int, int] | None:
        self.update_empty_cells()  # ensure board and list are in sync
        if not self.empty_cells:
            return None
        row_idx, col_idx = random.choice(list(self.empty_cells))
        self.board[row_idx][col_idx] = 2 if random.random() < 0.9 else 4
        self.new_tile_position = (row_idx, col_idx)
        self.empty_cells.remove((row_idx, col_idx))
        return (row_idx, col_idx)

    def merge_row(self, row):
        row = [value for value in row if value != 0]
        for i in range(len(row) - 1):
            if row[i] == row[i + 1]:
                row[i] *= 2
                self.score += row[i]
                row[i + 1] = 0
        row = [value for value in row if value != 0]
        while len(row) < self.grid_size:
            row.append(0)
        return row

    def move_left(self):
        moved = False
        for row_idx in range(self.grid_size):
            original_row = self.board[row_idx].copy()
            self.board[row_idx] = self.merge_row(self.board[row_idx])
            if original_row != self.board[row_idx]:
                moved = True
        return moved

    def move_right(self):
        moved = False
        for row_idx in range(self.grid_size):
            original_row = self.board[row_idx].copy()
            reversed_row = self.board[row_idx][::-1]
            slid_row = self.merge_row(reversed_row)
            self.board[row_idx] = slid_row[::-1]
            if original_row != self.board[row_idx]:
                moved = True
        return moved

    def move_up(self):
        self.transpose()
        moved = self.move_left()
        self.transpose()
        return moved

    def move_down(self):
        self.transpose()
        moved = self.move_right()
        self.transpose()
        return moved

    def transpose(self):
        self.board = [
            [self.board[col_idx][row_idx] for col_idx in range(self.grid_size)]
            for row_idx in range(self.grid_size)
        ]

    def is_game_over(self):
        for row_idx in range(self.grid_size):
            for col_idx in range(self.grid_size):
                if self.board[row_idx][col_idx] == 0:
                    return False
        for row_idx in range(self.grid_size):
            for col_idx in range(self.grid_size):
                if (
                    col_idx < self.grid_size - 1
                    and self.board[row_idx][col_idx] == self.board[row_idx][col_idx + 1]
                ):
                    return False
                if (
                    row_idx < self.grid_size - 1
                    and self.board[row_idx][col_idx] == self.board[row_idx + 1][col_idx]
                ):
                    return False
        return True

    def handle_input(self, event: pygame.event.Event) -> None:
        """Process a pygame event for moving tiles or restarting the game."""
        if event.type == pygame.KEYDOWN:
            now = pygame.time.get_ticks()
            if now - self.last_move_time < 150:  # Debounce key events
                return
            moves = {
                pygame.K_LEFT: self.move_left,
                pygame.K_RIGHT: self.move_right,
                pygame.K_UP: self.move_up,
                pygame.K_DOWN: self.move_down,
            }
            if event.key in moves:
                moved = moves[event.key]()
            elif event.key == pygame.K_r:
                self.restart()
                return
            else:
                moved = False

            if moved:
                self.update_empty_cells()
                self.add_random_tile()
                self.animation_start_time = pygame.time.get_ticks()
                self.last_move_time = now
                if self.is_game_over():
                    self.game_over = True

    def restart(self) -> None:
        # Reset game state for a new game.
        self.board = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.score = 0
        self.game_over = False
        self.new_tile_position = None
        self.empty_cells = {
            (i, j) for i in range(self.grid_size) for j in range(self.grid_size)
        }
        self.add_random_tile()
        self.add_random_tile()


# --- New Renderer class handling rendering logic ---
class Renderer:
    """Handles rendering logic for 2048."""

    def __init__(
        self,
        game: Game,
        tile_size: int,
        fps: int,
        config: GameConfig,
        font_name: str = "Arial",
    ):
        self.config = config
        self.animation_duration = 200  # milliseconds for new tile animation
        self.title_y = 20  # Y coordinate for the title text
        self.subtitle_y = 85  # Y coordinate for the subtitle text
        self.grid_top_y = 195  # Y coordinate where grid starts
        self.game = game
        self.tile_size = tile_size
        self.fps = fps
        self.font_name = font_name
        self.grid_padding = 15
        self.grid_width = (
            self.grid_padding * (game.grid_size + 1) + tile_size * game.grid_size
        )
        self.grid_height = self.grid_width
        self.width = max(500, self.grid_width + 40)
        self.height = 175 + self.grid_height + 100

        self.screen = None
        self.clock = None
        self.title_font = None
        self.subtitle_font = None
        self.instruction_font = None
        self.score_font = None
        self.score_label_font = None
        self.tile_fonts = {}

    def init_pygame(self) -> None:
        """Initializes pygame, display, and fonts."""
        pygame.init()
        try:
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("2048 Game")
            self.clock = pygame.time.Clock()
            self.title_font = pygame.font.SysFont(self.font_name, 60, bold=True)
            self.subtitle_font = pygame.font.SysFont(self.font_name, 18)
            self.instruction_font = pygame.font.SysFont(self.font_name, 16)
            self.score_font = pygame.font.SysFont(self.font_name, 25, bold=True)
            self.score_label_font = pygame.font.SysFont(self.font_name, 14, bold=True)
            for value in [2, 4, 8, 16, 32, 64]:
                self.tile_fonts[value] = pygame.font.SysFont(
                    self.font_name, 45, bold=True
                )
            for value in [128, 256, 512]:
                self.tile_fonts[value] = pygame.font.SysFont(
                    self.font_name, 40, bold=True
                )
            for value in [1024, 2048]:
                self.tile_fonts[value] = pygame.font.SysFont(
                    self.font_name, 30, bold=True
                )
        except Exception as e:
            print("Error initializing fonts or display:", e)
            sys.exit(1)
        self.game.add_random_tile()
        self.game.add_random_tile()

    def draw_tile(
        self, x: int, y: int, value: int, row_idx: int, col_idx: int, current_time: int
    ) -> None:
        # Update usage to snake_case.
        anim_duration = self.animation_duration
        elapsed = current_time - self.game.animation_start_time
        is_anim_tile = (self.game.new_tile_position == (row_idx, col_idx)) and (
            elapsed < anim_duration
        )
        scale: float = 1.0
        if is_anim_tile:
            progress = elapsed / anim_duration
            scale = 0.1 + 0.9 * progress
        elif self.game.new_tile_position == (row_idx, col_idx):
            self.game.new_tile_position = None
        # Draw tile background.
        color = self.config.tile_colors.get(value, self.config.tile_colors[2048])
        if is_anim_tile and scale < 1.0:
            scaled_size = int(self.tile_size * scale)
            offset = (self.tile_size - scaled_size) // 2
            # Create a transparent surface if alpha is desired.
            tile_surf = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
            tile_surf.fill(color)
            self.screen.blit(tile_surf, (x + offset, y + offset))
        else:
            tile_rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
            pygame.draw.rect(self.screen, color, tile_rect, border_radius=3)
        # Draw tile value text.
        if value != 0:
            font = self.tile_fonts.get(value, self.tile_fonts[2048])
            text_color = self.config.text_colors.get(value, self.config.light_text)
            text = font.render(str(value), True, text_color)
            if is_anim_tile and scale < 1.0:
                text = pygame.transform.scale(
                    text,
                    (int(text.get_width() * scale), int(text.get_height() * scale)),
                )
            text_x = x + (self.tile_size - text.get_width()) // 2
            text_y = y + (self.tile_size - text.get_height()) // 2
            self.screen.blit(text, (text_x, text_y))

    def draw(self):
        self.screen.fill(self.config.background_color)
        title_text = self.title_font.render("2048", True, self.config.text_color)
        self.screen.blit(
            title_text, (self.width // 2 - title_text.get_width() // 2, self.title_y)
        )
        subtitle_text = self.subtitle_font.render(
            "Join the tiles, get to 2048!", True, self.config.text_color
        )
        self.screen.blit(
            subtitle_text,
            (self.width // 2 - subtitle_text.get_width() // 2, self.subtitle_y),
        )
        pygame.draw.rect(
            self.screen,
            self.config.grid_color,
            (self.width // 2 - 70, 115, 140, 60),
            border_radius=5,
        )
        score_label_text = self.score_label_font.render("SCORE", True, (255, 255, 255))
        self.screen.blit(
            score_label_text, (self.width // 2 - score_label_text.get_width() // 2, 123)
        )
        score_text = self.score_font.render(str(self.game.score), True, (255, 255, 255))
        self.screen.blit(
            score_text, (self.width // 2 - score_text.get_width() // 2, 143)
        )
        grid_rect = pygame.Rect(
            (self.width - self.grid_width) // 2,
            self.grid_top_y,
            self.grid_width,
            self.grid_height,
        )
        pygame.draw.rect(
            self.screen, self.config.grid_color, grid_rect, border_radius=6
        )
        current_time = pygame.time.get_ticks()
        grid_bottom = self.grid_top_y + self.grid_height + 20
        for row_idx in range(self.game.grid_size):
            for col_idx in range(self.game.grid_size):
                value = self.game.board[row_idx][col_idx]
                x = (
                    (self.width - self.grid_width) // 2
                    + self.grid_padding * (col_idx + 1)
                    + self.tile_size * col_idx
                )
                y = (
                    self.grid_top_y
                    + self.grid_padding * (row_idx + 1)
                    + self.tile_size * row_idx
                )
                self.draw_tile(x, y, value, row_idx, col_idx, current_time)
        instruction_text1 = self.instruction_font.render(
            "HOW TO PLAY: Use your arrow keys to move the tiles.",
            True,
            self.config.text_color,
        )
        instruction_text2 = self.instruction_font.render(
            "When two tiles with the same number touch, they merge into one!",
            True,
            self.config.text_color,
        )
        self.screen.blit(
            instruction_text1,
            (self.width // 2 - instruction_text1.get_width() // 2, grid_bottom),
        )
        self.screen.blit(
            instruction_text2,
            (self.width // 2 - instruction_text2.get_width() // 2, grid_bottom + 25),
        )
        pygame.draw.line(
            self.screen,
            (200, 200, 200),
            (0, self.height - 10),
            (self.width, self.height - 10),
            1,
        )
        if self.game.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 150))
            self.screen.blit(overlay, (0, 0))
            game_over_text = self.title_font.render(
                "Game Over!", True, self.config.text_color
            )
            final_score_text = self.subtitle_font.render(
                f"Final Score: {self.game.score}", True, self.config.text_color
            )
            self.screen.blit(
                game_over_text,
                (
                    self.width // 2 - game_over_text.get_width() // 2,
                    self.height // 2 - 50,
                ),
            )
            self.screen.blit(
                final_score_text,
                (
                    self.width // 2 - final_score_text.get_width() // 2,
                    self.height // 2 + 10,
                ),
            )

    def run(self) -> None:
        self.init_pygame()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.game.handle_input(event)
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()
        sys.exit()


# --- Update main to use Game and Renderer ---
@click.command()
@click.option(
    "--grid-size",
    "-g",
    default=4,
    help="Size of the game grid (e.g. 4 for 4x4)",
    type=int,
)
@click.option(
    "--tile-size", "-t", default=100, help="Size of each tile in pixels", type=int
)
@click.option("--fps", "-f", default=60, help="Frames per second", type=int)
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True),
    help="Path to config YAML file",
)
def main(grid_size, tile_size, fps, config_path):
    """Entry point for the 2048 game."""
    if config_path:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        cfg = GameConfig(**data)
    else:
        cfg = GameConfig()
    game = Game(grid_size)
    renderer = Renderer(game, tile_size, fps, cfg)
    renderer.run()


if __name__ == "__main__":
    main()
