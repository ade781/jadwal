import pygame
import random
import math
from pygame.math import Vector2

# --- Inisialisasi Pygame & Mixer ---
pygame.init()
pygame.mixer.init() # Inisialisasi untuk suara
pygame.font.init()

# --- Pengaturan Utama ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
FPS = 60

# --- Konstanta Fisika & Efek ---
GRAVITY = Vector2(0, 0.09)
WIND = Vector2(0.01, 0) # Efek angin kecil ke arah kanan
ROCKET_LIFESPAN = 255
AUTO_FIREWORK_CHANCE = 0.03 # Peluang kembang api otomatis
CRACKLE_CHANCE = 0.08
NUM_CRACKLE_PARTICLES = 15
TEXT_MESSAGE = "semangat belajar Fika"
TEXT_ANIMATION_INTERVAL = 10000
TEXT_PARTICLE_SPEED = 5
TEXT_PARTICLE_HOLD_TIME = 240

# --- Pengaturan Warna ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GOLD = (255, 215, 0)

# --- Setup Layar & Font ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Kembang Api Interaktif | [P]eony [W]illow [R]ing | [A]uto | Klik")
clock = pygame.time.Clock()
try:
    # Coba gunakan font yang lebih menarik jika ada
    MESSAGE_FONT = pygame.font.SysFont("segoeuisemibold", 72)
    HELP_FONT = pygame.font.SysFont("segoeuisemibold", 18)
except:
    MESSAGE_FONT = pygame.font.SysFont("arial", 72)
    HELP_FONT = pygame.font.SysFont("arial", 18)

# --- Memuat Suara (Placeholder) ---
# Ganti dengan file suara Anda. Jika file tidak ada, program akan tetap berjalan tanpa error.
try:
    launch_sound = pygame.mixer.Sound('launch.wav')
    explode_sound = pygame.mixer.Sound('explode.wav')
    crackle_sound = pygame.mixer.Sound('crackle.wav')
    launch_sound.set_volume(0.4)
    explode_sound.set_volume(0.5)
    crackle_sound.set_volume(0.3)
except (pygame.error, FileNotFoundError): # PERUBAHAN DI SINI
    # Jika file suara tidak ditemukan, buat objek Sound dummy
    class DummySound:
        def play(self): pass
    launch_sound = explode_sound = crackle_sound = DummySound()
    print("Warning: File suara tidak ditemukan atau tidak dapat dimuat. Program akan berjalan tanpa suara.")


class Particle:
    """Kelas partikel dasar untuk semua efek."""
    def __init__(self, pos, vel, color, size, lifespan, has_gravity=True, can_crackle=False):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
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
                self.vel += GRAVITY
            self.vel += WIND # Terapkan efek angin
            self.lifespan -= 1

    def draw(self, surface):
        if self.is_alive():
            # Alpha memudar seiring waktu
            alpha = max(0, int(255 * (self.lifespan / self.initial_lifespan)**1.5))
            particle_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (*self.color, alpha), (self.size, self.size), self.size)
            surface.blit(particle_surf, (self.pos.x - self.size, self.pos.y - self.size))

    def is_alive(self):
        return self.lifespan > 0


class TextParticle(Particle):
    """Partikel khusus untuk membentuk tulisan."""
    def __init__(self, target_pos):
        start_pos = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        super().__init__(start_pos, (0,0), GOLD, 2, 500, has_gravity=False)
        self.target_pos = Vector2(target_pos)
        self.state = 'moving_to_target'
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
            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color_with_alpha, (size, size), size)
            surface.blit(particle_surf, (self.pos.x - size, self.pos.y - size))

    def is_alive(self):
        return self.pos.y < SCREEN_HEIGHT + 20 and self.lifespan > 0


