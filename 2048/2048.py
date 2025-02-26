#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "pydantic",
#     "pygame",
#     "pyyaml",
# ]
# ///
"""
2048 Game Implementation
A simple and clean implementation of the popular 2048 puzzle game
using Python and Pygame.
"""

import random
import sys
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple

import click
import pygame
import yaml
from pydantic import BaseModel, Field


class Action(Enum):
    """Game actions that can be performed."""

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    RESTART = auto()
    NONE = auto()


class GameConfig(BaseModel):
    """Configuration for the 2048 game."""

    # Grid and display settings
    grid_size: int = Field(default=4, ge=2, le=8, description="Size of the game grid")
    tile_size: int = Field(
        default=100, ge=40, le=200, description="Size of each tile in pixels"
    )
    fps: int = Field(default=60, ge=30, le=120, description="Frames per second")

    # Font settings
    font_name: str = "Arial"

    # Color settings
    background_color: Tuple[int, int, int] = (250, 248, 239)
    grid_color: Tuple[int, int, int] = (187, 173, 160)
    text_color: Tuple[int, int, int] = (119, 110, 101)
    light_text: Tuple[int, int, int] = (249, 246, 242)

    # Tile settings
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

    # Layout settings
    animation_duration: int = 200  # milliseconds for new tile animation
    title_y: int = 20  # Y coordinate for title text
    subtitle_y: int = 85  # Y coordinate for subtitle text
    grid_top_y: int = 195  # Y coordinate where the grid starts
    grid_padding: int = 15  # Padding around the grid
    debounce_time: int = 150  # milliseconds to prevent too rapid moves


