#/usr/bin/env python
from __future__ import print_function
import sys
import os
import math
import random
import time
import pygame
from pygame.locals import *
#from pgu import gui

# TODOS:
# Add Menus
# Add ability to save the game
# Add ability to choose size of ants-per-click
# Add ability to terminate phase early...
# Parse options properly (OptionsParse or whatever)
# Move more stuff from the game class into the base GameState class
# High Scores
# Network play
# Add Help
# Improve sidebar with:
#   "done" buttons
#   better looking fonts
#   cleaner layout
# Add Preferences

class Player(object):
    def __init__(self, id, is_computer, color):
        self.id = id
        self.is_computer = is_computer
        self.color = color
        self.pool = 0
        self.batch_size = 1
        self.other_player = None


class HumanPlayer(Player):
    def __init__(self, id, color):
        Player.__init__(self, id, is_computer=False, color=color)

class ComputerPlayer(Player):
    def __init__(self, id, color):
        Player.__init__(self, id, is_computer=True, color=color)
    
PLAYER_CLASSES = {True:ComputerPlayer, False:HumanPlayer}

class Hex(object):
    def __init__(self, x, y, owner, count):
        self.x = x
        self.y = y
        self.owner = owner
        self.count = count
        
none_player = Player(0, False, (0xff, 0xff, 0xff))
player_one = PLAYER_CLASSES["C1" in sys.argv[1:]](1, color=(0x00, 0xB0, 0x00))
player_two = PLAYER_CLASSES["C2" in sys.argv[1:] or "C" in sys.argv[1:]](2, color=(0xB0, 0x00, 0x00))
player_one.other_player = player_two
player_two.other_player = player_one

fr = [int(a[1:]) for a in sys.argv[1:] if a.startswith("F")]
if fr:
    FRAME_RATE = fr[0]
elif player_one.is_computer and player_two.is_computer:
    FRAME_RATE = 30
else:
    FRAME_RATE = 5

quiet = "Q" in sys.argv[1:]

args = [a for a in sys.argv[1:] if not a in ["C","C1","C2", "Q"] and not a.startswith("F")]
MAP_WIDTH = 16
MAP_HEIGHT = 15
if args:
    MAP_WIDTH, MAP_HEIGHT = list(map(int, args))

INITIAL_POOL_SIZE =  (MAP_WIDTH*MAP_HEIGHT)+MAP_WIDTH
INITIAL_PLACING_BATCH_SIZE = 2
INITIAL_PLAYING_BATCH_SIZE = 500
MIN_PER_TURN_BATCH_SIZE = 5
NUM_ATTACKS_PER_TURN = 3

# This is the rectangular size of the hexagon tiles.
TILE_WIDTH = 38
TILE_HEIGHT = 41

# This is the distance in height between two rows.
ROW_HEIGHT = 31

# This value will be applied to all odd rows x value.
ODD_ROW_X_MOD = 19

# This is the size of the square grid that will help us convert pixel locations to hexagon map locations.
GRID_WIDTH = 38
GRID_HEIGHT = 31

BORDER_SIZE = 2

SIDEBAR_PIXEL_WIDTH = 100
SIDEBAR_PIXEL_MIN_HEIGHT = 80


class GameLogger(object):
    # ---- Logging stuff....    
    def __init__(self, game):
        self.game = game

class GameState(object):
    def __init__(self, name, game, is_first=False, change_player=True):
        self.game = game
        self.name = name
        self.is_first = is_first
        
        self.game.log("BEGIN STATE %s" % self.name)
        if is_first:
            self.game.log("************************ FIRST %s STATE *******************************" % self.name)
            self.game.current_player = player_one
            self.game.log("SET PLAYER to %s" % self.game.current_player.id)
        elif change_player:
            self.game.current_player = self.game.current_player.other_player
            self.game.log("**** CHANGE PLAYER TO %s ***" % self.game.current_player.id)


    def handle_map_click(self, hex):
        self.log("MAP CLICK", hex)
        return self
        
    def handle_sidebar_click(self):
        self.log("SIDEBAR CLICK")
        return self
        
    def play_computer_turn(self):
        return self
    
    def check_victory(self):
        pass
        
    def __str__(self):
        return self.name
    
