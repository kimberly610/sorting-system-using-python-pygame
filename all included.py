import pygame
import sys
import random
import logging
import time
import math

# --- Logging setup ---
logging.basicConfig(filename="system.log", level=logging.INFO, format="%(asctime)s:%(message)s")
logging.info("Simulation Started")

# --- Sensor modes ---
valid_choices = {"weight": "Weight Sensor", "color": "Color Sensor", "size": "Size Sensor"}
chosen_sensor_choice = "weight"
chosen_sensor_name = valid_choices[chosen_sensor_choice]

# --- Pygame setup ---
pygame.init()
WIDTH, HEIGHT = 1100, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Conveyor Sorting Simulation — Attractive Mode")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)
big_font = pygame.font.SysFont(None, 28, bold=True)

# --- Colors ---
SENSOR_COLORS = {"Weight Sensor": (255, 200, 0), "Color Sensor": (0, 200, 200), "Size Sensor": (200, 0, 200)}
BOX_INNER = (245, 245, 245)
TEXT_COLOR = (10, 10, 10)
PACKAGE_COLORS = {"Red": (200, 40, 40), "Green": (40, 180, 40), "Blue": (40, 80, 200), "Yellow": (200, 180, 40)}

# --- Conveyor belt setup ---
INCOMING_Y = 120
INCOMING_HEIGHT = 120
OUTPUT_TOP_Y = 320
NUM_OUTPUT_BELTS = 4
OUTPUT_BELT_HEIGHT = 70
OUTPUT_GAP = 40
OUTPUT_BELT_POSITIONS = [OUTPUT_TOP_Y + i * (OUTPUT_BELT_HEIGHT + OUTPUT_GAP) for i in range(NUM_OUTPUT_BELTS)]

belt_offset = 0
BELT_SPEED_VIS = 4

# --- Package setup ---
PKG_W, PKG_H = 130, 70
PKG_SPEED = 2.5
POOL_SIZE = 10

# --- Sensor positions ---
sensor_positions = [
    {"name": "Weight Sensor", "x": 320},
    {"name": "Color Sensor", "x": 520},
    {"name": "Size Sensor", "x": 720},
]

# --- Arm setup ---
arm = {
    "x": None,
    "base_y": INCOMING_Y + INCOMING_HEIGHT,
    "length": 0,
    "target_length": 0,
    "speed": 12,
    "active": False
}

# --- Counts ---
total_spawned = 0
total_assigned = 0
assigned_counts = [0] * (NUM_OUTPUT_BELTS + 1)
processed_counts = [0] * (NUM_OUTPUT_BELTS + 1)
unsorted_count = 0

# --- Package pool ---
packages = []
for i in range(POOL_SIZE):
    color_name = random.choice(list(PACKAGE_COLORS.keys()))
    pkg = {
        "id": f"P{i+1}",
        "x": -random.randint(100, 1200),
        "y": INCOMING_Y + (INCOMING_HEIGHT - PKG_H) // 2,
        "color_name": color_name,
        "color": PACKAGE_COLORS[color_name],
        "weight": random.randint(1, 20),
        "size": random.choice(["Small", "Medium", "Large", "Extra Large"]),
        "belt": 0,
        "dropping": False,
        "target_y": None,
        "active": False
    }
    packages.append(pkg)

for s in sensor_positions:
    if s["name"] == chosen_sensor_name:
        arm["x"] = s["x"]

belt_queues = [[] for _ in range(NUM_OUTPUT_BELTS + 1)]
spawn_interval = 1.6
_last_spawn = time.time() - spawn_interval

# --- Mode Button Panel ---
button_width = 120
button_height = 30
button_spacing = 10
button_y = 76
button_rects = {
    "weight": pygame.Rect(16, button_y, button_width, button_height),
    "color": pygame.Rect(16 + (button_width + button_spacing), button_y, button_width, button_height),
    "size": pygame.Rect(16 + 2 * (button_width + button_spacing), button_y, button_width, button_height),
}

button_icons = {
    "weight": "⚖",
    "color": "🎨",
    "size": "📏"
}

# --- Sensor reading functions ---
def read_weight_sensor(pkg):
    logging.info(f"Read weight for {pkg['id']}: {pkg['weight']} kg")
    return pkg["weight"]

def read_color_sensor(pkg):
    logging.info(f"Read color for {pkg['id']}: {pkg['color_name']}")
    return pkg["color_name"]

def read_size_sensor(pkg):
    logging.info(f"Read size for {pkg['id']}: {pkg['size']}")
    return pkg["size"]