class Game:
    """Handles game state and logic for 2048."""

    def __init__(self, config: GameConfig) -> None:
        """Initialize a new game with the specified configuration.

        Args:
            config: Game configuration parameters
        """
        self.grid_size = config.grid_size
        self.board: List[List[int]] = [
            [0 for _ in range(self.grid_size)] for _ in range(self.grid_size)
        ]
        self.score: int = 0
        self.game_over: bool = False
        self.new_tile_position: Optional[Tuple[int, int]] = None
        self.animation_start_time: int = 0
        self.empty_cells: Set[Tuple[int, int]] = {
            (i, j) for i in range(self.grid_size) for j in range(self.grid_size)
        }

    def update_empty_cells(self) -> None:
        """Update the set of empty cells based on current board state."""
        self.empty_cells = {
            (i, j)
            for i in range(self.grid_size)
            for j in range(self.grid_size)
            if self.board[i][j] == 0
        }

    def add_random_tile(self) -> Optional[Tuple[int, int]]:
        """Add a random tile (2 or 4) to an empty cell.

        Returns:
            The position of the new tile, or None if no empty cells
        """
        self.update_empty_cells()  # ensure board and list are in sync
        if not self.empty_cells:
            return None
        row_idx, col_idx = random.choice(list(self.empty_cells))
        self.board[row_idx][col_idx] = 2 if random.random() < 0.9 else 4
        self.new_tile_position = (row_idx, col_idx)
        self.empty_cells.remove((row_idx, col_idx))
        return (row_idx, col_idx)

    def merge_row(self, row: List[int]) -> List[int]:
        """Merge a single row by combining identical adjacent values.

        Args:
            row: The row to merge

        Returns:
            The merged row
        """
        # Remove zeros
        row = [value for value in row if value != 0]

        # Merge adjacent identical values
        for i in range(len(row) - 1):
            if row[i] == row[i + 1]:
                row[i] *= 2
                self.score += row[i]
                row[i + 1] = 0

        # Remove zeros again and pad with zeros
        row = [value for value in row if value != 0]
        while len(row) < self.grid_size:
            row.append(0)

        return row

    def move_left(self) -> bool:
        """Move tiles to the left and merge them.

        Returns:
            True if the board changed, False otherwise
        """
        moved = False
        for row_idx in range(self.grid_size):
            original_row = self.board[row_idx].copy()
            self.board[row_idx] = self.merge_row(self.board[row_idx])
            if original_row != self.board[row_idx]:
                moved = True
        return moved

    def move_right(self) -> bool:
        """Move tiles to the right and merge them.

        Returns:
            True if the board changed, False otherwise
        """
        moved = False
        for row_idx in range(self.grid_size):
            original_row = self.board[row_idx].copy()
            reversed_row = self.board[row_idx][::-1]
            slid_row = self.merge_row(reversed_row)
            self.board[row_idx] = slid_row[::-1]
            if original_row != self.board[row_idx]:
                moved = True
        return moved

    def move_up(self) -> bool:
        """Move tiles up and merge them.

        Returns:
            True if the board changed, False otherwise
        """
        self.transpose()
        moved = self.move_left()
        self.transpose()
        return moved

    def move_down(self) -> bool:
        """Move tiles down and merge them.

        Returns:
            True if the board changed, False otherwise
        """
        self.transpose()
        moved = self.move_right()
        self.transpose()
        return moved

    def transpose(self) -> None:
        """Transpose the board matrix."""
        self.board = [
            [self.board[col_idx][row_idx] for col_idx in range(self.grid_size)]
            for row_idx in range(self.grid_size)
        ]

    def is_game_over(self) -> bool:
        """Check if the game is over (no more valid moves).

        Returns:
            True if game is over, False if moves are still possible
        """
        # Check for empty cells
        for row_idx in range(self.grid_size):
            for col_idx in range(self.grid_size):
                if self.board[row_idx][col_idx] == 0:
                    return False

        # Check for possible merges horizontally
        for row_idx in range(self.grid_size):
            for col_idx in range(self.grid_size - 1):
                if self.board[row_idx][col_idx] == self.board[row_idx][col_idx + 1]:
                    return False

        # Check for possible merges vertically
        for row_idx in range(self.grid_size - 1):
            for col_idx in range(self.grid_size):
                if self.board[row_idx][col_idx] == self.board[row_idx + 1][col_idx]:
                    return False

        return True

    def handle_action(self, action: Action) -> bool:
        """Process a game action and return whether the board changed.

        Args:
            action: The action to perform

        Returns:
            True if the board changed, False otherwise
        """
        if action == Action.RESTART:
            self.restart()
            return True

        if action == Action.NONE:
            return False

        action_handlers = {
            Action.LEFT: self.move_left,
            Action.RIGHT: self.move_right,
            Action.UP: self.move_up,
            Action.DOWN: self.move_down,
        }

        if action in action_handlers:
            moved = action_handlers[action]()
            if moved:
                self.update_empty_cells()
                self.add_random_tile()
                if self.is_game_over():
                    self.game_over = True
            return moved

        return False

    def restart(self) -> None:
        """Reset the game to its initial state."""
        self.board = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.score = 0
        self.game_over = False
        self.new_tile_position = None
        self.empty_cells = {
            (i, j) for i in range(self.grid_size) for j in range(self.grid_size)
        }
        self.add_random_tile()
        self.add_random_tile()


