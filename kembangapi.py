import pygame
import random
import math
from pygame.math import Vector2

# --- Inisialisasi Pygame & Mixer ---
pygame.init()
pygame.mixer.init()
pygame.font.init()

# --- Pengaturan Utama ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
FPS = 60
WATERLINE_Y = SCREEN_HEIGHT * 0.75  # Posisi permukaan air

# --- Konstanta Fisika & Efek ---
GRAVITY = Vector2(0, 0.08)  # Gravitasi sedikit dikurangi agar lebih 'melayang'
WIND = Vector2(0.01, 0)
ROCKET_LIFESPAN = 255
AUTO_FIREWORK_CHANCE = 0.02
CRACKLE_CHANCE = 0.08
NUM_CRACKLE_PARTICLES = 15
SHOOTING_STAR_CHANCE = 0.001

# --- Pengaturan Teks ---
DEFAULT_TEXT_MESSAGE = "Ketik [T] & Enter"
TEXT_ANIMATION_INTERVAL = 12000
TEXT_PARTICLE_SPEED = 5
TEXT_PARTICLE_HOLD_TIME = 240

# --- Pengaturan Grand Finale ---
FINALE_DURATION = 15000  # 15 detik
FINALE_LAUNCH_RATE = 0.3  # Peluang luncurkan kembang api setiap frame selama finale

# --- Pengaturan Warna ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GOLD = (255, 215, 0)
CITY_COLOR = (15, 15, 25)
WATER_OVERLAY_COLOR = (5, 10, 20, 120)
HEART_COLORS = [(255, 20, 147), (255, 105, 180), (255, 182, 193)]

# --- Setup Layar & Font ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Kembang Api v5 | [M]ulti | [H]ati | [F]inale")
clock = pygame.time.Clock()
try:
    MESSAGE_FONT = pygame.font.SysFont("segoeuisemibold", 72)
    HELP_FONT = pygame.font.SysFont("segoeuisemibold", 18)
    INPUT_FONT = pygame.font.SysFont("segoeuisemibold", 36)
except:
    MESSAGE_FONT = pygame.font.SysFont("arial", 72)
    HELP_FONT = pygame.font.SysFont("arial", 18)
    INPUT_FONT = pygame.font.SysFont("arial", 36)

# --- Memuat Suara (Placeholder) ---
try:
    launch_sound = pygame.mixer.Sound('launch.wav')
    explode_sound = pygame.mixer.Sound('explode.wav')
    crackle_sound = pygame.mixer.Sound('crackle.wav')
    launch_sound.set_volume(0.4)
    explode_sound.set_volume(0.5)
    crackle_sound.set_volume(0.3)
except (pygame.error, FileNotFoundError):
    class DummySound:
        def play(self): pass
    launch_sound = explode_sound = crackle_sound = DummySound()
    print("Warning: File suara tidak ditemukan. Program akan berjalan tanpa suara.")


