from spell import *

class Parser:

    globalCommandsOnHit = []
    globalCommandsOnMiss = []
    
    foregroundUpdates = []
    foregroundUpdatesAfterHit = []
    backgroundUpdates = []
    backgroundUpdatesAfterHit = []

    foregroundImages = {}
    backgroundImages = {}

    currentForeground = None
    currentBackground = None

    stretch = False

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

    def updateForeground(self, newForeground, waitFrames):

        self.currentForeground = newForeground

        if newForeground not in self.foregroundImages:
            self.foregroundImages[newForeground] = "%sFG%d" % (self.spellName, len(self.foregroundImages))

        if self.foundMissTerminator:
            self.foregroundUpdatesAfterHit.append((newForeground, waitFrames))

        else:
            self.foregroundUpdates.append((newForeground, waitFrames))

    def updateBackground(self, newBackground, waitFrames):

        self.currentBackground = newBackground

        if newBackground not in self.backgroundImages:
            self.backgroundImages[newBackground] = "%sBG%d" % (self.spellName, len(self.backgroundImages))

        if self.foundMissTerminator:
            self.backgroundUpdatesAfterHit.append((newBackground, waitFrames))

        else:
            self.backgroundUpdates.append((newBackground, waitFrames))

    def tryUpdateDisplay(self, newForeground, newBackground, waitFrames):
        
        if newForeground != self.currentBackground:
            self.updateForeground(newForeground, waitFrames)

        if newBackground != self.currentBackground:
            self.updateBackground(newBackground, waitFrames)

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
                                self.addGlobalCommand("sound", [str(arg1 * 256 + arg2)])

                            # 0x49 through 0x52 - passed to attacker's animation

                            # enable screen stretch - assume used for entire animation
                            case 0x53:
                                self.stretch = True

                            # unused
                            case _:
                                pass
                            

                    # update images
                    case "O":
                        
                        foregroundImage = line.split(" ")[-1]
                        backgroundImage = lines.pop().split(" ")[-1]
                        duration = int(lines.pop())

                        self.tryUpdateDisplay(foregroundImage, backgroundImage, duration)
                        self.currentFrame += duration

                    # miss terminator        
                    case "~":

                        if self.hasPanned:
                            self.addGlobalCommandOnMiss("pan")

                        self.foundMissTerminator = True

                    # ???
                    case _:
                        pass

        if self.hasPanned:
            self.addGlobalCommandOnHit("pan")

        return Spell(self.spellName, self.globalCommandsOnHit, self.globalCommandsOnMiss, self.foregroundUpdates, self.foregroundUpdatesAfterHit, self.backgroundUpdates, self.backgroundUpdatesAfterHit, self.foregroundImages, self.backgroundImages, self.stretch)