class ChoosingGameState(GameState):
    def __init__(self, game, is_first=False, change_player=True):
        GameState.__init__(self, "CHOOSING", game, is_first, change_player)

    def handle_map_click(self, hex):
        if hex.owner!=none_player:
            self.game.log("ALREADY OWNED", hex)
            return self
            
        hex.owner = self.game.current_player
        hex.count = 1
        self.game.changed_hexes.append(hex)        
        self.game.log("SET NEW OWNER %s" % self.game.current_player.id, hex)

        if not self.game.get_hexes_owned_by(none_player):
            return PlacingGameState(self.game, is_first=True)
        else:
            return ChoosingGameState(self.game)
    
    def play_computer_turn(self):
        avail_hexes = self.game.get_hexes_owned_by(none_player)
        my_hexes = self.game.get_hexes_owned_by(self.game.current_player)
        if len(my_hexes)<4 or len(avail_hexes)==1:
            target_hexes = avail_hexes
        else:
            their_hexes = self.game.get_hexes_owned_by(self.game.current_player.other_player)
    
            target_hexes = []
            for h in avail_hexes:
                adj = self.game.get_adjacent_hexes(h)
                n = len([a for a in adj if a in my_hexes])
                target_hexes.append([n, h])
    
            target_hexes.sort()
            target_hexes.reverse()
            target_hexes = [h for n,h in target_hexes]
            num_targets = len(target_hexes)
            quarter_targets = num_targets/4
            target_hexes = target_hexes[:1+quarter_targets]
        
        hex = random.choice(target_hexes)
        return self.handle_map_click(hex)

class PlacingGameState(GameState):
    def __init__(self, game, is_first=False, change_player=True):
        if is_first:
            player_one.pool = player_two.pool = INITIAL_POOL_SIZE
            player_one.batch_size = player_two.batch_size = INITIAL_PLACING_BATCH_SIZE
        GameState.__init__(self, "PLACING", game, is_first, change_player)
        
    def handle_map_click(self, hex):
        if hex.owner!=self.game.current_player:
            self.game.log("OTHER PLAYER OWNED", hex)
            return self

        self.game.load_hex(hex)        

        if player_one.pool==0 and player_two.pool==0:
            return ReinforcingGameState(self.game, is_first=True)
        elif self.game.current_player.other_player.pool!=0:
            return PlacingGameState(self.game)
        else:
            return self

    def play_computer_turn(self):
        avail_hexes = self.game.get_hexes_owned_by(self.game.current_player)
        safe_hexes = self.game.get_safe_hexes(avail_hexes)
        avail_hexes = [h for h in avail_hexes if not h in safe_hexes]
        hex = random.choice(avail_hexes)
        return self.handle_map_click(hex)

                
class ReinforcingGameState(GameState):
    def __init__(self, game, is_first=False, change_player=True):
        new_turn = False
        if is_first:
            game.turn = 1
            player_one.batch_size = player_two.batch_size = INITIAL_PLAYING_BATCH_SIZE
            new_turn = True
        elif game.current_player == player_one:
            game.turn += 1                    
            new_turn = True
        
        GameState.__init__(self, "REINFORCING", game, change_player)
        if new_turn:
            self.game.log("*********** START TURN %s ****************" % self.game.turn)

        hexes = self.game.get_hexes_owned_by(self.game.current_player)
        safe_hexes = self.game.get_safe_hexes(hexes)
        n = max(MIN_PER_TURN_BATCH_SIZE, len(hexes)+(len(safe_hexes)*2))
        self.game.current_player.pool = n
        self.game.log("Add %s TO POOL, now: %s" % (n, self.game.current_player.pool))

    def handle_map_click(self, hex):
        if hex.owner!=self.game.current_player:
            self.game.log("OTHER PLAYER OWNED", hex)
            return self

        self.game.load_hex(hex)        

        if not self.game.current_player.pool:            
            self.game.log("NO MORE REINFORCEMENTS")
            return AttackingGameState(self.game, change_player=False)
        else:
            return self # Reinforcing state continues until (a) no more in pool or (b) sidebar click


    def handle_sidebar_click(self):
        if not self.game.current_player.is_computer:
            self.game.log("ENDING REINFORCING PHASE")
            return AttackingGameState(self.game)
        else:
            return self

    def play_computer_turn(self):
        my_hexes = self.game.get_hexes_owned_by(self.game.current_player)
        safe_hexes = self.game.get_safe_hexes(my_hexes)
        reinforcing_hexes = [[h in safe_hexes, h.count, h] for h in my_hexes]
        reinforcing_hexes.sort()
        reinforcing_hexes = [h for s,c,h in reinforcing_hexes if self.game.load_hex_amount(h)]
                    
        if reinforcing_hexes:
            hex = random.choice(reinforcing_hexes[:3])
            return self.handle_map_click(hex)
        else:
            self.game.log("NO PLACE TO REINFORCE")
            return AttackingGameState(self.game, change_player=False)

    def check_victory(self):
        if not self.game.get_hexes_owned_by(player_one):
            self.game.winner = player_two
            self.game.is_over = True
            
        elif not self.game.get_hexes_owned_by(player_two):
            self.game.winner = player_one
            self.game.is_over = True

    def __str__(self):
        return "%s  %3s" % (self.name, self.game.turn)
        