class Particle:
    """Kelas partikel yang disempurnakan dengan state dan fisika yang lebih baik."""

    def __init__(self, pos, vel, color, size, lifespan, has_gravity=True, can_crackle=False, is_reflection=False, state='burning'):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.color = color
        self.size = size
        self.lifespan = lifespan
        self.initial_lifespan = lifespan
        self.has_gravity = has_gravity
        self.can_crackle = can_crackle
        self.crackled = False
        self.is_reflection = is_reflection
        self.state = state  # 'burning', 'fading', 'glitter'

    def update(self):
        if not self.is_alive():
            return

        self.lifespan -= 1
        self.pos += self.vel

        if self.has_gravity:
            # Pada state 'glitter', partikel jatuh lebih lambat dan terpengaruh angin lebih kuat
            if self.state == 'glitter':
                self.vel *= 0.96  # Efek hambatan udara
                self.vel += GRAVITY * 0.5
                self.vel += WIND * 1.5
            else:
                self.vel += GRAVITY
                self.vel += WIND

        # Transisi state partikel untuk efek visual yang lebih baik
        if self.lifespan < self.initial_lifespan * 0.2 and self.state == 'burning':
            self.state = 'fading'
            if random.random() < 0.2:  # Peluang menjadi glitter
                self.state = 'glitter'
                # Perpanjang sedikit umur untuk jatuh
                self.lifespan = self.initial_lifespan * 0.6

    def draw(self, surface):
        if not self.is_alive():
            return

        alpha_multiplier = 0.4 if self.is_reflection else 1.0
        current_size = self.size

        if self.state == 'glitter':
            # Efek berkelip untuk glitter
            alpha = max(0, int(random.choice(
                [150, 200, 255]) * alpha_multiplier))
            current_size *= 0.8
        else:
            alpha = max(
                0, int(255 * (self.lifespan / self.initial_lifespan)**1.2 * alpha_multiplier))

        if self.is_reflection:
            current_size *= 0.7
            if self.pos.y < WATERLINE_Y:
                self.lifespan = 0

        if current_size < 1:
            return

        particle_surf = pygame.Surface(
            (current_size * 2, current_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, (*self.color, alpha),
                           (current_size, current_size), current_size)
        surface.blit(particle_surf, (self.pos.x -
                     current_size, self.pos.y - current_size))

    def is_alive(self):
        return self.lifespan > 0


class TextParticle(Particle):
    # ... (Kelas ini sebagian besar tetap, hanya mewarisi Particle yang baru)
    def __init__(self, target_pos):
        start_pos = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        super().__init__(start_pos, (0, 0), GOLD, 2,
                         500, has_gravity=False, state='holding')
        self.target_pos = Vector2(target_pos)
        self.state = 'moving_to_target'  # State awal yang baru
        self.hold_timer = TEXT_PARTICLE_HOLD_TIME

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
                self.has_gravity = True
        elif self.state == 'falling':
            super().update()
            self.lifespan -= 1.5

    def draw(self, surface):
        if self.lifespan > 0:
            alpha = 255
            if self.state == 'falling':
                alpha = int(max(0, min(255, 255 * (self.lifespan / 100))))
            size = 2 if self.state == 'holding' else 1.5
            color_with_alpha = (*self.color, alpha)
            p_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, color_with_alpha, (size, size), size)
            surface.blit(p_surf, (self.pos.x - size, self.pos.y - size))

    def is_alive(self): return self.pos.y < SCREEN_HEIGHT + \
        20 and self.lifespan > 0


