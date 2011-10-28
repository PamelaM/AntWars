#/usr/bin/env python
import sys
import os, pygame,math
from pygame.locals import *


# TODOS:
# Re-size the game window based on MAP_WIDTH and MAP_HEIGHT
# Add Status windows - showing how many ants each player has in their pools
# Add ability to save the game
# Refactor into AntWarsGame, HexMap, Hex, Player classes
# Add ability to choose size of ants-per-click
# Add ComputerPlayer class

NO_OWNER = 0
PLAYER_1_OWNER = 1
PLAYER_2_OWNER = 2
OWNER_COLORS = [(0xff, 0xff, 0xff), (0x00, 0xE0, 0x00), (0xE0, 0x00, 0x00)]


MAP_WIDTH = 16
MAP_HEIGHT = 15
if sys.argv[1:]:
    MAP_WIDTH, MAP_HEIGHT = map(int, sys.argv[1:])

INITIAL_POOL_SIZE = 5

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

SIDEBAR_PIXEL_WIDTH = 80
SIDEBAR_PIXEL_MIN_HEIGHT = 80


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
            
    def drawHex(self, x, y):
        # Get the top left location of the tile.
        pixelX,pixelY = self.hexMapToPixel(x,y)

        # Blit the tile to the map image.
        self.mapimg.blit(self.tile,(pixelX,pixelY))

        # Show the hexagon map location in the center of the tile.
        hexOwner, hexVal = self.hexes[x][y]
        color = OWNER_COLORS[hexOwner]
        location = self.fnt.render("%d" % hexVal, 0, color)
        lrect=location.get_rect()
        lrect.center = (pixelX+(TILE_WIDTH/2),pixelY+(TILE_HEIGHT/2))                
        self.mapimg.blit(location,lrect.topleft)

    def get_map_pixel_size(self):
        map_pixel_width = (MAP_WIDTH*TILE_WIDTH)+ODD_ROW_X_MOD+(BORDER_SIZE*2)
        map_pixel_height = (MAP_HEIGHT*ROW_HEIGHT)+ODD_ROW_X_MOD+(BORDER_SIZE*2)
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
        self.fnt = pygame.font.Font(pygame.font.get_default_font(),12)

        map_pixel_width, map_pixel_height = self.get_map_pixel_size()
        self.mapimg = pygame.Surface((map_pixel_width,map_pixel_height),1).convert()
        self.mapimg.fill((104,104,104))
        self.hexes = []
        
        for x in range(MAP_WIDTH):
            self.hexes.append([])
            for y in range(MAP_HEIGHT):
                self.hexes[x].append([NO_OWNER,0])
                self.drawHex(x,y)

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
        location = self.fnt.render(self.game_state, 0, (0,0,0))
        self.sidebarimg.blit(location,(2,2))

        # current player
        color = OWNER_COLORS[self.current_player]        
        location = self.fnt.render("Player %s" % self.current_player, 0, color)
        self.sidebarimg.blit(location,(2,20))

        # player 1 pool size
        color = OWNER_COLORS[PLAYER_1_OWNER]        
        location = self.fnt.render("Pool: %4s" % self.player_info[PLAYER_1_OWNER]["pool"], 0, color)
        self.sidebarimg.blit(location,(2,40))

        # player 2 pool size
        color = OWNER_COLORS[PLAYER_2_OWNER]        
        location = self.fnt.render("Pool: %4s" % self.player_info[PLAYER_2_OWNER]["pool"], 0, color)
        self.sidebarimg.blit(location,(2,60))
                        
    def loadTiles(self):
        """
        Load the tile and the cursor.
        """
        self.tile = pygame.image.load("./hextile.png").convert()
        self.tile.set_colorkey((0x80, 0x00, 0x80), RLEACCEL)                

        self.up_cursor = pygame.image.load("./hexcursor.png").convert()
        self.up_cursor.set_colorkey((0x80, 0x00, 0x80), RLEACCEL)                        
        self.cursorPos = self.up_cursor.get_rect()
        self.cursor = self.up_cursor
        
        self.down_cursor = pygame.image.load("./hexcursor_down.png").convert()
        self.down_cursor.set_colorkey((0x80, 0x00, 0x80), RLEACCEL)                        
        assert(self.down_cursor.get_rect()==self.up_cursor.get_rect())

        self.player_1_tile = pygame.image.load("./p1_tile.png").convert()
        self.player_1_tile.set_colorkey((0x80, 0x00, 0x80), RLEACCEL)                        

        self.player_2_tile = pygame.image.load("./hexcursor.png").convert()
        self.player_2_tile.set_colorkey((0x80, 0x00, 0x80), RLEACCEL)                        

    def init(self):

        self.game_state = "CHOOSING"
        self.current_player = PLAYER_1_OWNER
        self.player_info = {}
        self.player_info[PLAYER_1_OWNER] = {"pool":0}
        self.player_info[PLAYER_2_OWNER] = {"pool":0}
        self.click_num = 0
        self.click_player = PLAYER_1_OWNER
        self.click_state = "CHOOSING"
        self.click_actions = []
        self.transition_actions = []

        """
        Setup the screen etc.
        """
        map_pixel_width, map_pixel_height = self.get_map_pixel_size()
        sidebar_pixel_width, sidebar_pixel_height = self.get_sidebar_pixel_size()
        
        self.screen = pygame.display.set_mode((map_pixel_width+sidebar_pixel_width, max(map_pixel_height, sidebar_pixel_height)),1)
        pygame.display.set_caption('Press SPACE to toggle the gridRect display')
        self.cursor_visible = False    
        self.loadTiles()
        self.drawMap()        
        self.drawSidebar() 
        self.sidebar_x_location = map_pixel_width

        self.gridRect = pygame.Rect(0,0,GRID_WIDTH,GRID_HEIGHT)

    def logClickAction(self, action):
        self.click_actions.append(action)

    def logTransitionAction(self, action):
        self.transition_actions.append(action)
        
    def logClick(self, x, y):
        self.click_num += 1
        click_num = self.click_num
        start_state = self.click_state
        start_pid = self.click_player
        curr_state = self.game_state
        curr_pid = self.current_player
        xy = "(%s,%s)" % (x, y)

        click_actions = ", ".join(self.click_actions)
        transition_actions = ", ".join(self.transition_actions)

        print "[%(click_num)3s] %(xy)7s : ACTION: %(start_state)s, P%(start_pid)s - %(click_actions)s" % locals(),
        if transition_actions:
            print "; TRANSITION: %(transition_actions)s" % locals(),
        print
        
        
        self.click_actions = []
        self.transition_actions = []
        self.click_player = self.current_player
        self.click_state = self.game_state

    def setCursor(self,x,y):
        """
        Set the hexagon map cursor.
        """
        mapX,mapY = self.pixelToHexMap(x,y)
        self.cursor_visible = mapX<MAP_WIDTH and mapY<MAP_HEIGHT   
        pixelX,pixelY = self.hexMapToPixel(mapX,mapY)        
        self.cursorPos.topleft = (pixelX,pixelY)

    def handleChoosingClick(self, mapX, mapY):
        if self.hexes[mapX][mapY][0]!=NO_OWNER:
            self.logClickAction("ALREADY OWNED")
            return
        self.logClickAction("NEW OWNER")
            
        self.hexes[mapX][mapY][0] = self.current_player
        self.hexes[mapX][mapY][1] = 1
        self.drawHex(mapX,mapY)
        
        num_not_owned = 0
        for row in self.hexes:
            for hex in row:
                if hex[0]==NO_OWNER:
                    num_not_owned += 1
        
        if num_not_owned==0:
            self.game_state = "PLACING"
            self.current_player = PLAYER_1_OWNER
            self.player_info[PLAYER_1_OWNER]['pool'] = INITIAL_POOL_SIZE
            self.player_info[PLAYER_2_OWNER]['pool'] = INITIAL_POOL_SIZE
            self.logTransitionAction("START PLACING")
        else:
            if self.current_player == PLAYER_1_OWNER:
                self.current_player = PLAYER_2_OWNER
            else:
                self.current_player = PLAYER_1_OWNER
            self.logTransitionAction("CHANGE PLAYER to %s" % self.current_player)
            
    def handlePlacingClick(self, mapX, mapY):
        if self.hexes[mapX][mapY][0]!=self.current_player:
            self.logClickAction("OTHER PLAYER OWNED")
            return

        self.hexes[mapX][mapY][1] += 1
        self.drawHex(mapX,mapY)
        self.logClickAction("Bump Hex to %s" % self.hexes[mapX][mapY][1])
        self.player_info[self.current_player]['pool'] -= 1
        self.logClickAction("Reduce pool to %s" % self.player_info[self.current_player]['pool'])

        if self.player_info[PLAYER_1_OWNER]['pool']==0 and \
           self.player_info[PLAYER_2_OWNER]['pool']==0:
            self.game_state = "PLAYING"
            self.current_player = PLAYER_1_OWNER
            self.logTransitionAction("START PLAYING")
        else:
            if self.current_player==PLAYER_1_OWNER and \
               self.player_info[PLAYER_2_OWNER]['pool']!=0:
                self.current_player = PLAYER_2_OWNER
                self.logTransitionAction("CHANGE PLAYER to %s" % self.current_player)
            elif self.current_player==PLAYER_2_OWNER and \
               self.player_info[PLAYER_1_OWNER]['pool']!=0:
                self.current_player = PLAYER_1_OWNER        
                self.logTransitionAction("CHANGE PLAYER to %s" % self.current_player)
                
    def mainLoop(self):    
        pygame.init()    

        self.init()

        clock = pygame.time.Clock()
                        
        while 1:
            clock.tick(30)
                                                                         
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        return                
                
                elif event.type == MOUSEMOTION:
                    self.setCursor(event.pos[0],event.pos[1])

                elif event.type == MOUSEBUTTONDOWN:
                    self.mouse_down_location = self.pixelToHexMap(event.pos[0],event.pos[1])

                elif event.type == MOUSEBUTTONUP:
                    mapX,mapY = mouse_up_location = self.pixelToHexMap(event.pos[0],event.pos[1])
                    
                    if mapX>=MAP_WIDTH or mapY>=MAP_HEIGHT:   
                        self.logClickAction("OUT-OF-AREA")

                    elif self.game_state=='CHOOSING':
                        self.handleChoosingClick(mapX, mapY)
                            
                    elif self.game_state=='PLACING':
                        self.handlePlacingClick(mapX, mapY)

                    elif self.game_state=='PLAYING':
                        self.logClickAction("NO-PLAYING-YET")
                    
                    else:
                        self.logClickAction("UNKNOWN STATE")
                    

                    self.logClick(mapX, mapY)
                    self.cursor = self.up_cursor
                    self.update_sidebar()
                    
            # DRAWING             
            self.screen.blit(self.mapimg, (0, 0))
            if self.cursor_visible:
                self.screen.blit(self.cursor,self.cursorPos)                        
            self.screen.blit(self.sidebarimg, (self.sidebar_x_location, 0))

            pygame.display.flip()
            
def main():
    g = HexagonExample()
    g.mainLoop()

 
#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
