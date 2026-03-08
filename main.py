#!/usr/bin/env python3
import random
import time
import os
import sys
import re
import textwrap


# --- TERMINAL COLORS ---
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

# --- GAME CONSTANTS & LORE ---
PHYSICAL_RESTRAINTS = [
    "anchor", "bound_hands", "gagged", "glass_heels", "suspended", 
    "blinded", "barbed_wings", "feral_claws", "chastity_belt", 
    "iron_corset", "halo_of_thorns", "pet_leash", "blood_shackles", "sensory_deprivation"
]
INSTANT_TRAPS = ["tethered", "expanding_core", "oblivion_helm", "guillotine"]

EFFECT_SUMMARIES = {
    "anchor": "[PERM] Abyssal Anchor: Heavy weight. -15 Stamina/turn.",
    "bound_hands": "[PERM] Penitent Manacles: Attacks require typing QTEs.",
    "gagged": "[PERM] Iron Gag: Potions require swallowing QTEs.",
    "glass_heels": "[PERM] Spiked Sabatons: Take 25% recoil DMG on attack.",
    "suspended": "[PERM] Crucifixion Chains: Hoisted in air. DEF is 0.",
    "blinded": "[PERM] Eclipse Veil: Blinded. Enemy intent hidden.",
    "barbed_wings": "[PERM] Barbed Wire: -15 HP, -5 Stamina per turn.",
    "feral_claws": "[PERM] Feral Claws: +80% DMG, -50% DEF, recoil.",
    "chastity_belt": "[PERM] Iron Chastity: Dodging impaired. Stamina costs rise.",
    "iron_corset": "[PERM] Iron Corset: Crushing lungs. Max HP reduced.",
    "halo_of_thorns": "[PERM] Halo of Thorns: Mana usage drains HP.",
    "pet_leash": "[PERM] Pet Leash: Randomly yanks you, skipping turns.",
    "blood_shackles": "[PERM] Blood Shackles: Iron teeth drain 10 HP per turn.",
    "sensory_deprivation": "[PERM] Sensory Deprivation: Complete UI blackout.",
    "rampage": "[TEMP] Blind Bloodlust: MIND SHATTERED. Auto-attacking wildly.",
    "halo_fracture": "[TEMP] Shattering Halo: Detonates soon for massive DMG.",
    "exposed": "[TEMP] Shattered Aegis: Armor ruined. DOUBLE damage."
}

PLAYER_ART = {
    "1": { "idle": ["      _O_      ", "     / | \\_/>  ", "       |       ", "      / \\      ", "    _/   \\_    ", "               ", "               "], "atk":  ["               ", "      _O_      ", "     / | \\     ", "    --/ \\-->   ", "    _/   \\_    ", "               ", "               "] },
    "2": { "idle": ["      [O]      ", "     /[|]\\     ", "    [  |  ]    ", "      / \\      ", "    _|   |_    ", "               ", "               "], "atk":  ["               ", "      [O]      ", "    [/[|]\\     ", "    [  |  ]>>  ", "    _|   |_    ", "               ", "               "] },
    "3": { "idle": ["       ^       ", "      /O\\      ", "     / | \\     ", "    <--|-->    ", "      / \\      ", "     /   \\     ", "               "], "atk":  ["               ", "       ^       ", "   --->O\\      ", "      /| \\     ", "     / \\  -->  ", "    /   \\      ", "               "] },
    "4": { "idle": ["       /\\      ", "      /  \\     ", "      (O )     ", "     / | \\     ", "    |  |       ", "    o / \\      ", "                 "], "atk":  ["       /\\      ", "      /  \\     ", "      (O )*~.  ", "     / | \\   * ", "    |  |      *", "    o / \\      ", "               "] },
}

ENEMY_ART = {
    "beast": { "idle": ["               ", "    /\\___/\\    ", "   ( o   o )   ", "   (  =^=  )   ", "   (        )  ", "   /|      |\\  ", "               "], "atk":  ["               ", "    /\\___/\\    ", "   ( >   < )   ", "   (  =O=  )>> ", "   (        )  ", "   /|      |\\  ", "               "] },
    "void": { "idle": ["      .o.      ", "    .oOOOo.    ", "   .O     O.   ", "   O       O   ", "   `O     O`   ", "    `O...O`    ", "      ~~~      "], "atk":  ["      .o.      ", "    .oOOOo.    ", "   .O o o O.   ", "   O  >O<  O>> ", "   `O     O`   ", "    `O...O`    ", "      ~~~      "] },
    "nature": { "idle": ["      \\|/      ", "     \\|||/     ", "    --_O_--    ", "      |||      ", "     /|||\\     ", "    //   \\\\    ", "               "], "atk":  ["               ", "      \\|/      ", "     \\|||/     ", "    --_O_-->>> ", "      |||      ", "     /|||\\     ", "               "] }
}

