import sys
import pygame
from time import sleep
from pygame.sprite import Group

from settings import Settings
from gameStart import GameStats  # Changed from gameStart to game_stats for consistency
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
    def __init__(self):
        """Initialize the game and create game resources."""
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Alien Invasion")

        # Create instances to store game statistics and create a scoreboard.
        self.stats = GameStats(self.settings)
        self.sb = Scoreboard(self.settings, self.screen, self.stats)

        # Create game objects
        self.ship = Ship(self.settings, self.screen)
        self.bullets = Group()
        self.aliens = Group()

        # Make the Play button.
        self.play_button = Button(self.settings, self.screen, "Play")

        # Create the fleet of aliens.
        self.create_fleet()

    def run_game(self):
        """Start the main loop for the game."""
        while True:
            self.check_events()

            if self.stats.game_active:
                self.ship.update()
                self.update_bullets()
                self.update_aliens()

            self.update_screen()

    def show_instructions(self):
        font = pygame.font.SysFont(None, 28)
        instructions = [
            "Intructions:",
            "- Use <- or -> to move the ship",
            "- Use SPACE to fire bullets",
            "- Use Q to quit the game",
        ]

        for i, line in enumerate(instructions):
            text_image = font.render(line, True, (0, 0, 0), self.settings.bg_color)
            text_rect = text_image.get_rect()
            text_rect.centerx = self.screen.get_rect().centerx
            text_rect.top = 400 + i * 30
            self.screen.blit(text_image, text_rect)

    def check_events(self):
        """Respond to keypresses and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self.check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self.check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.check_play_button(mouse_x, mouse_y)

    def check_keydown_events(self, event):
        """Respond to keypresses."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_SPACE:
            self.fire_bullet()
        elif event.key == pygame.K_q:
            sys.exit()

    def check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def check_play_button(self, mouse_x, mouse_y):
        """Start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_x, mouse_y)
        if button_clicked and not self.stats.game_active:
            # Reset the game settings.
            self.settings.initialize_dynamic_settings()

            # Hide the mouse cursor.
            pygame.mouse.set_visible(False)

            # Reset the game statistics.
            self.stats.reset_stats()
            self.stats.game_active = True

            # Reset the scoreboard images.
            self.sb.prep_score()
            self.sb.prep_high_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            # Empty the list of aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship.
            self.create_fleet()
            self.ship.center_ship()

    def fire_bullet(self):
        """Fire a bullet if limit not reached yet."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self.settings, self.screen, self.ship)
            self.bullets.add(new_bullet)

    def update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        # Update bullet positions.
        self.bullets.update()

        # Get rid of bullets that have disappeared.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self.check_bullet_alien_collisions()

    def check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # Remove any bullets and aliens that have collided.
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.check_high_score()

        if not self.aliens:
            # If the entire fleet is destroyed, start a new level.
            self.bullets.empty()
            self.settings.increase_speed()

            # Increase level.
            self.stats.level += 1
            self.sb.prep_level()

            self.create_fleet()

    def check_high_score(self):
        """Check to see if there's a new high score."""
        if self.stats.score > self.stats.high_score:
            self.stats.high_score = self.stats.score
            self.sb.prep_high_score()

    def update_aliens(self):
        """
        Check if the fleet is at an edge,
        then update the positions of all aliens in the fleet.
        """
        self.check_fleet_edges()
        self.aliens.update()

        # Look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self.ship_hit()

        # Look for aliens hitting the bottom of the screen.
        self.check_aliens_bottom()

    def check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self.change_fleet_direction()
                break

    def change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def ship_hit(self):
        """Respond to ship being hit by alien."""
        if self.stats.ships_left > 0:
            # Decrement ships_left.
            self.stats.ships_left -= 1

            # Update scoreboard.
            self.sb.prep_ships()

            # Empty the list of aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship.
            self.create_fleet()
            self.ship.center_ship()

            # Pause.
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # Treat this the same as if the ship got hit.
                self.ship_hit()
                break

    def create_fleet(self):
        """Create a full fleet of aliens."""
        # Create an alien and find the number of aliens in a row.
        alien = Alien(self.settings, self.screen)
        number_aliens_x = min(self.get_number_aliens_x(alien.rect.width), 10)
        number_rows = min(self.get_number_rows(self.ship.rect.height, alien.rect.height), 5)

        # Create the fleet of aliens.
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self.create_alien(alien_number, row_number)

    def get_number_aliens_x(self, alien_width):
        """Determine the number of aliens that fit in a row."""
        available_space_x = self.settings.screen_width - 2 * alien_width
        number_aliens_x = int(available_space_x / (2 * alien_width))
        return number_aliens_x

    def get_number_rows(self, ship_height, alien_height):
        """Determine the number of rows of aliens that fit on the screen."""
        available_space_y = (self.settings.screen_height -
                             (3 * alien_height) - ship_height)
        number_rows = int(available_space_y / (2 * alien_height))
        return number_rows

    def create_alien(self, alien_number, row_number):
        """Create an alien and place it in the row."""
        alien = Alien(self.settings, self.screen)
        alien_width = alien.rect.width
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        # Redraw the screen during each pass through the loop.
        self.screen.fill(self.settings.bg_color)

        # Draw bullets, ship, and aliens
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(self.screen)

        # Draw the score information.
        self.sb.show_score()

        # Draw the play button if the game is inactive.
        if not self.stats.game_active:
            self.play_button.draw_button()
            self.show_instructions()

        # Make the most recently drawn screen visible.
        pygame.display.flip()


if __name__ == '__main__':
    # Create game instance and run the game.
    ai = AlienInvasion()
    ai.run_game()