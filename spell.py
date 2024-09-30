from PyQt5.QtGui import QPixmap, QImage, QColor
import os

FOREGROUND_WIDTH = 480
FOREGROUND_HEIGHT = 160

BACKGROUND_WIDTH = 240
BACKGROUND_HEIGHT = 64

def wait(n):
    return ["wait", [n]]

class Spell:

    def __init__(self, name, globalCommands, globalCommandsAfterHit, foregroundUpdates, foregroundUpdatesAfterHit, backgroundUpdates, backgroundUpdatesAfterHit, foregroundImages, backgroundImages):

        self.name = name

        self.globalCommands = globalCommands
        self.globalCommandsAfterHit = globalCommandsAfterHit

        self.foregroundUpdates = foregroundUpdates
        self.foregroundUpdatesAfterHit = foregroundUpdatesAfterHit
        self.backgroundUpdates = backgroundUpdates
        self.backgroundUpdatesAfterHit = backgroundUpdatesAfterHit

        self.foregroundImages = foregroundImages
        self.backgroundImages = backgroundImages

        self.foregroundPaletteData = {}
        self.backgroundPaletteData = {}

    def getPaletteColours(self, imagePath):
        
        paletteColours = []

        image = QImage(imagePath)
        width = image.width()

        for x in range(width - 8, width):
            for y in range(0, 2):
                paletteColours.append(image.pixelColor(x, y).getRgb()[:3])

        return paletteColours

    def calculatePalettes(self, framesPath):

        foregroundColours = self.getPaletteColours(os.path.join(framesPath, list(self.foregroundImages.keys())[0]))
        for (idx, colour) in enumerate(foregroundColours):
            self.foregroundPaletteData[colour] = [idx % 8, int(idx / 8)]

        for backgroundImage in self.backgroundImages:

            for colour in self.getPaletteColours(os.path.join(framesPath, backgroundImage)):

                if colour not in self.backgroundPaletteData:
                    idx = len(self.backgroundPaletteData)
                    self.backgroundPaletteData[colour] = [idx % 8, int(idx / 8)]

    def generateParentEffectJSON(self):

        commandsOnHit = [
            [
                "enemy_effect",
                [
                    "%sFGHit" % self.name
                ],
            ],
            [
                "enemy_effect",
                [
                    "%sBGHit" % self.name
                ]
            ]
        ]

        commandsOnMiss = [
            [
                "enemy_effect",
                [
                    "%sFGMiss" % self.name
                ],
            ],
            [
                "enemy_effect",
                [
                    "%sBGMiss" % self.name
                ]
            ]
        ]

        currentFrame = 0

        for (commandFrame, name, parameters) in self.globalCommands:

            waitDuration = commandFrame - currentFrame
            currentFrame = commandFrame

            if name == "miss_pan":
                commandsOnMiss.append(wait(waitDuration))
                commandsOnMiss.append(["pan", None])
                continue

            if waitDuration != 0:
                commandsOnHit.append(wait(waitDuration))
                commandsOnMiss.append(wait(waitDuration))

            commandsOnHit.append([name, parameters])
            commandsOnMiss.append([name, parameters])

        currentFrame = 0

        for (commandFrame, name, parameters) in self.globalCommandsAfterHit:

            waitDuration = commandFrame - currentFrame
            currentFrame = commandFrame

            if waitDuration != 0:
                commandsOnHit.append(wait(waitDuration))

            commandsOnHit.append([name, parameters])

        commandsOnHit.append(["end_parent_loop", None])
        commandsOnMiss.append(["end_parent_loop", None])

        commandsOnHit.append(wait(1))
        commandsOnMiss.append(wait(1))
        
        return {
            "nid": self.name,
            "poses": [
                "Attack",
                commandsOnHit,
                "Miss",
                commandsOnMiss
            ],
            "frames": [],
            "palettes": []
        }
    
    def convertImagesToFrames(images, width, height):
        return [
            [
                frameName,
                [n * width, 0, width, height],
                [0, 0]
            ]
            for (n, frameName) in enumerate(images.values())
        ]
    
    def generateImageUpdateJSON(self, name, type, updates, images, width, height):

        commands = [
            [
                "frame",
                [
                    waitFrames,
                    images[newImage]
                ]
            ]
            for (newImage, waitFrames) in updates
        ]

        commands.append(wait(1))

        return {
            "nid": name + type,
            "poses": [
                "Attack",
                commands
            ],
            "frames": Spell.convertImagesToFrames(images, width, height),
            "palettes": [
                [
                    "Image",
                    "%s_Image" % name
                ]
            ]
        }
    
    def generateForegroundOnHitJSON(self):
        return self.generateImageUpdateJSON(
            self.name + "FG",
            "Hit",
            self.foregroundUpdates + self.foregroundUpdatesAfterHit,
            self.foregroundImages,
            FOREGROUND_WIDTH,
            FOREGROUND_HEIGHT
        )
    
    def generateForegroundOnMissJSON(self):
        return self.generateImageUpdateJSON(
            self.name + "FG",
            "Miss",
            self.foregroundUpdates,
            self.foregroundImages,
            FOREGROUND_WIDTH,
            FOREGROUND_HEIGHT
        )
    
    def generateBackgroundOnHitJSON(self):
        return self.generateImageUpdateJSON(
            self.name + "BG",
            "Hit",
            self.backgroundUpdates + self.backgroundUpdatesAfterHit,
            self.backgroundImages,
            BACKGROUND_WIDTH,
            BACKGROUND_HEIGHT
        )
    
    def generateBackgroundOnMissJSON(self):
        return self.generateImageUpdateJSON(
            self.name + "BG",
            "Miss",
            self.backgroundUpdates,
            self.backgroundImages,
            BACKGROUND_WIDTH,
            BACKGROUND_HEIGHT
        )
    
    def generateForegroundPaletteJSON(self):
        return [
            "%sFG_Image" % self.name,
            [[self.foregroundPaletteData[colour], list(colour)] for colour in self.foregroundPaletteData]
        ]
    
    def generateBackgroundPaletteJSON(self):
        return [
            "%sBG_Image" % self.name,
            [[self.backgroundPaletteData[colour], list(colour)] for colour in self.backgroundPaletteData]
        ]
    
    def getPalettizedSheet(animationPath, images, paletteData, width, height):

        palettizedSheet = QImage(width * len(images), height, QImage.Format.Format_RGB32)
        
        for (idx, image) in enumerate(images):
            
            image = QImage(os.path.join(animationPath, image))

            for x in range(0, width):
                for y in range(0, height):
                    colour = image.pixelColor(x, y).getRgb()[:-1]
                    [g, b] = paletteData[colour]
                    palettizedSheet.setPixelColor(width * idx + x, y, QColor(0, g, b))
        
        return palettizedSheet
    
    def getForegroundSheet(self, animationPath):
        return Spell.getPalettizedSheet(animationPath, self.foregroundImages, self.foregroundPaletteData, FOREGROUND_WIDTH, FOREGROUND_HEIGHT)

    def getBackgroundSheet(self, animationPath):
        return Spell.getPalettizedSheet(animationPath, self.backgroundImages, self.backgroundPaletteData, BACKGROUND_WIDTH, BACKGROUND_HEIGHT)