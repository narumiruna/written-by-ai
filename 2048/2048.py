# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pygame",
# ]
# ///
import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 500
# Calculate required height based on all UI elements:
# - Title/header area: ~175px
# - Grid area: GRID_HEIGHT + padding (~500px)
# - Instructions area: ~80px
# - Bottom padding: 20px
GRID_SIZE = 4
GRID_PADDING = 15
TILE_SIZE = 100
GRID_WIDTH = GRID_PADDING * (GRID_SIZE + 1) + TILE_SIZE * GRID_SIZE
GRID_HEIGHT = GRID_WIDTH
HEIGHT = 175 + GRID_HEIGHT + 100  # Dynamically calculate required height (~775px)
FPS = 60

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

# Setup the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048 Game")
clock = pygame.time.Clock()

# Fonts
title_font = pygame.font.SysFont("Arial", 60, bold=True)
subtitle_font = pygame.font.SysFont("Arial", 18)
instruction_font = pygame.font.SysFont("Arial", 16)
score_font = pygame.font.SysFont("Arial", 25, bold=True)
score_label_font = pygame.font.SysFont("Arial", 14, bold=True)
tile_fonts = {
    2: pygame.font.SysFont("Arial", 45, bold=True),
    4: pygame.font.SysFont("Arial", 45, bold=True),
    8: pygame.font.SysFont("Arial", 45, bold=True),
    16: pygame.font.SysFont("Arial", 45, bold=True),
    32: pygame.font.SysFont("Arial", 45, bold=True),
    64: pygame.font.SysFont("Arial", 45, bold=True),
    128: pygame.font.SysFont("Arial", 40, bold=True),
    256: pygame.font.SysFont("Arial", 40, bold=True),
    512: pygame.font.SysFont("Arial", 40, bold=True),
    1024: pygame.font.SysFont("Arial", 30, bold=True),
    2048: pygame.font.SysFont("Arial", 30, bold=True)
}