class AttackingGameState(GameState):
    def __init__(self, game, is_first=False, change_player=True):
        assert(not is_first)
        game.num_attacks = NUM_ATTACKS_PER_TURN
        GameState.__init__(self, "ATTACKING", game, is_first, change_player)

    def handle_sidebar_click(self):
        if not self.game.current_player.is_computer:
            self.game.log("ENDING ATTACKING PHASE")
            return ReinforcingGameState(self.game, change_player=True)
        else:
            return self
            
    def handle_map_click(self, hex):
        if hex.owner==self.game.current_player:
            self.game.log("NOT OTHER PLAYER OWNED", hex)
            return self
        target_points = hex.count
        attack_points = self.game.get_attack_points(hex, actual_attack=True)
        

        if target_points>attack_points:
            hex.count = target_points-attack_points
            result = "Defender wins"
        elif target_points==attack_points:            
            hex.count = 1
            result = "Defender ties"
        else:
            hex.count = attack_points-target_points
            hex.owner = self.game.current_player
            result = "Attacker wins"
                
        self.game.changed_hexes.append(hex)
        self.game.log("%s -> %s, %s" % (attack_points, target_points, result), hex)
        self.game.num_attacks -= 1            
        self.game.log("%s ATTACKS LEFT" % self.game.num_attacks, hex)
        
        if self.game.num_attacks<=1:
            return ReinforcingGameState(self.game, change_player=False)
        else:
            return self # Attacking state continues until (a) no more attacks or (b) sidebar click

                
    def play_computer_turn(self):
        # Get opposing hexes...
        my_hexes = self.game.get_hexes_owned_by(self.game.current_player)
        target_hexes = []
        their_hexes = self.game.get_hexes_owned_by(self.game.current_player.other_player)
        
        for h in their_hexes:
            attack_points = self.game.get_attack_points(h)
            if attack_points:
                adjacent_hexes = self.game.get_adjacent_hexes(h)
                surroundedness = len([a for a in adjacent_hexes if a in my_hexes])
                defendedness = len([a for a in adjacent_hexes if a in their_hexes])
                successfull = attack_points>h.count
                target_hexes.append([successfull, surroundedness, 6-defendedness, attack_points, h])
            
        target_hexes.sort()
        target_hexes.reverse()
        if target_hexes:
        
            #target_hexes = target_hexes[:3]
            #h = random.choice(target_hexes)
            hex = target_hexes[0][-1]
            return self.handle_map_click(hex)
        else:
            self.game.log("NO ATTACKS AVAILABLE")                
            return ReinforcingGameState(self.game, change_player=False)

    def __str__(self):
        return "%s  %3s" % (self.name, self.game.turn)

        