# ==========================================
# PLAYER DATA CLASS
# ==========================================
class Player:
    def __init__(self, name, u_class, c_name):
        self.name = name
        self.user_class = u_class
        self.class_name = c_name
        self.level, self.exp, self.exp_needed = 1, 0, 100

        # Base Stats Matrix
        if u_class == "1":
            self.health, self.max_health, self.mana, self.max_mana, self.atk, self.def_ = 100, 100, 20, 20, 15, 10
        elif u_class == "2":
            self.health, self.max_health, self.mana, self.max_mana, self.atk, self.def_ = 150, 150, 10, 10, 8, 15
        elif u_class == "3":
            self.health, self.max_health, self.mana, self.max_mana, self.atk, self.def_ = 80, 80, 15, 15, 20, 5
        elif u_class == "4":
            self.health, self.max_health, self.mana, self.max_mana, self.atk, self.def_ = 70, 70, 100, 100, 5, 3
        elif u_class == "5":
            self.health, self.max_health, self.mana, self.max_mana, self.atk, self.def_ = 80, 80, 80, 80, 25, 5

        self.stamina, self.max_stamina = 100, 100
        self.true_damage, self.true_defense = self.atk, self.def_
        self.extra_damage, self.extra_defense = 0, 0

        self.warrior_rage = 0
        self.rogue_combo = 0
        self.tank_guarding = False

        self.lucidity = 100
        self.resonance_meter = 0

        self.curses = {
            "rampage": 0, "halo_fracture": 0, "exposed": 0, "burn": 0,
            "anchor": 0, "bound_hands": 0, "gagged": 0, "glass_heels": 0, 
            "suspended": 0, "blinded": 0, "barbed_wings": 0, "feral_claws": 0,
            "chastity_belt": 0, "iron_corset": 0, "halo_of_thorns": 0, "pet_leash": 0,
            "blood_shackles": 0, "sensory_deprivation": 0,
            "tethered": False, "expanding_core": False, "oblivion_helm": False, 
            "guillotine": False, "endurance_test": False
        }

        self.p_state = "idle"
        self.player_offset = 0

    def update_stats(self):
        self.true_damage = self.atk + self.extra_damage
        self.true_defense = self.def_ + self.extra_defense

        if self.user_class == "1":
            self.true_damage += int(self.warrior_rage * 0.15)
        if self.user_class == "2" and self.tank_guarding:
            self.true_defense *= 3

        if self.user_class == "5":
            if self.health < self.max_health * 0.3:
                self.true_damage = int(self.true_damage * 2.0)
            if self.curses["feral_claws"] == -1:
                self.true_damage = int(self.true_damage * 1.8)
                self.true_defense = int(self.true_defense * 0.5)
            if self.curses["suspended"] == -1 or self.curses["exposed"] > 0:
                self.true_defense = 0
            if self.curses["rampage"] > 0:
                self.true_damage = int(self.true_damage * 1.5)

    def get_art(self):
        if self.user_class != "5":
            return PLAYER_ART[self.user_class][self.p_state].copy()

        head = "  ,;\\  O  /;,  "
        wings = "   \\\\//|\\\\//   "
        arms = "     \\/ \\/     "
        body = "       |       "
        legs1 = "      / \\      "
        legs2 = "     /   \\     "
        floor = "               "

        if self.curses["halo_fracture"] > 0 or self.curses["halo_of_thorns"] == -1:
            head = head.replace("  O  ", " *O* ")

        if self.curses["sensory_deprivation"] == -1:
            head = "  ,;\\ [X] /;,  "
        elif self.curses["blinded"] == -1 and self.curses["gagged"] == -1:
            head = head.replace("O", "X")
        elif self.curses["blinded"] == -1:
            head = head.replace("O", "-")
        elif self.curses["gagged"] == -1:
            head = head.replace("O", "m")

        if self.curses["barbed_wings"] == -1:
            wings = "   #\\//|\\\\/#   "
            head = "  *#\\  O  /#* "

        if self.curses["bound_hands"] == -1:
            arms = "      \\=/      "
        if self.curses["iron_corset"] == -1:
            body = "      [|]      "
        if self.curses["chastity_belt"] == -1:
            legs1 = "      /U\\      "
        if self.curses["glass_heels"] == -1:
            legs2 = "     L   J     "
        if self.curses["anchor"] == -1:
            floor = "     [WT]      "
        if self.curses["pet_leash"] == -1:
            head = head.replace("  O  ", " ~O~ ")

        sprite = [head, wings, arms, body, legs1, legs2, floor]

        if self.curses["suspended"] == -1:
            sprite = ["       |       ", head.replace(",;\\", "   ").replace("/;,", "   "), wings, arms, body, legs1, legs2]

        return sprite