class Game2048:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.add_random_tile()
        self.add_random_tile()
        
        # For animations
        self.new_tile_pos = None
        self.animation_time = 0
        
    def add_random_tile(self):
        """Add a random tile (2 or 4) to an empty cell"""
        empty_cells = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
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
        # Remove zeros
        row = [value for value in row if value != 0]
        
        # Combine tiles
        for i in range(len(row) - 1):
            if row[i] == row[i + 1]:
                row[i] *= 2
                self.score += row[i]
                row[i + 1] = 0
                
        # Remove zeros again after combining
        row = [value for value in row if value != 0]
        
        # Add zeros to the end
        while len(row) < GRID_SIZE:
            row.append(0)
            
        return row
    
    def move_left(self):
        """Move tiles left"""
        moved = False
        for r in range(GRID_SIZE):
            original_row = self.grid[r].copy()
            self.grid[r] = self.slide(self.grid[r])
            if original_row != self.grid[r]:
                moved = True
        return moved
        
    def move_right(self):
        """Move tiles right"""
        moved = False
        for r in range(GRID_SIZE):
            original_row = self.grid[r].copy()
            # Reverse, slide, then reverse back
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
        transposed = [[self.grid[c][r] for c in range(GRID_SIZE)] for r in range(GRID_SIZE)]
        self.grid = transposed
        
    def is_game_over(self):
        """Check if the game is over (no valid moves)"""
        # Check for empty cells
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == 0:
                    return False
                    
        # Check for adjacent matching tiles
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                # Check right neighbor
                if c < GRID_SIZE - 1 and self.grid[r][c] == self.grid[r][c + 1]:
                    return False
                # Check bottom neighbor
                if r < GRID_SIZE - 1 and self.grid[r][c] == self.grid[r + 1][c]:
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
        screen.fill(BACKGROUND_COLOR)
        
        # Draw title
        title_text = title_font.render("2048", True, TEXT_COLOR)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 20))
        
        # Draw subtitle
        subtitle_text = subtitle_font.render("Join the tiles, get to 2048!", True, TEXT_COLOR)
        screen.blit(subtitle_text, (WIDTH // 2 - subtitle_text.get_width() // 2, 85))
        
        # Draw score
        pygame.draw.rect(screen, GRID_COLOR, (WIDTH // 2 - 70, 115, 140, 60), border_radius=5)
        score_label_text = score_label_font.render("SCORE", True, (255, 255, 255))
        screen.blit(score_label_text, (WIDTH // 2 - score_label_text.get_width() // 2, 123))
        score_text = score_font.render(str(self.score), True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 143))
        
        # Draw grid background
        grid_rect = pygame.Rect(
            (WIDTH - GRID_WIDTH) // 2,
            195,  # Moved up slightly
            GRID_WIDTH,
            GRID_HEIGHT
        )
        pygame.draw.rect(screen, GRID_COLOR, grid_rect, border_radius=6)
        
        # Draw tiles
        current_time = pygame.time.get_ticks()
        animation_active = current_time - self.animation_time < 200  # 200ms animation
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                value = self.grid[r][c]
                
                # Calculate tile position
                x = (WIDTH - GRID_WIDTH) // 2 + GRID_PADDING * (c + 1) + TILE_SIZE * c
                y = 195 + GRID_PADDING * (r + 1) + TILE_SIZE * r  # Adjusted for new grid position
                
                # Create tile rect
                tile_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                
                # Draw tile
                color = TILE_COLORS.get(value, TILE_COLORS[2048])  # Default to 2048 color if value > 2048
                pygame.draw.rect(screen, color, tile_rect, border_radius=3)
                
                # Animate new tile
                scale = 1.0
                if animation_active and self.new_tile_pos == (r, c):
                    progress = (current_time - self.animation_time) / 200.0  # 0.0 to 1.0
                    scale = 0.1 + 0.9 * progress
                    
                    # Redraw with scale if animating
                    if scale < 1.0:
                        scaled_size = int(TILE_SIZE * scale)
                        offset = (TILE_SIZE - scaled_size) // 2
                        scaled_rect = pygame.Rect(
                            x + offset, 
                            y + offset, 
                            scaled_size, 
                            scaled_size
                        )
                        pygame.draw.rect(screen, color, scaled_rect, border_radius=3)
                
                # Draw tile text for non-zero tiles
                if value != 0:
                    font = tile_fonts.get(value, tile_fonts[2048])  # Default to 2048 font
                    text_color = TEXT_COLORS.get(value, LIGHT_TEXT)  # Default to light text
                    text = font.render(str(value), True, text_color)
                    
                    # Center the text on the tile
                    text_x = x + (TILE_SIZE - text.get_width()) // 2
                    text_y = y + (TILE_SIZE - text.get_height()) // 2
                    
                    # Apply scale for animation if needed
                    if animation_active and self.new_tile_pos == (r, c) and scale < 1.0:
                        text = pygame.transform.scale(
                            text, 
                            (int(text.get_width() * scale), int(text.get_height() * scale))
                        )
                        text_x = x + (TILE_SIZE - text.get_width()) // 2
                        text_y = y + (TILE_SIZE - text.get_height()) // 2
                        
                    screen.blit(text, (text_x, text_y))
        
        # Calculate the bottom position of the grid
        grid_bottom = 195 + GRID_HEIGHT + 20  # 20px padding
        
        # Draw instructions - moved to below the grid
        instruction_text1 = instruction_font.render(
            "HOW TO PLAY: Use your arrow keys to move the tiles.", 
            True, TEXT_COLOR
        )
        instruction_text2 = instruction_font.render(
            "When two tiles with the same number touch, they merge into one!", 
            True, TEXT_COLOR
        )
        
        # Position instructions below the grid with proper spacing
        screen.blit(instruction_text1, (WIDTH // 2 - instruction_text1.get_width() // 2, grid_bottom))
        screen.blit(instruction_text2, (WIDTH // 2 - instruction_text2.get_width() // 2, grid_bottom + 25))
        
        # Add a padding indicator line at the bottom to verify visibility
        pygame.draw.line(screen, 
                         (200, 200, 200), 
                         (0, HEIGHT - 10), 
                         (WIDTH, HEIGHT - 10), 
                         1)
        
        # Draw game over message
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 150))
            screen.blit(overlay, (0, 0))
            
            game_over_text = title_font.render("Game Over!", True, TEXT_COLOR)
            final_score_text = subtitle_font.render(f"Final Score: {self.score}", True, TEXT_COLOR)
            
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 + 10))


def main():
    game = Game2048()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif not game.game_over:
                game.handle_input(event)
        
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