class AntWarsGame(object):
    def __init__(self):
        self.log_start_time = time.time()
        self.state = None
        self.current_player = none_player
        self.turn = 0
        self.is_over = False
        
        self.state = ChoosingGameState(self, is_first=True)
        
        self.changed_hexes = []
        self.init_hexes()

    def log(self, action, hex=None):
        if quiet:
            return
            
        if self.state:
            state = self.state.name
        else:
            state = None
        pid = "P%s" % self.current_player.id
        turn = "T%s" % self.turn
        if hex:
            xy = "(%s,%s)" % (hex.x, hex.y)
        else:
            xy = "-"
        elapsed = time.time()-self.log_start_time
        print("[%(elapsed)7.2f] %(xy)7s : [ %(state)-12s %(turn)4s  %(pid)s] %(action)s" % locals())
        

    def init_hexes(self):
        self.hexes = []
        self.changed_hexes = []
        
        for x in range(MAP_WIDTH):
            self.hexes.append([])
            for y in range(MAP_HEIGHT):
                h = Hex(x,y,none_player,0)
                self.hexes[x].append(h)
                self.changed_hexes.append(h)


    def handleSidebarClick(self):
        if self.current_player.is_computer:
            self.log("IGNORE SIDEBAR CLICK - COMPUTER PLAYER")
        else:
            self.state = self.state.handle_sidebar_click()

    def handleMapClick(self, mapX, mapY):
        if self.current_player.is_computer:
            self.log("IGNORE MAP CLICK - COMPUTER PLAYER")
            
        elif mapX>=MAP_WIDTH or mapY>=MAP_HEIGHT:   
            self.log("MAP OUT-OF-AREA %s, %s" % (mapX, mapY))
        else:
            hex = self.hexes[mapX][mapY]
            self.state = self.state.handle_map_click(hex)
        

    def play_computer_turn(self):
        if self.current_player.is_computer:
            self.state = self.state.play_computer_turn()


    def load_hex_amount(self, hex):
        n = max(0, min(self.current_player.pool, self.current_player.batch_size, 25, 99-hex.count))
        return n
        
    def load_hex(self, hex):
        n = self.load_hex_amount(hex)
        
        if not n:
            return False            
        else:
            hex.count += n
            self.changed_hexes.append(hex)
            self.log("Bump Hex to %s" % hex.count, hex)
            self.current_player.pool -= n
            self.log("Reduce pool to %s" % self.current_player.pool, hex)
    
    def get_attack_points(self, hex, actual_attack=False):
        attack_points = 0
        for h in self.get_adjacent_hexes(hex):
            if h.owner==self.current_player and h.count>1:
                # TODO: change rules on attack points:
                #   ? 1/2 if wouldn't be safe
                #   ? All but one if would be?
                n = min(h.count/2, self.current_player.batch_size)
                attack_points += n
                if actual_attack:
                    h.count -= n
                    self.changed_hexes.append(h)
        return attack_points                        

    def get_safe_hexes(self, hexes):
        safe_hexes = []
        for h in hexes:
            if self.is_safe_hex(h, hexes):
                safe_hexes.append(h)
        return safe_hexes
        
    def is_safe_hex(self, h, hexes):
        for a in self.get_adjacent_hexes(h):
            if not a in hexes:
                return False
        return True
        

    def check_victory(self):
        self.state.check_victory()

    def get_adjacent_hexes(self, hex):
        x, y = hex.x, hex.y
        adjacent_coords = [(x-1, y),(x+1,y)]
        if x & 1:
            x_offset = -1
        else:
            x_offset = 0
        adjacent_coords.append((x+x_offset, y-1))
        adjacent_coords.append((x+x_offset+1, y-1))
        adjacent_coords.append((x+x_offset, y+1))
        adjacent_coords.append((x+x_offset+1, y+1))
        return [self.hexes[x][y] for x,y in adjacent_coords if x>=0 and x<MAP_WIDTH and y>=0 and y<MAP_HEIGHT]
    
    def get_hexes_owned_by(self, owner):
        hexes = []
        for row in self.hexes:
            for h in row:
                if h.owner==owner:
                    hexes.append(h)
        return hexes
        

# This is the modification tables for the square grid.

a1=(-1,-1)
b1=(0,0)
c1=(0,-1)

gridEvenRows = [
[a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,b1,b1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1],
[a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,b1,b1,b1,b1,b1,b1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1],
[a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1],
[a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1],
[a1,a1,a1,a1,a1,a1,a1,a1,a1,a1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,c1,c1,c1,c1,c1,c1,c1,c1,c1,c1],
[a1,a1,a1,a1,a1,a1,a1,a1,a1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,c1,c1,c1,c1,c1,c1,c1,c1,c1],
[a1,a1,a1,a1,a1,a1,a1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,c1,c1,c1,c1,c1,c1,c1],
[a1,a1,a1,a1,a1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,c1,c1,c1,c1,c1],
[a1,a1,a1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,c1,c1,c1],
[a1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,c1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1],
[b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1,b1]
]

a2=(-1,0)
b2=(0,-1)
c2=(0,0)