class Firework:
    """Kelas utama untuk kembang api."""
    def __init__(self, start_pos=None, firework_type='peony', initial_explosion=False):
        self.exploded = False
        self.particles = []
        self.smoke_trail = []
        self.firework_type = firework_type

        # Palet warna dibuat untuk setiap kembang api agar unik
        self.primary_color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        self.crackle_palette = [(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)) for _ in range(30)]

        if initial_explosion:
            # Jika langsung meledak (karena klik mouse)
            self.exploded = True
            explode_sound.play()
            self.explode(start_pos)
        else:
            # Peluncuran roket normal
            launch_sound.play()
            start_x = random.randint(int(SCREEN_WIDTH * 0.2), int(SCREEN_WIDTH * 0.8))
            start_vy = -random.uniform(10, 14)
            self.rocket = Particle((start_x, SCREEN_HEIGHT), (0, start_vy), WHITE, 3, ROCKET_LIFESPAN, True)

    def update(self):
        if not self.exploded:
            self.rocket.update()
            # Asap mengikuti roket
            if random.random() < 0.6:
                self.smoke_trail.append(Particle(self.rocket.pos, (0,0), GRAY, random.randint(1, 3), 40, False))

            # Meledak saat roket mencapai puncak (kecepatan y > 0)
            if self.rocket.vel.y >= 0:
                explode_sound.play()
                self.explode(self.rocket.pos)
        else:
            # Update partikel ledakan
            new_particles = []
            for p in self.particles:
                p.update()
                # Peluang partikel meletup (crackle)
                if p.can_crackle and not p.crackled and p.lifespan < p.initial_lifespan * 0.4 and random.random() < CRACKLE_CHANCE:
                    p.crackled = True
                    p.lifespan = 0
                    crackle_sound.play()
                    new_particles.extend(self._create_crackle(p.pos))
            self.particles.extend(new_particles)

        # Update asap dan bersihkan partikel yang mati
        for s in self.smoke_trail: s.update()
        self.particles = [p for p in self.particles if p.is_alive()]
        self.smoke_trail = [s for s in self.smoke_trail if s.is_alive()]

    def explode(self, pos):
        self.exploded = True
        self.rocket.lifespan = 0 # Matikan roket
        
        # Panggil metode ledakan berdasarkan tipe
        if self.firework_type == 'peony':
            self.particles.extend(self._create_peony_explosion(pos))
        elif self.firework_type == 'willow':
            self.particles.extend(self._create_willow_explosion(pos))
        elif self.firework_type == 'ring':
            self.particles.extend(self._create_ring_explosion(pos))

    # --- Metode untuk Tipe Ledakan Berbeda ---
    def _create_peony_explosion(self, pos):
        """Ledakan bulat klasik."""
        particles = []
        num_particles = random.randint(90, 160)
        max_speed = random.uniform(3.5, 5.5)
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.1, 1)**1.5 * max_speed
            vel = Vector2(math.cos(angle), math.sin(angle)) * speed
            size = random.uniform(1.5, 2.5)
            lifespan = random.uniform(70, 90)
            particles.append(Particle(pos, vel, self.primary_color, size, lifespan, True, True))
        return particles

    def _create_willow_explosion(self, pos):
        """Ledakan menjuntai seperti pohon willow."""
        particles = []
        num_particles = random.randint(60, 100)
        max_speed = random.uniform(2, 4)
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, 1) * max_speed
            vel = Vector2(math.cos(angle), math.sin(angle)) * speed
            size = random.uniform(1, 2)
            lifespan = random.uniform(120, 180) # Hidup lebih lama
            p = Particle(pos, vel, GOLD, size, lifespan, True, False)
            p.vel *= 0.8 # Kecepatan awal lebih lambat
            particles.append(p)
        return particles

    def _create_ring_explosion(self, pos):
        """Ledakan membentuk cincin."""
        particles = []
        num_particles = 100
        radius = 1 # Kecepatan partikel di cincin
        for i in range(num_particles):
            angle = (i / num_particles) * 2 * math.pi
            vel = Vector2(math.cos(angle), math.sin(angle)) * radius
            size = 2
            lifespan = 100
            # Kecepatan menyebar dari pusat
            vel *= random.uniform(2.5, 3.5)
            particles.append(Particle(pos, vel, self.primary_color, size, lifespan, True, True))
        return particles

    def _create_crackle(self, pos):
        """Ledakan kecil sekunder."""
        crackle_particles = []
        max_speed = 2.5
        for _ in range(NUM_CRACKLE_PARTICLES):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.1, 1) * max_speed
            vel = Vector2(math.cos(angle), math.sin(angle)) * speed
            size = random.uniform(1, 2)
            lifespan = random.uniform(30, 50)
            color = random.choice(self.crackle_palette)
            crackle_particles.append(Particle(pos, vel, color, size, lifespan, True, False))
        return crackle_particles

    def draw(self, surface):
        if not self.exploded: self.rocket.draw(surface)
        for s in self.smoke_trail: s.draw(surface)
        for p in self.particles: p.draw(surface)

    def is_done(self):
        return self.exploded and not self.particles and not self.smoke_trail