class Firework:
    """Kelas kembang api yang dirombak untuk mendukung sub-ledakan (multi-break)."""

    def __init__(self, start_pos=None, firework_type='peony', initial_explosion=False, is_sub_explosion=False):
        self.particles, self.smoke_trail, self.reflections = [], [], []
        self.firework_type = firework_type
        self.sub_explosions = []
        self.exploded = False
        self.primary_color = (random.randint(100, 255), random.randint(
            100, 255), random.randint(100, 255))
        self.crackle_palette = [(random.randint(100, 255), random.randint(
            100, 255), random.randint(100, 255)) for _ in range(30)]

        if not is_sub_explosion:
            launch_sound.play()

        if initial_explosion or is_sub_explosion:
            explode_sound.play()
            self.explode(start_pos)
        else:  # Peluncuran roket dari bawah
            start_x = random.randint(
                int(SCREEN_WIDTH * 0.2), int(SCREEN_WIDTH * 0.8))
            start_vy = -random.uniform(10, 14.5)
            self.rocket = Particle(
                (start_x, SCREEN_HEIGHT), (0, start_vy), WHITE, 3, ROCKET_LIFESPAN, True)
            self.rocket_reflection = self._create_reflection_particle(
                self.rocket)

    def _create_reflection_particle(self, p):
        # ... (Tidak ada perubahan signifikan di sini)
        ry = WATERLINE_Y + (WATERLINE_Y - p.pos.y)
        rvy = -p.vel.y * 0.3
        return Particle((p.pos.x, ry), (p.vel.x, rvy), p.color, p.size, p.lifespan, False, False, True)

    def update(self):
        if not self.exploded:
            self.rocket.update()
            self.rocket_reflection = self._create_reflection_particle(
                self.rocket)
            if random.random() < 0.6:
                self.smoke_trail.append(
                    Particle(self.rocket.pos, (0, 0), GRAY, random.randint(1, 3), 40, False))
            if self.rocket.vel.y >= 0:
                explode_sound.play()
                self.rocket.lifespan = 0
                self.explode(self.rocket.pos)
        else:
            new_particles, new_reflections = [], []
            for i in range(len(self.particles) - 1, -1, -1):
                p = self.particles[i]
                p.update()
                # Logika baru untuk Multi-Break
                if p.state == 'comet' and not p.is_alive():
                    sub_type = random.choice(['peony', 'crackle'])
                    self.sub_explosions.append(
                        Firework(p.pos, sub_type, is_sub_explosion=True))
                    self.particles.pop(i)
                    continue

                if p.can_crackle and not p.crackled and p.lifespan < p.initial_lifespan * 0.4 and random.random() < CRACKLE_CHANCE:
                    p.crackled = True
                    p.lifespan = 0
                    crackle_sound.play()
                    burst, reflect = self._create_crackle(p.pos)
                    new_particles.extend(burst)
                    new_reflections.extend(reflect)
            self.particles.extend(new_particles)
            self.reflections.extend(new_reflections)

        for group in [self.smoke_trail, self.particles, self.reflections, self.sub_explosions]:
            for item in group:
                item.update()

        # Bersihkan semua partikel dan sub-ledakan yang mati
        self.particles = [p for p in self.particles if p.is_alive()]
        self.smoke_trail = [s for s in self.smoke_trail if s.is_alive()]
        self.reflections = [r for r in self.reflections if r.is_alive()]
        self.sub_explosions = [
            se for se in self.sub_explosions if not se.is_done()]

    def explode(self, pos):
        self.exploded = True
        methods = {'peony': self._create_peony, 'willow': self._create_willow, 'ring': self._create_ring,
                   'heart': self._create_heart, 'multi': self._create_multi_break}
        particles, reflections = methods.get(
            self.firework_type, self._create_peony)(pos)
        self.particles.extend(particles)
        self.reflections.extend(reflections)

    def _create_explosion_base(self, pos, num, func):
        p, r = [], []
        [p.append(func(pos)) for _ in range(num)]
        [r.append(self._create_reflection_particle(i)) for i in p]
        return p, r

    # PERBAIKAN: Semua metode pembuatan ledakan diubah untuk membuat Vector2 dengan benar.
    def _create_peony(self, pos):
        def create_particle_func(p):
            vel = Vector2()
            vel.from_polar((random.uniform(3.5, 6.5), random.uniform(0, 360)))
            return Particle(p, vel, self.primary_color, random.uniform(1.5, 2.5), random.uniform(100, 150), True, True)
        return self._create_explosion_base(pos, random.randint(90, 160), create_particle_func)

    def _create_willow(self, pos):
        def create_particle_func(p):
            vel = Vector2()
            vel.from_polar((random.uniform(2, 4), random.uniform(0, 360)))
            vel *= 0.8
            return Particle(p, vel, GOLD, random.uniform(1, 2), random.uniform(150, 200), True, False, state='glitter')
        return self._create_explosion_base(pos, random.randint(60, 100), create_particle_func)

    def _create_ring(self, pos):
        def create_particle_func(p):
            vel = Vector2()
            vel.from_polar((random.uniform(2.5, 3.5), random.uniform(0, 360)))
            return Particle(p, vel, self.primary_color, 2, 120, True, True)
        return self._create_explosion_base(pos, 100, create_particle_func)

    def _create_heart(self, pos):
        particles, reflections = [], []
        for i in range(120):
            t = (i / 120) * 2 * math.pi
            scale = 12.0
            x = scale * (16 * (math.sin(t)**3))
            y = -scale * (13 * math.cos(t) - 5*math.cos(2*t) -
                          2*math.cos(3*t) - math.cos(4*t))
            p = Particle(pos, Vector2(x, y).normalize() * random.uniform(1.5, 2.5), random.choice(
                HEART_COLORS), random.uniform(2, 3), random.uniform(110, 140), True, False)
            particles.append(p)
            reflections.append(self._create_reflection_particle(p))
        return particles, reflections

    def _create_multi_break(self, pos):
        def create_particle_func(p):
            vel = Vector2()
            vel.from_polar((random.uniform(3.0, 5.0), random.uniform(0, 360)))
            return Particle(p, vel, (255, 255, 200), 4, random.uniform(60, 90), True, False, state='comet')
        return self._create_explosion_base(pos, random.randint(5, 8), create_particle_func)

    def _create_crackle(self, pos):
        def create_particle_func(p):
            vel = Vector2()
            vel.from_polar((random.uniform(0.5, 3.0), random.uniform(0, 360)))
            return Particle(p, vel, random.choice(self.crackle_palette), random.uniform(1, 2), random.uniform(30, 50), True, False)
        return self._create_explosion_base(pos, NUM_CRACKLE_PARTICLES, create_particle_func)

    def draw(self, surface):
        if not self.exploded and hasattr(self, 'rocket'):
            self.rocket.draw(surface)
            if hasattr(self, 'rocket_reflection'):
                self.rocket_reflection.draw(surface)
        for group in [self.smoke_trail, self.particles, self.reflections, self.sub_explosions]:
            for item in group:
                item.draw(surface)

    def is_done(self):
        return self.exploded and not self.particles and not self.smoke_trail and not self.reflections and not self.sub_explosions