def actuator_move_package_to(pkg, output_belt_index):
    global total_assigned, assigned_counts
    total_assigned += 1
    assigned_counts[output_belt_index] += 1
    pkg["x"] = arm["x"] - PKG_W // 2
    base_y = OUTPUT_BELT_POSITIONS[output_belt_index - 1] + (OUTPUT_BELT_HEIGHT - PKG_H) // 2
    pkg["target_y"] = base_y
    pkg["dropping"] = True
    pkg["belt"] = output_belt_index
    pkg["active"] = True
    logging.info(f"Actuator: moving {pkg['id']} to output belt {output_belt_index}")

def decide_output_belt(pkg, mode):
    if mode == "weight":
        w = read_weight_sensor(pkg)
        if w <= 5:
            return 1
        elif w <= 10:
            return 2
        elif w <= 15:
            return 3
        else:
            return 4
    elif mode == "color":
        cname = read_color_sensor(pkg)
        mapping = {"Red": 1, "Green": 2, "Blue": 3, "Yellow": 4}
        return mapping.get(cname, 1)
    elif mode == "size":
        s = read_size_sensor(pkg)
        mapping = {"Small": 1, "Medium": 2, "Large": 3, "Extra Large": 4}
        return mapping.get(s, 1)
    return 1

def set_mode(new_mode):
    global chosen_sensor_choice, chosen_sensor_name, arm
    chosen_sensor_choice = new_mode
    chosen_sensor_name = valid_choices[new_mode]
    for s in sensor_positions:
        if s["name"] == chosen_sensor_name:
            arm["x"] = s["x"]
    logging.info(f"Mode changed to {chosen_sensor_choice}")

def spawn_package():
    global total_spawned
    for pkg in packages:
        if not pkg["active"]:
            pkg["active"] = True
            pkg["x"] = -random.randint(80, 500)
            pkg["y"] = INCOMING_Y + (INCOMING_HEIGHT - PKG_H) // 2
            pkg["color_name"] = random.choice(list(PACKAGE_COLORS.keys()))
            pkg["color"] = PACKAGE_COLORS[pkg["color_name"]]
            pkg["weight"] = random.randint(1, 20)
            pkg["size"] = random.choice(["Small", "Medium", "Large", "Extra Large"])
            pkg["belt"] = 0
            pkg["dropping"] = False
            pkg["target_y"] = None
            pkg["active"] = True
            total_spawned += 1
            return True
    return False

# --- Gradient background ---
def draw_gradient(surface, color1, color2):
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

