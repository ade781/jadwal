import pygame
import random
import math
from pygame.math import Vector2

pygame.init()
pygame.font.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GOLD = (255, 215, 0)

GRAVITY = 0.08
ROCKET_LIFESPAN = 255

# Peluang kembang api baru diluncurkan otomatis setiap frame (misal: 0.02 berarti 2% peluang)
AUTO_FIREWORK_CHANCE = 0.02
CRACKLE_CHANCE = 0.08
NUM_CRACKLE_PARTICLES = 15

TEXT_MESSAGE = "semangat belajar FIka"
TEXT_ANIMATION_INTERVAL = 5000
TEXT_PARTICLE_SPEED = 5
TEXT_PARTICLE_HOLD_TIME = 240

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Animasi Kembang Api v3.6 - 30 Palet Warna")
clock = pygame.time.Clock()
try:
    MESSAGE_FONT = pygame.font.SysFont("segoeuisemibold", 72)
except:
    MESSAGE_FONT = pygame.font.SysFont("arial", 72)


class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifespan, has_gravity=True, can_crackle=False):
        self.pos = Vector2(x, y)
        self.vel = Vector2(vx, vy)
        self.color = color
        self.size = size
        self.lifespan = lifespan
        self.initial_lifespan = lifespan
        self.has_gravity = has_gravity
        self.can_crackle = can_crackle
        self.crackled = False

    def update(self):
        if self.is_alive():
            self.pos += self.vel
            if self.has_gravity:
                self.vel.y += GRAVITY
            self.lifespan -= 1

    def draw(self, surface):
        if self.is_alive():
            alpha = max(
                0, int(255 * (self.lifespan / self.initial_lifespan)**2))
            particle_surf = pygame.Surface(
                (self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (*self.color, alpha),
                               (self.size, self.size), self.size)
            surface.blit(
                particle_surf, (int(self.pos.x - self.size), int(self.pos.y - self.size)))

    def is_alive(self):
        return self.lifespan > 0


class TextParticle:
    def __init__(self, target_pos):
        self.target_pos = Vector2(target_pos)
        self.pos = Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.vel = Vector2(
            random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * TEXT_PARTICLE_SPEED
        self.state = 'moving_to_target'
        self.hold_timer = TEXT_PARTICLE_HOLD_TIME
        self.lifespan = 500

    def update(self):
        if self.state == 'moving_to_target':
            direction = (self.target_pos - self.pos)
            if direction.length() < 5:
                self.pos = self.target_pos
                self.vel = Vector2(0, 0)
                self.state = 'holding'
            else:
                self.vel = direction.normalize() * TEXT_PARTICLE_SPEED
                self.pos += self.vel

        elif self.state == 'holding':
            self.hold_timer -= 1
            if self.hold_timer <= 0:
                self.state = 'falling'

        elif self.state == 'falling':
            self.vel.y += GRAVITY * 0.8
            self.pos += self.vel
            self.lifespan -= 2

    def draw(self, surface):
        if self.lifespan > 0:
            alpha = 255
            if self.state == 'falling':
                alpha = int(max(0, min(255, 255 * (self.lifespan / 100))))

            size = 2 if self.state == 'holding' else 1.5
            color_with_alpha = (*GOLD, alpha)

            particle_surf = pygame.Surface(
                (size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                particle_surf, color_with_alpha, (size, size), size)
            surface.blit(
                particle_surf, (int(self.pos.x - size), int(self.pos.y - size)))

    def is_alive(self):
        return self.pos.y < SCREEN_HEIGHT + 20 and self.lifespan > 0


class Firework:
    def __init__(self, start_x=None, start_y=None, initial_particles=False):
        self.exploded = False
        self.particles = []
        self.smoke_trail = []

        self.explosion_color = (random.randint(100, 255), random.randint(
            100, 255), random.randint(100, 255))

        # Membuat 30 palet warna acak yang unik untuk ledakan kedua kembang api ini
        self.crackle_palette = [(random.randint(100, 255), random.randint(
            100, 255), random.randint(100, 255)) for _ in range(30)]

        self.num_particles = random.randint(90, 160)
        self.max_speed = random.uniform(3.5, 5.5)
        self.particle_lifespan = random.uniform(70, 90)

        if initial_particles:
            self.exploded = True
            self.particles = self._create_explosion(
                start_x, start_y, self.num_particles, self.explosion_color, True, max_speed=self.max_speed, base_lifespan=self.particle_lifespan)
        else:
            start_x = random.randint(
                int(SCREEN_WIDTH * 0.2), int(SCREEN_WIDTH * 0.8))
            start_vy = -random.uniform(9, 13)
            self.rocket = Particle(
                start_x, SCREEN_HEIGHT, 0, start_vy, WHITE, 3, ROCKET_LIFESPAN, True)

    def update(self):
        if not self.exploded:
            self.rocket.update()
            if random.random() < 0.5:
                self.smoke_trail.append(Particle(
                    self.rocket.pos.x, self.rocket.pos.y, 0, 0, GRAY, random.randint(1, 3), 40, False))

            if self.rocket.vel.y >= 0:
                self.explode()
        else:
            new_particles = []
            for p in self.particles:
                p.update()
                if p.can_crackle and not p.crackled and p.lifespan < p.initial_lifespan * 0.4 and random.random() < CRACKLE_CHANCE:
                    p.crackled = True
                    p.lifespan = 0

                    new_particles.extend(self._create_explosion(p.pos.x, p.pos.y, NUM_CRACKLE_PARTICLES,
                                         None, False, is_multicolor=True, palette=self.crackle_palette, max_speed=2.5))
            self.particles.extend(new_particles)

        for s in self.smoke_trail:
            s.update()

        self.particles = [p for p in self.particles if p.is_alive()]
        self.smoke_trail = [s for s in self.smoke_trail if s.is_alive()]

    def _create_explosion(self, x, y, num_particles, base_color, can_crackle_main, is_multicolor=False, palette=None, max_speed=4, base_lifespan=80):
        created_particles = []
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.1, 1)**1.5 * max_speed
            vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
            size = random.uniform(1.5, 2.5)
            lifespan = random.uniform(base_lifespan * 0.7, base_lifespan)

            if is_multicolor and palette:
                particle_color = random.choice(palette)
            else:
                particle_color = base_color

            created_particles.append(
                Particle(x, y, vx, vy, particle_color, size, lifespan, True, can_crackle_main))
        return created_particles

    def explode(self):
        self.exploded = True
        self.particles.extend(self._create_explosion(self.rocket.pos.x, self.rocket.pos.y, self.num_particles,
                              self.explosion_color, True, max_speed=self.max_speed, base_lifespan=self.particle_lifespan))
        self.rocket.lifespan = 0

    def draw(self, surface):
        if not self.exploded:
            self.rocket.draw(surface)

        for s in self.smoke_trail:
            s.draw(surface)
        for p in self.particles:
            p.draw(surface)

    def is_done(self):
        return self.exploded and not self.particles and not self.smoke_trail


def create_text_particles(message, font):
    text_surface = font.render(message, True, GOLD)
    text_rect = text_surface.get_rect(
        center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3))

    particles = []
    for x in range(0, text_surface.get_width(), 3):
        for y in range(0, text_surface.get_height(), 3):
            if text_surface.get_at((x, y))[3] > 0:
                target_pos = (text_rect.x + x, text_rect.y + y)
                particles.append(TextParticle(target_pos))
    return particles


def create_stars(num_stars):
    stars = []
    for _ in range(num_stars):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        brightness = random.choice([40, 60, 90])
        stars.append(((x, y), brightness))
    return stars


def main():
    fireworks = [Firework()]
    stars = create_stars(200)
    text_particles = []
    last_text_animation_time = pygame.time.get_ticks()

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                fireworks.append(
                    Firework(start_x=event.pos[0], start_y=event.pos[1], initial_particles=True))

        # Atur di sini untuk jumlah kembang api otomatis
        if random.random() < AUTO_FIREWORK_CHANCE:
            fireworks.append(Firework())

        if not text_particles and current_time - last_text_animation_time > TEXT_ANIMATION_INTERVAL:
            text_particles = create_text_particles(TEXT_MESSAGE, MESSAGE_FONT)
            last_text_animation_time = current_time

        for fw in fireworks:
            fw.update()
        for tp in text_particles:
            tp.update()

        fireworks = [fw for fw in fireworks if not fw.is_done()]
        text_particles = [tp for tp in text_particles if tp.is_alive()]

        trail_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        trail_surface.fill((0, 0, 8, 25))
        screen.blit(trail_surface, (0, 0))

        for star_data in stars:
            pos, brightness = star_data
            if random.random() < 0.001:
                new_brightness = random.choice([40, 60, 90])
                star_data = (pos, new_brightness)
            pygame.draw.circle(
                screen, (brightness, brightness, brightness), pos, 1)

        for fw in fireworks:
            fw.draw(screen)
        for tp in text_particles:
            tp.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