class Renderer:
    """Handles rendering logic for 2048."""

    def __init__(self, game: Game, config: GameConfig) -> None:
        """Initialize the renderer.

        Args:
            game: Game instance to render
            config: Configuration parameters
        """
        self.game = game
        self.config = config

        # Layout parameters
        self.animation_duration = config.animation_duration
        self.title_y = config.title_y
        self.subtitle_y = config.subtitle_y
        self.grid_top_y = config.grid_top_y
        self.tile_size = config.tile_size
        self.fps = config.fps
        self.font_name = config.font_name
        self.grid_padding = config.grid_padding
        self.debounce_time = config.debounce_time

        # Calculate dimensions
        self.grid_width = (
            self.grid_padding * (game.grid_size + 1) + self.tile_size * game.grid_size
        )
        self.grid_height = self.grid_width
        self.width = max(500, self.grid_width + 40)
        self.height = 175 + self.grid_height + 100

        # Initialize pygame resources
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.title_font: Optional[pygame.font.Font] = None
        self.subtitle_font: Optional[pygame.font.Font] = None
        self.instruction_font: Optional[pygame.font.Font] = None
        self.score_font: Optional[pygame.font.Font] = None
        self.score_label_font: Optional[pygame.font.Font] = None
        self.tile_fonts: Dict[int, pygame.font.Font] = {}

        # Tracking the last action time for debouncing
        self.last_action_time: int = 0

    def init_pygame(self) -> None:
        """Initialize pygame, display, and fonts."""
        pygame.init()
        try:
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("2048 Game")
            self.clock = pygame.time.Clock()

            # Initialize fonts
            self.title_font = pygame.font.SysFont(self.font_name, 60, bold=True)
            self.subtitle_font = pygame.font.SysFont(self.font_name, 18)
            self.instruction_font = pygame.font.SysFont(self.font_name, 16)
            self.score_font = pygame.font.SysFont(self.font_name, 25, bold=True)
            self.score_label_font = pygame.font.SysFont(self.font_name, 14, bold=True)

            # Initialize tile fonts with different sizes based on number of digits
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

            # Initialize game with two starting tiles
            self.game.add_random_tile()
            self.game.add_random_tile()

        except Exception as e:
            print(f"Error initializing pygame: {e}")
            sys.exit(1)

    def draw_tile(
        self, x: int, y: int, value: int, row_idx: int, col_idx: int, current_time: int
    ) -> None:
        """Draw a single tile on the screen.

        Args:
            x: X coordinate
            y: Y coordinate
            value: Tile value
            row_idx: Grid row index
            col_idx: Grid column index
            current_time: Current game time in milliseconds
        """
        # Calculate animation parameters
        anim_duration = self.animation_duration
        elapsed = current_time - self.game.animation_start_time
        is_anim_tile = (self.game.new_tile_position == (row_idx, col_idx)) and (
            elapsed < anim_duration
        )
        scale: float = 1.0

        # Apply animation scaling if this is a new tile
        if is_anim_tile:
            progress = elapsed / anim_duration
            scale = 0.1 + 0.9 * progress
        elif self.game.new_tile_position == (row_idx, col_idx):
            self.game.new_tile_position = None

        # Draw tile background
        color = self.config.tile_colors.get(value, self.config.tile_colors[2048])

        if is_anim_tile and scale < 1.0:
            # For animated tiles, draw them smaller with a growing animation
            scaled_size = int(self.tile_size * scale)
            offset = (self.tile_size - scaled_size) // 2
            tile_surf = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
            tile_surf.fill(color)
            self.screen.blit(tile_surf, (x + offset, y + offset))
        else:
            # Draw normal tile
            tile_rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
            pygame.draw.rect(self.screen, color, tile_rect, border_radius=3)

        # Draw tile value text if not empty
        if value != 0:
            font = self.tile_fonts.get(value, self.tile_fonts[2048])
            text_color = self.config.text_colors.get(value, self.config.light_text)
            text = font.render(str(value), True, text_color)

            # Scale text if this is an animated tile
            if is_anim_tile and scale < 1.0:
                text = pygame.transform.scale(
                    text,
                    (int(text.get_width() * scale), int(text.get_height() * scale)),
                )

            # Position text in the center of the tile
            text_x = x + (self.tile_size - text.get_width()) // 2
            text_y = y + (self.tile_size - text.get_height()) // 2
            self.screen.blit(text, (text_x, text_y))

    def draw(self) -> None:
        """Draw the complete game screen."""
        # Fill background
        self.screen.fill(self.config.background_color)

        # Draw title
        title_text = self.title_font.render("2048", True, self.config.text_color)
        self.screen.blit(
            title_text, (self.width // 2 - title_text.get_width() // 2, self.title_y)
        )

        # Draw subtitle
        subtitle_text = self.subtitle_font.render(
            "Join the tiles, get to 2048!", True, self.config.text_color
        )
        self.screen.blit(
            subtitle_text,
            (self.width // 2 - subtitle_text.get_width() // 2, self.subtitle_y),
        )

        # Draw score box
        pygame.draw.rect(
            self.screen,
            self.config.grid_color,
            (self.width // 2 - 70, 115, 140, 60),
            border_radius=5,
        )

        # Draw score label
        score_label_text = self.score_label_font.render("SCORE", True, (255, 255, 255))
        self.screen.blit(
            score_label_text, (self.width // 2 - score_label_text.get_width() // 2, 123)
        )

        # Draw score
        score_text = self.score_font.render(str(self.game.score), True, (255, 255, 255))
        self.screen.blit(
            score_text, (self.width // 2 - score_text.get_width() // 2, 143)
        )

        # Draw main grid background
        grid_rect = pygame.Rect(
            (self.width - self.grid_width) // 2,
            self.grid_top_y,
            self.grid_width,
            self.grid_height,
        )
        pygame.draw.rect(
            self.screen, self.config.grid_color, grid_rect, border_radius=6
        )

        # Get current time for animations
        current_time = pygame.time.get_ticks()

        # Calculate bottom position for instructions
        grid_bottom = self.grid_top_y + self.grid_height + 20

        # Draw each tile
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

        # Draw instructions
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

        # Draw footer line
        pygame.draw.line(
            self.screen,
            (200, 200, 200),
            (0, self.height - 10),
            (self.width, self.height - 10),
            1,
        )

        # Draw game over overlay if needed
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
            restart_text = self.subtitle_font.render(
                "Press 'R' to restart", True, self.config.text_color
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
            self.screen.blit(
                restart_text,
                (
                    self.width // 2 - restart_text.get_width() // 2,
                    self.height // 2 + 40,
                ),
            )

    def handle_pygame_event(self, event: pygame.event.Event) -> Action:
        """Convert a pygame event to a game action.

        Args:
            event: Pygame event to process

        Returns:
            Corresponding game action
        """
        if event.type == pygame.KEYDOWN:
            key_to_action = {
                pygame.K_LEFT: Action.LEFT,
                pygame.K_RIGHT: Action.RIGHT,
                pygame.K_UP: Action.UP,
                pygame.K_DOWN: Action.DOWN,
                pygame.K_r: Action.RESTART,
            }
            return key_to_action.get(event.key, Action.NONE)
        return Action.NONE

    def run(self) -> None:
        """Run the main game loop."""
        self.init_pygame()
        running = True

        while running:
            current_time = pygame.time.get_ticks()

            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Handle input with debouncing
                if event.type == pygame.KEYDOWN:
                    if current_time - self.last_action_time < self.debounce_time:
                        continue

                    action = self.handle_pygame_event(event)
                    moved = self.game.handle_action(action)

                    if moved:
                        self.game.animation_start_time = current_time
                        self.last_action_time = current_time

            # Update display
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.fps)

        # Clean up
        pygame.quit()
        sys.exit()


def load_config(config_path: Optional[str] = None) -> GameConfig:
    """Load game configuration from a file or use defaults.

    Args:
        config_path: Path to YAML config file, or None to use defaults

    Returns:
        Game configuration object
    """
    if config_path:
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
            return GameConfig(**data)
        except Exception as e:
            print(f"Error loading config file {config_path}: {e}")
            print("Using default configuration instead.")

    return GameConfig()


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
def main(grid_size: int, tile_size: int, fps: int, config_path: Optional[str]) -> None:
    """2048 Game - Join the tiles, get to 2048!

    Use arrow keys to move tiles, 'R' to restart.
    """
    # Load configuration
    cfg = load_config(config_path)

    # Override config fields with command-line options
    cfg = cfg.model_copy(
        update={"grid_size": grid_size, "tile_size": tile_size, "fps": fps}
    )

    # Start the game
    game = Game(cfg)
    renderer = Renderer(game, cfg)
    renderer.run()


if __name__ == "__main__":
    main()
