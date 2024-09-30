from spell import *
from sound import *

class Parser:

    globalCommandsOnHit = []
    globalCommandsOnMiss = []
    
    foregroundUpdates = []
    foregroundUpdatesAfterHit = []
    backgroundUpdates = []
    backgroundUpdatesAfterHit = []

    foregroundImages = {}
    backgroundImages = {}

    currentBrightness = 1

    currentForeground = None
    currentBackground = None

    lastForegroundChange = 0
    lastBackgroundChange = 0

    stretchForeground = False

    currentFrame = 0
    foundMissTerminator = False
    hasPanned = True

    def __init__(self, spellName):
        self.spellName = spellName

    def addGlobalCommandOnHit(self, name, parameters=None):
        self.globalCommandsOnHit.append([self.currentFrame, name, parameters])

    def addGlobalCommandOnMiss(self, name, parameters=None):
        self.globalCommandsOnMiss.append([self.currentFrame, name, parameters])

    def addGlobalCommand(self, name, parameters=None):
        
        self.addGlobalCommandOnHit(name, parameters)

        if not self.foundMissTerminator:
            self.addGlobalCommandOnMiss(name, parameters)

    def endLastForegroundUpdate(self):

        if not self.foundMissTerminator:            
            if len(self.foregroundUpdates) != 0:
                self.foregroundUpdates[-1] = (self.foregroundUpdates[-1], self.currentFrame - self.lastForegroundChange)

        else:
            if len(self.foregroundUpdatesAfterHit) != 0:
                self.foregroundUpdatesAfterHit[-1] = (self.foregroundUpdatesAfterHit[-1], self.currentFrame - self.lastForegroundChange)

        self.lastForegroundChange = self.currentFrame

    def endLastBackgroundUpdate(self):

        if not self.foundMissTerminator:            
            if len(self.backgroundUpdates) != 0:
                self.backgroundUpdates[-1] = (self.backgroundUpdates[-1], self.currentFrame - self.lastBackgroundChange)

        else:
            if len(self.backgroundUpdatesAfterHit) != 0:
                self.backgroundUpdatesAfterHit[-1] = (self.backgroundUpdatesAfterHit[-1], self.currentFrame - self.lastBackgroundChange)

        self.lastBackgroundChange = self.currentFrame

    def updateForeground(self, newForeground):

        self.currentForeground = newForeground
        self.endLastForegroundUpdate()

        if newForeground not in self.foregroundImages:
            self.foregroundImages[newForeground] = "%sFG%d" % (self.spellName, len(self.foregroundImages))

        if self.foundMissTerminator:
            self.foregroundUpdatesAfterHit.append(newForeground)

        else:
            self.foregroundUpdates.append(newForeground)

    def updateBackground(self, newBackground):

        self.currentBackground = newBackground
        self.endLastBackgroundUpdate()

        if newBackground not in self.backgroundImages:
            self.backgroundImages[newBackground] = "%sBG%d" % (self.spellName, len(self.backgroundImages))

        if self.foundMissTerminator:
            self.backgroundUpdatesAfterHit.append(newBackground)

        else:
            self.backgroundUpdates.append(newBackground)

    def tryUpdateDisplay(self, newForeground, newBackground):
        
        if newForeground != self.currentForeground:
            self.updateForeground(newForeground)

        if newBackground != self.currentBackground:
            self.updateBackground(newBackground)

    def parse(self, spellFilePath):

        with open(spellFilePath) as spell_file:

            lines = list(reversed([line.strip() for line in spell_file.readlines()]))

            while len(lines):

                line = lines.pop()

                if line == "":
                    continue

                match line[0]:
                
                    # comment
                    case "#":
                        pass

                    # command
                    case "C":

                        command = line.split(" ")[0]

                        commandNum = int(command[-2:], 16)
                        arg1 = 0
                        arg2 = 0

                        if len(command) > 3:
                            arg2 = int(command[-4:-2], 16)

                            if len(command) > 5:
                                arg1 = int(command[-6:-4], 16)

                        match commandNum:

                            # Attack (becomes critical automatically) with HP stealing
                            case 0x08:
                                pass
                            
                            # 0x14 through 0x28 - passed to attacker's animation;

                            case 0x1F:
                                self.addGlobalCommandOnHit("spell_hit")
                                self.addGlobalCommandOnMiss("miss")

                            # set brightness and opacity levels
                            case 0x29:
        
                                brightness = arg1 / 0x10
                                opacity = 1.0 - (arg2 / 0x10 / 2)

                                # assume if brightness changes, we are changing fully
                                if brightness < self.currentBrightness:
                                    self.currentBrightness = 0
                                    self.addGlobalCommand("darken")

                                elif brightness > self.currentBrightness:
                                    self.currentBrightness = 1
                                    self.addGlobalCommand("lighten")

                            # Sets whether maps 2 and 3 of the GBA screen should be visible.
                            case 0x2A:
                                displayMaps = arg2 != 0

                            # 0x2B through 0x3F - passed to attacker's animation

                            # Scrolls the screen from being centered on the attacker to being centered on the defender.
                            # This should not be used more than once per animation.
                            case 0x40:
                                self.addGlobalCommand("pan")
                                self.hasPanned = True

                            # 0x41 through 0x47 - passed to attacker's animation

                            # Plays sound or music whose ID corresponds to those documented in Music List.txt of the Nightmare module packages.
                            case 0x48:
                                soundID = arg1 * 256 + arg2
                                self.addGlobalCommand("sound", [SOUND_TABLE[soundID]])

                            # 0x49 through 0x52 - passed to attacker's animation

                            # enable screen stretch - assume used for entire animation
                            case 0x53:
                                self.stretchForeground = True

                            # unused
                            case _:
                                pass
                            

                    # update images
                    case "O":
                        
                        backgroundImage = line.split(" ")[-1]
                        foregroundImage = lines.pop().split(" ")[-1]
                        duration = int(lines.pop())

                        self.tryUpdateDisplay(foregroundImage, backgroundImage)
                        self.currentFrame += duration

                    # miss terminator        
                    case "~":

                        if self.hasPanned:
                            self.addGlobalCommandOnMiss("pan")

                        self.foregroundUpdatesAfterHit.append(self.foregroundUpdates[-1])
                        self.backgroundUpdatesAfterHit.append(self.backgroundUpdates[-1])

                        self.endLastForegroundUpdate()
                        self.endLastBackgroundUpdate()

                        self.foundMissTerminator = True

                    # ???
                    case _:
                        pass

        self.endLastForegroundUpdate()
        self.endLastBackgroundUpdate()

        if self.hasPanned:
            self.addGlobalCommandOnHit("pan")

        if self.foregroundUpdatesAfterHit[0][1] == 0:
            self.foregroundUpdatesAfterHit = self.foregroundUpdatesAfterHit[1:]

        if self.backgroundUpdatesAfterHit[0][1] == 0:
            self.backgroundUpdatesAfterHit = self.backgroundUpdatesAfterHit[1:]

        return Spell(self.spellName, self.globalCommandsOnHit, self.globalCommandsOnMiss, self.foregroundUpdates, self.foregroundUpdatesAfterHit, self.backgroundUpdates, self.backgroundUpdatesAfterHit, self.foregroundImages, self.backgroundImages, self.stretchForeground)
