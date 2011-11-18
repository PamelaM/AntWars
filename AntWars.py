#/usr/bin/env python
import sys
import os
import math
import random
import time
import pygame
from pygame.locals import *
from pgu import gui

# TODOS:
# Add Menus
# Add ability to save the game
# Add ability to choose size of ants-per-click
# Refactor Player into Human Player and ComputerPlayer classes
# Parse options properly
# High Scores
# Network play

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

args = [a for a in sys.argv[1:] if not a in ["C","C1","C2"]]
MAP_WIDTH = 16
MAP_HEIGHT = 15
if args:
    MAP_WIDTH, MAP_HEIGHT = map(int, args)

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



class AntWarsGame(object):
    def __init__(self):
        self.state = "CHOOSING"
        self.turn = 0
        self.is_over = False
        self.current_player = player_one
        if player_one.is_computer and player_two.is_computer:
            self.frame_rate = 60
        else:
            self.frame_rate = 10
        
        self.changed_hexes = []
        self.init_hexes()
        
        self.init_logging()        

    def init_hexes(self):
        self.hexes = []
        self.changed_hexes = []
        
        for x in range(MAP_WIDTH):
            self.hexes.append([])
            for y in range(MAP_HEIGHT):
                h = Hex(x,y,none_player,0)
                self.hexes[x].append(h)
                self.changed_hexes.append(h)


    def handleClick(self, mapX, mapY):
        if self.current_player.is_computer:
            self.logClickAction("COMPUTER PLAYER")
            
        elif mapX>=MAP_WIDTH or mapY>=MAP_HEIGHT:   
            self.logClickAction("OUT-OF-AREA")

        elif self.state=='CHOOSING':
            self.handleChoosingClick(mapX, mapY)
                
        elif self.state=='PLACING':
            self.handlePlacingClick(mapX, mapY)

        elif self.state=='PLAYING':
            self.handlePlayingClick(mapX, mapY)
        
        else:
            self.logClickAction("UNKNOWN STATE")
        

        self.logClick(self.hexes[mapX][mapY])
        
    def handleChoosingClick(self, mapX, mapY):

        h = self.hexes[mapX][mapY]
        
        if h.owner!=none_player:
            self.logClickAction("ALREADY OWNED")
            return
            
        self.logClickAction("NEW OWNER")

                    
        h.owner = self.current_player
        h.count = 1
        self.changed_hexes.append(h)
        
        num_not_owned = 0
        for row in self.hexes:
            for hex in row:
                if hex.owner==none_player:
                    num_not_owned += 1


        if num_not_owned==0:
            self.state = "PLACING"
            self.current_player = self.current_player.other_player
            player_one.pool = player_two.pool = INITIAL_POOL_SIZE
            player_one.batch_size = player_two.batch_size = INITIAL_PLACING_BATCH_SIZE
            self.logTransitionAction("START PLACING")
        else:
            self.change_player()
            

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
            self.logClickAction("Bump Hex to %s" % hex.count)
            self.current_player.pool -= n
            self.logClickAction("Reduce pool to %s" % self.current_player.pool)
    
    def handlePlacingClick(self, mapX, mapY):
        hex = self.hexes[mapX][mapY]
        if hex.owner!=self.current_player:
            self.logClickAction("OTHER PLAYER OWNED")
            return

        self.load_hex(hex)        

        if player_one.pool==0 and player_two.pool==0:
            self.state = "PLAYING"
            self.turn = 1
            self.num_attacks = NUM_ATTACKS_PER_TURN
            if player_one.is_computer and player_two.is_computer:
                self.frame_rate = 40
            else:
                self.frame_rate = 10
            self.current_player = self.current_player.other_player
            player_one.batch_size = player_two.batch_size = INITIAL_PLAYING_BATCH_SIZE            
            self.logTransitionAction("START PLAYING")
        else:
            self.change_player()

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
        
    def handlePlayingClick(self, mapX, mapY):        
        hex = self.hexes[mapX][mapY]
        if hex.owner==self.current_player:
            self.logClickAction("NOT OTHER PLAYER OWNED")
            return

        target_points = hex.count
        attack_points = self.get_attack_points(hex, actual_attack=True)
        

        if target_points>attack_points:
            hex.count = target_points-attack_points
            result = "Defender wins"
        elif target_points==attack_points:            
            hex.count = 1
            result = "Defender ties"
        else:
            hex.count = attack_points-target_points
            hex.owner = self.current_player
            result = "Attacker wins"
                
        self.changed_hexes.append(hex)
        self.logClickAction("%s -> %s, %s" % (attack_points, target_points, result))
        self.num_attacks -= 1            
        if self.num_attacks<=1:
            self.logClickAction("USED ALL ATTACKS")
            self.change_player()
        else:
            self.logClickAction("%s ATTACKS LEFT" % self.num_attacks)
                

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
        
    def change_player(self):  
        next_player = self.current_player.other_player

        if self.can_change_to_player(next_player):
            self.current_player = next_player
            self.logTransitionAction("CHANGE PLAYER to %s" % self.current_player.id)
            if self.state=='PLAYING':
                self.num_attacks = NUM_ATTACKS_PER_TURN
                hexes = self.get_hexes_owned_by(self.current_player)
                safe_hexes = self.get_safe_hexes(hexes)
                n = max(MIN_PER_TURN_BATCH_SIZE, len(hexes)+(len(safe_hexes)*2))
                self.current_player.pool = n
                self.logTransitionAction("Add %s TO POOL" % n)
                if self.current_player == player_one:
                    self.turn += 1                    
                    self.logTransitionAction("START TURN %s" % self.turn)
        else:
            self.logTransitionAction("CAN'T CHANGE PLAYER to %s" % self.current_player.id)
        

    def can_change_to_player(self, next_player):
        if self.current_player==next_player:
            return False
            
        if self.state=='CHOOSING':
            return True

        if self.state=='PLACING':
            return next_player.pool>0
        
        return True
        
    def check_victory(self):
        if self.state!='PLAYING':
            return 
        
        elif not self.get_hexes_owned_by(player_one):
            self.winner = player_two
            self.is_over = True
            
        elif not self.get_hexes_owned_by(player_two):
            self.winner = player_one
            self.is_over = True

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

    # ---- Logging stuff....    
    def init_logging(self):
        # Logging s
        self.click_num = 0
        self.click_player = player_one
        self.click_state = "CHOOSING"
        self.click_actions = []
        self.transition_actions = []
        self.log_start_time = time.time()
        
    def logClickAction(self, action):
        self.click_actions.append(action)

    def logTransitionAction(self, action):
        self.transition_actions.append(action)
        
    def logClick(self, hex):
        self.click_num += 1
        click_num = self.click_num
        start_state = self.click_state
        start_pid = self.click_player.id
        curr_state = self.state
        curr_pid = self.current_player.id
        xy = "(%s,%s)" % (hex.x, hex.y)
        elapsed = time.time()-self.log_start_time
        click_actions = ", ".join(self.click_actions)
        transition_actions = ", ".join(self.transition_actions)

        print "[%(click_num)3s %(elapsed)7.2f] %(xy)7s : ACTION: %(start_state)s, P%(start_pid)s - %(click_actions)s" % locals(),
        if transition_actions:
            print "; TRANSITION: %(transition_actions)s" % locals(),
        print        
        
        self.click_actions = []
        self.transition_actions = []
        self.click_player = self.current_player
        self.click_state = self.state
    
    def get_hexes_owned_by(self, owner):
        hexes = []
        for row in self.hexes:
            for h in row:
                if h.owner==owner:
                    hexes.append(h)
        return hexes
        
    def play_computer_turn(self):
        if self.current_player.is_computer:
            if self.state=='CHOOSING':
                self.play_computer_choosing()
            elif self.state=='PLACING':
                self.play_computer_placing()
            else:
                self.play_computer_playing()

    
    def play_computer_choosing(self):
        avail_hexes = self.get_hexes_owned_by(none_player)
        my_hexes = self.get_hexes_owned_by(self.current_player)
        if len(my_hexes)<4 or len(avail_hexes)==1:
            target_hexes = avail_hexes
        else:
            their_hexes = self.get_hexes_owned_by(self.current_player.other_player)
    
            target_hexes = []
            for h in avail_hexes:
                adj = self.get_adjacent_hexes(h)
                n = len([a for a in adj if a in my_hexes])
                target_hexes.append([n, h])
    
            target_hexes.sort()
            target_hexes.reverse()
            target_hexes = [h for n,h in target_hexes]
            num_targets = len(target_hexes)
            quarter_targets = num_targets/4
            target_hexes = target_hexes[:1+quarter_targets]
        
        h = random.choice(target_hexes)
        self.handleChoosingClick(h.x,h.y)                
        self.logClick(h)

    def play_computer_placing(self):
        avail_hexes = self.get_hexes_owned_by(self.current_player)
        safe_hexes = self.get_safe_hexes(avail_hexes)
        avail_hexes = [h for h in avail_hexes if not h in safe_hexes]
        h = random.choice(avail_hexes)
        self.handlePlacingClick(h.x,h.y)                
        self.logClick(h)

    def play_computer_playing(self):
        my_hexes = self.get_hexes_owned_by(self.current_player)
        if self.current_player.pool:
            safe_hexes = self.get_safe_hexes(my_hexes)
            reinforcing_hexes = [[h in safe_hexes, h.count, h] for h in my_hexes]
            reinforcing_hexes.sort()
            reinforcing_hexes = [h for s,c,h in reinforcing_hexes if self.load_hex_amount(h)]
                        
            if not reinforcing_hexes:
                self.logClickAction("NO REINFORCEMENTS AVAILABLE")
                self.current_player.pool = 0
            else:
                h = random.choice(reinforcing_hexes[:3])
                self.load_hex(h)
                
        else:            
            # Get opposing hexes...
            target_hexes = []
            their_hexes = self.get_hexes_owned_by(self.current_player.other_player)
            
            for h in their_hexes:
                attack_points = self.get_attack_points(h)
                if attack_points:
                    adjacent_hexes = self.get_adjacent_hexes(h)
                    surroundedness = len([a for a in adjacent_hexes if a in my_hexes])
                    defendedness = len([a for a in adjacent_hexes if a in their_hexes])
                    successfull = attack_points>h.count
                    target_hexes.append([successfull, surroundedness, 6-defendedness, attack_points, h])
                
            target_hexes.sort()
            target_hexes.reverse()
            if target_hexes:
            
                #target_hexes = target_hexes[:3]
                #h = random.choice(target_hexes)
                h = target_hexes[0][-1]
                self.handlePlayingClick(h.x, h.y)
            else:
                self.logClickAction("NO ATTACKS AVAILABLE")                
                self.change_player()
                
        self.logClick(h)
            

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

        print ox, x, gridX, gridPixelX, hexMapX, ':', oy, y, gridY, gridPixelY, hexMapY;sys.stdout.flush()
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
        if self.game.state == 'PLAYING':
            state_str = "PLAYING  %3s" % (self.game.turn)
        else:
            state_str = self.game.state
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
            self.game.handleClick(mapX, mapY)
                
    def handle_sidebar_mouse_event(self, px, py, event_type):
        if event_type == MOUSEMOTION:
            self.setCursor(px, py)
            
        elif event_type==MOUSEBUTTONUP:
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

            clock.tick(self.game.frame_rate)

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
            
            
        print "Player %s WINS!" % self.game.winner.id
            
def main():
    g = HexagonExample()
    g.mainLoop()

 
#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
