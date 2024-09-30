from parse import *
from spell import *

from PyQt5 import QtGui
import os
import json

spellName = input("spell name: ")
animationPath = input("animation path: ")
outputPath = input("output folder (will be created if it doesn't exist): ")

def dumpJSON(name, data):
    with open(os.path.join(outputPath, name + ".json"), "w") as outputFile:
        json.dump(data, outputFile, indent=4)

def main():

    app = QtGui.QGuiApplication([])

    parser = Parser(spellName)
    spell = parser.parse(os.path.join(animationPath, "Spell.txt"))

    spell.calculatePalettes(animationPath)

    if not os.path.exists(outputPath):
        os.mkdir(outputPath)

    dumpJSON(spell.name + "_effect", spell.generateParentEffectJSON())

    dumpJSON(spell.name + "FGHit_effect", spell.generateForegroundOnHitJSON())
    dumpJSON(spell.name + "FGMiss_effect", spell.generateForegroundOnMissJSON())
    dumpJSON(spell.name + "BGHit_effect", spell.generateBackgroundOnHitJSON())
    dumpJSON(spell.name + "BGMiss_effect", spell.generateBackgroundOnMissJSON())

    dumpJSON(spell.name + "FG_Image_palette", spell.generateForegroundPaletteJSON())
    dumpJSON(spell.name + "BG_Image_palette", spell.generateBackgroundPaletteJSON())

    spell.getForegroundSheet(animationPath).save(os.path.join(outputPath, spell.name + "FG.png"))
    spell.getBackgroundSheet(animationPath).save(os.path.join(outputPath, spell.name + "BG.png"))

if __name__ == "__main__":
    main()