class ShootingStar:
    """Kelas untuk bintang jatuh di latar belakang."""

    def __init__(self):
        self.pos = Vector2(random.randint(0, SCREEN_WIDTH),
                           random.randint(10, 50))
        self.vel = Vector2(-random.uniform(15, 25), random.uniform(5, 10))
        self.lifespan = 100
        self.particles = []

    def update(self):
        self.lifespan -= 1
        if self.is_alive():
            self.particles.append(
                Particle(self.pos.copy(), (0, 0), WHITE, random.uniform(1, 2), 20, False))
            self.pos += self.vel
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.is_alive()]

    def draw(self, surface): [p.draw(surface) for p in self.particles]
    def is_alive(self): return self.lifespan > 0

# --- Fungsi-fungsi Bantuan ---


def create_stars(num_stars):
    """Membuat latar belakang bintang yang berkelip."""
    return [{'pos': (random.randint(0, SCREEN_WIDTH), random.randint(0, int(WATERLINE_Y))),
             'brightness': random.choice([40, 60, 90, 120]),
             'flicker_speed': random.uniform(0.0005, 0.002)} for _ in range(num_stars)]


def create_text_particles(message, font):
    """Mengubah teks menjadi koordinat target untuk partikel."""
    if not message:
        return []
    text_surface = font.render(message, True, GOLD)
    text_rect = text_surface.get_rect(
        center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3))
    particles = []
    for x in range(0, text_surface.get_width(), 3):
        for y in range(0, text_surface.get_height(), 3):
            if text_surface.get_at((x, y))[3] > 0:
                tp = TextParticle((text_rect.x + x, text_rect.y + y))
                tp.state = 'moving_to_target'
                particles.append(tp)
    return particles


def create_city():
    """Membuat data kota, termasuk jendela."""
    city = {'rects': [], 'windows': []}
    x = 0
    while x < SCREEN_WIDTH:
        w = random.randint(30, 80)
        h = random.randint(int(SCREEN_HEIGHT * 0.1), int(SCREEN_HEIGHT * 0.25))
        rect = pygame.Rect(x, WATERLINE_Y - h, w, h)
        city['rects'].append(rect)
        for _ in range(int(w * h / 800)):
            city['windows'].append({
                'pos': (random.randint(rect.left+2, rect.right-4), random.randint(rect.top+2, rect.bottom-4)),
                'on': random.random() > 0.4
            })
        x += w + random.randint(1, 5)
    return city


def draw_background_elements(surface, stars, moon_pos, city, shooting_stars):
    for star in stars:
        if random.random() < star['flicker_speed']:
            star['brightness'] = random.choice([40, 60, 90, 120])
        pygame.draw.circle(surface, (star['brightness'],)*3, star['pos'], 1)
    pygame.draw.circle(surface, (200, 200, 180), moon_pos, 25)
    pygame.draw.circle(surface, (0, 0, 8), (moon_pos[0]+10, moon_pos[1]-5), 22)
    for ss in shooting_stars:
        ss.draw(surface)
    water_surf = pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT - WATERLINE_Y), pygame.SRCALPHA)
    for i in range(15):
        alpha = 40 - i*2
        pygame.draw.line(water_surf, (100, 100, 120, alpha), (0, 10+i*4 + math.sin(pygame.time.get_ticks() /
                         500 + i)*2), (SCREEN_WIDTH, 10+i*4 + math.sin(pygame.time.get_ticks()/500 + i)*2))
    water_surf.fill(WATER_OVERLAY_COLOR, special_flags=pygame.BLEND_RGBA_ADD)
    surface.blit(water_surf, (0, WATERLINE_Y))
    for rect in city['rects']:
        pygame.draw.rect(surface, CITY_COLOR, rect)
    for window in city['windows']:
        if window['on']:
            if random.random() < 0.0005:
                window['on'] = False
            pygame.draw.rect(surface, GOLD, (*window['pos'], 2, 2))
        elif random.random() < 0.0001:
            window['on'] = True


