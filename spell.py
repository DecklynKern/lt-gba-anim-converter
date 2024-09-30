from PyQt5.QtGui import QPixmap, QImage, QColor
import os

SCREEN_WIDTH = 240

FOREGROUND_WIDTH = 480
FOREGROUND_HEIGHT = 160

def wait(n):
    return ["wait", [n]]

class Spell:

    def __init__(self, name, globalCommandsOnHit, globalCommandsOnMiss, foregroundUpdates, foregroundUpdatesAfterHit, backgroundUpdates, backgroundUpdatesAfterHit, foregroundImages, backgroundImages, stretchBackground):

        self.name = name

        self.globalCommandsOnHit = globalCommandsOnHit
        self.globalCommandsOnMiss = globalCommandsOnMiss

        self.foregroundUpdates = foregroundUpdates
        self.foregroundUpdatesAfterHit = foregroundUpdatesAfterHit
        self.backgroundUpdates = backgroundUpdates
        self.backgroundUpdatesAfterHit = backgroundUpdatesAfterHit

        self.foregroundImages = foregroundImages
        self.backgroundImages = backgroundImages

        self.stretchBackground = stretchBackground

        self.foregroundPaletteData = {}
        self.backgroundPaletteData = {}

        self.backgroundImageHeight = None

    def addForegroundPaletteColours(self, imagePath):
        
        image = QImage(imagePath)

        for y in range(0, 2):
            for x in range(FOREGROUND_WIDTH - 1, FOREGROUND_WIDTH - 9, -1):

                colour = image.pixelColor(x, y).getRgb()[:3]
                
                if colour not in self.foregroundPaletteData:
                    idx = len(self.foregroundPaletteData)
                    self.foregroundPaletteData[colour] = [idx % 8, int(idx / 8)]

    # not all images have palette in top-right, need to iterate every pixel
    def addBackgroundPaletteColours(self, imagePath):

        image = QImage(imagePath)

        if self.backgroundImageHeight is None:

            self.backgroundImageHeight = image.height()

            if self.backgroundImageHeight < 80:
                self.stretchBackground = True
        
        for x in range(SCREEN_WIDTH):
            for y in range(self.backgroundImageHeight):

                colour = image.pixelColor(x, y).getRgb()[:3]

                if colour not in self.backgroundPaletteData:
                    idx = len(self.backgroundPaletteData)
                    self.backgroundPaletteData[colour] = [idx % 8, int(idx / 8)]

    def calculatePalettes(self, framesPath):

        for foregroundImage in self.foregroundImages:
            self.addForegroundPaletteColours(os.path.join(framesPath, foregroundImage))

        for backgroundImage in self.backgroundImages:
            self.addBackgroundPaletteColours(os.path.join(framesPath, backgroundImage))

    def generateParentEffectJSON(self):

        commandsOnHit = [
            [
                "enemy_effect",
                [
                    "%sFGHit" % self.name
                ],
            ],
            [
                "enemy_under_effect",
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
                "enemy_under_effect",
                [
                    "%sBGMiss" % self.name
                ]
            ]
        ]

        currentFrame = 0

        for (commandFrame, name, parameters) in self.globalCommandsOnHit:

            waitDuration = commandFrame - currentFrame
            currentFrame = commandFrame

            if waitDuration != 0:
                commandsOnHit.append(wait(waitDuration))

            commandsOnHit.append([name, parameters])

        commandsOnHit.append(["end_parent_loop", None])
        commandsOnHit.append(wait(1))

        currentFrame = 0

        for (commandFrame, name, parameters) in self.globalCommandsOnMiss:

            waitDuration = commandFrame - currentFrame
            currentFrame = commandFrame

            if waitDuration != 0:
                commandsOnMiss.append(wait(waitDuration))

            commandsOnMiss.append([name, parameters])

        commandsOnMiss.append(["end_parent_loop", None])
        commandsOnMiss.append(wait(1))
        
        return {
            "nid": self.name,
            "poses": [
                [
                    "Attack",
                    commandsOnHit,
                    "Miss",
                    commandsOnMiss
                ]
            ],
            "frames": [],
            "palettes": []
        }
    
    def convertImagesToFrames(images, height):
        return [
            [
                frameName,
                [n * SCREEN_WIDTH, 0, SCREEN_WIDTH, height],
                [0, 0]
            ]
            for (n, frameName) in enumerate(images.values())
        ]
    
    def generateImageUpdateJSON(self, name, updates, images, height):

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

        commands.insert(0, ["blend", [True]])
        commands.append(wait(1))

        return {
            "nid": name,
            "poses": [
                [
                    "Attack",
                    commands
                ]
            ],
            "frames": Spell.convertImagesToFrames(images, height),
            "palettes": [
                [
                    "Image",
                    "%s_Image" % name
                ]
            ]
        }
    
    def generateForegroundOnHitJSON(self):
        return self.generateImageUpdateJSON(
            self.name + "FGHit",
            self.foregroundUpdates + self.foregroundUpdatesAfterHit,
            self.foregroundImages,
            FOREGROUND_HEIGHT
        )
    
    def generateForegroundOnMissJSON(self):
        return self.generateImageUpdateJSON(
            self.name + "FGMiss",
            self.foregroundUpdates,
            self.foregroundImages,
            FOREGROUND_HEIGHT
        )
    
    def generateBackgroundOnHitJSON(self):
        return self.generateImageUpdateJSON(
            self.name + "BGHit",
            self.backgroundUpdates + self.backgroundUpdatesAfterHit,
            self.backgroundImages,
            self.backgroundImageHeight
        )
    
    def generateBackgroundOnMissJSON(self):
        return self.generateImageUpdateJSON(
            self.name + "BGMiss",
            self.backgroundUpdates,
            self.backgroundImages,
            self.backgroundImageHeight
        )
    
    def generateForegroundOnHitPaletteJSON(self):
        return [
            "%sFGHit_Image" % self.name,
            [[self.foregroundPaletteData[colour], list(colour)] for colour in self.foregroundPaletteData]
        ]
    
    def generateForegroundOnMissPaletteJSON(self):
        return [
            "%sFGMiss_Image" % self.name,
            [[self.foregroundPaletteData[colour], list(colour)] for colour in self.foregroundPaletteData]
        ]
    
    def generateBackgroundOnHitPaletteJSON(self):
        return [
            "%sBGHit_Image" % self.name,
            [[self.backgroundPaletteData[colour], list(colour)] for colour in self.backgroundPaletteData]
        ]
    
    def generateBackgroundOnMissPaletteJSON(self):
        return [
            "%sBGMiss_Image" % self.name,
            [[self.backgroundPaletteData[colour], list(colour)] for colour in self.backgroundPaletteData]
        ]
    
    def getPalettizedSheet(animationPath, images, paletteData, height, offsetX, hasPalette, stretch):

        palettizedHeight = 2 * height if stretch else height
        palettizedSheet = QImage(SCREEN_WIDTH * len(images), palettizedHeight, QImage.Format.Format_RGB32)
        
        for (idx, img) in enumerate(images):
            
            image = QImage(os.path.join(animationPath, img))

            for y in range(height):

                xrange = range(SCREEN_WIDTH) if (not hasPalette or y > 1) else range(SCREEN_WIDTH - 8)

                for x in xrange:
                    
                    colour = image.pixelColor(x + offsetX, y).getRgb()[:-1]
                    [g, b] = paletteData[colour]

                    outputX = SCREEN_WIDTH * idx + (SCREEN_WIDTH - x - 1)
                    outputColour = QColor(0, g, b)

                    if stretch:
                        palettizedSheet.setPixelColor(outputX, 2 * y, outputColour)
                        palettizedSheet.setPixelColor(outputX, 2 * y + 1, outputColour)
    
                    else:
                        palettizedSheet.setPixelColor(outputX, y, outputColour)
        
        return palettizedSheet
    
    def getForegroundSheet(self, animationPath):
        return Spell.getPalettizedSheet(animationPath, self.foregroundImages, self.foregroundPaletteData, FOREGROUND_HEIGHT, 240, True, False)

    def getBackgroundSheet(self, animationPath):
        return Spell.getPalettizedSheet(animationPath, self.backgroundImages, self.backgroundPaletteData, self.backgroundImageHeight, 0, False, self.stretchBackground)