gridOddRows = [
[a2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,c2],
[a2,a2,a2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,c2,c2,c2],
[a2,a2,a2,a2,a2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,b2,b2,b2,b2,b2,b2,b2,b2,b2,b2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,b2,b2,b2,b2,b2,b2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,b2,b2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2],
[a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,a2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2,c2]
]
        
class HexagonExample:

    def pixelToHexMap(self,x,y):
        """
        Converts a pixel location to a location on the hexagon map.
        """        
        ox, oy = x,y
        
        # Grid-math is topleft 0,0 based, so remove the border offset
        x -= BORDER_SIZE
        y -= BORDER_SIZE
        
        # Get the square location in our help grid.
        gridX = x/GRID_WIDTH
        gridY = y/GRID_HEIGHT
            
        # Calculate the pixel location within that square
        gridPixelX = x%GRID_WIDTH
        gridPixelY = y%GRID_HEIGHT

        # Update the gridRect to show the correct location in the grid
        self.gridRect.topleft = (gridX*GRID_WIDTH,gridY*GRID_HEIGHT)
       
        # Apply the modifiers to get the correct hexagon map location.
        if gridY&1:
            # Odd rows
            hexMapX=gridX+gridOddRows[gridPixelY][gridPixelX][0]
            hexMapY=gridY+gridOddRows[gridPixelY][gridPixelX][1]
        else:
            # Even rows
            hexMapX=gridX+gridEvenRows[gridPixelY][gridPixelX][0]
            hexMapY=gridY+gridEvenRows[gridPixelY][gridPixelX][1]

        #print(ox, x, gridX, gridPixelX, hexMapX, ':', oy, y, gridY, gridPixelY, hexMapY);sys.stdout.flush()
        return (hexMapX,hexMapY)

    def hexMapToPixel(self,mapX,mapY):
        """
        Returns the top left pixel location of a hexagon map location.
        """
        x = (mapX*TILE_WIDTH)+BORDER_SIZE
        y = (mapY*ROW_HEIGHT)+BORDER_SIZE
        if mapY & 1:
            # Odd rows will be moved to the right.
            x += ODD_ROW_X_MOD

        return x, y

        
    def drawHex(self, hex):
        # Get the top left location of the tile.
        pixelX,pixelY = self.hexMapToPixel(hex.x,hex.y)

        # Blit the tile to the map image.
        self.mapimg.blit(self.tile,(pixelX,pixelY))

        # Show the hexagon map location in the center of the tile.
        location = self.fnt.render("%d" % hex.count, 0, hex.owner.color)
        lrect=location.get_rect()
        lrect.center = (pixelX+(TILE_WIDTH/2),pixelY+(TILE_HEIGHT/2))                
        self.mapimg.blit(location,lrect.topleft)

    def get_map_pixel_size(self):
        map_pixel_width = (MAP_WIDTH*TILE_WIDTH)+ODD_ROW_X_MOD+(BORDER_SIZE*2)
        map_pixel_height = (MAP_HEIGHT*ROW_HEIGHT)+(ODD_ROW_X_MOD/2)+(BORDER_SIZE*2)
        return map_pixel_width, map_pixel_height

    def get_sidebar_pixel_size(self):
        sidebar_pixel_width = SIDEBAR_PIXEL_WIDTH
        map_pixel_width, map_pixel_height = self.get_map_pixel_size()        
        sidebar_pixel_height = max(SIDEBAR_PIXEL_MIN_HEIGHT, map_pixel_height)
        return sidebar_pixel_width, sidebar_pixel_height
        
    def drawMap(self):       
        """
        Draw the tiles.
        """
        self.fnt = pygame.font.SysFont("Times",12, bold=True)

        map_pixel_width, map_pixel_height = self.get_map_pixel_size()
        self.mapimg = pygame.Surface((map_pixel_width,map_pixel_height),1).convert()
        self.mapimg.fill((104,104,104))
        self.draw_changed_hexes()
    
    def draw_changed_hexes(self):
        while self.game.changed_hexes:
            h = self.game.changed_hexes.pop(0)            
            self.drawHex(h)
            

    def drawSidebar(self):       
        """
        Draw the sidebar
        """
        sidebar_pixel_width, sidebar_pixel_height = self.get_sidebar_pixel_size()
        self.sidebarimg = pygame.Surface((sidebar_pixel_width,sidebar_pixel_height),1).convert()
        
        self.update_sidebar()
    
    def update_sidebar(self):
        self.sidebarimg.fill((234,234,234))

        # game_state
        state_str = str(self.game.state)
        location = self.fnt.render(state_str, 0, (0,0,0))
        self.sidebarimg.blit(location,(2,2))

        # current player
        location = self.fnt.render("Player %s" % self.game.current_player.id, 0, self.game.current_player.color)
        self.sidebarimg.blit(location,(2,20))

        # player 1 pool size
        location = self.fnt.render("Pool: %4s [%2s]" % (player_one.pool, len(self.game.get_hexes_owned_by(player_one))), 0, player_one.color)
        self.sidebarimg.blit(location,(2,40))

        # player 2 pool size
        location = self.fnt.render("Pool: %4s [%2s]" % (player_two.pool, len(self.game.get_hexes_owned_by(player_two))), 0, player_two.color)
        self.sidebarimg.blit(location,(2,60))
                        
    def loadTiles(self):
        """
        Load the tile and the cursor.
        """
        self.tile = pygame.image.load("./hextile.png").convert()
        self.tile.set_colorkey((0x80, 0x00, 0x80), RLEACCEL)                

        self.cursor = pygame.image.load("./hexcursor.png").convert()
        self.cursor.set_colorkey((0x80, 0x00, 0x80), RLEACCEL)                        
        self.cursorPos = self.cursor.get_rect()
        

    def init(self):
        pygame.init()    
        
        self.game = AntWarsGame()

        """
        Setup the screen etc.
        """
        map_pixel_width, map_pixel_height = self.get_map_pixel_size()
        sidebar_pixel_width, sidebar_pixel_height = self.get_sidebar_pixel_size()
        
        self.screen = pygame.display.set_mode((map_pixel_width+sidebar_pixel_width, max(map_pixel_height, sidebar_pixel_height)),1)
        pygame.display.set_caption('Ant Wars')
        self.cursor_visible = False    
        self.loadTiles()
        self.drawMap()        
        self.drawSidebar() 
        self.sidebar_x_location = map_pixel_width

        self.gridRect = pygame.Rect(0,0,GRID_WIDTH,GRID_HEIGHT)


    def setCursor(self,x,y):
        """
        Set the hexagon map cursor.
        """
        mapX,mapY = self.pixelToHexMap(x,y)
        self.cursor_visible = mapX in range(MAP_WIDTH) and mapY in range(MAP_HEIGHT)
        pixelX,pixelY = self.hexMapToPixel(mapX,mapY)        
        self.cursorPos.topleft = (pixelX,pixelY)


    def handle_map_mouse_event(self, px, py, event_type):
        if event_type == MOUSEMOTION:
            self.setCursor(px, py)

        elif event_type == MOUSEBUTTONDOWN:
            self.mouse_down_location = self.pixelToHexMap(px, py)

        elif event_type == MOUSEBUTTONUP:
            mapX,mapY = mouse_up_location = self.pixelToHexMap(px, py)
            self.game.handleMapClick(mapX, mapY)
                
    def handle_sidebar_mouse_event(self, px, py, event_type):
        if event_type == MOUSEMOTION:
            self.setCursor(px, py)
            
        elif event_type==MOUSEBUTTONUP:
            self.game.handleSidebarClick()
            self.update_sidebar()


    def update_display(self):
        # DRAWING             
        self.update_sidebar()
        self.draw_changed_hexes()
        self.screen.blit(self.mapimg, (0, 0))
        if self.cursor_visible:
            self.screen.blit(self.cursor,self.cursorPos)                        
        self.screen.blit(self.sidebarimg, (self.sidebar_x_location, 0))

        pygame.display.flip()

    
    def mainLoop(self):    

        self.init()

        clock = pygame.time.Clock()
                        
        while not self.game.is_over:

            self.game.play_computer_turn()

            clock.tick(FRAME_RATE)

            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        return                
                elif event.type in (MOUSEMOTION, MOUSEBUTTONUP, MOUSEBUTTONDOWN):
                    px, py = event.pos[0],event.pos[1]
                    if px<self.sidebar_x_location:
                        self.handle_map_mouse_event(px, py, event.type)
                    else:
                        self.handle_sidebar_mouse_event(px, py, event.type)                    
            
            self.game.check_victory()
            self.update_display()
            
            
        print("Player %s WINS!" % self.game.winner.id)
            
def main():
    g = HexagonExample()
    g.mainLoop()

 
#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
