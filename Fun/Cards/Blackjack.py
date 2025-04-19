import discord
from discord.ext import commands
from discord.ui import Button, View
from Fun.Cards.Cards import Standard52CardDeck
import random
from Utils.CardFile import CardFile
from Utils.Embeds import createEmbed

""" NOTES:

1. If the player stands:
    A) If the dealer hand (upcard + hole card) is greater than 16, the dealer must stand
    B) If the dealer hand (upcard + hole card) is equal to or less than 16, the dealer must draw cards until they have more than a cumulative 16
    C) If the dealer is required to hit, and they bust, the player wins
    D) If the dealer's value is over the player's value but under 21, the dealer wins
    E) If the dealer's value is under the players value and under 21, the player wins

"""

class Blackjack:

    def __init__(self, bot):
        self.bot = bot
        self.interaction = None

        # Values
        self.player = {
            "value": 0,
            "cards": [],
        }
        self.dealer = {
            "value": 0,
            "cards": [],
        }
        self.holeCardName = ""
        self.holeCardFile = None

    # "Private" methods
    async def resetGame(self):
        self.interaction = None

        # Values
        self.player = {
            "value": 0,
            "cards": [],
        }
        self.dealer = {
            "value": 0,
            "cards": [],
        }
        self.holeCardName = ""
        self.holeCardFile = None

    async def aceCheck(self, cardValue):
        if isinstance(cardValue, tuple):
            if (self.player["value"] + 11) > 21:
                return 1
            elif (self.player["value"] + 11) <= 21:
                return 11
        else:
            return cardValue
        
    async def initialDraw(self):
        # Player
        await self.playerDraw() # First card
        await self.playerDraw() # Second card
        cards = self.player["cards"]
        card1Name = cards[0][0]
        card2Name = cards[1][0]
        card1 = await CardFile((cards[0][0], cards[0][1]), fileName="playercard1")
        card2 = await CardFile((cards[1][0], cards[1][1]), fileName="playercard2")

        # Dealer
        await self.dealerDraw() # Upcard
        cards = self.dealer["cards"]
        card3Name = cards[0][0]
        card3 = await CardFile((cards[0][0], cards[0][1]), fileName="dealercard1")
        dealerCurrentValue = self.dealer["value"]

        # Get the hole card data
        await self.dealerDraw() # Hole Card
        dealerCards = self.dealer["cards"]
        self.holeCardName = dealerCards[1][0]
        self.holeCardFile = await CardFile((dealerCards[1][0], dealerCards[1][1]), fileName="dealercard2")

        # Check if game is blackjack condition
        if await self.isBlackjackPushGame():
            await self.blackjackPush([card1, card2, card3, self.holeCardFile])
            return True
        elif await self.isBlackjackPlayerGame():
            await self.blackjackPlayer([card1, card2])
            return True
        elif await self.isBlackjackDealerGame():
            await self.blackjackDealer([card3, self.holeCardFile])
            return True
        else:
            embed = await createEmbed(title="Initial Hands", descr="Here is the initial hand for you and the dealer.", color=discord.Color.green())
            embed.add_field(name="Player Hand:", value=f"{self.player["value"]}", inline=False)
            embed.add_field(name="Player Card 1:", value=card1Name, inline=True)
            embed.add_field(name="Player Card 2:", value=card2Name, inline=True)
            embed.add_field(name="Dealer Hand:", value=f"{dealerCurrentValue} + ?", inline=False)
            embed.add_field(name="Dealer Upcard:", value=card3Name, inline=True)
            await self.interaction.followup.send(embed=embed, files=[card1, card2, card3], ephemeral=False)
            return False

    async def playerDraw(self):
        # Get card for player
        card = await self.drawRandCard()
        p_Card, p_path, p_value = card
        p_value = await self.aceCheck(p_value)
        
        # Add new value and append card
        print(f"p_value = {p_value}")
        self.player["value"] = self.player["value"] + p_value
        self.player["cards"].append(card)

    async def dealerDraw(self):
        # Get card for dealer
        card = await self.drawRandCard()
        comp_Card, comp_path, comp_value = card
        comp_value = await self.aceCheck(comp_value)
        
        # Add new value and append card
        print(f"comp_value = {comp_value}")
        self.dealer["value"] = self.dealer["value"] + comp_value
        self.dealer["cards"].append(card)

    async def isBlackjackPushGame(self):
        if self.player["value"] == 21 and self.dealer["value"] == 21:
            return True
        else:
            return False
        
    async def isBlackjackPlayerGame(self):
        if self.player["value"] == 21 and self.dealer["value"] != 21:
            return True
        else:
            return False
        
    async def isBlackjackDealerGame(self):
        if self.player["value"] != 21 and self.dealer["value"] == 21:
            return True
        else:
            return False

    async def hitOrStand(self, interaction: discord.Interaction):
        embed = await createEmbed(title=f"You now have a hand of {self.player["value"]}", descr="Hit... Or stand?", color=discord.Color.orange())
        hitButton = Button(label="Hit Me!", style=discord.ButtonStyle.green)
        standButton = Button(label="Stand...", style=discord.ButtonStyle.secondary)

        # Define callbacks
        result = None
        async def hit(interaction: discord.Interaction):
            nonlocal result
            result = True
            await interaction.response.defer()
            view.stop()
        async def stand(interaction: discord.Interaction):
            nonlocal result
            result = False
            await interaction.response.defer()
            view.stop()
        
        hitButton.callback = hit
        standButton.callback = stand

        # Create a View and add buttons
        view = View()
        view.add_item(hitButton)
        view.add_item(standButton)

        await interaction.followup.send(embed=embed, view=view, ephemeral=False)
        await view.wait()
        return result

    async def gameEndBreakdown(self, title: str, color: discord.Color, files=None):
        # Compare hands
        embed = await createEmbed(title=title, descr="Here's the breakdown.", color=color)
        embed.add_field(name="Your hand:", value=f"{self.player["value"]}", inline=False)
        embed.add_field(name="Dealer Up Card:", value=f"{self.dealer["cards"][0][0]}", inline=False)
        embed.add_field(name="Dealer Hole Card:", value=f"{self.holeCardName}", inline=False)
        embed.add_field(name="Dealer Total Hand:", value=f"{self.dealer["value"]}", inline=False)
        if files:
            await self.interaction.followup.send(embed=embed, files=files, ephemeral=False)
        else:
            await self.interaction.followup.send(embed=embed, ephemeral=False)

    async def win(self):
        await self.gameEndBreakdown("You win!", discord.Color.green())
        return
    
    async def winDealerBust(self):
        await self.gameEndBreakdown("You win (Dealer Bust)!", discord.Color.green())
        return

    async def push(self):
        await self.gameEndBreakdown("PUSH (Tie)!", discord.Color.yellow())
        return
    
    async def blackjackPush(self, files=None):
        await self.gameEndBreakdown("BLACKJACK (Push/Tie)!", discord.Color.yellow(), files=files)
        return
    
    async def blackjackPlayer(self, files=None):
        await self.gameEndBreakdown("BLACKJACK (Win)!", discord.Color.green(), files=files)
        return
    
    async def blackjackDealer(self, files=None):
        await self.gameEndBreakdown("BLACKJACK (LOSE)!", discord.Color.red(), files=files)
        return
    
    async def lose(self):
        await self.gameEndBreakdown("You lose!", discord.Color.red())
        return

    async def bust(self):
        await self.gameEndBreakdown("You lose (BUST)!", discord.Color.red())

    async def stand(self):
        dealerValue = self.dealer["value"]
        if dealerValue < 17: # Dealer must draw, otherwise the dealer stands if their hand is worth 17+
            # Dealer's turn
            await self.dealerDraw()
            allCards = self.dealer["cards"]
            card = allCards[-1]
            cardName, cardPath, cardValue = card
            cardValue = await self.aceCheck(cardValue)

        # Dealer conditions
        if dealerValue > 21: # Dealer bust condition
            await self.winDealerBust()
            return # Dealer busted, no need to go further!

        # Player conditions
        playerValue = self.player["value"]
        if playerValue < dealerValue:
            await self.lose()
        elif playerValue == dealerValue:
            await self.push()
        elif playerValue > dealerValue:
            await self.win()

    async def hit(self):
        # Player
        await self.playerDraw()
        allCards = self.player["cards"]
        card = allCards[-1] # Get the most recent card drawn
        cardName, cardPath, cardValue = card
        cardValue = await self.aceCheck(cardValue)
        playerValue = self.player["value"]

        # Player conditions
        if playerValue > 21: # Player bust condition
            await self.rounds(result=False)
        if playerValue <= 21: # Player limbo condition
            await self.rounds(result=True)
        
    async def rounds(self, result: bool):
        if result: # Player can hit or stand again
            hitOrStandResult = await self.hitOrStand(self.interaction)
            if hitOrStandResult: await self.hit()
            else: await self.stand()
        else: # Player busted
            await self.bust()

    async def drawRandCard(self):
        return random.choice(Standard52CardDeck().blackjack)

    # "Public" methods
    async def play(self, interaction: discord.Interaction):
        await self.resetGame()
        self.interaction = interaction

        # Initial message
        embed = await createEmbed(title="Starting Blackjack!", descr="Dealing initial hand...", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=False)

        # Draw cards
        gameIsBlackjack = await self.initialDraw()
        if gameIsBlackjack:
            print(f"GAME IS BLACKJACK ({self.player["value"]} vs {self.dealer["value"]})")
            return # Game is over, no need to go any further

        # Hit or stand
        await self.rounds(result=True)