# --- Main loop ---
running = True
while running:
    now = time.time()
    if now - _last_spawn >= spawn_interval:
        if spawn_package():
            _last_spawn = now

    mouse_x, mouse_y = pygame.mouse.get_pos()

    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False
        elif evt.type == pygame.MOUSEBUTTONDOWN:
            for key, rect in button_rects.items():
                if rect.collidepoint((mouse_x, mouse_y)):
                    set_mode(key)

    for pkg in packages:
        if not pkg["active"]:
            continue
        if pkg["belt"] == 0 and not pkg["dropping"]:
            pkg["x"] += PKG_SPEED
        if pkg["belt"] == 0 and not pkg["dropping"]:
            for s in sensor_positions:
                if s["name"] == chosen_sensor_name:
                    sensor_x = s["x"]
                    break
            if sensor_x - 6 < pkg["x"] + PKG_W / 2 < sensor_x + 6:
                out_index = decide_output_belt(pkg, chosen_sensor_choice)
                actuator_move_package_to(pkg, out_index)
                arm["target_length"] = (pkg["target_y"] + PKG_H) - arm["base_y"]
                if arm["target_length"] < 0:
                    arm["target_length"] = abs(arm["target_length"])
                arm["active"] = True
        if pkg["dropping"]:
            if pkg["y"] < pkg["target_y"]:
                pkg["y"] += 6
            else:
                pkg["y"] = pkg["target_y"]
                pkg["dropping"] = False
                if pkg["belt"] >= 1 and pkg not in belt_queues[pkg["belt"]]:
                    belt_queues[pkg["belt"]].append(pkg)
        if pkg["belt"] >= 1 and not pkg["dropping"]:
            pkg["x"] += PKG_SPEED
        if pkg["x"] > WIDTH + 80:
            if pkg["belt"] >= 1:
                if pkg in belt_queues[pkg["belt"]]:
                    belt_queues[pkg["belt"]].remove(pkg)
                processed_counts[pkg["belt"]] += 1
            else:
                unsorted_count += 1
            pkg["active"] = False
            pkg["belt"] = 0
            pkg["dropping"] = False
            pkg["target_y"] = None

    if arm["active"]:
        if arm["length"] < arm["target_length"]:
            arm["length"] += arm["speed"]
        else:
            arm["active"] = False
    else:
        if arm["length"] > 0:
            arm["length"] -= arm["speed"]
            if arm["length"] < 0:
                arm["length"] = 0

    belt_offset = (belt_offset - BELT_SPEED_VIS) % 40

    # --- Drawing ---
    draw_gradient(screen, (10, 10, 30), (60, 60, 80))

    pygame.draw.rect(screen, (50, 50, 50), (0, INCOMING_Y + 4, WIDTH, INCOMING_HEIGHT))
    pygame.draw.rect(screen, (80, 80, 80), (0, INCOMING_Y, WIDTH, INCOMING_HEIGHT))
    for sx in range(-40 + int(belt_offset), WIDTH, 40):
        pygame.draw.rect(screen, (120, 120, 120), (sx, INCOMING_Y, 20, INCOMING_HEIGHT))

    for idx, by in enumerate(OUTPUT_BELT_POSITIONS, start=1):
        pygame.draw.rect(screen, (50, 50, 50), (0, by + 4, WIDTH, OUTPUT_BELT_HEIGHT))
        pygame.draw.rect(screen, (80, 80, 80), (0, by, WIDTH, OUTPUT_BELT_HEIGHT))
        pygame.draw.rect(screen, (140, 140, 140), (0, by + OUTPUT_BELT_HEIGHT - 8, WIDTH, 8))
        txt = font.render(f"Belt {idx} — current:{len(belt_queues[idx])} assigned:{assigned_counts[idx]} processed:{processed_counts[idx]}", True, (240,240,240))
        screen.blit(txt, (WIDTH - 560, by + 10))

    for s in sensor_positions:
        color = SENSOR_COLORS[s["name"]]
        glow = 0
        if s["name"] == chosen_sensor_name:
            glow = abs(math.sin(time.time() * 3)) * 100
        glow_color = (min(255, color[0] + glow), min(255, color[1] + glow), min(255, color[2] + glow))
        pygame.draw.line(screen, glow_color, (s["x"], INCOMING_Y), (s["x"], INCOMING_Y + INCOMING_HEIGHT), 4 if s["name"] == chosen_sensor_name else 2)

    if arm["x"] is not None:
        pygame.draw.rect(screen, (50, 50, 50), (arm["x"] - 7 + 3, arm["base_y"] + 3, 14, arm["length"]))
        pygame.draw.rect(screen, (220, 180, 20), (arm["x"] - 7, arm["base_y"], 14, arm["length"]))

    for pkg in packages:
        if not pkg["active"]:
            continue
        pygame.draw.rect(screen, (0, 0, 0), (pkg["x"] + 4, pkg["y"] + 4, PKG_W, PKG_H))
        pygame.draw.rect(screen, pkg["color"], (pkg["x"], pkg["y"], PKG_W, PKG_H))
        pygame.draw.rect(screen, BOX_INNER, (pkg["x"] + 6, pkg["y"] + 6, PKG_W - 12, PKG_H - 12))
        screen.blit(font.render(pkg["id"], True, TEXT_COLOR), (pkg["x"] + 10, pkg["y"] + 6))
        if chosen_sensor_choice == "weight":
            screen.blit(font.render(f"W:{pkg['weight']}kg", True, TEXT_COLOR), (pkg["x"] + 10, pkg["y"] + 28))
        elif chosen_sensor_choice == "color":
            screen.blit(font.render(f"C:{pkg['color_name']}", True, TEXT_COLOR), (pkg["x"] + 10, pkg["y"] + 28))
        elif chosen_sensor_choice == "size":
            screen.blit(font.render(f"S:{pkg['size']}", True, TEXT_COLOR), (pkg["x"] + 10, pkg["y"] + 28))
        screen.blit(font.render(f"Bin:{pkg['belt']}", True, TEXT_COLOR), (pkg["x"] + 10, pkg["y"] + 46))

    # Mode display
    screen.blit(big_font.render(f"MODE: {chosen_sensor_choice.upper()}", True, (255, 255, 100)), (16, 16))

    # --- Draw buttons with icons ---
    for mode_key, rect in button_rects.items():
        selected = (chosen_sensor_choice == mode_key)
        pygame.draw.rect(screen, (180, 180, 50) if selected else (80, 80, 80), rect)
        pygame.draw.rect(screen, (200, 200, 200), rect, 2)
        label = font.render(f"{button_icons[mode_key]} {mode_key.capitalize()}", True, (0, 0, 0))
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    # Stats
    right_x = WIDTH - 320
    screen.blit(font.render(f"Input spawned: {total_spawned}", True, (220,220,220)), (right_x, 16))
    screen.blit(font.render(f"Total assigned: {total_assigned}", True, (220,220,220)), (right_x, 36))
    screen.blit(font.render(f"Total processed: {sum(processed_counts)}", True, (220,220,220)), (right_x, 56))
    screen.blit(font.render(f"Unsorted left incoming: {unsorted_count}", True, (220,220,220)), (right_x, 76))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()