def draw_help_text(surface, auto_fire, next_type, is_typing, finale_active):
    y = 10
    text_to_show = ""
    if finale_active:
        text_to_show = "GRAND FINALE!"
    elif is_typing:
        text_to_show = "Ketik pesan, tekan ENTER..."
    if text_to_show:
        surf = HELP_FONT.render(text_to_show, True, GOLD)
        surface.blit(surf, (SCREEN_WIDTH/2 - surf.get_width()/2, y))
        return

    controls = [f"[A] Auto-Launch: {'ON' if auto_fire else 'OFF'}", "[P]eony [W]illow [R]ing [H]eart [M]ulti",
                f"Berikutnya: {next_type.capitalize()}", "[T] Ganti Teks | [F] Grand Finale"]
    for i, line in enumerate(controls):
        color = GOLD if f"[{next_type[0].upper()}]" in line else WHITE
        surface.blit(HELP_FONT.render(line, True, color), (10, y + i * 22))

# --- Loop Utama (main) ---


def main():
    fireworks, stars, shooting_stars = [], create_stars(250), []
    city, text_particles = create_city(), []
    user_text, current_text_message = "", DEFAULT_TEXT_MESSAGE
    last_text_time, moon_pos = - \
        TEXT_ANIMATION_INTERVAL, (SCREEN_WIDTH*0.8, SCREEN_HEIGHT*0.2)
    auto_fire, is_typing, finale_active, finale_end_time = True, False, False, 0
    next_firework_type = 'peony'

    running = True
    while running:
        time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            if is_typing:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        is_typing = False
                        current_text_message = user_text if user_text else DEFAULT_TEXT_MESSAGE
                        user_text = ""
                        text_particles = create_text_particles(
                            current_text_message, MESSAGE_FONT)
                        last_text_time = time
                    elif event.key == pygame.K_BACKSPACE:
                        user_text = user_text[:-1]
                    else:
                        user_text += event.unicode
            else:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    fireworks.append(
                        Firework(event.pos, next_firework_type, True))
                if event.type == pygame.KEYDOWN:
                    key_map = {pygame.K_a: 'auto', pygame.K_p: 'peony', pygame.K_w: 'willow', pygame.K_r: 'ring',
                               pygame.K_h: 'heart', pygame.K_m: 'multi', pygame.K_t: 'typing', pygame.K_f: 'finale'}
                    action = key_map.get(event.key)
                    if action == 'auto':
                        auto_fire = not auto_fire
                    elif action in ['peony', 'willow', 'ring', 'heart', 'multi']:
                        next_firework_type = action
                    elif action == 'typing':
                        is_typing = True
                    elif action == 'finale':
                        finale_active = True
                        finale_end_time = time + FINALE_DURATION

        # --- Update Logic ---
        if finale_active:
            if time > finale_end_time:
                finale_active = False
            elif random.random() < FINALE_LAUNCH_RATE:
                fireworks.append(Firework(firework_type=random.choice(
                    ['peony', 'willow', 'ring', 'heart', 'multi'])))
        elif auto_fire and random.random() < AUTO_FIREWORK_CHANCE:
            fireworks.append(Firework(firework_type=next_firework_type))
        if random.random() < SHOOTING_STAR_CHANCE:
            shooting_stars.append(ShootingStar())

        if not text_particles and time - last_text_time > TEXT_ANIMATION_INTERVAL and not is_typing:
            text_particles = create_text_particles(
                current_text_message, MESSAGE_FONT)
            last_text_time = time

        for group in [fireworks, text_particles, shooting_stars]:
            [item.update() for item in group]
        fireworks = [fw for fw in fireworks if not fw.is_done()]
        text_particles = [tp for tp in text_particles if tp.is_alive()]
        shooting_stars = [ss for ss in shooting_stars if ss.is_alive()]

        # --- Drawing Logic ---
        screen.fill((0, 0, 8))
        draw_background_elements(screen, stars, moon_pos, city, shooting_stars)
        for fw in fireworks:
            fw.draw(screen)
        for tp in text_particles:
            tp.draw(screen)

        if is_typing:
            box_rect = pygame.Rect(
                SCREEN_WIDTH * 0.1, SCREEN_HEIGHT/2 - 50, SCREEN_WIDTH * 0.8, 100)
            pygame.draw.rect(screen, (20, 20, 40), box_rect)
            pygame.draw.rect(screen, GOLD, box_rect, 2)
            ts = INPUT_FONT.render(user_text, True, WHITE)
            if (time // 500) % 2 == 0:
                screen.blit(INPUT_FONT.render("_", True, WHITE),
                            (box_rect.x+10+ts.get_width(), box_rect.y+25))
            screen.blit(ts, (box_rect.x + 10, box_rect.y + 25))
        draw_help_text(screen, auto_fire, next_firework_type,
                       is_typing, finale_active)

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