# ==========================================
# GAME ENGINE 
# ==========================================
class LeavelyEngine:
    def __init__(self):
        self.players = []
        self.active_p = None
        self.party_gold = 0
        self.inv = {
            "Health Potion": 2, "Mana Potion": 1, "Skip Potion": 0, 
            "Resonance Vent": 0, "Halo Reset": 0, "Bolt Cutters": 0,
            "Extra Protection Potion": 0, "Extra Damage Potion": 0
        }

        self.difficulty = 1.0
        self.local_dfct = 1.0
        self.qte_mult = 1.0
        self.max_curses = 1

        self.creature_names = ["Grave-Stalker", "Void-Fiend", "Flesh-Weaver", "Abyssal Crawler", "Desecrator"]
        self.boss_names = ["The Warden of Chains", "Abyssal Behemoth", "The Grand Inquisitor", "Sovereign of Agony"]

        self.creature_name = ""
        self.creature_health = 0
        self.creature_max_health = 0
        self.creature_defense = 0
        self.creature_damage = 0
        self.creature_level = 0
        self.creature_type = "physical"
        self.e_sprite_type = "beast"
        self.is_boss = False
        self.enemy_intent = "agile"
        self.enemy_state = "idle"
        self.enemy_offset = 0

        self.story_log = ["The abyss watches.", "Journey begins..."]

    def init_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.write(HIDE_CURSOR)

    def restore_terminal(self):
        sys.stdout.write(SHOW_CURSOR)

    def render_frame(self, ui_text):
        sys.stdout.write('\033[2J\033[H' + ui_text)
        sys.stdout.flush()

    def strip_ansi(self, text):
        return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', text)

    def pad(self, text, width=85):
        return "  " + text + (" " * max(0, width - len(self.strip_ansi(text))))

    def center(self, text, width=85):
        return (" " * (max(0, width - len(self.strip_ansi(text))) // 2)) + text

    def log_event(self, text):
        self.story_log.append(text)
        if len(self.story_log) > 5:
            self.story_log.pop(0)

    def get_input(self):
        sys.stdout.write(SHOW_CURSOR)
        try:
            ans = input().strip().lower()
        except:
            self.restore_terminal()
            sys.exit(0)
        sys.stdout.write(HIDE_CURSOR)
        return ans

    def dramatic_prompt(self, text, color=WHITE, shake=False):
        self.draw()
        print(f"\n  {color}{text}{RESET}")
        if shake:
            self.screen_shake(intensity=3)
        sys.stdout.write(SHOW_CURSOR)
        input(f"\n  {WHITE}[ Press ENTER to continue ]{RESET}")
        sys.stdout.write(HIDE_CURSOR)

    def generate_bar(self, current, maximum, length=12, color=GREEN, hidden=False):
        if hidden: return f"{RED}[????????????]{RESET}"
        if maximum <= 0: maximum = 1
        fill = max(0, min(length, int(length * current / maximum)))
        return f"{color}[{'█' * fill}{'░' * (length - fill)}]{RESET}"

    def build_ui(self, message=""):
        p = self.active_p

        # Determine if Sensory Deprivation is active
        is_deprived = p and p.curses["sensory_deprivation"] == -1
        is_blinded = p and p.curses["blinded"] == -1

        buffer = [self.pad(f"{CYAN}={'=' * 83}{RESET}")]
        buffer.append(self.center(f"{MAGENTA}[ BOSS ENEMY ]{RESET}" if self.is_boss else f"{RED}[ ENEMY ]{RESET}"))

        intent = f"INTENT: {self.enemy_intent.upper()}"

        if is_deprived:
            buffer.append(self.pad(f"{RED}[ ???????? ] (Lv ??){RESET} | INTENT: {RED}???{RESET}"))
            buffer.append(self.pad(f"HP: {self.generate_bar(0, 1, hidden=True)} | ATK: ??? | DEF: ???"))
        elif is_blinded:
            buffer.append(self.pad(f"{self.creature_name} (Lv {int(self.creature_level)}) | INTENT: {RED}???{RESET}"))
            buffer.append(self.pad(f"HP: {self.generate_bar(0, 1, hidden=True)} | ATK: ??? | DEF: ???"))
        else:
            buffer.append(self.pad(f"{self.creature_name} (Lv {int(self.creature_level)}) | {self.creature_type.capitalize()} | {YELLOW}{intent}{RESET}"))
            buffer.append(self.pad(f"HP: {self.generate_bar(self.creature_health, self.creature_max_health, color=MAGENTA if self.is_boss else RED)} {int(self.creature_health)}/{int(self.creature_max_health)} | ATK: {int(self.creature_damage)} | DEF: {int(self.creature_defense)}"))

        buffer.append(self.pad(f"{CYAN}-{'=' * 83}{RESET}"))

        if p: p_art = p.get_art()
        else: p_art = PLAYER_ART["1"]["idle"].copy()

        e_art = ENEMY_ART.get(self.e_sprite_type, ENEMY_ART["beast"])[self.enemy_state]
        p_c = RED if p and p.curses["rampage"] > 0 else (MAGENTA if p and p.resonance_meter >= 80 else CYAN if p and p.user_class == "5" else GREEN)
        e_c = MAGENTA if self.is_boss else RED

        p_off = p.player_offset if p else 0
        for i in range(7):
            left_pad = " " * (2 + p_off)
            mid_pad = " " * (25 - p_off - self.enemy_offset)
            buffer.append(f"{left_pad}{p_c}{p_art[i]}{RESET}{mid_pad}{e_c}{e_art[i]}{RESET}")

        buffer.append(self.pad(f"{CYAN}-{'=' * 83}{RESET}"))
        buffer.append(self.center(f"{GREEN}[ PARTY - GOLD: {self.party_gold} ]{RESET}"))

        for pl in self.players:
            mark = f"{YELLOW}>>{RESET}" if pl == self.active_p else "  "
            stm_c = RED if pl.stamina < 30 else GREEN

            top_line = f"{mark} {pl.name} ({pl.class_name} Lv {pl.level}) | ATK: {int(pl.true_damage)} | DEF: {int(pl.true_defense)}"
            bar_line = f"    HP: {self.generate_bar(pl.health, pl.max_health)} {int(pl.health)}/{int(pl.max_health)} | MP: {self.generate_bar(pl.mana, pl.max_mana, color=BLUE)} | {stm_c}STM: {pl.stamina}%{RESET}"

            if pl.user_class == "1": bar_line += f" | {RED}RAGE: {pl.warrior_rage}%{RESET}"
            elif pl.user_class == "2" and pl.tank_guarding: bar_line += f" | {CYAN}[GUARDING]{RESET}"
            elif pl.user_class == "3": bar_line += f" | {YELLOW}COMBO: {pl.rogue_combo}{RESET}"
            elif pl.user_class == "5": 
                luc_c = RED if pl.lucidity < 30 else CYAN
                bar_line += f" | {YELLOW}RES: {pl.resonance_meter}%{RESET} | {luc_c}LUC: {pl.lucidity}%{RESET}"

            buffer.append(self.pad(top_line))
            buffer.append(self.pad(bar_line))

            if pl.user_class == "5" and pl == self.active_p:
                active_perms = [k for k, v in pl.curses.items() if v == -1]
                active_temps = [k for k, v in pl.curses.items() if v > 0]
                if active_perms:
                    p_str = ", ".join([k.replace("_", " ").title() for k in active_perms])
                    wrapped = textwrap.wrap(f"[PERM] {p_str}", width=75)
                    for w in wrapped: buffer.append(self.pad(f"    * {RED}{w}{RESET}"))
                if active_temps:
                    t_str = ", ".join([f"{k.replace('_', ' ').title()} ({pl.curses[k]}T)" for k in active_temps])
                    wrapped = textwrap.wrap(f"[TEMP] {t_str}", width=75)
                    for w in wrapped: buffer.append(self.pad(f"    * {MAGENTA}{w}{RESET}"))

        buffer.append(self.pad(f"{CYAN}-{'=' * 83}{RESET}"))

        log_lines = self.story_log[-5:]
        while len(log_lines) < 5: log_lines.append("")
        for log in log_lines:
            color = RED if any(w in log.lower() for w in ['curse', 'damage', 'blood', 'shatters', 'agony', 'trap', 'fail']) else WHITE
            buffer.append(self.pad(f"> {color}{log}{RESET}" if log else "> "))

        buffer.append(self.pad(f"{CYAN}={'=' * 83}{RESET}"))
        if message:
            for line in message.split('\n'): buffer.append(self.pad(line))
        return "\n".join(buffer)

    def draw(self, message=""): self.render_frame(self.build_ui(message))

    def screen_shake(self, intensity=2, duration=0.4):
        end = time.time() + duration
        lines = self.build_ui().split('\n')
        while time.time() < end:
            y, x = random.randint(-intensity, intensity), random.randint(-intensity, intensity)
            shaken = lines.copy()
            if y > 0: shaken = ['\033[K'] * y + shaken[:-y]
            elif y < 0: shaken = shaken[-y:] + ['\033[K'] * (-y)
            sys.stdout.write('\033[2J\033[H')
            sys.stdout.write("\n".join([(" " * max(0, x)) + ln for ln in shaken]))
            sys.stdout.flush()
            time.sleep(0.04)
        self.draw()

    def animate_p(self, p):
        p.p_state = "atk"; self.draw(); time.sleep(0.15)
        p.player_offset = 10; self.draw(); time.sleep(0.15)
        p.p_state = "idle"; p.player_offset = 0; self.draw()

    def animate_e(self):
        self.enemy_state = "atk"; self.draw(); time.sleep(0.2)
        self.enemy_offset = 10; self.draw(); self.screen_shake(2, 0.2); time.sleep(0.1)
        self.enemy_state = "idle"; self.enemy_offset = 0; self.draw()

    def set_difficulty_scaling(self):
        d = self.local_dfct
        if d == 0.25: self.max_curses = 1; self.qte_mult = 1.5
        elif d == 0.4: self.max_curses = 2; self.qte_mult = 1.0
        elif d == 0.75: self.max_curses = 3; self.qte_mult = 0.8
        else: self.max_curses = 5; self.qte_mult = 0.6

    def creature_spawn(self):
        party_max_lv = max(p.level for p in self.players)
        self.creature_level = party_max_lv + random.uniform(self.difficulty - 1, self.difficulty)
        self.creature_level = max(1, self.creature_level)
        scale = 1.75 if len(self.players) > 1 else 1.0 

        if random.random() < 0.2 or self.players[0].level % 5 == 0:
            self.is_boss = True; self.creature_name = random.choice(self.boss_names)
            mult = 0.3 + (self.local_dfct * 0.4)
            self.creature_damage = int((self.creature_level * random.randint(15, 25)) * mult * scale)
            self.creature_max_health = int((self.creature_level * random.randint(60, 90)) * mult * scale)
            self.creature_health = self.creature_max_health
            self.creature_defense = int((self.creature_level * random.randint(10, 20)) * mult * scale)
            self.e_sprite_type = "void"
            self.log_event(f"BOSS ENCOUNTER! {self.creature_name} steps out.")
        else:
            self.is_boss = False; self.creature_name = random.choice(self.creature_names)
            mult = 0.3 + (self.local_dfct * 0.4)
            self.creature_damage = int((self.creature_level * random.randint(8, 15)) * mult * scale)
            self.creature_max_health = int((self.creature_level * random.randint(25, 40)) * mult * scale)
            self.creature_health = self.creature_max_health
            self.creature_defense = int((self.creature_level * random.randint(5, 12)) * mult * scale)
            self.e_sprite_type = "beast"
            self.log_event(f"A wild {self.creature_name} blocks your path.")

        for p in self.players: p.update_stats()
        self.enemy_intent = random.choice(["agile", "brutal", "guard"])
        self.dramatic_prompt("COMBAT INITIATED.", color=YELLOW)

    # --- ANGEL QTE MECHANICS ---
    def run_memory_qte(self, p):
        p.curses["oblivion_helm"] = False
        self.draw(f"  {MAGENTA}=== [ THE OBLIVION HELM ] ===\n  {WHITE}Memorize the sequence quickly!{RESET}\n")
        time.sleep(1.5); seq = str(random.randint(10000, 99999))
        self.draw(f"  {CYAN}MEMORIZE: {seq}{RESET}\n"); time.sleep(1.0 * self.qte_mult)
        self.draw(f"  {MAGENTA}WHAT WAS THE SEQUENCE?{RESET}\n")
        ans = self.get_input()
        if ans == seq: self.dramatic_prompt("Memory retained. Helm shattered.", color=GREEN)
        else:
            p.stamina = max(0, p.stamina - 40); p.exp = max(0, p.exp - 50)
            self.dramatic_prompt("Memories ripped away! -40 Stamina, -50 EXP.", color=RED, shake=True)

    def run_accuracy_qte(self, p):
        p.curses["guillotine"] = False
        target = round(random.uniform(3.0, 5.0), 1)
        self.draw(f"  {MAGENTA}=== [ GUILLOTINE PENDULUM ] ===\n  {WHITE}Press ENTER exactly {target}s after GO!{RESET}\n")
        time.sleep(1.5); self.draw(f"  {RED}READY... GO!{RESET}\n")
        start = time.time(); sys.stdout.write(SHOW_CURSOR); input("  PRESS ENTER!"); sys.stdout.write(HIDE_CURSOR)
        elapsed = time.time() - start

        window = 0.5 * self.qte_mult
        if abs(elapsed - target) <= window: self.dramatic_prompt(f"Perfect timing ({elapsed:.2f}s). Escaped!", color=GREEN)
        else:
            p.health -= 50; msg = "Too early!" if elapsed < target else "Too late!"
            self.dramatic_prompt(f"{msg} ({elapsed:.2f}s). The blade slices deep! -50 HP.", color=RED, shake=True)

    def run_expanding_core_qte(self, p):
        p.curses["expanding_core"] = False
        target = random.choice(["purge", "expel", "burst"]); t = 2.5 * self.qte_mult
        self.draw(f"  {RED}EXPANDING CORE! Type '{target}' in {t:.1f}s!{RESET}\n")
        start_t = time.time(); ans = self.get_input()
        if ans == target and (time.time() - start_t) <= t: self.dramatic_prompt("PURGED THE CORE!", color=GREEN)
        else:
            p.max_health -= 15; p.health = min(p.health, p.max_health)
            self.dramatic_prompt("MUTILATED! Max HP permanently reduced by 15!", color=MAGENTA, shake=True)

    def run_tether_qte(self, p):
        p.curses["tethered"] = False
        k = random.choice(['q','w','e','a','s','d']); t = 1.5 * self.qte_mult
        self.draw(f"  {RED}JUDGMENT HOOK! Type '{k}' and hit ENTER in {t:.1f}s!{RESET}\n")
        start_t = time.time(); ans = self.get_input()
        if ans == k and (time.time() - start_t) <= t: self.dramatic_prompt("BRACED! Avoided slam.", color=GREEN)
        else: p.health -= 30; self.dramatic_prompt("Dragged and slammed! -30 HP.", color=RED, shake=True)

    def run_desperate_struggle(self, p):
        active_perms = [k for k, v in p.curses.items() if v == -1]
        if not active_perms:
            self.dramatic_prompt("No permanent physical restraints to break.", color=YELLOW); return False

        menu = f"  {MAGENTA}Which restraint will you pull against?{RESET}\n"
        for i, c in enumerate(active_perms, 1): menu += f"  [{i}] {c.replace('_', ' ').title()}\n"
        self.draw(menu); choice = self.get_input()

        try: target_curse = active_perms[int(choice)-1]
        except: self.dramatic_prompt("Invalid choice. Struggle wasted.", color=RED); p.stamina -= 10; return False

        # Multi-stage painful QTE
        words = ["pull", "strain", "break"]
        for w in words:
            t = 2.5 * self.qte_mult
            self.draw(f"  {MAGENTA}STRUGGLE! Type: '{w}' in {t:.1f}s!{RESET}\n")
            start_t = time.time()
            ans = self.get_input()
            if ans != w or (time.time() - start_t) > t:
                p.health -= 25; p.stamina -= 20
                self.dramatic_prompt("FAILED! The iron tears your flesh. -25 HP.", color=RED, shake=True)
                return False

        p.curses[target_curse] = 0; p.stamina -= 20
        self.dramatic_prompt(f"SUCCESS! {target_curse.replace('_', ' ').upper()} shattered.", color=GREEN)
        return True

    # --- PROCESS PLAYER TURN ---
    def process_player_turn(self, p):
        p.tank_guarding = False

        if p.user_class == "5":
            num_curses = random.randint(1, self.max_curses)
            applied = 0

            pool = [k for k, v in p.curses.items() if (isinstance(v, bool) and v is False and k not in ["endurance_test"]) or (isinstance(v, int) and v == 0 and k in PHYSICAL_RESTRAINTS)]
            if p.curses["halo_fracture"] == 0: pool.append("halo_fracture")
            random.shuffle(pool)

            for curse in pool:
                if applied >= num_curses: break
                if curse == "halo_fracture": p.curses[curse] = 4; self.log_event("CURSE: SHATTERING HALO! The divine bomb ticks down.")
                elif curse in INSTANT_TRAPS: p.curses[curse] = True
                else:
                    p.curses[curse] = -1 
                    if curse == "anchor": self.log_event("CURSE: ABYSSAL ANCHOR! A massive weight clamps to your waist.")
                    elif curse == "glass_heels": self.log_event("CURSE: SPIKED SABATONS! Iron boots lock on.")
                    elif curse == "bound_hands": self.log_event("CURSE: PENITENT MANACLES! Your hands are bound. Attacks are crippled.")
                    elif curse == "gagged": self.log_event("CURSE: IRON GAG! A brutal device forces your mouth open.")
                    elif curse == "suspended": self.log_event("CURSE: SUSPENSION BINDS! Ethereal ropes hoist you in the air.")
                    elif curse == "blinded": self.log_event("CURSE: ECLIPSE VEIL! A heavy blindfold seals your sight.")
                    elif curse == "barbed_wings": self.log_event("CURSE: BARBED WIRE! Razor wire tightly coils your wings.")
                    elif curse == "feral_claws": self.log_event("CURSE: FERAL CLAWS! Your hands mutate painfully.")
                    elif curse == "chastity_belt": self.log_event("CURSE: IRON CHASTITY! Your movements are heavily restricted.")
                    elif curse == "iron_corset": self.log_event("CURSE: IRON CORSET! Your lungs are squeezed, reducing Max HP.")
                    elif curse == "halo_of_thorns": self.log_event("CURSE: HALO OF THORNS! Spikes dig into your skull.")
                    elif curse == "pet_leash": self.log_event("CURSE: PET LEASH! A heavy iron collar and chain snaps on.")
                    elif curse == "blood_shackles": self.log_event("CURSE: BLOOD SHACKLES! Spiked iron tears your wrists.")
                    elif curse == "sensory_deprivation": self.log_event("CURSE: SENSORY DEPRIVATION! A heavy iron box locks over your head.")
                applied += 1

            if applied > 0: self.dramatic_prompt(f"[ THE ABYSS BINDS {p.name.upper()} ]", color=MAGENTA)

            res_gain = int(random.randint(10, 25) * (self.local_dfct * 2))
            p.resonance_meter += max(5, res_gain)
            active_binds = sum(1 for k, v in p.curses.items() if v == -1 or v is True)
            p.lucidity = max(0, p.lucidity - (5 + (active_binds * 8))) 

            if p.lucidity <= 0 and p.curses["rampage"] == 0:
                p.curses["rampage"] = 3; p.lucidity = 100
                self.dramatic_prompt(f"{p.name}'S MIND SHATTERS! Bloodlust triggers!", color=RED, shake=True)

            if p.curses["anchor"] == -1: p.stamina = max(0, p.stamina - 15)
            if p.curses["barbed_wings"] == -1: p.health -= 15; p.stamina = max(0, p.stamina - 5)
            if p.curses["blood_shackles"] == -1: p.health -= 10
            if p.curses["iron_corset"] == -1: p.max_health = max(10, p.max_health - 2); p.health = min(p.health, p.max_health)

            if p.resonance_meter >= 100:
                p.health -= 40; p.resonance_meter = 0; p.stamina = 0
                self.dramatic_prompt("RESONANCE OVERLOAD! Took 40 DMG!", color=RED, shake=True); return

            if p.curses["halo_fracture"] > 0:
                p.curses["halo_fracture"] -= 1
                if p.curses["halo_fracture"] == 0:
                    nuke = int(p.max_health * 0.5); p.health -= nuke
                    self.dramatic_prompt(f"HALO DETONATION! Took {nuke} unblockable DMG!", color=MAGENTA, shake=True)

            if p.stamina <= 0:
                p.stamina = 40
                self.dramatic_prompt("EXHAUSTED! You lose your turn gasping for breath!", color=RED); return

            if p.curses["pet_leash"] == -1 and random.random() < 0.3:
                self.dramatic_prompt("THE LEASH YANKS YOU! You stumble and lose your turn!", color=RED, shake=True); return

            if p.curses["oblivion_helm"]: self.run_memory_qte(p)
            if p.curses["guillotine"]: self.run_accuracy_qte(p)
            if p.curses["tethered"]: self.run_tether_qte(p)
            if p.curses["expanding_core"]: self.run_expanding_core_qte(p)

        if p.health <= 0: return

        for key in ["rampage", "exposed", "burn"]:
            if p.curses.get(key, 0) > 0: p.curses[key] -= 1

        p.update_stats()
        self.player_action_menu(p)

    def player_action_menu(self, p):
        attacks = []
        for _ in range(3):
            m = round(random.uniform(0.5, 2.5), 2)
            dmg = int(p.true_damage * m)
            hit = max(5, min(95, int(100 - (m*20)) + random.randint(-15, 15)))

            if p.user_class == "5":
                if p.curses["chastity_belt"] == -1: hit = int(hit * 0.8) 
                if p.curses["sensory_deprivation"] == -1: hit = int(hit * 0.5)

            stam = max(5, int(15 * m) + random.randint(-5, 5))
            attacks.append({"dmg": dmg, "hit": hit, "stam": stam})

        while True:
            if p.user_class == "5" and p.curses["rampage"] > 0:
                self.draw(f"  {RED}BLOODLUST ACTIVE! You have lost control!{RESET}\n")
                self.get_input()
                s = random.choice(attacks); p.stamina -= s["stam"]; self.animate_p(p)
                if random.randint(1, 100) <= s["hit"]:
                    self.creature_health -= s['dmg']
                    if p.curses["feral_claws"] == -1: p.health -= 20
                    self.dramatic_prompt(f"Wildly hit for {s['dmg']} DMG!", color=RED, shake=True)
                else: self.dramatic_prompt("WILD ATTACK MISSED.", color=RED)
                return

            menu = f"  {p.name}'S TURN:\n"

            if p.user_class == "5" and p.curses["bound_hands"] == -1:
                menu += f"  [1] Attack (HANDS BOUND. Requires Reflex QTE)\n"
            else:
                for i in range(3):
                    menu += f"  [{i+1}] Attack (Dmg: ~{attacks[i]['dmg']} | Hit: {attacks[i]['hit']}% | Stam: -{attacks[i]['stam']})\n"

            c_action = "Class Action"
            if p.user_class == "1": c_action = f"Execution (100% Rage)"
            elif p.user_class == "2": c_action = f"Bulwark Guard (20 Stam)"
            elif p.user_class == "3": c_action = f"Assassinate (3 Combo)"
            elif p.user_class == "4": c_action = f"Hellfire Burn (30 MP)"
            elif p.user_class == "5": c_action = f"Writhe in Chains (-15 HP, +20 STM, +10 MP)"

            menu += f"  [3] {c_action}\n  [4] Party Inventory\n"

            if p.user_class == "5":
                menu += f"  [{MAGENTA}5{RESET}] Desperate Struggle (Target 1 PERM Restraint)\n"
                if p.lucidity < 100: menu += f"  [{CYAN}6{RESET}] Pierce Palm to Stabilize (-15 HP, -10 Stam, +50 Lucidity)\n"

            self.draw(menu)
            c = self.get_input()

            if c in ["1", "2", "3"] and not (c == "3" and p.user_class != "5"): 
                # If hands are bound, any attack selection forces QTE
                if p.user_class == "5" and p.curses["bound_hands"] == -1 and c in ["1", "2"]:
                    cmd = random.choice(["swing", "slash", "strike", "thrust"])
                    t = 2.5 * self.qte_mult
                    self.draw(f"  {MAGENTA}HANDS BOUND! Type '{cmd}' in {t:.1f}s to attack!{RESET}\n")
                    s = time.time(); ans = self.get_input()
                    if ans != cmd or (time.time() - s) > t:
                        self.dramatic_prompt("You fumbled the weapon. Turn lost.", color=RED)
                        return
                    idx = 0 # Default to attack 0 if bound
                else:
                    if c == "3" and p.user_class == "5": pass # Handled below
                    else: idx = int(c) - 1

                if c == "3" and p.user_class == "5":
                    p.health -= 15; p.stamina = min(p.max_stamina, p.stamina + 20); p.mana = min(p.max_mana, p.mana + 10)
                    self.dramatic_prompt("You writhe against the iron. Skin tears. +20 STM, +10 MP.", color=MAGENTA, shake=True); return

                if p.user_class == "5" and p.curses["suspended"] == -1:
                    self.dramatic_prompt("You are bound mid-air! You cannot attack!", color=RED); continue

                if p.stamina < attacks[idx]["stam"]:
                    self.dramatic_prompt("Not enough stamina!", color=RED); continue

                p.stamina -= attacks[idx]["stam"]; self.animate_p(p)

                if random.randint(1, 100) <= attacks[idx]["hit"]:
                    actual = max(1, attacks[idx]["dmg"] - int(self.creature_defense * 0.2))
                    if p.user_class == "5" and (p.curses["feral_claws"] == -1 or p.curses["glass_heels"] == -1): p.health -= 15
                    self.creature_health -= actual
                    self.dramatic_prompt(f"IMPACT! {int(actual)} DMG dealt.", color=GREEN)

                    if p.user_class == "1": p.warrior_rage = min(100, p.warrior_rage + (25 if c == "2" else 15))
                    if p.user_class == "3" and c == "1": p.rogue_combo = min(5, p.rogue_combo + 1)
                else:
                    self.dramatic_prompt("ATTACK MISSED.", color=YELLOW)
                return 

            elif c == "3" and p.user_class != "5":
                if p.user_class == "1":
                    if p.warrior_rage >= 100: p.warrior_rage = 0; self.animate_p(p); self.creature_health -= p.true_damage * 3; self.dramatic_prompt(f"EXECUTION! {p.true_damage * 3} DMG!", color=RED); return 
                    else: self.dramatic_prompt("Not enough Rage!", color=YELLOW); continue
                elif p.user_class == "2":
                    if p.stamina >= 20: p.tank_guarding = True; p.stamina -= 20; self.dramatic_prompt("Shield raised! DEF x3. Enemy Provoked.", color=CYAN); return 
                    else: self.dramatic_prompt("Not enough Stamina!", color=YELLOW); continue
                elif p.user_class == "3":
                    if p.rogue_combo >= 3: p.rogue_combo -= 3; self.animate_p(p); self.creature_health -= p.true_damage * 2; self.dramatic_prompt("ASSASSINATED! Critical Hit!", color=MAGENTA); return 
                    else: self.dramatic_prompt("Not enough Combo!", color=YELLOW); continue
                elif p.user_class == "4":
                    if p.mana >= 30: p.mana -= 30; self.animate_p(p); self.creature_health -= p.true_damage * 2; p.curses["burn"] = 3; self.dramatic_prompt("HELLFIRE! Enemy is burning.", color=RED); return 
                    else: self.dramatic_prompt("Not enough MP!", color=YELLOW); continue

            elif c == "4":
                owned = [k for k, v in self.inv.items() if v > 0]
                if not owned: self.dramatic_prompt("Inventory empty.", color=RED); continue

                inv_menu = "  PARTY INVENTORY:\n"
                for i, item in enumerate(owned, 1): inv_menu += f"  [{i}] {item} (x{self.inv[item]})\n"
                inv_menu += "  [0] Back\n"

                self.draw(inv_menu); i_c = self.get_input()
                if i_c == "0": continue
                if i_c.isdigit() and 1 <= int(i_c) <= len(owned):
                    sel = owned[int(i_c)-1]; 

                    # Iron Gag Interactive Potion Swallow
                    if p.user_class == "5" and p.curses["gagged"] == -1 and "Potion" in sel:
                        t = 2.0 * self.qte_mult
                        self.draw(f"  {MAGENTA}IRON GAG! Type 'swallow' in {t:.1f}s to force it down!{RESET}\n")
                        s = time.time(); ans = self.get_input()
                        if ans != "swallow" or (time.time() - s) > t:
                            self.inv[sel] -= 1; p.health -= 15
                            self.dramatic_prompt("You choke! Potion wasted. -15 HP.", color=RED, shake=True); return

                    if sel == "Halo Reset":
                        if p.user_class == "5" and p.curses["halo_fracture"] > 0:
                            self.inv[sel] -= 1; p.curses["halo_fracture"] = 0; self.dramatic_prompt("Halo reset! Bomb deactivated.", color=CYAN, shake=True); return 
                        else: self.dramatic_prompt("No active Halo to reset.", color=YELLOW); continue

                    if sel == "Bolt Cutters":
                        if p.user_class == "5":
                            a_perms = [k for k, v in p.curses.items() if v == -1]
                            if a_perms:
                                f = random.choice(a_perms); p.curses[f] = 0; self.inv[sel] -= 1; self.dramatic_prompt(f"Used Cutters! {f.replace('_',' ').upper()} broken instantly.", color=GREEN); return 
                            else: self.dramatic_prompt("No permanent restraints to cut.", color=YELLOW); continue
                        else: self.dramatic_prompt("Only Angels need Bolt Cutters.", color=YELLOW); continue

                    if sel == "Resonance Vent":
                        if p.user_class == "5":
                            if p.curses["halo_of_thorns"] == -1: p.health -= 20
                            self.inv[sel] -= 1; p.resonance_meter = 0; self.dramatic_prompt("Resonance Purged!", color=CYAN); return 
                        else: self.dramatic_prompt("Only Angels build Resonance.", color=YELLOW); continue

                    if p.user_class == "5" and p.curses["halo_of_thorns"] == -1 and "Potion" in sel: p.health -= 15
                    self.inv[sel] -= 1

                    if sel == "Health Potion": p.health = min(p.max_health, p.health+40); return 
                    elif sel == "Mana Potion": p.mana = min(p.max_mana, p.mana+40); return 
                    elif sel == "Skip Potion": return 
                    elif sel == "Extra Damage Potion": p.extra_damage += 20; return 
                    elif sel == "Extra Protection Potion": p.extra_defense += 20; return 

            elif c == "5" and p.user_class == "5": 
                if self.run_desperate_struggle(p): return
            elif c == "6" and p.user_class == "5" and p.lucidity < 100:
                if p.health > 15 and p.stamina >= 10:
                    p.health -= 15; p.stamina -= 10; p.lucidity = min(100, p.lucidity + 50)
                    self.dramatic_prompt("You pierce your palm. Mind stabilized. +50 Lucidity.", color=CYAN); return 
                else: self.dramatic_prompt("Not enough HP/Stamina!", color=RED)

    def run_enemy_turn(self):
        if self.creature_health <= 0: return

        self.log_event(f"The {self.creature_name} attacks!")
        self.animate_e()

        alive_players = [pl for pl in self.players if pl.health > 0]
        if not alive_players: return

        target = random.choice(alive_players)
        tanks = [pl for pl in alive_players if pl.user_class == "2" and pl.tank_guarding]

        if tanks:
            target = random.choice(tanks)
            self.log_event(f"{target.name} provoked the attack!")

        dmg = max(1, self.creature_damage - int(target.true_defense * 0.2))
        if target.curses["exposed"] > 0 or target.curses["suspended"] == -1: dmg *= 2

        target.health -= dmg
        self.active_p = target
        self.dramatic_prompt(f"{target.name} took {dmg} damage!", color=RED, shake=True)

    def combat_loop(self):
        while any(p.health > 0 for p in self.players) and self.creature_health > 0:
            for p in self.players:
                if p.curses.get("burn", 0) > 0:
                    self.creature_health -= 15
                    self.log_event("Enemy burns from Hellfire! -15 HP.")
                    p.curses["burn"] -= 1

            if self.creature_health <= 0: break

            for idx, p in enumerate(self.players):
                if p.health <= 0 or self.creature_health <= 0: continue
                self.active_p = p
                p.stamina = min(p.max_stamina, p.stamina + 20) 
                self.process_player_turn(p)

            if self.creature_health <= 0: break

            self.enemy_intent = random.choice(["agile", "brutal", "guard"])
            self.run_enemy_turn()

        if all(p.health <= 0 for p in self.players): return False

        w = random.randint(80, 150) if self.is_boss else random.randint(20, 50)
        self.party_gold += w

        for p in self.players:
            if p.health > 0:
                p.exp += int(random.uniform(50, 100) * self.creature_level)
                if p.exp >= p.exp_needed:
                    p.level += 1
                    p.exp -= p.exp_needed
                    p.exp_needed = int(p.exp_needed * 1.5)
                    p.max_health += 10; p.max_mana += 5; p.health = p.max_health; p.mana = p.max_mana

            if p.user_class == "5":
                p.resonance_meter = max(0, p.resonance_meter - 20)
                p.lucidity = min(100, p.lucidity + 30)
                p.curses["halo_fracture"] = 0
                p.curses["rampage"] = 0

        self.dramatic_prompt(f"VICTORY! Party gains {w} Gold.", color=GREEN)
        return True

    def shop(self):
        for p in self.players: 
            if p.health > 0: p.health = p.max_health; p.mana = p.max_mana; p.stamina = p.max_stamina

        self.dramatic_prompt("Respite at a merchant. Party healed.", color=CYAN)

        pool = ["Skip Potion", "Extra Damage Potion", "Extra Protection Potion", "Bolt Cutters"]
        random.shuffle(pool)
        special_1 = pool[0]; special_2 = pool[1]

        hp_p = random.randint(25, 60); mp_p = random.randint(35, 75)
        vent_p = random.randint(60, 140); halo_p = random.randint(80, 180)
        sp_price1 = random.randint(80, 150); sp_price2 = random.randint(80, 150)
        cut_p = random.randint(100, 200)

        while True:
            menu = f"  MERCHANT OUTPOST - Party Gold: {int(self.party_gold)}\n"
            menu += f"  [1] Health Potion ({hp_p}g)\n  [2] Mana Potion ({mp_p}g)\n"
            menu += f"  [3] {special_1} ({sp_price1}g)\n  [4] {special_2} ({sp_price2}g)\n"

            angel_in_party = any(p.user_class == "5" for p in self.players)
            if angel_in_party:
                menu += f"  [{MAGENTA}5{RESET}] Resonance Vent ({vent_p}g)\n  [{CYAN}6{RESET}] Halo Reset ({halo_p}g)\n"
                if "Bolt Cutters" not in [special_1, special_2]:
                    menu += f"  [{RED}7{RESET}] Bolt Cutters ({cut_p}g) - Breaks 1 PERM Restraint\n"

            menu += "  [0] Proceed\n"
            self.draw(menu)
            c = self.get_input()

            if c == "1" and self.party_gold >= hp_p: self.party_gold -= hp_p; self.inv["Health Potion"] += 1; self.dramatic_prompt("Bought Health Potion.", color=GREEN)
            elif c == "2" and self.party_gold >= mp_p: self.party_gold -= mp_p; self.inv["Mana Potion"] += 1; self.dramatic_prompt("Bought Mana Potion.", color=BLUE)
            elif c == "3" and self.party_gold >= sp_price1: self.party_gold -= sp_price1; self.inv[special_1] += 1; self.dramatic_prompt(f"Bought {special_1}.", color=CYAN)
            elif c == "4" and self.party_gold >= sp_price2: self.party_gold -= sp_price2; self.inv[special_2] += 1; self.dramatic_prompt(f"Bought {special_2}.", color=CYAN)
            elif c == "5" and angel_in_party and self.party_gold >= vent_p: self.party_gold -= vent_p; self.inv["Resonance Vent"] += 1; self.dramatic_prompt("Bought Vent.", color=MAGENTA)
            elif c == "6" and angel_in_party and self.party_gold >= halo_p: self.party_gold -= halo_p; self.inv["Halo Reset"] += 1; self.dramatic_prompt("Bought Halo Reset.", color=CYAN)
            elif c == "7" and angel_in_party and self.party_gold >= cut_p and "Bolt Cutters" not in [special_1, special_2]: self.party_gold -= cut_p; self.inv["Bolt Cutters"] += 1; self.dramatic_prompt("Bought Cutters.", color=MAGENTA)
            elif c == "0": break
            else: self.dramatic_prompt("Invalid choice or insufficient funds.", color=RED)

    def print_angel_lore(self):
        lore = f"""
{MAGENTA}======================================================================{RESET}
{CYAN}                         THE PRIME EVIL                               {RESET}
{MAGENTA}======================================================================{RESET}

You were cast out. Stripped of your grace, your body is now a 
canvas for divine punishment. 

{RED}[ THE MECHANICS OF AGONY ]{RESET}
* {YELLOW}VISCERAL BONDAGE{RESET}: Chains don't just reduce stats. They physically stop
  you. Bound Hands force typing QTEs. Gags force swallowing QTEs.
  Sensory Deprivation hides the UI.
* {YELLOW}THE CURSE DUMP{RESET}: Every turn, the abyss throws heavy iron restraints onto 
  your body. THEY ARE PERMANENT UNTIL BROKEN.
* {YELLOW}MARTYRDOM{RESET}: Below 30% HP, your damage doubles.
* {YELLOW}LUCIDITY{RESET}: The pain drives you mad. If Lucidity hits 0%, you enter Bloodlust.
* {YELLOW}WRITHE{RESET}: Your only class action is to tear your own skin (-15 HP) to
  forcefully regain stamina and mana to survive.

You are weak. You are bound. You are going to suffer.
        """
        self.init_terminal(); print(lore)
        input(f"\n  {WHITE}[ Press ENTER to accept your Penance ]{RESET}")

    def setup_game(self):
        self.init_terminal()
        print(f"{CYAN}Made by Watery Fox{RESET}\n")

        mode_select = input("Select Mode:\n[1] Solo Campaign\n[2] Local Co-Op (2 Players)\n> ").strip()
        self.mode = 2 if mode_select == "2" else 1

        diff_str = input("\nSelect Difficulty:\n[1] Easy | [2] Normal | [3] Hard | [4] Insane\n> ").strip()
        self.local_dfct = {"1": 0.25, "2": 0.4, "3": 0.75, "4": 1.0}.get(diff_str, 1.0)
        self.difficulty = self.local_dfct * 2
        self.set_difficulty_scaling()

        angel_chosen = False

        for i in range(self.mode):
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{CYAN}--- PLAYER {i+1} CHOOSE DESTINY ---{RESET}\n")
            print("1. Warrior (Rage & Execute)\n2. Tank (Guard x3 DEF)\n3. Rogue (Combo & Assassinate)\n4. Witch (Hellfire Spells)")
            print(f"{RED}5. Fallen Angel (NIGHTMARE DIFFICULTY. INTERACTIVE BDSM. PRIME EVIL.){RESET}\n")

            while True:
                c = input("> ").strip()
                if c in ["1", "2", "3", "4", "5"]: break

            c_map = {"1": "Warrior", "2": "Tank", "3": "Rogue", "4": "Witch", "5": "Fallen Angel"}

            if c == "5":
                self.print_angel_lore()
                angel_chosen = True
                self.inv["Resonance Vent"] += 1
                self.inv["Halo Reset"] += 1

            name = input(f"\nEnter name for {c_map[c]}: ").strip() or f"Player {i+1}"
            self.players.append(Player(name, c, c_map[c]))

        if angel_chosen:
            if self.local_dfct == 0.25:
                self.local_dfct = 0.4; self.set_difficulty_scaling()
                self.story_log.append("There is no 'Easy' for the Fallen. Shifted to MEDIUM.")
            elif self.local_dfct == 0.4:
                self.local_dfct = 0.75; self.set_difficulty_scaling()
                self.story_log.append("The abyss rejects 'Medium'. Shifted to HARD.")
            elif self.local_dfct == 0.75:
                self.local_dfct = 1.0; self.set_difficulty_scaling()
                self.story_log.append("You thought 'Hard' was enough? Shifted to INSANE.")
            self.difficulty = self.local_dfct * 2

        self.active_p = self.players[0]

    def start(self):
        self.setup_game()
        while any(p.health > 0 for p in self.players):
            self.creature_spawn()
            alive = self.combat_loop()
            if not alive: break
            self.shop()

        self.init_terminal()
        print(f"\n{RED}PARTY WIPED. THE ABYSS CONSUMES ALL.{RESET}\n")
        sys.stdout.write(SHOW_CURSOR)
        input(f"\n{WHITE}[ Press ENTER to exit ]{RESET}")
        self.restore_terminal()

if __name__ == "__main__":
    game = LeavelyEngine()
    try: game.start()
    except KeyboardInterrupt: game.restore_terminal(); print("\nGame Terminated.")
