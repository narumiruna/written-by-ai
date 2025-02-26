# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "pygame",
# ]
# ///
import pygame
import random
import sys
import click

# Colors (similar to web version)
BACKGROUND_COLOR = (250, 248, 239)  # #faf8ef
GRID_COLOR = (187, 173, 160)  # #bbada0
TEXT_COLOR = (119, 110, 101)  # #776e65
LIGHT_TEXT = (249, 246, 242)  # #f9f6f2
EMPTY_TILE = (205, 193, 180, 50)  # rgba(238, 228, 218, 0.35)

# Tile colors based on value
TILE_COLORS = {
    0: EMPTY_TILE,
    2: (238, 228, 218),  # #eee4da
    4: (237, 224, 200),  # #ede0c8
    8: (242, 177, 121),  # #f2b179
    16: (245, 149, 99),  # #f59563
    32: (246, 124, 95),  # #f67c5f
    64: (246, 94, 59),  # #f65e3b
    128: (237, 207, 114),  # #edcf72
    256: (237, 204, 97),  # #edcc61
    512: (237, 200, 80),  # #edc850
    1024: (237, 197, 63),  # #edc53f
    2048: (237, 194, 46)  # #edc22e
}

# Text colors based on tile value
TEXT_COLORS = {
    2: TEXT_COLOR,
    4: TEXT_COLOR
}


