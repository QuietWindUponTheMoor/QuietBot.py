from Fun.Cards.Cards import Standard52CardDeck
import random

class Standard52CardDeckRandDraw:
    def __init__(self):
        self.random = random.choice(Standard52CardDeck().deck)