def create_text_particles(message, font):
    """Mengubah teks menjadi koordinat target untuk partikel."""
    text_surface = font.render(message, True, GOLD)
    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3))
    particles = []
    # Scan permukaan teks, buat partikel jika pixel tidak transparan
    for x in range(0, text_surface.get_width(), 3):
        for y in range(0, text_surface.get_height(), 3):
            if text_surface.get_at((x, y))[3] > 0:
                target_pos = (text_rect.x + x, text_rect.y + y)
                particles.append(TextParticle(target_pos))
    return particles


def create_stars(num_stars):
    """Membuat latar belakang bintang yang berkelip."""
    stars = []
    for _ in range(num_stars):
        pos = (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
        brightness = random.choice([40, 60, 90, 120])
        flicker_speed = random.uniform(0.0005, 0.002)
        stars.append({'pos': pos, 'brightness': brightness, 'flicker_speed': flicker_speed})
    return stars


def draw_help_text(surface, auto_fire_enabled, next_type):
    """Menampilkan teks bantuan di layar."""
    controls = [
        "[Klik] Ledakan Instan",
        f"[A] Auto-Launch: {'ON' if auto_fire_enabled else 'OFF'}",
        "[P] Peony",
        "[W] Willow",
        "[R] Ring",
        f"Tipe Selanjutnya: {next_type.capitalize()}"
    ]
    y_pos = 10
    for i, line in enumerate(controls):
        color = GOLD if f"[{next_type[0].upper()}]" in line else WHITE
        text_surf = HELP_FONT.render(line, True, color)
        surface.blit(text_surf, (10, y_pos + i * 22))

def main():
    fireworks = []
    stars = create_stars(250)
    text_particles = []
    last_text_animation_time = pygame.time.get_ticks()
    
    auto_fire_enabled = True
    next_firework_type = 'peony'

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Tombol kiri mouse
                    fireworks.append(Firework(start_pos=event.pos, firework_type=next_firework_type, initial_explosion=True))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    auto_fire_enabled = not auto_fire_enabled
                elif event.key == pygame.K_p:
                    next_firework_type = 'peony'
                elif event.key == pygame.K_w:
                    next_firework_type = 'willow'
                elif event.key == pygame.K_r:
                    next_firework_type = 'ring'

        # Kembang api otomatis jika diaktifkan
        if auto_fire_enabled and random.random() < AUTO_FIREWORK_CHANCE:
            fireworks.append(Firework(firework_type=next_firework_type))

        # Animasi teks periodik
        if not text_particles and current_time - last_text_animation_time > TEXT_ANIMATION_INTERVAL:
            text_particles = create_text_particles(TEXT_MESSAGE, MESSAGE_FONT)
            last_text_animation_time = current_time

        # --- Update semua objek ---
        for fw in fireworks: fw.update()
        for tp in text_particles: tp.update()

        # Bersihkan objek yang sudah tidak aktif
        fireworks = [fw for fw in fireworks if not fw.is_done()]
        text_particles = [tp for tp in text_particles if tp.is_alive()]

        # --- Proses Gambar (Drawing) ---
        # Latar belakang dengan efek jejak (trail)
        trail_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        trail_surface.fill((0, 0, 8, 25))
        screen.blit(trail_surface, (0, 0))

        # Gambar bintang
        for star in stars:
            if random.random() < star['flicker_speed']:
                star['brightness'] = random.choice([40, 60, 90, 120])
            pygame.draw.circle(screen, (star['brightness'], star['brightness'], star['brightness']), star['pos'], 1)

        # Gambar kembang api dan partikel teks
        for fw in fireworks: fw.draw(screen)
        for tp in text_particles: tp.draw(screen)

        # Tampilkan teks bantuan
        draw_help_text(screen, auto_fire_enabled, next_firework_type)

        # Update display
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