class Game2048:
    def __init__(self, grid_size, tile_size, fps):
        self.grid_size = grid_size
        self.tile_size = tile_size
        self.fps = fps
        
        self.grid_padding = 15
        self.grid_width = self.grid_padding * (self.grid_size + 1) + self.tile_size * self.grid_size
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
        
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.score = 0
        self.game_over = False
        
        self.new_tile_pos = None
        self.animation_time = 0

    def init_pygame(self):
        """Initialize Pygame and create resources"""
        pygame.init()
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("2048 Game")
        self.clock = pygame.time.Clock()
        
        self.title_font = pygame.font.SysFont("Arial", 60, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 18)
        self.instruction_font = pygame.font.SysFont("Arial", 16)
        self.score_font = pygame.font.SysFont("Arial", 25, bold=True)
        self.score_label_font = pygame.font.SysFont("Arial", 14, bold=True)
        
        for value in [2, 4, 8, 16, 32, 64]:
            self.tile_fonts[value] = pygame.font.SysFont("Arial", 45, bold=True)
        for value in [128, 256, 512]:
            self.tile_fonts[value] = pygame.font.SysFont("Arial", 40, bold=True)
        for value in [1024, 2048]:
            self.tile_fonts[value] = pygame.font.SysFont("Arial", 30, bold=True)
        
        self.add_random_tile()
        self.add_random_tile()

    def add_random_tile(self):
        """Add a random tile (2 or 4) to an empty cell"""
        empty_cells = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 0:
                    empty_cells.append((r, c))
        
        if not empty_cells:
            return None
            
        r, c = random.choice(empty_cells)
        self.grid[r][c] = 2 if random.random() < 0.9 else 4
        self.new_tile_pos = (r, c)
        return (r, c)
        
    def slide(self, row):
        """Slide a row to the left and combine tiles"""
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
        """Move tiles left"""
        moved = False
        for r in range(self.grid_size):
            original_row = self.grid[r].copy()
            self.grid[r] = self.slide(self.grid[r])
            if original_row != self.grid[r]:
                moved = True
        return moved
        
    def move_right(self):
        """Move tiles right"""
        moved = False
        for r in range(self.grid_size):
            original_row = self.grid[r].copy()
            reversed_row = self.grid[r][::-1]
            slid_row = self.slide(reversed_row)
            self.grid[r] = slid_row[::-1]
            if original_row != self.grid[r]:
                moved = True
        return moved
        
    def move_up(self):
        """Move tiles up"""
        self.transpose()
        moved = self.move_left()
        self.transpose()
        return moved
        
    def move_down(self):
        """Move tiles down"""
        self.transpose()
        moved = self.move_right()
        self.transpose()
        return moved
        
    def transpose(self):
        """Transpose the grid to simplify up/down movements"""
        transposed = [[self.grid[c][r] for c in range(self.grid_size)] for r in range(self.grid_size)]
        self.grid = transposed
        
    def is_game_over(self):
        """Check if the game is over (no valid moves)"""
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 0:
                    return False
                    
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if c < self.grid_size - 1 and self.grid[r][c] == self.grid[r][c + 1]:
                    return False
                if r < self.grid_size - 1 and self.grid[r][c] == self.grid[r + 1][c]:
                    return False
                    
        return True
        
    def handle_input(self, event):
        """Handle keyboard input"""
        if event.type == pygame.KEYDOWN:
            moved = False
            if event.key == pygame.K_LEFT:
                moved = self.move_left()
            elif event.key == pygame.K_RIGHT:
                moved = self.move_right()
            elif event.key == pygame.K_UP:
                moved = self.move_up()
            elif event.key == pygame.K_DOWN:
                moved = self.move_down()
                
            if moved:
                self.add_random_tile()
                self.animation_time = pygame.time.get_ticks()
                if self.is_game_over():
                    self.game_over = True
    
    def draw(self):
        """Draw the game board and UI"""
        self.screen.fill(BACKGROUND_COLOR)
        
        title_text = self.title_font.render("2048", True, TEXT_COLOR)
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 20))
        
        subtitle_text = self.subtitle_font.render("Join the tiles, get to 2048!", True, TEXT_COLOR)
        self.screen.blit(subtitle_text, (self.width // 2 - subtitle_text.get_width() // 2, 85))
        
        pygame.draw.rect(self.screen, GRID_COLOR, (self.width // 2 - 70, 115, 140, 60), border_radius=5)
        score_label_text = self.score_label_font.render("SCORE", True, (255, 255, 255))
        self.screen.blit(score_label_text, (self.width // 2 - score_label_text.get_width() // 2, 123))
        score_text = self.score_font.render(str(self.score), True, (255, 255, 255))
        self.screen.blit(score_text, (self.width // 2 - score_text.get_width() // 2, 143))
        
        grid_rect = pygame.Rect(
            (self.width - self.grid_width) // 2,
            195,
            self.grid_width,
            self.grid_height
        )
        pygame.draw.rect(self.screen, GRID_COLOR, grid_rect, border_radius=6)
        
        current_time = pygame.time.get_ticks()
        animation_active = current_time - self.animation_time < 200
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                value = self.grid[r][c]
                
                x = (self.width - self.grid_width) // 2 + self.grid_padding * (c + 1) + self.tile_size * c
                y = 195 + self.grid_padding * (r + 1) + self.tile_size * r
                
                tile_rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                
                color = TILE_COLORS.get(value, TILE_COLORS[2048])
                pygame.draw.rect(self.screen, color, tile_rect, border_radius=3)
                
                scale = 1.0
                if animation_active and self.new_tile_pos == (r, c):
                    progress = (current_time - self.animation_time) / 200.0
                    scale = 0.1 + 0.9 * progress
                    
                    if scale < 1.0:
                        scaled_size = int(self.tile_size * scale)
                        offset = (self.tile_size - scaled_size) // 2
                        scaled_rect = pygame.Rect(
                            x + offset, 
                            y + offset, 
                            scaled_size, 
                            scaled_size
                        )
                        pygame.draw.rect(self.screen, color, scaled_rect, border_radius=3)
                
                if value != 0:
                    font = self.tile_fonts.get(value, self.tile_fonts[2048])
                    text_color = TEXT_COLORS.get(value, LIGHT_TEXT)
                    text = font.render(str(value), True, text_color)
                    
                    text_x = x + (self.tile_size - text.get_width()) // 2
                    text_y = y + (self.tile_size - text.get_height()) // 2
                    
                    if animation_active and self.new_tile_pos == (r, c) and scale < 1.0:
                        text = pygame.transform.scale(
                            text, 
                            (int(text.get_width() * scale), int(text.get_height() * scale))
                        )
                        text_x = x + (self.tile_size - text.get_width()) // 2
                        text_y = y + (self.tile_size - text.get_height()) // 2
                        
                    self.screen.blit(text, (text_x, text_y))
        
        grid_bottom = 195 + self.grid_height + 20
        
        instruction_text1 = self.instruction_font.render(
            "HOW TO PLAY: Use your arrow keys to move the tiles.", 
            True, TEXT_COLOR
        )
        instruction_text2 = self.instruction_font.render(
            "When two tiles with the same number touch, they merge into one!", 
            True, TEXT_COLOR
        )
        
        self.screen.blit(instruction_text1, (self.width // 2 - instruction_text1.get_width() // 2, grid_bottom))
        self.screen.blit(instruction_text2, (self.width // 2 - instruction_text2.get_width() // 2, grid_bottom + 25))
        
        pygame.draw.line(self.screen, 
                         (200, 200, 200), 
                         (0, self.height - 10), 
                         (self.width, self.height - 10), 
                         1)
        
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 150))
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.title_font.render("Game Over!", True, TEXT_COLOR)
            final_score_text = self.subtitle_font.render(f"Final Score: {self.score}", True, TEXT_COLOR)
            
            self.screen.blit(game_over_text, 
                           (self.width // 2 - game_over_text.get_width() // 2, self.height // 2 - 50))
            self.screen.blit(final_score_text, 
                           (self.width // 2 - final_score_text.get_width() // 2, self.height // 2 + 10))

    def run(self):
        """Run the game loop with proper initialization and cleanup"""
        self.init_pygame()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif not self.game_over:
                    self.handle_input(event)
            
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        pygame.quit()
        sys.exit()


@click.command()
@click.option('--grid-size', '-g', default=4, help='Size of the game grid (e.g. 4 for 4x4)', type=int)
@click.option('--tile-size', '-t', default=100, help='Size of each tile in pixels', type=int)
@click.option('--fps', '-f', default=60, help='Frames per second', type=int)
def main(grid_size, tile_size, fps):
    """2048 Game - Join the tiles, get to 2048!"""
    game = Game2048(grid_size=grid_size, tile_size=tile_size, fps=fps)
    game.run()


if __name__ == "__main__":
    main()
